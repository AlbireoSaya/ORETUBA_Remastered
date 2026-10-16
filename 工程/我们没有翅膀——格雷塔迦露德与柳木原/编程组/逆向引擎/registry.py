#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内建命令「注册表」枚举（R1 修复过程的新发现；T1 修正窗长）。

模式：`68 <handler_VA> ... E8 <rel32->0x422730>` —— 把原生处理函数登记进注册表。
`sub_422730` 实为容器追加（vector push_back 形态：维护 [this+0x34]/[this+0x38]/[this+0x3C]）。

**T1 订正**：旧版用「push 与 call 间 16 字节固定窗」，漏掉 `0x41565C` 的
`push 0x417DC0`（其后夹了一条 11 字节的 `mov word[...]`，push→E8 恰 16 字节、越窗）。
现改为**从调用点向前搜索最近的 `push imm32`**（窗 48 字节），不再受中间指令长度影响。

用法：python -X utf8 registry.py
"""
import re

from pe_min import PE, DUMP_PATH

REG = 0x422730
BACK = 48


def main():
    pe = PE(DUMP_PATH)
    s = [x for x in pe.sections if x["name"] == ".text"][0]
    code = pe.data[s["rawptr"]:s["rawptr"] + s["rawsize"]]
    va0 = pe.image_base + s["vaddr"]
    lo, hi = va0, va0 + len(code)

    # 1) 所有 call 0x422730 的调用点
    calls = []
    for m in re.finditer(rb"\xe8(....)", code, re.S):
        o = m.start()
        rel = int.from_bytes(m.group(1), "little")
        if va0 + o + 5 + rel == REG:
            calls.append(o)

    # 2) 每个调用点**向前**找最近的 `68 <handler> 8B CE`（push 后紧跟 mov ecx,esi）
    ptrs = []
    for c in calls:
        for p in range(c - 1, max(-1, c - BACK), -1):
            if (code[p] == 0x68 and p + 7 <= c
                    and code[p + 5:p + 7] == b"\x8b\xce"):   # push imm32; mov ecx,esi
                h = int.from_bytes(code[p + 1:p + 5], "little")
                if lo <= h < hi:                              # handler 应是本模块代码指针
                    ptrs.append((va0 + p, va0 + c, h))
                break

    hs = [h for _, _, h in ptrs]
    print("注册调用点(call E8)数 =", len(calls),
          " 配对 push<handler> =", len(ptrs),
          " 不同处理函数 =", len(set(hs)))
    print("调用点(E8) VA 跨度 = 0x%X .. 0x%X" % (va0 + min(calls), va0 + max(calls)))
    print("push(handler) VA 跨度 = 0x%X .. 0x%X" % (ptrs[0][0], ptrs[-1][0]))
    print("处理函数 VA 范围 = 0x%X .. 0x%X" % (min(hs), max(hs)))
    print("前 20 个处理函数（按注册顺序）：")
    for pva, cva, h in ptrs[:20]:
        print("   push@0x%08X call@0x%08X -> handler 0x%08X" % (pva, cva, h))


if __name__ == "__main__":
    main()
