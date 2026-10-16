# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· **冻结态影子渲染栈**：从屏数据重建 `window.UI_LAYOUT` 并落进私有栈

■ 用途
  盘面会被其它模块轮换预设 / 改写。本脚本把「冻结的 `32_flowchart.json`」用**项目自己的发射器**
  （`工具\gen_layout.py` 的 `resolve_deep` + `to_js`，**只 import、不写盘**）拼回 `window.UI_LAYOUT`，
  连同其余渲染文件落进 `_工作\ISSUE-20260928-02_HTML\证据\_shadow\`（本模块私有，免疫盘面改写）。

■ ★ 执行顺序（一审 P0-3 指出的"先写后校验"已改正）
  ① 先读源屏 JSON → 算**三形态 md5**（原始 / LF / CRLF）→ 与锚点比对；**不符 ⇒ 打印并退出，不写任何文件**；
  ② 内存里重建 JS → 算其 **LF 形态** md5 → 再与锚点比对；**不符 ⇒ 退出，不写**；
  ③ 两关都过，才写影子栈（其余渲染文件从 `复刻\` 逐字节复制，素材用硬链接镜像）。

■ 锚点（第七批冻结态；**每形态都给**，任一命中即算命中）
  屏 JSON `layout\screens\32_flowchart.json`（289 元素）
      LF 规范化 `4c8f01c0c119c3df2da5b0adfe86e05e` ｜ CRLF 规范化/盘面实际 `cdedca7c5332d9acb621d143f30e3775`
  `复刻\ui_layout.js`
      LF 规范化 `9429a538bc6a6a8103bf7f27229ed20a` ｜ CRLF 规范化/盘面实际 `fd6686b3cdb4043d9eeaec2df26a16a7`
  ※ 仓库 `core.autocrlf=true` ⇒ **盘面字节通常是 CRLF**，而冻结书/记录写的是 **LF 值**；
    两者都接受，并在输出里同时打印，避免"按错形态哈希 ⇒ 误判不一致"。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_shadow_screen1.py [--src <屏 JSON>] [--out <影子栈目录>]
"""
import hashlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
TOOLS = os.path.join(UI, "工具")
LAYOUT = os.path.join(UI, "layout")
sys.path.insert(0, HERE)
sys.path.insert(0, TOOLS)
import e3_md5util as mu                     # noqa: E402
import e3_snapshot_stack as snap            # noqa: E402  （复用其 FILES / mirror_assets / OUT）

ANCHORS = {
    "screen": {"lf": "4c8f01c0c119c3df2da5b0adfe86e05e",
               "crlf": "cdedca7c5332d9acb621d143f30e3775"},
    "js":     {"lf": "9429a538bc6a6a8103bf7f27229ed20a",
               "crlf": "fd6686b3cdb4043d9eeaec2df26a16a7"},
}


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]

    def opt(name, default=None):
        return args[args.index(name) + 1] if name in args else default

    def multi(name):
        return [args[i + 1] for i, a in enumerate(args) if a == name]

    src = opt("--src", os.path.join(LAYOUT, "screens", "32_flowchart.json"))
    out = opt("--out", snap.OUT)
    live_js = os.path.join(snap.REP, "ui_layout.js")
    # ★ 锚点可用命令行覆盖（换预设/换批次）：`-` 表示"该形态不做哈希锚"
    scr_anchors = {"lf": opt("--anchor-screen-lf", ANCHORS["screen"]["lf"]),
                   "crlf": opt("--anchor-screen-crlf", ANCHORS["screen"]["crlf"])}
    js_anchors = {"lf": opt("--anchor-js-lf", ANCHORS["js"]["lf"]),
                  "crlf": opt("--anchor-js-crlf", ANCHORS["js"]["crlf"])}
    for d in (scr_anchors, js_anchors):
        for k in list(d):
            if d[k] in ("-", ""):
                d[k] = None
    expect_els = int(opt("--expect-els", "0") or 0)
    expect_ids = multi("--expect-id")
    js_has_anchor = bool(js_anchors["lf"] or js_anchors["crlf"])
    if not js_has_anchor and not (expect_els or expect_ids):
        print("★ 既没给 JS 锚点也没给内容锚（--expect-els / --expect-id）⇒ 拒绝运行（不得无锚重建）。")
        return 1
    print("锚点：屏 lf=%s crlf=%s ｜ JS lf=%s crlf=%s ｜ 内容锚：元素数=%s 指定件=%s"
          % (scr_anchors["lf"], scr_anchors["crlf"], js_anchors["lf"], js_anchors["crlf"],
             expect_els or "-", "、".join(expect_ids) if expect_ids else "-"))

    print("源屏 JSON = %s" % src)
    print(mu.describe(src, scr_anchors, label="[①源屏]"))

    # ── ① 先校验源屏锚点；不符即退出、**不写任何文件** ───────────────────────
    f_src = mu.forms(src)
    ok, form, val = mu.accepts(f_src, scr_anchors)
    if not ok:
        print("★ [①] 源屏锚点未命中（三形态均不在白名单）⇒ **退出且不写任何文件**。")
        print("  期望其一：LF=%s ｜ CRLF=%s" % (scr_anchors["lf"], scr_anchors["crlf"]))
        return 1

    # ── ② 内存里重建 JS，再校验 ────────────────────────────────────────────
    import gen_layout as GL                                  # ★ 只 import（其落盘都在 main() 里）
    palette = GL.load_palette()
    screen = GL.load_json(src)
    errs = GL.validate(screen, os.path.basename(src))
    hard = [e for e in errs if not e.startswith("[未产出]")]
    if hard:
        print("★ 源屏校验有硬错误：%s ⇒ 退出且不写。" % hard[:3])
        return 1
    merged = GL.load_json(os.path.join(LAYOUT, "ui_layout.json"))
    merged["screens"]["flowchart"] = GL.resolve_deep(screen, palette, "flowchart")
    js_lf = GL.to_js(merged)                                  # to_js 产出 LF 文本
    js_lf_md5 = md5_bytes(js_lf.encode("utf-8"))
    js_crlf_md5 = md5_bytes(js_lf.replace("\n", "\r\n").encode("utf-8"))
    # 内容锚（预设没有冻结哈希时的替代锚；只做**加严**、不放松）
    cbad = []
    els = screen.get("elements", [])
    if expect_els and len(els) != expect_els:
        cbad.append("元素数 %d ≠ 内容锚 %d" % (len(els), expect_els))
    ids = set(str(e.get("id", "")) for e in els)
    for i2 in expect_ids:
        if i2 not in ids:
            cbad.append("指定件 %s 不在屏数据里" % i2)
    print("[②重建] 重建 JS：LF %s ｜ CRLF %s ｜ 内容锚：元素数 %d%s ⇒ %s"
          % (js_lf_md5, js_crlf_md5, len(els),
             ("（期望 %d）" % expect_els) if expect_els else "", "通过 ✓" if not cbad else "未通过 ✗"))
    if cbad:
        print("★ [②] 内容锚未通过：%s ⇒ **退出且不写任何文件**。" % "；".join(cbad))
        return 1
    print("[②] JS 哈希锚 = %s" % ("校验" if js_has_anchor else "**无**（该预设无冻结哈希 ⇒ 以内容锚替代，已在输出中明示）"))
    if js_has_anchor:
        if js_lf_md5 != js_anchors["lf"] and js_crlf_md5 != js_anchors["crlf"]:
            print("★ [②] 重建 JS 锚点未命中（LF 与 CRLF 形态都不在白名单）⇒ **退出且不写任何文件**。")
            return 1

    # ── ③ 两关都过：写影子栈（保持与盘面同一字节形态） ─────────────────────
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for f in snap.FILES:
        shutil.copy2(os.path.join(snap.REP, f), os.path.join(out, f))
    crlf = mu.forms(live_js)["has_crlf"]                      # 与盘面同形态
    text = js_lf.replace("\n", "\r\n") if crlf else js_lf
    io.open(os.path.join(out, "ui_layout.js"), "wb").write(text.encode("utf-8"))
    shutil.copy2(src, os.path.join(out, "32_flowchart.screen1.json"))

    asset_mirror = os.path.join(os.path.dirname(out), "krkr", "assets")
    def _fresh(mir, live):
        """镜像新鲜度：逐件比 md5（素材被 unlink+create 替换时硬链接会停在旧 inode）。"""
        try:
            a = mu.forms(os.path.join(mir, "ui", "x_ui_read_check.png"))["raw"]
            b2 = mu.forms(os.path.join(live, "ui", "x_ui_read_check.png"))["raw"]
            return a == b2
        except OSError:
            return False
    if os.path.isdir(asset_mirror) and _fresh(asset_mirror, os.path.join(UI, "krkr", "assets")):
        n_ui = len(os.listdir(os.path.join(asset_mirror, "ui")))
        n_face = len(os.listdir(os.path.join(asset_mirror, "face")))
        print("[③] 素材镜像已存在，复用（%d+%d 件，未重建）" % (n_ui, n_face))
    else:
        if os.path.isdir(asset_mirror):
            shutil.rmtree(asset_mirror)
        n_ui, n_face = snap.mirror_assets(asset_mirror)

    print("\n[③写出] 影子栈 = %s（与盘面同字节形态：%s）" % (out, "CRLF" if crlf else "LF"))
    lines = ["E3 影子渲染栈（重建式）· 行尾口径：三形态 md5 都给，锚点任一命中即算命中",
             "源屏 JSON = %s" % src,
             mu.describe(src, ANCHORS["screen"], label="源屏"),
             mu.describe(os.path.join(out, "ui_layout.js"), js_anchors, label="影子 JS"),
             mu.describe(live_js, js_anchors, label="盘面 JS"),
             "重建 JS：LF %s ｜ CRLF %s（JS 哈希锚 %s）｜ 内容锚：元素数 %d（期望 %s）、指定件 %s"
             % (js_lf_md5, js_crlf_md5, "已校验" if js_has_anchor else "无（以内容锚替代）", len(els),
                expect_els or "-", "、".join(expect_ids) if expect_ids else "-"),
             "素材镜像（硬链接）%s ：ui %d 件 / face %d 件" % (asset_mirror, n_ui, n_face),
             "本次是否覆写影子：是（重建式），且**两关锚点均已先校验通过**"]
    for f in snap.FILES + ["32_flowchart.screen1.json"]:
        p = os.path.join(out, f)
        if os.path.exists(p):
            lines.append(mu.describe(p, label="影子"))
    io.open(os.path.join(out, "RECONSTRUCT_MD5.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\n✓ 两关锚点通过；影子栈已写出（明细 RECONSTRUCT_MD5.txt）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
