def _inline_header(data, start):
    if type(data) is not bytes or type(start) is not int:
        raise ValueError("data must be bytes and start must be int")
    if start < 0 or start + 6 > len(data):
        raise ValueError("start out of range")
    if data[start:start+2] != b"[s":
        raise ValueError("bad magic")
    n = int.from_bytes(data[start+2:start+6], "little")
    cs = start + 6
    flag = cs + n
    if flag + 5 > len(data):
        raise ValueError("truncated flag/reloc")
    tw = flag + 1
    size = int.from_bytes(data[tw:tw+4], "little")
    if size < 24:
        raise ValueError("bad reloc size")
    end = tw + size
    if end > len(data):
        raise ValueError("truncated reloc")
    return dict(start=start, end=end, code_start=cs, code_size=n, flag_offset=flag, compiled_flag=data[flag], reloc_start=tw, reloc_size=size)

def parse_inline_expression(data, start):
    expr = _inline_header(data, start)
    cursor = expr["reloc_start"] + 4
    relocations = []
    for group in range(5):
        if cursor + 4 > expr["end"]:
            raise ValueError("relocation count out of bounds")
        count = int.from_bytes(data[cursor:cursor + 4], "little")
        cursor += 4
        for _ in range(count):
            if cursor + 8 > expr["end"]:
                raise ValueError("relocation slot out of bounds")
            slot_offset = int.from_bytes(data[cursor:cursor + 4], "little")
            index = int.from_bytes(data[cursor + 4:cursor + 8], "little")
            if slot_offset + 4 > expr["code_size"]:
                raise ValueError("relocation slot beyond code")
            relocations.append({"group": group, "slot_offset": slot_offset, "index": index})
            cursor += 8
    if cursor != expr["end"]:
        raise ValueError("relocation table size mismatch")
    expr["relocations"] = relocations
    return expr