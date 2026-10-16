# -*- coding: utf-8 -*-
r"""【M1 copy】M47 config page-scope engine tour -- byte-identical to the original script
except the RUN constant (the original uses a shared dir that three modules fight over).


■ 为什么私有目录
  `krkr\run_autotour.bat` 每次 `del savedata\*.*`，且并发会话可能共用 `临时\ui_run`
  （2026-09-23 实测过一次日志被别的 agent 覆盖）⇒ 本脚本自建 `临时\ui_run_pagescope\`，
  镜像 game + assets + runtime，只动自己那份日志与导图。

■ 目的（用户 2026-09-24 报告「带值 flag 的元素在两页都可见」）
  编辑器侧已用 `m47_pagescope_probe.py` 复现并定位（raw flag 覆盖不跑派生）。
  本脚本回答**产品侧**（引擎）这一半：真机从系统页切到声音页后，系统页那 17 件值元素
  是否真的消失？做法 = 跑一遍巡演 → 从日志把 `shot_NN_config.png` 逐步对上步骤标签 →
  取「切页前（系统页）」与「切页后（声音页）」两张**引擎自己导出的 PNG**，
  对**系统页值元素所在的矩形区**做非背景像素占比统计（两页应一有、一无）。

■ 用法
    python _工作\M47_设置屏重设\复现脚本\m47_pagescope_tour.py
"""
import io
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))
SRC = os.path.join(UI, "krkr")
RUN = os.path.join(WT, "临时", "ui_run_m08_m47copy")   # M1 copy: unique dir
SAVE = os.path.join(RUN, "runtime", "savedata")
LOG = os.path.join(SAVE, "krkr.console.log")

# 系统页「选项值」所在区域（左列行区：条目名 x=100 / 值按钮 x≈445..875，行 y 200..800）
ROW_REGION = (100, 200, 880, 800)
# 声音页专属区域（角色列表 / 横幅照：x 1100..1880、y 250..1020）
SND_REGION = (1100, 250, 1880, 1020)


def build():
    if os.path.isdir(RUN):
        shutil.rmtree(RUN)
    shutil.copytree(os.path.join(SRC, "game"), os.path.join(RUN, "game"))
    for sub in ("assets",):
        s = os.path.join(SRC, sub)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(RUN, "game", sub))
    # 先拷 runtime（含 savedata 以外的全部），再自建空的 savedata：
    # ⚠️ 顺序反了会 `FileExistsError`（copytree 见到刚 makedirs 出来的 runtime 目录即报错，实测踩过）
    shutil.copytree(os.path.join(SRC, "runtime"), os.path.join(RUN, "runtime"),
                    ignore=shutil.ignore_patterns("savedata"))
    os.makedirs(SAVE, exist_ok=True)
    io.open(os.path.join(RUN, "game", "autotour.txt"), "w", encoding="utf-8").write("autotour\n")
    print("私有运行目录已建：", RUN)


def run_engine(wait_s=300):
    exe = os.path.join(RUN, "runtime", "tvpwin32.exe")
    assert os.path.exists(exe), "找不到引擎：" + exe
    p = subprocess.Popen([exe, os.path.join(RUN, "game")], cwd=os.path.join(RUN, "runtime"))
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < wait_s:
        time.sleep(3)
    if p.poll() is None:
        print("⚠️ %d 秒未自退，强制结束" % wait_s)
        p.kill()
    print("引擎退出码=%s，用时 %.0f 秒" % (p.poll(), time.time() - t0))


def read_log():
    raw = io.open(LOG, "rb").read()
    return raw.decode("utf-16-le", "replace").splitlines()


def pair_steps(lines):
    """把 `[UI][PNG] OK` 行与它前面最近的 `-> 下一步：<label>` 配对（导图顺序即步骤顺序）"""
    cur, out = "", []
    for l in lines:
        m = re.search(r"-> 下一步：(.*?)\s+屏=", l)
        if m:
            cur = m.group(1).strip()
        if "[UI][PNG] OK" in l:
            out.append((os.path.basename(l.strip().split()[-1]), cur))
    return out


def region_stats(png, box):
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    x0, y0, x1, y1 = box
    crop = im.crop(box)
    px = crop.load()
    w, h = crop.size
    # 背景 = 全屏压暗层（cfg.dim）+ 透明区 ⇒ 用「与压暗底色差异较大」当“有内容”判据
    from collections import Counter
    c = Counter(px[i, j][:3] for i in range(0, w, 2) for j in range(0, h, 2))
    bg, bgn = c.most_common(1)[0]
    tot = sum(c.values())
    other = tot - bgn
    return bg, bgn / tot, other / tot


def main():
    build()
    run_engine()
    lines = read_log()
    print("\n===== 巡演判词（config 相关 + 收尾统计）=====")
    for l in lines:
        if "[UI][TOUR]" in l and any(k in l for k in
                                     ("config", "配置", "巡演结束", "缺件", "缩放", "未知 kind",
                                      "转场", "EXCEPTION", "PNG 导出", "STEP")):
            print("  " + l[:220])
    pairs = pair_steps(lines)
    cfg = [(n, lab) for n, lab in pairs if "_config" in n]
    print("\n===== 配置屏导图（步骤标签 → PNG）=====")
    for n, lab in cfg:
        print("  %-28s %s" % (n, lab[:110]))
    if len(cfg) >= 2:
        a, b = cfg[0][0], cfg[1][0]
        print("\n===== 区域量化（引擎自导 PNG）=====")
        for n, lab in cfg[:4]:
            p = os.path.join(SAVE, n)
            if not os.path.exists(p):
                continue
            bgA, rA, oA = region_stats(p, ROW_REGION)
            bgB, rB, oB = region_stats(p, SND_REGION)
            print("  %-28s 左列行区 非背景 %.3f | 角色区 非背景 %.3f   ← %s"
                  % (n, oA, oB, lab[:60]))
    print("\n（引擎已退出；私有目录 %s 保留供复核）" % RUN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
