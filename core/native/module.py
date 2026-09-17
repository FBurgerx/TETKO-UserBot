import inspect
from .decorators import HandlerSpec

class NativeModule:
    name = None
    version = "0.0.0"
    author = "unknown"

    def __init__(self, context=None):
        self.context = context
        self.handlers = self._collect_handlers()
        self.module_name = self.name or self.__class__.__name__

    def _collect_handlers(self):
        result = []
        for _, value in inspect.getmembers(self.__class__):
            spec = getattr(value, "__tetko_handler__", None)
            if isinstance(spec, HandlerSpec):
                result.append(spec)
        return result

    async def on_load(self):
        return None

    async def on_unload(self):
        return None
