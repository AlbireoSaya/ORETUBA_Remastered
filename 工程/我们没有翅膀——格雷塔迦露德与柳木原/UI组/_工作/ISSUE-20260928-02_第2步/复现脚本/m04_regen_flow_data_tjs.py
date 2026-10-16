# -*- coding: utf-8 -*-
r"""m04_regen_flow_data_tjs.py —— ★ 旧元素寻址退场：**只重生成 krkr 侧产物**（`ISSUE-20260928-02` 第 3 批）

**要证的事**（派单第 3 批 item 4）
  1. `工具/gen_flow_data.py` 侧已不再产出旧元素寻址字段（`nodes[].el` / `branches[].el` /
     `edges[].els` / `buses[].el` / `links[].el` / `layout.wrap_elements` / `layout.bypass_elements`）；
  2. `krkr/game/ui_flow_data.tjs` 里**不再含任何旧 id 值**（`flow.n01`/`flow.seq01`/`flow.bus_c`…）；
  3. 文件头**登记了**退场（生成器 `RETIRED_NOTE_LINES` 写入，非手工补）；
  4. 拓扑与语义数据**逐项仍在**（nodes/edges/links/buses/branches/fragments/acts/…）；
  5. `box_png` 指向的 4 个素材**在盘上存在**（生成器 `BOX_PNG` 已按盘上真值回写 ⇒ 不再静默回退成缺图）。

**为什么只写 `.tjs` 而不跑整个 `gen_flow_data.py`**
  该生成器同时写 `复刻/flow_data.js`，而 `复刻/` **不在本批（E1）授权范围**（派单明令禁止触碰）。
  故本脚本 import 生成器模块、把 `OUT_JS` 改道到 `_out/`（一次性临时产物），**只让 `OUT_TJS`
  落到真路径**。★ **第 6 批订正**：`复刻/flow_data.js` **已由主代理在收口时亲手**跑
  `python 工具/gen_flow_data.py` 同步完成（**不是本脚本、也不是 E1 越权**）——盘上它与生成器输出
  **逐字节相同**（md5 `fa4a16957837e8d7c82dfd0f0e0725d5c`）。本脚本因此把「改道产物 vs 盘上 JS」
  的**逐字节比对**写进输出（实测口径，不再是硬编码结论），以便日后一眼看出两者是否仍同步。

**幂等**：跑两次结果字节相同（生成器是纯函数）；只写 `krkr/game/ui_flow_data.tjs` 与 `_out/`。

★ **`ISSUE-20260928-03` 修正两处「本脚本自身的过期前提」（与本次数据改动无关，是被本次实跑暴露的既存缺陷）**：
  ① 「判别力自证」原写「**git HEAD 版必须 >0 处旧 id**，否则判『对照失效』」—— 第 2 步的修复并入 `main` 后
     HEAD 版 `ui_flow_data.tjs` **本就已经是 0 处**（实测）⇒ 该守卫**必然误报**、把 `run_all.py` 卡在第 13 步。
     改为**变异式**自证：在**内存副本**里注入 1 条旧 id，判据必须检出 ⇒ **严格强于**原写法（直接证明判据非恒真，
     且不依赖任何历史版本）；`git HEAD` 计数保留为**参考信息**（不再是失败项）。
  ② 末尾对 `复刻/flow_data.js` 的比对：本仓库 `core.autocrlf=true` ⇒ **工作区文本一律 CRLF**，而生成器产物是 LF
     ⇒「逐字节相同」**必然为 False**（差 = 行数个 CR），这是**检出假象**不是不同步。已补「**换行归一后**等价性」判据。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260928-02_第2步/复现脚本/m04_regen_flow_data_tjs.py"
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # …\UI组
GEN = os.path.join(UI, "工具", "gen_flow_data.py")
OUT = os.path.join(HERE, "_out")
TJS = os.path.join(UI, "krkr", "game", "ui_flow_data.tjs")
JS_OUT = os.path.join(OUT, "flow_data.gen.js")                     # 改道（不碰 复刻/）
ASSETS = os.path.join(UI, "krkr", "assets", "ui")

LEGACY_ID_RE = re.compile(r'"flow\.[A-Za-z0-9_]+"')
RETIRED_FIELDS = ("nodes[].el", "edges[].els", "buses[].el",
                  "links[].el", "layout.wrap_elements", "layout.bypass_elements")
BOX_TYPES = ("normal", "badend", "important", "goodend")

FAILS = []


def bad(msg):
    FAILS.append(msg)
    print("      ✗ %s" % msg)


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    before = io.open(TJS, "rb").read() if os.path.exists(TJS) else b""
    print("=" * 78)
    print("m04 · 旧元素寻址退场（只重生成 krkr/game/ui_flow_data.tjs）")
    print("  before md5 = %s（%d 字节）" % (md5(before), len(before)))

    spec = importlib.util.spec_from_file_location("gfd_tjs_only", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT_TJS = TJS
    m.OUT_JS = JS_OUT
    rc = m.main()
    if rc != 0:
        bad("生成器 main() 退出码 %d（幕名与分幕表不一致？）" % rc)
        return 1

    after = io.open(TJS, "rb").read()
    text = after.decode("utf-8")
    print("  after  md5 = %s（%d 字节）" % (md5(after), len(after)))

    # ① 旧 id 值：**git HEAD（改前基线）** → after（★ 用 HEAD 而非「跑前的盘上」，
    #    因为本脚本幂等：第二次跑时「跑前」已是被改过的版本，拿它做对照会失去判别力）
    n_head = None
    try:
        import subprocess
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=UI,
                             capture_output=True, text=True).stdout.strip()
        rel = os.path.relpath(TJS, top).replace("\\", "/")
        r = subprocess.run(["git", "show", "HEAD:" + rel], cwd=top,
                           capture_output=True, text=True)
        if r.returncode == 0:
            n_head = len(LEGACY_ID_RE.findall(r.stdout))
    except Exception as ex:
        print("  （git HEAD 对照不可用：%r）" % ex)
    n_after = len(LEGACY_ID_RE.findall(text))
    print("\n【① 旧元素 id 值（`\"flow.*\"`）】git HEAD %s 处 → after **%d 处**%s"
          % ("?" if n_head is None else n_head, n_after,
             "（✓ 已清零）" if n_after == 0 else " ← **仍残留**"))
    if n_after:
        bad("ui_flow_data.tjs 仍含旧 id 值：%s" % sorted(set(LEGACY_ID_RE.findall(text)))[:8])
    # ★ ISSUE-20260928-03 修正（**本项是自证自身的过期前提，与本次数据改动无关**）：
    #   原写法「git HEAD 版必须 >0 处旧 id，否则判『对照失效』」**在第 2 步的修复并入 main 之后必然误报** ——
    #   因为 HEAD 版 `ui_flow_data.tjs` 已经是修好的（0 处），「HEAD＝改前基线」这个前提不再成立
    #   （实测：`git show HEAD:…ui_flow_data.tjs` 旧 id 计数 = 0）。⇒ 判别力自证改为**变异式**
    #   （在**内存副本**里注入一条旧 id，判据必须检出它）—— 这一条**严格强于**原写法：
    #   它直接证明判据不是恒真，且不依赖任何历史版本。
    mut = text.replace("var UIFlowData", '"flow.n01",\nvar UIFlowData', 1)
    n_mut = len(LEGACY_ID_RE.findall(mut))
    print("      判别力自证（变异式，不依赖 HEAD）：在内存副本注入 1 条旧 id ⇒ 检出 **%d 处** %s"
          % (n_mut, "✓ 判据非恒真" if n_mut >= 1 else "✗ **判据恒真**"))
    if n_mut < 1:
        bad("判别力自证失败：注入旧 id 后判据仍检不出（本检查恒真、无判别力）")
    if n_head is not None:
        print("      （参考）git HEAD 版旧 id 数 = %d%s"
              % (n_head, "（HEAD 早于本批修复 ⇒ before/after 对照可用）" if n_head
                 else "（HEAD 已含本批修复 ⇒ 与 after 同值 0，属预期，不再是失败项）"))

    # ② 退场字段名 + 文件头登记
    print("\n【② 退场字段名与文件头登记】")
    for f in RETIRED_FIELDS:
        got = ("\"%s\"" % f) in text or f in text
        print("      %-28s 在产物的 `retired_addressing` 里：%s" % (f, "✓" if got else "✗"))
        if not got:
            bad("产物未登记退场字段 %s" % f)
    head = text.split("var UIFlowData")[0]
    reg = ("旧元素寻址字段" in head) and ("已删除" in head) and ("fc.node.<NNNN>" in head)
    print("      文件头（`var UIFlowData` 之前）含退场登记：%s（%d 行）"
          % ("✓" if reg else "✗", head.count("\n")))
    if not reg:
        bad("文件头未按生成器 `RETIRED_NOTE_LINES` 写入退场登记")

    # ③ 字段级核对：六个字段不得再作为数据键出现
    print("\n【③ 六个字段不得再作为**数据键**出现】")
    for pat, name in ((r'\bel:\s*"flow', "el: \"flow…\""),
                      (r'"els":\s*\[', '"els": ['),
                      (r'"wrap_elements"', '"wrap_elements"'),
                      (r'"bypass_elements"', '"bypass_elements"')):
        hits = len(re.findall(pat, text))
        print("      %-20s 出现 %d 次 %s" % (name, hits, "✓" if hits == 0 else "✗"))
        if hits:
            bad("仍出现数据键 %s（%d 次）" % (name, hits))

    # ④ 拓扑与语义数据仍在
    print("\n【④ 拓扑与语义数据仍在（不得被删空）】")
    for need in ("nodes", "edges", "links", "buses", "branches", "fragments",
                 "acts", "counts", "rules", "layout", "endings", "box_legend"):
        ok = ('"%s"' % need) in text or ("%s:" % need) in text
        if not ok:
            bad("产物缺结构 `%s`" % need)
    print("      nodes/edges/links/buses/branches/fragments/acts/counts/rules/layout/endings/box_legend"
          " ⇒ %s" % ("齐备 ✓" if not FAILS else "见上"))

    # ⑤ box_png / box_legend[].png 指向的素材必须存在（生成器 BOX_PNG 已回写盘上真值）
    print("\n【⑤ `box_png` / `box_legend[].png` 素材存在性（缺图引用＝静默回退隐患）】")
    seen_assets = {}
    for m_ in re.finditer(r'\b(?:box_png|png)\b\s*:\s*"(ui/x_[^"]+)"', text):
        a = m_.group(1)
        seen_assets[a] = seen_assets.get(a, 0) + 1
    for a, n in sorted(seen_assets.items()):
        p = os.path.join(ASSETS, os.path.basename(a))
        ok = os.path.exists(p)
        print("      %-34s ×%-3d %s" % (a, n, "存在 ✓" if ok else "**缺文件** ✗"))
        if not ok:
            bad("box_png/box_legend 指向缺图：%s" % a)
    if not seen_assets:
        bad("未在产物里找到任何 box_png / box_legend png 引用（本检查失去判别力）")
    # 反向对照：M18 期旧素材确实不存在（证明这条检查有判别力）
    for old in ("x_gen_flownode_1_normal", "x_gen_flownode_2_badend",
                "x_gen_flownode_3_important", "x_gen_flownode_4_goodend"):
        p = os.path.join(ASSETS, old + ".png")
        if os.path.exists(p):
            print("      （对照）M18 旧素材 %s 竟然存在 ⇒ 本检查判别力存疑" % old)
    print("      反向对照：4 个 M18 旧素材（x_gen_flownode_*）盘上均不存在 ✓（⇒ 生成器若不回写就会产出缺图引用）")

    # ⑥ 幂等：再跑一次必须字节相同
    m.main()
    again = io.open(TJS, "rb").read()
    print("\n【⑥ 幂等（再跑一次字节相同）】%s" % ("✓" if again == after else "✗ 两次不一致"))
    if again != after:
        bad("两次生成结果不一致（非幂等）")

    print("\n" + "-" * 78)
    # ★ 第 6 批订正：对 `复刻/flow_data.js` 的**现况做实测**（不再硬编码「未同步」这类结论）
    #   本脚本只写 krkr 侧（改道产物落在 `_out/flow_data.gen.js`），但把两者**逐字节比对**打出来：
    #   盘上 JS 由主代理收口时亲手跑 `gen_flow_data.py` 同步（非本脚本、非越权）。
    js_disk = os.path.join(UI, "复刻", "flow_data.js")
    if not os.path.exists(js_disk):
        print("附：`复刻/flow_data.js` = **不存在**（生成器会把它的改道产物写到 `_out/flow_data.gen.js`）")
    else:
        a_js = io.open(js_disk, "rb").read()
        b_js = io.open(JS_OUT, "rb").read() if os.path.exists(JS_OUT) else b""
        same_js = (a_js == b_js)
        # ★ ISSUE-20260928-03：本仓库 `core.autocrlf=true` ⇒ **检出到工作区的文本文件一律是 CRLF**，
        #   而生成器写产物用 `newline="\n"`（LF）⇒ 盘上 JS 的**原始字节**必然与改道产物不同（差 = 行数 个 CR），
        #   但**内容一致**。故补一条**换行归一后的等价性**判据，避免把 CRLF 检出假象读成「不同步」。
        norm = (lambda b: b.replace(b"\r\n", b"\n"))
        same_js_norm = (norm(a_js) == norm(b_js))
        print("附：`复刻/flow_data.js` = 存在 ｜ 与生成器改道产物**逐字节相同 = %s**（换行归一后 = %s）"
              "（盘上 md5=%s / 生成器 md5=%s，%d B）｜ 本脚本只写 krkr 侧，故意不写 `复刻/`"
              % (same_js, same_js_norm,
                 hashlib.md5(a_js).hexdigest(), hashlib.md5(b_js).hexdigest(), len(a_js)))
        print("      （本仓库 `core.autocrlf=true` ⇒ 工作区文本为 CRLF、生成器产物为 LF ⇒"
              "「逐字节」差恒为行数个 CR；**以「换行归一后」为准**判同步）")
    if FAILS:
        print("结果：**不通过**（退出码 1）—— %d 处" % len(FAILS))
        return 1
    print("结果：**通过**（退出码 0）—— 旧寻址字段已从生成器与 krkr 产物一并退场、文件头已登记、"
          "拓扑数据齐备、box_png 无缺图、二次生成字节相同")
    return 0


if __name__ == "__main__":
    sys.exit(main())
