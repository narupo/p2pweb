from p2pweb import sock
from p2pweb import gui 
from p2pweb.context import Context
from p2pweb import settings
from p2pweb.settings import HTPP_VERSION
from p2pweb.exceptions import InvalidReceiveData, InvalidPath
from p2pweb.validations import validate_path
from p2pweb.utils import pop_head_slash, fix_url, solve_url, is_invalid_url
from p2pweb.markdownparser import MarkdownParser
from p2pweb.resource import Resource
from p2pweb.network import P2PNetworkManager
from p2pweb import font
import os
from threading import Thread
from urllib.parse import urlparse
import webbrowser


class WebBrowser(gui.Frame):
    def __init__(self, master, context):
        super().__init__(master)
        self.context = context

        self.top_frame = gui.Frame(self)
        self.top_frame.pack(side=gui.TOP, expand=True, fill=gui.BOTH)

        self.left_frame = gui.Frame(self.top_frame)
        self.left_frame.pack(side=gui.LEFT, fill=gui.Y)

        gui.Frame(self.top_frame).pack(side=gui.LEFT, padx=4)

        self.right_frame = gui.Frame(self.top_frame)
        self.right_frame.pack(side=gui.LEFT, expand=True, fill=gui.BOTH)

        self.bottom_frame = gui.Frame(self)
        self.bottom_frame.pack(side=gui.TOP, fill=gui.X)

        self.address_listbox = gui.ScrolledListbox(self.left_frame)
        self.address_listbox.pack(expand=True, fill=gui.BOTH)
        self.address_listbox.bind('<<ListboxSelect>>', self.address_select)

        self.address_bar = gui.AddressBar(
            self.right_frame,
            goto_command=self.goto,
        )
        self.address_bar.pack(side=gui.TOP, fill=gui.X)
        self.address_bar.bind('<Return>', lambda ev: self.goto())

        gui.Frame(self.right_frame).pack(side=gui.TOP, pady=4)

        self.text = gui.ScrolledText(self.right_frame, bd=0, height=10, state=gui.DISABLED)
        self.text.pack(side=gui.TOP, expand=True, fill=gui.BOTH)

        self.status_bar = gui.Label(self.bottom_frame, text='', anchor=gui.W)
        self.status_bar.pack(side=gui.BOTTOM, fill=gui.X)

    def address_select(self, ev):
        sel = self.address_listbox.curselection()
        addr = self.address_listbox.get(sel[0])
        url = 'htpp://' + addr
        self.address_bar.delete(0, gui.END)
        self.address_bar.insert(gui.END, url)
        self.goto()

    def add_address(self, addr):
        self.address_listbox.insert(gui.END, addr)

    def fix_address_bar(self):
        url = self.address_bar.get()
        url = fix_url(url)
        self.address_bar.delete(0, gui.END)
        self.address_bar.insert(gui.END, url)

    def goto(self):
        self.fix_address_bar()
        url = self.address_bar.get()
        if is_invalid_url(url):
            return
        self.load_from_url(url)

    def load_from_url(self, url):
        try:
            htpp_response = self.context.web_engine.get(url)
        except ConnectionRefusedError as e:
            print(e)
            self.text.delete('1.0', gui.END)
            self.text.insert(gui.END, 'Error: Connection Refused.')
            return
        except BaseException as e:
            print(e)
            self.text.delete('1.0', gui.END)
            self.text.insert(gui.END, f'Error: {e}')
            return

        self.address_bar.delete(0, gui.END)
        self.address_bar.insert(gui.END, url)

        if htpp_response.status == '200':
            scontent = htpp_response.content_to_string()
            assert(scontent)
            self.context.p2p_network.register_url(url)
        else:
            scontent = htpp_response.status_to_string()

        self.text.config(state=gui.NORMAL)
        if htpp_response.content_type == 'text/markdown':
            self.text.delete('1.0', gui.END)
            MarkdownParser(self.context, self.text).parse(scontent)
        else:
            self.text.delete('1.0', gui.END)
            self.text.insert(gui.END, scontent)
        self.text.config(state=gui.DISABLED)


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

    @staticmethod
    def create_500():
        return HtppResponse(
            version=HTPP_VERSION,
            status='500',
        )

    @staticmethod
    def create_404():
        return HtppResponse(
            version=HTPP_VERSION,
            status='404',
        )

    @staticmethod
    def create_403():
        return HtppResponse(
            version=HTPP_VERSION,
            status='403',
        )

    def __str__(self):
        return f'<HtppResponse version={self.version} status={self.status} content={self.content.decode()} />'

    def content_to_string(self):
        if self.content:
            return self.content.decode()
        return None

    def status_to_string(self):
        if self.status == '200':
            return f'{self.status} OK'
        else:
            return f'{self.status} Error'

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
        self.context.web_browser.status_bar.config(text=f'Launch on {addr[0]}:{addr[1]}')

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
            # print('recv_and_send_client_sock: send...', data)
            client_sock.send(data)
            print('recv_and_send_client_sock: send done')
            # print('send', data)

    def parse_receive_data(self, data: bytes):
        lines = data.replace(b'\r\n', b'\n').split(b'\n')

        for line in lines:
            print('line', line)
            if line.startswith(b'GETSIDE'):
                return self.process_method_get_side()
            elif line.startswith(b'GET'):
                toks = line.split(b' ')
                if len(toks) < 2:
                    raise InvalidReceiveData('invalid GET method')
                path = toks[1].decode()
                return self.process_method_get(path)
        print('end parse_receive_data')

    def get_content_type(self, path):
        _, ext = os.path.splitext(path)
        if ext == '.md':
            return 'text/markdown'
        else:
            return 'text/html'

    def process_method_get(self, path: str):
        # htpp://localhost:8888/index.md
        validate_path(path)
        path = pop_head_slash(path)
        if path == '':
            path = 'index.md'
        pub_path = os.path.join(self.context.public_dir, path)
        print('public_dir', self.context.public_dir)
        print('join path', path)

        if 'public' not in pub_path:
            return HtppResponse.create_500()
        elif not os.path.exists(pub_path):
            return HtppResponse.create_404()
        elif os.path.isdir(pub_path):
            return HtppResponse.create_403()

        with open(pub_path, 'rb') as fin:
            print('open', pub_path)
            content = fin.read()

        content_type = self.get_content_type(pub_path)

        return HtppResponse(
            version=HTPP_VERSION,
            status='200',
            content_type=content_type,
            content=content,
        )

    def process_method_get_side(self):
        content = self.context.p2p_network.side_nodes_to_bytes()
        print('process_method_get_side:', content)
        return HtppResponse(
            version=HTPP_VERSION,
            status='200',
            content=content,
        )

    def get(self, url: str):
        url = solve_url(self.context, url)
        o = urlparse(url)
        addr = o.hostname 
        port = o.port or settings.HTPP_PORT
        path = o.path
        if path is None:
            path = '/'

        sok = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        try:
            sok.connect((addr, port))
        except BaseException as e:
            raise e

        request = b'GET '
        request += path.encode()
        sok.send(request)
        
        response = b''
        nrecv = 1024
        while True:
            data = sok.recv(nrecv)
            response += data
            if len(data) < nrecv:
                break

        sok.close()
        ret = self.parse_response_data(response)
        return ret

    def parse_response_data(self, response: bytes):
        m = 0
        res = bytearray(response)
        ln = 0
        lines = res.split(b'\r\n')
        version = None
        status = None
        content = None
        content_type = None

        # print('response', response)
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

        # print(version, status, content, content_type)
        return HtppResponse(
            version=version,
            status=status,
            content=content,
            content_type=content_type,
        )

    def send_request_and_recv(self, method: str, url: str):
        o = urlparse(url)
        port = o.port if o.port is not None else settings.HTPP_PORT
        sok = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        sok.connect((o.hostname, port))

        data = f'{method}\r\n'.encode()
        sok.send(data)

        nrecv = 1024
        response = b''
        while True:
            res = sok.recv(nrecv)
            response += res
            if len(res) < nrecv:
                break

        return response

    def get_side_nodes(self, addr):
        url = f'htpp://{addr}'
        response = self.send_request_and_recv('GETSIDE\r\n', url)
        return self.parse_response_data(response)


