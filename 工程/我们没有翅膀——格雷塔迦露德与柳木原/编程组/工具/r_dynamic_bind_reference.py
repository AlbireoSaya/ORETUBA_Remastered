from lucifen_tob_binding_reference import relocation_writes

_U32 = 0xFFFFFFFF


def bind_expression(rb, wb, wr, source_base, expr, maps, string_base=0):
    flag = (source_base + expr["flag_offset"]) & _U32
    if rb(flag) != 0:
        return False
    wb(flag, 1)
    base = (source_base + expr["code_start"]) & _U32
    for a, v in relocation_writes(expr, base, maps, string_base):
        wr(a, v)
    return True
