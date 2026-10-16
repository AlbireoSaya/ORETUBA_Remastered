# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 把**当前盘面**（新冻结态）快照成私有渲染栈，后续测量全在快照上做

■ 为什么
  盘面会被其它模块继续改写（数据层重跑预设 / 文档模块）。测量必须钉在一个**不变的快照**上；
  快照由盘面**逐字节复制**而来（不跑任何生成器），并记录 md5 与关键结构自证，供报告引用。

■ 快照内容（落 `_工作\ISSUE-20260928-02_HTML\证据\_shadow\`）
  ui_layout.js、index.html、replica.css、replica.js、flow_data.js、asset_index.js
  32_flowchart.screen1.json   ← 盘面 `layout/screens/32_flowchart.json` 的原样副本
  STACK_MD5.txt               ← 全部 md5 + 结构自证（元素数 / 外壳数 / 层内容数 / 底托件清单）

■ 自证（不满足即报错退出）
  ① 屏 JSON 三形态 md5（原始/LF/CRLF）**任一命中**白名单（默认 LF `4c8f01c0…` / CRLF `cdedca7c…`，第七批冻结态；可用 `--want-md5` 覆盖）；**不符即退出且不写任何文件**；
  ② 元素数 == 289（默认；可 `--want-els` 覆盖）；外壳（无 vis_flag）== 61；
  ③ 6 件 `fc.frag<G>_title_bg` 全部存在、全部**带 `vis_flag=fc_layer`**、`vis_when=frag<G>`
     （⇒ 属**层内容**，不计入「外壳 61 件」）；
  ④ 外壳（不带 vis_flag）仍 == 61 件。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_snapshot_stack.py
"""
import hashlib
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e3_md5util as mu                                   # noqa: E402

HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
OUT = os.path.join(HTML_DIR, "证据", "_shadow")
# ★ 锚点**每形态都给**（行尾健壮；仓库 autocrlf=true ⇒ 盘面字节通常是 CRLF，记录写的是 LF 值）
ANCHORS = {"lf": "4c8f01c0c119c3df2da5b0adfe86e05e",          # 第七批冻结态（LF 规范化）
           "crlf": "cdedca7c5332d9acb621d143f30e3775"}        # 同内容的 CRLF 形态（＝盘面实际字节）
JS_ANCHORS = {"lf": "9429a538bc6a6a8103bf7f27229ed20a",       # 复刻/ui_layout.js 第七批（LF）
              "crlf": "fd6686b3cdb4043d9eeaec2df26a16a7"}     # 同内容的 CRLF 形态（＝盘面实际字节）
WANT_JSON_MD5 = ANCHORS["lf"]                                 # 命令行 --want-md5 的默认值
WANT_ELS = 289
WANT_SHELL = 61
FILES = ["index.html", "replica.css", "replica.js", "flow_data.js", "asset_index.js", "ui_layout.js",
         "_selftest_states.html"]


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def mirror_assets(dst):
    """把 `krkr/assets/{ui,face}` **硬链接**到 `<证据>/krkr/assets/`。
    目的：快照页 `_shadow/index.html` 的默认素材根是相对路径 `../krkr/assets`
    ⇒ 必须有 `<证据>/krkr/assets` 才能解析（否则图片 naturalWidth=0，套 B 的
    `zeronine.*` 会假失败——实测过）。硬链接零拷贝；原件被**替换**（unlink+create）时
    镜像保留旧 inode，正合"快照免疫改写"之意。"""
    n_ui = n_face = 0
    for sub in ("ui", "face"):
        src = os.path.join(UI, "krkr", "assets", sub)
        if not os.path.isdir(src):
            continue
        d = os.path.join(dst, sub)
        os.makedirs(d, exist_ok=True)
        for name in os.listdir(src):
            s = os.path.join(src, name)
            if not os.path.isfile(s):
                continue
            try:
                os.link(s, os.path.join(d, name))
            except OSError:
                shutil.copy2(s, os.path.join(d, name))
            if sub == "ui":
                n_ui += 1
            else:
                n_face += 1
    return n_ui, n_face


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    want = args[args.index("--want-md5") + 1] if "--want-md5" in args else WANT_JSON_MD5
    want_els = int(args[args.index("--want-els") + 1]) if "--want-els" in args else WANT_ELS

    src_json = os.path.join(LAYOUT, "screens", "32_flowchart.json")
    sc = json.load(io.open(src_json, encoding="utf-8"))
    els = sc["elements"]
    shell = [e for e in els if not e.get("vis_flag")]
    content = [e for e in els if e.get("vis_flag")]
    bg = [e for e in els if "_title_bg" in str(e.get("id", ""))]
    bad = []
    # ── ① 先校验锚点（行尾健壮：三形态任一命中即算命中）；不符 ⇒ 退出且**不写任何文件** ──
    fs = mu.forms(src_json)
    ok, form, val = mu.accepts(fs, ANCHORS)
    print(mu.describe(src_json, ANCHORS, label="[①源屏]"))
    if not ok:
        print("★ [①] 源屏锚点未命中（原始/LF/CRLF 三形态均不在白名单）⇒ **退出且不写任何文件**。")
        print("  期望其一：LF=%s ｜ CRLF=%s ｜ （也接受命令行 --want-md5 覆盖）"
              % (ANCHORS["lf"], ANCHORS["crlf"]))
        return 1
    if want != ANCHORS["lf"]:
        fs2 = {}
        ok2 = (fs.get("lf") == want) or (fs.get("crlf") == want) or (fs.get("raw") == want)
        if not ok2:
            print("★ [①] 命令行 --want-md5=%s 与源屏三形态均不符 ⇒ 退出且不写。" % want)
            return 1
    if len(els) != want_els:
        print("★ [①] 元素数 %d ≠ 期望 %d ⇒ 退出且不写。" % (len(els), want_els))
        return 1
    if len(shell) != WANT_SHELL:
        print("★ [①] 外壳件（无 vis_flag）%d ≠ 期望 %d ⇒ 退出且不写。" % (len(shell), WANT_SHELL))
        return 1
    if len(bg) != 6:
        print("★ [①] 底托件 %d ≠ 6 ⇒ 退出且不写。" % len(bg))
        return 1
    for e in bg:
        if e.get("vis_flag") != "fc_layer":
            print("★ [①] %s 的 vis_flag=%r ≠ fc_layer（会被误算进外壳）⇒ 退出且不写。" % (e.get("id"), e.get("vis_flag")))
            return 1
        if not str(e.get("vis_when", "")).startswith("frag"):
            print("★ [①] %s 的 vis_when=%r 不以 frag 开头 ⇒ 退出且不写。" % (e.get("id"), e.get("vis_when")))
            return 1

    # ── ② 校验通过才写 ─────────────────────────────────────────────────────
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for f in FILES:
        shutil.copy2(os.path.join(REP, f), os.path.join(OUT, f))
    shutil.copy2(src_json, os.path.join(OUT, "32_flowchart.screen1.json"))
    asset_mirror = os.path.join(os.path.dirname(OUT), "krkr", "assets")
    if os.path.isdir(asset_mirror):
        shutil.rmtree(asset_mirror)
    n_ui, n_face = mirror_assets(asset_mirror)

    lines = ["E3 影子渲染栈快照（ISSUE-20260928-02 · HTML 侧）",
             "来源：盘面逐字节复制（不跑任何生成器）",
             "★ 行尾口径（本工程通用写法）：仓库 core.autocrlf=true ⇒ **盘面实际字节通常是 CRLF**，",
             "   而冻结书/记录里写的是 **LF 规范化值**。故每件都同时给三形态 md5：",
             "   `原始` = 磁盘实际字节 ｜ `LF` = CRLF→LF 规范化 ｜ `CRLF` = LF→CRLF 规范化；锚点任一命中即算命中。",
             "[①源屏] " + mu.describe(src_json, ANCHORS, label="layout/screens/32_flowchart.json"),
             "[盘面JS] " + mu.describe(os.path.join(REP, "ui_layout.js"), JS_ANCHORS, label="复刻/ui_layout.js"),
             "[盘面合并树] " + mu.describe(os.path.join(LAYOUT, "ui_layout.json"), label="layout/ui_layout.json"),
             "元素 %d ｜ 外壳（无 vis_flag）%d ｜ 层内容（带 vis_flag）%d ｜ 底托件 %d"
             % (len(els), len(shell), len(content), len(bg)),
             "口径：外壳 = 不带 vis_flag（两种层共用舞台）；层内容 = 带 vis_flag（含 fc.frag<G>_title_bg）",
             "底托件："]
    for e in bg:
        lines.append("  %-20s %s vis_when=%s rect=%s,%s %sx%s z=%s"
                     % (e["id"], e.get("asset"), e.get("vis_when"), e["x"], e["y"], e["w"], e["h"], e.get("z")))
    for f in FILES + ["32_flowchart.screen1.json"]:
        lines.append("快照 " + mu.describe(os.path.join(OUT, f)))
    lines.append("素材镜像（硬链接）%s ：ui %d 件 / face %d 件（供快照页的 `../krkr/assets` 相对路径解析）"
                 % (asset_mirror, n_ui, n_face))
    io.open(os.path.join(OUT, "STACK_MD5.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print("\n✓ 快照自证通过（[①]锚点先校验：屏 JSON 三形态命中 / 元素数 / 外壳 61 / 底托 6；通过后才写出）")
    print("  影子栈目录：%s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
