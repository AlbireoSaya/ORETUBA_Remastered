# -*- coding: utf-8 -*-
r"""M47 · 设置**读档路径**实机验证（私有运行目录版，避免与并行 agent 抢同一个 `临时\ui_run`）

一审机制模块 M4.1：`krkr\run_autotour.bat` 每次都 `del savedata\*.*` ⇒ `ui_state.txt` 永不存活 ⇒
`uiStateLoad → uiSettingApplyAll → uiScreenConfigMemoClear` **从未被真正执行过**。
本脚本自建 `临时\ui_run_m47load\`（镜像 game+runtime+assets），**先种入可辨识设置值**再启动引擎，
最后从**自己那份日志**里读 `load -> OK … settings_read=1 | settings=…`，核对种入值被读回。

⚠️ 坑（实测）：`ui_state.txt` 是 **UTF-16LE + BOM**（引擎 `Array.save` 写的），裸 `utf-16-le` 写出**无 BOM**
⇒ 引擎读不到；必须用 Python 的 `utf-16` codec。种入的键要选**巡演不会碰**的（巡演会跑 config_reset 复位）。

用法：
    python _工作\M47_设置屏重设\复现脚本\m47_state_load_probe.py --all
（--all = 建目录 → 种值 → 启动 → 等 110 秒 → 校验；一次跑完，输出可整段贴进工程记录）
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
RUN = os.path.join(WT, "临时", "ui_run_m47load")
SEED = {"vol_bgm": "35", "text_speed": "25", "auto_speed": "45", "vol_sysse": "70"}


def build():
    if os.path.isdir(RUN):
        shutil.rmtree(RUN)
    os.makedirs(os.path.join(RUN, "savedata"))
    shutil.copytree(os.path.join(SRC, "game"), os.path.join(RUN, "game"))
    for sub in ("assets",):
        s = os.path.join(SRC, sub)
        if os.path.isdir(s):
            shutil.copytree(s, os.path.join(RUN, "game", sub))
    shutil.copytree(os.path.join(SRC, "runtime"), os.path.join(RUN, "runtime"),
                    ignore=shutil.ignore_patterns("savedata"))
    io.open(os.path.join(RUN, "game", "autotour.txt"), "w", encoding="utf-8").write("autotour\n")
    print("私有运行目录已建：", RUN)


def seed_state():
    """在**引擎自己写的** ui_state.txt 上改 settings 行（关键：手搓整份文件引擎不认，
    实测把同内容的 CRLF/编码都调对仍判「没有可读的存档」；改引擎产物则一次通过）。
    ⇒ 所以私有目录必须先跑过一次引擎（生成该文件），本函数才生效。"""
    p = os.path.join(RUN, "runtime", "savedata", "ui_state.txt")   # 引擎实际读写的就是这一份
    assert os.path.exists(p), "私有目录里还没有 ui_state.txt —— 先跑一次引擎生成它（--all 会先跑一次）"
    s = io.open(p, encoding="utf-16", errors="replace").read()
    lines = s.split(chr(10))
    done = 0
    for i2, l in enumerate(lines):
        if l.startswith("settings="):
            kv = {}
            for part in l[len("settings="):].split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    kv[k.strip()] = SEED.get(k.strip(), v.strip())
            lines[i2] = "settings=" + ",".join("%s:%s" % (k, kv[k]) for k in kv)
            done += 1
            print("改 settings 行 →", lines[i2][:180])
    assert done == 1, "引擎产物里没有 settings= 行"
    io.open(p, "w", encoding="utf-16").write(chr(10).join(lines))
    print("已写回（UTF-16 + BOM，其余字节沿用引擎产物）：", p)


def run_and_check(wait=115):
    log = os.path.join(RUN, "runtime", "savedata", "krkr.console.log")
    subprocess.Popen([os.path.join(RUN, "runtime", "tvpwin32.exe"), os.path.join(RUN, "game")],
                     cwd=os.path.join(RUN, "runtime"))
    print("引擎已启动（私有目录，巡演约 100 秒自退）…")
    time.sleep(wait)
    t = io.open(log, "rb").read().decode("utf-16-le", "replace").splitlines()
    got = [l for l in t if "[UI][STATE]" in l and "load" in l]
    ok = any("load -> OK" in l for l in got)
    print("load 行：")
    for l in got:
        print("  " + l[:300])
    hit = {}
    load_text = "\n".join(got)
    for k in SEED:
        m = re.search(r"\b%s:([0-9A-Za-z_]+)" % k, load_text)
        if m:
            hit[k] = m.group(1)
    print("load 行里读回的值：", hit, "（期望 == 种入）")
    bad = [k for k, v in SEED.items() if hit.get(k) != v]
    print("判定：%s" % ("**PASS —— 设置读档链路（解析 + 应用）实机成立**" if ok and not bad
                       else "**未达预期**（load ok=%s，差异=%s）" % (ok, bad)))
    print("日志：", log)
    return 0 if (ok and not bad) else 1


if __name__ == "__main__":
    if "--all" in sys.argv:
        if not os.path.exists(os.path.join(RUN, "savedata", "ui_state.txt")):
            print("（首次）先建目录并跑一轮引擎，以取得它自己写的 ui_state.txt …")
            build(); run_and_check(wait=100)
        seed_state()
        sys.exit(run_and_check())
    print(__doc__)
