def lookup(labels, name):
    if name is None:
        return 0
    for raw, val in labels:
        if raw == name:
            return val
    return 0xffffffff


def table(values, index):
    if isinstance(index, bool) or not isinstance(index, int):
        return 0xffffffff
    if index < 0 or index >= 2 ** 32 or index >= len(values):
        return 0xffffffff
    return values[index]


def target(codebase, labels, name, offset):
    if name is None:
        return (codebase + offset) % 2 ** 32
    val = lookup(labels, name)
    if val == 0xffffffff:
        return 0
    return (codebase + val) % 2 ** 32