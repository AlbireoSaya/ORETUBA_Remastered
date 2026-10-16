import struct


def decode_literal_record(data: bytes, start: int) -> dict:
    if data[start:start + 2] != b'\x5b\x20':
        raise ValueError('bad record header')
    if len(data) < start + 7:
        raise ValueError('truncated record header')
    opcode = struct.unpack_from('<I', data, start + 2)[0]
    if data[start + 6] != 1:
        raise NotImplementedError('unsupported condition byte')
    if len(data) < start + 11:
        raise ValueError('truncated record length')
    length = struct.unpack_from('<I', data, start + 7)[0]
    end = start + 7 + length
    if length < 5 or end > len(data):
        raise ValueError('invalid declared length')
    count = data[start + 11]
    cursor = start + 12
    pairs = []
    pointer_item_indexes = []

    def need(n, at):
        if at + n > end:
            raise ValueError('truncated item')

    for index in range(count):
        need(1, cursor)
        tag = data[cursor]
        cursor += 1
        if tag == 0:
            pairs.append((0, 0))
        elif tag == 2:
            need(4, cursor)
            pairs.append((0, struct.unpack_from('<I', data, cursor)[0]))
            cursor += 4
        else:
            need(1, cursor)
            selector = data[cursor]
            cursor += 1
            if selector == 0:
                need(4, cursor)
                pairs.append((tag, struct.unpack_from('<I', data, cursor)[0]))
                cursor += 4
            elif selector == 1:
                need(2, cursor)
                n = struct.unpack_from('<H', data, cursor)[0]
                cursor += 2
                if n > 0:
                    need(n, cursor)
                    pairs.append((tag | 2, cursor))
                    pointer_item_indexes.append(index)
                    cursor += n
                else:
                    pairs.append((tag | 2, 0))
            else:
                raise NotImplementedError('unsupported selector')

    if cursor != end:
        raise ValueError('record length mismatch')
    return {'opcode': opcode, 'count': count, 'pairs': pairs,
            'pointer_item_indexes': pointer_item_indexes,
            'cursor': cursor, 'end': end}