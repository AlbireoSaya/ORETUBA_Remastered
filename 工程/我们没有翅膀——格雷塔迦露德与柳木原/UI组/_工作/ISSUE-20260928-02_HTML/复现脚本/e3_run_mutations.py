# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· ㉔ 断言的**变异自证**：把机制/数据逐条打废，㉔ 必须报警。

■ 目的
  「套 A = SELFTEST ALL PASS」只证明断言当前是绿的，**不证明它有牙齿**。
  本脚本按 `?e3=<mode>`（见 `复刻\_selftest_states.html` 的 E3MUT 段）逐个打废一条判据，
  断言**那一条**㉔ 必须 FAIL，且其余 ㉔ 仍 OK —— 「全绿可能只是没覆盖」由此排除。

■ 模式 → 期望报警的断言
  stale     切层只改 flag、不重画 canvas        ⇒ ㉔a
  noaction  抹掉**首个**入口热区的 action        ⇒ ㉔b
  noaction6 抹掉**最后一层**入口热区的 action    ⇒ ㉔b（前几层仍正常 ⇒ 只有扩到 6 层才抓得到）
  noback    最后一层返回热区打成永不显示        ⇒ ㉔f（按组返回键结构）
  badgeom   把 FLOW_RING.r 由 16 改成 4         ⇒ ㉔c
  noexist   元素 asset 改指不存在的文件          ⇒ ㉔d
  foldhover 删掉 state_assets.hover（回落常态）  ⇒ ㉔d
  stalehover 悬停后把态图还原成初态              ⇒ ㉔e
  nofromhit  导出的 flowLayerValues 摘掉夹具层   ⇒ ㉔g（来源③ 未实现）

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_run_mutations.py            # 全部模式 + 基线
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_run_mutations.py --json out.json
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)                       # …\ISSUE-20260928-02_HTML
UI = os.path.dirname(os.path.dirname(HTML_DIR))        # …\UI组
REP = os.path.join(UI, "复刻")
# ★ 盘面会被其它模块改写 ⇒ 默认在**私有快照栈**上跑（e3_snapshot_stack.py 建的）；
#   未设该环境变量时回落到盘面 复刻\（与官方 m39 同路径）。
SELFTEST_DIR = os.environ.get("E3_SELFTEST_DIR", REP)
sys.path.insert(0, HERE)
import e3_md5util as mu   # noqa: E402  （行尾健壮指纹：防『跑了陈旧副本』）
EVID = os.path.join(HTML_DIR, "证据")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3"

KEYS = ("㉔a", "㉔b", "㉔c", "㉔d", "㉔e", "㉔f", "㉔g")

MODES = [
    ("", "㉔a", "（基线：不打废任何东西）", None),
    ("stale", "㉔a", "切层只改 flag、不重画 canvas", "㉔a"),
    ("noaction", "㉔b", "抹掉首个入口热区的 action（点击不再派发）", "㉔b"),
    ("noaction6", "㉔b", "抹掉**最后一层**入口热区的 action（前几层仍正常）", "㉔b"),
    ("noback", "㉔f", "最后一层「返回主干」热区打成永不显示", "㉔f"),
    ("badgeom", "㉔c", "FLOW_RING.r 16 → 4", "㉔c"),
    ("noexist", "㉔d", "元素 asset 改指不存在的文件", "㉔d"),
    ("foldhover", "㉔d", "删掉 state_assets.hover（回落常态）", "㉔d"),
    ("stalehover", "㉔e", "悬停后把态图内联样式还原成初态（模拟修前的无组路径）", "㉔e"),
    ("nofromhit", "㉔g", "导出的 flowLayerValues 摘掉夹具层（＝模拟来源③ 未实现）", "㉔g"),
]


def url_of(path, query=""):
    return "file:///" + urllib.parse.quote(path.replace("\\", "/")) + query


def run_selftest(query, budget=15000):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1400,900", "--virtual-time-budget=%d" % budget, "--dump-dom",
           url_of(os.path.join(SELFTEST_DIR, "_selftest_states.html"), query)]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace")


def verdicts(dom):
    """逐条 ㉔ 判定（含 ㉔ 前缀的 OK/FAIL 行）。

    ★ 解析口径（2026-09-28 修）：`say()` 拼出的 OK 行是 `'SELFTEST OK   '`（**三个空格**），
    而 FAIL 行是 `'SELFTEST FAIL '`（一个空格）—— 旧正则 `SELFTEST (OK|FAIL) (㉔` 只吃一个空格，
    于是**只解析到 FAIL 行、OK 行全部漏读**（`out` 里根本没有 OK 键，`expect_key is not False`
    靠"没读到"侥幸通过，且基线打印出空表却看不出来）。这里改成 `[ \\t]*` 容忍任意空格。 """
    out = {}
    for m in re.finditer(r"SELFTEST (OK|FAIL)[ \t]+(㉔[a-z])", dom):
        out[m.group(2)] = (m.group(1) == "OK")
    allp = re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", dom)
    return out, (allp.group(1) if allp else "(未找到)")


