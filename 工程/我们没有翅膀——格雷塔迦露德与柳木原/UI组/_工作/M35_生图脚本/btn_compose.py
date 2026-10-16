# -*- coding: utf-8 -*-
r"""按钮文字成品合成：**独立羽毛层（下） + 正文字层（上）**。

用户 2026-09-22：「羽毛单独生成一层，放在字体下方」。

■ 几何（严格照用户算式）
  正文层：每个汉字字身 = 48×48，字间距 = 4px
          → 正文层画布 = (48n + 4(n-1)) × 48
            4 字 = 204×48 ｜ 3 字 = 152×48 ｜ 2 字 = 100×48
  羽毛层：画布 = 正文层 + 四周 PAD 留白（(48n+4(n-1)+2·PAD) × (48+2·PAD)）
          —— 48 高的画布里字身几乎占满，羽毛若与正文同画布会被完全遮住，
             故羽毛层必须比正文层大一圈，留白处才看得见羽毛（实测 8× 目视确认）。
          羽毛取自 `FEATHER_sheet.png` 切出的独立精灵，缩放后散落，alpha 峰值压低。
  合成层：羽毛在下、正文在正中 (PAD, PAD)。

■ 羽毛精灵的切取
  `FEATHER_sheet.png` 上约 23 根互不相邻的羽毛 → alpha>40 的八连通域 → 逐根取 bbox。
"""
import os, sys
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import btn_slice2 as B

OUT = os.path.join(HERE, "out_btn")
CH, GAP = 48, 4
PAD = 24                      # 羽毛层四周留白
FEATHER_MAX_H = 0.80          # 单根羽毛高度上限（占画布高的比例）
FEATHER_PEAK = 150            # 羽毛层 alpha 峰值（0-255）
WORDS = B.WORDS


# ───────────────────────────── 羽毛精灵 ─────────────────────────────

def label_components(mask):
    """八连通标记 → 每块的 bbox（纯 python + numpy，数据量小够用）。"""
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys.tolist(), xs.tolist()):
        if seen[sy, sx]:
            continue
        stack = [(sy, sx)]
        seen[sy, sx] = True
        mnx = mxx = sx; mny = mxy = sy; n = 0
        while stack:
            cy, cx = stack.pop(); n += 1
            if cx < mnx: mnx = cx
            elif cx > mxx: mxx = cx
            if cy < mny: mny = cy
            elif cy > mxy: mxy = cy
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        out.append((mnx, mny, mxx, mxy, n))
    return out


_SPRITES = None


def feather_sprites(path=None):
    global _SPRITES
    if _SPRITES is not None and path is None:
        return _SPRITES
    path = path or os.path.join(OUT, "FEATHER_sheet.png")
    rgba = Image.open(path).convert("RGBA")
    al = np.array(rgba)[..., 3]
    comps = label_components(al > 40)
    sprites = []
    for (x0, y0, x1, y1, n) in comps:
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if w < 28 or h < 28 or n < 220:
            continue
        sprites.append((rgba.crop((x0, y0, x1 + 1, y1 + 1)), (w, h), n))
    sprites.sort(key=lambda s: -max(s[1]))
    if path is None:
        _SPRITES = sprites
    return sprites


def scaled_feather(spr, max_h, alpha_scale):
    im = spr[0]
    w, h = im.size
    k = min(max_h / float(h), max_h / float(w))
    nw, nh = max(1, int(round(w * k))), max(1, int(round(h * k)))
    im = im.resize((nw, nh), Image.LANCZOS)
    r, g, b, a = im.split()
    a = a.point(lambda v: int(v * alpha_scale))
    return Image.merge("RGBA", (r, g, b, a))


