import sys
from importlib.util import find_spec, module_from_spec
from typing import Any

from .async_server import AsyncServer
from .async_server.process_server import ProcessServer
from .async_server.thread_server import ThreadServer
from .async_server.call_server import CallServer

_server_kinds: dict[str, type] = {
    "process": ProcessServer,  # long tasks
    "thread": ThreadServer,    # short tasks
    "call": CallServer,        # supershort tasks
}

def load(klass: str) -> Any:
    module_name, _, klass_name = klass.rpartition(".")
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = find_spec(module_name)
        if spec:
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[module_name] = module
        else:
            raise ModuleNotFoundError(f"No module named '{module_name}'")
    try:
        return getattr(module, klass_name)
    except AttributeError:
        raise ImportError(f"cannot import name '{klass_name}' from '{module_name}'")

def load_and_instantiate(desc: dict[str, Any] | None) -> Any:
    if not desc:
        return None
    name = desc.pop("name")
    klass = load(name)
    args = desc.get('args', [])
    kwargs = desc.get('kwargs', {})
    obj = klass(*args, **kwargs)
    return obj

def load_and_instantiate_server(desc: dict[str, Any] | None) -> AsyncServer | None:
    if not desc:
        return None
    name = desc.pop("name")
    kind = desc.pop("kind", "process")
    kind_klass = _server_kinds[kind.lower()]
    klass = load(name)
    args = desc.get('args', [])
    kwargs = desc.get('kwargs', {})
    obj: AsyncServer = kind_klass(klass, *args, **kwargs)
    return obj
