# -*- coding: utf-8 -*-
r"""rA2 · A 路（程序化）定稿：页脚日文除字 + 中文黑体合成
=====================================================================
与上一版（pA.py）的三处差异（落实用户裁决）：
 1) 对齐：中文按「原文字框左端」起排（左对齐），不再整体居中、不拉字距；图标原位。
 2) 除字底源：新增「10 屏同背景精确底板」（r1_plate.py 产出）。
    在底板可信处（free_count>=3，即 ≥3 件在该像素无字足迹），除字区直接用底板填底
    ——底板 = 真背景，含雪晶在内的淡蓝装饰被逐像素精确保留。
    底板不可信处（仅右端 ⊗戻る／✿選択／◎決定 列，全部屏同位有字）沿用旧法：
    掩码内填列向插值底 + 窗口内软回拉中和残辉光。
 3) otv_mu_bg 第三项照实测：◎再生／停止 / ⊗戻る / ✿選択 → 播放／停止 / 返回 / 选择。
=====================================================================
输出：
  PSV系统UI参考\_复核_20260926\页脚双路\<件名>_A_程序化.png   (1024x148, 覆盖)
  页脚双路_对比.png（左=原版 / 中=A 新定稿 / 右=B 保留）
  _证据\r_A2\ 下的掩码图、除字底图、gm_bg1 雪晶自证图
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV_P = os.path.join(WORK, "_证据", "r_plate")
EV = os.path.join(WORK, "_证据", "r_A2"); os.makedirs(EV, exist_ok=True)
ERASE_ONLY = os.path.join(EV, "erase_only"); os.makedirs(ERASE_ONLY, exist_ok=True)
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路"); os.makedirs(OUT, exist_ok=True)

FX0, FY0, FX1, FY1 = 880, 940, 1904, 1088      # 页脚裁片（与 B 路同框）
BX0, BX1, BY0, BY1 = 850, 1910, 930, 1088       # 工作带

# ---- 文字样式（沿用 pA / p5 标定，未改） ----
FONT = r"C:\Windows\Fonts\msyhbd.ttc"           # 微软雅黑粗体
SIZE = 44                                       # @2× 字号（原日文每字 advance 41-45）
SS = 4                                          # 超采样倍数
BTH = 20                                        # 蓝饱和度阈值 b-r（原字＝近白字心+强蓝描边）
DIL_BAD = 3                                     # 旧法掩码膨胀半径（底板不可信区）
REF_GAP = 20                                    # 背景估计：仅用窗框外 >=20px 的干净霜面
DEG_T0, DEG_RANGE = 2.5, 9.0                    # 窗内残边软回拉：阈值与过渡带宽
ICON_W_DEF = 45                                 # 文字框左端 = word.x0 + 图标宽（默认 45）
CORE_MX, CORE_MY = 12, 12                       # 除字核心区外扩（px，覆盖原字蓝辉光尾）
FEATH = 6                                       # 除字窗羽化带宽（px），w 由 1 线性降到 0
GOOD_MIN = 3                                    # free_count >= 3 视作底板可信
DIFF_T = 3.0                                    # 底板可信区除字判据：|原件-底板| > 3
FILL = (244, 247, 255)
STROKE_RGB = (94, 152, 244)
GLOW1, GLOW2 = (150, 190, 250), (214, 230, 253)
STROKE_SS = 7        # 蓝描边膨胀半径（4x）
HALO_SS = 20         # 白外晕膨胀半径（4x）
GLO_SS = 34          # 蓝辉光高斯 sigma（4x）
GLO2_SS = 70         # 宽蓝辉光 sigma（4x）
HALO_A = 0.93
HALO_RGB = (252, 254, 255)
G1A, G2A = 0.72, 0.22

# ---- 中文文案（7 件） ----
TEXT = {
    "otv_save_bg.png": ["确定", "删除数据", "返回"],
    "otv_load_bg.png": ["确定", "删除数据", "返回"],
    "otv_quick_load_bg.png": ["确定", "返回"],
    "otv_bklog.png": ["语音播放", "返回"],
    "otv_gm_bg1.png": ["部分图片可滚动查看", "确定", "返回"],
    "otv_mu_bg.png": ["播放／停止", "返回", "选择"],       # 第三项：✿選択 → 选择（实测）
    "otv_mv_bg.png": ["播放", "返回"],
}
ORDER = list(TEXT.keys())

bbox = json.load(open(os.path.join(WORK, "footer_bbox.json"), encoding="utf-8"))
split = json.load(open(os.path.join(WORK, "footer_bbox_split.json"), encoding="utf-8"))
plate = np.load(os.path.join(EV_P, "plate.npy")).astype(np.float32)
free = np.load(os.path.join(EV_P, "free_count.npy")).astype(np.int32)
confn = np.load(os.path.join(EV_P, "conf_count.npy")).astype(np.int32)
snow = np.load(os.path.join(EV_P, "snowflake_mask.npy"))
GOOD = free >= GOOD_MIN                 # ≥3 件在该像素无字足迹
CONF = confn >= 2                       # ≥2 件与底板逐像素一致 → 底板即真背景


def dilate_bool(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im) > 51


def icon_width(name, idx):
    """文字框左端相对 word.x0 的偏移：优先用 footer_bbox_split 实测图标宽（<=50 才可信）"""
    try:
        t = split[name][idx]["text"]
        if t is not None:
            w = int(t[0]) - int(bbox[name][idx]["x0"])
            if 30 <= w <= 50:
                return w
    except Exception:
        pass
    return ICON_W_DEF


def band_of(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    a = np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im))
    return a.astype(np.float32)[BY0:BY1, BX0:BX1, :3]


def interp_fill(band, mask, win, br):
    """旧法（底板不可信区）：窗框外 >=GAP 像素的干净霜面作端点，逐列线性插值；
    掩码区填插值底，窗内非掩码像素按与底的偏差软回拉（中和蓝辉光尾与白晕残边）。"""
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
    """4x 超采样渲染：蓝辉光 -> 白外晕 -> 蓝描边 -> 近白字心（由外到内）"""
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
    halo = dilate_bool(core, HALO_SS)
    st = dilate_bool(core, STROKE_SS) & ~core
    rgb = np.zeros((Hh, Ww, 3), np.float32)
    al = np.zeros((Hh, Ww), np.float32)
    hb = Image.fromarray((halo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(GLO_SS))
    g = np.asarray(hb).astype(np.float32) / 255.0 * G1A
    hb2 = Image.fromarray((halo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(GLO2_SS))
    g2 = np.asarray(hb2).astype(np.float32) / 255.0 * G2A
    rgb[:] = GLOW2
    al = np.clip(g2, 0, 1)
    selg = g > al
    rgb[selg] = GLOW1
    al = np.maximum(al, np.clip(g, 0, 1))
    sel = halo & (al < HALO_A)
    rgb[sel] = HALO_RGB
    al[sel] = HALO_A
    rgb[st] = STROKE_RGB
    al[st] = 1.0
    rgb[core] = FILL
    al[core] = 1.0
    layer = np.concatenate([rgb, al[:, :, None] * 255.0], axis=2)
    limg = Image.fromarray(np.clip(layer, 0, 255).astype(np.uint8), "RGBA").resize(
        (max(1, Ww // SS), max(1, Hh // SS)), Image.LANCZOS)
    la = np.asarray(limg).astype(np.float32)
    ys, xs = np.nonzero(la[:, :, 3] > 40)
    ink = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return la, ink


def build_erase(name):
    """返回 (除字底图 float32, 羽化权重 w, winall bool, 统计 dict)
    羽化：文字窗核心区 w=1（整窗用底板/旧法底替换），四周向外 FEATH px 线性衰减到 w=0
          → 窗边界 w=0，除字底==原件，补底台阶恒为 0（构造保证）。
          图标一侧为硬边（w 从文字框左端直接起跳），图标像素永不触碰。"""
    band = band_of(name)
    br = band[:, :, 2] - band[:, :, 0]
    lum = band.mean(axis=2)
    H, W = band.shape[:2]
    words = bbox[name]
    iws = [icon_width(name, i) for i in range(len(words))]

    w = np.zeros((H, W), np.float32)
    for wd, iw in zip(words, iws):
        xc0 = max(0, min(W - 1, wd["x0"] + iw - BX0))          # 硬边：文字框左端（图标右缘外）
        xc1 = max(xc0, min(W, wd["x1"] + CORE_MX - BX0))
        yc0 = max(0, wd["y0"] - CORE_MY - BY0)
        yc1 = min(H, wd["y1"] + CORE_MY - BY0)
        px = np.zeros(W, np.float32)
        px[xc0:xc1] = 1.0
        for i in range(FEATH):
            j = xc1 + i
            if j < W:
                px[j] = 1.0 - (i + 1) / float(FEATH + 1)
        py = np.zeros(H, np.float32)
        py[yc0:yc1] = 1.0
        for i in range(FEATH):
            if yc0 - 1 - i >= 0:
                py[yc0 - 1 - i] = 1.0 - (i + 1) / float(FEATH + 1)
            if yc1 + i < H:
                py[yc1 + i] = 1.0 - (i + 1) / float(FEATH + 1)
        w = np.maximum(w, np.minimum(px[None, :], py[:, None]))
    winall = w > 0

    strong = (br > BTH) & (lum < 246)
    dtxt = np.abs(band - plate).max(axis=2)
    pure_snow = snow & (dtxt <= 1.0)          # 未受日文覆盖的雪晶：原值即背景，一律不动
    w = np.where(pure_snow, 0.0, w)
    win_conf = winall & CONF
    win_bad = winall & ~CONF
    mask_bad = dilate_bool(strong, DIL_BAD) & win_bad

    bg = plate.copy()
    alt = interp_fill(band, mask_bad, winall & ~CONF, br)
    bg[win_bad] = alt[win_bad]
    filled = band * (1.0 - w[:, :, None]) + bg * w[:, :, None]

    st = {"win_conf": int(win_conf.sum()), "win_bad": int(win_bad.sum()),
          "mask_bad": int(mask_bad.sum()), "snow_pure": int(pure_snow.sum()),
          "overlap": int((mask_bad & snow).sum()),
          "feather": int(((w > 0) & (w < 1)).sum()),
          "conf_pct": round(100.0 * win_conf.sum() / max(1, winall.sum()), 1)}
    return filled, w, winall, iws, st


def process(name, save_overlay=True):
    band = band_of(name)
    filled, mask, winall, iws, st = build_erase(name)   # mask 此处即羽化权重 w
    H, W = band.shape[:2]
    filled_rgba = np.concatenate([filled, np.full((H, W, 1), 255.0, np.float32)], axis=2)
    lay = Image.fromarray(np.clip(filled_rgba, 0, 255).astype(np.uint8))

    print("=" * 78)
    print("%s  可信窗 %d px (%.0f%%) / 旧法窗 %d px ｜ 旧法掩码 %d px ｜ 羽化带 %d px ｜ 未覆盖雪晶(不动) %d px"
          % (name, st["win_conf"], st["conf_pct"], st["win_bad"], st["mask_bad"],
             st["feather"], st["snow_pure"]))
    rep = []
    for i, (txt, w) in enumerate(zip(TEXT[name], bbox[name])):
        tx0 = w["x0"] + iws[i]                      # 左对齐：原文字框左端
        la, ink = render_text(txt, SIZE, FONT)
        cy = (w["y0"] + w["y1"]) / 2.0
        iy = (ink[1] + ink[3] + 1) / 2.0
        px = int(round(tx0 - ink[0])) - BX0
        py = int(round(cy - iy)) - BY0
        lay.alpha_composite(Image.fromarray(la.astype(np.uint8), "RGBA"), (px, py))
        rep.append((txt, w["x0"], tx0, w["x1"], int(ink[2] - ink[0] + 1), int(ink[3] - ink[1] + 1),
                    px + BX0, py + BY0, cy))
        print("   %-12s 文字框 x%4d-%4d 起排 x%4d (图标宽%2d)  墨 %dx%d  贴(%d,%d) 垂直中心 %.1f"
              % (txt, w["x0"], w["x1"], tx0, iws[i], ink[2] - ink[0] + 1, ink[3] - ink[1] + 1,
                 px + BX0, py + BY0, cy))

    res = np.asarray(lay).astype(np.float32)
    fullimg = Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))
    crop = fullimg.crop((FX0 - BX0, FY0 - BY0, FX1 - BX0, FY1 - BY0)).convert("RGB")
    p = os.path.join(OUT, name.replace(".png", "") + "_A_程序化.png")
    crop.save(p)

    # 除字底图（未叠中文）
    eo = np.full((BY1 - BY0, BX1 - BX0, 3), 255, np.float32)
    eo[:] = filled
    Image.fromarray(np.clip(eo, 0, 255).astype(np.uint8)).crop(
        (FX0 - BX0, FY0 - BY0, FX1 - BX0, FY1 - BY0)).save(
        os.path.join(ERASE_ONLY, name.replace(".png", "") + "_A_erase_only.png"))
    np.save(os.path.join(EV, "w_%s.npy" % name.replace(".png", "")), mask.astype(np.float32))

    if save_overlay:
        ov = filled.copy()
        mm = mask >= 0.5
        ov[mm] = ov[mm] * 0.3 + np.array([255, 40, 40], np.float32) * 0.7
        ff = (mask > 0) & (mask < 0.5)
        ov[ff] = ov[ff] * 0.4 + np.array([255, 190, 40], np.float32) * 0.6
        ov[snow & winall] = ov[snow & winall] * 0.35 + np.array([0, 170, 60], np.float32) * 0.65
        Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)).crop(
            (FX0 - BX0, FY0 - BY0, FX1 - BX0, FY1 - BY0)).save(
            os.path.join(EV, "mask_%s.png" % name.replace(".png", "")))
    return p, st


if __name__ == "__main__":
    stats = {}
    for n in ORDER:
        p, st = process(n)
        stats[n] = st
    with open(os.path.join(EV, "erase_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("\nA 路 7 件落盘 ->", OUT)
