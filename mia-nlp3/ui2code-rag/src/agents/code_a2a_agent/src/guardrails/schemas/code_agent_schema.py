# src/agents/code_agent/src/guardrails/schemas/code_agent_schema.py
"""
JSON Schema de salida del Code Agent.

Objetivo:
- Validar que el agente devuelva HTML no vacío.
- Incluir metadatos de generación (modelo, patrones, etc.).
- Propagar un resumen del análisis visual (para trazabilidad).
- Ser tolerante a casos donde no haya componentes detectados (listas vacías).
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        # Debe existir y no ser vacío. Si tu generación falla, poné un fallback antes de validar.
        "html_code": {"type": "string", "minLength": 1},

        # Metadatos de la generación del Code Agent
        "generation_metadata": {
            "type": "object",
            "properties": {
                "model_used": {"type": "string"},
                "patterns_used": {"type": "integer"},
                # Lista de nombres de componentes visuales usados (strings). Permitimos vacío.
                "visual_components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                },
                "custom_instructions": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                # Campo opcional para propagar errores/avisos no fatales
                "error": {"type": "string"},
            },
            "required": [
                "model_used",
                "patterns_used",
                "visual_components",
                "custom_instructions",
                "timestamp",
            ],
            "additionalProperties": True,
        },

        # Resumen del análisis visual (para trazabilidad hacia el Visual Agent)
        "visual_analysis_summary": {
            "type": "object",
            "properties": {
                # Acepta array de strings u objetos, y permitimos vacío.
                "components": {
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "array", "items": {"type": "object"}},
                    ],
                    "default": [],
                },
                "layout": {"type": "string"},
                "style": {"type": "string"},
            },
            "required": ["components", "layout", "style"],
            "additionalProperties": True,
        },

        # Campos auxiliares opcionales para depuración/telemetría
        "status": {"type": "string"},
        "missing": {"type": "array", "items": {"type": "string"}},
        "used_component_ids": {"type": "array", "items": {"type": "string"}},
        "hash": {"type": "string"},
    },

    # Campos mínimos obligatorios de la salida del Code Agent
    "required": ["html_code", "generation_metadata", "visual_analysis_summary"],

    # Permitimos campos adicionales por si querés extender sin romper validaciones
    "additionalProperties": True,
}
