from pathlib import Path
import re, unicodedata
from typing import Iterable

# Local dependencies
from ..core.documents import Document, chunk_text

# Librería para leer PDFs
try:
    import pdfplumber
except Exception as e:
    raise RuntimeError("Para usar pdf_loader necesitás instalar pdfplumber:\n" "   pip install pdfplumber\n") from e


_NONWORD = re.compile(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9.,;:?!¿¡()\"'–—\-/%\[\]<> ]")
_MANY_SYMBOLS = re.compile(r"[^\w\s]{3,}")  # secuencias largas de símbolos
_MULTI_SPACE = re.compile(r"\s+")
_HARD_HYPH = re.compile(r"(\w)-\n(\w)")  # palabra-\ncontinuación
_SOFT_HYPH = re.compile(r"[\u00AD]")  # soft hyphen
_PAGE_NUM = re.compile(r"^\s*(page|p\.)\s*\d+\s*$", re.I)
_SECTION_NUM = re.compile(r"^\s*\d+(\.\d+)*\s*$")  # líneas tipo "3", "4.2.1"
_URL_LINE = re.compile(r"https?://\S+", re.I)


def _normalize(text: str) -> str:
    """Normalize text encoding and characters"""
    # NFKC para normalizar formas; reemplaza espacios no-break, etc.
    t = unicodedata.normalize("NFKC", text or "")
    t = t.replace("\u00a0", " ")  # NBSP → espacio
    # ligaduras comunes
    t = t.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return t


def _split_lines_keep(text: str) -> list:
    """Split text into lines and remove empty ones"""
    # normaliza saltos → líneas "crudas"
    t = text.replace("\r", "\n")
    raw = [ln.strip() for ln in t.splitlines()]
    return [ln for ln in raw if ln]  # quita vacías


def _dehyphenate(paragraph: str) -> str:
    """Remove hyphenation across line breaks"""
    # une palabra-\npalabra → palabracontinuación
    return _HARD_HYPH.sub(r"\1\2", paragraph)


def _noise_ratio(line: str) -> float:
    """Calculate noise ratio of a line"""
    if not line:
        return 1.0
    letters = sum(ch.isalnum() for ch in line)
    return 1.0 - (letters / max(1, len(line)))


def _looks_header_footer(lines: Iterable[str]) -> tuple[set, set]:
    """
    Heurística simple: si la 1ª línea o la última línea se repite en >=30% de páginas,
    considéralas encabezado/pie
    """
    return set(), set()


def _clean_line(line: str) -> str:
    """Clean individual line"""
    # elimina soft hyphen y controla símbolos extraños
    line = _SOFT_HYPH.sub("", line)
    # quita urls complejas que ensucian tokens
    if _URL_LINE.search(line):
        line = _URL_LINE.sub("", line)
    # quita caracteres de control/raros
    line = _NONWORD.sub(" ", line)
    # colapsa espacios
    line = _MULTI_SPACE.sub(" ", line).strip()
    return line


def _is_junky(line: str) -> bool:
    """Check if line is likely junk (headers, page numbers, etc.)"""
    # líneas demasiado "símbolo" o con muy poca señal alfabética
    if len(line) <= 2:
        return True
    if _PAGE_NUM.match(line) or _SECTION_NUM.match(line):
        return True
    # muchas secuencias de símbolos (cuadros, barras, etc.)
    if len(_MANY_SYMBOLS.findall(line)) >= 2:
        return True
    # si más del 45% no son alfanuméricos/espacios, descarta
    if _noise_ratio(line) > 0.45:
        return True
    return False


def _merge_short_lines(lines: list, max_len: int = 60) -> list:
    """
    Junta líneas muy cortas (cortes "duros" de PDF) para formar frases más largas.
    """
    merged = []
    buf = ""
    for ln in lines:
        if not buf:
            buf = ln
            continue
        if len(buf) < max_len and not buf.endswith((".", "?", "!", ":", ";")):
            buf = f"{buf} {ln}"
        else:
            merged.append(buf)
            buf = ln
    if buf:
        merged.append(buf)
    return merged


