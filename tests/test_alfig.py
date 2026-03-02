"""Tests for Alfig."""

import json
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alfig import Alfig, ValidationError, SchemaError
from alfig.formats import conf_fmt

# -----------------------------------------------------------------------
# Schema validation tests
# -----------------------------------------------------------------------

SCHEMA = {
    "database": {
        "host": str,
        "port": int,
        "user": str,
        "password": (str, "secret"),
    },
    "features": {
        "enable_logging": bool,
        "max_threads": (int, 4),
    },
}


def test_validate_valid_data():
    cfg = Alfig(SCHEMA)
    cfg.load_dict({
        "database": {"host": "localhost", "port": 5432, "user": "admin"},
        "features": {"enable_logging": True},
    })
    cfg.validate()
    assert cfg.get("database.port") == 5432
    assert cfg.get("database.password") == "secret"   # default filled
    assert cfg.get("features.max_threads") == 4        # default filled


def test_validate_missing_required():
    cfg = Alfig(SCHEMA)
    cfg.load_dict({
        "database": {"port": 5432},  # missing host and user
        "features": {"enable_logging": True},
    })
    with pytest.raises(ValidationError, match="host"):
        cfg.validate()


def test_validate_wrong_type():
    cfg = Alfig(SCHEMA)
    cfg.load_dict({
        "database": {"host": "localhost", "port": "not-a-number", "user": "x"},
        "features": {"enable_logging": True},
    })
    with pytest.raises(ValidationError, match="port"):
        cfg.validate()


def test_validate_bool_not_int():
    """bool must not be accepted where int is expected."""
    cfg = Alfig(SCHEMA)
    cfg.load_dict({
        "database": {"host": "h", "port": True, "user": "u"},
        "features": {"enable_logging": True},
    })
    with pytest.raises(ValidationError, match="port"):
        cfg.validate()


# -----------------------------------------------------------------------
# get / set / delete
# -----------------------------------------------------------------------

def test_get_set():
    cfg = Alfig()
    cfg.load_dict({"a": {"b": {"c": 42}}})
    assert cfg.get("a.b.c") == 42
    cfg.set("a.b.c", 99)
    assert cfg.get("a.b.c") == 99


def test_set_creates_intermediaries():
    cfg = Alfig()
    cfg.load_dict({})
    cfg.set("x.y.z", "hello")
    assert cfg.get("x.y.z") == "hello"


def test_get_missing_returns_default():
    cfg = Alfig()
    cfg.load_dict({})
    assert cfg.get("nope.nope", "fallback") == "fallback"


def test_delete():
    cfg = Alfig()
    cfg.load_dict({"a": 1, "b": 2})
    cfg.delete("a")
    assert cfg.get("a") is None
    assert cfg.get("b") == 2


# -----------------------------------------------------------------------
# JSON round-trip
# -----------------------------------------------------------------------

def test_json_roundtrip(tmp_path):
    data = {"server": {"host": "0.0.0.0", "port": 8080}, "debug": True}
    cfg = Alfig()
    cfg.load_dict(data)
    out = tmp_path / "out.json"
    cfg.save(str(out))
    cfg2 = Alfig()
    cfg2.load(str(out))
    assert cfg2.as_dict() == data


def test_json_dumps():
    cfg = Alfig()
    cfg.load_dict({"x": 1})
    text = cfg.dumps("json")
    assert json.loads(text) == {"x": 1}


# -----------------------------------------------------------------------
# CONF format — unit tests for our custom parser
# -----------------------------------------------------------------------

SAMPLE_CONF = """\
[database]
host = localhost
port = 5432
enabled = true

[database.replica]
host = replica.local
port = 5433

[features]
max_threads = 8
tags = ["web", "api"]
"""


def test_conf_loads_nested():
    data = conf_fmt.loads(SAMPLE_CONF)
    assert data["database"]["host"] == "localhost"
    assert data["database"]["port"] == 5432
    assert data["database"]["enabled"] is True
    assert data["database"]["replica"]["host"] == "replica.local"
    assert data["database"]["replica"]["port"] == 5433
    assert data["features"]["max_threads"] == 8
    assert data["features"]["tags"] == ["web", "api"]


def test_conf_roundtrip():
    data = conf_fmt.loads(SAMPLE_CONF)
    serialized = conf_fmt.dumps(data)
    reparsed = conf_fmt.loads(serialized)
    assert reparsed == data


def test_conf_bool_coercion():
    text = "[s]\na = true\nb = false\n"
    d = conf_fmt.loads(text)
    assert d["s"]["a"] is True
    assert d["s"]["b"] is False


def test_conf_list_coercion():
    text = '[s]\nitems = [1, 2, 3]\n'
    d = conf_fmt.loads(text)
    assert d["s"]["items"] == [1, 2, 3]


def test_conf_comments_ignored():
    text = "# this is a comment\n[s]\n; also a comment\nkey = val\n"
    d = conf_fmt.loads(text)
    assert d["s"]["key"] == "val"


def test_conf_root_keys():
    text = "version = 1\nname = myapp\n"
    d = conf_fmt.loads(text)
    assert d["version"] == 1
    assert d["name"] == "myapp"


# -----------------------------------------------------------------------
# YAML round-trip (skipped if PyYAML not installed)
# -----------------------------------------------------------------------

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_yaml_roundtrip(tmp_path):
    data = {"app": {"name": "test", "version": 2}, "debug": False}
    cfg = Alfig()
    cfg.load_dict(data)
    out = tmp_path / "out.yaml"
    cfg.save(str(out))
    cfg2 = Alfig()
    cfg2.load(str(out))
    assert cfg2.as_dict() == data


# -----------------------------------------------------------------------
# convert() static method
# -----------------------------------------------------------------------

def test_convert_json_to_conf(tmp_path):
    src = tmp_path / "src.json"
    src.write_text(json.dumps({"database": {"host": "localhost", "port": 5432}}))
    dst = tmp_path / "dst.conf"
    Alfig.convert(str(src), str(dst))
    reparsed = conf_fmt.load(str(dst))
    assert reparsed["database"]["host"] == "localhost"
    assert reparsed["database"]["port"] == 5432
