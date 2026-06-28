class Plugin:
    def load(self): pass
    def execute(self, a: str): pass
    def unload(self): pass

def dynamic_dispatch(p, action: str):
    m = getattr(p, action, None)
    if m and callable(m):
        return m()
    return None
