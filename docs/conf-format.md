# CONF Format Specification

Alfig's `.conf` / `.ini` format extends the classic INI syntax with **nested sections via dot-notation headers** and **automatic type coercion**. It is implemented entirely in `alfig/formats/conf_fmt.py` with no external dependencies.

---

## Syntax

### Comments

Lines starting with `#` or `;` are ignored. Inline comments are not supported.

```ini
# This is a comment
; This is also a comment
key = value   # this part after the value is NOT a comment — avoid it
```

---

### Root-level keys

Keys written before any section header belong to the root level of the config dict.

```ini
version = 1
name = myapp
```

Parses to:
```python
{"version": 1, "name": "myapp"}
```

---

### Sections

Section headers are written in square brackets. A section header creates a nested dict.

```ini
[server]
host = localhost
port = 8080
```

Parses to:
```python
{"server": {"host": "localhost", "port": 8080}}
```

---

### Nested sections

Nesting is expressed by **dot-separating section names**. There is no depth limit.

```ini
[server]
host = localhost

[server.tls]
enabled = true
cert = /etc/certs/server.crt

[server.tls.verify]
client = false
ca_bundle = /etc/certs/ca.crt
```

Parses to:
```python
{
    "server": {
        "host": "localhost",
        "tls": {
            "enabled": True,
            "cert": "/etc/certs/server.crt",
            "verify": {
                "client": False,
                "ca_bundle": "/etc/certs/ca.crt",
            }
        }
    }
}
```

> **Note:** You do not need to declare a parent section before a child. `[server.tls]` will create `server` automatically if it hasn't appeared yet.

---

## Type coercion

Since all raw INI values are strings, Alfig auto-coerces them to the most appropriate Python type using the following priority order:

| Raw value | Result | Python type |
|-----------|--------|-------------|
| `true` / `false` (case-insensitive) | `True` / `False` | `bool` |
| Valid JSON array: `[1, 2, 3]` | `[1, 2, 3]` | `list` |
| Valid JSON object: `{"x": 1}` | `{"x": 1}` | `dict` |
| Integer string: `42` | `42` | `int` |
| Float string: `3.14` | `3.14` | `float` |
| Quoted string: `"hello"` | `hello` | `str` (quotes stripped) |
| Anything else | `"value"` | `str` |

### Examples

```ini
[types]
a_bool    = true
a_neg     = false
an_int    = 42
a_float   = 3.14
a_string  = hello world
a_quoted  = "hello world"
a_list    = ["one", "two", "three"]
an_object = {"key": "value", "n": 1}
```

---

## Serialization

When writing `.conf` files, Alfig:

- Recursively flattens nested dicts into dot-notation sections
- Writes scalars as their string representation
- Writes `bool` as `true` / `false`
- Writes `list` and `dict` as compact JSON (`["a","b"]`)
- Separates sections with a blank line

### Round-trip guarantee

Any dict that can be expressed in the CONF format will survive a parse → serialize → parse cycle unchanged:

```python
from alfig.formats import conf_fmt

data = conf_fmt.loads(text)
assert conf_fmt.loads(conf_fmt.dumps(data)) == data
```

---

## Limitations

- No multi-line values (use JSON lists for arrays)
- No inline comments (everything after `=` is the value)
- Dict values must be valid JSON when written inline (complex nested structures should use sub-sections instead)
- Section names must not contain `=` or `[` `]`
