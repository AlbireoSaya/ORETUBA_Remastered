from r_dynamic_bind_reference import bind_expression
from lucifen_inline_vm_reference import run_vm

U32 = 0xFFFFFFFF


def evaluate_parameter(rd, wr, rb, wb, ctx, source_base, expr, maps, string_base, native, max_steps=10000):
    bound = bind_expression(rb, wb, wr, source_base, expr, maps, string_base)
    entry = (source_base + expr["code_start"]) & U32
    vm = run_vm(rd, wr, rb, ctx, entry, native, max_steps, resume=False)
    value = rd(maps[2][0]) & U32
    return {
        "value": value,
        "vm": vm,
        "bound": bound,
    }
