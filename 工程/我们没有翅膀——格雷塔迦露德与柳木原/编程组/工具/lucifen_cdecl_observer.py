import struct

from unicorn import UcError
from unicorn.unicorn_const import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX,
    UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP,
    UC_X86_REG_ESP, UC_X86_REG_EIP,
)

SP0 = 0x2008000
SENTINEL = 0x200F000

_SEED_REGS = {
    "eax": UC_X86_REG_EAX, "ebx": UC_X86_REG_EBX, "ecx": UC_X86_REG_ECX,
    "edx": UC_X86_REG_EDX, "esi": UC_X86_REG_ESI, "edi": UC_X86_REG_EDI,
    "ebp": UC_X86_REG_EBP,
}


def _is_u32(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 0xFFFFFFFF


def observe_cdecl_until(uc, entry, frame_ptr, stop_pc, read_stack_words=8,
                        register_seeds=None, count=100000, timeout=1000000):
    """Run cdecl callee from entry until stop_pc, sentinel return, count or timeout."""
    if not (_is_u32(entry) and _is_u32(frame_ptr) and _is_u32(stop_pc)):
        raise ValueError("entry/frame_ptr/stop_pc must be u32 non-bool")
    if not isinstance(read_stack_words, int) or isinstance(read_stack_words, bool) \
            or not 0 <= read_stack_words <= 32:
        raise ValueError("read_stack_words must be int in 0..32")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ValueError("count must be a positive int")
    seeds = {} if register_seeds is None else register_seeds
    if not isinstance(seeds, dict):
        raise ValueError("register_seeds must be a dict")
    for name, value in seeds.items():
        if name not in _SEED_REGS or not _is_u32(value):
            raise ValueError("bad register seed: %r" % (name,))

    uc.mem_write(SP0, struct.pack("<II", SENTINEL, frame_ptr))
    for name, value in seeds.items():
        uc.reg_write(_SEED_REGS[name], value)
    uc.reg_write(UC_X86_REG_ESP, SP0)
    uc.reg_write(UC_X86_REG_EIP, entry)

    state = {"reached": False}
    error = None
    hook = None
    try:
        def _on_code(_uc, address, _size, _user):
            if address == stop_pc:
                state["reached"] = True
                _uc.emu_stop()

        hook = uc.hook_add(UC_HOOK_CODE, _on_code)
        try:
            uc.emu_start(entry, SENTINEL, count=count, timeout=timeout)
        except UcError as exc:
            error = str(exc)
    finally:
        if hook is not None:
            uc.hook_del(hook)

    eip = uc.reg_read(UC_X86_REG_EIP) & 0xFFFFFFFF
    esp = uc.reg_read(UC_X86_REG_ESP) & 0xFFFFFFFF
    result = {
        "stop_reached": state["reached"],
        "returned": (not state["reached"]) and eip == SENTINEL,
        "eip": eip,
        "esp": esp,
        "eax": uc.reg_read(UC_X86_REG_EAX) & 0xFFFFFFFF,
        "ecx": uc.reg_read(UC_X86_REG_ECX) & 0xFFFFFFFF,
        "edx": uc.reg_read(UC_X86_REG_EDX) & 0xFFFFFFFF,
        "stack_words": None,
        "error": error,
    }
    if read_stack_words:
        try:
            raw = uc.mem_read(esp, read_stack_words * 4)
            result["stack_words"] = list(
                struct.unpack("<%dI" % read_stack_words, bytes(raw)))
        except UcError as exc:
            result["stack_error"] = str(exc)
    else:
        result["stack_words"] = []
    return result
