#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xreg.py — 内建 handler 注册表完整枚举 + 与 maps[1] 的索引关系核验。

事实链（本脚本核验）：
  * 管理器 = 0x4154D0 构造的 0x404 字节对象（init `0x414130` 存入 [app+0x19C8]）。
    ⚠️ 旧注释误写 `0x41418C`；2026-10-08 按 `执行模型.md` §〇/§三 订正（`0x414130` = `malloc(0x404)` → `call 0x4154D0` 的 init 函数；
    `0x4141D9` 是该 init 内调用 `sub_424460` 的调用点）。
  * 其构造第一句 `call 0x422200`（子构造，vtable 0x4EDEF0）先注册 3 个 handler
    （0x4221D0/0x4221B0/0x4221F0 → 写全局 [0x50382C]=2/1/3，即「请求换场」）。
  * 之后 0x41565C..0x422393 的 `push <handler>; mov ecx,esi; call 0x422730` 继续注册。
  * sub_422730 = vector.push_back，向量 = [manager+0x38](begin)/[+0x3C](end)/[+0x40](cap)。
  * **maps[1] 重定位** `code[off] = [manager+0x38][value]`（sub_424D30 循环 B）
    ⇒ maps[1] 的 value 就是该 handler 向量的**下标**；VM op 0x05 调用它。

用法：python -X utf8 xreg.py [--sig N]   # 打印前 N 个 + 全部 handler 地址与首指令
"""
import re
import struct
import sys

import capstone

from pe_min import PE, DUMP_PATH

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
REG = 0x422730
BACK = 64


def enum_registry(pe):
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    lo, hi = va0, va0 + len(code)
    out = []
    for m in re.finditer(rb"\xe8(....)", code, re.S):
        o = m.start()
        rel = int.from_bytes(m.group(1), "little")
        if va0 + o + 5 + rel != REG:
            continue
        for p in range(o - 1, max(-1, o - BACK), -1):
            if (code[p] == 0x68 and p + 7 <= o
                    and code[p + 5:p + 7] == b"\x8b\xce"):
                h = int.from_bytes(code[p + 1:p + 5], "little")
                if lo <= h < hi:
                    out.append((va0 + o, h, va0 + p))
                break
    return out


# 管理器构造函数内注册的 3 个「换场」handler（先于 0x41565C 块）
CTOR_HANDLERS = [0x4221D0, 0x4221B0, 0x4221F0]


def first_insn(pe, va, n=4):
    off = pe.rva_to_off(va - pe.image_base)
    out = []
    for ins in md.disasm(pe.data[off:off + 64], va):
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
        if len(out) >= n:
            break
    return " ; ".join(out)


def main():
    pe = PE(DUMP_PATH)
    regs = enum_registry(pe)
    print("注册调用点 = %d, 配对 handler = %d, 不同 handler = %d"
          % (len(regs), len(regs), len(set(h for _, h, _ in regs))))
    # 构成向量下标：ctor 3 个在前（顺序 = 构造函数中 call 0x422730 的先后）
    print("\n== 向量下标 0..2（0x422200 构造第一句 call，先于 0x41565C 块）==")
    for i, h in enumerate(CTOR_HANDLERS):
        print("  [%3d] 0x%08X  %s" % (i, h, first_insn(pe, h)))
    print("\n== 向量下标 3.. （注册顺序，前 40）==")
    for i, (cva, h, pva) in enumerate(regs[:40]):
        print("  [%3d] 0x%08X  %s" % (i + 3, h, first_insn(pe, h)))
    print("  ... 共 %d 项（下标 3..%d）" % (len(regs), len(regs) + 2))
    # 统计 maps[1] 值域
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
    from decode_sob0 import Sob0
    root = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") \
        else r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT"
    mx, cnt, vals = -1, 0, {}
    for fn in sorted(os.listdir(root)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            sob = Sob0(os.path.join(root, fn))
        except Exception:
            continue
        for v in sob.maps[1].values():
            cnt += 1
            mx = max(mx, v)
            vals[v] = vals.get(v, 0) + 1
    print("\n== maps[1] 值域（%s，%d 文件）==" % (os.path.basename(root), len(os.listdir(root))))
    print("  项数=%d  max(value)=%d  不同值=%d" % (cnt, mx, len(vals)))
    print("  0/1/2 出现次数 = %s（= 构造函数注册的 3 个换场 handler 下标）"
          % {k: vals.get(k, 0) for k in (0, 1, 2)})
    print("  max 是否 < 798(handler 总数+3?) : %s" % (mx < len(regs) + 3))


if __name__ == "__main__":
    main()
