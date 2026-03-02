"""
examples/conf_format.py
========================
Deep dive into Alfig's custom CONF/INI format:
  - Nested sections via dot-notation headers
  - Auto type coercion
  - Round-trip fidelity
  - Comparison with equivalent JSON
"""

from alfig.formats import conf_fmt
import json

# ── What a .conf file looks like with Alfig's format ──────────────────
CONF_TEXT = """\
# Alfig CONF format — nested sections use dot-notation headers

[app]
name = myservice
version = 2
debug = false

[app.logging]
enabled = true
level = info
format = json

[database]
host = db.internal
port = 5432

[database.pool]
min_size = 2
max_size = 20
timeout = 30

[database.replica]
host = replica.db.internal
port = 5433

[cache]
backend = redis
ttl = 300
hosts = ["cache1.internal", "cache2.internal"]
"""

print("── Input CONF ────────────────────────────────────────────────────")
print(CONF_TEXT)

# Parse it
data = conf_fmt.loads(CONF_TEXT)

print("── Parsed Python dict ────────────────────────────────────────────")
print(json.dumps(data, indent=2))

# Demonstrate type coercion worked
print("\n── Coercion check ────────────────────────────────────────────────")
print(f"app.version      : {data['app']['version']}  (type: {type(data['app']['version']).__name__})")
print(f"app.debug        : {data['app']['debug']}   (type: {type(data['app']['debug']).__name__})")
print(f"app.logging.enabled : {data['app']['logging']['enabled']}  (type: {type(data['app']['logging']['enabled']).__name__})")
print(f"database.port    : {data['database']['port']}  (type: {type(data['database']['port']).__name__})")
print(f"cache.hosts      : {data['cache']['hosts']}  (type: {type(data['cache']['hosts']).__name__})")

# Round-trip
serialized = conf_fmt.dumps(data)
reparsed = conf_fmt.loads(serialized)

print("\n── Round-trip fidelity ───────────────────────────────────────────")
print("Serialized CONF:")
print(serialized)
print("Round-trip match:", reparsed == data)
