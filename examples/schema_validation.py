"""
examples/schema_validation.py
==============================
Demonstrates schema validation: required fields, defaults,
type checking, nested sections, and SchemaError for bad schemas.
"""

from alfig import Alfig, ValidationError, SchemaError

# ── Schema definition ─────────────────────────────────────────────────
schema = {
    "service": {
        "name": str,                     # required
        "port": int,                     # required
        "debug": (bool, False),          # optional, default False
        "workers": (int, 2),             # optional, default 2
    },
    "cache": {
        "backend": str,                  # required
        "ttl_seconds": (int, 300),       # optional, default 300
        "options": {
            "max_size": (int, 1000),
            "eviction": (str, "lru"),
        },
    },
}


def try_load(label: str, data: dict):
    print(f"\n── {label} {'─' * (50 - len(label))}")
    try:
        cfg = Alfig(schema)
        cfg.load_dict(data)
        cfg.validate()
        print("  ✓ Valid!")
        print(f"    workers  = {cfg.get('service.workers')}")
        print(f"    ttl      = {cfg.get('cache.ttl_seconds')}")
        print(f"    eviction = {cfg.get('cache.options.eviction')}")
    except ValidationError as e:
        print(f"  ✗ ValidationError: {e}")


# ── Case 1: Fully valid, all optional fields use defaults
try_load("All defaults", {
    "service": {"name": "myapp", "port": 8000},
    "cache": {"backend": "redis"},
})

# ── Case 2: Override some defaults
try_load("Partial override", {
    "service": {"name": "myapp", "port": 8000, "workers": 8},
    "cache": {"backend": "memcached", "ttl_seconds": 60},
})

# ── Case 3: Missing required field
try_load("Missing required field (service.name)", {
    "service": {"port": 8000},
    "cache": {"backend": "redis"},
})

# ── Case 4: Wrong type
try_load("Wrong type (port should be int)", {
    "service": {"name": "myapp", "port": "eight-thousand"},
    "cache": {"backend": "redis"},
})

# ── Case 5: bool passed where int expected
try_load("bool is not int (port=True)", {
    "service": {"name": "myapp", "port": True},
    "cache": {"backend": "redis"},
})

# ── Case 6: Nested section wrong type
try_load("Nested section not a dict", {
    "service": {"name": "myapp", "port": 8000},
    "cache": "redis",    # should be a dict
})

# ── SchemaError: bad schema definition
print("\n── Bad schema ─────────────────────────────────────────")
try:
    bad_schema = {"field": (str, 42)}   # default doesn't match type
    Alfig(bad_schema).load_dict({"field": "x"}).validate()
except SchemaError as e:
    print(f"  ✗ SchemaError: {e}")
