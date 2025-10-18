from typing import Optional

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    raise ImportError("sentence_transformers is required. Install with: pip install sentence-transformers")


class CrossEncoderReranker:
    """Cross-encoder model for reranking query-document pairs"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: Optional[str] = None):
        """
        Initialize cross-encoder reranker

        Args:
            model_name: Name of the cross-encoder model
            device: Device to run model on (cuda/cpu)
        """
        self.model = CrossEncoder(model_name, device=device)
        self.model_name = model_name

    def rerank(
        self, query: str, candidates: list[tuple[str, str, dict]], batch_size: int = 16
    ) -> list[tuple[str, str, dict, float]]:
        """
        Rerank candidates using cross-encoder scores

        Args:
            query: Search query
            candidates: list of (doc_id, text, metadata) tuples
            batch_size: Batch size for inference

        Returns:
            list of (doc_id, text, metadata, score) tuples sorted by score
        """
        if not candidates:
            return []

        # Prepare query-document pairs
        pairs = [(query, text) for _, text, _ in candidates]

        # Get cross-encoder scores
        try:
            scores = self.model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
        except Exception as e:
            # Fallback: return candidates with dummy scores
            return [(doc_id, text, meta, 0.0) for doc_id, text, meta in candidates]

        # Combine with original data
        reranked = []
        for i, (doc_id, text, meta) in enumerate(candidates):
            score = float(scores[i]) if i < len(scores) else 0.0
            reranked.append((doc_id, text, meta, score))

        # Sort by score (descending)
        reranked.sort(key=lambda x: x[3], reverse=True)

        return reranked

    def __repr__(self):
        return f"CrossEncoderReranker(model='{self.model_name}')"
