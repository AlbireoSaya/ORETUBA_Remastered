def copy_cstr_guest(uc, dst, src, limit=4096):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be positive non-bool int")
    buf = bytearray()
    for i in range(limit):
        b = uc.mem_read(src + i, 1)[0]
        buf.append(b)
        if b == 0:
            n = i + 1
            break
    else:
        raise ValueError("NUL not found within limit")
    if src < dst + n and dst < src + n:
        raise ValueError("src/dst ranges overlap")
    uc.mem_write(dst, bytes(buf))
    return dst

import struct
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EIP

def stdcall_lstrcpy_gate(uc):
    sp = uc.reg_read(UC_X86_REG_ESP)
    ret, dst, src = struct.unpack('<III', uc.mem_read(sp, 12))
    if copy_cstr_guest(uc, dst, src, limit=260) is False:
        raise RuntimeError('copy_cstr_guest failed')
    uc.reg_write(UC_X86_REG_EAX, dst)
    uc.reg_write(UC_X86_REG_ESP, sp + 12)
    uc.reg_write(UC_X86_REG_EIP, ret)
    return {'destination': dst, 'source': src, 'return_va': ret,
            'esp_before': sp, 'esp_after': sp + 12}