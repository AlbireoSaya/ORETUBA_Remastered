# -*- coding: utf-8 -*-
r"""ISSUE-20260927-03 · 模块 I · HTML 复刻端「标签墨迹」1:1 取图（改前 / 改后各一套）。

■ 取哪三屏
    backlog   任务 ① 的主战场（`bl.list` 的 `item_buttons[].label`，4 块）
    ending    `ed.hit_skip`（hit.label，h64 / 字号 26）—— 核对 hit.label 同族同病一并处理的结果
    fragment  `fragment.hit_back`（hit.label，h58 / 字号 30）—— 同上

■ 「改前」怎么来的（**不碰生产文件**）
    若把当前 `复刻\` 复制到临时目录、把本模块在 `replica.js` 里的 **2 处 `+3` 改回去**
    （`translateY(3 - X)` → `if (X) translateY(-X)`，即修前的「只做半行距补偿」），
    就得到一字不差的**修前口径**渲染。替换命中数不是 2 ⇒ 直接报错（夹具失效不得静默）。

■ 为什么用临时副本而不是直接截 `复刻\index.html`
    ① 需要「隐藏页面外壳 + `setScale(1)`」才能让截图左上 1920×1080 就是画布本体；
    ② 需要把素材根指回真实 `krkr\assets\`；
    两者都要往页面里注入钩子 ⇒ 只能在副本里做（模块 I 的写白名单不含 index.html）。

■ ★ 坑（本轮实测，通用）：**无头 Edge 的视口 ≠ `--window-size`**
    `--window-size=W,H` 得到的视口是 **`(W−24) × (H−93)`**（实测 1920×1080 ⇒ 视口 1896×987）。
    截图文件仍是 W×H，但**视口之外不绘制**——即 1080 画布的最下 93px / 最右 24px 会是被抠掉的
    空白（`elementsFromPoint` 在那里返回空数组）。只量 y≲987 的元素时看不出来，
    **量 y≥990 的元素（本模块的 `ed.hit_skip` y990 / `fragment.hit_back` y944）会误判成「没画」**。
    故本脚本用 `--window-size=1944,1180`（⇒ 视口 1920×1087 ≥ 1080）。

■ 用法
    python _工作\ISSUE-20260927-03_墨迹与套B\复现脚本\i03_html_shots.py
      → 写 `取证\改前\i03_html_<屏>_改前.png` / `取证\改后\i03_html_<屏>_改后.png`，打印文件大小与路径
"""
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(MOD))
REP = os.path.join(UI, "复刻")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(MOD, "取证")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_i03"

COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js"]
SHOTS = [("backlog", "?screen=backlog"), ("ending", "?screen=ending"), ("fragment", "?screen=fragment")]

# 本模块在 replica.js 里的两处「+3」——修前口径 = 退回下式（半行距补偿，无 +3）
NEW_BTN = "            bl.style.transform = 'translateY(' + px(3 - blHL) + ')';"
OLD_BTN = "            if (blHL) bl.style.transform = 'translateY(' + px(-blHL) + ')';"
NEW_HIT = "      lab.style.transform = 'translateY(' + px(3 - labHL) + ')';"
OLD_HIT = "      if (labHL) lab.style.transform = 'translateY(' + px(-labHL) + ')';"

# 素材根**必须在 replica.js 之前**注入：ASSET_BASE 是 replica.js 装载时读的
#   （`window.UI_ASSET_ROOT || …`），放在 </body> 会晚一步 —— 实测那样**全部素材变缺件**
#   （画面变暗底 + 缺件红框），本轮就栽过（见文件头「坑」）。
ASSET_HOOK = '<script>window.UI_ASSET_ROOT = \'__ASSET_BASE__\';</script>\n'

HOOK = """
<script>
/* 取图专用钩子（**只存在于临时副本**）：隐藏页面外壳 + 强制 1:1 */
(function () {
  var st = document.createElement('style');
  st.textContent = '.shell{max-width:none!important;padding:0!important;margin:0!important}'
    + '.shell-head,.shell-foot{display:none!important}'
    + '#stage-wrap{justify-content:flex-start!important;display:block!important}'
    + '#stage{box-shadow:none!important}';
  document.head.appendChild(st);
  window.addEventListener('load', function () {
    if (window.UI_REPLICA && window.UI_REPLICA.setScale) window.UI_REPLICA.setScale(1);
  });
})();
</script>
"""


def build(dst, before):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    if before:
        rp = os.path.join(dst, "replica.js")
        src = io.open(rp, encoding="utf-8").read()
        n = src.count(NEW_BTN) + src.count(NEW_HIT)
        if n != 2:
            raise SystemExit("修前夹具失效：待替换的 `+3` 命中 %d/2 —— 请同步更新本脚本" % n)
        src = src.replace(NEW_BTN, OLD_BTN).replace(NEW_HIT, OLD_HIT)
        io.open(rp, "w", encoding="utf-8").write(src)
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    asset_base = "file:///" + urllib.parse.quote(ASSETS.replace("\\", "/")) + "/"
    page = page.replace('<script src="replica.js"></script>',
                        ASSET_HOOK.replace("__ASSET_BASE__", asset_base)
                        + '<script src="replica.js"></script>')
    if asset_base not in page:
        raise SystemExit("素材根未注入（index.html 里没找到 replica.js 的 script 标签）——夹具失效")
    page = page.replace("</body>", HOOK.replace("__ASSET_BASE__", asset_base) + "\n</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)


def shot(page, query, out_png):
    """截 1:1 画布 + 同时取 DOM：**取图夹具自证** —— DOM 里若有「缺件 / ui-missing / 未知 kind」
    就说明本页的素材根没接对（会静默改变画面底色的那种），必须当场报错而不是拿它量数。"""
    os.makedirs(UD, exist_ok=True)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    url = ("file:///" + urllib.parse.quote(page.replace("\\", "/")) + query)
    # 视口 = (W−24) × (H−93)；用 1944×1180 ⇒ 视口 1920×1087，完整覆盖 1920×1080 画布（见文件头注）
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
           "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out_png),
           "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    # ⚠ 判据只能用**占位节点的类名**：index.html 的说明文本本身就含「缺件」二字
    #   （实测第一版按「缺件」判 ⇒ 每次都假报夹具失败）；`ui-missing` 这个类名只出现在
    #   replica.js 的 DOM 里，页面自带文本不含它。
    miss = sorted(set(re.findall(r"缺件：([^\s<]+)", dom)))
    bad = ["ui-missing-label"] if "ui-missing-label" in dom else []
    return os.path.exists(out_png), bad, miss


def main():
    ok = True
    for tag, before in (("改前", True), ("改后", False)):
        dst = os.path.join(EVID, "_htmlshot_%s" % ("before" if before else "after"))
        build(dst, before)
        page = os.path.join(dst, "index.html")
        for name, q in SHOTS:
            out = os.path.join(EVID, tag, "i03_html_%s_%s.png" % (name, tag))
            got, bad, miss = shot(page, q, out)
            ok = ok and got and not bad
            extra = ("" if not bad else "  ⚠ 夹具自证失败：DOM 含 " + "/".join(bad))
            if miss:
                extra += "  ｜ 本页缺件 %d 件：%s" % (len(miss), "、".join(miss[:4]))
            print("[%s] %-9s %-18s -> %s（%d 字节）%s"
                  % ("OK " if (got and not bad) else "BAD", name, q, out,
                     os.path.getsize(out) if got else 0, extra))
    shutil.rmtree(UD, ignore_errors=True)
    print("\n临时副本保留于 %s（供复核；可随时删除）" % os.path.join(EVID, "_htmlshot_*"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
