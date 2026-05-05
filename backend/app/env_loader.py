from __future__ import annotations

import os
from pathlib import Path


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(env_path: Path | None = None, override: bool = False) -> Path | None:
    root = Path(__file__).resolve().parents[1]
    target = env_path or root / ".env"
    if not target.exists():
        return None

    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
    return target
