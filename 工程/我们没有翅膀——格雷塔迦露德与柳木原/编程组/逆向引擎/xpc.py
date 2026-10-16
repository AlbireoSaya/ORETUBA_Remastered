#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xpc.py — 从 **exe 侧**列出「能改写 VM 的 pc（ctx+0x8）的 opcode」——切分判据 C2 的根据。

用途（M1，ISSUE-20261008-04）
    切分判据的「控制流目标集」必须**完备**：漏一个能跳转的 op，就会有代码被误判为「不可达」。
    本脚本逐字反汇编 VM 主循环的分派表 `0x433B54` 的 47 个 handler（`执行模型.md` §4.4），
    找出所有 `mov dword ptr [esi + 8], <reg/mem>`（esi = ctx，`ctx+8` = pc）的写入点，
    并归到对应 opcode。**唯一真正的「跳转类」写入**会把 pc 设成非直落值；其余是各 handler
    结尾把 pc 前进到 `edi + N*4` 的常规推进。

结论（本件实测，可复跑）
    静态可转移控制权的 op 只有 6 个：
      0x00 HALT_OK（返回 1，结束 VM 帧）、0x01 RET（pc = pop）、0x02 RETVAL_RET（pc = pop，
      且 a==0 时直接返回 VM）、0x04 CALL（pc = *op）、0x06 JMP（pc = *op）、
      0x07 TABJMP（pc = table[*(op)]）、0x1E JZ（*op0==0 → pc = op1，否则直落）。
    ⇒ 目标集 = {0x04/0x06/0x1E 的操作数, 0x07 表项}；0x01/0x02 的目标来自运行期栈（动态），
      不产生静态边 —— 这正是「静态不可达区」（见 xvseg.py --evidence）无法解释的部分。

目标 exe：`D:\\Gal\\[Navel]我们没有翅膀\\ORE_TUBA.EXE`（只读）。全节反汇编 `skipdata=True`。
用法：python -X utf8 xpc.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xdis import PE, EXES, md  # noqa: E402

H = {0x00: 0x433B43, 0x01: 0x433687, 0x02: 0x4336A1, 0x03: 0x4336C1, 0x04: 0x4336D2,
     0x05: 0x4336EC, 0x06: 0x433716, 0x07: 0x433720, 0x08: 0x43372E, 0x09: 0x43374A,
     0x0A: 0x433753, 0x0B: 0x433771, 0x0C: 0x433786, 0x0D: 0x43379B, 0x0E: 0x4337B4,
     0x0F: 0x4337CD, 0x10: 0x4337E5, 0x11: 0x4337FD, 0x12: 0x433815, 0x13: 0x43383B,
     0x14: 0x433854, 0x15: 0x43386D, 0x16: 0x433886, 0x17: 0x43389D, 0x18: 0x4338B9,
     0x19: 0x4338D2, 0x1A: 0x4338EB, 0x1B: 0x4338FF, 0x1C: 0x433913, 0x1D: 0x43392C,
     0x1E: 0x433945, 0x1F: 0x433965, 0x20: 0x43397A, 0x21: 0x433991, 0x22: 0x4339A8,
     0x23: 0x4339FE, 0x24: 0x4339C2, 0x25: 0x4339DE, 0x26: 0x433A1A, 0x27: 0x433A38,
     0x28: 0x433A51, 0x29: 0x433A6B, 0x2A: 0x433A8E, 0x2B: 0x433AB1, 0x2C: 0x433AD0,
     0x2D: 0x433AEF, 0x2E: 0x433B0E}
JUMP = {0x00: "HALT_OK(结束 VM 帧)", 0x01: "RET(pc=pop 动态)", 0x02: "RETVAL_RET(pc=pop 动态)",
        0x04: "CALL(pc=*op1)", 0x06: "JMP(pc=*op1)", 0x07: "TABJMP(pc=table[idx])",
        0x1E: "JZ(op1)"}


def main():
    pe = PE(EXES["ORE"])
    rev = {v: k for k, v in H.items()}
    lo, hi = 0x433687, 0x433B54
    off = pe.rva_to_off(lo - pe.image_base)
    cur = 0x00
    seen = {}
    for ins in md.disasm(pe.data[off:pe.rva_to_off(hi - pe.image_base)], lo):
        if ins.address in rev:
            cur = rev[ins.address]
        if "dword ptr [esi + 8]" in ins.op_str and ins.mnemonic.startswith("mov"):
            seen.setdefault(cur, []).append((ins.address, ins.op_str))
    print("== handler 中写 ctx+0x8（pc）的指令，按 opcode 归类（0x%X..0x%X）==" % (lo, hi))
    for op in sorted(seen):
        tag = JUMP.get(op, "（常规 pc 推进到 edi+N*4，非跳转）")
        print("  op%02X %-34s 写点数=%-3d 首例 0x%X %s"
              % (op, tag, len(seen[op]), seen[op][0][0], seen[op][0][1]))
    print("\n== 可静态转移控制权的 opcode（切分判据 C2 的目标集来源）==")
    for op in sorted(JUMP):
        print("  op%02X  %-28s handler=0x%X" % (op, JUMP[op], H[op]))
    print("  说明：op00（HALT_OK，handler 0x433B43）体为 `return 1`，**不写 pc**，故未出现在上表；"
          "op05 的 5 处写点中 4 处是常规推进 / 传参（`pc=&op2` 供 handler 读实参），**不构成静态边**。")


if __name__ == "__main__":
    main()
