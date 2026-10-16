#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_26_tokendsl.py — 反汇编并解码 PC 的**立绘方向 token DSL**(原生实现) (只读).

背景: 场景脚本的 `sp_move`(V=0x18B74 / 0x186C8) 实参里带方向 token 串(`c`/`l`/`r`/`<2`/`!l`/`$`/`d`/`u` …).
      本次实测: 「效果/精灵移动」命令名表在 `.data 0x4FB22C`(8 项: sp_move/bg_move/quake/noise/paper/light/snow/rain),
      由 `0x41D55F` 一带逐项注册 ⇒ **`sp_move` 的原生实现 = `0x4033A0`**;
      `0x4033A0` 先调 **`0x402970`** 把 token 串解析成 (dx, dy), 再 `call [obj_vtbl+0x38]`((= 0x46CF30 位置 setter)落位。
      `0x402970` 内用**字符分派表**:
        0x402ED0 = 9 项 u32 跳转表 ; 0x402EF4 = 0x56 字节索引表(索引 = 字符 - 0x20)

用法: python -X utf8 _probe_26_tokendsl.py
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ⚠️ 旧开发位置（`子代理工作区\ISSUE-20261008-09\EXE\`）= **历史副本，勿用**；
#    本探针不入复跑链，未改常量（`EXE = HERE\work\ORE_TUBA.EXE` 为已剔出库件 ⇒ 需先备齐才能跑通）。
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-09\EXE")
from _probe_common import PE, dis, fmt   # noqa: E402

EXE = os.path.join(HERE, "work", "ORE_TUBA.EXE")
RES = []


def chk(tag, ok, detail):
    RES.append(ok)
    print("  [%s] %s  %s" % ("PASS" if ok else "FAIL", tag, detail))


def main():
    pe = PE(EXE)

    # 1) 效果/移动命令名表
    tbl = [struct.unpack_from("<I", pe.read_va(0x4FB22C, 0x20), i * 4)[0] for i in range(8)]
    names = [pe.cstr(v, 24).decode("latin1") for v in tbl]
    print("效果/移动命令名表 @0x4FB22C :", names)
    chk("T1 表首项 = sp_move", names[0] == "sp_move", "names=%s" % names)

    # 2) sp_move 原生实现 -> token 解析器
    calls = []
    for ins in dis(pe, 0x4033A0, 0x60):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            calls.append((ins.address, ins.op_str))
    print("0x4033A0 内的 call :", [c[1] for c in calls])
    chk("T2 sp_move 调 0x402970 解析 token", any(c[1] == "0x402970" for c in calls), "%s" % calls)

    # 3) 分派表
    jt = [struct.unpack_from("<I", pe.read_va(0x402ED0, 0x24), i * 4)[0] for i in range(9)]
    bt = pe.read_va(0x402EF4, 0x56)
    mp = {}
    for i, b in enumerate(bt):
        mp.setdefault(b, []).append(chr(0x20 + i))
    print("字符分派(索引=字符-0x20):")
    for b in sorted(mp):
        print("   idx %d -> 0x%X : %r" % (b, jt[b], "".join(mp[b]) if b < 8 else "".join(mp[b])))
    chk("T3 分派表覆盖 'c','l','r','<','>','!','$','d','u'",
        all(ch in "".join(mp.get(1, []) + mp.get(8, [])) or ch in "".join(mp[1]) for ch in "clr<>!$")
        and "d" in mp[1] and "u" in mp[1], "idx1=%r" % "".join(mp[1]))

    # 4) 关键常量 (位置算术)
    code = pe.read_va(0x402970, 0x60A)
    hexs = code.hex()
    has_sar2 = "c1f902" in hexs or "c1fe02" in hexs       # sar ecx,2 / sar esi,2  (÷4)
    has_25a = "83c619" in hexs and "83c719" in hexs       # add esi,0x19 / add edi,0x19
    has_25s = "83ee19" in hexs and "83ef19" in hexs       # sub esi,0x19 / sub edi,0x19
    chk("T4 含 ÷4 (`sar …,2`)", has_sar2, "sar …,2 = %s" % has_sar2)
    chk("T5 含 ±25 (`add/sub …,0x19`)", has_25a and has_25s, "add19=%s sub19=%s" % (has_25a, has_25s))
    chk("T6 0..1500 内无位置常量", not any(struct.pack("<I", v) in code
                                        for v in (236, 336, 436, 640, 844, 944, 1044, 304, 404)),
        "扫描 236/336/436/640/844/944/1044/304/404 = 0 命中")

    # 5) 落位出口 = obj vtable+0x38
    outs = [ins.op_str for ins in dis(pe, 0x4033A0, 0x80)
            if ins.mnemonic == "call" and "0x38" in ins.op_str]
    chk("T7 落位走 obj_vtbl+0x38 (位置 setter)", bool(outs), "%s" % outs)

    print("\n==== %d/%d PASS ====" % (sum(RES), len(RES)))
    return 0 if all(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
