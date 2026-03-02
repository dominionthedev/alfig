"""YAML format handler. Requires PyYAML."""

try:
    import yaml
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def _check():
    if not _AVAILABLE:
        raise ImportError(
            "PyYAML is required for YAML support. Install it with: pip install pyyaml"
        )


def load(path: str) -> dict:
    _check()
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def loads(text: str) -> dict:
    _check()
    return yaml.safe_load(text) or {}


def dump(data: dict, path: str) -> None:
    _check()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def dumps(data: dict) -> str:
    _check()
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)
