from lucifen_direct_cfg import walk_direct_function

def describe_instruction(ins):
    ops = []
    for op in ins.operands:
        rec = {"size": op.size, "access": op.access}
        if op.type == 1:  # reg
            rec["type"] = "reg"
            rec["reg"] = ins.reg_name(op.reg)
        elif op.type == 2:  # imm
            rec["type"] = "imm"
            rec["imm"] = op.imm
        elif op.type == 3:  # mem
            m = op.mem
            rec["type"] = "mem"
            rec["segment"] = ins.reg_name(m.segment) if m.segment else ""
            rec["base"] = ins.reg_name(m.base) if m.base else ""
            rec["index"] = ins.reg_name(m.index) if m.index else ""
            rec["scale"] = m.scale
            rec["disp"] = m.disp
        else:
            rec["type"] = op.type  # 未知类型，原样保留整数
        ops.append(rec)
    rec = {"site": ins.address, "size": ins.size, "mnemonic": ins.mnemonic,
           "op_str": ins.op_str, "operands": ops}
    try:
        r, w = ins.regs_access()
        rec["regs_read"] = [ins.reg_name(i) for i in r]
        rec["regs_write"] = [ins.reg_name(i) for i in w]
    except Exception as e:
        rec["regs_access_error"] = str(e)
        rec["regs_read"] = None
        rec["regs_write"] = None
    return rec
def collect_function_rows(read_bytes, ranges, entry, known_entries=(), limit=10000):
    import capstone as cs
    captured = {}
    def read_cb(site, *args):
        data = read_bytes(site, *args)
        if data:
            captured[site] = data
        return data
    result = walk_direct_function(read_cb, ranges, entry, known_entries, limit)
    if isinstance(result, dict):
        edges = result.get('edges')
        unresolved = result.get('unresolved')
        diagnostics = list(result.get('diagnostics') or [])
        instruction_count = result.get('instruction_count')
    else:
        edges, unresolved, diagnostics, instruction_count = result
        diagnostics = list(diagnostics or [])
    md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
    md.detail = True
    md.skipdata = False
    rows = []
    for site in sorted(captured):
        data = captured[site]
        ins = next(md.disasm(data, site), None)
        if ins is None or ins.size > len(data):
            continue
        row = describe_instruction(ins)
        rows.append(row)
        if isinstance(row, dict) and row.get('regs_access_error'):
            diagnostics.append({'type': 'regs_access_error', 'site': site, 'error': row['regs_access_error']})
    if len(rows) != instruction_count:
        diagnostics.append({'type': 'capture_count_mismatch',
                            'rows': len(rows),
                            'instruction_count': instruction_count})
    return {'edges': edges, 'entry': entry, 'unresolved': unresolved, 'diagnostics': diagnostics,
            'instruction_count': instruction_count, 'instructions': rows}