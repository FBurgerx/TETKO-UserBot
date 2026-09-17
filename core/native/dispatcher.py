import inspect

class NativeDispatcher:
    def __init__(self, registry, logger=None):
        self.registry = registry
        self.logger = logger

    async def dispatch_command(self, name, message):
        item = self.registry.handlers["command"].get(name)
        if not item:
            return False
        module, spec = item
        result = getattr(module, spec.callback.__name__)(message)
        if inspect.isawaitable(result):
            await result
        return True

    async def dispatch_watchers(self, message):
        for module, spec in sorted(self.registry.handlers["watcher"], key=lambda x: -x[1].priority):
            result = getattr(module, spec.callback.__name__)(message)
            if inspect.isawaitable(result):
                await result
