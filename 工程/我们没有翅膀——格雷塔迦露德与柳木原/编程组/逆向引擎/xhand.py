#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xhand.py — 内建 handler 的首句形态分档（判据写死，可逐格复现）。

口径（**全文唯一口径，写死如下**）：
  * handler 集合 = `xreg.py` 同款枚举：`.text` 内 `68 <handler_VA> 8B CE E8 <rel→0x422730>`
    的 798 个调用点所配对的 handler VA，**去重** ⇒ 789 个。
  * 「首句」= 从 handler VA 起 capstone 线性反汇编得到的**第 1 条指令**（`skipdata=True`）。
  * 分类键 = **(mnemonic, op_str)** —— capstone 5.0.7 的**原样**字符串，全等匹配。
    （op_str 的寄存器/内存渲染形式随 capstone 版本固定，本工作区实测版本 = 5.0.7。）
  * **不做任何「前 N 句扫描」**：本脚本只判首句。早期文档里的「12 句内 [esp+4]」
    子档已删除（口径不自然、不可复现）。

用法：python -X utf8 xhand.py
"""
import collections
import re

import capstone

from pe_min import PE, DUMP_PATH

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
REG = 0x422730
BACK = 64


def handlers(pe):
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    lo, hi = va0, va0 + len(code)
    hs = []
    for m in re.finditer(rb"\xe8(....)", code, re.S):
        o = m.start()
        rel = int.from_bytes(m.group(1), "little")
        if va0 + o + 5 + rel != REG:
            continue
        for p in range(o - 1, max(-1, o - BACK), -1):
            if code[p] == 0x68 and p + 7 <= o and code[p + 5:p + 7] == b"\x8b\xce":
                h = int.from_bytes(code[p + 1:p + 5], "little")
                if lo <= h < hi:
                    hs.append(h)
                break
    return sorted(set(hs)), len(hs)


def first(pe, va):
    off = pe.rva_to_off(va - pe.image_base)
    for ins in md.disasm(pe.data[off:off + 16], va):
        return ins.mnemonic, ins.op_str
    return None


def main():
    pe = PE(DUMP_PATH)
    U, ncall = handlers(pe)
    print("注册调用点 = %d，不同 handler（去重）= %d" % (ncall, len(U)))
    cat = collections.Counter()
    forms = collections.Counter()
    for h in U:
        f = first(pe, h)
        if f is None:
            cat["(无法解码)"] += 1
            continue
        m, o = f
        forms[(m, o)] += 1
        if (m, o) == ("mov", "eax, dword ptr [esp + 4]"):
            cat["1. mov eax,[esp+4]"] += 1
        elif (m, o) == ("mov", "ecx, dword ptr [esp + 4]"):
            cat["2. mov ecx,[esp+4]"] += 1
        elif (m, o) == ("mov", "edx, dword ptr [esp + 4]"):
            cat["3. mov edx,[esp+4]"] += 1
        elif m == "mov":
            cat["4. 其余 mov"] += 1
        elif m == "push":
            cat["5. push"] += 1
        elif m == "sub":
            cat["6. sub"] += 1
        elif m == "jmp":
            cat["7. jmp"] += 1
        elif m == "xor":
            cat["8. xor"] += 1
        else:
            cat["9. 其它 %s" % m] += 1
    tot = sum(cat.values())
    print("\n== 首句形态分档（判据见文件头；合计 %d）==" % tot)
    s = 0
    for k in sorted(cat):
        print("  %-20s %4d  (%.1f%%)" % (k, cat[k], 100 * cat[k] / tot))
        s += cat[k]
    print("  校验合计 =", s)
    strict = cat["1. mov eax,[esp+4]"] + cat["2. mov ecx,[esp+4]"]
    print("\n档1 严格（eax|ecx,[esp+4]）= %d (%.1f%%)" % (strict, 100 * strict / tot))
    print("档2 放宽（+edx,[esp+4]）    = %d (%.1f%%)" % (strict + cat["3. mov edx,[esp+4]"],
                                                    100 * (strict + cat["3. mov edx,[esp+4]"]) / tot))
    print("档3 非档1（含 edx 首句）    = %d (%.1f%%)" % (tot - strict, 100 * (tot - strict) / tot))
    print("\n== 最常见首句 (mnemonic, op_str) 前 10 ==")
    for (m, o), n in forms.most_common(10):
        print("  %-6s %-44s x%d" % (m, o, n))


if __name__ == "__main__":
    main()
