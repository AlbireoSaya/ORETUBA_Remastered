from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_ALL

def map_pe(pe):
    if pe.machine != 0x14c or pe.magic != 0x10b:
        raise ValueError("not a 32-bit PE")
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    align = lambda n: (n + 0xFFF) & ~0xFFF
    uc.mem_map(pe.image_base, align(pe.size_image), UC_PROT_ALL)
    uc.mem_write(pe.image_base, bytes(pe.data[:pe.size_headers]))
    for s in pe.sections:
        uc.mem_write(pe.image_base + s["vaddr"],
                     bytes(pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]))
    uc.mem_map(0x1000000, 0x100000, UC_PROT_ALL)
    uc.mem_map(0x2000000, 0x10000, UC_PROT_ALL)
    return uc

import struct
from unicorn import UcError, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX as ECX, UC_X86_REG_ESP as ESP, UC_X86_REG_EIP as EIP, UC_X86_REG_EAX as EAX

CTX, BC, SB, STOP, DST, SP0 = 0x1000000, 0x1010000, 0x1020000, 0x200f000, 0x1030000, 0x2008000


def _u32(uc, addr):
    return struct.unpack("<I", uc.mem_read(addr, 4))[0]


def execute_vm(uc, entry, fetch, words):
    uc.mem_write(CTX + 8, struct.pack("<II", BC, SB))
    if words:
        uc.mem_write(BC, struct.pack("<%dI" % len(words), *words))
    uc.mem_write(SP0, struct.pack("<I", STOP))
    uc.reg_write(ECX, CTX)
    uc.reg_write(ESP, SP0)
    trace = []

    def on_code(_uc, addr, _size, _ud):
        if addr == fetch:
            pc = _u32(_uc, CTX + 8)
            try:
                opcode = _u32(_uc, pc)
            except UcError:
                opcode = None
            trace.append({"pc": pc, "opcode": opcode})

    uc.hook_add(UC_HOOK_CODE, on_code)
    error = ""
    try:
        uc.emu_start(entry, STOP, timeout=3000000, count=20000)
    except UcError as exc:
        error = str(exc)
    eip = uc.reg_read(EIP)
    return {
        "error": error,
        "EIP": eip,
        "EAX": uc.reg_read(EAX),
        "pc": _u32(uc, CTX + 8),
        "sp": _u32(uc, CTX + 12),
        "words": list(struct.unpack("<%dI" % len(words), uc.mem_read(BC, 4 * len(words)))),
        "dest_word": _u32(uc, DST),
        "stack_words": list(struct.unpack("<4I", uc.mem_read(SB, 16))),
        "trace": trace,
        "returned": eip == STOP,
    }

import struct
from unicorn.x86_const import (UC_X86_REG_ECX, UC_X86_REG_ESP,
                               UC_X86_REG_EAX, UC_X86_REG_EIP)

GC_STACK_TOP = 0x2008000
GC_RET_SENTINEL = 0x200f000

def invoke_thiscall(uc, addr, ctx):
    uc.mem_write(GC_STACK_TOP, struct.pack("<I", GC_RET_SENTINEL))
    uc.reg_write(UC_X86_REG_ECX, ctx)
    uc.reg_write(UC_X86_REG_ESP, GC_STACK_TOP)
    uc.emu_start(addr, GC_RET_SENTINEL, timeout=1000000, count=10000)
    if uc.reg_read(UC_X86_REG_EIP) != GC_RET_SENTINEL:
        raise RuntimeError("thiscall did not return to sentinel")
    return uc.reg_read(UC_X86_REG_EAX)
