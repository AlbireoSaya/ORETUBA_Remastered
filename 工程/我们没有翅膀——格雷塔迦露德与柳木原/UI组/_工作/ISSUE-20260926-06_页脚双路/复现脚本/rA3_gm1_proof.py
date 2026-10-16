# -*- coding: utf-8 -*-
r"""rA3 · gm_bg1 长项「雪晶保护带」自证
产出：
  _证据\r_A2\gm1_snow_8x.png      雪晶区 8× 四联：原件 / 真背景板 / 新 A 除字底 / 新 A 成图
  _证据\r_A2\gm1_long_3x.png      长项整段 3× 三联：原件 / 除字底 / 成图
  _证据\r_A2\gm1_overlap_8x.png   笔画∩雪晶 重叠范围图（重叠像素标黄）
  控制台台账：雪晶连通域数/像素数（原件 / 真背景板 / 旧 A / 新 A）、补底台阶、图标完好性
"""
import sys, os, json
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
EV_P = os.path.join(WORK, "_证据", "r_plate")
EV = os.path.join(WORK, "_证据", "r_A2")
OUT = os.path.join(BASE, "PSV系统UI参考", "_复核_20260926", "页脚双路")
BX0, BY0 = 850, 930
FX0, FY0 = 880, 940
NAME = "otv_gm_bg1.png"
LONGW = [971, 987, 1505, 1033]        # 长项 word bbox
ICONW = 45

plate = np.load(os.path.join(EV_P, "plate.npy"))
confn = np.load(os.path.join(EV_P, "conf_count.npy"))
snow = np.load(os.path.join(EV_P, "snowflake_mask.npy"))


def band(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      ).astype(np.float32)[930:1088, 850:1910, :3]


def dil(m, r):
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))) > 51


def erase_only(name):
    a = np.asarray(Image.open(os.path.join(EV, "erase_only", name.replace(".png", "") +
                                           "_A_erase_only.png")).convert("RGB")).astype(np.float32)
    f = np.full((158, 1060, 3), 255.0, np.float32)
    f[940 - BY0:1088 - BY0, 880 - BX0:1904 - BX0] = a
    return f


def finalA(name):
    a = np.asarray(Image.open(os.path.join(OUT, name.replace(".png", "") +
                                           "_A_程序化.png")).convert("RGB")).astype(np.float32)
    f = np.full((158, 1060, 3), 255.0, np.float32)
    f[940 - BY0:1088 - BY0, 880 - BX0:1904 - BX0] = a
    return f


def cc_count(mask):
    """8 连通域数与该域内像素总数（掩码为 bool）"""
    un = mask.copy()
    ys, xs = np.nonzero(mask)
    n = tot = 0
    for y0, x0 in zip(ys, xs):
        if not un[y0, x0]:
            continue
        n += 1
        st = [(y0, x0)]; un[y0, x0] = False
        while st:
            y, x = st.pop(); tot += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and un[ny, nx]:
                        un[ny, nx] = False; st.append((ny, nx))
    return n, tot


def snow_in_zone(img, zone):
    br = img[:, :, 2] - img[:, :, 0]
    lum = img.mean(axis=2)
    m = (br - np.asarray(Image.fromarray(np.clip(br + 30, 0, 255).astype(np.uint8)).filter(
        ImageFilter.BoxBlur(20)), np.float32) + 30 > 3) & (br >= 5) & (lum <= 253)
    m = m & zone
    return m


def to_band(arr148):
    f = np.full((158, 1060, 3), 255.0, np.float32)
    f[940 - BY0:1088 - BY0, 880 - BX0:1904 - BX0] = arr148
    return f


