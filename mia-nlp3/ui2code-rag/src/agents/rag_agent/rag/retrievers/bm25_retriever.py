import numpy as np
from rank_bm25 import BM25Okapi

# Local dependencies
from ..core.documents import Document, simple_tokenize


class BM25Index:
    """BM25 search index for lexical retrieval"""

    def __init__(self, docs: list[Document], chunks_per_doc: dict[str, list[str]]):
        """
        Initialize BM25 index

        Args:
            docs: list of documents
            chunks_per_doc: Dictionary mapping document IDs to their chunks
        """
        self.doc_ids: list[str] = []
        self.chunks: list[str] = []

        # Build flat list of chunks with document mapping
        for d in docs:
            for ch in chunks_per_doc[d.id]:
                self.doc_ids.append(d.id)
                self.chunks.append(ch)

        # Tokenize and create BM25 index
        self.tokenized = [simple_tokenize(t) for t in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized)

    def search(self, query: str, top_k: int = 50) -> list[tuple[int, float]]:
        """
        Search using BM25 algorithm

        Args:
            query: Search query
            top_k: Number of top results to return

        Returns:
            list of (chunk_index, score) tuples
        """
        q_tokens = simple_tokenize(query)
        scores = self.bm25.get_scores(q_tokens)
        idx_sorted = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[int(i)])) for i in idx_sorted]
