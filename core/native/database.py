class NativeDatabase:
    def __init__(self): self._data={}
    def get(self, namespace, key, default=None): return self._data.get(namespace, {}).get(key, default)
    def set(self, namespace, key, value): self._data.setdefault(namespace, {})[key]=value
    def delete(self, namespace, key): self._data.get(namespace, {}).pop(key, None)
