# API Reference

## `Alfig` class

```python
from alfig import Alfig
```

The main interface. All mutating methods return `self` for chaining.

---

### Constructor

```python
Alfig(schema: dict | None = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `schema`  | `dict \| None` | Optional schema dict. If `None`, `.validate()` is a no-op. |

---

### Loading

#### `.load(path, format=None)` → `self`

Load config from a file. Format is auto-detected from the file extension unless overridden.

```python
config.load("settings.yaml")
config.load("settings.toml")
config.load("settings.conf")
config.load("data.cfg", format="conf")   # force format
```

**Supported extensions:** `.json`, `.yaml`, `.yml`, `.toml`, `.conf`, `.ini`

---

#### `.loads(text, format)` → `self`

Load config from a raw string.

```python
config.loads('{"host": "localhost"}', format="json")
config.loads("[server]\nhost = localhost", format="conf")
```

---

#### `.load_dict(data)` → `self`

Load config from a Python `dict`. The dict is deep-copied internally.

```python
config.load_dict({"server": {"host": "localhost", "port": 8080}})
```

---

### Validation

#### `.validate()` → `self`

Validate the loaded config against the schema. Fills in default values for optional fields. Raises `ValidationError` if any field fails.

```python
config.validate()   # raises ValidationError if invalid
```

If no schema was provided at construction, this is a no-op and returns `self`.

---

### Accessors

#### `.get(key_path, default=None)` → `Any`

Read a value using dot-notation.

```python
host = config.get("database.host")
port = config.get("database.port", 5432)   # default if missing
deep = config.get("a.b.c.d")
```

Returns `default` (default: `None`) if any part of the path is missing.

---

#### `.set(key_path, value)` → `self`

Write a value using dot-notation. Creates intermediate `dict`s as needed.

```python
config.set("database.host", "prod.db")
config.set("features.flags.dark_mode", True)   # creates intermediate dicts
```

---

#### `.delete(key_path)` → `self`

Delete a key. Silent no-op if the key doesn't exist.

```python
config.delete("features.legacy_flag")
```

---

#### `.as_dict()` → `dict`

Return a deep copy of the entire internal config as a plain Python dict.

```python
data = config.as_dict()
```

---

#### `key_path in config`

Check existence of a key using `in`.

```python
if "database.host" in config:
    ...
```

---

### Saving

#### `.save(path, format=None)` → `self`

Save config to a file. Format is auto-detected from the extension unless overridden.

```python
config.save("out.json")
config.save("out.toml")
config.save("out.conf")
config.save("output", format="yaml")   # no extension? force it
```

---

#### `.dumps(format)` → `str`

Serialize config to a string without writing to disk.

```python
json_text = config.dumps("json")
yaml_text = config.dumps("yaml")
conf_text = config.dumps("conf")
toml_text = config.dumps("toml")
```

---

### Static helpers

#### `Alfig.convert(input_path, output_path, input_format=None, output_format=None)`

Convert a config file from one format to another without instantiating `Alfig`.

```python
Alfig.convert("settings.toml", "settings.json")
Alfig.convert("data.cfg", "data.yaml", input_format="conf")
```

---

## `schema` module

```python
from alfig.schema import validate, ValidationError, SchemaError
```

### Schema syntax

| Syntax | Meaning |
|--------|---------|
| `"field": str` | Required `str` field |
| `"field": int` | Required `int` field |
| `"field": float` | Required `float` field |
| `"field": bool` | Required `bool` field |
| `"field": list` | Required `list` field |
| `"field": dict` | Required `dict` field |
| `"field": (str, "default")` | Optional `str`, default `"default"` |
| `"field": (int, 0)` | Optional `int`, default `0` |
| `"section": {...}` | Nested section (recursive) |

### `validate(data, schema)` → `dict`

Validates `data` against `schema`. Returns a new dict with defaults filled in. Raises `ValidationError` on any failure.

```python
from alfig.schema import validate

result = validate(
    {"host": "localhost", "port": 5432},
    {"host": str, "port": int, "debug": (bool, False)},
)
# result == {"host": "localhost", "port": 5432, "debug": False}
```

---

## Exceptions

| Exception | Module | When |
|-----------|--------|------|
| `ValidationError` | `alfig.schema` | Config data fails schema validation |
| `SchemaError` | `alfig.schema` | The schema definition itself is invalid |
| `AlfigError` | `alfig.core` | Base error class |

---

## Formats

| Format | Handler | Notes |
|--------|---------|-------|
| `json` | `alfig.formats.json_fmt` | Built-in `json` module, no dependencies |
| `yaml` | `alfig.formats.yaml_fmt` | Requires `PyYAML` |
| `toml` | `alfig.formats.toml_fmt` | Read: `tomllib` (3.11+ built-in) or `tomli`; Write: `tomli-w` or `toml` |
| `conf` | `alfig.formats.conf_fmt` | Custom parser, no dependencies |

You can use format handlers directly if needed:

```python
from alfig.formats import conf_fmt

data = conf_fmt.loads("[section]\nkey = value")
text = conf_fmt.dumps({"section": {"key": "value"}})
```
