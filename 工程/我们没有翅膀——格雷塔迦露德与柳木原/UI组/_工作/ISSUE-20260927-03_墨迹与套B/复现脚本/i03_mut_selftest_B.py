# -*- coding: utf-8 -*-
r"""ISSUE-20260927-03 · 模块 I · ②「套 B 快捷条图标断言」的**负向对照**（内存/临时副本，不落盘生产数据）。

■ 为什么要有它（派单口径：**保持牙齿**）
  ② 把 `replica.js::runSelfTestChecks` 的图标断言由「写死素材名」改成「从数据推」。
  但「期望值从数据推」有一个**对称性风险**：数据本身指错时，期望与 DOM 会一起错，
  断言恒真 ⇒ 看起来全绿却什么都没验。故必须证明**改完之后仍能报警**。
  做法 = 把 `复刻\` 的宿主页复制到本证据目录，**在页面里注入一段内存改写**
  （改 `window.UI_LAYOUT.screens.quickbar` 的两枚图标），不碰任何生产文件；
  逐档跑 `?selftest=1&mut=<档>`，断言「该档必须 FAIL / 该档必须 PASS」。

■ 五个档（口径与 `_selftest_states.html` 的 `?mut=` 同源）
    none       不改（线上路径一字不改）                        ⇒ 期望 **PASS**（RESULT=OK）
    missing    `quick.ic_save.state_assets.hover` 改指**不存在的文件**
                                                            ⇒ 期望 **FAIL**（存在性锚点报警）
    foldhover  删掉 `quick.ic_save.state_assets.hover`（回落常态）
                                                            ⇒ 期望 **FAIL**（区分力锚点报警）
    rename     两枚图标的**全部**三态改指**另一组存在的**素材（合法改名）
                                                            ⇒ 期望 **PASS**（★ 这正是本修复的目的：
                                                               改名不再让套 B 由绿转红）
    ungroup    给 `quick.ic_save` 去掉 `state_group`（**打废组绑定机制**、数据仍合法）
                                                            ⇒ 期望 **FAIL**（行为断言报警 = 变异自证）

■ 另加一档「回归夹具」（证明本修复**确实**把 Major 遗留修掉了）
    legacy    把**临时副本**里的断言退回修前那三行**写死素材名**的比较（+ 修前的正则
              `nameOf`），数据同 `rename`（合法改名）
                                                            ⇒ 期望 **FAIL**（修前口径下改名即红，
                                                               与一审的 Major 判定一致）
              该档只改**临时副本**的 replica.js，生产文件一字未动。

■ 为什么要临时副本 / 注入而不是改 index.html
  模块 I 的写白名单只有 `krkr\game\ui_widget.tjs` / `复刻\replica.js` / `复刻\_selftest_states.html`
  —— **不给改 index.html**，而 `index.html` 又不加载 `asset_index.js`（本套 B 的清单靠
  `replica.js::ensureAssetIndex` 动态注入，见该函数注释）。

■ 用法
    python _工作\ISSUE-20260927-03_墨迹与套B\复现脚本\i03_mut_selftest_B.py
      → 五档逐跑，打印 RESULT 与两条相关断言的判词，并按上表判定 PASS/FAIL，退出码 0/1
"""
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)                       # …\ISSUE-20260927-03_墨迹与套B
UI = os.path.dirname(os.path.dirname(MOD))        # …\UI组
REP = os.path.join(UI, "复刻")
ASSETS = os.path.join(UI, "krkr", "assets")
TMP = os.path.join(MOD, "取证", "_muttmp")        # 临时副本（跑完删）
OUT = os.path.join(MOD, "取证", "负向对照_套B.txt")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_i03"

# 复制到临时副本的最小文件集（index.html 引用的那几件 + 素材清单）
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]

MUT_JS = r"""
<script>
/* ★ 负向对照专用钩子（**只存在于临时副本**，不进任何交付文件）
   ① 把素材根指回工作区真实 `krkr/assets/`（临时副本不在 复刻\ 下，相对路径会 404）；
   ② 按 `?mut=<档>` 在**渲染前**就地改写 quickbar 两枚图标的数据。 */
(function () {
  window.UI_ASSET_ROOT = '__ASSET_BASE__';
  var m = /(?:^|[?&])mut=([a-z]+)/.exec(location.search || '');
  var mode = m ? m[1] : '';
  if (!mode || mode === 'none') return;
  var L = window.UI_LAYOUT || {};
  var els = ((L.screens || {}).quickbar || {}).elements || [];
  function byId(id) { for (var i = 0; i < els.length; i++) if (els[i].id === id) return els[i]; return null; }
  var S = byId('quick.ic_save'), LO = byId('quick.ic_load');
  if (!S || !LO) return;
  if (mode === 'missing') {
    S.state_assets.hover = 'ui/__mut_no_such_asset__.png';
  } else if (mode === 'foldhover') {
    delete S.state_assets.hover;
  } else if (mode === 'rename') {
    /* 合法改名：两枚图标的 normal/hover 全部改指另一组**确实存在**的素材
       （借「回想」「流程图」两枚的图当替身 —— 名字与语义无关，只为证明「不认名字」）。 */
    S.state_assets = { normal: 'ui/x_ui_qbicon_log.png',    hover: 'ui/x_ui_qbicon_log_on.png' };
    LO.state_assets = { normal: 'ui/x_ui_qbicon_chart.png', hover: 'ui/x_ui_qbicon_chart_on.png' };
  } else if (mode === 'ungroup') {
    delete S.state_group;          /* 机制打废：悬停热区不再把悬停态广播给这枚图标 */
  }
})();
</script>
"""


