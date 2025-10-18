# src/agents/rag_agent/rag/evaluators/evaluate_retrieval.py

import argparse
import os
from pathlib import Path
import pandas as pd
from loguru import logger

# Local deps
from src.config import project_dir
from ..adapters.pinecone_adapter import PineconeSearcher
from ..core.io_utils import load_docs_jsonl, load_qrels_csv
from ..core.metrics import mrr, ndcg_at_k, precision_at_k, recall_at_k
from ..core.rag_pipeline import RagPipeline


def resolve_path(p: str) -> Path:
    """Return absolute path for files that may be provided as relative to the project root."""
    pp = Path(p)
    return pp if pp.is_absolute() else (project_dir() / pp)


def _non_empty_docs(docs) -> int:
    """Count docs that have non-empty text."""
    return sum(1 for d in docs if getattr(d, "text", "") and str(d.text).strip())


def evaluate(pipeline: RagPipeline, qrels, ks=(5, 10), top_retrieve=50, top_final=10):
    """Run retrieval evaluation and return (per-query df, aggregated df)."""
    rows = []

    logger.info(
        f"Evaluating retrieval with top_retrieve={top_retrieve}, "
        f"top_final={top_final}, ks={ks}"
    )

    for query, rel_ids in qrels.items():
        # Hybrid retrieval (BM25 + vector) with metadata
        logger.debug(f"Evaluating query: {query} with relevant documents: {rel_ids}")
        cand = pipeline.retrieve_with_metadata(query, top_k=top_retrieve)

        # Pre-rerank doc ids (dedup preserves order)
        logger.debug(f"Retrieved {len(cand)} candidate chunks for query: {query}")
        pre_ids = [doc_id for (doc_id, _chunk, _meta) in cand]
        pre_ids = list(dict.fromkeys(pre_ids))

        # Rerank with Cross-Encoder and deduplicate by doc id
        logger.debug(f"Reranking top {top_final} candidates for query: {query}")
        rer = pipeline.reranker.rerank(query, cand)[:top_final]
        post_ids = [doc_id for (doc_id, _chunk, _meta, _score) in rer]
        post_ids = list(dict.fromkeys(post_ids))

        # Metrics for each K
        logger.debug(f"Calculating metrics for query: {query}")
        for k in ks:
            rows.append(
                {
                    "query": query,
                    "k": k,
                    "precision_pre": precision_at_k(pre_ids, rel_ids, k),
                    "recall_pre": recall_at_k(pre_ids, rel_ids, k),
                    "ndcg_pre": ndcg_at_k(pre_ids, rel_ids, k),
                    "precision_post": precision_at_k(post_ids, rel_ids, k),
                    "recall_post": recall_at_k(post_ids, rel_ids, k),
                    "ndcg_post": ndcg_at_k(post_ids, rel_ids, k),
                    "mrr_pre": mrr(pre_ids, rel_ids),
                    "mrr_post": mrr(post_ids, rel_ids),
                }
            )

    df = pd.DataFrame(rows)
    agg = df.groupby("k").mean(numeric_only=True).reset_index() if not df.empty else pd.DataFrame()
    return df, agg


