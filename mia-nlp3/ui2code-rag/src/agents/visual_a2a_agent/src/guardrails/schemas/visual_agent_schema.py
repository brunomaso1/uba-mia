# src/agents/visual_agent/src/guardrails/schemas/visual_agent_schema.py

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "components": {
            "oneOf": [
                {"type": "array", "items": {"type": "string"}},
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string"},
                            "bbox": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 4,
                                "maxItems": 4,
                            },
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "evidence": {
                                "type": "object",
                                "properties": {"ocr": {"type": "string"}},
                                "additionalProperties": True,
                            },
                        },
                        "required": ["id", "type"],
                        "additionalProperties": True,
                    },
                },
            ]
        },

        "layout": {"type": "string"},
        "style": {"type": "string"},
        "analysis_text": {"type": "string"},  # <- opcional

        # Soportar forma corta actual
        "image_meta": {
            "type": "object",
            "properties": {
                "w": {"type": "integer", "minimum": 1},
                "h": {"type": "integer", "minimum": 1},
            },
            "required": ["w", "h"],
            "additionalProperties": True,
        },

        # Y la forma extendida
        "image_metadata": {
            "type": "object",
            "properties": {
                "dimensions": {"type": "object"},
                "dominant_colors": {"type": "array", "items": {}},
                "layout_hints": {"type": "object"},
                "file_size": {"type": "integer"},
                "format": {"type": "string"},
            },
            "required": ["dimensions", "dominant_colors", "layout_hints", "file_size", "format"],
            "additionalProperties": True,
        },

        "model_used": {"type": "string"},
        "analysis_timestamp": {"type": ["string", "null"]},

        # Extras
        "spacing_unit": {"type": "integer"},
        "palette": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"hex": {"type": "string"}, "ratio": {"type": "number"}},
                "required": ["hex"],
                "additionalProperties": True,
            },
        },
        "hash": {"type": "string"},
    },

    "required": ["components", "layout", "style", "model_used", "analysis_timestamp"],

    "anyOf": [
        {"required": ["image_meta"]},
        {"required": ["image_metadata"]},
    ],

    "additionalProperties": True,
}
