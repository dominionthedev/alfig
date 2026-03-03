<p align="center">
  <img src="assets/logo.svg" alt="Alfig" width="600"/>
</p>

<p align="center">
  <a href="https://github.com/dominionthedev/alfig/actions"><img src="https://img.shields.io/github/actions/workflow/status/dominionthedev/alfig/ci.yml?branch=main&label=CI&logo=github" alt="CI"></a>
  <a href="https://pypi.org/project/alfig/"><img src="https://img.shields.io/pypi/v/alfig?color=7C3AED" alt="PyPI"></a>
  <a href="https://pypi.org/project/alfig/"><img src="https://img.shields.io/pypi/pyversions/alfig?color=4F46E5" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0EA5E9" alt="License"></a>
</p>

<p align="center">
  A config library that lets you use <strong>TOML, JSON, YAML, and .conf files interchangeably</strong>,<br>
  with a single canonical schema, validation, and automatic format conversion.
</p>

---

## Install

```bash
pip install alfig
# With optional format support:
pip install alfig[yaml]   # adds PyYAML
pip install alfig[toml]   # adds tomli-w (for writing TOML)
pip install alfig[all]    # everything
```

> Python 3.11+ includes `tomllib` for reading TOML. For writing TOML, `tomli-w` is required.

---

## Quick Start

```python
from alfig import Alfig

# Define your schema once
schema = {
    "database": {
        "host": str,
        "port": int,
        "user": str,
        "password": (str, "secret"),   # (type, default)
    },
    "features": {
        "enable_logging": bool,
        "max_threads": (int, 4),
    },
}

# Create instance
config = Alfig(schema)

# Load from any supported format — auto-detected by extension
config.load("settings.yaml")   # or .json, .toml, .conf, .ini

# Validate against schema (fills in defaults for optional fields)
config.validate()

# Access values with dot-notation
db_host = config.get("database.host")
threads = config.get("features.max_threads")   # → 4 (default)

# Modify values
config.set("features.max_threads", 16)

# Save to any format
config.save("settings.json")
config.save("settings.toml")
config.save("settings.conf")
```

---

## Schema Reference

| Definition            | Meaning                        |
| --------------------- | ------------------------------ |
| `"field": str`        | Required string field          |
| `"field": int`        | Required int field             |
| `"field": bool`       | Required bool field            |
| `"field": float`      | Required float field           |
| `"field": list`       | Required list field            |
| `"field": dict`       | Required dict field            |
| `"field": (str, "x")` | Optional string, default `"x"` |
| `"field": (int, 0)`   | Optional int, default `0`      |
| `"section": {...}`    | Nested section                 |

---

## Supported Formats

| Format | Extension      | Read | Write | Notes                                                                 |
| ------ | -------------- | ---- | ----- | --------------------------------------------------------------------- |
| JSON   | `.json`        | ✓    | ✓     | Built-in                                                              |
| YAML   | `.yaml` `.yml` | ✓    | ✓     | Requires `PyYAML`                                                     |
| TOML   | `.toml`        | ✓    | ✓     | Read: `tomllib` (builtin 3.11+) / `tomli`; Write: `tomli-w` or `toml` |
| CONF   | `.conf` `.ini` | ✓    | ✓     | Custom parser (see below)                                             |

---

## CONF Format — Nested Sections

The `.conf` format uses **dot-notation section headers** for nesting:

```ini
# settings.conf

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
```

This maps to the same dict as the equivalent JSON:

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "enabled": true,
    "replica": {
      "host": "replica.local",
      "port": 5433
    }
  },
  "features": {
    "max_threads": 8,
    "tags": ["web", "api"]
  }
}
```

**Auto-coercion rules** (all CONF values are strings at parse time):

| Raw value        | Python type |
| ---------------- | ----------- |
| `true` / `false` | `bool`      |
| `42`             | `int`       |
| `3.14`           | `float`     |
| `["a", "b"]`     | `list`      |
| `{"x": 1}`       | `dict`      |
| everything else  | `str`       |

---

## API Reference

### `Alfig(schema=None)`

Create a config instance. `schema` is optional — omit it to skip validation.

### `.load(path, format=None)` → `self`

Load from a file. Format auto-detected from extension unless overridden.

### `.loads(text, format)` → `self`

Load from a raw string.

### `.load_dict(data)` → `self`

Load directly from a Python dict.

### `.validate()` → `self`

Validate against schema, filling defaults. Raises `ValidationError` on failure.

### `.get(key_path, default=None)` → value

Read a value with dot-notation: `config.get("database.host")`.

### `.set(key_path, value)` → `self`

Write a value with dot-notation. Creates intermediate dicts as needed.

### `.delete(key_path)` → `self`

Remove a key.

### `.as_dict()` → `dict`

Return a deep copy of the internal data.

### `.save(path, format=None)` → `self`

Save to a file. Format auto-detected from extension unless overridden.

### `.dumps(format)` → `str`

Serialize to a string in the given format.

### `Alfig.convert(input_path, output_path, ...)` (static)

Convert a file from one format to another without instantiating Alfig.

---

## CLI

```bash
# Convert between formats
alfig convert settings.toml --to json
alfig convert settings.yaml --to conf --out app.conf

# Validate / inspect a file
alfig validate settings.yaml
alfig validate settings.yaml --verbose   # prints parsed JSON

# Read a single value
alfig get settings.yaml database.host
```

---

## Project Structure

```
alfig/
├── __init__.py        # Public API
├── core.py            # Alfig class
├── schema.py          # Validation engine
├── cli.py             # CLI entry point
└── formats/
    ├── __init__.py    # Format registry
    ├── json_fmt.py
    ├── yaml_fmt.py
    ├── toml_fmt.py
    └── conf_fmt.py    # Custom nested INI parser
```
