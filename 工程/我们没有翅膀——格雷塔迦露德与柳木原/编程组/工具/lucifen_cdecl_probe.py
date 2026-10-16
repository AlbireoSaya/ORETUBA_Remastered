import struct
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX

def invoke_cdecl(uc, address, args, count=2000000, timeout=1000000):
    for v in args:
        if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= 0xffffffff):
            raise ValueError("args must be non-bool u32 ints")
    esp = 0x2008000
    sentinel = 0x200f000
    payload = struct.pack("<I", sentinel) + b"".join(struct.pack("<I", v) for v in args)
    uc.mem_write(esp, payload)
    uc.reg_write(UC_X86_REG_ESP, esp)
    uc.emu_start(address, sentinel, timeout=timeout, count=count)
    if uc.reg_read(UC_X86_REG_EIP) != sentinel or uc.reg_read(UC_X86_REG_ESP) != esp + 4:
        raise RuntimeError("cdecl return check failed")
    return uc.reg_read(UC_X86_REG_EAX)