# -*- coding: utf-8 -*-
r"""audit_unused_assets.py —— UI 组**闲置资源**盘点（顾问模式 · 只读）

**要回答的问题**：`krkr\assets\` 里有多少素材**当前没有任何运行时引用**、占多少体积，
以及哪些体积其实**不会进成品**（只在开发侧占盘）。

**判据（两档，避免把「潜在可用」冒充实闲）**
  · **硬闲置**：`layout\screens\*.json`（屏数据）**未引用** 且 `krkr\game\*.tjs` + `复刻\*.js`
    （**出货运行时代码**）**也未引用** ⇒ 运行时确实用不到。
  · **软闲置**：屏数据与出货代码都未引用，但**被 `工具\` 或 `_工作\` 的脚本提到**（生成器常量、
    校验器白名单、证据脚本、备选件登记） ⇒ 运行时不用，但**可能是「有意保留的备选/回退件」**，
    删之前要人判。
  · **在用**：屏数据或出货代码引用到。

**引用抽取口径（宁可多算引用，不可漏算）**
  · 屏数据：递归扫**所有字符串值**，取其中以 `.png` 结尾者（覆盖 `asset` / `state_assets` /
    `list.frames` / `item_variants` / `item_buttons` 等任意嵌套位置），按 basename 归并；
  · 出货代码：正则抓 `xxx.png` 字面量（`["'` ] 括起）与 `ui/xxx.png` / `face/xxx.png` 路径字面量；
  · **另单列 `face/` 命名空间**（运行期按说话人换图，屏内只点名 1 件 ⇒ 其余不是"闲置"而是"素材库"）。

**只读**：不写、不删任何素材；只打印与落一份 TSV/JSON 到本目录。
用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python audit_unused_assets.py
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))          # …\UI组
UIROOT = os.path.dirname(UI)                          # …\工程\我们没有翅膀——…
ASSUI = os.path.join(UI, "krkr", "assets", "ui")
ASSFACE = os.path.join(UI, "krkr", "assets", "face")
SCREENS = os.path.join(UI, "layout", "screens")
GAME = os.path.join(UI, "krkr", "game")
REPL = os.path.join(UI, "复刻")
TOOLS = os.path.join(UI, "工具")
WORK = os.path.join(UI, "_工作")
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                      capture_output=True, text=True).stdout.strip()

PNG_RE = re.compile(r"^[A-Za-z0-9_\-]+\.png$")
LIT_RE = re.compile(r"""["'](?:ui/|face/)?([A-Za-z0-9_\-]+\.png)["']""")


def walk_strings(obj, out):
    """递归收集 JSON 里的**所有字符串**。"""
    if isinstance(obj, dict):
        for v in obj.values():
            walk_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_strings(v, out)
    elif isinstance(obj, str):
        out.append(obj)


def refs_from_screens():
    """屏数据里的素材引用（basename 归一）。返回 (basename 集合, 详细记录)。"""
    refs, detail = set(), []
    for fn in sorted(os.listdir(SCREENS)):
        if not fn.endswith(".json"):
            continue
        doc = json.load(io.open(os.path.join(SCREENS, fn), encoding="utf-8"))
        strs = []
        walk_strings(doc.get("elements", []), strs)
        for s in strs:
            b = os.path.basename(s)
            if PNG_RE.match(b):
                refs.add(b)
                detail.append((fn, doc.get("id", "?"), b))
    return refs, detail


def refs_from_code(dirs, exts=(".tjs", ".js", ".py", ".html", ".json"), skip=()):
    r"""代码字面量里的素材名（basename 归一）。

    ★ 扫面必须**排除「素材清单类产物」**：`复刻\asset_index.js` 本身列了**每一件**素材名，
      它出现在任何扫描面里都会把「未引用」全部掩盖成「已引用」（本轮第一次跑就是这样，
      结果荒谬地报「100% 在用」）；`screen_index.js`（屏清单）与 `_selftest_states.html`（自检页）
      同属「清单 / 测试产物」，也不代表运行时使用。
    ★ 工具层只扫 `.py`（`_工作` 下的 `.json` 证据快照会把整屏元素 dump 进来、同样全命中）。
    """
    refs, detail = set(), []
    skip = set(skip)
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            if "__pycache__" in root:
                continue
            for f in files:
                if not f.endswith(exts) or f in skip:
                    continue
                p = os.path.join(root, f)
                try:
                    t = io.open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                for m in LIT_RE.finditer(t):
                    refs.add(m.group(1))
                    detail.append((os.path.relpath(p, UI), m.group(1)))
    return refs, detail


def files_of(d, exts=(".png",)):
    if not os.path.isdir(d):
        return []
    return [f for f in os.listdir(d) if f.lower().endswith(exts)]


def size_of(p):
    try:
        return os.path.getsize(p)
    except OSError:
        return 0


def family(name):
    """文件名 → 前缀族（照 asset_index.js 的分组粒度取「前 3–4 段」的近似）。"""
    stem = name[:-4]
    parts = stem.split("_")
    if stem.startswith("x_ui_"):
        return "x_ui_" + parts[2] if len(parts) > 2 else "x_ui_*"
    if stem.startswith("x_gen_"):
        return "x_gen_" + parts[2] if len(parts) > 2 else "x_gen_*"
    if stem.startswith("x_gal_"):
        return "x_gal_" + parts[2] if len(parts) > 2 else "x_gal_*"
    if stem.startswith("x_psv_"):
        return "x_psv_" + parts[2] if len(parts) > 2 else "x_psv_*"
    return parts[0] + "_*"


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%.2f %s" % (n, u) if u != "B" else "%d B" % n
        n /= 1024.0


def is_ignored(relpath):
    r = subprocess.run(["git", "check-ignore", "-v", relpath], cwd=REPO,
                       capture_output=True, text=True)
    return (r.stdout.strip() or "") if r.returncode == 0 else ""


def dir_stat(path, label):
    if not os.path.isdir(path):
        return {"label": label, "path": path, "files": 0, "bytes": 0}
    n = b = 0
    for root, _d, fs in os.walk(path):
        if "__pycache__" in root:
            continue
        for f in fs:
            n += 1
            b += size_of(os.path.join(root, f))
    return {"label": label, "path": path, "files": n, "bytes": b}


def refs_from_docs():
    r"""`.md` 文档里提到的素材名（**只作「历史/已删屏遗留」的证据**，不算运行时引用）。

    为什么单列这一档：本工程有「只删屏、保留素材」的口径（如 `ending` 屏删除后
    `x_ui_ending_bg.png` 仍在库），这类件在**文档/工程记录/会话交接**里被反复提到，
    但**运行时确实不用** ⇒ 既不能算「在用」，也不该与「全库无人提及的彻底孤儿」混为一谈。
    """
    rels = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "*.md"],
                          cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8").stdout.splitlines()
    refs, detail = set(), []
    for rel in rels:
        if rel.startswith("临时/"):
            continue                    # 其它 worktree 的副本，不计
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in re.finditer(r"[A-Za-z0-9_\-]+\.png", t):
            refs.add(m.group(0))
            detail.append((rel, m.group(0)))
    return refs, detail


