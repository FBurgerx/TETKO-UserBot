class DispatcherController:
    def __init__(self, context):
        self.context = context
        self.dispatchers = []

    def add(self, name, dispatcher, priority=0):
        self.dispatchers.append((priority, name, dispatcher))
        self.dispatchers.sort(key=lambda item: item[0], reverse=True)
        self.context.dispatchers = self.dispatchers

    async def dispatch(self, message, command=None):
        for _, _, dispatcher in self.dispatchers:
            result = await dispatcher.dispatch(message, command)
            if result and result.handled:
                return result
        return None
