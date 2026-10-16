#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_real_acceptance.py — ISSUE-20260927-05 / E2 · **正式验收**（真实数据，走官方 bat）

与夹具路径分开（**这是唯一产出「真实数据验收图」的脚本**）：
  1. 跑 `krkr\\run_autotour.bat`（＝默认路径：镜像仓库 `krkr\\game`/`krkr\\assets`/`krkr\\runtime`，
     数据来自仓库 `layout/screens/32_flowchart.json`，**不注入任何夹具**）；
  2. 等巡演自行结束（日志出现「巡演结束」；实测一轮 ≈162 s，不是 45–60 s）；
  3. 把引擎自导的 `shot_*_flowchart.png` 复制进本目录（运行目录下次会被清空）；
  4. 摘 FLOWLINK/EXCEPTION/验收行到 `E2_真实数据_run_autotour_日志摘录.txt`；
  5. 调 `check_e2_png.py --real` 做像素级核对（预测色＝从数据读到的 `links[].color`）。

⚠ 与本目录的 `run_e2_fixture.py` 的区别（**关键**）：
   · 本脚本/`run_autotour.bat` ⇒ 运行目录 `临时\\ui_run\\`       ⇒ **仓库真实数据**；
   · `run_e2_fixture.py`        ⇒ 运行目录 `临时\\ui_run_e2_fixture\\` ⇒ **夹具注入**（仅自证用）。
   两个运行目录互不相同，夹具**永远不会**进 `临时\\ui_run\\`。
"""

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
UI = HERE.parents[3]
WT = HERE.parents[6]
RUN = WT / "临时" / "ui_run"
SAVEDATA = RUN / "runtime" / "savedata"


def log(m):
    print(m, flush=True)


def tail_log():
    p = SAVEDATA / "krkr.console.log"
    if not p.exists():
        return ""
    raw = p.read_bytes()
    for enc in ("utf-16-le", "utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def main():
    # 0) data color(s) BEFORE the run —— 供报告「新预测色」一栏
    d = json.loads((UI / "layout" / "screens" / "32_flowchart.json").read_text(encoding="utf-8"))
    links = d.get("links") or []
    log("[0] links=%d  color=%s" % (len(links), ", ".join(sorted({("#%08X" % l["color"]) for l in links}))))
    # ★ 记录本次验收对应的**数据修订**（E1 会继续改生成器 ⇒ 图必须能追到具体数据）
    h_screen = hashlib.sha256((UI / "layout" / "screens" / "32_flowchart.json").read_bytes()).hexdigest()
    h_tjs = hashlib.sha256((UI / "krkr" / "game" / "ui_layout.tjs").read_bytes()).hexdigest()
    log("[0] data rev: 32_flowchart.json sha256=%s" % h_screen)
    log("[0] data rev: ui_layout.tjs     sha256=%s" % h_tjs)

    # ★ 护栏：临时\ui_run 是**共享运行目录**，本工作树有并发代理在跑引擎 ——
    #   若已有 tvpwin32 在跑，本轮的 PNG/日志会与它混淆 ⇒ 先等它退出（最多 6 分钟）。
    for _ in range(72):
        t = subprocess.run(["tasklist", "/FI", "IMAGENAME eq tvpwin32.exe"],
                           capture_output=True, text=True, errors="replace").stdout or ""
        if "tvpwin32.exe" not in t:
            break
        log("    [guard] 检测到另一个 tvpwin32 在运行（共享运行目录），等 5s ...")
        time.sleep(5)
    else:
        raise SystemExit("[ABORT] tvpwin32 一直在跑（并发代理占用共享运行目录），本轮不做验收")

    for old in SAVEDATA.glob("shot_*_flowchart.png"):
        old.unlink()

    # 1) 官方默认路径
    log("[1] cmd /c krkr\\run_autotour.bat  (真实数据；夹具路径不参与)")
    cp = subprocess.run(["cmd", "/c", "krkr\\run_autotour.bat"], cwd=str(UI),
                        capture_output=True, text=True, errors="replace")
    log("    bat rc=%s" % cp.returncode)
    for ln in (cp.stdout or "").splitlines():
        log("    | " + ln)

    # 2) 等巡演结束（引擎由 start 分离，bat 立即返回）
    t0 = time.time()
    done = False
    while time.time() - t0 < 300:
        time.sleep(5)
        lg = tail_log()
        if "巡演结束" in lg or "quit (autotour" in lg:
            done = True
            break
    time.sleep(3)
    log("[2] tour %s after %.0fs" % ("finished" if done else "TIMEOUT", time.time() - t0))

    # 3) 存图
    pngs = sorted(SAVEDATA.glob("shot_*_flowchart.png"))
    for p in pngs:
        dst = HERE / ("E2_真实数据验收图_%s" % p.name)
        shutil.copy2(p, dst)
        log("[3] PNG -> %s" % dst)

    # 4) 日志摘录
    lg = tail_log()
    keys = ("FLOWLINK", "EXCEPTION", "屏=flowchart", "巡演结束", "PNG 导出", "quit (autotour")
    keep = [ln.rstrip() for ln in lg.splitlines() if any(k in ln for k in keys)]
    (HERE / "E2_真实数据_run_autotour_日志摘录.txt").write_text(
        "\n".join(["ISSUE-20260927-05 / E2 · 正式验收（run_autotour.bat，真实 links %d 条）" % len(links),
                   "run dir : %s" % RUN,
                   "=" * 70] + keep) + "\n", encoding="utf-8")
    log("[4] 日志摘录 -> E2_真实数据_run_autotour_日志摘录.txt")
    for ln in keep:
        log("    | " + ln)

    # 5) 像素核对（--real：色值从 layout 读）
    log("[5] check_e2_png.py --real")
    cp2 = subprocess.run([sys.executable, str(HERE / "check_e2_png.py"), "--real",
                          "--run-dir", str(RUN)],
                         capture_output=True, text=True, errors="replace")
    out = (cp2.stdout or "") + (cp2.stderr or "")
    (HERE / "real_check.log").write_text(out, encoding="utf-8")
    for ln in out.splitlines():
        log("    | " + ln)
    log("[5] 像素核对 rc=%s" % cp2.returncode)
    return 0 if (done and cp2.returncode == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
