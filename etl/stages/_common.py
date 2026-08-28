from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "etl" / "out"


def rows_of(payload: Any) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("results", "data", "companies", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        for v in payload.values():
            if isinstance(v, list):
                return v
    return []


def total_count(payload: Any) -> int | None:
    if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict):
        return payload["pagination"].get("total_count")
    return None


def save(name: str, obj: Any) -> pathlib.Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def load(name: str) -> Any:
    path = OUT / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run the earlier stage first")
    return json.loads(path.read_text(encoding="utf-8"))


def log(msg: str) -> None:
    print(f"    {msg}")
