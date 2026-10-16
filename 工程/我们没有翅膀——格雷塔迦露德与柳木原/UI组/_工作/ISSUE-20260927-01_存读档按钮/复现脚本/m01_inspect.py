# -*- coding: utf-8 -*-
"""m01_inspect.py —— 只读侦察：列出目标屏里右上角三系统按钮组与页码徽章、潜在相交对象。
不使用 gen_layout.py / verify_ui.py / test_*.py；本脚本纯读盘。
用法： python m01_inspect.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
UI = HERE.parents[3]          # ...\UI组
SCREENS = UI / "layout" / "screens"

TARGET_GROUPS = ("sv.sys_game", "sv.sys_title", "sv.sys_end")
BADGE = ("sv.pgnum_",)


def load(name):
    with open(SCREENS / name, encoding="utf-8") as f:
        return json.load(f)


def rect(e):
    return (e.get("x", 0), e.get("y", 0), e.get("w", 0), e.get("h", 0))


def fmt(e):
    x, y, w, h = rect(e)
    return "%-22s %-6s x=%-5s y=%-5s w=%-5s h=%-5s z=%-4s right=%-6s bottom=%-6s" % (
        e.get("id"), e.get("kind"), x, y, w, h, e.get("z", "-"), x + w, y + h)


for fn in ("23_save.json", "24_load.json"):
    d = load(fn)
    els = d["elements"]
    print("=" * 100)
    print(fn, " elements =", len(els), " page_flag =", d.get("page_flag"))
    print("-" * 100)
    print("[A] 三系统按钮组（含 _tx/_hit）与页码徽章：")
    for e in els:
        eid = e.get("id", "")
        if eid.startswith(TARGET_GROUPS) or eid.startswith(BADGE):
            print("   ", fmt(e), "  vis=", e.get("vis_flag"), e.get("vis_when"), " act=", e.get("action"))
    print("-" * 100)
    print("[B] 目标组右沿 / 徽章左沿：")
    grp = [e for e in els if e.get("id", "").startswith(TARGET_GROUPS)]
    bad = [e for e in els if e.get("id", "").startswith(BADGE)]
    if grp:
        gr = max(e["x"] + e["w"] for e in grp)
        print("    组右沿 =", gr, " 组左沿 =", min(e["x"] for e in grp))
    if bad:
        bl = min(e["x"] for e in bad)
        print("    徽章左沿 =", bl, " 徽章右沿 =", max(e["x"] + e["w"] for e in bad))
    print("-" * 100)
    print("[C] 全部元素 id/几何（供相交体检对照）：")
    for e in els:
        print("   ", fmt(e))
