"""
core.py — The main Alfig class.
"""

import copy
from typing import Any, Optional

from alfig import schema as schema_module
from alfig.formats import get_handler, detect_format


class AlfigError(Exception):
    """Base error for Alfig."""
    pass


class Alfig:
    """
    Unified config manager.

    Usage:
        config = Alfig(schema)
        config.load("settings.yaml")
        config.validate()
        db_host = config.get("database.host")
        config.set("features.max_threads", 16)
        config.save("settings.toml")
    """

    def __init__(self, schema: Optional[dict] = None):
        """
        Args:
            schema: Optional schema dict. If omitted, validation is skipped.
        """
        self._schema = schema
        self._data: dict = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, path: str, format: Optional[str] = None) -> "Alfig":
        """
        Load config from a file.

        Args:
            path:   Path to the config file.
            format: Force a specific format ('json', 'yaml', 'toml', 'conf').
                    If omitted, format is auto-detected from the file extension.
        """
        fmt = format or detect_format(path)
        handler = get_handler(fmt)
        self._data = handler.load(path)
        return self

    def loads(self, text: str, format: str) -> "Alfig":
        """
        Load config from a string.

        Args:
            text:   Raw config text.
            format: Format of the text ('json', 'yaml', 'toml', 'conf').
        """
        handler = get_handler(format)
        self._data = handler.loads(text)
        return self

    def load_dict(self, data: dict) -> "Alfig":
        """Load config directly from a Python dict."""
        self._data = copy.deepcopy(data)
        return self

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> "Alfig":
        """
        Validate the loaded config against the schema.
        Fills in default values for optional fields.
        Raises schema_module.ValidationError on failure.
        """
        if self._schema is None:
            return self
        self._data = schema_module.validate(self._data, self._schema)
        return self

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a config value using dot-notation.

        Args:
            key_path: Dot-separated path, e.g. "database.host"
            default:  Value to return if the key doesn't exist.
        """
        parts = key_path.split(".")
        node = self._data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key_path: str, value: Any) -> "Alfig":
        """
        Set a config value using dot-notation, creating intermediate dicts.

        Args:
            key_path: Dot-separated path, e.g. "features.max_threads"
            value:    The value to set.
        """
        parts = key_path.split(".")
        node = self._data
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        return self

    def delete(self, key_path: str) -> "Alfig":
        """Delete a key using dot-notation."""
        parts = key_path.split(".")
        node = self._data
        for part in parts[:-1]:
            if not isinstance(node, dict) or part not in node:
                return self
            node = node[part]
        node.pop(parts[-1], None)
        return self

    def as_dict(self) -> dict:
        """Return a deep copy of the internal config dict."""
        return copy.deepcopy(self._data)

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    def save(self, path: str, format: Optional[str] = None) -> "Alfig":
        """
        Save config to a file.

        Args:
            path:   Output file path.
            format: Target format. Auto-detected from extension if omitted.
        """
        fmt = format or detect_format(path)
        handler = get_handler(fmt)
        handler.dump(self._data, path)
        return self

    def dumps(self, format: str) -> str:
        """
        Serialize config to a string in the given format.

        Args:
            format: 'json', 'yaml', 'toml', or 'conf'.
        """
        handler = get_handler(format)
        return handler.dumps(self._data)

    # ------------------------------------------------------------------
    # Conversion helper (static)
    # ------------------------------------------------------------------

    @staticmethod
    def convert(input_path: str, output_path: str,
                input_format: Optional[str] = None,
                output_format: Optional[str] = None) -> None:
        """
        Convert a config file from one format to another.

        Args:
            input_path:    Source file.
            output_path:   Destination file.
            input_format:  Force source format (auto-detected if omitted).
            output_format: Force target format (auto-detected if omitted).
        """
        cfg = Alfig()
        cfg.load(input_path, format=input_format)
        cfg.save(output_path, format=output_format)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Alfig(keys={list(self._data.keys())})"

    def __contains__(self, key_path: str) -> bool:
        return self.get(key_path) is not None
