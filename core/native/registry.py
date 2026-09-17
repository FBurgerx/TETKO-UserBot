class NativeRegistry:
    def __init__(self):
        self.modules = {}
        self.handlers = {"command": [], "watcher": [], "callback": [], "loop": []}

    def register(self, module):
        key = module.module_name.casefold()
        self.modules[key] = module
        for spec in module.handlers:
            self.handlers.setdefault(spec.kind, []).append(spec)

    add = register

    def unregister(self, name):
        module = self.modules.pop(name.casefold(), None)
        if module:
            for specs in self.handlers.values():
                specs[:] = [s for s in specs if getattr(s, 'module', None) is not module and getattr(s, 'callback', None).__qualname__.split('.')[0] != module.__class__.__name__]
        return module

    remove = unregister

    def find_handlers(self, command):
        command = (command or '').casefold().lstrip('.')
        return [s for s in self.handlers.get('command', []) if command in ((s.name.casefold(),) + tuple(a.casefold() for a in s.aliases))]

    def watchers(self):
        return sorted(self.handlers.get('watcher', []), key=lambda s: -s.priority)
