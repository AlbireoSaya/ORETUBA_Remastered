# -*- coding: utf-8 -*-
r"""ISSUE-20260926-02 · PSV bg_config_01/02 去字（程序化补底路）v3

v3 修订（依据 corners_zoom.png 4× 实测）：
 · 保护：雪带/CONFIG、页面左右留白（大雪花）、右上角跨界雪花、面板四角盒（由边框矩形反推）、
   线条保护（横向长游程＝面板边框 ±3 / 滑槽 ±9 以保住两端箭头；纵向 ≥300＝左右边框）；
 · 章节标签（基本設定/サウンド設定）压在面板上边框上 → 标签区**无视线条保护**整字擦除，
   填充后按两侧干净段的边框核心行**横向插值补画边框**；
 · 右下三钮为浅色发光字 → 按钮区阈值单独放宽（bg-12）；
 · 药丸条：行投影阈值 0.5（抗相邻药丸软边粘连），切出 8/6 个药丸壳；
 · 滑槽裁件：按行带分组（间隙≤4 合并）自动定位，从去字后页面裁出。
输出/证据路径同 v2；全部实测矩形写 manifest（RECTS_JSON）。
"""
import os, sys, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\outpaint\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC  = os.path.join(BASE, "PSV系统UI参考")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-02_PSVconfig去字")
EV   = os.path.join(WORK, "_证据"); os.makedirs(EV, exist_ok=True)
OUT1 = os.path.join(BASE, "PSV系统UI参考", "去字件", "1x"); os.makedirs(OUT1, exist_ok=True)

CFG = {
 "otv_bg_config_01.png": {
   "label_zone": (68, 91, 198, 122),      # 基本設定（压上边框，需补线）
   "value_zones": [(420, 96, 880, 390)],  # 右侧数值词区（放宽阈值）
   "btn_zone":   (552, 470, 958, 542),    # 右下三钮（浅色发光字，阈值放宽）
   "extra_protect": [(850, 93, 960, 152)],# 右上角跨界雪花
 },
 "otv_bg_config_02.png": {
   "label_zone": (76, 91, 215, 128),      # サウンド設定
   "value_zones": [(500, 280, 770, 350)],
   "btn_zone":   (552, 470, 958, 542),
   "extra_protect": [(850, 90, 960, 152)],
 },
}
BASE_PROTECT = [(0, 0, 960, 93), (0, 93, 62, 545), (903, 93, 960, 545)]
DARK_TH, LIGHT_TH, DILATE, ITERS = 22, 25, 7, 800
PILL_XMAX = 340                # 药丸列右界（雪碧条内）
H_BORDER, H_GROOVE, V_LINE = 600, 250, 300

