# -*- coding: utf-8 -*-
r"""M13 实机巡演驱动器（Python 版，避免 shell 对中文路径的编码抖动）。

用法：
    PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python run_tour.py

做的事（与 README_运行方式.md 的 run_autotour.bat 等价）：
  1) 建 <工作区>\临时\ui_run（叶子名 ASCII）
  2) 复制 krkr\game -> RUN\game、krkr\assets -> RUN\game\assets、krkr\runtime -> RUN\runtime
  3) 写 RUN\game\autotour.txt（巡演触发方式 ③）
  4) 启动 RUN\runtime\tvpwin32.exe RUN\game，等 N 秒后 taskkill
  5) 打印 savedata 里的产物与日志关键行

路径不靠命令行传入（命令行中文会被二次编码），一律从 E:\ZCode Workspace\Galgame
逐层 listdir 发现，避免手写中文。
"""
import os
import shutil
import subprocess
import sys
import time

GAL = "E:/ZCode Workspace/Galgame"
WAIT_S = int(sys.argv[1]) if len(sys.argv) > 1 else 62


def find_child(parent, contains):
    for name in sorted(os.listdir(parent)):
        if contains in name:
            return os.path.join(parent, name)
    raise SystemExit("找不到含 %r 的目录于 %s" % (contains, parent))


# 临时 / 工程 两个中文目录名用「内容特征」发现，不手写
tmp_root = None
for name in sorted(os.listdir(GAL)):
    p = os.path.join(GAL, name)
    if os.path.isdir(p) and name not in (".git", ".zcode", ".qoder"):
        try:
            if "ui_run" in os.listdir(p) or "wt-ui" in os.listdir(p) or "agents_ctx.txt" in os.listdir(p):
                tmp_root = p
        except OSError:
            pass
if tmp_root is None:
    raise SystemExit("找不到临时目录")
print("临时目录 =", tmp_root)

proj_root = find_child(GAL, "\u5de5\u7a0b")          # 工程
# UI 组目录 = 工程\<作品>\UI*\ ，且其 layout/screens 下有 33_sysicons.json（本模块的产物）
ui_root = None
for name in sorted(os.listdir(proj_root)):
    p = os.path.join(proj_root, name)
    if not os.path.isdir(p):
        continue
    for sub in sorted(os.listdir(p)):
        cand = os.path.join(p, sub)
        if os.path.isfile(os.path.join(cand, "layout", "screens", "33_sysicons.json")):
            ui_root = cand
            break
    if ui_root:
        break
if ui_root is None:
    raise SystemExit("找不到含 33_sysicons.json 的 UI 组目录")
print("UI 组目录 =", ui_root)

krkr = os.path.join(ui_root, "krkr")
RUN = os.path.join(tmp_root, "ui_run_m13")   # 独立目录：M14 并行模块也用 临时\ui_run，避免互相 rm -rf

if os.path.isdir(RUN):
    shutil.rmtree(RUN)
os.makedirs(RUN)
shutil.copytree(os.path.join(krkr, "game"), os.path.join(RUN, "game"))
shutil.copytree(os.path.join(krkr, "assets"), os.path.join(RUN, "game", "assets"))
shutil.copytree(os.path.join(krkr, "runtime"), os.path.join(RUN, "runtime"))
with open(os.path.join(RUN, "game", "autotour.txt"), "w") as f:
    f.write("autotour")

exe = os.path.join(RUN, "runtime", "tvpwin32.exe")
print("启动 =", exe, os.path.join(RUN, "game"))
p = subprocess.Popen([exe, os.path.join(RUN, "game")],
                     cwd=os.path.join(RUN, "runtime"),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("pid =", p.pid)
time.sleep(WAIT_S)
subprocess.run(["taskkill", "/PID", str(p.pid), "/F"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)

sd = os.path.join(RUN, "runtime", "savedata")
print("savedata 存在 =", os.path.isdir(sd))
if os.path.isdir(sd):
    for f in sorted(os.listdir(sd)):
        print("   ", f, os.path.getsize(os.path.join(sd, f)))

log = os.path.join(sd, "krkr.console.log")
if os.path.isfile(log):
    txt = open(log, encoding="utf-16-le", errors="replace").read()
    print("=" * 70)
    for line in txt.splitlines():
        if ("[UI][TOUR]" in line or "[UI][SYSICON]" in line or "[UI][MOUSE]" in line
                or "[UI][OVERLAY]" in line or "EXCEPTION" in line or "exception" in line
                or "[UI][MISS]" in line or "[UI][SCREENS]" in line or "canvas =" in line):
            print(line)
    print("=" * 70)
    print("EXCEPTION 行数 =", txt.count("EXCEPTION"))
    print("An exception occured 行数 =", txt.count("An exception occured"))
    print("[UI][MISS] 行数 =", txt.count("[UI][MISS]"))