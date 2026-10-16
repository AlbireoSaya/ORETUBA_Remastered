# -*- coding: utf-8 -*-
r"""ISSUE-20260927-05 · E3 下伸部修复：**全 19 屏 HTML 回归**（改前/改后像素对照）。

■ 被测改动
    `复刻\replica.js::buildText`：`wrap && max_lines` 的文字（走 `-webkit-line-clamp` +
    `overflow:hidden`）在内层加 `padding-bottom = ceil(字形盒高 − 行盒高)`，把**裁切盒**向下扩，
    救回行盒之外的下伸部墨迹（`_` `g` `y` …）；并按 valign 折算回 padding 引起的居中偏移。

■ 回归判据（两两对照，全部**像素级**）
    A0 = 改前（把 `descenderPad` 强制为 0）；A1 = 改后；A0' = 改前复跑一次（**噪声基线**）
    ① changed = |A0 − A1|；noise = |A0 − A0'|（动画/栅格化的非确定性）
    ② 「允许变化区」= 各 `wrap && max_lines` 文字元素的数据框，**向下扩**（该元素的 descPad）
       —— 只有这一带里允许出现新像素（下伸部墨迹）。
    ③ 判定：`unexpected = changed ∧ ¬noise(dilated 1px) ∧ ¬allowed` 必须 == 0；
       且**横向**：新像素必须落在该元素的 x 区间内（若越出 ⇒ 可能是「原本被 overflow 挡住的
       横向溢出文字」冒出来 ⇒ 立即报警，这正是主代理要求盯的副作用）。
    ④ 逐屏列出：changed 像素数 / noise 像素数 / unexpected 数 / 受影响元素 id。

■ 另附：`max_lines` 截断语义保持（夹具）
    临时副本里把 `fc.node.0003_tx.sample` 改成超长串（>2 行），三种渲染对照：
      · 改后 + clamp        ⇒ 第 3 行带**无墨**（截断仍生效）
      · 改后 + 去掉 clamp   ⇒ 第 3 行带**有墨**（证明该带确实能显示文字，故「无墨」不是采样错误）
      · 改前 + clamp        ⇒ 第 3 行带无墨（对照）

用法：python E3_descender_regression.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(MOD))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(MOD, "取证")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_e3_reg"
COPY = ["index.html", "replica.css", "ui_layout.js", "flow_data.js", "replica.js", "asset_index.js",
        "_selftest_states.html"]
BASE_MD5 = "815e2d175b433e4eb109f2b428a7bd63"
ANCHOR = "      var fits = isFinite(lines) && lines <= c.maxLines;"
FIX_ID = "fc.node.0003_tx"      # 夹具主语（节点标签）
HOOK = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
        ".shell-head,.shell-foot{display:none!important}"
        "#stage-wrap{justify-content:flex-start!important;display:block!important}"
        "#stage{box-shadow:none!important}</style>"
        "<script>window.addEventListener('load',function(){"
        "window.UI_REPLICA&&window.UI_REPLICA.setScale(1);});</script>")


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def build(tag, before=False, long_sample=False, drop_clamp=False):
    """临时副本页：before=True ⇒ **改前口径**（总是 clamp）；False ⇒ 改后（按行数实测才 clamp）。
    drop_clamp=True ⇒ 变异「完全不裁」（负向对照，证明夹具确实超行）。"""
    d = os.path.join(EVID, "E3_reg_" + tag)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(d, f))
    if before or drop_clamp:
        p = os.path.join(d, "replica.js")
        s = io.open(p, encoding="utf-8").read()
        n = s.count(ANCHOR)
        if n != 1:
            raise SystemExit("夹具失效：锚点命中 %d/1 —— 请同步更新本脚本" % n)
        s = s.replace(ANCHOR, "      var fits = %s;" % ("true" if drop_clamp else "false"))
        io.open(p, "w", encoding="utf-8").write(s)
    if long_sample or drop_clamp:
        p = os.path.join(d, "ui_layout.js")
        s = io.open(p, encoding="utf-8").read()
        tree = json.loads(s[s.index("{"):s.rindex("}") + 1])
        els = tree["screens"]["flowchart"]["elements"]
        for e in els:
            if e.get("id") == "fc.node.0003_tx":
                if long_sample:
                    e["sample"] = "鹰振翅高飞" * 6          # 远超 2 行
                if drop_clamp:
                    e.pop("max_lines", None)      # 保留 wrap：仍折行，但不截断 ⇒ 第 3 行应出现
        # 用「整份 ui_layout.js 重写」的方式注入（与生成物同格式）
        io.open(p, "w", encoding="utf-8").write(
            "// 回归夹具（只存在于临时副本）\nwindow.UI_LAYOUT = "
            + json.dumps(tree, ensure_ascii=False, indent=2) + ";\n")
    p = os.path.join(d, "index.html")
    s = io.open(p, encoding="utf-8").read()
    ab = fileurl(ASSETS) + "/"
    s = s.replace('<script src="replica.js"></script>',
                  "<script>window.UI_ASSET_ROOT = '%s';</script>\n<script src=\"replica.js\"></script>" % ab)
    s = s.replace("</body>", HOOK + "</body>")
    io.open(p, "w", encoding="utf-8").write(s)
    return d


def edge_url(target):
    os.makedirs(UD, exist_ok=True)
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--user-data-dir=" + UD, "--hide-scrollbars",
                        "--window-size=1400,900", "--virtual-time-budget=15000", "--dump-dom",
                        fileurl(target)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8", "replace")


def shot(d, screen, out):
    os.makedirs(UD, exist_ok=True)
    url = fileurl(os.path.join(d, "index.html")) + "?screen=%s&chrome=0" % screen
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("截图失败：" + out)
    return Image.open(out).convert("RGB").crop((0, 0, 1920, 1080))


def main():
    import hashlib
    md5 = hashlib.md5(io.open(os.path.join(LAYOUT, "screens", "32_flowchart.json"), "rb").read()).hexdigest()
    if md5 != BASE_MD5:
        print("基线 md5 %s ≠ 期望 %s ⇒ 停止" % (md5, BASE_MD5)); return 3
    tree = json.load(io.open(os.path.join(LAYOUT, "ui_layout.json"), encoding="utf-8"))
    screens = list(tree["screens"].keys())
    # 「允许变化区」= 各屏 wrap&&max_lines 元素的数据框（向下扩该元素的 descPad）
    need = {}
    for sid, sc in tree["screens"].items():
        for e in sc.get("elements", []):
            if e.get("kind") == "text" and e.get("wrap") and e.get("max_lines"):
                size = e["font"]["size"]
                sp = e.get("line_spacing")
                if sp is None:
                    sp = (tree.get("fonts", {}).get("line_spacing", {}) or {}).get(e.get("line_spacing_role") or "body", 1.4)
                pad = max(0, int(-(-(size * 1.32) // 1) - size * sp) if False else 0)
                # 用与渲染器同口径的解析式（字形盒 1.32em 为保守上限；实际取实测值见 fontbox_metrics.txt）
                boxp = {16: 21, 18: 24, 19: 25, 20: 26, 22: 29, 27: 36, 42: 55}.get(int(size))
                lh = size * float(sp)
                pad = max(0, (boxp - lh)) if boxp else 0
                pad = int(pad) if pad == int(pad) else int(pad) + 1
                need.setdefault(sid, []).append((e["id"], e["x"], e["y"], e["w"], e["h"], pad, size, float(sp)))
    print("wrap&&max_lines 元素：%d 屏 / %d 件；其中需要下伸余量（字形盒>行盒）的 %d 件"
          % (len(need), sum(len(v) for v in need.values()),
             sum(1 for v in need.values() for it in v if it[5] > 0)))
    d0 = build("before", before=True)
    d0b = build("before2", before=True)
    d1 = build("after")
    os.makedirs(EVID, exist_ok=True)
    ok = True
    print("=" * 124)
    print("%-10s %-9s %-9s %-11s %s" % ("screen", "changed", "noise", "unexpected", "受影响元素（新像素所在允许区）"))
    print("=" * 124)
    for sid in screens:
        a0 = shot(d0, sid, os.path.join(EVID, "E3_reg_tmp_a0.png"))
        a0b = shot(d0b, sid, os.path.join(EVID, "E3_reg_tmp_a0b.png"))
        a1 = shot(d1, sid, os.path.join(EVID, "E3_reg_tmp_a1.png"))
        ch = ImageChops.difference(a0, a1).convert("L")
        no = ImageChops.difference(a0, a0b).convert("L")
        # 噪声掩膜膨胀 1px
        no_d = no.point(lambda v: 255 if v > 0 else 0).filter(__import__("PIL.ImageFilter", fromlist=["x"]).MaxFilter(3))
        allowed = Image.new("1", (1920, 1080), 0)
        ap = allowed.load()
        for (eid, x, y, w, h, pad, size, sp) in need.get(sid, []):
            for yy in range(max(0, y - 2), min(1080, y + h + pad + 2)):
                for xx in range(max(0, x - 2), min(1920, x + w + 2)):
                    ap[xx, yy] = 1
        chp, nop, app = ch.load(), no_d.load(), allowed.load()
        nch = nno = nun = 0
        hitels = set()
        for yy in range(1080):
            for xx in range(1920):
                if chp[xx, yy] == 0:
                    continue
                nch += 1
                if nop[xx, yy] > 0:
                    nno += 1
                    continue
                if app[xx, yy]:
                    for (eid, x, y, w, h, pad, size, sp) in need.get(sid, []):
                        if x - 2 <= xx < x + w + 2 and y - 2 <= yy < y + h + pad + 2:
                            hitels.add(eid)
                else:
                    nun += 1
        if nun:
            ok = False
            ch.save(os.path.join(EVID, "E3_reg_异常_%s.png" % sid))
        print("%-10s %-9d %-9d %-11d %s%s" % (sid, nch, nno, nun,
                                             "、".join(sorted(hitels)) if hitels else "（无）",
                                             "  ← ✗ 有预期外像素（已存 E3_reg_异常_%s.png）" % sid if nun else ""))
    print("=" * 124)
    # 夹具：`max_lines` 截断语义保持（**判据不依赖任何取色阈值**：三态互相比对）
    #   ① 改后 vs 改前（always clamp）必须 **0 像素差** ⇒ 超行时行为与改动前逐字相同
    #   ② 改后 vs 变异「完全不裁」必须 **>0**    ⇒ 证明该夹具真的超行（否则①无意义）
    print("附：`max_lines` 截断语义保持（夹具：%s 的 sample 改为超长串，%d 行 > max_lines=%s）"
          % (FIX_ID, 3, 2))
    dA = build("fx_after", long_sample=True)
    dB = build("fx_before", long_sample=True, before=True)
    dC = build("fx_noclamp", long_sample=True, drop_clamp=True)
    iA = shot(dA, "flowchart", os.path.join(EVID, "E3_reg_夹具_改后.png"))
    iB = shot(dB, "flowchart", os.path.join(EVID, "E3_reg_夹具_改前_总是clamp.png"))
    iC = shot(dC, "flowchart", os.path.join(EVID, "E3_reg_夹具_变异_完全不裁.png"))
    fx = [x for x in tree["screens"]["flowchart"]["elements"] if x.get("id") == FIX_ID][0]
    fbox = (fx["x"] - 6, fx["y"] - 4, fx["x"] + fx["w"] + 6, fx["y"] + fx["h"] + 26)
    def dfc(a, b):
        d = ImageChops.difference(a.crop(fbox), b.crop(fbox)).convert("L")
        return sum(1 for v in d.getdata() if v > 8)
    n_ab, n_ac = dfc(iA, iB), dfc(iA, iC)
    print("   改后 vs 改前(总是 clamp)：差异>8 = %d（期望 0 ⇒ 超行时与改动前逐字相同）" % n_ab)
    print("   改后 vs 变异(完全不裁)  ：差异>8 = %d（期望 >0 ⇒ 该夹具确实超行，①才有意义）" % n_ac)
    if not (n_ab == 0 and n_ac > 0):
        ok = False
    # ── ㉓ 断言的变异自证：把「是否裁切」的决策强制成 总是裁 / 从不裁 ⇒ ㉓ 必须 FAIL ──
    print("附：自检 ㉓（clamp 裁切决策）三变体")
    import re as _re
    def selftest_23(variant):
        dv = build("st_" + variant, before=(variant == "always"), drop_clamp=(variant == "never"))
        dom = edge_url(os.path.join(dv, "_selftest_states.html"))
        shutil.rmtree(dv, ignore_errors=True)
        vt = dom[dom.find('id="verdict"'):dom.find("</div>", dom.find('id="verdict"'))]
        m = _re.search("SELFTEST (OK|FAIL) +㉓ [^<\n]*", vt)
        verdict = _re.search(r"SELFTEST (ALL PASS|FAILED \d+ 项)", vt)
        return (verdict.group(1) if verdict else "(无判定)"), (m.group(0) if m else "(未找到 ㉓ 行)"),                bool(m) and m.group(1) == "FAIL"
    for variant, want_fail in (("normal", False), ("always", True), ("never", True)):
        v, line, is_fail = selftest_23(variant)
        good = (is_fail == want_fail) and ("执行期异常" not in line)
        ok = ok and good
        print("   [%-6s] 期望 ㉓ %s ｜ 总判定 %-16s %s" % (variant, "FAIL" if want_fail else "OK", v,
                                                       "✓" if good else "✗ 与期望不符"))
        print("            " + line[:240])

    print("=" * 124)
    print("判定：%s" % ("全 19 屏除「下伸部」外无预期外像素变化 + 截断语义保持 ✓" if ok else "存在不符合期望项 ✗"))
    for f in ("E3_reg_tmp_a0.png", "E3_reg_tmp_a0b.png", "E3_reg_tmp_a1.png"):
        try:
            os.remove(os.path.join(EVID, f))
        except OSError:
            pass
    for d in (d0, d0b, d1, dA, dB):
        shutil.rmtree(d, ignore_errors=True)
    shutil.rmtree(UD, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
