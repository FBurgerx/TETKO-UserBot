class NativeConfig:
    def __init__(self, values=None): self.values=dict(values or {})
    def get(self, key, default=None): return self.values.get(key, default)
    def set(self, key, value): self.values[key]=value
