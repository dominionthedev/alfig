# Contributing to Alfig

Thanks for your interest in contributing! This document covers the development workflow.

---

## Before every commit

Run these two commands locally before pushing anything. They mirror exactly what CI checks:

```bash
ruff check alfig/          # lint — should print "All checks passed!"
python -m build --sdist    # proves the package is installable end-to-end
```

And for good measure:

```bash
python -m pytest tests/ -v # confirm nothing is broken
```

If any of these fail locally, CI will fail too. Catching it before the push saves a round-trip.

---

## Setup

```bash
git clone https://github.com/dominionthedev/alfig
cd alfig
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"
pip install pytest pytest-cov ruff
```

---

## Running tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=alfig    # with coverage
```

---

## Linting

```bash
ruff check alfig/
ruff check alfig/ --fix   # auto-fix where possible
```

---

## Adding a new format

1. Create `alfig/formats/<name>_fmt.py` implementing four functions:

   ```python
   def load(path: str) -> dict: ...
   def loads(text: str) -> dict: ...
   def dump(data: dict, path: str) -> None: ...
   def dumps(data: dict) -> str: ...
   ```

2. Register it in `alfig/formats/__init__.py`:

   ```python
   from alfig.formats import your_fmt

   _REGISTRY["yourformat"] = your_fmt
   _EXTENSION_MAP[".yourext"] = "yourformat"
   ```

3. Add tests in `tests/test_alfig.py`.
4. Update `docs/api.md` and `CHANGELOG.md`.

---

## Commit style

Alfig uses [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix      | When                                |
| ----------- | ----------------------------------- |
| `feat:`     | New feature                         |
| `fix:`      | Bug fix                             |
| `test:`     | Adding or fixing tests              |
| `docs:`     | Documentation only                  |
| `chore:`    | Build, CI, tooling                  |
| `refactor:` | Code change with no behavior change |

---

## Pull requests

- Open an issue first for large changes
- Keep PRs focused — one concern per PR
- All CI checks must pass before merge
- Add or update tests for any changed behavior
