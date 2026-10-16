def value_op(op,a,b=0):
    m=0xffffffff
    a&=m
    b&=m
    s=lambda v:v if v<0x80000000 else v-0x100000000
    r={13:a+b,19:a&b,20:a|b,23:int(a==0),44:int(s(a)>=s(b)),45:int(a==b)}.get(op)
    if r is None:raise ValueError(op)
    return r&m

def step_memory(rd, wr, ctx, op, p):
    if op == 26:
        ptr = rd(p) & 0xffffffff
        wr(ptr, (rd(ptr) + 1) & 0xffffffff)
        wr(ctx + 8, (rd(ctx + 8) + 4) & 0xffffffff)
        return True
    if op == 31:
        a = rd(p) & 0xffffffff
        d = rd(p + 4) & 0xffffffff
        wr(d, a)
        wr(ctx + 8, (rd(ctx + 8) + 8) & 0xffffffff)
        return True
    if op == 32:
        a = rd(p) & 0xffffffff
        d = rd(p + 4) & 0xffffffff
        wr(d, rd(a) & 0xffffffff)
        wr(ctx + 8, (rd(ctx + 8) + 8) & 0xffffffff)
        return True
    if op == 40:
        sp = rd(ctx + 12) & 0xffffffff
        a = rd(p) & 0xffffffff
        d = rd(p + 4) & 0xffffffff
        wr(d, (sp - a) & 0xffffffff)
        wr(ctx + 8, (rd(ctx + 8) + 8) & 0xffffffff)
        return True
    return False

def step_control(rd, wr, ctx, op, p, native):
    if op == 1:
        sp = rd(ctx + 12) - 4
        wr(ctx + 12, sp)
        t = rd(sp)
        if t == 0:
            return 0
        wr(ctx + 8, t)
        return None
    if op == 8:
        wr(rd(ctx + 12), rd(p))
        wr(ctx + 12, rd(ctx + 12) + 4)
        wr(ctx + 8, rd(ctx + 8) + 4)
        return None
    if op == 12:
        wr(ctx + 12, rd(ctx + 12) - rd(p))
        wr(ctx + 8, p + 4)
        return None
    if op == 5:
        h = rd(p)
        wr(ctx + 8, p + 4)
        f = rd(rd(ctx + 8))
        wr(ctx + 8, rd(ctx + 8) + 4)
        v = native(h, f)
        wr(rd(rd(ctx + 8)), v)
        wr(ctx + 8, rd(ctx + 8) + 4)
        return None
    raise NotImplementedError(op)

def expression_native(rd, rb, handler, frame):
    if handler == 0x411C40:
        if rd(frame) != 0 or rb(frame + 4) != 13:
            raise NotImplementedError
        app = rd(0x530C94)
        return rb(app + 0xF1F)
    if handler == 0x418650:
        if rd(frame) != 9 or rd(frame + 4) != 3:
            raise NotImplementedError
        parent = rd(0x530EB4)
        if parent == 0:
            return 0
        return rb(parent + 0x4F5) | rb(parent + 0x4F4)
    if handler == 0x414160:
        app = rd(0x530C94)
        if rb(app + 0xF92) != 0:
            keys = (0x1D, 0x9D)
        else:
            keys = (0x2A, 0x36)
        kbd = rd(0x530CA4)
        if rd(kbd) not in (0x518704, 0x519610, 0x51A054):
            raise NotImplementedError
        if rb(kbd + 4) not in (0, 1):
            raise NotImplementedError
        base = kbd + 5 + ((rb(kbd + 4) ^ 1) << 8)
        if rb(base + keys[0]) & 0x80:
            return 1
        return int(bool(rb(base + keys[1]) & 0x80))
    raise NotImplementedError

def run_vm(rd, wr, rb, ctx, entry, native, max_steps=10000):
    if rb(ctx + 24) != 0 and rd(ctx + 20) != 0:
        raise NotImplementedError

    wr(ctx + 8, entry)
    wr(rd(ctx + 12), 0)
    wr(ctx + 12, rd(ctx + 12) + 4)

    trace = []
    for step in range(1, max_steps + 1):
        pc = rd(ctx + 8)
        op = rd(pc)
        p = pc + 4
        wr(ctx + 8, p)
        trace.append({'pc': pc, 'opcode': op})

        if op in (1, 5, 8, 12):
            c = step_control(rd, wr, ctx, op, p, native)
            if c is not None:
                return {'return_code': c, 'trace': trace, 'steps': step}
        elif op in (26, 31, 32, 40):
            step_memory(rd, wr, ctx, op, p)
        elif op == 23:
            wr(rd(p + 4), value_op(23, rd(p)))
            wr(ctx + 8, rd(ctx + 8) + 8)
        elif op in (13, 19, 20, 44, 45):
            a = rd(p)
            b = rd(p + 4)
            d = rd(p + 8)
            wr(d, value_op(op, a, b))
            wr(ctx + 8, rd(ctx + 8) + 12)
        else:
            raise NotImplementedError(op)

    raise RuntimeError

def record_value(item, base, rd, eval_expr, var_map):
    k = item['kind']
    if k == 'always':
        return 1
    elif k == 'empty':
        return 0
    elif k == 'literal':
        return item['value']
    elif k == 'inline':
        if item['data_size'] != 0:
            return base + item['data_offset']
        else:
            return 0
    elif k == 'array':
        return rd(var_map[item['bank_index']] + 4 * item['element_index'])
    elif k == 'expression':
        return eval_expr(item['expression'])
    else:
        raise NotImplementedError(k)

def record_arguments(record, base, rd, eval_expr, var_map):
    c = record_value(record['condition'], base, rd, eval_expr, var_map) & 0xffffffff
    if record['opcode'] == 0:
        c = int(c == 0)
    if c == 0:
        return {'accepted': False, 'condition_value': 0, 'params': []}
    params = []
    for item in record['items']:
        params.append((item['flags'],
                       record_value(item, base, rd, eval_expr, var_map) & 0xffffffff))
    return {'accepted': True, 'condition_value': c, 'params': params}
