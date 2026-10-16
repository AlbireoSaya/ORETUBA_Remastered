import sys
import json
import struct
import hashlib

sys.path.insert(0, r"E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/逆向引擎")
from pe_min import PE
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM

EVIDENCE = 'local_signature_candidates_not_runtime_vector'


def pick_text(sections):
    for s in sections:
        name = s.get('name')
        if name == '.text' or name == b'.text':
            return s
    return None


def main():
    p = PE(sys.argv[1])
    data = p.data
    if p.machine != 0x14c or p.magic != 0x10b:
        raise ValueError("unsupported PE: expected 32-bit i386 PE32 (machine 0x14c, magic 0x10b)")
    image_base = p.image_base
    sec = pick_text(p.sections)
    groups = {}
    if sec is not None:
        rawptr = sec['rawptr']
        rawsize = sec['rawsize']
        va0 = image_base + sec['vaddr']
        text_end = rawptr + rawsize
        va_end = va0 + rawsize
        cs = Cs(CS_ARCH_X86, CS_MODE_32)
        cs.detail = True
        cs.skipdata = False
        i = rawptr
        last = text_end - 5
        while i <= last:
            if data[i] != 0xE8:
                i += 1
                continue
            calloff = i
            call_va = va0 + (calloff - rawptr)
            target_va = call_va + 5 + struct.unpack_from('<i', data, calloff + 1)[0]
            if va0 <= target_va < va_end:
                lo = max(rawptr, calloff - 64)
                j = calloff - 7
                match = None
                while j >= lo:
                    if data[j] == 0x68 and data[j + 5] == 0x8B and data[j + 6] == 0xCE:
                        handler_va = struct.unpack_from('<I', data, j + 1)[0]
                        if va0 <= handler_va < va_end:
                            match = (j, handler_va)
                            break
                    j -= 1
                if match is not None:
                    pushoff, handler_va = match
                    push_va = va0 + (pushoff - rawptr)
                    good = False
                    for insn in cs.disasm(data[pushoff:calloff + 5], push_va):
                        if insn.address >= call_va:
                            if (insn.address == call_va and insn.mnemonic == 'call'
                                    and insn.address + insn.size == call_va + 5
                                    and insn.operands
                                    and insn.operands[0].type == CS_OP_IMM
                                    and (insn.operands[0].imm & 0xFFFFFFFF) == (target_va & 0xFFFFFFFF)):
                                good = True
                            break
                        if insn.address + insn.size > call_va:
                            break
                    if good:
                        groups.setdefault(target_va, []).append({
                            'push_va': push_va,
                            'call_va': call_va,
                            'handler_va': handler_va,
                            'push_fileoffset': pushoff,
                            'call_fileoffset': calloff,
                        })
            i += 1
    out = []
    for target_va, rows in groups.items():
        out.append({
            'rows': rows,
            'count': len(rows),
            'unique_handlers': len({r['handler_va'] for r in rows}),
            'target_va': target_va,
        })
    out.sort(key=lambda g: (-g['count'], g['target_va']))
    result = {
        'exe_sha256': hashlib.sha256(data).hexdigest(),
        'exe_bytes': len(data),
        'image_base': image_base,
        'groups': out,
        'evidence_level': EVIDENCE,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()