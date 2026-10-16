# -*- coding: utf-8 -*-
r"""pA · A 路（程序化）：页脚日文除字（保图标）+ 黑体中文合成
做法：
 1. 文字掩码 = 蓝饱和度 (b-r)>20（原字为「近白字心 + 强蓝描边 + 蓝辉光」）；
    在文字窗（word_x0+47 .. word_x1+6，y0-5 .. y1+6）内取掩码 → 膨胀 → 洞填充（补字心）；
    图标区（word_x0 .. word_x0+47）不动。
 2. 补底：行向线性插值 x0.6 + 列向线性插值 x0.4，再掩码内盒式平滑（霜面近乎平整）。
 3. 中文渲染：微软雅黑粗体 msyhbd.ttc，size=41 @2×（= 原日文每字 advance 41px），4× 超采样；
    样式 = 字心 (240,244,254) + 描边 (100,158,246) + 双层蓝辉光；
    水平居中于原文字框、垂直居中于原墨迹中心，1:1 贴回。
输出：PSV系统UI参考\_复核_20260926\页脚双路\<件名>_A_程序化.png（页脚裁片 1024x148）
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV = os.path.join(WORK, "_证据"); os.makedirs(EV, exist_ok=True)
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路"); os.makedirs(OUT, exist_ok=True)

FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088      # 页脚裁片（与 B 路同框）
BX0, BX1 = 850, 1910                            # 工作带 x
BY0, BY1 = 930, 1088                            # 工作带 y
FONT = r"C:\Windows\Fonts\msyhbd.ttc"
SIZE = 44
SS = 4
BTH = 20
DIL = 3
CLN_BR, CLN_LUM = 6, 244   # 「干净霜面」判据（插值端点）
REF_GAP = 20               # 背景估计：仅用窗框外 >=20px 的干净霜面
DEG_T0, DEG_RANGE = 2.5, 9.0   # 窗内残边软回拉：|偏差| 阈值与过渡带宽
ICON_W = 47
FILL = (244, 247, 255)
STROKE_RGB = (94, 152, 244)
GLOW1, GLOW2 = (150, 190, 250), (214, 230, 253)
STROKE_SS = 7         # 蓝描边膨胀半径（4x）-> 1x 约 1.75px
HALO_SS = 20          # 白外晕膨胀半径（4x）-> 1x 约 5px
GLO_SS = 34           # 蓝辉光高斯 sigma（4x）-> 1x 约 8.5px
GLO2_SS = 70          # 宽蓝辉光 sigma（4x）
HALO_A = 0.93         # 白外晕不透明度
HALO_RGB = (252, 254, 255)
G1A, G2A = 0.72, 0.22 # 近辉光 / 宽辉光强度

TEXT = {
    "otv_save_bg.png": ["确定", "删除数据", "返回"],
    "otv_load_bg.png": ["确定", "删除数据", "返回"],
    "otv_quick_load_bg.png": ["确定", "返回"],
    "otv_bklog.png": ["语音播放", "返回"],
    "otv_gm_bg1.png": ["部分图片可滚动查看", "确定", "返回"],
    "otv_mu_bg.png": ["播放／停止", "返回", "选择"],
    "otv_mv_bg.png": ["播放", "返回"],
}
bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))


def dilate_bool(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im) > 51


def fill_holes(m):
    pad = np.zeros((m.shape[0] + 2, m.shape[1] + 2), bool)
    pad[1:-1, 1:-1] = m
    inv = Image.fromarray(((~pad) * 255).astype(np.uint8))
    w, h = inv.size
    for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if inv.getpixel(xy) == 255:
            ImageDraw.floodfill(inv, xy, 128)
    return (np.asarray(inv) == 255)[1:-1, 1:-1]


def interp_fill(band, mask, win, br):
    """掩码区补底 + 残余辉光/白晕中和
    端点只用「窗框外 >=GAP 像素」的干净霜面（避开字身、蓝辉光尾与白晕），
    沿列做线性插值得到背景估计 colf；掩码区填 colf，窗内非掩码像素按
    与 colf 的偏差做软性回拉（一并中和蓝辉光尾与白晕残边）。
    """
    lum = band.mean(axis=2)
    h, w = mask.shape[:2]
    good = ~dilate_bool(win, REF_GAP)
    colf = band.copy()
    yall = np.arange(h)
    for x in range(w):
        g = good[:, x]
        if g.sum() < 2:
            g = ~mask[:, x]
        if not g.any():
            continue
        for c in range(3):
            colf[:, x, c] = np.interp(yall, yall[g], band[g, x, c])
    out = band.copy()
    out[mask] = colf[mask]
    dev = np.abs(lum - colf.mean(axis=2))
    alpha = np.clip((dev - DEG_T0) / DEG_RANGE, 0, 1)
    alpha[~(win & ~mask)] = 0
    out = out * (1 - alpha[:, :, None]) + colf * alpha[:, :, None]
    for _ in range(24):
        blur = np.asarray(Image.fromarray(out.astype(np.uint8)).filter(ImageFilter.BoxBlur(3))).astype(np.float32)
        out[mask] = blur[mask]
    return out


def render_text(txt, size, font_path):
    """4x 超采样渲染：外层蓝辉光 -> 白外晕 -> 蓝描边 -> 近白字心（顺序=由外到内）"""
    f = ImageFont.truetype(font_path, size * SS)
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), txt, font=f)
    pad = 20 * SS
    W = bb[2] - bb[0] + pad * 2
    H = bb[3] - bb[1] + pad * 2
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=255)
    ma = np.asarray(m).astype(np.float32) / 255.0
    Hh, Ww = ma.shape
    core = ma > 0.5
    # 白外晕（原字为「字心 + 蓝描边 + 白色外晕 + 蓝辉光」四层）
    halo = dilate_bool(core, HALO_SS)
    st = dilate_bool(core, STROKE_SS) & ~core
    rgb = np.zeros((Hh, Ww, 3), np.float32)
    al = np.zeros((Hh, Ww), np.float32)
    # 1) 蓝辉光（由白晕外扩高斯）
    hb = Image.fromarray((halo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(GLO_SS))
    g = np.asarray(hb).astype(np.float32) / 255.0 * G1A
    hb2 = Image.fromarray((halo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(GLO2_SS))
    g2 = np.asarray(hb2).astype(np.float32) / 255.0 * G2A
    rgb[:] = GLOW2
    al = np.clip(g2, 0, 1)
    selg = g > al
    rgb[selg] = GLOW1
    al = np.maximum(al, np.clip(g, 0, 1))
    # 2) 白外晕
    sel = halo & (al < HALO_A)
    rgb[sel] = HALO_RGB
    al[sel] = HALO_A
    # 3) 蓝描边
    rgb[st] = STROKE_RGB
    al[st] = 1.0
    # 4) 字心
    rgb[core] = FILL
    al[core] = 1.0
    layer = np.concatenate([rgb, al[:, :, None] * 255.0], axis=2)
    limg = Image.fromarray(np.clip(layer, 0, 255).astype(np.uint8), "RGBA").resize(
        (max(1, Ww // SS), max(1, Hh // SS)), Image.LANCZOS)
    la = np.asarray(limg).astype(np.float32)
    ys, xs = np.nonzero(la[:, :, 3] > 40)
    ink = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return la, ink


def process(name, size=SIZE, font=FONT, tag=""):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    band = a[BY0:BY1, BX0:BX1].copy()
    band = np.asarray(Image.alpha_composite(
        Image.new("RGBA", (BX1 - BX0, BY1 - BY0), (255, 255, 255, 255)),
        Image.fromarray(band.astype(np.uint8), "RGBA"))).astype(np.float32)
    br = band[:, :, 2] - band[:, :, 0]

    words = bbox[name]
    full = np.zeros(br.shape, bool)
    winall = np.zeros(br.shape, bool)
    for w in words:
        x0, y0, x1, y1 = w["x0"] - BX0, w["y0"] - BY0, w["x1"] - BX0, w["y1"] - BY0
        wx0, wx1 = x0 + ICON_W, min(x1 + 7, br.shape[1])
        wy0, wy1 = max(0, y0 - 5), min(br.shape[0], y1 + 6)
        win = np.zeros(br.shape, bool)
        win[wy0:wy1, wx0:wx1] = True
        m = dilate_bool((br > BTH) & win, DIL)
        m = (m | fill_holes(m)) & win
        full |= m
        winall |= win
    filled = interp_fill(band, full, winall, br)

    lay = Image.fromarray(np.clip(filled, 0, 255).astype(np.uint8), "RGBA")
    rep = []
    # 逐件同字号：取「各词都能塞进原文字框」的最大字号（下限 36，上限 size）
    use_file = size
    for txt, w in zip(TEXT[name], words):
        boxw = w["x1"] - (w["x0"] + ICON_W)
        fit = int(boxw / float(max(1, len(txt))))          # CJK 每字 advance = 字号
        if fit < use_file:
            use_file = max(34, fit)
    for txt, w in zip(TEXT[name], words):
        tx0 = w["x0"] + ICON_W
        la, ink = render_text(txt, use_file, font)
        use = use_file
        cx = (tx0 + w["x1"]) / 2.0
        cy = (w["y0"] + w["y1"]) / 2.0
        ix = (ink[0] + ink[2] + 1) / 2.0
        iy = (ink[1] + ink[3] + 1) / 2.0
        px = int(round(cx - ix)) - BX0
        py = int(round(cy - iy)) - BY0
        lay.alpha_composite(Image.fromarray(la.astype(np.uint8), "RGBA"), (px, py))
        rep.append((txt + ("(缩%d)" % use if use != size else ""), ink[2] - ink[0] + 1,
                    ink[3] - ink[1] + 1, px + BX0, py + BY0, w["x1"] - tx0, w["y1"] - w["y0"] + 1))
    res = a.copy()
    res[BY0:BY1, BX0:BX1] = np.asarray(lay).astype(np.float32)
    fullimg = Image.fromarray(res.astype(np.uint8), "RGBA")
    crop = fullimg.crop((FX0, FY0, FX1, FY1)).convert("RGB")
    p = os.path.join(OUT, name.replace(".png", "") + "_A_程序化" + tag + ".png")
    crop.save(p)
    ov = np.clip(filled, 0, 255).astype(np.float32)
    ov[full] = ov[full] * 0.3 + np.array([255, 40, 40, 255]) * 0.7
    Image.fromarray(ov.astype(np.uint8), "RGBA").crop(
        (FX0 - BX0, FY0 - BY0, FX1 - BX0, FY1 - BY0)).convert("RGB").save(
        os.path.join(EV, "A_mask" + tag + "_" + name))
    print("   erase px=%d -> %s" % (int(full.sum()), os.path.basename(p)))
    for r in rep:
        print("     %-14s ink %dx%d  贴(x=%d,y=%d) 原文字框宽%d 原墨高%d" % r)
    return p


if __name__ == "__main__":
    for n in TEXT:
        print("=" * 74); print(n)
        process(n)
