#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_e2_fixture.py — ISSUE-20260927-05 / E2 · 流程图连线渲染的**可复跑自证机件**

做什么
  1. 把 krkr\\game + krkr\\assets + krkr\\runtime 镜像到一个**临时运行目录**（同 run_autotour.bat 的口径）；
  2. 把 links_fixture.json 里的夹具节点/连线**注入运行目录的 ui_layout.tjs 副本**
     （`临时\\ui_run_e2_fixture\\game\\ui_layout.tjs`），**绝不改仓库 layout\\**；
  3. 写 autotour.txt 起巡演，等它走到 flowchart 屏（引擎自导 shot_NN_flowchart.png，**不是抓屏**）；
  4. 摘出与 [UI][FLOWLINK] 相关的日志行，落一份 .txt 到本目录。

两种模式
  默认        ：带 layerExDraw.dll（正向自证）
  --no-dll   ：**负向对照** —— 删掉运行目录里的 layerExDraw.dll，Plugins.link 必然失败，
               断言「不画线 + 日志有中文提示 + 不崩（EXCEPTION 0、巡演照常结束）」

用法（本目录下）
  python run_e2_fixture.py
  python run_e2_fixture.py --no-dll
  python run_e2_fixture.py --timeout 300

注意
  · 巡演 81 步 × 2 s/步 ≈ 162 s（UI_TOUR_STEP_MS=2000，见 startup.tjs），故超时默认 300 s。
  · 引擎进程据 POC 实测**不会自行退出**，本脚本在日志出现「巡演结束」后 taskkill 兜底。
  · 产物 PNG 落在 <运行目录>\\runtime\\savedata\\，由 check_e2_png.py 做像素核对。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../取证/E2_自证
UI = HERE.parents[3]                            # .../UI组
GAME = HERE.parents[4]                          # .../我们没有翅膀——格雷塔迦露德与柳木原
WT = HERE.parents[6]                            # 工作树根（含 临时\）
KRKR = UI / "krkr"

REAL_ALPHA = 0xFF << 24


def log(msg):
    print(msg, flush=True)


def read_palette_colors():
    with open(UI / "layout" / "palette.json", encoding="utf-8") as f:
        return {k: v for k, v in json.load(f)["colors"].items() if not k.startswith("_")}


def color_int(colors, ref):
    v = colors[ref]["value"]            # '#RRGGBB'
    return REAL_ALPHA | int(v[1:], 16)


# ---------------------------------------------------------------- 夹具几何自检
def compute_pts(nodes, link):
    """按契约 §三 路由口径从节点几何复算 pts，并与夹具里写死的 pts 逐点比对（防手抄错）"""
    a = nodes[link["src"]]
    b = nodes[link["dst"]]
    ax, ay, aw, ah = a["rect"]
    bx, by, bw, bh = b["rect"]
    sx, sy = ax + 148, ay + ah          # 源节点底边中点
    tx, ty = bx + 148, by               # 目标节点顶边中点
    form = link["form"]
    if form == "straight" or form == "straight-novector":
        return [[sx, sy], [tx, ty]]
    if form == "VZ":
        my = (sy + ty) / 2.0
        return [[sx, sy], [sx, my], [tx, my], [tx, ty]]
    if form == "VL":
        ex = sx + (148 if tx > sx else -148)
        return [[ex, sy - 32], [tx, sy - 32], [tx, ty]]
    raise SystemExit("未知 form: %s" % form)


def check_fixture():
    fx = json.load(open(HERE / "links_fixture.json", encoding="utf-8"))
    nodes = {n["id"]: n for n in fx["nodes"]}
    errs = []
    for lk in fx["links"]:
        got, want = compute_pts(nodes, lk), lk["pts"]
        if got != want:
            errs.append("%s: 复算 %s != 夹具 %s" % (lk["id"], got, want))
        # 相邻点只有一维变化（正交）
        for i in range(1, len(want)):
            if want[i][0] != want[i - 1][0] and want[i][1] != want[i - 1][1]:
                errs.append("%s: 第 %d 段非正交" % (lk["id"], i))
        # arrow ⇒ 末段长度 ≥ 2.0*w
        last = want[-1]
        prev = want[-2]
        seg = abs(last[0] - prev[0]) + abs(last[1] - prev[1])
        if lk["arrow"] and seg < 2.0 * lk["w"]:
            errs.append("%s: arrow 但末段长 %s < 2.0*w" % (lk["id"], seg))
    if errs:
        print("[FAIL] 夹具几何自检：")
        for e in errs:
            print("   " + e)
        raise SystemExit(1)
    log("[OK] 夹具几何自检：pts 与契约公式一致（%d 条边，%d 个节点）" % (len(fx["links"]), len(fx["nodes"])))
    return fx


