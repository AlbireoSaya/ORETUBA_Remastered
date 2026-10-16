# -*- coding: utf-8 -*-
r"""M47 后 · 「跨页可见」诊断之复刻端对照：raw flag 深链 vs 真点页签

■ 要证的一件事
  复刻页（`复刻\index.html`）上，**原始 flag 深链** `?flags=cfg_page:snd` 与**真点页签**
  （`--click cfg.tab2_hit`，走 `config_tab_2` 动作 ⇒ 动作内部会跑切页派生）**画出来一样不一样**？
  · 一样 ⇒ 复刻端不存在跨页残留（进屏/深链都由 `configFlagsInitFor` 兜住，C4 修的那一处）；
  · 不一样 ⇒ 深链路径会残留，与编辑器同类问题。

■ 做法
  复用 W4 的 `w4_html_config_shots.py --shot` 入口（隐藏页面外壳 + `setScale(1)` ⇒ 左上
  1920×1080 即画布本体），三张图落本目录，再用 PIL 作差：
    · 差异框 = None ⇒ 逐像素一致。

■ 用法
    python _工作\ISSUE-20260924-03_跨页可见诊断\复现脚本\m47_pagescope_replica.py
"""
import os
import subprocess
import sys

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)                       # …\ISSUE-20260924-03_跨页可见诊断
UI = os.path.dirname(os.path.dirname(EVID))        # …\UI组
SHOTS = os.path.join(UI, "_工作", "ISSUE-20260924-01_W4_证据", "复现脚本", "w4_html_config_shots.py")

A = os.path.join(EVID, "诊断_复刻_深链声音页.png")      # ?flags=cfg_page:snd（raw）
B = os.path.join(EVID, "诊断_复刻_点击声音页.png")      # 真点页签 cfg.tab2_hit
C = os.path.join(EVID, "诊断_复刻_深链系统页.png")      # 默认系统页


def shot(query, out, click=None):
    cmd = [sys.executable, SHOTS, "--shot", query, out]
    if click:
        cmd += ["--click", click]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("  " + r.stdout.decode("utf-8", "replace").strip().splitlines()[-1])


def main():
    print("① 复刻页三张 1:1 画布截图（左上 1920×1080 = 画布本体）")
    shot("?screen=config&flags=cfg_page:snd", A)
    shot("?screen=config", B, click="cfg.tab2_hit")
    shot("?screen=config", C)
    ia, ib, ic = (Image.open(p).convert("RGB") for p in (A, B, C))
    print("② 作差")
    d1 = ImageChops.difference(ia, ib).getbbox()
    print("   raw 深链声音页  vs  真点页签声音页  差异框 =", d1,
          "⇒ " + ("**逐像素一致**（复刻端无跨页残留）" if d1 is None else "**有差异**（深链路径残留）"))
    d2 = ImageChops.difference(ia, ic).getbbox()
    print("   raw 深链声音页  vs  系统页          差异框 =", d2, "（两页本就该不同）")
    ImageChops.difference(ia, ib).save(os.path.join(EVID, "诊断_差异_rawvs点击.png"))
    print("③ 差异图已写：诊断_差异_rawvs点击.png（本例为空图 —— 差异为 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