if __name__ == "__main__":
    logger.info(f"Project root: {project_dir}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=str, default="", help="e.g., data/evaluate/docs_sample_en.jsonl")
    parser.add_argument("--qrels", type=str, default="", help="e.g., data/evaluate/qrels_sample_en.csv (query,doc_id,label)")
    parser.add_argument("--ks", type=str, default="5,10")
    parser.add_argument("--top_retrieve", type=int, default=50)
    parser.add_argument("--top_final", type=int, default=10)
    parser.add_argument("--device", type=str, default=None)
    args = parser.parse_args()

    logger.info(f"Arguments: {args}")
    ks = tuple(int(x) for x in args.ks.split(",") if x.strip().isdigit()) or (5, 10)

    # Resolve and verify paths
    logger.info("Loading documents and qrels...")
    docs_path = resolve_path(args.docs) if args.docs else None
    qrels_path = resolve_path(args.qrels) if args.qrels else None
    logger.info(f"Resolved docs path : {docs_path}")
    logger.info(f"Resolved qrels path: {qrels_path}")

    if not (docs_path and qrels_path and docs_path.exists() and qrels_path.exists()):
        logger.error("Valid docs/qrels files not found.")
        raise SystemExit(
            f"[ERROR] Could not find valid files.\n"
            f"  docs = {docs_path} (exists={docs_path.exists() if docs_path else None})\n"
            f"  qrels= {qrels_path} (exists={qrels_path.exists() if qrels_path else None})\n"
            f"  cwd  = {Path.cwd()}\n"
            f"Example: python -m src.agents.rag_agent.rag.evaluators.evaluate_retrieval "
            f"--docs data/evaluate/docs_sample_en.jsonl --qrels data/evaluate/qrels_sample_en.csv"
        )

    logger.info(f"Loading documents from: {docs_path}")
    docs = load_docs_jsonl(docs_path)
    logger.info(f"Loading qrels from: {qrels_path}")
    qrels = load_qrels_csv(qrels_path)

    # --- Guards to prevent ZeroDivisionError in BM25 (empty corpus) ---
    if not docs:
        logger.error("No documents were loaded (len(docs) == 0). BM25 will fail (division by zero).")
        raise SystemExit(
            "[ERROR] 0 documents loaded. "
            "Check that the file exists inside the container and that your Docker volume is correctly mounted.\n"
            f"  docs_path = {docs_path}\n"
            f"  qrels_path= {qrels_path}\n"
            f"  cwd       = {Path.cwd()}\n"
            "Tip: map host './data' to '/app/data' and use paths like 'data/evaluate/...'."
        )

    non_empty = _non_empty_docs(docs)
    if non_empty == 0:
        logger.error("All documents have empty/whitespace text. BM25 will not work.")
        raise SystemExit(
            "[ERROR] All loaded documents have empty text. Provide non-empty documents for evaluation."
        )

    if not qrels:
        logger.warning("Qrels is empty. Metrics may be meaningless (no relevant docs per query).")

    # Pinecone searcher with isolated namespace for evaluation
    logger.info("Setting up PineconeSearcher...")
    index_name = os.getenv("PINECONE_INDEX", "pln3-index")
    searcher = PineconeSearcher(index_name=index_name, namespace="eval-metrics")
    try:
        searcher.clear_namespace()  # First time may say “does not exist”; that's fine
    except Exception as e:
        logger.warning(f"clear_namespace warning (ignored): {e}")

    # Build pipeline
    logger.info("Building RAG pipeline...")
    try:
        pipeline = RagPipeline(
            docs=docs,
            pinecone_searcher=searcher,
            max_tokens_chunk=120,
            overlap=30,
            ce_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
            device=args.device,
        )
    except ZeroDivisionError:
        logger.exception("ZeroDivisionError while initializing BM25 (likely empty corpus).")
        raise SystemExit(
            "[ERROR] BM25 initialization failed due to empty corpus (division by zero).\n"
            "Verify your docs file and Docker volume mapping."
        )

    # Run evaluation
    logger.info("Starting evaluation...")
    df, agg = evaluate(pipeline, qrels, ks=ks, top_retrieve=args.top_retrieve, top_final=args.top_final)
    logger.info("Evaluation completed.")

    if df.empty:
        print("\n[WARNING] No rows produced (empty evaluation). Check your qrels and retrieval outputs.")
    else:
        print("\n=== Metrics by query and K ===")
        print(df.to_string(index=False))

    if agg.empty:
        print("\n[WARNING] No aggregated metrics (empty DataFrame).")
    else:
        print("\n=== Macro averages by K ===")
        print(agg.to_string(index=False))

    print(f"\nDocs parent folder: {docs_path.parent}")
    doc_parent_path = docs_path.parent

    logger.info(f"Saving results to {doc_parent_path}")
    df_path = doc_parent_path / "eval_retrieval_per_query.csv"
    df.to_csv(df_path, index=False)

    logger.info(f"Saving aggregated results to {doc_parent_path}")
    agg_path = doc_parent_path / "eval_retrieval_aggregated.csv"
    agg.to_csv(agg_path, index=False)
