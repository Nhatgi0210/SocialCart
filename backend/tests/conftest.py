"""Load each service under a distinct name (both have an app.main module)."""
import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load_service(service):
    name = service.replace("-", "_") + "_main"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, BACKEND / service / "app/main.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]
