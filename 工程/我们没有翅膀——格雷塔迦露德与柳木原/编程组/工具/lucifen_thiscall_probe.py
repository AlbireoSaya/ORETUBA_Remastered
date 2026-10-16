import struct
from unicorn.x86_const import UC_X86_REG_EIP as EIP, UC_X86_REG_ESP as ESP, UC_X86_REG_EAX as EAX, UC_X86_REG_ECX as ECX

def _u32(v):
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 0xFFFFFFFF:
        raise ValueError("not a u32 int: %r" % (v,))
    return v

def invoke_thiscall_args(uc, address, obj, args, count=100000, timeout=1000000, esp0=0x2008000, sentinel=0x200F000):
    args = tuple(args)
    obj = _u32(obj)
    values = tuple(_u32(a) for a in args)
    uc.mem_write(esp0, b"".join(struct.pack("<I", n) for n in (sentinel,) + values))
    uc.reg_write(ESP, esp0)
    uc.reg_write(ECX, obj)
    uc.emu_start(address, sentinel, count=count, timeout=timeout)
    if uc.reg_read(EIP) != sentinel or uc.reg_read(ESP) != esp0 + 4 + 4 * len(values):
        raise RuntimeError("thiscall emulation did not return cleanly")
    return uc.reg_read(EAX) & 0xFFFFFFFF
