"""Load each service under a distinct name (both have an app.main module)."""
import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load_service(service, *, fresh=False):
    name = service.replace("-", "_") + "_main"
    if fresh or name not in sys.modules:
        previous = {key: value for key, value in sys.modules.items() if key == "app" or key.startswith("app.")}
        for key in previous:
            sys.modules.pop(key)
        sys.path.insert(0, str(BACKEND / service))
        try:
            spec = importlib.util.spec_from_file_location(name, BACKEND / service / "app/main.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
            for key in tuple(sys.modules):
                if key == "app" or key.startswith("app."):
                    sys.modules.pop(key)
            sys.modules.update(previous)
    return sys.modules[name]