def main():
    print("=" * 100)
    print("UI 组闲置资源盘点（只读）｜ %s" % UI)
    print("=" * 100)

    scr_refs, scr_detail = refs_from_screens()
    # 出货运行时代码＝krkr 侧 tjs ＋ HTML 复刻侧 js/html，**排除清单/测试产物**（见 refs_from_code docstring）
    #   ⚠ `krkr\game\ui_layout.tjs` 是**生成布局数据**＝运行时真读的那份 ⇒ 它的素材名是**真引用**；
    #     同名易混的 `复刻\ui_layout.js` 亦同（都保留），只排 `asset_index.js` / `screen_index.js` / 自检页。
    ship_refs, ship_detail = refs_from_code(
        [GAME, REPL], exts=(".tjs", ".js", ".html"),
        skip=("asset_index.js", "screen_index.js", "_selftest_states.html"))
    # 工具层：**只扫 .py**（生成器常量 / 校验器白名单 / 证据脚本）
    tool_refs, tool_detail = refs_from_code([TOOLS, WORK], exts=(".py",))
    # 文档层：只作「历史/已删屏遗留」的证据（不算运行时引用）
    doc_refs, doc_detail = refs_from_docs()

    universe = sorted(files_of(ASSUI))
    total_bytes = sum(size_of(os.path.join(ASSUI, f)) for f in universe)

    used_ship = sorted(f for f in universe if f in scr_refs or f in ship_refs)
    only_tool = sorted(f for f in universe
                       if f not in scr_refs and f not in ship_refs and f in tool_refs)
    only_doc = sorted(f for f in universe
                      if f not in scr_refs and f not in ship_refs and f not in tool_refs
                      and f in doc_refs)
    orphan = sorted(f for f in universe
                    if f not in scr_refs and f not in ship_refs and f not in tool_refs
                    and f not in doc_refs)
    soft = only_tool + only_doc

    def rep(title, names, note=""):
        b = sum(size_of(os.path.join(ASSUI, f)) for f in names)
        print("\n【%s】%d 件 / %s（占素材库 %.1f%%）%s"
              % (title, len(names), human(b), 100.0 * b / total_bytes if total_bytes else 0, note))
        fam = {}
        for f in names:
            k = family(f)
            fam.setdefault(k, [0, 0])
            fam[k][0] += 1
            fam[k][1] += size_of(os.path.join(ASSUI, f))
        for k, (n, bb) in sorted(fam.items(), key=lambda kv: -kv[1][1])[:14]:
            print("    %-26s %3d 件  %10s" % (k, n, human(bb)))
        if len(fam) > 14:
            print("    …（另有 %d 个族，见 TSV）" % (len(fam) - 14))
        return b

    print("\n素材库 `krkr/assets/ui/`：**%d 件 / %s**" % (len(universe), human(total_bytes)))
    print("引用面：屏数据引用 %d 件 ｜ 出货代码引用 %d 件 ｜ 工具/证据脚本提到 %d 件"
          % (len(scr_refs), len(ship_refs), len(tool_refs)))

    b_used = rep("在用（屏数据或出货代码引用）", used_ship)
    b_soft = rep("软闲置 · 仅被脚本提到（可能是备选件/回退件/校验器白名单）", only_tool)
    b_doc = rep("软闲置 · 仅被文档提到（**多为「只删屏保留素材」的历史遗留**）", only_doc)
    b_orphan = rep("硬闲置（**全库无人提及**：屏/代码/脚本/文档都没有）", orphan)

    print("\n★ 小结：在用 %s ｜ 软闲置（脚本）%s ｜ 软闲置（文档）%s ｜ 彻底孤儿 %s"
          % (human(b_used), human(b_soft), human(b_doc), human(b_orphan)))
    print("★ **不参与运行时**的合计 = 软闲置(脚本+文档) + 孤儿 = %s（%d 件）"
          % (human(b_soft + b_doc + b_orphan), len(soft) + len(orphan)))

    # ── face/ 命名空间单列（运行期按说话人换图 ⇒ 不按「闲置」处理）────────────
    faces = sorted(files_of(ASSFACE))
    fb = sum(size_of(os.path.join(ASSFACE, f)) for f in faces)
    face_named = sorted(f for f in faces if ("face/" + f) in " ".join(scr_refs) or f in scr_refs)
    print("\n【face/ 命名空间（头像素材库）】%d 件 / %s" % (len(faces), human(fb)))
    print("    屏内点名到的：%s" % (face_named or "无（屏里写的是 `face/<族>.png` 形式，见下）"))
    print("    ⚠ 口径：运行期按**说话人**换图（映射归编程组）⇒ **整库都算可用**，")
    print("      只有「族」粒度上的冗余（同族多表情）才可能被裁；**不计入闲置**。")

    # ── 开发侧目录（**不会进成品** 的那部分体积）────────────────────────────
    print("\n" + "=" * 100)
    print("开发侧目录体量（**不进成品**，只占开发盘/仓库）")
    print("=" * 100)
    rows = [
        dir_stat(os.path.join(UI, "PSV系统UI参考"), "PSV系统UI参考（参照集，非出货）"),
        dir_stat(os.path.join(UI, "生图入料"), "生图入料（AI 原始出图）"),
        dir_stat(os.path.join(UI, "_工作"), "_工作（中间产物/证据）"),
        dir_stat(os.path.join(UI, "用户临时文件区"), "用户临时文件区"),
        dir_stat(os.path.join(UI, "编辑器修改区"), "编辑器修改区"),
        dir_stat(os.path.join(UI, "_侦察"), "_侦察"),
        dir_stat(ASSFACE, "krkr/assets/face（头像库）"),
        dir_stat(ASSUI, "krkr/assets/ui（出货贴图库）"),
        dir_stat(GAME, "krkr/game（代码）"),
        dir_stat(REPL, "复刻（HTML 复刻 + 编辑器）"),
        dir_stat(os.path.join(UI, "layout"), "layout（布局数据源）"),
        dir_stat(TOOLS, "工具（生成器/闸门）"),
    ]
    print("\n| 目录 | 件数 | 体积 | 是否入库（git） |")
    print("| --- | ---: | ---: | --- |")
    for r in rows:
        rel = os.path.relpath(r["path"], REPO).replace("\\", "/")
        ign = is_ignored(rel + "/")
        tracked = subprocess.run(["git", "ls-files", rel], cwd=REPO,
                                 capture_output=True, text=True).stdout.strip()
        ntr = len(tracked.splitlines()) if tracked else 0
        state = "全部/部分忽略（%s）" % ign.split(":")[0] if ign else ("已入库 %d 件" % ntr)
        print("| %s | %d | %s | %s |" % (r["label"], r["files"], human(r["bytes"]), state))

    # ── 落盘证据（本目录，不入库）──────────────────────────────────────────
    out = []
    for f in universe:
        p = os.path.join(ASSUI, f)
        if f in used_ship:
            tier = "在用"
        elif f in only_tool:
            tier = "软闲置-脚本"
        elif f in only_doc:
            tier = "软闲置-文档"
        else:
            tier = "孤儿"
        out.append({"file": f, "tier": tier, "bytes": size_of(p),
                    "family": family(f),
                    "in_screen": f in scr_refs, "in_shipcode": f in ship_refs,
                    "in_toolcode": f in tool_refs, "in_doc": f in doc_refs})
    io.open(os.path.join(HERE, "闲置盘点.json"), "w", encoding="utf-8").write(
        json.dumps({"total": {"files": len(universe), "bytes": total_bytes},
                    "used_bytes": b_used, "soft_script_bytes": b_soft,
                    "soft_doc_bytes": b_doc, "orphan_bytes": b_orphan,
                    "items": out}, ensure_ascii=False, indent=1))
    with io.open(os.path.join(HERE, "闲置盘点.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("tier\tfamily\tbytes\tfile\tin_screen\tin_shipcode\tin_toolcode\tin_doc\n")
        for r in sorted(out, key=lambda x: (x["tier"] != "在用", -x["bytes"])):
            fh.write("%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n" % (
                r["tier"], r["family"], r["bytes"], r["file"], r["in_screen"],
                r["in_shipcode"], r["in_toolcode"], r["in_doc"]))
    print("\n证据已落：%s（闲置盘点.tsv / .json）" % HERE)
    print("⚠ 本脚本与产物属**顾问模式参考资料**，不入 main。")


if __name__ == "__main__":
    main()
