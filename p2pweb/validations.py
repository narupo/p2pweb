import os
from p2pweb.exceptions import InvalidPath


def validate_path(path):
    if '..' in path:
        raise InvalidPath('found ..')