def _clean(text: str) -> str:
    """
    Limpieza mejorada del texto extraído:
      - Normaliza Unicode/espacios/ligaduras
      - Dehyphenation (palabra-\npalabra)
      - Elimina líneas ruidosas (headers, pies, urls, símbolos)
      - Junta líneas muy cortas
    """
    if not text:
        return ""

    # 1) Normalización general
    t = _normalize(text)

    # 2) Dehyphenation en quiebres de línea
    t = _dehyphenate(t)

    # 3) Partir en líneas "crudas" y limpiar por línea
    raw_lines = _split_lines_keep(t)
    cleaned = []
    for ln in raw_lines:
        ln = _clean_line(ln)
        if not ln:
            continue
        if _is_junky(ln):
            continue
        cleaned.append(ln)

    if not cleaned:
        return ""

    # 4) Merge de líneas muy cortas (mejora coherencia del chunk)
    cleaned = _merge_short_lines(cleaned, max_len=80)

    # 5) Compactar espacios finales
    out = "\n".join(cleaned)
    out = _MULTI_SPACE.sub(" ", out)
    return out.strip()


def pdf_to_documents(pdf_path: Path, doc_id_prefix: str = None) -> list[Document]:
    """
    Lee un PDF y devuelve una lista de Document:
    - Un Document por página con su metadato 'page'.
    - El id se arma como {doc_id_prefix}_p{nro_pagina}.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {pdf_path}")

    docs: list[Document] = []
    base_id = doc_id_prefix or pdf_path.stem

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = _clean(page.extract_text() or "")
            if not text.strip():
                continue
            docs.append(
                Document(
                    id=f"{base_id}_p{i}",  # identificador único del documento
                    text=text,  # el texto ya limpio y normalizado de esa página
                    source=str(pdf_path.name),  # nombre del PDF
                    page=i,  # número de página
                )
            )
    return docs


def folder_pdfs_to_documents(folder: Path, recursive: bool = True) -> list[Document]:
    """
    Carga TODOS los PDFs de una carpeta (y subcarpetas si recursive=True).
    Devuelve lista de Documents (cada uno corresponde a una página).
    """
    pattern = "**/*.pdf" if recursive else "*.pdf"
    docs: list[Document] = []
    for pdf_path in folder.glob(pattern):
        docs.extend(pdf_to_documents(pdf_path))
    return docs


def documents_to_chunks(docs: list[Document], max_tokens_chunk: int = 400, overlap: int = 100) -> dict[str, list[str]]:
    """
    Convierte cada Document en sus chunks de texto.
    Retorna {doc_id: [chunk1, chunk2, ...]}.

    Extra: si una página es muy corta y chunk_text() devuelve [],
    generamos al menos un chunk de respaldo para que el doc no quede fuera del índice.
    """
    out: dict[str, list[str]] = {}
    for d in docs:
        chunks = chunk_text(d.text, max_tokens_chunk, overlap)

        if not chunks:
            # fallback para páginas cortas: un solo chunk recortado a ~max_tokens_chunk palabras
            txt = " ".join((d.text or "").split())
            if txt:
                words = txt.split()
                if len(words) > max_tokens_chunk:
                    words = words[:max_tokens_chunk]
                chunks = [" ".join(words)]
            else:
                chunks = []  # si realmente está vacío, dejamos vacío

        out[d.id] = chunks
    return out


#  Demo de uso rápido
if __name__ == "__main__":
    from src.config import corpus_dir

    all_docs = folder_pdfs_to_documents(corpus_dir(), recursive=True)
    print(f"Se leyeron {len(all_docs)} páginas con texto.")

    chunks_map = documents_to_chunks(all_docs, max_tokens_chunk=300, overlap=80)
    n_chunks = sum(len(v) for v in chunks_map.values())
    print(f"Se generaron {n_chunks} chunks.")