# ---------------------------------------------------------------- TJS 注入
def tjs_num(v):
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return repr(v)


def build_injection(fx, colors, tint=None):
    """tint: 非 None 时把所有连线的颜色**统一改成该 0xAARRGGBB 整数**
    （只用于「复核机件是否真从数据读色」的注入自证；不改仓库数据）"""
    lines = []
    lines.append("")
    lines.append("// ===================== E2 FIXTURE INJECTION (scratch copy only) =====================")
    lines.append("// 由 _工作\\ISSUE-20260927-05_流程图实现\\取证\\E2_自证\\run_e2_fixture.py 注入；")
    lines.append("// 只存在于运行目录的 ui_layout.tjs 副本，仓库 layout\\ 未被改动。")
    # 夹具节点（矩形色块；只为读出连线端点，不冒充 E1 的真实节点框）
    # ★ 色值口径差异（自证踩到的坑）：**元素色 = 0xRRGGBB**（`uiThemeColor` 原样透传给
    #   `Layer.colorRect`，全库既有元素都是 6 位），而**连线色 = 0xAARRGGBB**（契约 §三，
    #   GdiPlus 的 ARGB）。夹具节点若不掐掉 alpha 位会渲染成黑块 ⇒ 这里按 6 位写。
    fill = color_int(colors, "highlight") & 0xFFFFFF
    lines.append("if(UILayoutData.screens.flowchart.elements !== void) {")
    # ★ 夹具隔离（2026-09-27 追加）：先摘掉生成器产的**图内容层**（契约 §一 列出的那批 id），
    #   否则 E1 的真实节点框会压住夹具走廊 —— 实测本层 117 元素时出现「采样点 1~4 个被判被遮、
    #   箭头探针 line_run=0 ⇒ 判定不成立」。摘掉后夹具 = 屏装饰(chrome) + 夹具节点/连线，
    #   与 E1 的并发改动**完全解耦**，同一夹具每次跑出同一张图（可复现）。
    lines.append("  var __fxEls = UILayoutData.screens.flowchart.elements;")
    lines.append("  var __fxDrop = [ \"fc.node.\", \"fc.label.\", \"fc.branch.\", \"fc.entry.\","
                 " \"fc.newmark\", \"fc.n_section\", \"fc.n_select\", \"fc.n_extra\" ];")
    lines.append("  var __fxKeep = [];")
    lines.append("  for(var __fxI = 0; __fxI < __fxEls.count; __fxI++) {")
    lines.append("    var __fxE = __fxEls[__fxI];")
    lines.append("    var __fxId = \"\" + __fxE.id;")
    lines.append("    var __fxCut = false;")
    lines.append("    for(var __fxJ = 0; __fxJ < __fxDrop.count; __fxJ++) {")
    lines.append("      if(__fxId.indexOf(__fxDrop[__fxJ]) == 0) { __fxCut = true; break; }")
    lines.append("    }")
    lines.append("    if(!__fxCut) __fxKeep.push(__fxE);")
    lines.append("  }")
    lines.append("  UILayoutData.screens.flowchart.elements = __fxKeep;")
    lines.append("  Debug.message(\"[UI][FLOWLINK][FIXTURE] stripped content layer: kept=\""
                 " + __fxKeep.count + \" of \" + __fxEls.count);")
    for n in fx["nodes"]:
        x, y, w, h = n["rect"]
        lines.append("  UILayoutData.screens.flowchart.elements.push(%[")
        lines.append("    id: %s, kind: \"rect\", x: %d, y: %d, w: %d, h: %d, z: 20,"
                     % (json.dumps(n["id"]), x, y, w, h))
        lines.append("    color: 0x%06X, opacity: 210 ]);" % fill)
    # 夹具连线（顶层键 links，与契约 §三 同字段）
    eff = []
    lines.append("  UILayoutData.screens.flowchart.links = [")
    for i, lk in enumerate(fx["links"]):
        pts = ", ".join("[" + ",".join(tjs_num(c) for c in p) + "]" for p in lk["pts"])
        tail = "" if i == len(fx["links"]) - 1 else ","
        col = color_int(colors, lk["color_ref"]) if tint is None else (tint | 0)
        eff.append({"id": lk["id"], "pts": lk["pts"], "w": lk["w"], "color": col,
                    "arrow": bool(lk["arrow"])})
        # ★ 结尾**不留逗号**：TJS2 的数组字面量把尾逗号当成一个额外空元素
        #   （实测：4 条 + 尾逗号 ⇒ links.count == 5），真实生成器（gen_layout.py 的
        #   tjs_literal）用 ", ".join 拼接、同样不留尾逗号 ⇒ 夹具与真数据同形。
        lines.append("    %%[ id: %s, kind: \"normal\", pts: [%s], w: %d, color: 0x%08X, arrow: %s ]%s"
                     % (json.dumps(lk["id"]), pts, lk["w"], col,
                        "true" if lk["arrow"] else "false", tail))
    lines.append("  ];")
    lines.append("}")
    lines.append("Debug.message(\"[UI][FLOWLINK][FIXTURE] injected links=\" + UILayoutData.screens.flowchart.links.count);")
    lines.append("// =================== E2 FIXTURE INJECTION END ===================")
    lines.append("")
    return "\n".join(lines), eff


