# spec_utils.py
import json, hashlib
from typing import Dict, Any, List, Tuple

def canonical_dumps(obj: Dict[str, Any]) -> str:
    """JSON canónico, sin espacios, claves ordenadas, para hashing estable."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def compute_spec_hash(spec: Dict[str, Any]) -> str:
    """sha256 del spec canónico (ignorando campos volátiles si hace falta)."""
    # Opcional: filtrar campos no deterministas antes del hash
    canonical = canonical_dumps(spec)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def bbox_area(b: List[int]) -> int:
    # b = [x, y, w, h]
    return max(int(b[2]), 0) * max(int(b[3]), 0)

def compute_coverage(components: List[Dict[str, Any]], image_w: int, image_h: int) -> float:
    if not components or image_w <= 0 or image_h <= 0:
        return 0.0
    total_area = image_w * image_h
    # Suma de áreas (sin union-find). Aproximación suficiente para gating.
    covered = sum(bbox_area(c.get("bbox", [0, 0, 0, 0])) for c in components)
    return min(1.0, covered / total_area)
