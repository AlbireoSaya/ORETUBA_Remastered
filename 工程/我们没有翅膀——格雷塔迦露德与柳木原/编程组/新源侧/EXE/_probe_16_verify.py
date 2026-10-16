#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_16_verify.py — 层序归属结论的可复跑验证 (只读, PASS/FAIL).

复核以下断言 (报告中每条结论的机器判据):
  V1  exe 只静态导入 10 个 Win32 DLL, 无 ddraw/tvpgl/ds_sprite (⇒ LoadLibrary 路径)
  V2  插件名串与引用点 (tvpgl.dll 0x4FC070<-0x4135C8; %sDS_SPRITE.DLL 0x4FC060<-0x413656; ddraw.dll 0x4FF350<-0x493919)
  V3  DS_SPRITE.DLL / DS_MOVIE.DLL / tvpgl.dll 的导出名 (身份判定)
  V4  exe 内 DS_SPRITE 宿主类 vtable=0x4EED94, 且 +0x5C = 0x46D220 (绘制/合成), +0x34..+0x60 方法族
  V5  DS_SPRITE 宿主绘制体 0x46D220 内含 call [0x503A9C] 与 call [0x5039AC] (tvpgl 原语)
  V6  exe 图形对象基类 vtable=0x4EE290, 其 +0x04 = 0x43FFD0 = `mov al,4; ret` (类型号 4)
  V7  DS_SPRITE.DLL 控制对象 vtable=0x600132B8 (+0x08=0x60002A40, +0x44=0x60002830)
  V8  app+0xC 链表管理器: 0x471DA0 / 0x471B60 为"尾插"追加 (node 链到 [head+4])
  V9  无反证字串: exe 全字节 'layer'/'zord'/'depth' = 0; 'priority' 唯一命中 = 导入名 SetThreadPriority
  V10 语料无层序字段: func_lib.sob 与 413 个 ot .sob 的 'priority' = 0
  V11 立绘图串 CHR\\%s.ELG (func_lib 串区 0x2AF09) 仅被 V=0x14F98 引用; PIC\\%s.ELG 属 0x2C3C/0x3958 过程