# ---------------------------------------------------------------- 镜像
def mirror(run_dir):
    if (run_dir / "game").exists():
        shutil.rmtree(run_dir / "game")
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(KRKR / "game", run_dir / "game")
    shutil.copytree(KRKR / "assets", run_dir / "game" / "assets")
    if not (run_dir / "runtime").exists():
        shutil.copytree(KRKR / "runtime", run_dir / "runtime")
    # 与 bat 的 [4b/6] 同口径：插件目录每次强制刷新
    plug_dst = run_dir / "runtime" / "plugin"
    plug_dst.mkdir(parents=True, exist_ok=True)
    for f in (KRKR / "plugin").iterdir():
        if f.is_file():
            shutil.copy2(f, plug_dst / f.name)
    return run_dir


# ---------------------------------------------------------------- 运行
def tail_log(run_dir):
    p = run_dir / "runtime" / "savedata" / "krkr.console.log"
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-dll", action="store_true", help="负向对照：删掉运行目录里的 layerExDraw.dll")
    ap.add_argument("--timeout", type=int, default=300, help="等待巡演结束的秒数（默认 300）")
    ap.add_argument("--keep", action="store_true", help="保留旧运行目录（默认不删，仅覆盖文件）")
    ap.add_argument("--tint", default="", help="把所有连线色统一改成该 0xAARRGGBB（如 0xFF65B1D4）——"
                                              "用于自证「渲染与复核都从数据读色」，不改仓库数据")
    ap.add_argument("--tag", default="", help="证据文件名后缀（区分同一轮的不同自证）")
    args = ap.parse_args()

    tint = int(args.tint, 16) if args.tint else None
    fx = check_fixture()
    colors = read_palette_colors()

    run_dir = WT / "临时" / ("ui_run_e2_nodll" if args.no_dll else "ui_run_e2_fixture")
    if args.no_dll and run_dir.exists() and not args.keep:
        shutil.rmtree(run_dir)
    log("[1/5] run dir = %s" % run_dir)
    mirror(run_dir)

    # 注入夹具
    layout_tjs = run_dir / "game" / "ui_layout.tjs"
    txt = layout_tjs.read_text(encoding="utf-8")
    if "E2 FIXTURE INJECTION" in txt:
        txt = txt.split("// ===================== E2 FIXTURE INJECTION (scratch copy only) =====================")[0]
    inj, eff = build_injection(fx, colors, tint)
    layout_tjs.write_text(txt + inj, encoding="utf-8")
    log("[2/5] fixture injected into %s" % layout_tjs)
    # ★ 落一份「本次**实际注入**的连线数据」（含解析后的颜色整数）——复核机具据此读色，
    #   与注入同源，杜绝「机具自己再推一遍色」造成的口径漂移；也是「从数据读色」的证据链。
    eff_path = HERE / ("fixture_effective%s.json" % (("_" + args.tag) if args.tag else ""))
    eff_path.write_text(json.dumps({
        "_what": "run_e2_fixture.py 本次**实际注入**运行目录的 links（颜色已解析为 0xAARRGGBB 整数）",
        "_tint": args.tint or "(未覆盖，取自 links_fixture.json 的 color_ref → palette)",
        "run_dir": str(run_dir),
        "links": eff,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    log("[2/5] effective fixture data -> %s" % eff_path)

    # 负向对照：删掉 dll（exe 目录与 plugin\ 子目录两处都查一遍）
    dll_state = "present"
    if args.no_dll:
        removed = []
        for cand in ((run_dir / "runtime" / "layerExDraw.dll"),
                     (run_dir / "runtime" / "plugin" / "layerExDraw.dll")):
            if cand.exists():
                cand.unlink()
                removed.append(str(cand))
        dll_state = "removed: " + (", ".join(removed) if removed else "(no dll found!)")
        log("[3/5] NEGATIVE CONTROL -> %s" % dll_state)
    else:
        log("[3/5] dll present: %s" % (run_dir / "runtime" / "plugin" / "layerExDraw.dll"))

    # autotour 触发
    (run_dir / "game" / "autotour.txt").write_bytes(b"autotour\n")
    savedata = run_dir / "runtime" / "savedata"
    savedata.mkdir(parents=True, exist_ok=True)
    for old in savedata.glob("*"):
        if old.is_file():
            try:
                old.unlink()
            except OSError:
                pass

    log("[4/5] launching tvpwin32.exe (tour 81 steps x 2s ~= 162s) ...")
    exe = run_dir / "runtime" / "tvpwin32.exe"
    # 引擎往 stdout 写 GBK 字节，Python 按 UTF-8 解码会抛 UnicodeDecodeError（无害但刷栈）
    #   ⇒ 直接丢弃子进程 stdout/stderr；引擎日志请看 savedata\krkr.console.log。
    proc = subprocess.Popen([str(exe), str(run_dir / "game")], cwd=str(run_dir / "runtime"),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    t0 = time.time()
    done = False
    while time.time() - t0 < args.timeout:
        time.sleep(3)
        lg = tail_log(run_dir)
        if ("巡演结束" in lg) or ("quit (autotour" in lg):
            done = True
            break
        if proc.poll() is not None:
            done = True
            break
    time.sleep(3)
    subprocess.run(["taskkill", "/F", "/IM", "tvpwin32.exe"],
                   capture_output=True, text=True)
    log("[5/5] tour %s after %.0fs (process exit=%s)"
        % ("finished" if done else "TIMEOUT", time.time() - t0, proc.poll()))

    # 摘日志
    lg = tail_log(run_dir)
    keys = ("FLOWLINK", "EXCEPTION", "TRACE", "屏=flowchart", "巡演结束", "PNG 导出")
    keep = [ln.rstrip() for ln in lg.splitlines() if any(k in ln for k in keys)]
    tag = "负向_无dll" if args.no_dll else "正向"
    if args.tag:
        tag = tag + "_" + args.tag
    out = HERE / ("E2_%s_巡演日志摘录.txt" % tag)
    hdr = [
        "ISSUE-20260927-05 / E2 · run_e2_fixture.py 摘录（%s）" % tag,
        "run dir : %s" % run_dir,
        "dll     : %s" % dll_state,
        "fixture : %s" % (HERE / "links_fixture.json"),
        "PNG     : %s" % (savedata / "shot_77_flowchart.png"),
        "=" * 70,
    ]
    out.write_text("\n".join(hdr + keep) + "\n", encoding="utf-8")
    log("[OUT] %s" % out)
    # ★ 把引擎自导的流程图 PNG **立刻复制进证据目录** —— 运行目录下一次跑就被清空，
    #   不复制就会丢证据（本机实测踩过：链式跑第二轮把第一轮的图删了）。
    slug = ("nodll" if args.no_dll else "positive") + (("_" + args.tag) if args.tag else "")
    for p in sorted(savedata.glob("shot_*_flowchart.png")):
        dst = HERE / ("E2_巡演图_%s_%s" % (slug, p.name))
        shutil.copy2(p, dst)
        log("[OUT] PNG -> %s" % dst)
    log("[OUT] PNG dir = %s" % savedata)
    log("--- FLOWLINK / EXCEPTION lines ---")
    for ln in keep:
        log("  " + ln)
    if not done:
        log("[WARN] 巡演未在 %ds 内结束（可能只是慢；日志摘录仍已落盘）" % args.timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
