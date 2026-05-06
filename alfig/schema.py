"""
Schema validation and default handling for Alfig.

Schema format:
    {
        "field": type,
        "field": (type, default_value),
        "section": {
            "field": type,
            "field": (type, default_value),
        }
    }
"""

import json
from typing import Any, Optional, Union
import jsonschema

SUPPORTED_TYPES = (int, float, str, bool, list, dict)


class SchemaError(Exception):
    """Raised when the schema itself is malformed."""
    pass


class ValidationError(Exception):
    """Raised when config data doesn't match the schema."""
    pass


class Schema:
    """
    Schema model for Alfig.
    Supports both the original Alfig dictionary schema and JSON schema.
    """

    def __init__(self, schema_def: Union[dict, str]):
        """
        Initialize the Schema.
        Args:
            schema_def: Either a dictionary (Alfig schema or JSON schema)
                        or a path to a JSON schema file.
        """
        self.raw_schema = schema_def
        self.is_json_schema = False

        if isinstance(schema_def, str):
            with open(schema_def, 'r') as f:
                self.schema_dict = json.load(f)
            self.is_json_schema = True
        elif isinstance(schema_def, dict):
            self.schema_dict = schema_def
            # Basic heuristic to detect JSON schema
            if "$schema" in schema_def or "type" in schema_def and isinstance(schema_def["type"], str):
                 self.is_json_schema = True
        else:
            raise SchemaError("Schema must be a dict or a path to a JSON schema file.")

    def validate(self, data: dict) -> dict:
        """
        Validate data against the schema.
        Returns a new dict with defaults filled in.
        """
        if self.is_json_schema:
            try:
                # jsonschema doesn't fill defaults by default
                # We'll use a validator that does if needed, but for now just validate
                jsonschema.validate(instance=data, schema=self.schema_dict)
                # Note: filling defaults with jsonschema is tricky,
                # might need a custom validator or just return data as is for now.
                return data
            except jsonschema.ValidationError as e:
                raise ValidationError(str(e))
        else:
            return _validate_node(data, self.schema_dict)


def _parse_field(field_def) -> tuple[type, bool, Any]:
    """
    Returns (expected_type, has_default, default_value).
    """
    if isinstance(field_def, type):
        if field_def not in SUPPORTED_TYPES:
            raise SchemaError(f"Unsupported type in schema: {field_def}")
        return field_def, False, None

    if isinstance(field_def, tuple):
        if len(field_def) != 2 or not isinstance(field_def[0], type):
            raise SchemaError(
                f"Tuple schema fields must be (type, default): got {field_def}"
            )
        typ, default = field_def
        if typ not in SUPPORTED_TYPES:
            raise SchemaError(f"Unsupported type in schema: {typ}")
        # Type check the default itself
        if default is not None and not isinstance(default, typ):
            raise SchemaError(
                f"Default value {default!r} doesn't match declared type {typ}"
            )
        return typ, True, default

    raise SchemaError(
        f"Invalid schema field definition: {field_def!r}. "
        "Expected a type or (type, default) tuple."
    )


def _validate_node(data: dict, schema: dict, path: str = "") -> dict:
    """
    Recursively validates and fills defaults into `data` against `schema`.
    Returns the completed data dict.
    """
    result = {}

    for key, field_def in schema.items():
        full_key = f"{path}.{key}" if path else key

        # Nested section
        if isinstance(field_def, dict):
            sub_data = data.get(key, {})
            if not isinstance(sub_data, dict):
                raise ValidationError(
                    f"'{full_key}' should be a section (dict), got {type(sub_data).__name__}"
                )
            result[key] = _validate_node(sub_data, field_def, full_key)
            continue

        expected_type, has_default, default = _parse_field(field_def)

        if key not in data:
            if has_default:
                result[key] = default
                continue
            else:
                raise ValidationError(f"Required field '{full_key}' is missing.")

        value = data[key]

        # bool must come before int — bool is a subclass of int in Python,
        # so we must explicitly reject bool when int is expected (and vice versa).
        if expected_type is bool:
            if not isinstance(value, bool):
                raise ValidationError(
                    f"'{full_key}' must be bool, got {type(value).__name__}: {value!r}"
                )
        elif expected_type is int and isinstance(value, bool):
            raise ValidationError(
                f"'{full_key}' must be int, got bool: {value!r}"
            )
        elif not isinstance(value, expected_type):
            raise ValidationError(
                f"'{full_key}' must be {expected_type.__name__}, "
                f"got {type(value).__name__}: {value!r}"
            )

        result[key] = value

    # Warn about extra keys not in schema (non-fatal, just pass them through)
    for key in data:
        if key not in schema:
            result[key] = data[key]

    return result


def validate(data: dict, schema: Union[dict, Schema]) -> dict:
    """
    Validate `data` against `schema`.
    Returns a new dict with defaults filled in.
    Raises ValidationError on failure.
    """
    if isinstance(schema, Schema):
        return schema.validate(data)

    if not isinstance(schema, dict):
        raise SchemaError("Schema must be a dict or a Schema instance.")

    return _validate_node(data, schema)
