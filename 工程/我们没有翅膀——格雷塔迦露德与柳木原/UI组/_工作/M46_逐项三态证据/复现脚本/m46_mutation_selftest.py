# -*- coding: utf-8 -*-
r"""M46 · **变异自证**：两套自检必须抓得住两类「整条路径失效」的回归

一审（两位独立 reviewer）都用了「变异实验」——把一段机制**整条打废**，看自检是否报警。
本脚本把这两次实验固化成可复跑的机器判据（一审 Major-3 的收口）：

| 变体 | 怎么破坏 | 期望 |
| --- | --- | --- |
| B | 删掉 `ui_layout.js` 里 `ch.choices.item_frame.state_assets`（逐项态图整体消失） | 套 A **必须 FAIL** |
| C | 把 `replica.js` 元素级 `attachStateEvents` 的左键判定反过来（`ev.button !== 0` → `=== 0`） | 套 A **必须 FAIL** |

（C 的来历：M46 初版把 ①–⑤ 的被测元素从元素级迁到列表项，导致**元素级按下路径 0 条断言** ——
变异实验坐实「打废它套 A 仍 ALL PASS」。⑱ 段迁回元素级主语后，本条应恢复成 FAIL。）

■ 做法：把自检所需的 5 个文件复制到 `临时\m46_mutation\<变体>\`（**绝不改仓库文件**），
  在副本上做变异，再用无头 Edge 跑 `_selftest_states.html`，读 `SELFTEST` 判定行。
■ 用法：`python _工作\M46_逐项三态证据\复现脚本\m46_mutation_selftest.py`
"""
import io
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
REP = os.path.join(UI, "复刻")
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))
SCRATCH = os.path.join(WT, "临时", "m46_mutation")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

FILES = ["_selftest_states.html", "replica.js", "replica.css",
         "ui_layout.js", "screen_index.js", "asset_index.js"]


def stage(variant, mutate):
    d = os.path.join(SCRATCH, variant)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for f in FILES:
        src = os.path.join(REP, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(d, f))
    # 资产目录：ui_layout.js 里是相对路径 ../krkr/assets/… ⇒ 在副本同级放一个指向真身的软链不可靠，
    # 故直接复制需要的 ui/ 子目录（自检只读样式，不校验像素）。
    kill = os.path.join(d, "assets", "ui")
    os.makedirs(kill, exist_ok=True)
    src_ui = os.path.join(UI, "krkr", "assets", "ui")
    if os.path.isdir(src_ui):
        for f in os.listdir(src_ui)[:400]:
            if f.endswith(".png"):
                try:
                    shutil.copy2(os.path.join(src_ui, f), os.path.join(kill, f))
                except Exception:
                    pass
    # 让副本里的相对路径 ../krkr/assets/ui 生效：造一个 krkr/assets/ui 目录树
    tree = os.path.join(os.path.dirname(d), "krkr", "assets", "ui")
    os.makedirs(tree, exist_ok=True)
    if os.path.isdir(src_ui):
        for f in os.listdir(src_ui)[:400]:
            if f.endswith(".png"):
                try:
                    shutil.copy2(os.path.join(src_ui, f), os.path.join(tree, f))
                except Exception:
                    pass
    if mutate:
        mutate(d)
    return d


def verdict(d):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + os.path.join(SCRATCH, "_ud"),
           "--window-size=1400,900", "--hide-scrollbars",
           "--virtual-time-budget=12000", "--dump-dom",
           "file:///" + os.path.join(d, "_selftest_states.html").replace("\\", "/").replace(" ", "%20")]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    m = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", dom)
    n_fail = len(re.findall(r"SELFTEST FAIL ", dom))
    return (m.group(1) if m else "(未找到判定)"), n_fail


def m_drop_item_states(d):
    """变体 B：删掉 item_frame.state_assets（逐项态图整体消失）。"""
    p = os.path.join(d, "ui_layout.js")
    s = io.open(p, encoding="utf-8").read()
    n = s.count("state_assets")
    s2 = re.sub(r'"state_assets"\s*:\s*\{[^{}]*\}\s*,?', "", s, count=0)
    io.open(p, "w", encoding="utf-8", newline="").write(s2)
    print("   变体 B：ui_layout.js 里 state_assets 出现 %d 处 → 正则删除后 %d 处"
          % (n, s2.count("state_assets")))


def m_break_element_press(d):
    """变体 C：把元素级左键判定反过来（元素级按下路径整条打废）。"""
    p = os.path.join(d, "replica.js")
    s = io.open(p, encoding="utf-8").read()
    old = "if (ev.button !== 0) return;"
    assert s.count(old) >= 1, "找不到元素级的左键判定（attachStateEvents）"
    s = s.replace(old, "if (ev.button === 0) return;", 1)
    io.open(p, "w", encoding="utf-8", newline="\r\n").write(s)
    print("   变体 C：元素级 `ev.button !== 0` → `=== 0`（按下路径打废）")


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    fails = []
    for variant, mutate, want_fail in (("B_drop_item_states", m_drop_item_states, True),
                                       ("C_break_element_press", m_break_element_press, True),
                                       ("A_baseline", None, False)):
        print("── %s ──" % variant)
        d = stage(variant, mutate)
        v, n = verdict(d)
        got_fail = v.startswith("FAILED")
        ok = got_fail == want_fail
        print("   判定 = %s（FAIL 条数 %d）⇒ %s"
              % (v, n, "符合预期 ✓" if ok else "**不符合预期** ✗"))
        if not ok:
            fails.append(variant)
    print("结果：" + ("**全部符合预期**" if not fails else ("未通过 → " + "、".join(fails))))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