class Peer(gui.RootWindow):
    def __init__(self, addr_port: str = None):
        super().__init__()
        self.init_env(addr_port)
        self.title('PW Browser')
        self.geometry('500x500')

        self.main_frame = gui.Frame(self)
        self.main_frame.pack(expand=True, fill=gui.BOTH, pady=10, padx=10)

        self.web_engine = WebEngine(self.context)
        self.context.web_engine = self.web_engine

        self.p2p_network = P2PNetworkManager(self.context)
        self.context.p2p_network = self.p2p_network

        self.web_browser = WebBrowser(self.main_frame, self.context)
        self.web_browser.pack(expand=True, fill=gui.BOTH)
        self.context.web_browser = self.web_browser

        self.web_engine.start()
        self.p2p_network.start()

    def init_env(self, addr_port=None):
        app_dir = os.path.abspath('.')
        public_dir = os.path.join(app_dir, 'public')
        if not os.path.exists(public_dir):
            os.mkdir(public_dir)

        print('app_dir', app_dir)
        print('public_dir', public_dir)
        print('addr_port', addr_port)

        Resource.get_instance().load()
        font.init()

        self.context = Context(
            app_dir=app_dir,
            public_dir=public_dir,
            addr_port=addr_port,
        )
        self.context.add_listener('jump_to_link', self.jump_to_link)

    def jump_to_link(self, url):
        url = solve_url(self.context, url)
        o = urlparse(url)
        if o.scheme == 'http':
            webbrowser.open_new(url.strip())
        elif o.scheme == 'htpp':
            self.web_browser.load_from_url(url)
