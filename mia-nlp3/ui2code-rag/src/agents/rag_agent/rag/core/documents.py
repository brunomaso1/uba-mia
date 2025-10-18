"""
Document processing and chunking utilities
Migrated from raglib.documents with path-aware configuration
"""

import re, unicodedata
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup


@dataclass
class Document:
    """Represents a document with metadata"""

    id: str
    text: str
    source: str = ""
    page: Optional[int] = None


# tokenización básica (casefold + letras con acentos y dígitos)
_TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+")


def simple_tokenize(text: str) -> list[str]:
    """Simple tokenization extracting alphanumeric tokens"""
    return _TOKEN_RE.findall((text or "").lower())


# utilidades para chunking basado en oraciones
# divide en oraciones simples: punto/exclamación/interrogación + espacio + mayúscula
_SENT_SPLIT = re.compile(r"(?<=[\.\!\?])\s+(?=[A-ZÁÉÍÓÚÑ])")
_SOFT_HYPH = re.compile(r"[\u00AD]")  # soft hyphen
_HARD_HYPH = re.compile(r"(\w)-\n(\w)")  # palabra-\ncontinuación


def _normalize(text: str) -> str:
    """Normalize text by removing hyphens and compacting whitespace"""
    t = unicodedata.normalize("NFKC", text or "")
    t = t.replace("\u00a0", " ")  # NBSP → espacio
    # de-hyphenation
    t = _SOFT_HYPH.sub("", t)
    t = _HARD_HYPH.sub(r"\1\2", t)
    # compacta espacios
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences"""
    if not text:
        return []
    # no asumimos que todo empiece en mayúscula; si no hay cortes, devolvemos el texto entero
    parts = _SENT_SPLIT.split(text.strip())
    if len(parts) <= 1:
        return [text.strip()]
    # limpiar espacios
    return [" ".join(p.split()) for p in parts if p.strip()]


def _count_tokens(t: str) -> int:
    """Count tokens in text"""
    return len(simple_tokenize(t))


def _slide_merge(sents: list[str], max_tok: int, overlap: int) -> list[str]:
    """
    Arma chunks concatenando oraciones hasta max_tok.
    Aplica solapamiento de ~overlap tokens usando la cola del chunk previo.
    Hace split adicional por ; : si una oración es enorme.
    """
    chunks: list[str] = []
    buf: list[str] = []
    buf_tokens = 0

    def flush():
        nonlocal buf, buf_tokens
        if buf_tokens >= 40:  # mínimo útil
            txt = " ".join(buf).split()
            # hard cap suave (max_tok + 20)
            if len(txt) > max_tok + 20:
                txt = txt[: max_tok + 20]
            chunks.append(" ".join(txt))
        buf, buf_tokens = [], 0

    for s in sents:
        st = _count_tokens(s)
        # si una oración es enorme, intentá partir por ; :
        if st > max_tok:
            pieces = re.split(r"[;:]\s+", s)
            for p in pieces:
                pt = _count_tokens(p)
                if pt == 0:
                    continue
                if pt > max_tok:
                    # si sigue siendo enorme, recortá
                    p = " ".join(p.split()[:max_tok])
                    pt = _count_tokens(p)
                if buf_tokens + pt <= max_tok:
                    buf.append(p)
                    buf_tokens += pt
                else:
                    flush()
                    # overlap: tomar cola del último chunk
                    if chunks:
                        tail = " ".join(chunks[-1].split()[-overlap:])
                        buf, buf_tokens = [tail], _count_tokens(tail)
                    buf.append(p)
                    buf_tokens += pt
            continue

        # caso normal
        if buf_tokens + st <= max_tok:
            buf.append(s)
            buf_tokens += st
        else:
            flush()
            if chunks:
                tail = " ".join(chunks[-1].split()[-overlap:])
                buf, buf_tokens = [tail], _count_tokens(tail)
            buf.append(s)
            buf_tokens += st

    if buf:
        flush()
    return chunks


def chunk_html_semantic_with_tags(html_text, max_tokens, overlap):

    soup = BeautifulSoup(html_text, "html.parser")
    tags_to_chunk = [
        "section",
        "div",
        "article",
        "header",
        "footer",
        "main",
        "nav",
        "aside",
        "form",
        "table",
        "ul",
        "ol",
        "li",
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]
    chunks = []
    for tag in soup.find_all(tags_to_chunk):
        html_chunk = str(tag)
        words = tag.get_text(separator=" ", strip=True).split()
        if len(words) >= max_tokens:
            # Si el bloque es muy grande, subdividir por tokens pero manteniendo la etiqueta
            start = 0

            while start < len(words):
                end = min(start + max_tokens, len(words))
                # Reconstruir el chunk con la etiqueta y el subset de texto
                # Puedes usar solo el texto, pero aquí se mantiene la etiqueta original

                chunk_text = " ".join(words[start:end])
                # Reemplaza el texto del tag por el chunk (manteniendo la etiqueta)

                tag_copy = BeautifulSoup(str(tag), "html.parser")

                for t in tag_copy.find_all(tags_to_chunk):
                    t.string = chunk_text
                chunks.append(str(tag_copy))
                start += max_tokens - overlap
        else:
            chunks.append(html_chunk)
    return chunks


def chunk_text(text: str, max_tokens: int = 200, overlap: int = 60) -> list[str]:
    """
    Chunking:
      - target ~200 tokens por chunk
      - solapamiento ~60 tokens
      - descarta chunks < 20 tokens
      - recorta > 220 tokens
    """
    if not text:
        return []
    norm = _normalize(text)
    sents = _split_sentences(norm)
    if not sents:
        return []
    chunks = _slide_merge(sents, max_tok=max_tokens, overlap=overlap)

    # filtro final de longitud
    out: list[str] = []
    for ch in chunks:
        nt = _count_tokens(ch)
        if 20 <= nt <= 220:
            out.append(ch)
    return out


def documents_to_chunks(
    docs: list[Document], max_tokens_chunk: int = 200, overlap: int = 60, chunking_method=chunk_html_semantic_with_tags
) -> dict[str, list[str]]:
    """
    Convert documents to chunks

    Args:
        docs: list of Document objects
        max_tokens_chunk: Maximum tokens per chunk
        overlap: Overlap between chunks

    Returns:
        Dictionary mapping document IDs to their chunks
    """
    chunks_per_doc = {}

    for doc in docs:
        chunks = chunking_method(doc.text, max_tokens_chunk, overlap)
        if not chunks:
            # Fallback for very short documents
            clean_text = " ".join((doc.text or "").split())
            if clean_text:
                words = clean_text.split()
                if len(words) > max_tokens_chunk:
                    words = words[:max_tokens_chunk]
                chunks = [" ".join(words)]
            else:
                chunks = []

        chunks_per_doc[doc.id] = chunks

    return chunks_per_doc
