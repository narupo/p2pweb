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


def solve_url(context, url):
    o = urlparse(url.strip())
    is_path_only = not len(o.scheme) and o.hostname is None and o.path
    is_absolute_path = url[0] == '/'
    is_relative_path = url[0] != '/'

    # print(o, o.scheme, o.hostname, o.path, is_path_only, is_absolute_path, is_relative_path)
    if is_path_only:
        path = url
        o = urlparse(context.web_browser.address_bar.get())
        port = ':' + str(o.port) if str(o.port) else ''
        if is_absolute_path:
            url = o.scheme + '://' + o.hostname + port + path
        elif is_relative_path:
            url = o.scheme + '://' + o.hostname + port + '/'.join(o.path.split('/')[:-1]) + '/' + path
            
    return url
