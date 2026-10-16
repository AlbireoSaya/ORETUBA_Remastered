# -*- coding: utf-8 -*-
r"""M39 · 引擎实拍（表驱动）：每档一个变体，逐个**从原始 TJS 重新起**再打补丁

■ 为什么可以不改正式数据
  引擎读 `<运行副本>\game\ui_layout.tjs`。本脚本自搭运行副本（与 `krkr\run_autotour.bat`
  同一套镜像口径：game + assets → RUN\game、runtime → RUN\runtime、项目根放 autotour.txt），
  **只改副本里的 ui_layout.tjs**；收尾断言 4 个正式文件 md5 前后不变。

■ ★★ 踩过的坑（本轮真实发生，务必保留这条教训）
  第一版脚本按「先改 opacity、再叠层」的顺序**在同一个 TJS 上连续打补丁**，
  于是「双叠 150×2」那一轮实际拿到的是「双叠 **255×2**」——因为上一轮已把 opacity
  改成了 255。**症状**：巡查只看到"跑完了、出图了、日志干净"，看不出任何异常；
  是**引擎实拍强度自证**（反推 α_eff 并与解析预测比对）把它抓出来的
  （y=950 反推 201 vs 预测 135）。⇒ 本脚本改为**每个变体前先 restore_ui_tjs()**。

■ 变体表
  单层 255 / 双叠 150×2（强度轴）｜ 剖面C（y400 h680 线性）/ 剖面D（y200 h880 t^0.8）（剖面轴）

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_engine_shots.py [变体名…]
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
KRKR = os.path.join(UI, "krkr")
RUN = "E:/ZCode Workspace/Galgame/临时/wt-qbicons/临时/ui_run_m39strong"
PROF_DIR = os.path.join(EVID, "剖面实验")
EXE = "tvpwin32.exe"
PRISTINE = os.path.join(KRKR, "game", "ui_layout.tjs")
OFFICIAL = [os.path.join(UI, "layout", "screens", "10_dialog.json"),
            os.path.join(UI, "layout", "ui_layout.json"),
            PRISTINE,
            os.path.join(UI, "复刻", "ui_layout.js")]

MARK_ID = '        id: "dlg.mask_bottom",'
MARK_NEXT = '\n      ], %[\n        id: "dlg.name",'
OFFICIAL_ASSET = "ui/x_ui_dlgmask_bottom.png"

# 变体名 → (元素 asset, y, h, opacity, 额外层数, 输出 PNG 名)
VARIANTS = [
    ("单层255", (OFFICIAL_ASSET, 680, 400, 255), 0, "M39_引擎导出_dialog_遮罩255.png"),
    ("双叠150x2", (OFFICIAL_ASSET, 680, 400, 150), 1, "M39_引擎导出_dialog_双叠150x2.png"),
    ("剖面C", ("ui/x_ui_dlgmask_bottom_h680_lin.png", 400, 680, 150), 0,
     "M39_引擎导出_dialog_剖面C.png"),
    ("剖面D", ("ui/x_ui_dlgmask_bottom_h880_t0.8.png", 200, 880, 150), 0,
     "M39_引擎导出_dialog_剖面D.png"),
    # ★ 定稿方向：贴底 250px · 线性 · 85%（opacity 217）
    ("定稿250px线性85", ("ui/x_ui_dlgmask_bottom_h250_lin.png", 830, 250, 217), 0,
     "M39_引擎导出_dialog_250px_线性85.png"),
    # 现行 A：不打任何补丁（= 正式数据 y680 h400 t^1.6 opacity150），用于同轮对照
    ("现行A", (OFFICIAL_ASSET, 680, 400, 150), 0,
     "M39_引擎导出_dialog_现行A.png"),
    # ★ 定稿轮（贴底 350px 线性）：85% 与 90%
    ("定稿350px85", ("ui/x_ui_dlgmask_bottom_350.png", 730, 350, 217), 0,
     "M39_引擎导出_dialog_350px_85.png"),
    ("定稿350px90", ("ui/x_ui_dlgmask_bottom_350.png", 730, 350, 230), 0,
     "M39_引擎导出_dialog_350px_90.png"),
]


def md5s():
    return {os.path.relpath(p, UI): hashlib.md5(open(p, "rb").read()).hexdigest()
            for p in OFFICIAL}


def mirror():
    if os.path.exists(RUN):
        shutil.rmtree(RUN, ignore_errors=True)
    os.makedirs(os.path.join(RUN, "game"), exist_ok=True)
    for src, dst in [(os.path.join(KRKR, "game"), os.path.join(RUN, "game")),
                     (os.path.join(KRKR, "assets"), os.path.join(RUN, "game", "assets")),
                     (os.path.join(KRKR, "runtime"), os.path.join(RUN, "runtime"))]:
        subprocess.run(["xcopy", src, dst, "/E", "/I", "/Y", "/Q"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    io.open(os.path.join(RUN, "game", "autotour.txt"), "w").write("autotour\n")
    # 实验素材拷进运行副本的 assets\ui（正式 assets 目录不动）
    for f in os.listdir(PROF_DIR):
        shutil.copyfile(os.path.join(PROF_DIR, f),
                        os.path.join(RUN, "game", "assets", "ui", f))
    assert os.path.exists(os.path.join(RUN, "runtime", EXE)), "运行副本缺 %s" % EXE
    print("  运行副本已建：%s（含 %d 张实验素材）" % (RUN, len(os.listdir(PROF_DIR))))


def restore_ui_tjs():
    """★ 每个变体前把副本的 ui_layout.tjs **还原成原始件**，杜绝补丁叠加"""
    shutil.copyfile(PRISTINE, os.path.join(RUN, "game", "ui_layout.tjs"))


def patch(asset, y, h, opacity, extra):
    tjs = os.path.join(RUN, "game", "ui_layout.tjs")
    t = io.open(tjs, encoding="utf-8").read()
    i0, i1 = t.index(MARK_ID), t.index(MARK_NEXT)
    seg = t[i0:i1]                       # 遮罩元素的全部字段行
    for old, new in [('        asset: "%s",' % OFFICIAL_ASSET, '        asset: "%s",' % asset),
                     ('        y: 680,', '        y: %d,' % y),
                     ('        h: 400,', '        h: %d,' % h),
                     ('        opacity: 150,', '        opacity: %d,' % opacity)]:
        assert seg.count(old) == 1, "遮罩块内 %r 出现 %d 次（期望 1）" % (old, seg.count(old))
        seg = seg.replace(old, new)
    out = t[:i0] + seg                   # 到遮罩字段尾为止
    if extra > 0:
        dup = seg.replace('id: "dlg.mask_bottom",', 'id: "dlg.mask_bottom2",')
        assert '        z: 15,' in dup, "遮罩块内找不到 z: 15"
        dup = dup.replace('        z: 15,', '        z: 16,', 1)
        out += "\n      ], %[\n" + dup
    out += t[i1:]                        # 原样接回「], %[ id: dlg.name …」
    io.open(tjs, "w", encoding="utf-8").write(out)
    print("  补丁：asset=%s y=%d h=%d opacity=%d 额外层=%d"
          % (os.path.basename(asset), y, h, opacity, extra))


def run_tour(tag):
    sd = os.path.join(RUN, "runtime", "savedata")
    if os.path.isdir(sd):
        for f in os.listdir(sd):
            try:
                os.remove(os.path.join(sd, f))
            except OSError:
                pass
    print("  [%s] 启动引擎（无人值守巡演，约 50 s）…" % tag)
    p = subprocess.Popen([os.path.join(RUN, "runtime", EXE), os.path.join(RUN, "game")],
                         cwd=os.path.join(RUN, "runtime"),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while p.poll() is None and time.time() - t0 < 300:
        time.sleep(2)
    if p.poll() is None:
        p.kill()
        print("  !! 超时，已 kill")
        return None
    print("  [%s] 引擎退出 rc=%s，用时 %.0f s" % (tag, p.poll(), time.time() - t0))
    log = os.path.join(sd, "krkr.console.log")
    if os.path.exists(log):
        txt = io.open(log, encoding="utf-16-le", errors="replace").read()
        for ln in txt.splitlines():
            if "屏=dialog" in ln and "标签=对话框" in ln:
                print("     " + ln.strip())
        print("     " + " ｜ ".join("%s=%d" % (k, txt.count(k))
                                    for k in ("An exception occured", "redraw EXCEPTION",
                                              "[UI][MISS]")))
    shot = os.path.join(sd, "shot_03_dialog.png")
    return shot if os.path.exists(shot) else None


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    print("=" * 88)
    print("M39 · 引擎实拍（表驱动，每档先还原 ui_layout.tjs 再打补丁）")
    print("=" * 88)
    before = md5s()
    tl = subprocess.run(["tasklist", "/FI", "IMAGENAME eq tvpwin32.exe"],
                        stdout=subprocess.PIPE).stdout.decode("gbk", "replace")
    print("  跑前 tasklist：%s" % ("无 tvpwin32" if "tvpwin32" not in tl else "**有残留！**"))
    mirror()
    ok = True
    for name, (asset, y, h, opa), extra, out in VARIANTS:
        if want and name not in want:
            continue
        print("\n" + "-" * 88)
        print("■ 变体 %s" % name)
        restore_ui_tjs()
        patch(asset, y, h, opa, extra)
        shot = run_tour(name)
        if shot is None:
            ok = False
            continue
        dst = os.path.join(EVID, out)
        shutil.copyfile(shot, dst)
        print("  → %s（%d 字节）" % (out, os.path.getsize(dst)))
    after = md5s()
    same = (before == after)
    print("\n■ 正式数据未被改动（4 个受保护文件 md5 前后对比）= %s" % same)
    for k in sorted(before):
        print("   %-34s %s%s" % (k, before[k][:12],
                                 "" if before[k] == after[k] else "  **变了！→ " + after[k][:12]))
    tl = subprocess.run(["tasklist", "/FI", "IMAGENAME eq tvpwin32.exe"],
                        stdout=subprocess.PIPE).stdout.decode("gbk", "replace")
    print("\n  跑后 tasklist：%s" % ("无 tvpwin32" if "tvpwin32" not in tl else "**有残留！**"))
    return 0 if (ok and same) else 1


if __name__ == "__main__":
    sys.exit(main())
