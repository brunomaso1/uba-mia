"""RAG Agent for retrieving HTML/CSS examples based on visual analysis."""

import os
from pathlib import Path
from typing import Any
from loguru import logger

# Local dependencies
from .rag.core.documents import Document
from .rag.core.rag_pipeline import RagPipeline
from .rag.adapters.pinecone_adapter import PineconeSearcher
from .rag.ingestion.websight_loader import WebSightLoader
from src.config import (
    ui_examples_dir,
    pinecone_index,
    pinecone_model_name,
    pinecone_cloud,
    pinecone_region,
    pinecone_api_key,
    pinecone_rag_namespace,
    rag_ce_model,
    corpus_dir,
    websight_data_dir,
    st_model_name,
)


class RAGAgent:
    def __init__(self):
        self.rag_pipeline = None

    def initialize_corpus_rag_pipeline(self) -> bool:
        """Inicializa el pipeline RAG con los documentos del corpus local."""
        if not corpus_dir().exists():
            logger.warning(f"Corpus directory not found: {corpus_dir()}")
            return False
        if not any(corpus_dir().iterdir()):
            logger.warning(f"Corpus directory is empty: {corpus_dir()}")
            return False

        documents = []

        self.rag_pipeline = self._initialize_rag_pipeline(documents)
        raise NotImplementedError("Local corpus loading not implemented yet.")

    def initialize_websight_rag_pipeline(self) -> bool:
        """Inicializa el pipeline RAG con ejemplos de HTML/CSS del conjunto de datos WebSight."""
        websight_data_dir().mkdir(parents=True, exist_ok=True)
        if not any(websight_data_dir().iterdir()):
            logger.info(f"WebSight data directory is empty: {websight_data_dir()}. Downloading dataset...")
            try:
                self._download_websight_dataset(websight_data_dir())
            except Exception as e:
                logger.error(f"Error downloading WebSight dataset: {e}")
                return False
        else:
            logger.info(
                f"WebSight data directory already exists: {websight_data_dir()}. Skipping download. Maybe outdated?"
            )

        documents: list[Document] = []
        documents = self._load_websight_html_examples()
        self.rag_pipeline = self._initialize_rag_pipeline(documents)
        return self.rag_pipeline is not None

    def _initialize_rag_pipeline(self, documents: list[Document]) -> RagPipeline:
        """Initialize RAG pipeline with HTML/CSS examples"""
        try:
            pinecone_searcher = None
            if pinecone_api_key:
                try:
                    logger.debug("Initializing Pinecone searcher for RAG pipeline...")
                    pinecone_searcher = PineconeSearcher(
                        index_name=pinecone_index,
                        model_name=st_model_name,
                        cloud=pinecone_cloud,
                        region=pinecone_region,
                        api_key=pinecone_api_key,
                        namespace=pinecone_rag_namespace,
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize Pinecone: {e}")

            # Initialize RAG pipeline
            logger.info("Creating RAG pipeline...")
            return RagPipeline(
                docs=documents,
                pinecone_searcher=pinecone_searcher,
                max_tokens_chunk=400,  # Slightly larger chunks for HTML/CSS
                overlap=100,
                ce_model=rag_ce_model,
            )
        except Exception as e:
            logger.error(f"Error initializing RAG pipeline: {e}")
            return None

    def _load_websight_html_examples(self) -> list[Document]:
        """
        Load HTML/CSS examples using WebSightLoader from core layer.
        This loads data from WebSight dataset JSON files.
        Load HTML/CSS examples using WebSightLoader from core layer.
        This loads data from WebSight dataset JSON files.
        """
        websight_loader = WebSightLoader()
        documents = []

        try:
            logger.debug("Loading HTML/CSS examples using WebSightLoader...")
            documents = websight_loader.load_full_websight_pipeline(max_examples=1000)

            if documents:
                logger.success(f"Successfully loaded {len(documents)} WebSight documents")
                return documents

            # Fallback: try loading from ui_examples directory if WebSight fails
            logger.warning("No WebSight documents loaded, trying fallback to ui_examples...")
            examples_dir = ui_examples_dir()

            if not examples_dir.exists():
                logger.error(f"Examples directory not found: {examples_dir}")
                return []

            # Load HTML files
            html_files = list(examples_dir.glob("**/*.html"))
            logger.info(f"Found {len(html_files)} HTML files in ui_examples.")

            for html_file in html_files:
                try:
                    with open(html_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Create document
                    doc = Document(id=html_file.stem, text=content, source=str(html_file))

                    # Add additional attributes
                    doc.doc_type = "html_example"
                    doc.filename = html_file.name
                    doc.html_code = content
                    doc.file_size = len(content)
                    documents.append(doc)

                except Exception as e:
                    logger.error(f"Error loading {html_file}: {e}")

            print(f"Loaded {len(documents)} HTML examples from fallback")
            return documents

        except Exception as e:
            print(f"Error loading HTML examples: {e}")
            logger.error(f"Error loading HTML examples: {e}")
            return []

    def _download_websight_dataset(self, output_dir: Path) -> bool:
        """Descarga el conjunto de datos WebSight en el directorio especificado."""
        websight_loader = WebSightLoader()
        try:
            websight_loader.download_websight_data(output_dir)
            return True
        except Exception as e:
            logger.error(f"Error downloading WebSight dataset: {e}")
            return False

    def create_rag_index(self, folder_path: str):
        """Crea o actualiza el índice RAG con documentos HTML/CSS desde una carpeta local.
        Esta carpeta contiene archivos HTML que se cargarán y procesarán para
        crear o actualizar el índice RAG utilizado para la recuperación de patrones.
        """
        raise NotImplementedError("RAG index creation not implemented yet.")

    def invoke(self, visual_analysis: dict[str, Any], top_k: int = 5) -> list[tuple]:
        """
        Retrieve similar HTML/CSS patterns based on visual analysis

        Args:
            visual_analysis: Analysis result from VisualAgent
            top_k: Number of top patterns to retrieve

        Returns:
            List of tuples (doc_id, chunk, metadata_enriched, score)
            where metadata_enriched includes the full html_code
            List of tuples (doc_id, chunk, metadata_enriched, score)
            where metadata_enriched includes the full html_code
        """
        if not self.rag_pipeline:
            return []

        try:
            # Extract analysis text for RAG search
            analysis_text = visual_analysis.get("analysis_text", "")

            if not analysis_text:
                # Fallback: construct analysis text from components
                components = visual_analysis.get("components", [])
                layout = visual_analysis.get("layout", "")
                style = visual_analysis.get("style", "")

                analysis_text = f"UI components: {', '.join(components)}. Layout: {layout}. Style: {style}"

            # Use RAG pipeline to retrieve similar patterns
            results = self.rag_pipeline.retrieve_and_rerank(
                query=analysis_text,
                top_retrieve=20,  # Retrieve more candidates
                top_final=top_k,  # Return top_k final results
            )

            # Enrich results with full html_code from original documents
            enriched_results = []
            for doc_id, chunk, metadata, score in results:
                # Get the original document to access html_code
                doc = self.rag_pipeline.docs.get(doc_id)

                # Create enriched metadata with full HTML code
                metadata_enriched = dict(metadata) if isinstance(metadata, dict) else {}

                if doc and hasattr(doc, "html_code"):
                    metadata_enriched["html_code"] = doc.html_code
                    metadata_enriched["doc_type"] = getattr(doc, "doc_type", "unknown")
                    metadata_enriched["description"] = getattr(doc, "description", "No description")
                    metadata_enriched["components"] = getattr(doc, "components", [])
                    metadata_enriched["filename"] = getattr(doc, "filename", doc_id)
                    logger.debug(
                        f"Enriched pattern {doc_id} with html_code ({len(metadata_enriched['html_code'])} chars)"
                    )
                else:
                    # Fallback: use chunk as html_code if document not found
                    metadata_enriched["html_code"] = chunk
                    logger.warning(f"Could not find document {doc_id}, using chunk as html_code")

                enriched_results.append((doc_id, chunk, metadata_enriched, score))

            logger.info(f"Retrieved and enriched {len(enriched_results)} patterns for code generation")
            return enriched_results

        except Exception as e:
            logger.error(f"Error retrieving patterns: {e}", exc_info=True)
            return []

    def get_rag_status(self) -> dict[str, Any]:
        """Get status of the RAG pipeline"""
        if not self.rag_pipeline:
            return {"status": "not_initialized", "message": "RAG pipeline is not initialized"}

        try:
            total_docs = len(self.rag_pipeline.docs) if hasattr(self.rag_pipeline, "docs") else 0
            total_chunks = (
                sum(len(chunks) for chunks in self.rag_pipeline.chunks_per_doc.values())
                if hasattr(self.rag_pipeline, "chunks_per_doc")
                else 0
            )

            return {
                "status": "ready",
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "vector_search_available": self.rag_pipeline.vec is not None,
                "bm25_search_available": self.rag_pipeline.bm25 is not None,
                "examples_directory": str(ui_examples_dir()),
            }

        except Exception as e:
            return {"status": "error", "message": f"Error getting RAG status: {str(e)}"}


if __name__ == "__main__":
    agent = RAGAgent()
    status = agent.initialize_websight_rag_pipeline()
    print(f"RAG initialization status: {status}")