# 「回归夹具」：把临时副本的断言退回修前的写死口径（仅临时副本）
LEGACY_NEW_NAMEOF = """      function nameOf(v) {
        var m = /url\\("?([^")]+)"?\\)/.exec(String(v));
        return m ? nameBase(decodeURIComponent(m[1])) : '';
      }"""
LEGACY_OLD_NAMEOF = ("      function nameOf(v) { var m = /x_ui_qbicon_[a-z_]+\\.png/"
                     ".exec(String(v)); return m ? m[0] : ''; }")
LEGACY_NEW_OKH = """      var okH = n2 === stS.normal && n3 === stL.normal
                && h2 === stS.hover && h3 === stL.normal
                && r2 === stS.normal;"""
LEGACY_OLD_OKH = """      var okH = n2 === 'x_ui_qbicon_save.png' && n3 === 'x_ui_qbicon_load.png'
                && h2 === 'x_ui_qbicon_save_on.png' && h3 === 'x_ui_qbicon_load.png'
                && r2 === 'x_ui_qbicon_save.png';"""


def build_tmp(legacy=False):
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(TMP, f))
    if legacy:
        rp = os.path.join(TMP, "replica.js")
        src = io.open(rp, encoding="utf-8").read()
        n1 = src.count(LEGACY_NEW_NAMEOF) + src.count(LEGACY_NEW_OKH)
        src = src.replace(LEGACY_NEW_NAMEOF, LEGACY_OLD_NAMEOF).replace(LEGACY_NEW_OKH, LEGACY_OLD_OKH)
        if n1 != 2:
            raise SystemExit("回归夹具：临时副本里待替换的修后代码没找到（命中 %d/2）—— 夹具失效，请同步更新" % n1)
        io.open(rp, "w", encoding="utf-8").write(src)
    page = io.open(os.path.join(TMP, "index.html"), encoding="utf-8").read()
    asset_base = "file:///" + urllib.parse.quote(ASSETS.replace("\\", "/")) + "/"
    hook = MUT_JS.replace("__ASSET_BASE__", asset_base)
    # 插在 ui_layout.js 之后、replica.js 之前 ⇒ 渲染与断言都看得到改写后的数据
    page = page.replace('<script src="replica.js"></script>',
                        hook + '\n<script src="replica.js"></script>')
    io.open(os.path.join(TMP, "index.html"), "w", encoding="utf-8").write(page)


def run(mode):
    os.makedirs(UD, exist_ok=True)
    url = ("file:///" + urllib.parse.quote(os.path.join(TMP, "index.html").replace("\\", "/"))
           + "?selftest=1&mut=" + mode)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1400,900", "--virtual-time-budget=30000", "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    res = re.search(r"RESULT=(\w+)", dom)
    lines = {}
    for ln in re.findall(r"(?:PASS|FAIL|SKIP)\t[^<\n]*", dom):
        parts = ln.split("\t")
        if len(parts) >= 2:
            lines[parts[1]] = (parts[0], parts[2] if len(parts) > 2 else "")
    return (res.group(1) if res else "(未找到 RESULT=)"), lines, r.returncode


# (数据改写档, 是否退回归夹具口径, 期望 RESULT, 说明)
EXPECT = [
    ("none",      False, "PASS", "线上路径一字不改：守护件与行为断言都必须全绿"),
    ("missing",   False, "FAIL", "素材存在性锚点：数据指向不存在的文件 ⇒ 必须报警"),
    ("foldhover", False, "FAIL", "区分力锚点：normal==hover（回落）⇒「换态图」断言恒真 ⇒ 必须报警"),
    ("rename",    False, "PASS", "★ 合法改名（改指另一组存在的素材）⇒ 必须仍然全绿 = 本修复的目的"),
    ("ungroup",   False, "FAIL", "变异自证：打废组绑定机制（数据仍合法）⇒ 行为断言必须报警"),
    ("rename",    True,  "FAIL", "回归夹具：退到修前「写死素材名」口径 + 合法改名 ⇒ 修前即红（一审 Major 判定复现）"),
]
GUARD = "flags.icon-hover-material-guard"
MAIN = "flags.icon-hover-material-via-group"


def main():
    rep = []
    ok_all = True
    rep.append("模块 I · ② 套 B 快捷条图标断言的负向对照（内存/临时副本改写，不落盘生产数据）")
    rep.append("临时副本：%s ｜ 断言两条：%s / %s" % (TMP, GUARD, MAIN))
    rep.append("=" * 100)
    for mode, legacy, want, why in EXPECT:
        build_tmp(legacy=legacy)
        res, lines, rc = run(mode)
        got = "PASS" if res == "OK" else ("FAIL" if res == "NG" else "?")
        g = lines.get(GUARD, ("(缺)", ""))
        m = lines.get(MAIN, ("(缺)", ""))
        good = (got == want)
        ok_all = ok_all and good
        rep.append("[%s] mut=%-9s%s 期望 %-4s → 实测 %-4s %s ｜ %s"
                   % ("OK " if good else "BAD", mode, " (legacy)" if legacy else "         ",
                      want, got, "✓" if good else "✗", why))
        rep.append("     guard %s —— %s" % (g[0], g[1][:190]))
        rep.append("     main  %s —— %s" % (m[0], m[1][:190]))
    rep.append("=" * 100)
    rep.append("结论：%s" % ("五档全部符合预期 ✓" if ok_all else "存在不符预期的档 ✗"))
    text = "\n".join(rep)
    print(text)
    io.open(OUT, "w", encoding="utf-8").write(text + "\n")
    shutil.rmtree(UD, ignore_errors=True)
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n（临时副本与无头 Edge 的 user-data-dir 已清理；证据落盘：%s）" % OUT)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
