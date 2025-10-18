import os
import json
import streamlit as st

from app.services.agents import get_rag_agent
from app.services.rag_pipeline import get_legacy_pdf_pipeline
from src.config import project_dir, corpus_dir
from app.ui.theme import stable_code_block

def _get_pdf_status(pipeline=None):
    """
    Devuelve info del corpus PDF legacy (si existe) y del índice BM25/vector del pipeline heredado.
    """
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

                # Muestra (hasta 10) para UI
                for doc in docs[:10]:
                    text_preview = doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
                    chunk_count = 0
                    if pipeline and hasattr(pipeline, "chunks_per_doc") and doc.id in pipeline.chunks_per_doc:
                        chunk_count = len(pipeline.chunks_per_doc[doc.id])

                    documents.append(
                        {
                            "doc_id": doc.id,
                            "source": doc.source,
                            "page": doc.page,
                            "text_preview": text_preview,
                            "chunk_count": chunk_count,
                        }
                    )

                if pipeline and hasattr(pipeline, "chunks_per_doc"):
                    total_chunks = sum(len(chs) for chs in pipeline.chunks_per_doc.values())
            except Exception as e:
                st.warning(f"Error cargando PDFs legacy: {e}")

        bm25_ready = pipeline is not None
        vector_ready = pipeline is not None and getattr(pipeline, "vec", None) is not None

        vector_info = {}
        if vector_ready:
            try:
                vector_info = {
                    "vector_index_name": getattr(pipeline.vec, "index_name", None),
                    "vector_namespace": getattr(pipeline.vec, "namespace", None),
                    "total_vectors": None, 
                }
            except Exception:
                pass

        return {
            "status": "healthy" if (corpus_exists and total_docs > 0) else "warning",
            "corpus": {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "corpus_path": str(corpus_path),
                "documents": documents,
            },
            "indices": {"bm25_ready": bm25_ready, "vector_ready": vector_ready, **vector_info},
            "config": {
                "project_root": str(project_dir()),
                "corpus_dir": str(corpus_path),
                "pipeline_initialized": pipeline is not None,
            },
        }
    except Exception as e:
        st.error(f"Error obteniendo estado del PDF legacy: {e}")
        return None


def render():
    st.header("⚙️ System Status")

    if st.button("🔄 Refresh Status"):
        st.cache_resource.clear()
        st.rerun()

    # ---- Estado RAG principal (HTML/CSS patterns) ----
    rag_agent = get_rag_agent()
    if not rag_agent:
        st.error("❌ RAG Agent no disponible. Reiniciá la aplicación.")
        return

    rag_status = rag_agent.get_rag_status()  # debe exponer keys: status, total_documents, total_chunks, ...
    is_healthy = rag_status.get("status") == "ready" and rag_status.get("total_documents", 0) > 0
    status_emoji = "🟢" if is_healthy else "🟡"
    status_text = "HEALTHY" if is_healthy else "WARNING"

    st.markdown(f"## {status_emoji} System Status: {status_text}")

    st.markdown("### 📚 HTML/CSS Pattern Corpus")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("HTML Documents", rag_status.get("total_documents", 0))
    with c2:
        st.metric("Code Patterns", rag_status.get("total_chunks", 0))
    with c3:
        vector_status = "🟢 Ready" if rag_status.get("vector_search_available") else "🔴 Not Ready"
        st.metric("Vector Search", vector_status)
    with c4:
        bm25_status = "🟢 Ready" if rag_status.get("bm25_search_available") else "🔴 Not Ready"
        st.metric("BM25 Search", bm25_status)

    examples_dir = rag_status.get("examples_directory", "Unknown")
    stable_code_block(f"Corpus Path: {examples_dir}", language="bash", key="corpus_path_block")

    # ---- Detalle índices ----
    st.markdown("### 🔗 Search Index Details")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**BM25 Index (Keyword Search)**")
        if rag_status.get("bm25_search_available"):
            st.success("✅ Activo — keyword retrieval")
            st.info(f"📊 Indexed chunks: {rag_status.get('total_chunks', 0)}")
        else:
            st.error("❌ No disponible")

    with col2:
        st.markdown("**Vector Index (Semantic Search)**")
        if rag_status.get("vector_search_available"):
            st.success("✅ Activo — Pinecone semantic search")
            pinecone_index = os.getenv("PINECONE_INDEX", "rag-index")
            st.info(f"📦 Index: `{pinecone_index}`")
            st.info("🏷️ Namespace: `html-css-examples`")
            st.info(f"🔢 Vectors aprox.: {rag_status.get('total_chunks', 0)}")
        else:
            st.error("❌ No disponible — revisar PINECONE_API_KEY")

    # ---- Estado de agentes (servicios A2A externos) ----
    st.markdown("### 🤖 Agents Status")
    cva, cca, cra = st.columns(3)

    try:
        import httpx
        from src.config import visual_agent_url, code_agent_url
    except Exception:
        httpx = None
        visual_agent_url = None
        code_agent_url = None

    with cva:
        st.markdown("**Visual Agent**")
        if httpx and visual_agent_url:
            try:
                r = httpx.get(f"{visual_agent_url}/.well-known/agent-card.json", timeout=2.0)
                if r.status_code == 200:
                    st.success("✅ Running")
                else:
                    st.warning(f"⚠️ HTTP {r.status_code}")
                st.info(f"URL: {visual_agent_url}")
            except Exception:
                st.error("❌ Not reachable")
                st.info(f"URL: {visual_agent_url}")
        else:
            st.info("No configurado")

    with cca:
        st.markdown("**Code Agent**")
        if httpx and code_agent_url:
            try:
                r = httpx.get(f"{code_agent_url}/.well-known/agent-card.json", timeout=2.0)
                if r.status_code == 200:
                    st.success("✅ Running")
                else:
                    st.warning(f"⚠️ HTTP {r.status_code}")
                st.info(f"URL: {code_agent_url}")
            except Exception:
                st.error("❌ Not reachable")
                st.info(f"URL: {code_agent_url}")
        else:
            st.info("No configurado")

    with cra:
        st.markdown("**RAG Agent**")
        if rag_status.get("status") == "ready":
            st.success("✅ Ready")
            st.info(f"📚 {rag_status.get('total_documents', 0)} docs")
        else:
            st.error("❌ Not initialized")

    # ---- Configuración útil ----
    st.markdown("### ⚙️ Configuration")
    config_info = {
        "project_root": str(project_dir()),
        "websight_data_dir": str(project_dir() / "data" / "websight"),
        "html_patterns_dir": examples_dir,
        "rag_agent_initialized": True,
        "total_html_patterns": rag_status.get("total_documents", 0),
        "pinecone_configured": rag_status.get("vector_search_available", False),
    }
    st.json(config_info)

    # ---- Corpus PDF opcional (legacy) ----
    pipeline = get_legacy_pdf_pipeline()
    pdf_status = _get_pdf_status(pipeline)
    if pdf_status and pdf_status["corpus"]["total_documents"] > 0:
        st.markdown("---")
        st.markdown("### 📄 Additional PDF Corpus (Legacy)")
        st.info("PDFs legacy para retrieval general (no se usan para generar HTML).")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("PDF Documents", pdf_status["corpus"]["total_documents"])
        with c2:
            st.metric("PDF Chunks", pdf_status["corpus"]["total_chunks"])
