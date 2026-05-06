"""
core.py — The main Alfig class.
"""

import copy
import os
import re
from typing import Any, Optional, Union

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

    def __init__(self, schema: Optional[Union[dict, schema_module.Schema]] = None):
        """
        Args:
            schema: Optional schema dict or Schema instance. If omitted, validation is skipped.
        """
        if schema is not None and not isinstance(schema, schema_module.Schema) and isinstance(schema, dict):
             # Try to wrap dict schema in Schema model for consistency, but keep it as dict if it's the old style for now
             # Actually, let's always wrap it if it's not None
             self._schema = schema_module.Schema(schema)
        else:
             self._schema = schema
        self._data: dict = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, path: str, format: Optional[str] = None, merge: bool = False) -> "Alfig":
        """
        Load config from a file.

        Args:
            path:   Path to the config file.
            format: Force a specific format ('json', 'yaml', 'toml', 'conf').
                    If omitted, format is auto-detected from the file extension.
            merge:  If True, merge the loaded data with existing data instead of overwriting.
        """
        fmt = format or detect_format(path)
        handler = get_handler(fmt)
        new_data = handler.load(path)

        if merge:
            self._data = self._deep_merge(self._data, new_data)
        else:
            self._data = new_data
        return self

    def _deep_merge(self, base: dict, overlay: dict) -> dict:
        """Deeply merge two dictionaries."""
        for key, value in overlay.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = copy.deepcopy(value)
        return base

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

    def load_dict(self, data: dict, merge: bool = False) -> "Alfig":
        """
        Load config directly from a Python dict.

        Args:
            data:  The dictionary to load.
            merge: If True, merge the loaded data with existing data instead of overwriting.
        """
        if merge:
            self._data = self._deep_merge(self._data, data)
        else:
            self._data = copy.deepcopy(data)
        return self

    def load_env(self, prefix: str = "ALFIG_") -> "Alfig":
        """
        Load config values from environment variables.
        Expected format: PREFIX_SECTION_KEY=value
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_path = key[len(prefix):].lower().replace("__", ".")
                # Try to coerce value
                self.set(config_path, self._coerce_env_value(value))
        return self

    def _coerce_env_value(self, value: str) -> Any:
        """Try to coerce environment variable string to a Python type."""
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def interpolate(self) -> "Alfig":
        """
        Perform environment variable interpolation on all string values in the config.
        Format: ${VAR} or ${VAR:default}
        """
        self._data = self._interpolate_node(self._data)
        return self

    def _interpolate_node(self, node: Any) -> Any:
        if isinstance(node, dict):
            return {k: self._interpolate_node(v) for k, v in node.items()}
        if isinstance(node, list):
            return [self._interpolate_node(i) for i in node]
        if isinstance(node, str):
            return self._interpolate_str(node)
        return node

    def _interpolate_str(self, value: str) -> str:
        pattern = re.compile(r"\$\{(\w+)(?::([^}]+))?\}")

        def replace(match):
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default if default is not None else match.group(0))

        return pattern.sub(replace, value)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> "Alfig":
        """
        Validate the loaded config against the schema.
        Fills in default values for optional fields (for Alfig schema).
        Raises schema_module.ValidationError on failure.
        """
        if self._schema is None:
            return self

        if isinstance(self._schema, schema_module.Schema):
            self._data = self._schema.validate(self._data)
        else:
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
