class RegistrationRollback:
    def __init__(self):
        self.actions = []

    def add(self, undo):
        self.actions.append(undo)

    def rollback(self):
        for undo in reversed(self.actions):
            try:
                undo()
            except Exception:
                pass
        self.actions.clear()
