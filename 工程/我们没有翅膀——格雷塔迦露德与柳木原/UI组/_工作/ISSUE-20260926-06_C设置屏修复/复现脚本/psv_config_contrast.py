# -*- coding: utf-8 -*-
r"""psv_config_contrast.py —— 25 设置屏「文字/底 对比度」离线审计（无 GUI、无巡演）

**为什么需要本脚本**（缺陷 ④ 的量化依据，不是目视结论）：
  PSV 换皮后，面板底从「深色面板」换成了 **PSV 浅色霜板**（实测 L≈223），而本屏绝大多数
  文字仍沿用 M47 时代的 `@palette.text_menu`（#E8E8F0，L≈232）—— 那是给**深色底**配的浅字。
  浅字压浅底 ⇒ 对比度 ≈1.0，观感即「洗白的残影」。本脚本对**每一条 text 元素**：
    ① 按 z 序把「该文字之下的全部可见 image」合成出**它的真实底**；
    ② 在文字框内取底的**分位数亮度**（默认 p10/p50/p90，覆盖「浅板压雪花白装饰」这类
       底不匀的情形 —— 判据取**最不利**的那个分位）；
    ③ 与文字色算 **WCAG 2.x 相对亮度对比度**（含 font.size 判定 large = ≥24px 或 ≥18.66px bold）。
  输出：低于阈值的清单 + 每条的建议（换哪个 palette 键）。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python _工作\ISSUE-20260926-06_C设置屏修复\复现脚本\psv_config_contrast.py [--min 4.5]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCREEN = os.path.join(UI, "layout", "screens", "25_config.json")
PALETTE = os.path.join(UI, "layout", "palette.json")
ASSETS = os.path.join(UI, "krkr", "assets")


def load():
    doc = json.load(open(SCREEN, encoding="utf-8"))
    pal = json.load(open(PALETTE, encoding="utf-8"))["colors"]
    return doc, {k: v["value"] for k, v in pal.items()}


def color_of(ref, pal):
    if isinstance(ref, str) and ref.startswith("@palette."):
        return pal.get(ref.split(".", 1)[1])
    return ref


def hex_rgb(v):
    v = str(v).lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def rel_lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [f(float(x)) for x in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def asset_path(a):
    a = str(a).strip().replace("\\", "/")
    return os.path.join(ASSETS, a if "/" in a else ("ui/" + a))


def nine_resize(im, w, h, n):
    l, t, r, b = n["l"], n["t"], n["r"], n["b"]
    if l == t == r == b == 0:
        return im.resize((max(1, w), max(1, h)), Image.LANCZOS)
    sw, sh = im.size
    mw, mh = max(1, sw - l - r), max(1, sh - t - b)
    cw, ch = max(1, w - l - r), max(1, h - t - b)
    out = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    out.paste(im.crop((l, t, sw - r, sh - b)).resize((cw, ch), Image.LANCZOS), (l, t))
    for (x0, y0, x1, y1, dx, dy) in [(0, 0, l, t, 0, 0), (sw - r, 0, sw, t, w - r, 0),
                                     (0, sh - b, l, sh, 0, h - b),
                                     (sw - r, sh - b, sw, sh, w - r, h - b)]:
        if x1 > x0 and y1 > y0 and dx < w and dy < h:
            out.paste(im.crop((x0, y0, x1, y1)), (dx, dy))
    if t > 0 and cw > 0:
        out.paste(im.crop((l, 0, sw - r, t)).resize((cw, t), Image.LANCZOS), (l, 0))
    if b > 0 and cw > 0:
        out.paste(im.crop((l, sh - b, sw - r, sh)).resize((cw, b), Image.LANCZOS), (l, h - b))
    if l > 0 and ch > 0:
        out.paste(im.crop((0, t, l, sh - b)).resize((l, ch), Image.LANCZOS), (0, t))
    if r > 0 and ch > 0:
        out.paste(im.crop((sw - r, t, sw, sh - b)).resize((r, ch), Image.LANCZOS), (w - r, t))
    return out


def visible(e, flags):
    if e.get("visible_default") is False:
        return False
    vf, vw = e.get("vis_flag"), e.get("vis_when")
    if not vf:
        return True
    cur = flags.get(vf, "")
    return (cur != "") if vw == "*" else (cur == vw)


def key_pages(doc):
    kp = {}
    for e in doc["elements"]:
        eid = e["id"]
        if eid.startswith("cfg.o_") and eid.endswith("_on_hit"):
            kp[eid[len("cfg.o_"):-len("_on_hit")]] = e.get("vis_when", "")
    kp["vchar"] = "snd"
    return kp


def flags_for_page(doc, kp, page):
    f = {"cfg_page": page}
    for k, v in doc["flags_default"].items():
        if k.startswith("cfg_v_"):
            pg = kp.get(k[len("cfg_v_"):])
            f[k] = v if pg == page else ""
    f["cfg_vchar"] = "asu" if page == "snd" else ""
    return f


def base_stack(doc, flags, zmax, cache):
    """把 z < zmax 的可见 image 合成到画布（纯图底，不含文字、不含与文字同 z 及更高者）。

    ★ z 序口径：引擎按 z 升序绘制 ⇒ 文字的「底」= 严格 z 更小的图。同 z 的图与文字
      按声明序绘制，属数据自证项（本屏同 z 重叠已登记），不进底口径。"""
    canvas = Image.new("RGBA", (1920, 1080), (28, 30, 38, 255))
    els = sorted([e for e in doc["elements"] if visible(e, flags) and e.get("z", 0) < zmax],
                 key=lambda e: e.get("z", 0))
    for e in els:
        if e["kind"] not in ("image", "hit", "slider") or not e.get("asset"):
            continue
        p = asset_path(e["asset"])
        if not os.path.isfile(p):
            continue
        key = (p, e["w"], e["h"], json.dumps(e.get("nine"), sort_keys=True))
        if key in cache:
            im = cache[key]
        else:
            im = Image.open(p).convert("RGBA")
            if e.get("nine"):
                im = nine_resize(im, e["w"], e["h"], e["nine"])
            elif im.size != (e["w"], e["h"]):
                im = im.resize((e["w"], e["h"]), Image.LANCZOS)
            cache[key] = im
        if e.get("opacity", 255) < 255:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: v * e["opacity"] // 255))
        canvas.alpha_composite(im, (e["x"], e["y"]))
    return np.asarray(canvas.convert("RGB")).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=4.5, help="普通字最小对比度（large 字按 3.0）")
    args = ap.parse_args()
    doc, pal = load()
    kp = key_pages(doc)
    cache = {}
    rows = []
    for page in ("sys", "snd"):
        flags = flags_for_page(doc, kp, page)
        stack = base_stack(doc, flags, 30, cache)
        for e in doc["elements"]:
            if e["kind"] != "text" or not visible(e, flags):
                continue
            x, y, w, h = e["x"], e["y"], e["w"], e["h"]
            x0, y0 = max(0, x), max(0, y)
            x1, y1 = min(1920, x + w), min(1080, y + h)
            if x1 <= x0 or y1 <= y0:
                continue
            patch = stack[y0:y1, x0:x1].reshape(-1, 3)
            L = patch.mean(axis=1)
            f = e.get("font", {})
            size = int(f.get("size", 24))
            large = size >= 24 or (size >= 18.66 and f.get("bold"))
            need = 3.0 if large else args.min
            col = color_of(f.get("color", "#FFFFFF"), pal)
            if col is None:
                continue
            rgb = hex_rgb(col)
            # ★ 判据底 = **框内亮度中位数**（字形只占框内少数像素 ⇒ 中位数 ≈ 字形所在处的底），
            #   p10/p90 一并打印，用于识别「底不匀（压雪花白装饰）」的混合底 —— 混合底另按
            #   **最不利分位**复算一次，两者取小（保守），避免把「半张框压白装饰」判成达标。
            med = float(np.median(L))
            p10, p90 = float(np.percentile(L, 10)), float(np.percentile(L, 90))
            fg_l = rel_lum(rgb)
            worst = p90 if fg_l > rel_lum((med,) * 3) else p10
            bg_rgb = tuple(float(v) for v in np.percentile(patch, 50, axis=0))
            bg_worst = tuple(float(v) for v in
                             np.percentile(patch, 90 if fg_l > rel_lum((med,) * 3) else 10, axis=0))
            c_med = contrast(rgb, bg_rgb)
            c_worst = contrast(rgb, bg_worst)
            cr = min(c_med, c_worst)
            rows.append((page, e["id"], e.get("sample", "").split("\n")[0][:14], col, size, large,
                         round(med, 0), round(p10, 0), round(p90, 0), round(c_med, 2), round(c_worst, 2),
                         round(cr, 2), need, "OK" if cr >= need else "FAIL"))
    rows.sort(key=lambda r: (r[13] != "FAIL", r[11]))
    print("=" * 150)
    print("25 设置屏 · 文字压底对比度审计（WCAG 2.x ｜ large = size>=24 或 >=18.66+bold ⇒ 门槛 3.0，否则 %.1f）" % args.min)
    print("判据 = min(中位底对比度, 最不利分位对比度)；p10/p90 用于识别「底不匀」")
    print("=" * 150)
    print("%-4s %-30s %-15s %-22s %-4s %-5s %5s %5s %5s %7s %7s %7s %5s %s"
          % ("页", "元素", "样文", "色", "字号", "large", "底中位", "底p10", "底p90",
             "中位比", "最差比", "取用", "门槛", "判定"))
    nf = 0
    for r in rows:
        if r[13] == "FAIL":
            nf += 1
            print("%-4s %-30s %-15s %-22s %-4s %-5s %5.0f %5.0f %5.0f %7.2f %7.2f %7.2f %5.1f %s"
                  % (r[0], r[1], r[2], r[3], r[4], "是" if r[5] else "否", r[6], r[7], r[8],
                     r[9], r[10], r[11], r[12], r[13]))
    print("-" * 150)
    print("文字元素 %d 条 ｜ 不达标 %d 条（仅打印不达标）" % (len(rows), nf))
    return 0


if __name__ == "__main__":
    sys.exit(main())
