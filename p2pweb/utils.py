def pop_head_slash(path):
    if not len(path):
        return path
    if path[0] == '/' or path[0] == '\\':
        return path[1:]
    return path