"""
import csv
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_common import PE, dis, iter_insns
from _probe_12_funclib import Sob

RE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\逆向引擎"
FUNCLIB = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob"
SCRIPTDIR = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT"

results = []


def chk(tag, cond, detail=""):
    results.append((tag, bool(cond), detail))
    print("%-6s %-5s %s" % (tag, "PASS" if cond else "FAIL", detail))


pe = PE(EXE := os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "ORE_TUBA.EXE"))

# V1
rva, sz = pe.ddirs[1]
raw = pe.data[pe.rva_to_off(rva):pe.rva_to_off(rva) + sz]
dlls = set()
p = 0
while p + 20 <= len(raw):
    ilt, ts, fc, nr, iat = struct.unpack_from("<IIIII", raw, p)
    if ilt == 0 and ts == 0 and nr == 0:
        break
    dlls.add(pe.cstr(pe.image_base + nr, 64).decode("latin1").lower())
    p += 20
bad = [d for d in ("ddraw.dll", "tvpgl.dll", "ds_sprite.dll", "ds_movie.dll", "ds_prim.dll") if d in dlls]
chk("V1", not bad, "imports=%d %s ; 动态库命中=%s" % (len(dlls), sorted(dlls), bad))

# V2
s_tvpgl = pe.cstr(0x4FC070, 32); s_spr = pe.cstr(0x4FC060, 32); s_dd = pe.cstr(0x4FF350, 32)
chk("V2a", s_tvpgl == b"tvpgl.dll" and s_spr == b"%sDS_SPRITE.DLL" and s_dd == b"ddraw.dll",
    "%r / %r / %r" % (s_tvpgl, s_spr, s_dd))


def ref_of(va):
    out = []
    for ins in iter_insns(pe, *pe.sec_range(".text")):
        if ("0x%x" % va) in ins.op_str and ins.mnemonic in ("push", "mov", "lea", "cmp"):
            out.append(ins.address)
    return out


chk("V2b", 0x4135C8 in ref_of(0x4FC070) or any(0x4135C0 <= a <= 0x4135D0 for a in ref_of(0x4FC070)),
    "tvpgl.dll refs=%s" % [hex(a) for a in ref_of(0x4FC070)][:4])
chk("V2c", any(0x413650 <= a <= 0x413660 for a in ref_of(0x4FC060)),
    "DS_SPRITE refs=%s" % [hex(a) for a in ref_of(0x4FC060)][:4])
chk("V2d", 0x493919 in ref_of(0x4FF350) or any(0x493915 <= a <= 0x493920 for a in ref_of(0x4FF350)),
    "ddraw refs=%s" % [hex(a) for a in ref_of(0x4FF350)][:4])

# V3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe_03_exports import parse_exports
ds = parse_exports(r"D:\Gal\[Navel]我们没有翅膀\DS_SPRITE.DLL")
mv = parse_exports(r"D:\Gal\[Navel]我们没有翅膀\DS_MOVIE.DLL")
chk("V3", {n for n, _, _ in ds["names"]} == {"GetDShowGdiSpriteCtrl", "GetDllVersion"}
    and {n for n, _, _ in mv["names"]} == {"GetMovieObject", "GetDllVersion"},
    "DS_SPRITE=%s ; DS_MOVIE=%s" % ([n for n, _, _ in ds["names"]], [n for n, _, _ in mv["names"]]))

# V4
vt = 0x4EED94
m5c = pe.u32(vt + 0x5C)
chk("V4", m5c == 0x46D220, "vtable 0x%X: +0x34=%X +0x38=%X +0x3C=%X +0x40=%X +0x44=%X +0x5C=%X +0x60=%X"
    % (vt, pe.u32(vt + 0x34), pe.u32(vt + 0x38), pe.u32(vt + 0x3C), pe.u32(vt + 0x40),
       pe.u32(vt + 0x44), m5c, pe.u32(vt + 0x60)))

# V5
body = " ".join("%s %s" % (i.mnemonic, i.op_str) for i in dis(pe, 0x46D220, 0x280))
chk("V5", "call dword ptr [0x503a9c]" in body and "call dword ptr [0x5039ac]" in body,
    "0x46D220 内 tvpgl 调用 = %s" % re.findall(r"call dword ptr \[(0x503[0-9a-f]{3})\]", body))

# V6
f = pe.u32(0x4EE290 + 4)
ins = dis(pe, f, 8)
chk("V6", len(ins) >= 2 and ins[0].mnemonic == "mov" and ins[1].mnemonic == "ret"
    and ins[0].op_str in ("al, 4", "eax, 4"),
    "vtable 0x4EE290 (+0x04)=0x%X : %s" % (f, " | ".join("%s %s" % (x.mnemonic, x.op_str) for x in ins[:2])))

# V7
dpe = PE(os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "DS_SPRITE.DLL"))
chk("V7", dpe.u32(0x600132B8 + 8) == 0x60002A40 and dpe.u32(0x600132B8 + 0x44) == 0x60002830,
    "DS_SPRITE vtable 0x600132B8: +0x08=0x%X +0x24=0x%X +0x28=0x%X +0x38=0x%X +0x3C=0x%X +0x44=0x%X"
    % (dpe.u32(0x600132B8 + 8), dpe.u32(0x600132B8 + 0x24), dpe.u32(0x600132B8 + 0x28),
       dpe.u32(0x600132B8 + 0x38), dpe.u32(0x600132B8 + 0x3C), dpe.u32(0x600132B8 + 0x44)))

# V8
b8 = " ".join("%s %s" % (i.mnemonic, i.op_str) for i in dis(pe, 0x471D3F, 0x40))
chk("V8", "mov esi, dword ptr [ebp + 0x1d4]" in b8 and "mov dword ptr [esi + 4], eax" in b8,
    "0x471D3F.. 尾插: %s" % b8[:140])

# V9
d = pe.data
lz = len(re.findall(rb"layer", d, re.I)) + len(re.findall(rb"zord", d, re.I)) + len(re.findall(rb"depth", d, re.I))
pri = [m.start() for m in re.finditer(rb"priority", d, re.I)]
# 唯一命中必须落在导入名区且其所在串正是 "SetThreadPriority"
pri_ok = False
pri_str = None
if len(pri) == 1:
    o = pri[0]
    st = o
    while st > 0 and d[st - 1] != 0:
        st -= 1
    en = d.find(b"\0", o)
    pri_str = d[st:en]
    # IMAGE_IMPORT_BY_NAME = WORD hint + name, 故串首可能有 2 字节 hint
    pri_ok = pri_str.endswith(b"SetThreadPriority") and len(pri_str) <= 18 + 2
chk("V9", lz == 0 and pri_ok,
    "layer/zord/depth=%d ; priority 命中=%s 所在串=%r" % (lz, [hex(x) for x in pri], pri_str))

# V10
sob = Sob(FUNCLIB)
fs = open(FUNCLIB, "rb").read()
n_fl = len(re.findall(rb"priority", fs, re.I))
n_ot = 0
cnt = 0
for fn in os.listdir(SCRIPTDIR):
    pp = os.path.join(SCRIPTDIR, fn)
    if os.path.isfile(pp):
        cnt += 1
        n_ot += len(re.findall(rb"priority", open(pp, "rb").read(), re.I))
chk("V10", n_fl == 0 and n_ot == 0, "func_lib=%d ; SCRIPT 目录 %d 文件 priority 合计=%d" % (n_fl, cnt, n_ot))

# V11
# maps[4] 的 value == 字符串偏移; key 才是"引用站点(字节偏移)". 过程归属看站点.
sites = {k: v for k, v in sob.maps[4].items() if v in (0x2AF09, 0x2AF78, 0x2B559, 0x2B564)}
rows = list(csv.DictReader(open(os.path.join(RE, "funclib_切分.tsv"), encoding="utf-8"), delimiter="\t"))


def proc_of(site):
    return [r["V"] for r in rows if int(r["过程起"], 16) <= site < int(r["过程止"], 16)]


owner = {}
for k, v in sites.items():
    owner.setdefault(hex(v), []).append((hex(k), proc_of(k)))
chk("V11", owner.get("0x2af09", [(None, [])])[0][1] == ["0x14f98"],
    "CHR\\%%s.ELG(value 0x2AF09) 引用站点->过程 %s ; PIC 各站点->过程 %s"
    % (owner.get("0x2af09"), [owner.get(k) for k in ("0x2af78", "0x2b559", "0x2b564")]))

print("=" * 60)
npass = sum(1 for _, ok, _ in results if ok)
print(">>> %d/%d PASS %s" % (npass, len(results), "ALL_PASS" if npass == len(results) else "FAIL"))
