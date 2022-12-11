from urllib.parse import urlparse
import os


def pop_head_slash(path):
    if not len(path):
        return path
    while len(path):
        if path[0] == '/' or path[0] == '\\':
            path = path[1:]
        else:
            break
    return path


def fix_url(url):
    if not url.startswith('htpp://'):
        url = 'htpp://' + url
    o = urlparse(url)
    path = o.path
    if path:
        path = os.path.normpath(o.path).replace('\\', '/')
    port = ':' + str(o.port) if str(o.port) else ''
    url = o.scheme + '://' + o.hostname + port + path
    return url
