class NativePermissions:
    def __init__(self, owner_ids=None):
        self.owner_ids = set(owner_ids or ())

    def allowed(self, spec, message):
        if not getattr(spec, 'owner_only', False):
            return True
        return getattr(message, 'sender_id', None) in self.owner_ids