def main():
    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    rows = []
    bad = []
    for mode, expect_key, why, filter_key in MODES:
        q = ("?e3=" + mode) if mode else ""
        dom = run_selftest(q)
        vs, allp = verdicts(dom)
        io.open(os.path.join(EVID, "E3_mut_%s_dump.html" % (mode or "baseline")),
                "w", encoding="utf-8").write(dom)
        row = {"mode": mode or "(baseline)", "expect_key": expect_key, "why": why,
               "verdicts": vs, "all": allp}
        rows.append(row)
        # 先验解析完整性：六个 ㉔ 断言都必须被读到（否则"没读到"会被误当"没报警"）
        missing = [k for k in KEYS if k not in vs]
        if missing:
            bad.append("%s：解析不到 %s（断言被改名/被吞，或解析正则与 say() 的空白不符）"
                       % (mode or "baseline", "、".join(missing)))
        if mode == "":
            if allp != "ALL PASS":
                bad.append("（基线）期望 ALL PASS，实得 " + allp)
            notok = [k for k in KEYS if vs.get(k) is not True]
            if notok:
                bad.append("（基线）期望 %s 全 OK，实得 %s"
                           % ("、".join(KEYS), "、".join("%s=%s" % (k, vs.get(k)) for k in notok)))
        else:
            if vs.get(expect_key) is not False:
                bad.append("%s：期望 %s FAIL，实得 %s" % (mode, expect_key, vs.get(expect_key)))
            # 其余 ㉔ 不应被这条变异连累（防"打废一处、四处报警"式的假覆盖）
            others = [k for k in KEYS if k != expect_key]
            leaked = [k for k in others if vs.get(k) is False]
            if leaked:
                bad.append("%s：只有 %s 应报警，但 %s 也 FAIL（变异不够定向）"
                           % (mode, expect_key, "、".join(leaked)))
        print("[%s] %s  ⇒ %s ｜ %s" % (
            (mode or "baseline").ljust(9), allp,
            " ".join("%s=%s" % (k, "OK" if v else "FAIL") for k, v in sorted(vs.items())),
            why))

    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        io.open(p, "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1))
        print("已写 " + p)

    # ── ★ 一审 P0-2：日志由**本脚本自己写**（此前那份 `E3_变异自证_日志.txt` 是旧版、只列 6 个模式）。
    #    模式数一律从 `MODES` 推导（不写死数字）；逐模式列出「目标断言 / 实际 FAIL 集合 / 其余是否仍 OK」。
    n_modes = len(MODES) - 1
    lg = ["E3 ㉔ 断言的变异自证（ISSUE-20260928-02 · HTML 侧）",
          "脚本：%s" % os.path.basename(__file__),
          "自检页：%s" % os.path.join(SELFTEST_DIR, "_selftest_states.html"),
          "★ 本次实际使用的自检页指纹（防陈旧副本）：%s"
          % mu.describe(os.path.join(SELFTEST_DIR, "_selftest_states.html"), label="自检页"),
          "模式数（从 MODES 推导，**不写死**）：非基线 %d 个；另有基线 1 个" % n_modes,
          "断言编号全集（从 KEYS 推导）：%s" % "、".join(KEYS),
          "判定口径：基线须 ALL PASS 且 %s 全 OK；每个非基线的目标断言须 FAIL、其余断言须全 OK（定向、不连累）" % "、".join(KEYS),
          ""]
    for row in rows:
        m = row["mode"]
        vs = row["verdicts"]
        fails = [k for k in KEYS if vs.get(k) is False]
        notok = [k for k in KEYS if vs.get(k) is not True]
        lg.append("─ 模式 %-10s ｜ %s" % (m, row["why"]))
        lg.append("   目标断言：%s" % ("（基线：不打废任何东西）" if m == "(baseline)" else row["expect_key"]))
        lg.append("   实际 FAIL 的断言集合：%s" % ("（空）" if not fails else "、".join(fails)))
        lg.append("   其余断言是否仍 OK：%s" % ("是（%s 全 OK）" % "、".join(KEYS) if not notok
                                          else "否（仍非 OK：%s）" % "、".join(notok)))
        lg.append("   汇总判定：%s ｜ 该模式是否符合期望：%s"
                  % (row["all"],
                     "符合 ✓" if (m == "(baseline)" and row["all"] == "ALL PASS" and not notok)
                     or (m != "(baseline)" and fails == [row["expect_key"]]) else "不符合 ✗"))
    lg += ["", "总体判定：%s" % ("全部通过：%d 个非基线模式各自精确打废其目标断言、其余断言不受连累；基线 ALL PASS"
                                % n_modes if not bad else "未通过：" + "；".join(bad))]
    io.open(os.path.join(EVID, "E3_变异自证_日志.txt"), "w", encoding="utf-8").write("\n".join(lg) + "\n")
    print("\n日志已写：%s（非基线 %d 个模式，逐模式列出目标/实际 FAIL 集合/其余是否 OK）"
          % (os.path.join(EVID, "E3_变异自证_日志.txt"), n_modes))

    shutil.rmtree(UD, ignore_errors=True)
    print("\n" + ("=" * 70))
    if bad:
        print("变异自证 **未通过**：")
        for b in bad:
            print("  ✗ " + b)
        return 1
    print("变异自证 **全部通过**：%d 个模式各自精确打废其目标断言，其余 ㉔ 不受连累；基线 ALL PASS" % n_modes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
