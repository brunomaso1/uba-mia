import os
from pathlib import Path
import pandas as pd
import streamlit as st
from loguru import logger

from src.config import project_dir


# ---------- Path resolution that works locally and in Docker ----------
def _resolve_eval_path(p: str) -> Path:
    """
    Resolve a data path for both local dev and Docker.
    Tries, in order:
      1) Absolute path (if given)
      2) project_dir()/p
      3) CWD/p
      4) DATA_DIR/p  (DATA_DIR defaults to /app/data)
      5) If p startswith 'data/', also tries DATA_DIR/<after 'data/'>
    Returns the FIRST existing candidate; if none exists, returns the first candidate
    (so the caller can show a helpful error with the attempted candidates).
    """
    if not p or not str(p).strip():
        raise FileNotFoundError("Empty path provided.")

    p = p.strip()
    if p.startswith("/"):
        return Path(p)

    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    candidates: list[Path] = [
        project_dir() / p,       # typical local
        Path.cwd() / p,          # fallback to CWD
        data_dir / p,            # docker default mount
    ]

    if p.startswith("data/"):
        # allow mapping `data/...` -> `/app/data/...`
        after = p.split("data/", 1)[1]
        candidates.append(data_dir / after)

    for c in candidates:
        if c.exists():
            logger.info(f"Resolved path '{p}' -> {c}")
            return c

    # None existed: return first so caller can error with context
    logger.warning(
        "Path not found. Tried:\n" + "\n".join(f" - {c}" for c in candidates)
    )
    return candidates[0]


# ---------- Evaluation runner ----------
def _run_eval(
    docs_path: str,
    qrels_path: str,
    ks: tuple[int, ...],
    top_retrieve: int,
    top_final: int,
    device: str | None,
):
    """
    Execute the evaluation pipeline inside Streamlit.
    """
    from src.agents.rag_agent.rag.adapters.pinecone_adapter import PineconeSearcher
    from src.agents.rag_agent.rag.core.io_utils import load_docs_jsonl, load_qrels_csv
    from src.agents.rag_agent.rag.core.rag_pipeline import RagPipeline
    from src.agents.rag_agent.rag.evaluators.evaluate_retrieval import evaluate

    # Resolve paths robustly for local & docker
    docs_abs = _resolve_eval_path(docs_path)
    qrels_abs = _resolve_eval_path(qrels_path)

    if not docs_abs.exists() or not qrels_abs.exists():
        tried = f"docs={docs_abs} (exists={docs_abs.exists()}) | qrels={qrels_abs} (exists={qrels_abs.exists()})"
        raise FileNotFoundError(
            f"Data files not found.\n{tried}\n"
            f"CWD={Path.cwd()} | DATA_DIR={os.getenv('DATA_DIR', '/app/data')} | PROJECT_DIR={project_dir()}"
        )

    # Load data
    docs = load_docs_jsonl(docs_abs)
    qrels = load_qrels_csv(qrels_abs)

    if not docs:
        raise FileNotFoundError(
            f"No documents loaded from {docs_abs}. "
            "Check your volume mapping and file contents."
        )

    # Pinecone config
    from src.config import pinecone_index as cfg_pinecone_index, pinecone_api_key as cfg_pinecone_api_key
    index_name = os.getenv("PINECONE_INDEX") or (cfg_pinecone_index if cfg_pinecone_index else "pln3-index")
    api_key = os.getenv("PINECONE_API_KEY") or cfg_pinecone_api_key
    if not api_key:
        st.error("PINECONE_API_KEY not configured. Set it in environment variables or src.config.")
        st.stop()

    # Fresh namespace for eval
    searcher = PineconeSearcher(index_name=index_name, namespace="eval-metrics")
    try:
        searcher.clear_namespace()
    except Exception:
        pass

    # Build RAG pipeline
    pipeline = RagPipeline(
        docs=docs,
        pinecone_searcher=searcher,
        max_tokens_chunk=120,
        overlap=30,
        ce_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        device=device,
    )

    # Run evaluation
    df, agg = evaluate(
        pipeline, qrels, ks=ks,
        top_retrieve=top_retrieve,
        top_final=top_final
    )
    return df, agg


def _download_btn(df: pd.DataFrame, label: str, filename: str):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", type="primary")


# ---------- Page ----------
def render():
    st.header("📏 Evaluaciones de Retrieval")
    st.markdown("Corre métricas **MRR, nDCG, Precision@k, Recall@k** sobre tu set de evaluación.")

    with st.expander("⚙️ Parámetros", expanded=True):
        c1, c2 = st.columns([2, 2])
        with c1:
            # These work both local (./data/...) and docker (/app/data/... via mapping)
            docs = st.text_input("Ruta Docs JSONL", value="data/evaluate/docs_ui_code_en.jsonl")
            qrels = st.text_input("Ruta Qrels CSV", value="data/evaluate/qrels_ui_code_en.csv")
        with c2:
            ks_str = st.text_input("K's (coma)", value="3,5")
            ks = tuple(int(x) for x in ks_str.split(",") if x.strip().isdigit())
            top_ret = st.slider("top_retrieve", 5, 200, 10, step=5)
            top_fin = st.slider("top_final", 1, 50, 5, step=1)
        device = st.selectbox("Device (opcional)", ["auto", "cpu", "cuda", "mps"], index=0)

    run = st.button("🚀 Ejecutar evaluación", type="primary")
    if run:
        with st.spinner("Indexando y evaluando…"):
            try:
                df, agg = _run_eval(
                    docs, qrels,
                    ks=ks,
                    top_retrieve=top_ret,
                    top_final=top_fin,
                    device=None if device == "auto" else device
                )
            except FileNotFoundError as e:
                st.error(f"No se encontraron archivos: {e}")
                return
            except Exception as e:
                st.error(f"Error durante la evaluación: {e}")
                st.exception(e)
                return

        st.subheader("📊 Métricas por query y K")
        st.dataframe(df, use_container_width=True)
        _download_btn(df, "⬇️ Descargar per-query", "eval_retrieval_per_query.csv")

        st.subheader("✅ Promedios (macro) por K")
        st.dataframe(agg, use_container_width=True)
        _download_btn(agg, "⬇️ Descargar agregados", "eval_retrieval_aggregated.csv")

        with st.expander("📈 Tips de lectura"):
            st.markdown(
                "- **MRR** resalta si el doc relevante aparece muy arriba.\n"
                "- **nDCG** captura ganancias por posición, útil si hay múltiples relevantes.\n"
                "- **Precision@k/Recall@k**: micro-claros para comparar pre/post reranking."
            )
