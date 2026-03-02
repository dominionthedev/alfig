"""
examples/format_conversion.py
==============================
Shows how to convert between all supported formats programmatically,
mirroring what `alfig convert` does from the CLI.
"""

import os
import tempfile
from alfig import Alfig

# Sample data we'll use for all conversions
data = {
    "app": {
        "name": "myservice",
        "version": "1.0.0",
        "debug": False,
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "workers": 4,
    },
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "workers": 4,
        "tls": {
            "enabled": True,
            "cert": "/etc/certs/server.crt",
            "key": "/etc/certs/server.key",
        },
    },
    "tags": ["web", "api", "v1"],
}


def show_format(label: str, text: str):
    print(f"\n{'─' * 50}")
    print(f"  {label}")
    print('─' * 50)
    print(text)


cfg = Alfig()
cfg.load_dict(data)

# Render each format in memory
show_format("JSON", cfg.dumps("json"))
show_format("CONF / INI  (Alfig nested format)", cfg.dumps("conf"))

try:
    show_format("YAML", cfg.dumps("yaml"))
except ImportError:
    print("\n[YAML skipped — install PyYAML: pip install pyyaml]")

try:
    show_format("TOML", cfg.dumps("toml"))
except ImportError:
    print("\n[TOML write skipped — install tomli-w: pip install tomli-w]")

# File-based conversion via Alfig.convert()
print("\n\n── File-based conversion example ─────────────────────")
with tempfile.TemporaryDirectory() as tmp:
    src = os.path.join(tmp, "config.json")
    dst = os.path.join(tmp, "config.conf")

    cfg.save(src)
    Alfig.convert(src, dst)

    print(f"Wrote: {src}")
    print(f"Converted to: {dst}")
    print("\nResulting .conf file:")
    with open(dst) as f:
        print(f.read())
