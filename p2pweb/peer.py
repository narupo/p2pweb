from p2pweb import sock
from p2pweb import gui 
from p2pweb.context import Context
from p2pweb import settings
from p2pweb.settings import HTPP_VERSION
from p2pweb.exceptions import InvalidReceiveData, InvalidPath
from p2pweb.validations import validate_path
from p2pweb.utils import pop_head_slash
import os
import time
from threading import Thread
import re


class WebBrowser(gui.Frame):
    def __init__(self, master, context):
        super().__init__(master)
        self.context = context

        self.address_bar = gui.AddressBar(
            self,
            goto_command=self.goto,
        )
        self.address_bar.pack(side=gui.TOP, fill=gui.X)

        gui.Frame(self).pack(side=gui.TOP, pady=4)

        self.text = gui.Text(self)
        self.text.pack(side=gui.TOP, expand=True, fill=gui.BOTH)

    def goto(self):
        address = self.address_bar.get()

        try:
            htpp_response = self.context.web_engine.get(address)
        except ConnectionRefusedError as e:
            print(e)
            self.text.delete('1.0', gui.END)
            self.text.insert(gui.END, 'Error: Connection Refused.')
            return

        print(htpp_response)
        content = htpp_response.content_to_string()
        self.text.delete('1.0', gui.END)
        self.text.insert(gui.END, content)


class HtppResponse:
    def __init__(
        self,
        version=None,
        status=None,
        content=None,
    ):
        self.version: str = version
        self.status: str = status
        self.content: bytes = content

    def __str__(self):
        return f'<HtppResponse version={self.version} status={self.status} content={self.content.decode()} />'

    def content_to_string(self):
        return self.content.decode()


class WebEngine:
    def __init__(self, context):
        self.context = context

    def start(self):
        addr = self.context.addr_port
        if addr is None:
            addr = settings.recv_address

        self.recv_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self.recv_sock.bind(addr)
        print('bind', addr)
        self.recv_sock.listen(10)

        self.recv_worker_thread = Thread(target=self.recv_worker, daemon=True)
        self.recv_worker_thread.start()

    def recv_worker(self):
        while True:
            print('accept...')
            client_sock, client_addr = self.recv_sock.accept()
            thread = Thread(target=self.recv_client_worker, daemon=True, args=(client_sock, ))
            thread.start()

    def recv_client_worker(self, client_sock):
        while True:
            print('recv...')
            try:
                self.recv_client_sock(client_sock)
            except ConnectionAbortedError as e:
                print(e)
                break
        print('end recv_client_worker')

    def recv_client_sock(self, client_sock):
        try:
            data = client_sock.recv(1024)
        except ConnectionAbortedError as e:
            raise e

        try:
            result: bytes = self.parse_receive_data(data)
        except InvalidReceiveData as e:
            print(e)
            client_sock.send(f'{HTPP_VERSION} 500\r\n'.encode())
        except InvalidPath as e:
            print(e)
            client_sock.send(f'{HTPP_VERSION} 500\r\n'.encode())
        else:
            response = b''
            response += HTPP_VERSION.encode()
            if result:
                response += b' 200\r\n\r\n' + result
            else:
                response += b' 200\r\n'
            client_sock.send(response)
            print('send', response)

    def parse_receive_data(self, data: bytes):
        data = data.decode()
        lines = data.replace('\r\n', '\n').split('\n')

        for line in lines:
            print('line', line)
            if line.startswith('GET'):
                toks = line.split(' ')
                if len(toks) < 2:
                    raise InvalidReceiveData('invalid GET method')
                path = toks[1]
                result = self.process_method_get(path)
                print('result', result)
                return result

    def process_method_get(self, path: str):
        # htpp://localhost:8888/index.md
        path = os.path.normpath(path)
        validate_path(path)
        path = pop_head_slash(path)
        path = os.path.join(self.context.public_dir, path)
        print('public_dir', self.context.public_dir)
        print('join path', path)

        if 'public' not in path or not os.path.exists(path):
            return None

        with open(path, 'rb') as fin:
            print('open', path)
            return fin.read()

    def get(self, address: str):
        address = address.strip()
        print('address', address)
        m = re.match(r'htpp://(?P<addr>[0-9|a-z|A-Z|\_\-\.]+):?(?P<port>[0-9]+)?(?P<path>[0-9|a-z|A-Z|\_\-\/\.]*)', address)
        addr = m.group('addr')
        port = m.group('port') or settings.HTPP_PORT
        port = int(port)
        path = m.group('path')
        if path is None:
            path = '/'
        print('get', addr, port, path)

        sok = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        sok.connect((addr, port))

        while True:
            request = b'GET '
            request += path.encode()
            sok.send(request)
            response = sok.recv(1024)
            sok.close()
            return self.parse_response_data(response)

    def parse_response_data(self, response: bytes):
        m = 10
        version = bytearray()
        status = bytearray()
        content = bytearray()
        digits = [ord('0'), ord('1'), ord('2'), ord('3'), ord('4'),
                  ord('5'), ord('6'), ord('7'), ord('8'), ord('9')]

        for c in response:
            print(c)
            if m == 0:
                if c == ord('H'):
                    m = 10
                    version.append(c)
            elif m == 10:
                if c == ord(' '):
                    m = 20
                else:
                    version.append(c)
            elif m == 20:
                if c in digits:
                    status.append(c)
                elif c == ord('\r'):
                    m = 30
            elif m == 30:
                if c == ord('\r'):
                    m = 40
            elif m == 40:
                if c == ord('\n'):
                    m = 50
            elif m == 50:
                content.append(c)

        print(version, status, content)
        return HtppResponse(
            version=version.decode(),
            status=status.decode(),
            content=content,
        )


class Peer(gui.RootWindow):
    def __init__(self, addr_port: str = None):
        self.init_env(addr_port)

        super().__init__()
        self.title('Peer')
        self.geometry('400x300')

        self.main_frame = gui.Frame(self)
        self.main_frame.pack(expand=True, fill=gui.BOTH, pady=10, padx=10)

        self.web_engine = WebEngine(self.context)
        self.web_engine.start()
        self.context.web_engine = self.web_engine

        self.web_browser = WebBrowser(self.main_frame, self.context)
        self.web_browser.pack(expand=True, fill=gui.BOTH)

    def init_env(self, addr_port=None):
        app_dir = os.path.abspath('.')
        public_dir = os.path.join(app_dir, 'public')
        if not os.path.exists(public_dir):
            os.mkdir(public_dir)

        print('app_dir', app_dir)
        print('public_dir', public_dir)
        print('addr_port', addr_port)

        self.context = Context(
            app_dir=app_dir,
            public_dir=public_dir,
            addr_port=addr_port,
        )
