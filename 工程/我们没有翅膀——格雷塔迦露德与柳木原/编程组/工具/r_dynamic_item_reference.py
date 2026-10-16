from lucifen_inline_vm_reference import record_value


def write_record_item(item, base, dest, rd, wr, eval_expr, var_map):
    is_inline = item["kind"] == "inline"
    first_flags = item["tag"] if is_inline else item["flags"]
    wr(dest, first_flags)
    if is_inline:
        wr(dest, (rd(dest) | 2) & 0xFFFFFFFF)
    value = record_value(item, base, rd, eval_expr, var_map) & 0xFFFFFFFF
    wr((dest + 4) & 0xFFFFFFFF, value)
    return value
