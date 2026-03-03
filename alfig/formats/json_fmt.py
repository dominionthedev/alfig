"""JSON format handler."""

import json


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def loads(text: str) -> dict:
    return json.loads(text)


def dump(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def dumps(data: dict) -> str:
    return json.dumps(data, indent=2)
