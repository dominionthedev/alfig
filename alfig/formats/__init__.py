"""Format registry — maps format names to their handler modules."""

from alfig.formats import json_fmt, yaml_fmt, toml_fmt, conf_fmt

_REGISTRY = {
    "json": json_fmt,
    "yaml": yaml_fmt,
    "yml": yaml_fmt,
    "toml": toml_fmt,
    "conf": conf_fmt,
    "ini": conf_fmt,
}

_EXTENSION_MAP = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".conf": "conf",
    ".ini": "ini",
}


def get_handler(fmt: str):
    fmt = fmt.lower()
    handler = _REGISTRY.get(fmt)
    if handler is None:
        raise ValueError(
            f"Unsupported format: '{fmt}'. "
            f"Supported formats: {', '.join(sorted(set(_REGISTRY.keys())))}"
        )
    return handler


def detect_format(path: str) -> str:
    """Detect format from file extension."""
    import os
    _, ext = os.path.splitext(path)
    fmt = _EXTENSION_MAP.get(ext.lower())
    if fmt is None:
        raise ValueError(
            f"Cannot detect format from extension '{ext}'. "
            "Please specify the format explicitly."
        )
    return fmt
