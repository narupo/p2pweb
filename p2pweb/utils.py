def pop_head_slash(path):
    if not len(path):
        return path
    while len(path):
        if path[0] == '/' or path[0] == '\\':
            path = path[1:]
        else:
            break
    return path
