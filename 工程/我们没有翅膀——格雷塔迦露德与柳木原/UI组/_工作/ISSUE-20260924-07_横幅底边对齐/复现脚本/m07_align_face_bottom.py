# -*- coding: utf-8 -*-
r"""ISSUE-20260924-07 · 声音页角色横幅头像「底边对齐底板底边」

■ 用户要求（唯一验收标准）
    「现在的人物头像(cfg.pv_face_xxx)和背景(cfg.banner_frame)位置有偏差，要求**所有人物头像
      底部要和背景底部对齐**，**顶部无所谓（可超出背景顶部）**。」

■ 实测到的真实偏差（本脚本的立论依据，全部可复现）
    ① **元素框**：`cfg.banner_frame` = (1099,261,644,239) ⇒ 元素底边 500；
       33 件 `cfg.pv_face_<族>` = (1540,261,191,239) ⇒ 元素底边 500。
       ⇒ **两者的「元素框底边」本来就相等（0px）** —— 派单里那条「y+h 必须等于
       banner_frame.y+banner_frame.h」的判据，改前就已成立，**它不是真正的偏差源**。
    ② **可见底边**：底板素材 `ui/x_ui_cfg_preview_frame.png` 是 **96×96 九宫格**，
       内容 bbox = (7,7,89,89) ⇒ **四周各有 7px 全透明留边**。九宫格（slice 24 / border 24，
       见 `复刻/replica.js` 的 border-image 分支与 krkr 侧 `uiWidgetNine`）把源图边缘带
       **1:1** 画在元素框的边缘带上 ⇒ 那 7px 透明留边同样落在元素框内侧。
       ⇒ 底板的**可见底边 = 261+239-7 = 493**（截图像素实测：底框线笔画在 y490-491，
       末行内容 y492）。而头像素材 276×345 内容 bbox 铺满整图（末行就是衣服）
       ⇒ 头像**可见底边 = 500**。
    ③ ⇒ 真实偏差 = **头像比底板可见底边低 7px**（头像从底板下框线穿出去）。
       这才是用户在截图上看到的那处「有偏差」。

■ 处置（本脚本做的事）
    只改 `y`（`x`/`w`/`h` 一律不动；`vis_flag`/`vis_when`/`z` 一律不碰）：
        y_new = (banner_frame.y + banner_frame.h - FRAME_PAD) - h
              = (261 + 239 - 7) - 239 = **254**
    ⇒ 头像可见底边 493 == 底板可见底边 493（逐像素对齐）。
    头像顶边随之由 261 升到 254（比底板可见顶边 268 高 14px）—— 用户已明示「顶部无所谓」。

■ 用法
    python _工作\ISSUE-20260924-07_横幅底边对齐\复现脚本\m07_align_face_bottom.py --check
        → 只读：打印底板 + 33 件头像的逐件表 + 逐族断言结果，不改文件
    python _工作\ISSUE-20260924-07_横幅底边对齐\复现脚本\m07_align_face_bottom.py --apply
        → 写盘：精确替换（只动 y），随后 json.load 校验 + 逐件断言
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)                       # …\ISSUE-20260924-07_横幅底边对齐
UI = os.path.dirname(os.path.dirname(EVID))       # …\UI组
CFG = os.path.join(UI, "layout", "screens", "25_config.json")

FRAME_ID = "cfg.banner_frame"
FRAME_PAD = 7          # 底板素材 96×96 的四周全透明留边（bbox 7,7,89,89），九宫格 1:1 落在元素内侧
TARGET_Y = 254         # = (261 + 239 - 7) - 239


def load(path=CFG):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def collect(doc):
    frame = None
    faces = []
    for e in doc["elements"]:
        if e["id"] == FRAME_ID:
            frame = e
        elif e["id"].startswith("cfg.pv_face_"):
            faces.append(e)
    return frame, faces


def report(frame, faces, tag):
    fy, fh = frame["y"], frame["h"]
    vis_bottom = fy + fh - FRAME_PAD
    print("=" * 100)
    print("[%s] 底板 %s = (x=%d, y=%d, w=%d, h=%d)  元素底边=%d  可见底边=元素底边-%d=%d"
          % (tag, FRAME_ID, frame["x"], fy, frame["w"], fh, fy + fh, FRAME_PAD, vis_bottom))
    print("-" * 100)
    print("%-22s %6s %6s %6s %6s | %8s %8s | %s" %
          ("元素 id", "x", "y", "w", "h", "元素底边", "可见底边", "断言"))
    print("-" * 100)
    bad = 0
    rows = []
    for e in faces:
        eb = e["y"] + e["h"]
        vb = eb                      # 头像素材内容铺满整图（bbox 全图）⇒ 可见底边 == 元素底边
        ok = (vb == vis_bottom)
        if not ok:
            bad += 1
        rows.append((e["id"], e["y"], eb))
        print("%-22s %6d %6d %6d %6d | %8d %8d | %s" %
              (e["id"], e["x"], e["y"], e["w"], e["h"], eb, vb,
               "OK" if ok else "FAIL(差 %+d)" % (vb - vis_bottom)))
    print("-" * 100)
    print("[%s] 逐族断言：%d 件，OK=%d，FAIL=%d  ⇒ %s"
          % (tag, len(faces), len(faces) - bad, bad,
             "全部对齐（头像可见底边 == 底板可见底边 %d）" % vis_bottom if bad == 0 else "存在未对齐项"))
    # 同时如实登记「与派单原判据（元素框底边相等）」的关系
    lit = sum(1 for e in faces if e["y"] + e["h"] == fy + fh)
    print("[%s] 附带登记：按派单原判据（y+h == banner_frame.y+banner_frame.h = %d）成立的件数 = %d / %d"
          % (tag, fy + fh, lit, len(faces)))
    return rows, bad


def apply_patch():
    with io.open(CFG, encoding="utf-8") as f:
        src = f.read()

    # 逐块精确替换：定位每个 cfg.pv_face_<族> 的 id，再改它**本块内**第一个 "y": <num>
    id_re = re.compile(r'"id": "cfg\.pv_face_[A-Za-z0-9_]+",')
    out = []
    pos = 0
    n = 0
    changed = []
    for m in id_re.finditer(src):
        out.append(src[pos:m.end()])
        pos = m.end()
        y_m = re.compile(r'("y": )(\d+)').search(src, pos)
        assert y_m, "块内找不到 y 字段：%s" % m.group(0)
        # 该 y 必须落在本块内（下一个 id 之前）
        nxt = src.find('"id": ', pos)
        assert nxt < 0 or y_m.start() < nxt, "y 字段越块：%s" % m.group(0)
        old = int(y_m.group(2))
        out.append(src[pos:y_m.start()])
        out.append(y_m.group(1) + str(TARGET_Y))
        changed.append((m.group(0), old))
        pos = y_m.end()
        n += 1
    out.append(src[pos:])
    assert n == 33, "pv_face 块数不是 33，而是 %d" % n
    new = "".join(out)

    with io.open(CFG, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    return n, changed


def main():
    apply = "--apply" in sys.argv
    doc = load()
    frame, faces = collect(doc)
    assert frame is not None and len(faces) == 33, "元素数异常"
    report(frame, faces, "改前")

    if not apply:
        print("\n[--check] 只读模式：未改盘。加 --apply 执行精确替换。")
        return

    n, changed = apply_patch()
    print("\n[--apply] 已写盘：%d 件 cfg.pv_face_* 的 y 被替换" % n)
    oldset = sorted(set(y for _, y in changed))
    print("           改前 y 取值集合 = %s ⇒ 改后 y = %d" % (oldset, TARGET_Y))

    doc2 = load()          # ★ json.load 校验
    frame2, faces2 = collect(doc2)
    report(frame2, faces2, "改后")
    # 只改 y 的校验：其余字段逐一比对
    d1 = {e["id"]: e for e in doc["elements"]}
    d2 = {e["id"]: e for e in doc2["elements"]}
    assert set(d1) == set(d2), "元素集合发生变化"
    diffs = []
    for k in d1:
        if d1[k] != d2[k]:
            diff_keys = [f for f in set(d1[k]) | set(d2[k]) if d1[k].get(f) != d2[k].get(f)]
            diffs.append((k, diff_keys))
    print("\n[只改 y 的校验] 字段差异清单：%d 件元素有差异" % len(diffs))
    for k, ks in diffs[:5]:
        print("   %s → %s" % (k, ks))
    assert len(diffs) == 33 and all(ks == ["y"] for _, ks in diffs), "除 y 外还有字段被改动！"
    print("   ⇒ 全部 33 件且**仅** y 字段变化 ✓")


if __name__ == "__main__":
    main()