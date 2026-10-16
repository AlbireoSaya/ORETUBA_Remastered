from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_CALL, CS_GRP_INT, CS_GRP_JUMP, CS_GRP_RET
from capstone.x86 import X86_OP_IMM

_TERMINATORS = frozenset(("ret", "retf", "iret", "iretd", "iretq", "hlt", "ud0", "ud1", "ud2"))
_UNCOND_JUMPS = frozenset(("jmp", "ljmp"))


def walk_direct_function(read_bytes, ranges, entry, known_entries=(), limit=10000):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    known = set(known_entries)
    edges, unresolved, diags = [], [], []
    visited, todo = set(), [entry]
    count = 0

    def room(addr):
        for start, end in ranges:
            if start <= addr < end:
                return end - addr
        return 0

    while todo:
        site = todo.pop()
        if site in visited:
            continue
        visited.add(site)
        if count >= limit:
            diags.append({"site": site, "kind": "limit"})
            break
        space = room(site)
        if space <= 0:
            diags.append({"site": site, "kind": "out_of_range"})
            continue
        try:
            data = bytes(read_bytes(site, min(15, space)))
        except Exception as exc:
            diags.append({"site": site, "kind": "read_error", "detail": str(exc)})
            continue
        decoded = list(md.disasm(data, site, count=1))
        if not decoded:
            diags.append({"site": site, "kind": "decode_error"})
            continue
        insn = decoded[0]
        if insn.size > len(data):
            diags.append({"site": site, "kind": "truncated"})
            continue
        count += 1
        next_pc = insn.address + insn.size
        mnemonic = insn.mnemonic.lower()
        operands = insn.operands
        imm = operands[-1].imm if operands and operands[-1].type == X86_OP_IMM else None
        if mnemonic in _TERMINATORS or insn.group(CS_GRP_RET) or insn.group(CS_GRP_INT):
            continue
        if insn.group(CS_GRP_CALL):
            if imm is None:
                unresolved.append({"site": site, "kind": "indirect_call"})
            else:
                edges.append({"site": site, "target": imm, "kind": "call"})
            todo.append(next_pc)
            continue
        if insn.group(CS_GRP_JUMP) or insn.mnemonic in ("loop", "loope", "loopne"):
            if imm is None:
                unresolved.append({"site": site, "kind": "indirect_jump"})
            elif mnemonic in _UNCOND_JUMPS:
                if imm in known and imm != entry:
                    edges.append({"site": site, "target": imm, "kind": "tail"})
                else:

                    todo.append(imm)
            else:

                todo.append(imm)
                todo.append(next_pc)
            continue
        todo.append(next_pc)

    edges.sort(key=lambda edge: (edge["site"], edge["target"], edge["kind"]))
    unresolved.sort(key=lambda item: (item["site"], item["kind"]))
    return {"entry": entry, "instruction_count": count, "edges": edges, "unresolved": unresolved, "diagnostics": diags}

from collections import deque

def collect_direct_graph(walk, roots, targets, max_functions=5000, max_instructions=2000000):
    diag, seen, total = [], {}, 0
    queued, queue = set(), deque()
    for e in sorted(set(roots) | set(targets)):
        if e not in queued:
            queued.add(e)
            queue.append(e)

    while queue:
        if len(seen) >= max_functions:
            diag.append("function_budget_exhausted")
            break
        if total >= max_instructions:
            diag.append("instruction_budget_exhausted")
            break
        entry = queue.popleft()
        if entry in seen:
            continue
        res = walk(entry, queued, min(10000, max_instructions - total))
        seen[entry] = res
        total += int(res.get("instruction_count") or 0)
        for ed in res.get("edges") or []:
            if ed.get("kind") in ("call", "tail"):
                tgt = ed.get("target")
                if tgt is not None and tgt not in queued and tgt not in seen:
                    queued.add(tgt)
                    queue.append(tgt)

    return {
        "status": "STATIC_DIRECT_CFG_ONLY",
        "functions": [seen[e] for e in sorted(seen)],
        "budget": {"functions": len(seen), "instructions": total},
        "diagnostics": diag,
    }
