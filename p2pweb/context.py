from p2pweb.eventmanager import EventManager


class Context:
    def __init__(
        self,
        prev_context=None,
        app_dir=None,
        public_dir=None,
        web_engine=None,
        addr_port=None,
    ):
        self.event_manager = EventManager()
        self.prev_context = prev_context
        self.app_dir = app_dir
        self.public_dir = public_dir
        self.web_engine = web_engine

        if isinstance(addr_port, str):
            addr, port = addr_port.split(':')
            self.addr_port = (addr, int(port))
        else:
            self.addr_port = addr_port

    @property
    def root(self):
        cur = self
        while True:
            if cur.prev_context is None:
                break
            cur = cur.prev_context

        return cur

    def dispatch(self, name, *args, **kwargs):
        return self.event_manager.dispatch(name, *args, **kwargs)

    def add_listener(self, name, listener):
        return self.event_manager.add_listener(name, listener)
