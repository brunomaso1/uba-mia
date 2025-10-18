import streamlit as st
from loguru import logger
from src.config import corpus_dir, pinecone_index, pinecone_cloud, pinecone_region, pinecone_api_key, pinecone_namespace, st_model_name

@st.cache_resource
def get_legacy_pdf_pipeline():
    try:
        from src.agents.rag_agent.rag.adapters.pinecone_adapter import PineconeSearcher
        from src.agents.rag_agent.rag.core.rag_pipeline import RagPipeline
        from src.agents.rag_agent.rag.ingestion.pdf_loader import folder_pdfs_to_documents

        docs = folder_pdfs_to_documents(corpus_dir(), recursive=True)
        if not docs:
            return None

        pinecone_searcher = None
        if pinecone_api_key:
            pinecone_searcher = PineconeSearcher(
                index_name=pinecone_index,
                model_name=st_model_name,
                cloud=pinecone_cloud,
                region=pinecone_region,
                api_key=pinecone_api_key,
                namespace=pinecone_namespace,
            )

        return RagPipeline(
            docs=docs,
            pinecone_searcher=pinecone_searcher,
            max_tokens_chunk=300,
            overlap=80,
            ce_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        )
    except Exception as e:
        logger.warning(f"PDF pipeline init error: {e}")
        return None
