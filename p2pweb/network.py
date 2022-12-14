from threading import Thread, Lock
import time
from urllib.parse import urlparse
from p2pweb.utils import is_invalid_url


class P2PNetworkManager:
    def __init__(self, context):
        self.context = context
        self.registered_addresses = {}
        self.task_queue = []
        self.task_queue_lock = Lock()

    def start(self):
        self.worker_thread = Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def register_url(self, url):
        print('P2PNetworkManager: register_url:', url)
        if is_invalid_url(url):
            return
        o = urlparse(url)
        if o.hostname is None:
            return
        if o.port is not None:
            addr = f'{o.hostname}:{o.port}'
        else:
            addr = o.hostname

        if addr in self.registered_addresses.keys():
            return

        self.registered_addresses[addr] = True
        print('P2PNetworkManager: register_url:', self.registered_addresses)
        with self.task_queue_lock:
            self.task_queue.append(addr)

        self.context.web_browser.add_address(addr)

    def worker(self):
        while True:
            # print('P2PNetworkManager: working...', self.registered_addresses)
            time.sleep(1)
            addr = None
            with self.task_queue_lock:
                if len(self.task_queue):
                    addr = self.task_queue.pop(0)
            if addr:
                self.crawl(addr)

    def crawl(self, addr):
        print('P2PNetworkManager: crawl', addr)
        try:
            htpp_response = self.context.web_engine.get_side_nodes(addr)
        except BaseException as e:
            print(e)
            raise e

        if htpp_response.status != '200':
            print('P2PNetworkManager:', htpp_response.status_to_string())
            return

        content = htpp_response.content
        if content is None:
            print('P2PNetworkManager: content is None')
            return

        print('content', content)
        for address in content.decode().split('\r\n'):
            print(f'address[{address}] [{type(address)}]')
            url = 'htpp://' + address
            self.register_url(url)

    def side_nodes_to_bytes(self):
        dst = ''
        for addr in self.registered_addresses.keys():
            dst += f'{addr}\r\n'

        print('P2PNetworkManager: side_nodes_to_bytes:', dst)
        return dst.encode()
