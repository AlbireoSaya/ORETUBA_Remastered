"""Read-only Unicorn x86-32 native frame snapshot helper for editor-easy."""
import struct

from unicorn.x86_const import UC_X86_REG_ESP


def snapshot_native_frame(uc, ctx, word_count):
    """Read the live native frame; never writes memory, registers or hooks."""
    if isinstance(ctx, bool) or not isinstance(ctx, int) or not 0 <= ctx <= 0xFFFFFFFF:
        raise ValueError("ctx must be a u32 integer, got %r" % (ctx,))
    if isinstance(word_count, bool) or not isinstance(word_count, int) or not 0 <= word_count <= 32:
        raise ValueError("word_count must be an integer in 0..32, got %r" % (word_count,))

    esp = uc.reg_read(UC_X86_REG_ESP)
    frame_ptr = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
    if word_count:
        frame_words = list(struct.unpack("<%dI" % word_count,
                                         uc.mem_read(frame_ptr, word_count * 4)))
    else:
        frame_words = []
    vm_pc = struct.unpack("<I", uc.mem_read(ctx + 8, 4))[0]
    vm_sp = struct.unpack("<I", uc.mem_read(ctx + 12, 4))[0]

    return {
        "esp": esp,
        "frame_ptr": frame_ptr,
        "frame_words": frame_words,
        "vm_pc": vm_pc,
        "vm_sp": vm_sp,
    }

def reference_setup(read32, write32, pc, sp, argc, max_steps=1000):
    M = 0xffffffff
    if isinstance(pc, bool) or not isinstance(pc, int) or not 0 <= pc <= M:
        raise ValueError("pc must be u32")
    if isinstance(sp, bool) or not isinstance(sp, int) or not 0 <= sp <= M:
        raise ValueError("sp must be u32")
    if isinstance(argc, bool) or not isinstance(argc, int) or not 0 <= argc <= 32:
        raise ValueError("argc must be 0..32")
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps <= 0:
        raise ValueError("max_steps must be positive int")
    pc &= M
    sp &= M
    rd = lambda a: read32(a & M) & M
    wr = lambda a, v: write32(a & M, v & M)
    steps = 0
    while steps < max_steps:
        op = rd(pc)
        steps += 1
        if op == 8:
            wr(sp, rd(pc + 4))
            sp = (sp + 4) & M
            pc = (pc + 8) & M
        elif op == 13:
            a, b, c = rd(pc + 4), rd(pc + 8), rd(pc + 12)
            wr(c, a + b)
            pc = (pc + 16) & M
        elif op == 31:
            a, b = rd(pc + 4), rd(pc + 8)
            wr(b, a)
            pc = (pc + 12) & M
        elif op == 32:
            a, b = rd(pc + 4), rd(pc + 8)
            wr(b, rd(a))
            pc = (pc + 12) & M
        elif op == 35:
            a, b = rd(pc + 4), rd(pc + 8)
            wr(b, rd(sp - a))
            pc = (pc + 12) & M
        elif op == 40:
            a, b = rd(pc + 4), rd(pc + 8)
            wr(b, sp - a)
            pc = (pc + 12) & M
        elif op == 5:
            a, b, c = rd(pc + 4), rd(pc + 8), rd(pc + 12)
            fp = b & M
            return {"call_pc": pc, "handler": a, "frame_ptr": fp,
                    "frame_words": [rd(fp + i * 4) for i in range(argc)],
                    "vm_sp": sp, "steps": steps}
        else:
            raise ValueError("unknown op")
    raise ValueError("step budget exceeded")