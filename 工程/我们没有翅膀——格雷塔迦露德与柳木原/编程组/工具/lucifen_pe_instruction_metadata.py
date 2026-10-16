"""
Bounded x86-32 instruction metadata extraction for an already-mapped PE image.

The caller guarantees the PE mapping is complete.  This module never parses or
maps the PE itself, never writes anywhere, and never emits raw instruction
bytes; it only decodes the supplied byte range and reports metadata.
"""

from __future__ import annotations

from capstone import CS_ARCH_X86, CS_GRP_CALL, CS_GRP_JUMP, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

MAX_BYTES = 65536
MAX_INSTRUCTIONS = 4096


def _as_int(name: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s must be int, got %s" % (name, type(value).__name__))
    return value


def disassemble_bounded(pe, start_va, byte_count, max_instructions=4096):
    """Decode up to max_instructions instructions inside a byte range.

    The range is [start_va, start_va + byte_count) expressed as virtual
    addresses; only that range is decoded and no reachability is claimed.
    Returns a list of dicts with keys va, size, mnemonic, op_str,
    direct_target and memory_displacements.
    """
    start_va = _as_int("start_va", start_va)
    byte_count = _as_int("byte_count", byte_count)
    max_instructions = _as_int("max_instructions", max_instructions)
    if start_va <= 0:
        raise ValueError("start_va must be > 0")
    if not 1 <= byte_count <= MAX_BYTES:
        raise ValueError("byte_count must be in [1, %d]" % MAX_BYTES)
    if not 1 <= max_instructions <= MAX_INSTRUCTIONS:
        raise ValueError("max_instructions must be in [1, %d]" % MAX_INSTRUCTIONS)

    code = pe.read_rva(start_va - pe.image_base, byte_count)
    if code is None or len(code) != byte_count:
        got = 0 if code is None else len(code)
        raise ValueError("read_rva returned %d bytes, expected %d" % (got, byte_count))

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    results = []
    for insn in md.disasm(code, start_va):
        if len(results) >= max_instructions:
            break
        direct_target = None
        if insn.group(CS_GRP_CALL) or insn.group(CS_GRP_JUMP):
            for op in insn.operands:
                if op.type == X86_OP_IMM:
                    direct_target = op.imm
                    break
        results.append({
            "va": insn.address,
            "size": insn.size,
            "mnemonic": insn.mnemonic,
            "op_str": insn.op_str,
            "direct_target": direct_target,
            "memory_displacements": [
                op.mem.disp for op in insn.operands if op.type == X86_OP_MEM
            ],
        })
    return results