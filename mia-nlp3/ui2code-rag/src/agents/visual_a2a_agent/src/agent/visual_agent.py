# TODO: Posibles mejoras
# - Tests
# - Los returns tendrían que ser objetos.
from loguru import logger
from io import BytesIO
import os, json, base64, sys, hashlib
from typing import Any, Dict, List, Tuple
import openai
from PIL import Image
import cv2
import numpy as np
import pytesseract

# Custom dependencies
from ..config import settings
from ..texts.prompts import ANALYSIS_PROMPT, REINFORCEMENT_PROMPT
from ..texts.types import COMMON_COMPONENTS

OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_BASE_URL = settings.openrouter_base_url
CODE_MODEL = settings.openrouter_visual_model
OPENAI_KEY = settings.openai_key
OPENAI_MODEL = settings.openai_visual_model


class VisualAgent:
    """
    Agent responsible for analyzing UI design images and extracting structural information
    """

    def __init__(self):
        if not (OPENROUTER_API_KEY or OPENAI_KEY):
            raise ValueError("No API key found for available providers. Please set one in the environment.")
        if OPENROUTER_API_KEY:
            self.client = openai.OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            self.model = CODE_MODEL
            self.use_openrouter = True
        else:
            if OPENAI_KEY:
                self.client = openai.OpenAI(api_key=OPENAI_KEY)
                self.model = OPENAI_MODEL
                self.use_openrouter = False

    def invoke(self, img: Image) -> dict[str, Any]:
        """
        Analyze a UI image and extract component information using vision model.
        Pipeline:
          1) Preprocess (meta + paleta + layout hints)
          2) Vision model con prompt STRICT JSON
          3) Parse robusto y normalización de spec (components/palette/spacing/image_meta)
          4) Hash del spec
        """
        try:
            # --- (1) Preprocess image
            image_metadata = self._preprocess_image(img)
            if "error" in image_metadata:
                return image_metadata

            # --- (2) Prompt + vision call
            prompt = self._get_analysis_prompt_strict_json()
            base64_image = self._encode_image_to_base64(img)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.1,
            )

            analysis_text = response.choices[0].message.content or ""
            try:
                llm_obj = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback: extracción por texto (muy conservador)
                llm_obj = {
                    "components": self._extract_components_from_text(analysis_text),
                    "layout": "unknown",
                    "style": "modern",
                }

            # --- (3) Normalizar spec + enriquecer con preprocesado
            spec = self._build_spec(llm_obj, image_metadata, img)

            # --- (4) Hash del spec
            spec["hash"] = self._compute_spec_hash(spec)

            # --- (5) Resultado final
            final_result = {
                **spec,
                "model_used": self.model,
                "analysis_timestamp": None,
            }
            return final_result

        except Exception as e:
            return {
                "error": f"Image analysis failed: {str(e)}",
                "image_metadata": image_metadata if "image_metadata" in locals() else None,
            }

    def _preprocess_image(self, image: Image) -> dict[str, Any]:
        """Extrae metadata básica y pistas de layout. También calcula paleta preliminar."""
        try:
            if image is None:
                raise ValueError("Image is None")
            if not hasattr(image, "size"):
                raise ValueError("Invalid image")

            width, height = image.size
            # PIL -> OpenCV BGR
            img_bgr = self._pil_to_cv(image)

            # Paleta a hex con ratio
            palette = self._extract_palette_kmeans(img_bgr, k=5)

            # Layout hints simples
            layout_info = self._detect_basic_layout(img_bgr)

            memory_size = sys.getsizeof(image.tobytes())

            return {
                "image_meta": {"w": width, "h": height, "aspect_ratio": float(width) / float(height)},
                "palette_pre": palette,  # lista de {hex, ratio}
                "layout_hints": layout_info,  # total_elements / complexity
                "file_size": memory_size,
                "format": image.format or "unknown",
            }
        except Exception as e:
            return {"error": f"Image preprocessing failed: {str(e)}"}

    @staticmethod
    def _pil_to_cv(image: Image) -> np.ndarray:
        """PIL (RGB/RGBA/…) -> OpenCV BGR uint8"""
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        elif image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        arr = np.array(image)  # RGB o L
        if len(arr.shape) == 2:  # L -> BGR
            arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        else:
            # RGB -> BGR
            arr = arr[:, :, ::-1].copy()
        return arr

    @staticmethod
    def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        r, g, b = rgb
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _extract_palette_kmeans(self, img_bgr: np.ndarray, k: int = 5) -> List[Dict[str, float]]:
        """Devuelve paleta como [{'hex':'#rrggbb','ratio':0.xx}, ...]"""
        try:
            if img_bgr is None or img_bgr.size == 0:
                return []
            # Reducir tamaño para velocidad
            h, w = img_bgr.shape[:2]
            scale = 256 / max(h, w) if max(h, w) > 256 else 1.0
            if scale < 1.0:
                img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            data = img_bgr.reshape((-1, 3)).astype(np.float32)  # BGR
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            compactness, labels, centers = cv2.kmeans(data, k, None, criteria, 5, cv2.KMEANS_PP_CENTERS)

            centers = centers.astype(np.uint8)  # BGR
            counts = np.bincount(labels.flatten(), minlength=k).astype(float)
            ratios = (counts / counts.sum()).tolist()

            # Convertir a HEX (RGB)
            palette = []
            for i, c in enumerate(centers):
                b, g, r = int(c[0]), int(c[1]), int(c[2])
                palette.append({"hex": self._rgb_to_hex((r, g, b)), "ratio": float(ratios[i])})

            # Ordenar por ratio desc
            palette.sort(key=lambda x: x["ratio"], reverse=True)
            return palette
        except Exception as e:
            logger.warning(f"Palette kmeans failed: {e}")
            return []

    def _detect_basic_layout(self, img_bgr: np.ndarray) -> dict[str, Any]:
        """Detección simple de complejidad por contornos."""
        try:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            total_contours = len(contours)
            large_contours = [c for c in contours if cv2.contourArea(c) > 1000]
            return {
                "total_elements": total_contours,
                "major_elements": len(large_contours),
                "complexity": "high" if total_contours > 50 else "medium" if total_contours > 20 else "low",
            }
        except Exception:
            return {"complexity": "unknown"}

    def _encode_image_to_base64(self, image: Image) -> str:
        """Encode image to base64 for API transmission"""
        try:
            buffered = BytesIO()

            # Validate input
            if image is None:
                raise ValueError("Image cannot be None")
            if not hasattr(image, "mode") or not hasattr(image, "size"):
                raise ValueError("Invalid PIL Image object")
            if image.size[0] == 0 or image.size[1] == 0:
                raise ValueError("Image has invalid dimensions")

            # Handle different image modes
            try:
                if image.mode in ("RGBA", "LA", "P"):
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
            except Exception as e:
                logger.warning(f"Image mode conversion failed: {e}, attempting direct RGB conversion")
                image = image.convert("RGB")

            try:
                image.save(buffered, format="JPEG", quality=85, optimize=True)
            except Exception as e:
                logger.warning(f"JPEG save with optimization failed: {e}, trying without optimization")
                buffered = BytesIO()
                image.save(buffered, format="JPEG", quality=85)

            image_data = buffered.getvalue()
            if len(image_data) == 0:
                raise ValueError("No image data was generated")

            encoded_string = base64.b64encode(image_data).decode("utf-8")
            if not encoded_string:
                raise ValueError("Base64 encoding resulted in empty string")
            return encoded_string
        except Exception as e:
            logger.error(f"Failed to encode image to base64: {e}")
            raise ValueError(f"Image encoding failed: {str(e)}")
        finally:
            if "buffered" in locals():
                buffered.close()

    def _get_analysis_prompt_strict_json(self) -> str:
        """Prompt reforzado para minimizar alucinación (exige JSON estricto)."""
        suffix = REINFORCEMENT_PROMPT
        return f"{ANALYSIS_PROMPT}\n\n{suffix}"

    def _extract_components_from_text(self, text: str) -> list:
        """Extract UI components from text analysis when JSON parsing fails"""
        found_components = []
        text_lower = text.lower()
        for component in COMMON_COMPONENTS:
            if component in text_lower:
                found_components.append(component)
        return found_components if found_components else ["container", "content"]

    def _estimate_spacing_unit(self, img_bgr: np.ndarray) -> int:
        """Heurística simple: fallback a 8 si no se puede estimar."""
        try:
            # TODO: heurística real (distancias entre líneas). Por ahora:
            return 8
        except Exception:
            return 8

    def _try_ocr(self, image_pil: Image) -> str:
        """Intenta extraer texto con OCR si está disponible."""
        try:
            txt = pytesseract.image_to_string(image_pil)
            return (txt or "").strip()
        except Exception:
            return ""

    def _normalize_components(self, comps_raw: Any) -> List[Dict[str, Any]]:
        """Normaliza components asegurando campos requeridos."""
        norm: List[Dict[str, Any]] = []
        if isinstance(comps_raw, list):
            for idx, c in enumerate(comps_raw):
                if isinstance(c, dict):
                    _id = str(c.get("id") or f"cmp_{idx}")
                    _type = str(c.get("type") or "container")
                    bbox = c.get("bbox") or [0, 0, 0, 0]
                    if not (isinstance(bbox, list) and len(bbox) == 4):
                        bbox = [0, 0, 0, 0]
                    conf = float(c.get("confidence", 0.0))
                    ev = c.get("evidence") or {}
                    if not isinstance(ev, dict):
                        ev = {}
                    ev_ocr = ev.get("ocr") or ""
                    norm.append(
                        {
                            "id": _id,
                            "type": _type,
                            "bbox": [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])],
                            "confidence": max(0.0, min(1.0, conf)),
                            "evidence": {"ocr": str(ev_ocr)},
                        }
                    )
                elif isinstance(c, str):
                    # De _extract_components_from_text (fallbacks)
                    norm.append(
                        {
                            "id": f"cmp_{idx}",
                            "type": c,
                            "bbox": [0, 0, 0, 0],
                            "confidence": 0.3,
                            "evidence": {"ocr": ""},
                        }
                    )
        return norm

    def _build_spec(self, llm_obj: Dict[str, Any], image_metadata: Dict[str, Any], image_pil: Image) -> Dict[str, Any]:
        """Construye el spec final esperado por el guard: image_meta + palette + spacing_unit + components + layout/style."""
        image_meta = image_metadata.get("image_meta", {})
        w = int(image_meta.get("w") or image_pil.size[0])
        h = int(image_meta.get("h") or image_pil.size[1])

        # Paleta: usar la precomputada; si viene desde el LLM y es válida, se podría fusionar.
        palette_pre = image_metadata.get("palette_pre", [])
        palette = [{"hex": p.get("hex"), "ratio": float(p.get("ratio", 0.0))} for p in palette_pre if p.get("hex")]

        # Components normalizados
        components = self._normalize_components(llm_obj.get("components", []))

        # Evidence OCR global (opcional)
        ocr_global = self._try_ocr(image_pil)
        if ocr_global and components:
            # No sobrescribir si ya hay OCR a nivel componente
            for c in components:
                if not c.get("evidence", {}).get("ocr"):
                    c["evidence"]["ocr"] = ""

        # Layout/style
        layout = llm_obj.get("layout", "unknown")
        style = llm_obj.get("style", "modern")

        # spacing_unit
        spacing_unit = self._estimate_spacing_unit(self._pil_to_cv(image_pil))

        spec = {
            "image_meta": {"w": w, "h": h},
            "spacing_unit": int(spacing_unit),
            "palette": palette if palette else [{"hex": "#111111", "ratio": 1.0}],
            "components": (
                components
                if components
                else [
                    {
                        "id": "container_0",
                        "type": "container",
                        "bbox": [0, 0, w, h],
                        "confidence": 0.2,
                        "evidence": {"ocr": ""},
                    }
                ]
            ),
            "layout": layout,
            "style": style,
        }
        return spec

    @staticmethod
    def _canonical_dumps(obj: Dict[str, Any]) -> str:
        """JSON canónico para hashing estable (sin espacios, claves ordenadas)."""
        return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _compute_spec_hash(self, spec: Dict[str, Any]) -> str:
        """sha256 del spec canónico (ignorando campos no deterministas si hiciera falta)."""
        # Si querés excluir campos volátiles, hacelo acá (p.ej., recortar evidence.ocr largo).
        canonical = self._canonical_dumps(spec)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
