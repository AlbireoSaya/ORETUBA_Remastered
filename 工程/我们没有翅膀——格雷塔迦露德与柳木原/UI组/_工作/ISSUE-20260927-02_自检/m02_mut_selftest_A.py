# -*- coding: utf-8 -*-
r"""ISSUE-20260927-02 · 负向对照夹具：带 `?mut=<mode>` 跑 `复刻\_selftest_states.html`

■ 为什么需要它
  修好规则 ⑱（期望图名从 ui_layout.js 的数据推）之后，**必须证明断言仍有牙齿** ——
  否则「改了数据也跟着改期望值」会退化成恒真的空断言。`_selftest_states.html` 内置了
  负向对照开关 `?mut=`（默认空 = 线上路径一字不改，见文件内 MUT 处注释），本脚本负责驱动它。

■ 模式与**期望结果**（--expect 用于自动判定）
    （无）       线上路径                                    ⇒ SELFTEST ALL PASS
    missing     state_assets.normal 指向**不存在的素材**      ⇒ FAIL（⑱ 数据侧存在性守卫）
    foldhover   删掉 state_assets.hover（回落常态）           ⇒ FAIL（⑱ 数据侧区分力守卫）
    swap        对调 hover / normal                          ⇒ ALL PASS（**合法重映射**：
                36_choices.json 的 note 明写「若日后判定"粉＝常态、蓝紫＝悬停"，只改本字段三者映射即可」）
    drift       **渲染之后**再改数据（DOM 与数据脱钩）         ⇒ FAIL（比较类断言：期望≠实际）
    expect      期望值退回**修前那组写死的素材名**             ⇒ FAIL 10 项（复现修前的套 A 恒 FAIL）

■ 用法
    python _工作\ISSUE-20260927-02_自检\m02_mut_selftest_A.py            # 跑全部模式并判定
    python _工作\ISSUE-20260927-02_自检\m02_mut_selftest_A.py --only expect
"""
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))                       # …\UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_selftest_mut"

MODES = ["missing", "foldhover", "swap", "drift", "expect"]
EXPECT_VERDICT = {          # True = 必须 FAIL（断言有牙齿）；False = 必须 ALL PASS（合法数据变更）
    "missing": True,
    "foldhover": True,
    "swap": False,
    "drift": True,
    "expect": True,
}


def verdict_text(dom):
    """只取 #verdict 节点内的判定文本 —— 否则会把 <script> 源码里的
    `SELFTEST FAIL ...` 字样当成断言结果（本文件正文确实含这些字面量）。"""
    i = dom.find('id="verdict"')
    if i < 0:
        return ""
    j = dom.find("</div>", i)
    return dom[i:j if j > 0 else i + 200000]


def run(mode):
    out = os.path.join(HERE, "mut_%s_dump.html" % (mode or "none"))
    q = ("?mut=" + mode) if mode else ""
    url = "file:///" + urllib.parse.quote(os.path.join(REP, "_selftest_states.html").replace("\\", "/")) + q
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1400,900", "--virtual-time-budget=15000", "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    io.open(out, "w", encoding="utf-8").write(dom)
    vt = verdict_text(dom)
    m = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", vt)
    note = re.search(r"SELFTEST NOTE [^<\n]*", vt)
    fails = re.findall(r"SELFTEST FAIL [^<\n]*", vt)
    return {"dom": dom, "verdict": (m.group(1) if m else "(未找到判定)"),
            "note": (note.group(0).strip() if note else "(无 NOTE)"),
            "fails": fails, "out": out, "rc": r.returncode}


def main():
    only = ""
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].lower()
    os.makedirs(UD, exist_ok=True)
    plan = [""] + (MODES if not only else [m for m in MODES if m == only])
    ok_all = True
    for mode in plan:
        res = run(mode)
        want_fail = EXPECT_VERDICT.get(mode)
        if want_fail is None:                       # 线上路径
            good = res["verdict"] == "ALL PASS"
            want_txt = "ALL PASS"
        else:
            good = (res["verdict"] != "ALL PASS") if want_fail else (res["verdict"] == "ALL PASS")
            want_txt = ("必须 FAIL" if want_fail else "必须 ALL PASS（合法数据变更）")
        print("=" * 78)
        print("[%s] 期望：%s" % (mode or "(无 · 线上路径)", want_txt))
        print("  NOTE   ：%s" % res["note"])
        for f in res["fails"][:12]:
            print("  " + f)
        if len(res["fails"]) > 12:
            print("  … 另有 %d 条 FAIL" % (len(res["fails"]) - 12))
        print("  判定：%s ｜ edge rc=%d ｜ dump=%s ｜ 结果=%s"
              % (res["verdict"], res["rc"], res["out"], "符合期望 ✓" if good else "与期望不符 ✗"))
        if not good:
            ok_all = False
    shutil.rmtree(UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % UD)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
