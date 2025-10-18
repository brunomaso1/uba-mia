from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import os
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# Local dependencies:
from src.config import (
    pinecone_cloud,
    pinecone_region,
    pinecone_metric,
    st_model_name,
    pinecone_namespace,
    pinecone_api_key,
)


# Convención de IDs de chunk: f"{doc_id}::chunk_{local_idx}"
def make_chunk_id(doc_id: str, local_idx: int) -> str:
    """Create a unique chunk ID"""
    return f"{doc_id}::chunk_{local_idx}"


def parse_chunk_id(chunk_id: str) -> tuple[str, int]:
    """Parse chunk ID to get document ID and local index"""
    doc_id, rest = chunk_id.split("::", 1)
    i = int(rest.replace("chunk_", ""))
    return doc_id, i


def ensure_pinecone_index(
    pc: Pinecone,
    name: str,
    dim: int,
    cloud: str = pinecone_cloud,
    region: str = pinecone_region,
    metric: str = pinecone_metric,
):
    """Ensure Pinecone index exists, create if not"""
    idxs = {i["name"]: i for i in pc.list_indexes().get("indexes", [])}
    if name not in idxs:
        pc.create_index(
            name=name,
            dimension=dim,
            metric=metric,
            spec=ServerlessSpec(cloud=cloud, region=region),
        )


@dataclass
class PineconeSearcher:
    """
    Maneja embeddings + upsert + query sobre Pinecone.
    Guarda registro local (chunk_id -> meta) para mapear resultados a texto y metadatos.
    """

    index_name: str
    model_name: str = st_model_name
    cloud: str = pinecone_cloud
    region: str = pinecone_region
    api_key: Optional[str] = pinecone_api_key
    namespace: str = pinecone_namespace  # configurable

    def __post_init__(self):
        """Initialize Pinecone connection and embedding model"""
        key = self.api_key
        if not key:
            raise RuntimeError("Falta PINECONE_API_KEY en entorno o parámetro api_key.")

        self.pc = Pinecone(api_key=key)
        self.model = SentenceTransformer(self.model_name)
        dim = self.model.get_sentence_embedding_dimension()
        ensure_pinecone_index(self.pc, self.index_name, dim, cloud=self.cloud, region=self.region)
        self.index = self.pc.Index(self.index_name)

        # registro local: chunk_id -> dict(text, doc_id, local_idx, source, page)
        self.registry: dict[str, dict] = {}

    def _ns_vector_count(self) -> int:
        """Cantidad de vectores en la namespace actual."""
        try:
            stats = self.index.describe_index_stats()
            ns = getattr(stats, "namespaces", None) or stats.get("namespaces", {})
            if isinstance(ns, dict):
                node = ns.get(self.namespace, {})
                # Pinecone v3: {"vectorCount": N}
                if isinstance(node, dict):
                    return int(node.get("vectorCount", 0))
        except Exception as e:
            print(f"[WARN] describe_index_stats falló: {e}")
        return 0

    def clear_namespace(self):
        """
        Borra TODO en esta namespace si existe.
        Evita 404 'Namespace not found' en primeras corridas.
        """
        try:
            # describe_index_stats devuelve un dict con 'namespaces'
            stats = self.index.describe_index_stats()
            ns = getattr(stats, "namespaces", None) or stats.get("namespaces", {})
            if isinstance(ns, dict) and self.namespace in ns:
                self.index.delete(deleteAll=True, namespace=self.namespace)
            else:
                # No hay nada que borrar (namespace aún no creada)
                print(f"[INFO] Namespace '{self.namespace}' no existe todavía; skip clear.")
        except Exception as e:
            # No detengas la ejecución por esto; sólo avisa
            print(f"[WARN] clear_namespace saltado: {e}")

    def upsert_chunks(self, chunks_per_doc: dict[str, list[str]], docs_meta: dict[str, dict]):
        """Upload chunks to Pinecone with embeddings"""
        vectors = []
        for doc_id, chunks in chunks_per_doc.items():
            if not chunks:
                continue
            embs = self.model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
            for i, (ch, v) in enumerate(zip(chunks, embs)):
                chunk_id = make_chunk_id(doc_id, i)
                # Build metadata, excluding None values (Pinecone requirement)
                meta = {
                    "doc_id": doc_id,
                    "local_idx": i,
                    "source": (docs_meta.get(doc_id, {}) or {}).get("source", ""),
                    "text": ch,
                }
                # Only include page if it's not None
                page_val = (docs_meta.get(doc_id, {}) or {}).get("page")
                if page_val is not None:
                    meta["page"] = page_val
                self.registry[chunk_id] = meta
                vectors.append({"id": chunk_id, "values": v.tolist(), "metadata": meta})

        print(
            f"[UPSERT] index={self.index_name} ns={self.namespace} vectors={len(vectors)} (antes={self._ns_vector_count()})"
        )
        B = 100
        for i in range(0, len(vectors), B):
            self.index.upsert(vectors=vectors[i : i + B], namespace=self.namespace)
        print(f"[UPSERT] después={self._ns_vector_count()} en ns={self.namespace}")

    def search(self, query: str, top_k: int = 50, meta_filter: Optional[dict] = None) -> list[tuple[str, float, dict]]:
        """
        Search for similar chunks

        Returns:
            list of (chunk_id, score, metadata) tuples, score higher = more similar
        """
        q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].tolist()
        res = self.index.query(
            vector=q,
            top_k=top_k,
            include_metadata=True,
            namespace=self.namespace,  # usamos namespace
            filter=meta_filter,  # opcional: filtrar por source/page/etc.
        )
        out = []
        for m in res.matches:
            meta = self.registry.get(m.id) or (m.metadata or {})
            out.append((m.id, float(m.score), meta))
        return out
