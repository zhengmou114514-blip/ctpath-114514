from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_backend_app_path = Path(__file__).resolve().parent.parent / 'backend' / 'app'
if _backend_app_path.exists():
    backend_app = str(_backend_app_path)
    if backend_app not in __path__:
        __path__.append(backend_app)

    try:
        from app.env_loader import load_env_file

        load_env_file()
    except Exception:
        pass
