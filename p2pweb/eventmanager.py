class EventManager:
    def __init__(self):
        self.listeners = {}

    def dispatch(self, name, *args, **kwargs):
        if name in self.listeners.keys():
            return self.listeners[name](*args, **kwargs)
        else:
            print(f'EventManager: not found name "{name}"')

    def add_listener(self, name, listener):
        self.listeners[name] = listener
