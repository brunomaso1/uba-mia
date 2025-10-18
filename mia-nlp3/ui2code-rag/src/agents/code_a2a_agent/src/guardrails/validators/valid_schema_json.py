import json
from typing import Any, Dict
import jsonschema

from guardrails.validators import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
    register_validator,
)


@register_validator(name="guardrails/valid_schema_json", data_type=["string", "object", "list"])
class ValidSchemaJson(Validator):
    """Validates that a value is parseable as valid JSON.

    **Key Properties**

    | Property                      | Description                       |
    | ----------------------------- | --------------------------------- |
    | Name for `format` attribute   | `guardrails/valid_json`           |
    | Supported data types          | `string`, `list`, `object`        |
    | Programmatic fix              | None                              |
    """  # noqa

    def __init__(self, json_schema: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.json_schema = json_schema

    def validate(self, value: Any, metadata: Dict = {}) -> ValidationResult:
        """Validates that a value is parseable as valid JSON and optionally validates against a JSON schema."""
        stringified = value
        parsed, error = (None, None)
        try:
            if not isinstance(value, str):
                stringified = json.dumps(value)

            parsed = json.loads(stringified)
        except json.decoder.JSONDecodeError as json_error:
            error = json_error
        except TypeError as type_error:
            error = type_error

        if error or not parsed:
            return FailResult(
                error_message=f"Value is not parseable as valid JSON! Reason: {str(error)}",
            )

        # If a JSON schema is provided, validate against it
        if self.json_schema:
            try:
                jsonschema.validate(instance=parsed, schema=self.json_schema)
            except Exception as schema_error:
                return FailResult(
                    error_message=f"JSON does not match schema! Reason: {str(schema_error)}",
                )

        return PassResult()