def feather_layer(W, H, wkey, density=0.0, seed_extra=0):
    """按词名确定性铺羽毛（同一词多次运行结果一致）。"""
    import zlib
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if density <= 0:
        return lay
    sprites = feather_sprites()
    if not sprites:
        return lay
    rnd = zlib.crc32(("%s|%d" % (wkey, seed_extra)).encode("utf-8"))
    n_feather = max(1, int(round(density * W / 96.0)))
    for i in range(n_feather):
        rnd = (1103515245 * rnd + 12345) & 0x7fffffff
        s = sprites[(rnd >> 7) % len(sprites)]
        rnd = (1103515245 * rnd + 12345) & 0x7fffffff
        fx = (rnd >> 7) % 1000 / 1000.0
        rnd = (1103515245 * rnd + 12345) & 0x7fffffff
        fy = (rnd >> 7) % 1000 / 1000.0
        rnd = (1103515245 * rnd + 12345) & 0x7fffffff
        sc = 0.62 + ((rnd >> 7) % 1000) / 1000.0 * 0.38
        im = scaled_feather(s, H * FEATHER_MAX_H * sc, FEATHER_PEAK / 255.0)
        x = int(round(fx * (W - im.width)))
        y = int(round(fy * (H - im.height)))
        lay.alpha_composite(im, (x, y))
    return lay


# ───────────────────────────── 逐词组包 ─────────────────────────────

def build_word(cells, zh, wkey, density, pad=PAD, seed_extra=0):
    """返回 (正文层 W×48, 独立羽毛层 (W+2p)×(48+2p), 合成层 (W+2p)×(48+2p))。"""
    n = len(zh)
    W, H = CH * n + GAP * (n - 1), CH
    bare = B.compose_word(cells, zh)
    PW, PH = W + 2 * pad, H + 2 * pad
    fl = feather_layer(PW, PH, wkey, density, seed_extra)
    comp = fl.copy()
    comp.alpha_composite(bare, (pad, pad))
    return bare, fl, comp


def run(batch, density, dest, tag):
    src = os.path.join(OUT, "BATCH%s_7rows.png" % batch)
    res, diag = B.slice_sheet(src)
    if res is None:
        print("切分失败：%s" % batch)
        for d in diag:
            print(d)
        return None
    print("=" * 78)
    print("批次 %s ｜ 羽毛密度 %.2f ｜ 落盘 %s" % (batch, density, dest))
    os.makedirs(dest, exist_ok=True)
    man = []
    for zh, wkey in WORDS:
        cells = res.get(zh)
        if not cells or any(c is None for c in cells):
            print("  ✗ %s 缺格" % zh); continue
        bare, fl, comp = build_word(cells, zh, wkey, density)
        bare.save(os.path.join(dest, "%s_%s.png" % (tag, wkey)))
        fl.save(os.path.join(dest, "%sf_%s.png" % (tag, wkey)))
        comp.save(os.path.join(dest, "%sc_%s.png" % (tag, wkey)))
        man.append((zh, wkey, bare.size, comp.size))
        print("  %-5s 正文 %s ｜ 羽毛层/合成 %s" % (zh, bare.size, comp.size))
    return man


if __name__ == "__main__":
    stage = os.path.join(HERE, "_btn_stage")
    os.makedirs(stage, exist_ok=True)
    sp = feather_sprites()
    print("羽毛精灵 %d 根，尺寸 %s …" % (len(sp), [s[1] for s in sp[:6]]))
    m2 = run("2", 1.1, stage, "x_ui_btntxt2")
    m3 = run("3", 1.1, stage, "x_ui_btntxt3")

    # 4× 预览（衬 110,120,132 中灰），只画合成层
    K = 4
    for tag, batch in (("batch2", "2"), ("batch3", "3")):
        rows = []
        for zh, wkey, bs, cs in (m2 if batch == "2" else m3) or []:
            p = os.path.join(stage, "x_ui_btntxt%sc_%s.png" % (batch, wkey))
            im = Image.open(p).convert("RGBA")
            bg = Image.new("RGBA", im.size, (110, 120, 132, 255)); bg.alpha_composite(im)
            rows.append(bg.convert("RGB").resize((im.width * K, im.height * K), Image.NEAREST))
        if not rows:
            continue
        Wc = max(r.width for r in rows) + 16
        Hc = sum(r.height for r in rows) + 8 * (len(rows) + 1)
        cv = Image.new("RGB", (Wc, Hc), (110, 120, 132))
        y = 8
        for r in rows:
            cv.paste(r, (8, y)); y += r.height + 8
        cv.save(os.path.join(HERE, "_证据", "FINAL_%s_4x.png" % tag))
        print("预览 → _证据/FINAL_%s_4x.png" % tag)