def local_bg(lum, f=8):
    w, h = lum.size
    small = lum.resize((max(1, w//f), max(1, h//f)), Image.BOX).filter(ImageFilter.MedianFilter(5))
    return np.asarray(small.resize((w, h), Image.BILINEAR), dtype=np.float32)

def box_blur(a, r=4):
    pad = np.pad(a, ((r+1, r), (0, 0), (0, 0)), mode="edge")
    c = np.cumsum(pad, axis=0); a = (c[2*r+1:] - c[:-2*r-1]) / (2*r+1)
    pad = np.pad(a, ((0, 0), (r+1, r), (0, 0)), mode="edge")
    c = np.cumsum(pad, axis=1); return (c[:, 2*r+1:] - c[:, :-2*r-1]) / (2*r+1)

def harmonic_fill(arr, mask, iters=ITERS):
    out = arr.copy(); out[mask] = box_blur(out)[mask]
    for _ in range(iters):
        out[mask] = box_blur(out)[mask]
    return out

def runs(bool_1d, min_len):
    idx = np.flatnonzero(bool_1d)
    if len(idx) == 0: return []
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    return [(int(g[0]), int(g[-1])) for g in groups if g[-1] - g[0] + 1 >= min_len]

def in_rects(shape, rects):
    m = np.zeros(shape, dtype=bool)
    for x0, y0, x1, y1 in rects: m[y0:y1, x0:x1] = True
    return m

def border_repair(page, zone, border_rows):
    """标签区内被擦断的面板上边框：按核心行两侧干净段横向插值补画"""
    x0, y0, x1, y1 = zone
    for r in border_rows:
        if not (y0 <= r < y1): continue
        left  = page[r, max(0, x0-14):x0].mean(axis=0)
        right = page[r, x1:x1+14].mean(axis=0) if x1+14 < page.shape[1] else page[r, x1-6:x1].mean(axis=0)
        n = x1 - x0
        t = np.linspace(0, 1, n)[:, None]
        page[r, x0:x1] = left[None, :] * (1 - t) + right[None, :] * t

def process(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    W, H = im.size
    a = np.asarray(im).astype(np.float32)
    op = (a[:, :, 3] > 8).mean(axis=1)
    page_end = int(np.where(op > 0.9)[0].max()) + 1
    page, strip = a[:page_end].copy(), a[page_end:]
    tag = name.replace("otv_bg_config_", "bgc").replace(".png", "")
    cfg = CFG[name]

    lum = page[:, :, :3].mean(axis=2)
    bg = local_bg(Image.fromarray(lum.astype(np.uint8)))
    dark = lum < bg - DARK_TH

    # 线条：横向游程分类（边框 ≥600 / 滑槽 250..450 且起点 460..520，实测滑槽游程 s=505），纵向 ≥300
    border_rows, groove_rows, hlines = [], [], []
    for i in range(lum.shape[0]):
        for s, e in runs(dark[i], H_GROOVE):
            hlines.append((i, s, e))
            if e - s >= H_BORDER: border_rows.append(i)
            elif 460 <= s <= 520: groove_rows.append(i)
    hrows = np.zeros(lum.shape[0], dtype=bool)
    for i, s, e in hlines: hrows[i] = True
    border_rows = sorted(set(border_rows))
    left_col  = [j for j in range(0, 200)  if runs(dark[:, j], V_LINE)]
    right_col = [j for j in range(700, 960) if runs(dark[:, j], V_LINE)]
    xt_l = min([j for j in left_col] or [65]); xt_r = max([j for j in right_col] or [897])
    y_top, y_bot = (border_rows[0], border_rows[-1]) if border_rows else (100, 460)

    prot = in_rects(lum.shape, BASE_PROTECT + cfg["extra_protect"])
    # 面板边框带（±3）与四角盒（35px）
    prot[y_top-3:y_top+4, xt_l-4:xt_r+5] = True
    prot[y_bot-3:y_bot+4, xt_l-4:xt_r+5] = True
    prot[:, xt_l-3:xt_l+4] = True; prot[:, xt_r-3:xt_r+4] = True
    for (a0, b0, a1, b1) in [(xt_l, y_top, xt_l+35, y_top+35), (xt_r-35, y_top, xt_r+4, y_top+35),
                             (xt_l, y_bot-35, xt_l+35, y_bot+4), (xt_r-35, y_bot-35, xt_r+4, y_bot+4)]:
        prot[max(0, b0):b1, max(0, a0):a1] = True
    # 滑槽行 ±9（保两端箭头）
    for i in groove_rows: prot[max(0, i-9):i+10, 450:830] = True

    lz = cfg["label_zone"]
    lz_rect = in_rects(lum.shape, [lz])
    btnz = cfg["btn_zone"]
    btn_rect = in_rects(lum.shape, [btnz])
    dark_soft = lum < bg - 12
    val_rect = in_rects(lum.shape, cfg.get("value_zones", []))
    mask = (dark & ~prot & ~lz_rect & ~val_rect) | (dark_soft & lz_rect) |            (dark_soft & btn_rect) | ((np.abs(lum - bg) > 12) & val_rect)
    mk = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(DILATE))
    mask_d = np.asarray(mk) > 0
    mask = (mask_d & ~prot) | (mask_d & lz_rect) | (mask_d & btn_rect) | (mask_d & val_rect)

    filled = harmonic_fill(page, mask)
    # 边框补画：面板上边框核心行（y_top±2）与标签区的交集
    core_rows = [r for r in range(max(0, y_top-2), y_top+3) if lz[1] <= r < lz[3]]
    border_repair(filled, lz, core_rows)

    # 证据叠图
    ov = filled.copy(); ov[mask] = ov[mask] * 0.25 + np.array([255, 60, 60, 255]) * 0.75
    img_ov = Image.fromarray(ov.astype(np.uint8)); d = ImageDraw.Draw(img_ov)
    for r in [(0,0,960,92),(0,92,62,545),(903,92,960,545),cfg["extra_protect"][0],lz,btnz]:
        d.rectangle([r[0], r[1], r[2]-1, r[3]-1], outline=(60, 220, 60, 255), width=1)
    d.rectangle([xt_l, y_top, xt_r, y_bot], outline=(255, 210, 0, 255), width=1)
    img_ov.save(os.path.join(EV, tag + "_overlay_v3.png"))

    # 输出页面 + 滑槽（行带分组；x 范围用 corners_zoom 实测固定值 458..818，含两端箭头）
    Image.fromarray(filled.astype(np.uint8)).save(os.path.join(OUT1, tag + "_page.png"))
    Image.fromarray((mask * 255).astype(np.uint8)).save(os.path.join(EV, tag + "_mask.png"))
    grows = sorted(set(groove_rows)); gbands = []
    for i in grows:
        if gbands and i - gbands[-1][1] <= 4: gbands[-1][1] = i
        else: gbands.append([i, i])
    for k, (g0, g1) in enumerate(gbands):
        Image.fromarray(filled[max(0, g0-9):g1+10, 458:818].astype(np.uint8)).save(
            os.path.join(OUT1, "%s_slider_%02d.png" % (tag, k+1)))

    # 雪碧条药丸
    s_op = (strip[:, :, 3] > 8)
    rows = s_op[:, :340].mean(axis=1)
    bands, s = [], None
    for i, v in enumerate(rows):
        if v > 0.5 and s is None: s = i
        elif v <= 0.5 and s is not None: bands.append((max(0, s-2), min(len(rows), i+2))); s = None
    if s is not None: bands.append((max(0, s-2), len(rows)))
    n = 0
    for (y0, y1) in bands:
        if y1 - y0 < 16: continue
        cols = s_op[y0:y1].mean(axis=0)
        # 药丸本体＝最左的长柱状游程（≥120px）；数值词/雪花与药丸之间有透明间隙，天然隔离
        pr = [r for r in runs(cols > 0.15, 8) if r[1] - r[0] >= 120]
        if not pr: continue
        x0, x1 = pr[0][0], pr[0][1] + 1
        if x1 - x0 < 150: continue
        pill = strip[y0:y1, x0:x1]
        pl = pill[:, :, :3].mean(axis=2)
        pbg = local_bg(Image.fromarray(pl.astype(np.uint8)))
        pmask = pl > pbg + 12
        inset = np.zeros_like(pmask); inset[4:-4, 6:-6] = True
        pmask &= inset
        pmk = Image.fromarray((pmask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
        pf = harmonic_fill(pill, np.asarray(pmk) > 0, iters=400)
        n += 1
        Image.fromarray(pf.astype(np.uint8)).save(os.path.join(OUT1, "%s_pill_%02d.png" % (tag, n)))

    manifest = {"page_end": page_end, "panel": [int(xt_l), int(y_top), int(xt_r), int(y_bot)],
                "label_zone": lz, "btn_zone": btnz, "label_border_rows": core_rows,
                "groove_bands": [[int(g0), int(g1)] for g0, g1 in gbands],
                "pill_bands": [[int(y0), int(y1)] for y0, y1 in bands],
                "pills": n, "mask_px": int(mask.sum())}
    print(name, json.dumps(manifest, ensure_ascii=False))
    return manifest

if __name__ == "__main__":
    man = {}
    for n in ["otv_bg_config_01.png", "otv_bg_config_02.png"]:
        man[n] = process(n)
    with open(os.path.join(WORK, "复现脚本", "rects_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
