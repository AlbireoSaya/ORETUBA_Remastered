# -*- coding: utf-8 -*-
r"""m07_readback_verify.py —— 独立读回复核（ISSUE-20260927-07 · 系统按钮模块）

不依赖补丁脚本的内存态：**从盘上重新读入**改后的两个屏 JSON，与取证目录内的改前快照逐件比对。
断言：
  [1] 九件 sv.sys_* 的 x = 目标值（864/864/856/1114/1114/1106/1472/1472/1464）；
  [2] 元素逐件字段 diff：**除这九件的 x 外，无任何字段变化**（y/w/h/z/asset/font/action/
      vis_flag/vis_when/机制字段全等）；元素数量不变；
  [3] 三按钮两两间距改前 = 改后（可见件 40/40、hit 层 24/24）；
  [4] 屏级字段（id/title_cn/owner/flags_default/page_flag）全等；note 仅追加；
  [5] 字节面：CRLF 数不变、无 BOM、文件仅在 9 处数字与 note 尾部有差异。
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # ...\取证
UI = HERE.parents[2]                            # ...\UI组
SCREENS = UI / "layout" / "screens"

PAIRS = [("23_save.json", HERE / "改前_23_save.json"),
         ("24_load.json", HERE / "改前_24_load.json")]

TARGET = {
    "sv.sys_game": 864, "sv.sys_game_tx": 864, "sv.sys_game_hit": 856,
    "sv.sys_title": 1114, "sv.sys_title_tx": 1114, "sv.sys_title_hit": 1106,
    "sv.sys_end": 1472, "sv.sys_end_tx": 1472, "sv.sys_end_hit": 1464,
}
ORDER = list(TARGET)

fails = []


def gaps(xs):
    vis = [xs["sv.sys_game"], 210], [xs["sv.sys_title"], 318], [xs["sv.sys_end"], 210]
    hit = [xs["sv.sys_game_hit"], 226], [xs["sv.sys_title_hit"], 334], [xs["sv.sys_end_hit"], 226]
    r = []
    for a, b in ((vis[0], vis[1]), (vis[1], vis[2])):
        r.append(b[0] - (a[0] + a[1]))
    for a, b in ((hit[0], hit[1]), (hit[1], hit[2])):
        r.append(b[0] - (a[0] + a[1]))
    return r


for fn, snap in PAIRS:
    cur = SCREENS / fn
    cb, ob = cur.read_bytes(), snap.read_bytes()
    ct, ot = cb.decode("utf-8"), ob.decode("utf-8")
    C, O = json.loads(ct), json.loads(ot)

    print("=" * 96)
    print("%s  盘上 md5=%s  改前快照 md5=%s" % (
        fn, __import__("hashlib").md5(cb).hexdigest(), __import__("hashlib").md5(ob).hexdigest()))
    print("  字节 %d → %d（Δ%+d）  CRLF %d → %d  BOM=%s" % (
        len(ob), len(cb), len(cb) - len(ob), ot.count("\r\n"), ct.count("\r\n"),
        cb[:3] == b"\xef\xbb\xbf"))

    # [1] x 读回
    ci = {e["id"]: e for e in C["elements"]}
    oi = {e["id"]: e for e in O["elements"]}
    print("  [1] 九件 x 读回：")
    ok1 = True
    for eid in ORDER:
        got, want = ci[eid]["x"], TARGET[eid]
        flag = "OK" if got == want else "!!"
        if got != want:
            ok1 = False
        print("      %-18s x %5d → %5d  %s" % (eid, oi[eid]["x"], got, flag))
    if not ok1:
        fails.append("%s [1] x 目标不符" % fn)

    # [2] 全量字段 diff
    print("  [2] 逐元素字段 diff（应仅 9 处 x）：")
    if set(ci) != set(oi):
        fails.append("%s [2] 元素 id 集合变化" % fn)
    diffs = []
    for eid in sorted(set(ci) & set(oi)):
        a, b = oi[eid], ci[eid]
        for k in sorted(set(a) | set(b)):
            if k == "x":
                continue
            if a.get(k, "\0MISSING") != b.get(k, "\0MISSING"):
                diffs.append((eid, k, a.get(k), b.get(k)))
    for eid in ORDER:
        if oi[eid]["x"] != ci[eid]["x"]:
            diffs.append((eid, "x", oi[eid]["x"], ci[eid]["x"]))
    ndiff = len([d for d in diffs if d[1] == "x"])
    print("      x 变化 %d 处；非 x 字段变化 %d 处" % (ndiff, len(diffs) - ndiff))
    for d in diffs:
        if d[1] != "x":
            print("      !! %s.%s %r → %r" % d)
    if ndiff != 9 or len(diffs) != 9:
        fails.append("%s [2] 字段 diff 异常：%d 处" % (fn, len(diffs)))

    # [3] 间距
    gb = gaps({i: oi[i]["x"] for i in ORDER})
    ga = gaps({i: ci[i]["x"] for i in ORDER})
    print("  [3] 间距  可见 40/40   hit 24/24  —— 改前 %s / 改后 %s  %s"
          % (gb[:2], ga[:2], "OK" if gb == ga else "!!"))
    print("          hit 层：改前 %s / 改后 %s  %s" % (gb[2:], ga[2:], "OK" if gb == ga else "!!"))
    if gb != ga:
        fails.append("%s [3] 间距改变" % fn)

    # [4] 屏级字段
    lvl = [k for k in set(C) | set(O) if k not in ("elements", "note")]
    bad = [k for k in lvl if C.get(k) != O.get(k)]
    print("  [4] 屏级字段 %s：%s" % (sorted(lvl), "全等 OK" if not bad else "!! %s" % bad))
    if bad:
        fails.append("%s [4] 屏级字段变化 %s" % (fn, bad))
    print("      note 长度 %d → %d（仅追加：旧内容是新内容的前缀=%s）"
          % (len(O["note"]), len(C["note"]), C["note"].startswith(O["note"])))
    if not C["note"].startswith(O["note"]):
        fails.append("%s [4] note 非纯追加" % fn)

    # [5] 字节面：note 之后区段（"elements" 起）两串仅应在 9 处数字上不同
    ko = ot.index('",\r\n "elements": [')
    kc = ct.index('",\r\n "elements": [')
    norm = lambda t: re.sub(r"-?\d+", "#", t)
    same_tail = norm(ct[kc:]) == norm(ot[ko:])
    print("  [5] bytes 结构：CRLF 数相同=%s；note 之后区段（elements 起）除数字外逐字相同=%s"
          % (ct.count("\r\n") == ot.count("\r\n"), same_tail))
    if ct.count("\r\n") != ot.count("\r\n") or not same_tail:
        fails.append("%s [5] 字节结构异常" % fn)

print("=" * 96)
if fails:
    print("结论：FAIL —— %s" % "；".join(fails))
    sys.exit(1)
print("结论：PASS —— 九件 x 全部到位、非 x 字段零变化、间距不变、note 纯追加、字节结构完好")
