"""
Custom CONF/INI format handler for Alfig.

Nesting strategy:
    Sections use dot-notation to represent hierarchy.

    [database]
    host = localhost
    port = 5432

    [database.replica]
    host = replica.local
    port = 5433

    [features]
    enable_logging = true
    tags = ["web", "api"]

This maps to:
    {
        "database": {
            "host": "localhost",
            "port": 5432,
            "replica": {
                "host": "replica.local",
                "port": 5433,
            }
        },
        "features": {
            "enable_logging": True,
            "tags": ["web", "api"],
        }
    }

Type coercion:
    Since INI values are always strings, we auto-coerce:
      - "true" / "false"  → bool
      - integer strings   → int
      - float strings     → float
      - JSON arrays/dicts → list / dict
      - everything else   → str
"""

import json
import re
from typing import Any


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------

def _coerce(value: str) -> Any:
    """Auto-coerce a raw string value to the best Python type."""
    stripped = value.strip()

    # Bool
    if stripped.lower() == "true":
        return True
    if stripped.lower() == "false":
        return False

    # JSON list or dict (must start with [ or {)
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

    # Int
    try:
        return int(stripped)
    except ValueError:
        pass

    # Float
    try:
        return float(stripped)
    except ValueError:
        pass

    # Quoted string — strip surrounding quotes
    if (stripped.startswith('"') and stripped.endswith('"')) or \
       (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]

    return stripped


def _serialize(value: Any) -> str:
    """Serialize a Python value back to a conf-compatible string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _set_nested(data: dict, key_path: list[str], value: Any) -> None:
    """Set a value deep inside a nested dict given a key path."""
    node = data
    for part in key_path[:-1]:
        node = node.setdefault(part, {})
    node[key_path[-1]] = value


def _get_nested(data: dict, key_path: list[str]) -> dict:
    """Navigate to a nested dict, creating intermediaries as needed."""
    node = data
    for part in key_path:
        node = node.setdefault(part, {})
    return node


def loads(text: str) -> dict:
    """Parse a CONF-format string into a nested dict."""
    result: dict = {}
    current_section_path: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        # Skip blanks and comments
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        # Section header: [some.nested.section]
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            current_section_path = [part.strip() for part in section_name.split(".")]
            # Ensure the section dict exists
            _get_nested(result, current_section_path)
            continue

        # Key = value
        if "=" in line:
            key, _, raw_value = line.partition("=")
            key = key.strip()
            value = _coerce(raw_value.strip())

            if current_section_path:
                node = _get_nested(result, current_section_path)
                node[key] = value
            else:
                result[key] = value
            continue

    return result


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return loads(f.read())


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _flatten_sections(data: dict, prefix: list[str] = None) -> list[tuple[list[str], dict]]:
    """
    Walk a nested dict and return a list of (section_path, flat_key_values).
    Root-level scalar keys are collected under an empty path.
    """
    prefix = prefix or []
    scalars = {}
    sections = []

    for key, value in data.items():
        if isinstance(value, dict):
            # Recurse into nested section
            sub_sections = _flatten_sections(value, prefix + [key])
            sections.extend(sub_sections)
        else:
            scalars[key] = value

    # Scalars at this level form a "section"
    if scalars or not sections:
        sections.insert(0, (prefix, scalars))

    return sections


def dumps(data: dict) -> str:
    lines = []
    sections = _flatten_sections(data)

    for section_path, kvs in sections:
        if section_path:
            lines.append(f"[{'.'.join(section_path)}]")
        
        for key, value in kvs.items():
            lines.append(f"{key} = {_serialize(value)}")

        lines.append("")  # blank line between sections

    return "\n".join(lines).rstrip() + "\n"


def dump(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(dumps(data))
