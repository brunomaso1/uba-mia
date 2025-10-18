def rrf_combine(*ranked_lists: list[str], k: float = 60.0) -> list[str]:
    """
    Recibe múltiples listas ordenadas (BM25, vectorial, dense) y devuelve una lista fusionada usando RRF.

    Args:
        *ranked_lists: Variable number of ranked lists
        k: RRF parameter (default 60.0)

    Returns:
        Combined ranked list using RRF
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank + 1.0)
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item for item, _ in sorted_items]