if __name__ == "__main__":
    o = band(NAME)
    eo = erase_only(NAME)
    fa = finalA(NAME)
    oldp = os.path.join(EV, "旧A_上一版", "otv_gm_bg1_A_程序化.png")
    old_a = to_band(np.asarray(Image.open(oldp).convert("RGB")).astype(np.float32)) if os.path.exists(oldp) else None

    # 雪晶关注区：长项左侧那枚（连通域 x1004-1093 y949-1014）+ 余量
    ZX0, ZX1, ZY0, ZY1 = 985, 1140, 945, 1035
    zone = np.zeros(o.shape[:2], bool)
    zone[ZY0 - BY0:ZY1 - BY0, ZX0 - BX0:ZX1 - BX0] = True
    print("=" * 78)
    print("【雪晶连通域 / 像素数】关注区 x%d-%d y%d-%d（=长项左侧那枚雪晶所在）" % (ZX0, ZX1, ZY0, ZY1))
    sm = snow & zone
    n0, t0 = cc_count(sm)
    print("  真背景板（10 屏交叉中位）雪晶模板：%d 连通域 / %d px" % (n0, t0))
    for lbl, img in [("原件 gm_bg1（PSV 烘焙日文）", o), ("新 A 除字底（未叠中文）", eo)] + \
                    ([("旧 A 除字底等价（旧成图）", old_a)] if old_a is not None else []):
        d = np.abs(img - plate).max(axis=2)
        keep = int((d[sm] <= 1).sum())
        print("  %-26s 雪晶模板像素 = 真背景值 %4d / %4d (%.1f%%)  max偏差=%3.0f  px偏差>1=%d"
              % (lbl, keep, t0, 100.0 * keep / max(1, t0), d[sm].max(), int((d[sm] > 1).sum())))
    cov_o = int((np.abs(o - plate).max(axis=2)[sm] > 1).sum())
    cov_n = int((np.abs(fa - plate).max(axis=2)[sm] > 1).sum())
    print("  新 A 成图：新中文笔画覆盖雪晶模板 %d px；原件日文覆盖 %d px（文字框同位，均不可避免）"
          % (cov_n, cov_o))
    print("  说明：原件被日文笔画/辉光覆盖，模板像素大量偏离背景；除字后应以真背景板为准复原为 100%。")

    print("\n【逐像素保真】除字底 vs 真背景板，仅在雪晶模板像素上")
    d = np.abs(eo - plate).max(axis=2)
    print("  除字底 @雪晶模板: max=%.0f mean=%.4f  px>0=%d / %d"
          % (d[sm].max(), d[sm].mean(), int((d[sm] > 0).sum()), int(sm.sum())))
    print("  （成图 @雪晶模板 max=%.0f：含新中文笔画覆盖，非背景误差）"
          % np.abs(fa - plate).max(axis=2)[sm].max())

    print("\n【除字掩码与雪晶的关系】")
    strong = ((o[:, :, 2] - o[:, :, 0]) > 20) & (o.mean(axis=2) < 246)
    cropdom = np.zeros(o.shape[:2], bool)
    cropdom[940 - BY0:1088 - BY0, 880 - BX0:1904 - BX0] = True
    eo_diff = (np.abs(eo - o).max(axis=2) > 0) & cropdom
    print("  除字改动像素（裁片域内，除字底与原件不同处）= %d" % int(eo_diff.sum()))
    print("  其中落在雪晶模板上 = %d px（= 日语笔画/辉光实际压到雪晶处）" % int((eo_diff & sm).sum()))
    pure = sm & (np.abs(o - plate).max(axis=2) <= 1)
    print("  未受日文覆盖的雪晶像素（原值=背景）= %d px" % int(pure.sum()))
    print("    其中被除字掩码改动 = %d px（应为 0）" % int((eo_diff & pure).sum()))
    print("    处理后与真背景板完全一致 = %s (max偏差=%.0f)"
          % ("是" if np.abs(eo - plate).max(axis=2)[pure].max() == 0 else "否",
             np.abs(eo - plate).max(axis=2)[pure].max()))

    print("\n【补底台阶】")
    x0, x1 = 1016 - BX0, 1521 - BX0
    y0, y1 = 971 - BY0, 1049 - BY0
    win = np.zeros(o.shape[:2], bool); win[y0:y1, x0:x1] = True
    ww = np.load(os.path.join(EV, "w_otv_gm_bg1.npy"))
    inside = ww > 0
    ring0 = (~inside) & dil(inside, 1)
    print("  羽化窗外缘(w=0)环 |除字底 - 原件|: max=%.1f  ← 构造上 w=0 处不动，台阶为 0" %
          np.abs(eo - o).max(axis=2)[ring0].max())
    core = ww >= 1.0
    print("  除字核心区(w=1) |除字底 - 原件|: max=%.1f  |除字底 - 真背景板|(仅 CONF 列)=%.1f"
          % (np.abs(eo - o).max(axis=2)[core].max(),
             np.abs(eo - plate).max(axis=2)[core & (confn >= 2)].max()))
    icon = np.zeros(o.shape[:2], bool)
    icon[987 - BY0:1033 - BY0, 971 - BX0:(971 + ICONW) - BX0] = True
    print("  长项图标区(x971-%d) 除字底 vs 原件: max=%.1f  ← 图标未被触碰"
          % (971 + ICONW, np.abs(eo - o).max(axis=2)[icon].max()))

    # ---- 出图 ----
    def panel(arr, z, box):
        c = arr[box[1] - BY0:box[3] - BY0, box[0] - BX0:box[2] - BX0]
        return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).resize(
            ((box[2] - box[0]) * z, (box[3] - box[1]) * z), Image.NEAREST)

    f = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 22)
    box8 = (995, 948, 1135, 1038)
    panels = [("原件（PSV 烘焙日文）", o), ("真背景板（10 屏交叉中位）", plate),
              ("新 A 除字底（已还原雪晶）", eo), ("新 A 成图（叠中文）", fa)]
    ps = [panel(a, 8, box8) for _, a in panels]
    W = sum(p.width for p in ps) + 16 * 5
    H = max(p.height for p in ps) + 46
    sh = Image.new("RGB", (W, H), (26, 28, 34))
    d2 = ImageDraw.Draw(sh)
    x = 16
    for (lbl, _), p in zip(panels, ps):
        sh.paste(p, (x, 44))
        d2.text((x, 14), lbl, font=f, fill=(255, 235, 180))
        d2.rectangle([x, 44, x + p.width - 1, 44 + p.height - 1], outline=(90, 95, 110))
        x += p.width + 16
    sh.save(os.path.join(EV, "gm1_snow_8x.png"))

    # 长项整段 3x 三联
    boxl = (960, 960, 1520, 1055)
    lps = [panel(a, 3, boxl) for _, a in [("", o), ("", eo), ("", fa)]]
    W = sum(p.width for p in lps) + 16 * 4
    H = max(p.height for p in lps) + 44
    sh2 = Image.new("RGB", (W, H), (26, 28, 34))
    d3 = ImageDraw.Draw(sh2)
    x = 16
    for lbl, p in zip(["原件", "新 A 除字底（雪晶保留）", "新 A 成图"], lps):
        sh2.paste(p, (x, 42))
        d3.text((x, 12), lbl, font=f, fill=(255, 235, 180))
        d3.rectangle([x, 42, x + p.width - 1, 42 + p.height - 1], outline=(90, 95, 110))
        x += p.width + 16
    sh2.save(os.path.join(EV, "gm1_long_3x.png"))

    # 重叠范围图：笔画∩雪晶 标黄，纯雪晶标绿，笔画标红
    ov = np.clip(plate, 0, 255).astype(np.uint8).copy()
    sz = snow & zone
    ov[sz] = (0, 190, 90)
    st = dil(strong, 1) & zone
    ov[st] = (235, 60, 60)
    ov[sz & st] = (255, 225, 40)
    c = ov[box8[1] - BY0:box8[3] - BY0, box8[0] - BX0:box8[2] - BX0]
    c8 = Image.fromarray(c).resize(((box8[2] - box8[0]) * 8, (box8[3] - box8[1]) * 8), Image.NEAREST)
    sh3 = Image.new("RGB", (c8.width, c8.height + 40), (26, 28, 34))
    sh3.paste(c8, (0, 40))
    ImageDraw.Draw(sh3).text((8, 10), "红=日语笔画  绿=纯雪晶  黄=笔画∩雪晶重叠", font=f, fill=(255, 235, 180))
    sh3.save(os.path.join(EV, "gm1_overlap_8x.png"))
    print("\nsaved gm1_snow_8x.png / gm1_long_3x.png / gm1_overlap_8x.png ->", EV)
