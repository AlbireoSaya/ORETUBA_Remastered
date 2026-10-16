"""Bounded control-step dispatcher for the lucifen inline VM (_reference)."""

from lucifen_inline_vm_reference import step_control, step_memory

_U32_MAX = 0xFFFFFFFF


def _u32(name, value):
    """Strict non-bool uint32 guard for ctx/op/p."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a non-bool int uint32")
    if not 0 <= value <= _U32_MAX:
        raise ValueError(f"{name} out of uint32 range")
    return value


def step(rd, wr, ctx, op, p, native):
    """Execute exactly one bounded instruction step.

    rd/wr/native are caller-owned callbacks; this is a pure instruction step,
    never an engine loop.  Unknown opcodes propagate NotImplementedError.
    """
    ctx = _u32("ctx", ctx)
    op = _u32("op", op)
    p = _u32("p", p)
    if ctx > _U32_MAX - 12:
        raise ValueError("ctx+12 exceeds the uint32 address space")
    if op == 6:
        wr(ctx + 8, rd(p))
        return None
    if op == 11:
        wr(ctx + 12, (rd(ctx + 12) + rd(p)) & _U32_MAX)
        wr(ctx + 8, (p + 4) & _U32_MAX)
        return None
    if step_memory(rd, wr, ctx, op, p) is True:
        return None
    return step_control(rd, wr, ctx, op, p, native)
