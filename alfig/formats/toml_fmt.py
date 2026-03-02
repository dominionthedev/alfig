"""TOML format handler. Uses tomllib (Python 3.11+) or tomli as fallback."""

try:
    import tomllib
    _READ_LIB = "tomllib"
except ImportError:
    try:
        import tomli as tomllib
        _READ_LIB = "tomli"
    except ImportError:
        tomllib = None
        _READ_LIB = None

try:
    import tomli_w
    _WRITE_LIB = "tomli_w"
except ImportError:
    try:
        import toml
        _WRITE_LIB = "toml"
    except ImportError:
        _WRITE_LIB = None


def _check_read():
    if tomllib is None:
        raise ImportError(
            "A TOML read library is required. On Python < 3.11 install: pip install tomli"
        )


def _check_write():
    if _WRITE_LIB is None:
        raise ImportError(
            "A TOML write library is required. Install one of: pip install tomli-w  OR  pip install toml"
        )


def load(path: str) -> dict:
    _check_read()
    with open(path, "rb") as f:
        return tomllib.load(f)


def loads(text: str) -> dict:
    _check_read()
    if hasattr(tomllib, "loads"):
        return tomllib.loads(text)
    return tomllib.load(__import__("io").BytesIO(text.encode()))


def dump(data: dict, path: str) -> None:
    _check_write()
    if _WRITE_LIB == "tomli_w":
        import tomli_w
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
    else:
        import toml
        with open(path, "w", encoding="utf-8") as f:
            toml.dump(data, f)


def dumps(data: dict) -> str:
    _check_write()
    if _WRITE_LIB == "tomli_w":
        import tomli_w
        return tomli_w.dumps(data)
    else:
        import toml
        return toml.dumps(data)
