def relocation_writes(expr, code_base, group_maps, string_base=0):
    writes = []
    for r in expr['relocations']:
        group = r['group']
        index = r['index']
        if group in (0, 1, 2):
            value = group_maps[group][index]
        elif group == 3:
            value = string_base + index
        elif group == 4:
            value = code_base + index
        else:
            raise ValueError(group)
        writes.append(((code_base + r['slot_offset']) & 0xffffffff, value & 0xffffffff))
    return writes