import streamlit as st, asyncio
from datetime import datetime
from app.services.agents import get_orchestrator, get_rag_agent
from app.ui.components.code_preview import html_preview
from app.ui.theme import stable_code_block
from src.agents.orchestator_agent.utils import save_analysis_result, save_generated_code
from src.config import temp_images_dir
from PIL import Image

def render():
    st.header("🎨 UI → Code Generator")
    st.markdown("Subí un diseño (imagen) y generá HTML/Tailwind limpio.")

    orchestrator = get_orchestrator()
    rag_agent = get_rag_agent()
    if not orchestrator or not rag_agent:
        st.error("Agentes no disponibles. Ver configuración.")
        return

    c1, c2 = st.columns([2,1])
    with c1:
        file = st.file_uploader("Upload UI Design", type=["png","jpg","jpeg","webp"])
    with c2:
        st.markdown("### Settings")
        top_k = st.slider("Patrones similares", 1, 10, 5)
        save = st.checkbox("Guardar artefactos", value=True)
        ex = st.selectbox("Ejemplos rápidos (opcional)", ["","Use dark theme with purple accents","Make it fully responsive","Add glassmorphism","ARIA labels + A11y"])
        custom = st.text_area("Instrucciones (opcional)", value=ex or "")

    if file is not None:
        st.markdown("### 📷 Vista previa")
        st.image(file, use_container_width=True)

        tmp = temp_images_dir(); tmp.mkdir(parents=True, exist_ok=True)
        path = tmp / f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
        with open(path, "wb") as f: f.write(file.getbuffer())
        

        if st.button("🚀 Analizar & Generar", type="primary"):
            pbar = st.progress(0); msg = st.empty()
            try:
                loop = asyncio.get_event_loop()
                msg.info("Paso 1/3: Análisis visual…"); pbar.progress(10)
                with st.spinner("Vision model…"):
                    analysis = loop.run_until_complete(orchestrator.send_message_to_visual_agent(path))
                pbar.progress(30)

                if "error" in analysis:
                    st.error(f"Análisis falló: {analysis['error']}"); return

                st.markdown("### 🔍 Resultados de análisis")
                cA,cB,cC = st.columns(3)
                with cA: st.metric("Componentes", len(analysis.get("components", [])))
                with cB: st.write("**Layout:**", analysis.get("layout","?"))
                with cC: st.write("**Estilo:**", analysis.get("style","?"))
                with st.expander("📋 Detalle"):
                    st.json(analysis)

                msg.info("Paso 2/3: Buscando patrones…"); pbar.progress(55)
                with st.spinner("RAG HTML/CSS…"):
                    patterns = rag_agent.invoke(analysis, top_k=top_k)

                if patterns:
                    st.subheader(f"🔗 {len(patterns)} patrones similares")
                    for i,(doc_id,chunk,meta,score) in enumerate(patterns,1):
                        with st.expander(f"Pattern #{i} — {meta.get('filename','?')} (score {score:.3f})"):
                            st.markdown(f"**Tipo:** {meta.get('type','?')} — **Desc.:** {meta.get('description','—')}")
                            stable_code_block(chunk[:700] + ("..." if len(chunk)>700 else ""), language="html", key="gen_code_block")

                msg.info("Paso 3/3: Generando código…"); pbar.progress(85)
                with st.spinner("Code Agent…"):
                    result = loop.run_until_complete(
                        orchestrator.send_message_to_code_agent(patterns, analysis, custom_instructions=custom)
                    )
                pbar.progress(100); msg.success("¡Listo!")

                html_code = result.get("html_code","")
                st.subheader("💻 HTML/Tailwind generado")
          
                stable_code_block(html_code or "<!-- empty -->", language="html", key="gen_code_block")
                st.subheader("🌐 Preview")
                html_preview(html_code)

                with st.expander("🛠️ Detalles de generación"):
                    st.json(result.get("generation_metadata", {}))

                if save and html_code:
                    try:
                        p1 = save_generated_code(result)
                        p2 = save_analysis_result(analysis)
                        st.success(f"Código guardado en: {p1}")
                        st.info(f"Análisis guardado en: {p2}")
                    except Exception as e:
                        st.warning(f"No se pudo guardar: {e}")

            finally:
                try: path.exists() and path.unlink()
                except: pass
