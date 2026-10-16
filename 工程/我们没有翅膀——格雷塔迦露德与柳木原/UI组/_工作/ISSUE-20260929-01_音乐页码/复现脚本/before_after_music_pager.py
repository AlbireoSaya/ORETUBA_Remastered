# -*- coding: utf-8 -*-
r"""before_after_music_pager.py —— 音乐页码行「改前 y939 / 改后 y964」的**同渲染器对照**

做法：在 `verify_music_pager.py` 建好的临时栈上，把 `ui_layout.js` 里这 7 个元素的 `y`
**临时改回改前值**（视觉 939 / 热区 931）渲一帧，再与新值帧比：
  · 墨迹纵向范围与中心（应整体 +25）
  · 墨迹色（改前 `mu.pg_tx_1` 已是 #4A4A56；2/3 为 #E8E8F0 —— 本脚本顺便读取**旧栈**的三页色作对照）
只读数据 + 只改临时栈（不碰工作区）。
"""
import io
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
EVID = os.path.join(ISSUE, "证据")
TMP = os.path.join(EVID, "_stack")
UD = r"E:/ZCode Workspace/Galgame/临时/edge_music29_before"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BOX = (858, 964, 204, 56)
OLD = {"mu.pg_tx_1": 939, "mu.pg_tx_2": 939, "mu.pg_tx_3": 939,
       "mu.pg_prev": 939, "mu.pg_next": 939,
       "mu.pg_prev_hit": 931, "mu.pg_next_hit": 931}


def fileurl(p):
    p = os.path.abspath(p).replace("\\", "/")
    return "file:///" + (p[0].lower() + p[1:] if p[1:2] == ":" else p)


def patch_color_back():
    """再把 `mu.pg_tx_2/3` 的色改回**解析后的旧值** `#E8E8F0`（临时栈里是已解析的十六进制，
    故必须写 hex：写 `@palette.text_menu` 令牌不合产物原貌）。"""
    p = os.path.join(TMP, "ui_layout.js")
    t = io.open(p, encoding="utf-8", newline="").read()
    n = 0
    for eid in ("mu.pg_tx_2", "mu.pg_tx_3"):
        i = t.find('"id": "%s"' % eid); assert i > 0, eid
        j = t.find('"color": "#4A4A56"', i); assert j > 0, eid
        t = t[:j] + '"color": "#E8E8F0"' + t[j + len('"color": "#4A4A56"'):]
        n += 1
    io.open(p, "w", encoding="utf-8", newline="").write(t)
    print("  临时栈已把 tx_2/tx_3 色改回旧值 #E8E8F0：%d 件" % n)


def patch_layout_back():
    """把临时栈的 ui_layout.js 里这 7 件的 y 改回旧值（仅临时栈）。"""
    p = os.path.join(TMP, "ui_layout.js")
    t = io.open(p, encoding="utf-8", newline="").read()
    n = 0
    for eid, y in OLD.items():
        # 定位该元素对象：`"id": "<eid>"` 之后最近的 `"y": <num>`
        i = t.find('"id": "%s"' % eid)
        assert i > 0, eid
        m = re.search(r'"y":\s*(\d+)', t[i:])
        assert m, eid
        assert int(m.group(1)) == (964 if "_hit" not in eid else 956), (eid, m.group(1))
        t = t[:i + m.start(1)] + str(y) + t[i + m.end(1):]
        n += 1
    io.open(p, "w", encoding="utf-8", newline="").write(t)
    print("  临时栈已改回旧 y：%d 件" % n)


def shot(tag, page):
    out = os.path.join(EVID, "对照_%s_page%d.png" % (tag, page))
    url = fileurl(os.path.join(TMP, "index.html")) + "?screen=music&chrome=0&flags=music_page:%d" % page
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    im = Image.open(out).convert("RGB")
    if im.width >= 1920 and im.height >= 1080:
        im = im.crop((0, 0, 1920, 1080)); im.save(out)
    return out


