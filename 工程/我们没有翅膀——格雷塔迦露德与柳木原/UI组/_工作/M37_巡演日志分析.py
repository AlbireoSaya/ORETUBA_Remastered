# -*- coding: utf-8 -*-
r"""M37 · krkr 巡演日志分析（`krkr.console.log` 是 **UTF-16LE**，追加式）

■ 输出（贴原始行，不做润色）
  1. `[UI][TOUR]` 每屏行 = 「屏名 + 实绘元素数」（实绘含附加层，见 ui_screens.tjs:1013）
  2. `EXCEPTION` / `Error` / `error` 行（期望 0）
  3. 缺件（`[UI][MISS]` / `缺件` / `MISS`）行（期望 0）
  4. `[UI][ATTACH]` / `[UI][QBAR]`（附加层与呼出状态机）行

■ 用法
    python _工作\M37_巡演日志分析.py <run 名，如 ui_run | ui_run_quickbar> [期望quickbar屏名]
"""
import io
import os
import re
import sys

# UI组\_工作 → UI组 → <game> → 工程 → <worktree 根>
WT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "..", "..", ".."))


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "ui_run"
    p = os.path.join(WT, "临时", run, "runtime", "savedata", "krkr.console.log")
    if not os.path.exists(p):
        print("!! 找不到日志：%s" % p)
        return 2
    txt = io.open(p, "r", encoding="utf-16-le", errors="replace").read()
    lines = [l.rstrip() for l in txt.splitlines()]
    print("=" * 78)
    print("巡演日志：%s（%d 行）" % (p, len(lines)))
    print("=" * 78)

    tour = [l for l in lines if "[UI][TOUR]" in l]
    print("\n[1] [UI][TOUR] 每屏行（%d 条）—— 格式含「实绘元素数」：" % len(tour))
    for l in tour:
        print("  " + l)

    exc = [l for l in lines if "EXCEPTION" in l or "An exception" in l]
    print("\n[2] 异常行（期望 0）：%d 条" % len(exc))
    for l in exc[:20]:
        print("  !! " + l)

    # 只认**非零**缺件（TOUR 行里 `缺件=0` 是统计字段，不是缺件事件）
    miss = [l for l in lines
            if re.search(r"缺件=\s*[1-9]", l)
            or re.search(r"缺件元素\s*[1-9]", l)
            or "[UI][MISS]" in l
            or re.search(r"缺件（|缺件：", l)]
    print("\n[3] 缺件行（期望 0）：%d 条" % len(miss))
    for l in miss[:20]:
        print("  !! " + l)

    att = [l for l in lines if "[UI][ATTACH]" in l]
    qb = [l for l in lines if "[UI][QBAR]" in l]
    print("\n[4] 附加层行（%d 条）：" % len(att))
    for l in att[:12]:
        print("  " + l)
    print("\n[5] 快捷条状态机行（%d 条）：" % len(qb))
    for l in qb[:20]:
        print("  " + l)

    # quickbar 屏的实绘数
    m = re.search(r"\[UI\]\[TOUR\][^\n]*quickbar[^\n]*", txt)
    print("\n[6] quickbar 屏的 TOUR 行：%s" % (m.group(0) if m else "(未找到)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
