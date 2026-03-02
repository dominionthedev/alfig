"""
examples/basic_usage.py
=======================
The simplest possible Alfig workflow:
  load → validate → read → modify → save
"""

from alfig import Alfig

# 1. Define your schema
schema = {
    "database": {
        "host": str,
        "port": int,
        "user": str,
        "password": (str, "changeme"),   # optional, has a default
    },
    "features": {
        "enable_logging": bool,
        "max_threads": (int, 4),          # optional, defaults to 4
    },
}

# 2. Create the Alfig instance with your schema
config = Alfig(schema)

# 3. Load from a dict (in practice: load("settings.yaml") etc.)
config.load_dict({
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "admin",
        # password intentionally omitted — the default kicks in
    },
    "features": {
        "enable_logging": True,
        # max_threads intentionally omitted — defaults to 4
    },
})

# 4. Validate — fills in defaults, raises if anything is wrong
config.validate()

# 5. Read values with dot-notation
print("DB host   :", config.get("database.host"))         # localhost
print("DB port   :", config.get("database.port"))         # 5432
print("password  :", config.get("database.password"))     # changeme (default)
print("threads   :", config.get("features.max_threads"))  # 4 (default)

# 6. Mutate
config.set("features.max_threads", 16)
config.set("database.host", "prod.db.internal")

print("\nAfter mutation:")
print("DB host   :", config.get("database.host"))
print("threads   :", config.get("features.max_threads"))

# 7. Serialize to different formats
print("\n── JSON ──────────────────────────────────")
print(config.dumps("json"))

print("── CONF ──────────────────────────────────")
print(config.dumps("conf"))
