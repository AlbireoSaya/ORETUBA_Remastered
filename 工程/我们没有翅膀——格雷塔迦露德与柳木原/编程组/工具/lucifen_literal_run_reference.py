def literal_run(data, start, end):
    if type(data) is not bytes or type(start) is not int or type(end) is not int:
        raise ValueError('invalid argument types')
    if start < 0 or end < start or end > len(data):
        raise ValueError('invalid range')
    pos = start
    units = []
    stop = 'limit'
    while pos < end:
        b = data[pos]
        if b == 0x00 or b == 0x5b:
            stop = 'nul' if b == 0x00 else 'marker'
            break
        if 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc:
            if pos + 1 >= end:
                raise ValueError('truncated lead')
            units.append((pos, 2))
            pos += 2
        else:
            units.append((pos, 1))
            pos += 1
    return {
        'start': start,
        'end': pos,
        'payload': data[start:pos],
        'units': units,
        'stop': stop,
    }