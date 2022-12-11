from p2pweb import sock
from p2pweb import gui 
from p2pweb.context import Context
from p2pweb import settings
from p2pweb.settings import HTPP_VERSION
from p2pweb.exceptions import InvalidReceiveData, InvalidPath
from p2pweb.validations import validate_path
from p2pweb.utils import pop_head_slash
from p2pweb.markdownparser import MarkdownParser
from p2pweb.resource import Resource
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

        self.text = gui.Text(self, bd=0)
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

        scontent = htpp_response.content_to_string()
        assert(scontent)

        if htpp_response.content_type == 'text/markdown':
            self.text.delete('1.0', gui.END)
            MarkdownParser(self.text).parse(scontent)
        else:
            self.text.delete('1.0', gui.END)
            self.text.insert(gui.END, scontent)


class HtppResponse:
    def __init__(
        self,
        version=None,
        status=None,
        content_type=None,
        content=None,
    ):
        self.version: str = version
        self.status: str = status
        self.content_type: str = content_type
        self.content: bytes = content

    def __str__(self):
        return f'<HtppResponse version={self.version} status={self.status} content={self.content.decode()} />'

    def content_to_string(self):
        if self.content:
            return self.content.decode()
        return None

    def to_bytes(self):
        dst = bytearray()
        dst += self.version.encode()
        dst += b' '
        dst += self.status.encode()
        dst += b'\r\n'

        if self.content_type:
            dst += b'Content-Type: ' + self.content_type.encode() + b'\r\n'

        if self.content:
            dst += b'\r\n'
            dst += self.content

        return dst


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
                self.recv_and_send_client_sock(client_sock)
            except ConnectionAbortedError as e:
                print(e)
                break

            client_sock.close()
            break
        print('end recv_client_worker')

    def recv_and_send_client_sock(self, client_sock):
        try:
            data = client_sock.recv(1024)
        except ConnectionAbortedError as e:
            raise e

        try:
            htpp_response: bytes = self.parse_receive_data(data)
        except InvalidReceiveData as e:
            print(e)
            client_sock.send(f'{HTPP_VERSION} 500\r\n'.encode())
        except InvalidPath as e:
            print(e)
            client_sock.send(f'{HTPP_VERSION} 500\r\n'.encode())
        else:
            data = htpp_response.to_bytes()
            client_sock.send(data)
            print('send', data)

    def parse_receive_data(self, data: bytes):
        lines = data.replace(b'\r\n', b'\n').split(b'\n')

        for line in lines:
            print('line', line)
            if line.startswith(b'GET'):
                toks = line.split(b' ')
                if len(toks) < 2:
                    raise InvalidReceiveData('invalid GET method')
                path = toks[1].decode()
                return self.process_method_get(path)

    def get_content_type(self, path):
        _, ext = os.path.splitext(path)
        if ext == '.md':
            return 'text/markdown'
        else:
            return 'text/html'

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
            content = fin.read()

        content_type = self.get_content_type(path)

        return HtppResponse(
            version=HTPP_VERSION,
            status='200',
            content_type=content_type,
            content=content,
        )

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
        m = 0
        res = bytearray(response)
        ln = 0
        lines = res.split(b'\r\n')
        version = None
        status = None
        content = None
        content_type = None

        print('response', response)
        for line in lines:
            if m == 0:
                if line == b'':
                    m = 10
                elif line.startswith(b'HTPP'):
                    toks = line.split(b' ')
                    version = toks[0].decode()
                    status = toks[1].decode()
                elif line.startswith(b'Content-Type'):
                    toks = line.split(b':')
                    content_type = toks[1].strip().decode()
            elif m == 10:
                content = res[ln:]
                break
            ln += len(line) + 2

        print(version, status, content, content_type)
        return HtppResponse(
            version=version,
            status=status,
            content=content,
            content_type=content_type,
        )


class Peer(gui.RootWindow):
    def __init__(self, addr_port: str = None):
        super().__init__()
        self.init_env(addr_port)
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

        Resource.get_instance().load()