def ink_rows(png, band=(900, 1060)):
    r"""墨迹行范围。**两级判据**：
    ① 深墨（lum<150）—— 新配色（#4A4A56）适用；
    ② 退化为「与霜板基准色的偏差 > 6」—— 旧配色（#E8E8F0 近白）**在深墨判据下无像素**（正是它不可读的原因），
       此时用与底板的微小偏差定位，避免 `min()` 空序列报错。"""
    a = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
    x, _, w, _ = BOX
    seg = a[band[0]:band[1], x:x + w]
    lum = 0.299 * seg[:, :, 0] + 0.587 * seg[:, :, 1] + 0.114 * seg[:, :, 2]
    rows = [i + band[0] for i in range(seg.shape[0]) if (lum[i] < 150).sum() > 3]
    if rows:
        return min(rows), max(rows), "深墨"
    # 退化判据：只认**核心字身**（对底板偏差 > 40 ⇒ 近白 #E8E8F0 对霜板 (252,252,252) 的 |Δ|₁ = 52 能命中；
    # 浅蓝雪花装饰 ≈20 被排除）；观测带避开板上方深色区（band 收到 930..1035）
    seg2 = a[930:1035, x:x + w]
    plate = np.median(seg2.reshape(-1, 3), axis=0)
    dev = np.abs(seg2 - plate).sum(axis=2)
    rows = [i + 930 for i in range(seg2.shape[0]) if (dev[i] > 40).sum() > 3]
    # ★ 如实：近白字在像素上**本就难以定位**（正是它不可读的原因）。若「命中行数」多得不合理
    #   （> 40 行 ⇒ 混进了雪花/板边，不是一行字），则**不报位置**，只报「不可测」——
    #   页 2/3 的 +25 由「数据 diff（三件同几何、同 y）+ 页 1 实测 + 新配色下三页落点一致」共同支撑。
    if rows and (max(rows) - min(rows)) <= 40:
        return min(rows), max(rows), "近白(核心字身偏差>40)"
    return None, None, "不可测（近白·像素级难定位）"


def ink_color(png):
    a = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
    x, y, w, h = BOX
    box = a[y - 30:y + h + 30, x:x + w].reshape(-1, 3)
    lum = 0.299 * box[:, 0] + 0.587 * box[:, 1] + 0.114 * box[:, 2]
    sel = box[lum < 150]
    return tuple(int(v) for v in np.median(sel, axis=0)) if len(sel) else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # ★ 先**从仓库重建**临时栈（保证幂等：上一次运行可能已把栈改成旧值 ⇒ 直接回退会撞断言）
    import importlib.util
    spec = importlib.util.spec_from_file_location("vmp", os.path.join(HERE, "verify_music_pager.py"))
    vmp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vmp)
    print("  从仓库重建临时栈…")
    vmp.build()
    old_color = "--old-color" in sys.argv
    patch_layout_back()
    if old_color:
        patch_color_back()
    print("改前（y939/931%s）：" % ("，且 tx_2/3 用旧色 #E8E8F0" if old_color else "，色仍为改后值"))
    before_rows = {}
    for pg in (1, 2, 3):
        p = shot("改前色" if old_color else "改前", pg)
        r0, r1, how = ink_rows(p)
        before_rows[pg] = (r0, r1)
        print("  page%d 墨迹 y=%s..%s（中心 %s）｜ 判据=%s ｜ 色 %s"
              % (pg, r0, r1, ("%.1f" % ((r0 + r1) / 2)) if r0 else "-", how, ink_color(p)))
    print("改后（y964/956，来自 verify 的帧）：")
    for pg in (1, 2, 3):
        p = os.path.join(EVID, "复刻_music_page%d.png" % pg)
        r0, r1, how = ink_rows(p)
        if r0 and before_rows[pg][0]:
            d = ((r0 + r1) / 2) - ((before_rows[pg][0] + before_rows[pg][1]) / 2)
            note = "✓ 恰 +25" if abs(d - 25) <= 1 else "✗"
        else:
            d, note = float("nan"), "（一侧未测到）"
        print("  page%d 墨迹 y=%s..%s（中心 %s）｜ 判据=%s ｜ 色 %s ｜ 中心位移 %s ⇒ %s"
              % (pg, r0, r1, ("%.1f" % ((r0 + r1) / 2)) if r0 else "-", how, ink_color(p),
                 ("%+.1f px" % d) if d == d else "-", note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
