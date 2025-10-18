import os
import json
import streamlit as st

from app.services.agents import get_rag_agent
from app.services.rag_pipeline import get_legacy_pdf_pipeline
from src.config import project_dir, corpus_dir

# --- helper compartido con system_status ---
def _get_pdf_status(pipeline=None):
    try:
        corpus_path = corpus_dir()
        corpus_exists = corpus_path.exists()

        documents = []
        total_docs = 0
        total_chunks = 0

        if corpus_exists:
            try:
                from src.agents.rag_agent.rag.ingestion.pdf_loader import folder_pdfs_to_documents

                docs = folder_pdfs_to_documents(corpus_path, recursive=True)
                total_docs = len(docs)

                if pipeline and hasattr(pipeline, "chunks_per_doc"):
                    total_chunks = sum(len(chs) for chs in pipeline.chunks_per_doc.values())
            except Exception as e:
                st.warning(f"Error cargando PDFs legacy: {e}")

        return {
            "corpus": {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "corpus_path": str(corpus_path),
                "documents": documents,
            }
        }
    except Exception as e:
        st.error(f"Error obteniendo estado del PDF legacy: {e}")
        return None


def render():
    st.header("📚 HTML/CSS Pattern Corpus Information")
    if st.button("🔄 Refresh Corpus Information"):
        st.cache_resource.clear()
        st.rerun()

    rag_agent = get_rag_agent()
    if not rag_agent:
        st.error("❌ RAG Agent no disponible.")
        return

    rag_status = rag_agent.get_rag_status()

    if rag_status.get("status") == "ready":
        st.markdown("### 📊 Corpus Summary")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("HTML Documents", rag_status.get("total_documents", 0))
        with c2:
            st.metric("Code Patterns", rag_status.get("total_chunks", 0))
        with c3:
            st.metric("Vector Search (Pinecone)", "✅ Yes" if rag_status.get("vector_search_available") else "❌ No")
        with c4:
            st.metric("BM25 Search", "✅ Yes" if rag_status.get("bm25_search_available") else "❌ No")

        if rag_status.get("vector_search_available"):
            st.markdown("### 🔗 Vector Search Details")
            pinecone_index = os.getenv("PINECONE_INDEX", "rag-index")
            pinecone_namespace = "html-css-examples"
            col1, col2 = st.columns(2)
            with col1:
                st.code(f"Index: {pinecone_index}", language="text")
                st.code(f"Namespace: {pinecone_namespace}", language="text")
            with col2:
                st.code(f"Vectors (aprox): {rag_status.get('total_chunks', 0)}", language="text")
                st.code("Model: sentence-transformers/all-MiniLM-L6-v2", language="text")
            st.info("💡 Pinecone se usa para búsqueda semántica sobre todos los patrones HTML.")

        st.markdown("### 📁 Corpus Location")
        st.code(rag_status.get("examples_directory", "Unknown"), language="bash")

        st.markdown("### 🔍 Pattern Types")
        st.markdown(
            """
- **Landing pages** — Hero, CTAs, features  
- **Dashboards** — Sidebars, stat cards, tables  
- **Navigation** — Headers, menus, breadcrumbs  
- **Forms** — Inputs, validaciones, layouts  
- **Cards & Components** — UI reutilizable  
- **Responsive layouts** — Mobile-first
"""
        )

        # WebSight source info (conteo rápido de JSONs)
        st.markdown("### 📦 Source Data (WebSight)")
        websight_dir = project_dir() / "data" / "websight"
        st.markdown(f"**WebSight JSON files:** `{websight_dir}`")

        try:
            json_files = list(websight_dir.glob("websight_*.json"))
            total_rows = 0
            valid_files = 0
            for jf in json_files:
                try:
                    with open(jf, "r") as f:
                        data = json.load(f)
                        rows = len(data.get("rows", []))
                        if rows > 0:
                            total_rows += rows
                            valid_files += 1
                except Exception:
                    pass

            st.markdown(f"- **JSON files:** {len(json_files)} total ({valid_files} válidos)")
            st.markdown(f"- **Total HTML examples:** ~{total_rows}")
            st.markdown(f"- **Actualmente cargados:** {rag_status.get('total_documents', 0)} documentos")
        except Exception as e:
            st.warning(f"No se pudo leer WebSight dir: {e}")

        st.markdown("### 🎯 Uso")
        st.info(
            """
Este corpus se usa automáticamente en:
1) **UI → Code**: imagen → análisis visual → RAG recupera patrones → generación de código  
2) **RAG Search**: búsqueda de patrones por descripción  
3) **Prompt → HTML**: descripción → patrones similares → generación
"""
        )
    else:
        st.error("RAG system no está listo.")
        st.json(rag_status)

    pipeline = get_legacy_pdf_pipeline()
    pdf_status = _get_pdf_status(pipeline)
    if pdf_status and pdf_status["corpus"]["total_documents"] > 0:
        st.markdown("---")
        st.markdown("### 📄 PDF Corpus (Legacy)")
        st.info("PDFs adicionales para retrieval general (no se usan para UI→Code).")
        st.markdown(f"**PDF Documents:** {pdf_status['corpus']['total_documents']}")
        st.markdown(f"**Total Chunks:** {pdf_status['corpus']['total_chunks']}")
