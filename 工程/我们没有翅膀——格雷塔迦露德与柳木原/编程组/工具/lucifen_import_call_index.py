"""Linear-scan candidate index of absolute-IAT CALL/JMP sites.

This module performs a purely linear disassembly pass over the supplied
byte buffer and reports only CALL/JMP instructions whose single operand is
an absolute memory reference (mem.base, mem.index, mem.segment all zero)
whose 32-bit displacement matches a key in ``iat_names``.

The result is a candidate index only.  A linear sweep may step through
mixed code and data, so these hits do NOT prove CFG reachability, do NOT
prove that the site is actually invoked, and do NOT constitute original
binary restoration or any self-test.  Output exists solely to help the
root batch perform semantic triage.  No file I/O, no embedded game bytes,
no OS loading.  Only the workspace root applies candidates; this module
does not use Git, does not monopolize or revert others' changes, and does
not invoke pause roles.  Non-translation spec unchanged; cache plus new
parallel rules acknowledged.
"""

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM


def collect_import_call_sites(code: bytes, start_va: int, iat_names: dict) -> list:
    """Return candidate absolute-IAT CALL/JMP sites via linear disassembly.

    Each hit is a dict with keys: address, size, mnemonic, iat, name.
    """
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True

    hits = []
    for insn in md.disasm(code, start_va):
        if insn.id == 0:
            continue
        if insn.mnemonic not in ("call", "jmp"):
            continue
        operands = insn.operands
        if len(operands) != 1:
            continue
        op = operands[0]
        if op.type != X86_OP_MEM:
            continue
        mem = op.mem
        if mem.base != 0 or mem.index != 0 or mem.segment != 0:
            continue
        iat = mem.disp & 0xFFFFFFFF
        name = iat_names.get(iat)
        if name is None:
            continue
        hits.append({
            "address": insn.address,
            "size": insn.size,
            "mnemonic": insn.mnemonic,
            "iat": iat,
            "name": name,
        })
    return hits
