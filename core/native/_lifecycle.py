class NativeLifecycle:
    async def load(self, module):
        await module.on_load()
        return module

    async def unload(self, module):
        await module.on_unload()
        return module
