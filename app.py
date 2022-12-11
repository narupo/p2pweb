from p2pweb.peer import Peer
import sys


class App(Peer):
    pass


if len(sys.argv) >= 2:
    App(sys.argv[1]).mainloop()
else:
    App().mainloop()
