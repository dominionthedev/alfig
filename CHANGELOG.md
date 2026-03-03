# Changelog

All notable changes to Alfig are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Alfig follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-03-01

First public release.

### Added

- **Core `Alfig` class** — unified config manager with `load`, `save`, `get`, `set`, `delete`, `validate`, `dumps`, `as_dict`
- **Schema validation engine** (`alfig/schema.py`)
  - Supports `str`, `int`, `float`, `bool`, `list`, `dict`
  - Required fields raise `ValidationError` when missing
  - Optional fields via `(type, default)` tuple syntax
  - Nested sections as nested dicts
  - Correctly rejects `bool` where `int` is expected (Python `bool` is a subclass of `int`)
- **JSON format handler** (`alfig/formats/json_fmt.py`) — built-in, no dependencies
- **YAML format handler** (`alfig/formats/yaml_fmt.py`) — requires `PyYAML`
- **TOML format handler** (`alfig/formats/toml_fmt.py`) — read via `tomllib` (3.11+) or `tomli`; write via `tomli-w` or `toml`
- **Custom CONF/INI format handler** (`alfig/formats/conf_fmt.py`)
  - Nested sections via dot-notation headers (`[section.subsection]`)
  - Automatic type coercion: `bool`, `int`, `float`, `list` (JSON), `dict` (JSON), `str`
  - Full round-trip fidelity
  - No external dependencies
- **Format auto-detection** from file extension
- **Fluent API** — all mutating methods return `self` for chaining
- **`Alfig.convert()` static method** for file-to-file format conversion
- **CLI** (`alfig`) with three commands:
  - `alfig convert <file> --to <format>` — convert between formats
  - `alfig validate <file>` — parse and validate, optionally print as JSON
  - `alfig get <file> <key>` — read a single value with dot-notation
- **GitHub Actions CI** — tests on Python 3.11/3.12/3.13 across Ubuntu, macOS, Windows
- **Examples** — `basic_usage.py`, `format_conversion.py`, `schema_validation.py`, `conf_format.py`
- **Documentation** — API reference, CONF format specification
- **Branding** — SVG logo and icon with gradient design

[Unreleased]: https://github.com/dominionthedev/alfig/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dominionthedev/alfig/releases/tag/v0.1.0
