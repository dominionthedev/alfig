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

from typing import Any

SUPPORTED_TYPES = (int, float, str, bool, list, dict)


class SchemaError(Exception):
    """Raised when the schema itself is malformed."""
    pass


class ValidationError(Exception):
    """Raised when config data doesn't match the schema."""
    pass


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


def validate(data: dict, schema: dict) -> dict:
    """
    Validate `data` against `schema`.
    Returns a new dict with defaults filled in.
    Raises ValidationError on failure.
    """
    if not isinstance(schema, dict):
        raise SchemaError("Schema must be a dict.")
    return _validate_node(data, schema)
