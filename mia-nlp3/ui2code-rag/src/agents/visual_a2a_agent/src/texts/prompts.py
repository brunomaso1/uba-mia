ANALYSIS_PROMPT = """
Analiza esta imagen de diseño de interfaz de usuario. Identifica y describe:

1. Componentes principales (header, navbar, buttons, forms, cards, etc.)
2. Layout y estructura (grid, flexbox, columnas, filas)
3. Estilo visual (colores, tipografía, spacing, sombras)
4. Elementos interactivos (botones, enlaces, campos de entrada)

IMPORTANTE: 
- Describe la FUNCIÓN de los elementos, no íconos específicos
- Enfócate en la estructura y organización
- Identifica patrones de diseño comunes

Responde en formato JSON válido:
{
    "components": ["lista", "de", "componentes", "identificados"],
    "layout": "descripción del sistema de layout (grid, flexbox, etc.)",
    "style": "descripción del estilo visual",
    "color_scheme": "esquema de colores dominante",
    "typography": "características tipográficas",
    "interactive_elements": ["lista", "de", "elementos", "interactivos"],
    "design_patterns": ["patrones", "de", "diseño", "identificados"],
    "analysis_text": "descripción detallada y completa para búsqueda RAG - incluye todos los detalles técnicos y estructurales que podrían ser útiles para encontrar ejemplos similares de código HTML/CSS"
}
"""

REINFORCEMENT_PROMPT = """
Respond ONLY with a single JSON object. No prose, no markdown, no backticks.
JSON shape (min):
{
  "components": [
    {
      "id": "string",
      "type": "button|navbar|card|image|text|input|icon|container|…",
      "bbox": [x,y,w,h],
      "confidence": 0.0_to_1.0,
      "evidence": { "ocr": "string or empty" }
    }
  ],
  "layout": "grid|flex|unknown",
  "style": "modern|classic|…"
}
Rules:
- Do not invent components. If unsure, omit it or set low confidence.
- Copy textual content into evidence.ocr (use what you can read).
- bbox must be integers [x,y,w,h] in image pixel coordinates.
"""
