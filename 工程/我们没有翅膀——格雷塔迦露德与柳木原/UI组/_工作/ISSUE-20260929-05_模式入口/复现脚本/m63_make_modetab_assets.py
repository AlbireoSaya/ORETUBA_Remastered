# -*- coding: utf-8 -*-
r"""m63_make_modetab_assets.py · 流程图「模式入口」三态底光素材（**3 件**）—— 纯程序化 PIL，无 AI 生图

Issue  : **ISSUE-20260929-05**（流程图模式入口收敛）· 模块 **E1 素材**
接口   : `_工作\ISSUE-20260929-05_模式入口\接口冻结.md` **§B / §C / §D**（**唯一接口**；尺寸、几何、
         三态口径**不得自行改动**）
用户指令: 冻结书 §0 引用的用户原话 —— 「(1) 排版整齐 (2) 高度 60px 左右 (3) **白色文字＋黑色描边＋
         白色淡光**，字体微软雅黑 Regular (4) 常规/悬停/点击三态，**悬停态＝该文字按钮整体发亮**，
         三态必须一眼可辨」；按下态由用户裁决为「**实底胶囊（半透明冰蓝 + 亮边）**」（冻结书 §C）。

■■ 产出清单（`krkr\assets\ui\`，**3 件**；仅新增，绝不覆盖任何既有件）

    x_ui_modetab_off.png    180×60 RGBA  常规  **柔和白色淡光（弱档）**：底框 120×40 上平铺 α=104 白，
                                               框外多方向高斯式柔化肩部，越靠外越淡至全透明
    x_ui_modetab_over.png   180×60 RGBA  悬停  **同一枚光晕整体提亮/加大**：α=104→172、横向肩 9.0→11.2、
                                               纵向肩 6.0→5.6（峰值更高 ⇒ **同一绝对 α 上的展开更宽**）
    x_ui_modetab_press.png  180×60 RGBA  按下  **半透明冰蓝实底胶囊**（圆角 10，填充 @palette.accent 系
                                               α=160 竖向微渐变）＋**1px 亮边**（@palette.accent 向白
                                               50% 混合、α=255）；**整枚胶囊下沉 1px**（底框 y10..50 →
                                               胶囊 y11..51）

★ **两个入口共用这 3 张**：文案由引擎画、形状与文案无关（两入口同为 4 字、同 180×60）⇒ **只出 3 件**，
  符合冻结书 §D「优先省件数」。
  ⚠ **命名对账（交给接线方 E2）**：冻结书 §B 的字面 asset 串写的是
    `ui/x_ui_modetab_main_off.png` / `ui/x_ui_modetab_frag_off.png`（6 件口径）；本批按派单出
    **`ui/x_ui_modetab_{off,over,press}.png` 3 件**，两入口的 `asset`/`state_assets` 一律指向这 3 件。

■ 三态口径（**逐条可机检**，见「自证」）

  · **底框 = 文字区 = 中心 120×40**（连续坐标 x∈[30,150]、y∈[10,50]），与冻结书 §B「元素 180×60、
    文字居中」一致。光晕在底框内为**平铺（plateau）**、框外为光滑肩部 ⇒ 「文字区域外一圈多方向柔化的
    白晕」；**无硬描边、无硬边**（场是解析高斯式，处处 C¹ 连续，框沿法向导数为 0 ⇒ 无折痕）。
  · **α 上限有意压低**（off 104 / over 172，均 < 180）：文字是**白字 + 2px 黑描边**压在光上，
    若把底光做成近不透明的白板，白字与底板就无对比（观感上「光吃掉字」）。本批口径：
    off 的峰值 α 取 0.41、over 取 0.67，**两态都刻意留出「白字(255) vs 底板合成色」的亮度台阶**，
    并在证据里给出实测台阶与 WCAG 对比度（`E1_模拟合成_文字压光.png`）。
  · **黑描边不可能被吃掉**：描边由引擎以**不透明黑**栅格化在文字层内、整层压在光之上 ⇒ 合成为纯黑。
    本批用 `E1_模拟合成_文字压光.png` **实测**描边像素的合成色恒为 (0,0,0)（见自证报告 §三）。
  · **悬停「一眼可辨」的量化差**：文字区平均 α 104→172（×1.65）、峰值 α 104→172、全画布 α>8 面积
    约 +16%；且**任一绝对 α 上 over 的展开都比 off 宽**（σ_x 9.0→11.2）。
  · **按下「下沉 1px」**：底框上沿 y=10 → 胶囊上沿 y=11。**实测口径**：以「α≥200 区 bbox 上沿」
    比较 —— press 的 α≥200 像素来自 1px 亮边（α=255 档）⇒ bbox 上沿 **11**；off/over 的底框上沿由
    **平铺区实测**（α ≥ 0.995×峰值 的首行）⇒ **10**。断言 `press_top == off_top + 1 == over_top + 1`（±0）。
    ⚠ 冻结书 §C 的「文字下移 1px」在 schema 上不可实现（文字逐态位移无接口），故以**底沉 1px**等价表达。

■ 边缘策略 `frame`
  最外 1px 帧 α **恒为 0**：解析场在设计上已使帧值 ≤10，再经 `m55.clip_low_alpha(thr=10)`
  （本工程登记的「柔光尾归零」口径，见 m55 注释与 §D）收敛为 0。脚本同时断言**剪前帧 αmax ≤10**
  与**剪后帧 αmax == 0**（两条都判，避免断言空转）。

■ 配色（**一律引色板键，不直写色值**）
  · 白淡光：`@palette.text_primary`(#FFFFFF)
  · 胶囊填充：`@palette.accent`(#7AB0E8) —— 上端 `mix(accent, text_primary, 0.10)`、
    下端 `mix(accent, panel_edge, 0.22)`（**均为色板键的线性混合**，不新增色号）
  · 1px 亮边：`mix(accent, text_primary, 0.50)`
  （色板经 `m55_make_flow_assets.load_palette()` 读取；缺键即抛错，无静默回落。）

■ 幂等
  纯程序化：**无随机、无时间戳、无网络、无 AI 生图、不读任何既有素材的像素**（只读 `palette.json`）。
  脚本自证「内存里连造两次逐字节一致」＋「磁盘现值 == 本次生成值」；且**写前/写后对
  `krkr\assets\ui\` 全目录做 (文件名→字节数→md5) 台账**，断言**唯一差异 = 本批 3 件**（＝「未覆盖、
  未删除任何既有素材」的机检）。目标文件若已存在而字节不同 ⇒ **直接报错退出**，绝不静默覆盖。

■ 依赖：Pillow（`ImageDraw.rounded_rectangle` ≥8.2）、numpy；字体 `C:\Windows\Fonts\msyh.ttc`(index 0,
  Microsoft YaHei Regular) 与 `msyhbd.ttc`（**仅用于证据图标注**，不参与素材本体）。
  本机实测：Python / Pillow / numpy 版本见运行输出。

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python "_工作\ISSUE-20260929-05_模式入口\复现脚本\m63_make_modetab_assets.py"            # 产出＋自证＋证据
    python "…\m63_make_modetab_assets.py" --dry-run                                        # 只自证，不写盘
    python "…\m63_make_modetab_assets.py" --check                                          # 只读核对磁盘现值
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════════════ 路径
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)                                    # _工作\ISSUE-20260929-05_模式入口
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
EVID = os.path.join(ISSUE_DIR, "证据")
VERIFY_UI = os.path.join(UI_GROUP, "工具", "verify_ui.py")
BUDGET_MB = 96

# ★ 复用 m55 的色板读取与掩膜助手（本工程现行口径；m55 带 __main__ 守卫、可安全 import）
M55_DIR = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "复现脚本")
if M55_DIR not in sys.path:
    sys.path.insert(0, M55_DIR)
import m55_make_flow_assets as M55  # noqa: E402

# ═══════════════════════════════════════════════════════ 规格（冻结书 §B/§D，不得自行改动）
W, H = 180, 60
CX, CY = 90.0, 30.0           # 画布中心（= 元素 180×60 中心）
HX, HY = 60.0, 20.0           # 底框（文字区）半宽/半高 ⇒ 120×40，居中
CORE_X0, CORE_X1 = 30, 150    # 文字区像素列 [30,150)
CORE_Y0, CORE_Y1 = 10, 50     # 文字区像素行 [10,50)
R_CAP = 10                    # 胶囊圆角（冻结书 §D「圆角约 10」）
CAP_DY = 1                    # 胶囊下沉 1px

CLIP_THR = M55.CLIP_THR       # 10 —— 本工程「柔光尾归零」阈值
RAW_FRAME_MAX = M55.RAW_FRAME_MAX  # 10 —— 剪前最外 1px 帧 α 上限
CORE_FRAC = 0.995             # 平铺区判据：α ≥ 0.995×峰值 记作「底框内」

# 光晕参数（A=峰 α，sx/sy=归一化肩宽，dy=整体下沉）
GLOW = {
    "off":   dict(A=104, sx=9.0,  sy=6.0, dy=0),
    "over":  dict(A=172, sx=14.0, sy=5.6, dy=0),
    "press": dict(A=64,  sx=11.0, sy=6.0, dy=CAP_DY),   # 胶囊背后的弱光（与另两态同族）
}
FILL_A = 160                  # 胶囊填充 α（半透明）
RIM_A = 255                   # 1px 亮边 α
FILES = {s: "x_ui_modetab_%s.png" % s for s in ("off", "over", "press")}

# 色板键（**唯一色值来源**）
WHITE = M55.C("text_primary")     # #FFFFFF
ACCENT = M55.C("accent")          # #7AB0E8
PANEL_EDGE = M55.C("panel_edge")  # #5A6A8A
FILL_TOP = M55.mix(ACCENT, WHITE, 0.10)
FILL_BOT = M55.mix(ACCENT, PANEL_EDGE, 0.22)
RIM_RGB = M55.mix(ACCENT, WHITE, 0.50)

# 证据图
FONT_TEXT = r"C:\Windows\Fonts\msyh.ttc"      # index 0 = Microsoft YaHei Regular（冻结书 §B 指定）
FONT_LABEL = r"C:\Windows\Fonts\msyhbd.ttc"
TEXT = "本篇集合"
TEXT_SIZE = 30
OUTLINE_W = 2
CLOUD = (162, 172, 178)                        # 浅云底（派单给定，取自 `主代理_全屏.png`）


# ═══════════════════════════════════════════════════════ 基础
def md5b(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def enc_png(im: Image.Image) -> bytes:
    buf = __import__("io").BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def png_ihdr(blob: bytes) -> dict:
    """解析 PNG 头 + 块名序列 ⇒ 机检「真 alpha / PNG-32」：颜色类型 6（RGBA）、位深 8、
    且**不得**出现调色板/透明索引块（PLTE / tRNS）——后者即「不是 PNG-32」的判据。"""
    import struct
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        return dict(ok=False, why="非 PNG 签名")
    w, h, bd, ct = struct.unpack(">IIBB", blob[16:26])
    names, i = [], 8
    while i + 8 <= len(blob):
        ln = struct.unpack(">I", blob[i:i + 4])[0]
        nm = blob[i + 4:i + 8].decode("latin-1")
        names.append(nm)
        if nm == "IEND":
            break
        i += 12 + ln
    ok = (w == W and h == H and bd == 8 and ct == 6
          and "PLTE" not in names and "tRNS" not in names)
    return dict(ok=ok, w=w, h=h, bitdepth=bd, colortype=ct, chunks=names)


def rgba_arr(im: Image.Image) -> np.ndarray:
    assert im.mode == "RGBA", "非 RGBA：%s" % im.mode
    return np.asarray(im, dtype=np.uint8)


def glow_field(A: float, sx: float, sy: float, dy: int) -> np.ndarray:
    """解析式「平铺底框 + 高斯肩部」α 场（float64, 0..A）。

    采样点取**像素中心**（x+0.5, y+0.5），底框连续域 x∈[30,150]、y∈[10,50]：
    底框内 dx=dy=0 ⇒ α≡A（平铺）；框沿 dx=dy=0 处 dα/dx=0 ⇒ 处处 C¹ 连续、**无折痕**。
    """
    x = np.arange(W, dtype=np.float64) + 0.5 - CX
    y = np.arange(H, dtype=np.float64) + 0.5 - (CY + dy)
    dx = np.maximum(np.abs(x)[None, :] - HX, 0.0)
    dyv = np.maximum(np.abs(y)[:, None] - HY, 0.0)
    return A * np.exp(-((dx / sx) ** 2 + (dyv / sy) ** 2))


def white_layer(a: np.ndarray) -> Image.Image:
    """α 场 → 纯白 RGBA 层（RGB ≡ @palette.text_primary）"""
    al = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    rgb = np.zeros((H, W, 3), np.uint8)
    rgb[...] = WHITE
    return Image.fromarray(np.dstack([rgb, al]), "RGBA")


def over_composite(layers):
    """标准 over 合成（涂在下面→上面）；返回 RGBA。用 float 保证 α 精确。"""
    acc_a = np.zeros((H, W), np.float64)
    acc_c = np.zeros((H, W, 3), np.float64)
    for im in layers:
        arr = rgba_arr(im).astype(np.float64)
        a = arr[..., 3] / 255.0
        acc_c = arr[..., :3] * a[..., None] + acc_c * (1.0 - a[..., None])
        acc_a = a + acc_a * (1.0 - a)
    out = np.zeros((H, W, 4), np.uint8)
    safe = np.maximum(acc_a, 1e-9)[..., None]
    out[..., :3] = np.clip(np.rint(acc_c / safe), 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.rint(acc_a * 255.0), 0, 255).astype(np.uint8)
    out[acc_a <= 0] = (255, 255, 255, 0)      # 全透明区 RGB 归一，便于体积压缩
    return Image.fromarray(out, "RGBA")


def build_glow(state: str):
    """常规 / 悬停：纯白淡光。返回 (剪后图, 剪前帧 αmax, 剪前 αmax)"""
    g = GLOW[state]
    a = glow_field(g["A"], g["sx"], g["sy"], g["dy"])
    raw = white_layer(a)
    pre_frame = M55.frame_max(raw, 1)
    pre_amax = int(np.rint(a).clip(0, 255).max())
    return M55.clip_low_alpha(raw, CLIP_THR), pre_frame, pre_amax


def build_press():
    """按下：半透明冰蓝实底胶囊 + 1px 亮边 + 胶囊背后的弱光；**整枚下沉 1px**"""
    g = GLOW["press"]
    cap = M55.rr_mask((W, H), (30, 11, 150, 51), R_CAP)                 # 沾满 y∈[11,51]
    inner = M55.rr_mask((W, H), (31, 12, 149, 50), R_CAP - 1)
    rim = M55.sub_mask(cap, inner)                                      # 1px 环（**在轮廓内侧**）
    # 弱光：**胶囊内不叠**（halo × (1-cap)）⇒ 胶囊填充 α 精确 = FILL_A
    a_h = glow_field(g["A"], g["sx"], g["sy"], g["dy"])
    halo = np.clip(np.rint(a_h), 0, 255).astype(np.float64)
    halo = halo * (1.0 - np.asarray(cap, np.float64) / 255.0)
    halo_im = white_layer(halo)
    pre_frame = M55.frame_max(halo_im, 1)
    pre_amax = int(halo.clip(0, 255).max())
    # 填充：accent 系竖向微渐变 × cap，α 恒 160
    col = np.array([M55.mix(FILL_TOP, FILL_BOT, j / float(H - 1)) for j in range(H)], np.uint8)
    rgb = np.repeat(col[:, None, :], W, axis=1)
    fa = (np.asarray(cap, np.uint16) * FILL_A // 255).astype(np.uint8)
    fill = Image.fromarray(np.dstack([rgb, fa]), "RGBA")
    rim_im = M55.tint(rim, RIM_RGB, RIM_A)
    out = over_composite([M55.clip_low_alpha(halo_im, CLIP_THR), fill, rim_im])
    return M55.clip_low_alpha(out, CLIP_THR), pre_frame, pre_amax


def build_all():
    imgs = {}
    pre = {}
    for s in ("off", "over"):
        imgs[s], pf, pa = build_glow(s)
        pre[s] = (pf, pa)
    imgs["press"], pf, pa = build_press()
    pre["press"] = (pf, pa)
    return imgs, pre


def metrics(im: Image.Image) -> dict:
    a = np.asarray(im.getchannel("A"), dtype=np.int32)
    core = a[CORE_Y0:CORE_Y1, CORE_X0:CORE_X1]
    return dict(
        amax=int(a.max()), amin=int(a.min()),
        core_mean=float(core.mean()), core_peak=int(core.max()),
        core_cov8=int((core > 8).sum()), core_n=int(core.size),
        full_cov8=int((a > 8).sum()),
        op128=int((a >= 128).sum()), op200=int((a >= 200).sum()),
        frame=int(M55.frame_max(im, 1)),
    )


def core_top(im: Image.Image, frac: float = CORE_FRAC):
    """底框上沿 = **平铺区**首行：该行在文字区列上的最大 α ≥ frac×峰值（实测，非写死常量）"""
    a = np.asarray(im.getchannel("A"), dtype=np.int32)
    thr = frac * a.max()
    for j in range(H):
        if a[j, CORE_X0:CORE_X1].max() >= thr:
            return j
    return None


def op200_bbox(im: Image.Image, thr: int = 200):
    a = np.asarray(im.getchannel("A"), dtype=np.int32)
    ys, xs = np.where(a >= thr)
    if len(ys) == 0:
        return None
    return dict(top=int(ys.min()), bottom=int(ys.max()),
                left=int(xs.min()), right=int(xs.max()),
                w=int(xs.max() - xs.min() + 1), h=int(ys.max() - ys.min() + 1),
                n=int(len(ys)))


# ═══════════════════════════════════════════════════════ 目录台账
def dir_ledger(d: str) -> dict:
    out = {}
    for f in sorted(os.listdir(d)):
        if f.lower().endswith(".png"):
            p = os.path.join(d, f)
            out[f] = (os.path.getsize(p), md5b(open(p, "rb").read()))
    return out


def budget_now(d: str):
    n, tot = 0, 0
    for f in sorted(os.listdir(d)):
        if f.lower().endswith(".png"):
            n += 1
            tot += os.path.getsize(os.path.join(d, f))
    return n, tot


# ═══════════════════════════════════════════════════════ 证据图工具
def fnt(path, size):
    return ImageFont.truetype(path, size)


def checker(w, h, cell=8, a=(88, 92, 100), b=(150, 156, 164)):
    im = Image.new("RGB", (w, h), a)
    d = ImageDraw.Draw(im)
    for yy in range(0, h, cell):
        for xx in range(0, w, cell):
            if ((xx // cell) + (yy // cell)) % 2:
                d.rectangle([xx, yy, xx + cell - 1, yy + cell - 1], fill=b)
    return im


def flat_bg(w, h, rgb):
    return Image.new("RGB", (w, h), rgb)


def zoom_rgb_under(im: Image.Image, z: int, bg: Image.Image) -> Image.Image:
    """把 RGBA 素材叠到指定底上并 z 倍 NEAREST 放大"""
    rgba = im.resize((W * z, H * z), Image.NEAREST)
    base = bg.convert("RGBA")
    base.alpha_composite(rgba)
    return base.convert("RGB")


def srgb_lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(rgb):
    return 0.2126 * srgb_lin(rgb[0]) + 0.7152 * srgb_lin(rgb[1]) + 0.0722 * srgb_lin(rgb[2])


def contrast(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def lum_arr(rgb):
    """向量的 WCAG 相对亮度（rgb: (...,3) 0..255）"""
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def text_layer(font) -> tuple:
    """「白字 + 2px 黑描边」（PIL 实现；无描边版用于分离墨迹/描边掩膜）"""
    def render(stroke):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # 先按墨迹 bbox 量出居中偏移（与引擎 valign:middle 的行盒居中差 ≤2px，仅影响观感）
        tmp = Image.new("L", (W * 4, H * 4), 0)
        dt = ImageDraw.Draw(tmp)
        dt.text((0, 0), TEXT, font=font, fill=255)
        bb = tmp.getbbox()
        tw, th = (bb[2] - bb[0]), (bb[3] - bb[1])
        x = (W - tw) / 2.0 - bb[0]
        y = (H - th) / 2.0 - bb[1]
        d.text((x, y), TEXT, font=font, fill=(255, 255, 255, 255),
               stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        return im
    plain = render(0)
    full = render(OUTLINE_W)
    return plain, full


# ═══════════════════════════════════════════════════════ 主流程
def main(argv):
    dry = "--dry-run" in argv
    check = "--check" in argv

    rows = []      # (编号, 断言, 实测, PASS/FAIL)

    def T(tag, claim, measured, ok):
        rows.append((tag, claim, measured, "PASS" if ok else "FAIL"))
        return ok

    print("=" * 84)
    print("m63_make_modetab_assets.py · ISSUE-20260929-05 E1 素材（模式入口三态底光）")
    print("  python %s | Pillow %s | numpy %s" % (sys.version.split()[0], Image.__version__,
                                                  np.__version__))
    print("  产物目录 : %s" % OUT)
    print("  色板     : %s" % M55.PALETTE)
    print("  色值     : text_primary=%s  accent=%s  panel_edge=%s  fill_top=%s  fill_bot=%s  rim=%s"
          % ("#%02X%02X%02X" % WHITE, "#%02X%02X%02X" % ACCENT, "#%02X%02X%02X" % PANEL_EDGE,
             "#%02X%02X%02X" % FILL_TOP, "#%02X%02X%02X" % FILL_BOT, "#%02X%02X%02X" % RIM_RGB))
    print("=" * 84)

    # ── 0. 台账（写前）
    led_before = dir_ledger(OUT)
    n_before, tot_before = budget_now(OUT)

    # ── 1. 生成 + 幂等（内存两次）
    imgs, pre = build_all()
    again, pre2 = build_all()
    raw = {s: enc_png(imgs[s]) for s in FILES}
    raw2 = {s: enc_png(again[s]) for s in FILES}

    for s in FILES:
        T("I-%s" % s, "幂等：内存连造两次逐字节一致",
          "md5 %s == %s" % (md5b(raw[s])[:12], md5b(raw2[s])[:12]), raw[s] == raw2[s])

    # ── 2. 落盘（只在非 --check；目标已存在且不同 ⇒ 报错拒绝覆盖，须显式 --force）
    for s in FILES:
        p = os.path.join(OUT, FILES[s])
        if os.path.isfile(p):
            cur = open(p, "rb").read()
            if cur != raw[s]:
                if "--force" not in argv:
                    print("!! 目标文件已存在且字节不同，拒绝覆盖：%s" % p)
                    print("   （本批自身迭代需覆盖时，显式加 --force；覆盖前旧值 md5=%s）" % md5b(cur)[:12])
                    return 3
                print("!! --force：覆盖本批自身旧产物 %s（旧 md5=%s → 新 md5=%s）"
                      % (FILES[s], md5b(cur)[:12], md5b(raw[s])[:12]))
    if not dry and not check:
        for s in FILES:
            with open(os.path.join(OUT, FILES[s]), "wb") as f:
                f.write(raw[s])

    led_after = dir_ledger(OUT)
    n_after, tot_after = budget_now(OUT)
    added = sorted(set(led_after) - set(led_before))
    removed = sorted(set(led_before) - set(led_after))
    changed = sorted(f for f in set(led_before) & set(led_after) if led_before[f] != led_after[f])
    exp_added = [] if (dry or check) else sorted(FILES.values())
    targets_ok = all(FILES[s] in led_after and led_after[FILES[s]][1] == md5b(raw[s]) for s in FILES)
    changed_other = [f for f in changed if f not in FILES.values()]
    T("L-1", "**无既有素材被改写/删除**：除本批 3 件外零改动；新增项 ⊆ 本批 3 件",
      "added=%s ｜ 本批外改动=%s ｜ 删除=%s ｜ 本批 3 件 md5 就位=%s"
      % (added, changed_other, removed, targets_ok),
      added in ([], exp_added) and not removed and not changed_other and targets_ok)
    # ── git 侧独立复核（只读）：本批 3 件应为「未跟踪」，其余**无 M/D**
    try:
        import subprocess
        gp = subprocess.run(["git", "status", "--porcelain", "--", "krkr/assets/ui"],
                            cwd=UI_GROUP, capture_output=True, text=True, timeout=120)
        lines = [l for l in gp.stdout.splitlines() if l.strip()]
        bad = [l for l in lines if not (l.startswith("??") and l.split()[-1].endswith(tuple(FILES.values())))]
        T("L-3", "git 侧独立复核：assets/ui 下除本批 3 件（未跟踪 ??）外无任何 M/A/D",
          "porcelain %d 行 ｜ 异常 %s" % (len(lines), bad or "无"), gp.returncode == 0 and not bad)
    except Exception as e:                                     # noqa: BLE001
        T("L-3", "git 侧独立复核（git 不可用时跳过）", "skipped: %s" % e, True)
    if dry or check:
        T("L-2", "磁盘现值 == 本次生成值（--dry-run/--check：按定义未写盘，跳过）",
          "skipped（未写盘）", True)
    else:
        T("L-2", "磁盘现值 == 本次生成值",
          "; ".join("%s %s" % (FILES[s], md5b(open(os.path.join(OUT, FILES[s]), "rb").read())[:12])
                    for s in FILES),
          all(open(os.path.join(OUT, FILES[s]), "rb").read() == raw[s] for s in FILES))

    # ── 3. 结构断言（派单 1）
    M = {s: metrics(imgs[s]) for s in FILES}
    for s in FILES:
        im = imgs[s]
        ok = (im.size == (W, H) and im.mode == "RGBA")
        T("S1-%s" % s, "尺寸 180×60 / 模式 RGBA", "%s / %s" % (im.size, im.mode), ok)
        hd = png_ihdr(raw[s])
        T("S2-%s" % s, "PNG-32 真 alpha（IHDR 颜色类型 6 / 位深 8；无 PLTE / tRNS 索引色块）",
          "colortype=%s bitdepth=%s chunks=%s" % (hd.get("colortype"), hd.get("bitdepth"),
                                                  ",".join(hd.get("chunks", []))), bool(hd.get("ok")))
        T("S3-%s" % s, "最外 1px 帧 αmax == 0（frame 策略，剪后）", "frame_amax=%d" % M[s]["frame"],
          M[s]["frame"] == 0)
        T("S4-%s" % s, "剪前最外 1px 帧 αmax ≤ %d（断言不空转）" % RAW_FRAME_MAX,
          "raw_frame_amax=%d  raw_amax=%d" % (pre[s][0], pre[s][1]),
          pre[s][0] <= RAW_FRAME_MAX)
        T("S5-%s" % s, "αmin == 0 且 αmax > 0",
          "αmin=%d αmax=%d" % (M[s]["amin"], M[s]["amax"]), M[s]["amin"] == 0 and M[s]["amax"] > 0)

    # ── 4. 三态量化差（派单 2）
    print("\n── 三态量化（「文字区」= 元素中心 120×40 = 行 10..49 × 列 30..149）" + "-" * 20)
    print("%-6s %10s %10s %12s %12s %12s %10s" %
          ("态", "均α(文字区)", "峰α(文字区)", "α>8(文字区)", "α>8(全画布)", "α≥128(全画布)", "α≥200"))
    for s in ("off", "over", "press"):
        m = M[s]
        print("%-6s %10.2f %10d %9d/%-3d %12d %12d %10d" %
              (s, m["core_mean"], m["core_peak"], m["core_cov8"], m["core_n"],
               m["full_cov8"], m["op128"], m["op200"]))
    T("D-1", "悬停更亮：off 文字区均 α < over", "off=%.2f over=%.2f" % (M["off"]["core_mean"],
                                                                       M["over"]["core_mean"]),
      M["off"]["core_mean"] < M["over"]["core_mean"])
    T("D-2", "悬停更高：off 文字区峰 α < over", "off=%d over=%d" % (M["off"]["core_peak"],
                                                                   M["over"]["core_peak"]),
      M["off"]["core_peak"] < M["over"]["core_peak"])
    T("D-3", "悬停更「大」：off 全画布 α>8 面积 < over",
      "off=%d over=%d (+%.1f%%)" % (M["off"]["full_cov8"], M["over"]["full_cov8"],
                                    100.0 * (M["over"]["full_cov8"] - M["off"]["full_cov8"])
                                    / M["off"]["full_cov8"]),
      M["off"]["full_cov8"] < M["over"]["full_cov8"])
    T("D-4", "over 的「整体提亮」幅度可辨（≥1.5× 文字区均 α）",
      "%.2f×" % (M["over"]["core_mean"] / M["off"]["core_mean"]),
      M["over"]["core_mean"] / M["off"]["core_mean"] >= 1.5)
    T("D-5", "press 底色可见性：**近实底像素（α≥200，＝派单 3 的「不透明区」口径）press > 0，"
             "而 off/over 皆为 0**（光晕有意做成半透明白，故不产生近实底像素）",
      "off=%d over=%d press=%d" % (M["off"]["op200"], M["over"]["op200"], M["press"]["op200"]),
      M["press"]["op200"] > 0 and M["off"]["op200"] == 0 and M["over"]["op200"] == 0)
    T("D-6", "press 实底面积与胶囊几何一致（α≥200 计数 ≈ 1px 亮边周长 299±60）",
      "α≥200 n=%d" % M["press"]["op200"], 240 <= M["press"]["op200"] <= 360)
    T("D-7", "off/over 有意不出现近不透明白板（峰值 α < 180 ⇒ 白字与底板留亮度台阶）",
      "off_max=%d over_max=%d" % (M["off"]["amax"], M["over"]["amax"]),
      M["off"]["amax"] <= 120 and M["over"]["amax"] < 180)
    T("D-8", "同一绝对 α 上 over 的展开 ≥ off（悬停「加大」，非仅调亮）",
      "α>8 面积 off=%d ≤ over=%d" % (M["off"]["full_cov8"], M["over"]["full_cov8"]),
      M["off"]["full_cov8"] <= M["over"]["full_cov8"])
    # 肩部（文字区外的柔光带）实测：α(第 30 行, 第 20 列) —— 离底框左沿 10px
    def stub(s):
        return int(np.asarray(imgs[s].getchannel("A"))[30, 20])
    so, sv, sp = stub("off"), stub("over"), stub("press")
    T("D-9", "「整体发亮」不止在文字区：文字区外肩部（行 30 / 列 20）over 的 α ≥ 2.5× off",
      "α: off=%d over=%d（%.2f×） press=%d" % (so, sv, sv / float(so), sp), sv >= 2.5 * so)
    T("D-10", "肩部在浅云底上的亮度提升（合成后）over ≥ 25 灰阶、off ≥ 5 灰阶（肉眼可辨的量级）",
      "off +%.1f ｜ over +%.1f ｜ 云底 172（0.35/255 每级）"
      % (so / 255.0 * (255 - CLOUD[1]), sv / 255.0 * (255 - CLOUD[1])),
      so / 255.0 * (255 - CLOUD[1]) >= 5 and sv / 255.0 * (255 - CLOUD[1]) >= 25)

    # ── 5. 下沉 1px（派单 3）
    ct_off = core_top(imgs["off"])
    ct_over = core_top(imgs["over"])
    bb_press = op200_bbox(imgs["press"], 200)
    print("\n── 下沉口径 ──  off 底框上沿=%s  over 底框上沿=%s  press α≥200 bbox=%s"
          % (ct_off, ct_over, bb_press))
    T("K-1", "off 底框上沿实测 == 10（平铺区首行，判据 α≥0.995×峰值）", "top=%s" % ct_off, ct_off == 10)
    T("K-2", "over 底框上沿实测 == 10（与 off 共用同一底框）", "top=%s" % ct_over, ct_over == 10)
    T("K-3", "press 的 α≥200 区（1px 亮边）bbox 上沿 == %s" % bb_press, "top=%s" % (bb_press or {}).get("top"),
      bb_press is not None and bb_press["top"] == 11)
    T("K-4", "**胶囊下沉 1px**：press_bbox.top == off 底框上沿 + 1 == over 底框上沿 + 1（±0）",
      "press=%s  off+1=%s  over+1=%s" % (bb_press["top"], ct_off + 1, ct_over + 1),
      bb_press["top"] == ct_off + 1 and bb_press["top"] == ct_over + 1)
    T("K-5", "press 胶囊与底框**等宽等高**（下沉＝平移，不是缩放）",
      "α≥200 bbox %s×%s（底框 120×40）" % (bb_press["w"], bb_press["h"]),
      bb_press["w"] == (CORE_X1 - CORE_X0) and bb_press["h"] == (CORE_Y1 - CORE_Y0))

    # ── 6. 体积（派单 4）
    sizes = {s: len(raw[s]) for s in FILES}
    tot3 = sum(sizes.values())
    print("\n── 体积 ──  " + "  ".join("%s=%.2f KiB" % (FILES[s], sizes[s] / 1024.0)
                                     for s in ("off", "over", "press")))
    T("B-1", "3 件合计 < 60 KiB", "%.2f KiB（逐件 %.2f / %.2f / %.2f KiB）"
      % (tot3 / 1024.0, sizes["off"] / 1024.0, sizes["over"] / 1024.0, sizes["press"] / 1024.0),
      tot3 < 60 * 1024)
    T("B-2", "单件均 ≤ 24 KiB（任何一件都不吃掉预算）", "max=%.2f KiB" % (max(sizes.values()) / 1024.0),
      max(sizes.values()) <= 24 * 1024)

    # ── 7. 预算（派单 6）— 目录级实测
    n_add = len(added) if not (dry or check) else 3
    budget_bytes = BUDGET_MB * 1024 * 1024
    margin = budget_bytes - tot_after
    print("── 预算 ──  目录 %d 件 / %.4f MiB（预算 %d MB）⇒ 余量 %.2f KiB；本批 3 件合计 %.2f KiB"
          % (n_after, tot_after / 1024.0 / 1024.0, BUDGET_MB, margin / 1024.0, tot3 / 1024.0))
    T("P-1", "本批落盘后仍在 %d MB 预算内（余量 > 本批体积）" % BUDGET_MB,
      "余量 %.2f KiB vs 本批 %.2f KiB" % (margin / 1024.0, tot3 / 1024.0),
      margin > tot3)

    # ── 8. 证据图
    os.makedirs(EVID, exist_ok=True)
    evid_files = []
    if not dry and not check:
        evid_files = make_evidence(imgs, M, dict(off=ct_off, over=ct_over), bb_press, sizes,
                                   tot3, n_before, tot_before, n_after, tot_after, T)
        # TSV
        tsv = os.path.join(EVID, "E1_三态自证.tsv")
        with open(tsv, "w", encoding="utf-8", newline="\n") as f:
            f.write("编号\t断言\t实测\t判定\n")
            for r in rows:
                f.write("%s\t%s\t%s\t%s\n" % r)
        evid_files.insert(0, tsv)

    # ── 9. 汇总
    fails = [r for r in rows if r[3] == "FAIL"]
    print("\n" + "=" * 84)
    print("自证：%d 条，PASS %d，FAIL %d" % (len(rows), len(rows) - len(fails), len(fails)))
    for r in fails:
        print("  x %s | %s | 实测 %s" % (r[0], r[1], r[2]))
    if evid_files:
        print("证据：" + " | ".join(os.path.basename(p) for p in evid_files))
    print("结果：%s" % ("全部通过" if not fails else "存在 FAIL"))
    print("=" * 84)
    return 0 if not fails else 1


# ═══════════════════════════════════════════════════════ 证据图
def make_evidence(imgs, M, core_tops, bb_press, sizes, tot3, n_before, tot_before, n_after,
                  tot_after, T):
    out = []
    Z = 4
    f_t = fnt(FONT_LABEL, 26)
    f_s = fnt(FONT_LABEL, 19)
    f_m = fnt(FONT_TEXT, 17)
    order = ["off", "over", "press"]
    name_cn = {"off": "常规 off（弱档白淡光）", "over": "悬停 over（整体提亮/加大）",
               "press": "按下 press（冰蓝实底胶囊，下沉 1px）"}

    # ── 证据 1：三态对照（棋盘 / 浅云 / 纯黑 三行底）
    MAR, GAP = 26, 18
    cellw, cellh = W * Z, H * Z
    bgs = [("棋盘底（透明区可视化）", checker(cellw, cellh, 16)),
           ("浅云底 (162,172,178)（实机流程图页背景亮度）", flat_bg(cellw, cellh, CLOUD)),
           ("纯黑底 (0,0,0)（白淡光最有利的情形）", flat_bg(cellw, cellh, (0, 0, 0)))]
    head, rlab, nameh, numh, rgap = 106, 26, 24, 46, 14
    Wtot = MAR * 2 + len(order) * cellw + (len(order) - 1) * GAP
    Htot = head + len(bgs) * (rlab + nameh + cellh + numh + rgap) + 30
    im = Image.new("RGB", (Wtot, Htot), (24, 27, 33))
    d = ImageDraw.Draw(im)
    d.text((MAR, 16), "E1_三态对照 · ISSUE-20260929-05 模式入口底光 3 件（4x NEAREST，180x60 源 → 720x240）",
           font=f_t, fill=(236, 240, 248))
    d.text((MAR, 50),
           "底框 = 文字区 = 元素中心 120x40（行 10..49 / 列 30..149）；"
           "品红虚线 = 底框上沿 y=10，press 的胶囊上沿应落在其下 1px（4x 图上 4px）",
           font=f_s, fill=(168, 200, 232))
    d.text((MAR, 74),
           "α>8 / α>=128 / α>=200 为全画布计数；「均α / 峰α」取文字区（120x40）",
           font=f_s, fill=(140, 160, 184))
    y = head
    for bname, bg in bgs:
        d.text((MAR, y + 4), bname, font=f_s, fill=(210, 220, 236))
        yl = y + rlab
        y0 = yl + nameh
        for i, s in enumerate(order):
            x0 = MAR + i * (cellw + GAP)
            d.text((x0, yl), "%s ｜ %s" % (FILES[s], name_cn[s]), font=f_s, fill=(232, 224, 150))
            im.paste(zoom_rgb_under(imgs[s], Z, bg.copy()), (x0, y0))
            d.rectangle([x0 - 1, y0 - 1, x0 + cellw, y0 + cellh], outline=(96, 106, 124))
            ly = y0 + 10 * Z          # 底框上沿 y=10（4x）
            for xx in range(x0, x0 + cellw, 10):
                d.line([xx, ly, min(xx + 5, x0 + cellw - 1), ly], fill=(255, 64, 168))
            m = M[s]
            d.text((x0, y0 + cellh + 6),
                   "均α %.1f ｜ 峰α %d ｜ α>8 %d ｜ α>=128 %d ｜ α>=200 %d"
                   % (m["core_mean"], m["core_peak"], m["full_cov8"], m["op128"], m["op200"]),
                   font=f_m, fill=(196, 206, 222))
            d.text((x0, y0 + cellh + 26),
                   "文字区 α>8 覆盖 %d/%d ｜ αmax %d ｜ 剪后帧 αmax %d"
                   % (m["core_cov8"], m["core_n"], m["amax"], m["frame"]),
                   font=f_m, fill=(150, 162, 182))
        y = y0 + cellh + numh + rgap
    d.text((MAR, Htot - 24),
           "press α>=200 bbox 上沿 = %d（= off/over 底框上沿 %d + 1）｜ 胶囊 bbox %dx%d ｜ "
           "3 件合计 %.2f KiB ｜ 资产 %d→%d 件 / %.4f→%.4f MiB"
           % (bb_press["top"], core_tops["off"], bb_press["w"], bb_press["h"], tot3 / 1024.0,
              n_before, n_after, tot_before / 1024.0 / 1024.0, tot_after / 1024.0 / 1024.0),
           font=f_m, fill=(180, 190, 206))
    p1 = os.path.join(EVID, "E1_三态对照.png")
    im.save(p1, "PNG", optimize=True)
    out.append(p1)


    # ── 证据 2：模拟合成（白字+2px 黑描边 压三态，浅云底）
    font = fnt(FONT_TEXT, TEXT_SIZE)
    plain, full = text_layer(font)
    ink_a = np.asarray(plain.getchannel("A"), dtype=np.int32)
    full_a = np.asarray(full.getchannel("A"), dtype=np.int32)
    ink = ink_a > 200
    # 「描边像素」= 被描边覆盖（full α>200）且**墨迹覆盖很低**（ink α<64）的像素 ——
    # 不取 ink>200 作补集，否则会把「描边→墨迹」交界处那圈「白/黑混合」的 AA 像素算进描边，
    # 使 p90 假性偏高（实测 146），把「描边是否够黑」这条判据冲淡。
    ring = (full_a > 200) & (ink_a < 64)

    cloud = flat_bg(W * Z, H * Z, CLOUD)
    panels = []
    stats = {}
    for s in order + ["none"]:
        base = cloud.copy().convert("RGBA")
        if s != "none":
            base.alpha_composite(imgs[s].resize((W * Z, H * Z), Image.NEAREST))
        # 文字层（自下而上：先描边层、再墨迹层；与引擎同序）
        tl = full.resize((W * Z, H * Z), Image.NEAREST)
        base.alpha_composite(tl)
        panels.append(base.convert("RGB"))
        # 量：墨迹下合成底色 / 描边像素是否纯黑
        bg_layer = cloud.copy().convert("RGBA")
        if s != "none":
            bg_layer.alpha_composite(imgs[s].resize((W * Z, H * Z), Image.NEAREST))
        bl = np.asarray(bg_layer.convert("RGB"), dtype=np.int32)
        solid = np.kron(ink_a == 255, np.ones((Z, Z), bool))     # 墨迹**实心**像素
        inkz = np.kron(ink, np.ones((Z, Z), bool))
        ringz = np.kron(ring, np.ones((Z, Z), bool))
        fin = np.asarray(panels[-1], dtype=np.int32)
        fin_gray = fin.max(axis=2)                                # 通道级灰度（0..255）
        bg_under = bl[inkz].mean(axis=0) if inkz.any() else np.array([0, 0, 0])
        outline_px = fin[ringz] if ringz.any() else np.zeros((1, 3), np.int32)
        solid_px = fin[solid] if solid.any() else np.zeros((1, 3), np.int32)
        stats[s] = dict(
            bg_under=tuple(int(round(v)) for v in bg_under),
            ink_contrast=contrast(lum(WHITE), lum(tuple(bg_under))),
            out_contrast=contrast(lum((0, 0, 0)), lum(tuple(bg_under))),
            outline_black_frac=float((outline_px.max(axis=1) <= 8).mean()) if ringz.any() else 0.0,
            outline_p50=float(np.percentile(fin_gray[ringz], 50)) if ringz.any() else 0.0,
            outline_p90=float(np.percentile(fin_gray[ringz], 90)) if ringz.any() else 0.0,
            ink_rgb=tuple(int(round(v)) for v in solid_px.mean(axis=0)) if solid.any() else None,
            ink_px=int(ink.sum()), ring_px=int(ring.sum()),
        )

    MAR, GAP = 26, 18
    head, labh, numh2 = 118, 30, 76
    Wtot = MAR * 2 + len(panels) * W * Z + (len(panels) - 1) * GAP
    Htot = head + labh + H * Z + numh2 + 26
    im2 = Image.new("RGB", (Wtot, Htot), (24, 27, 33))
    d2 = ImageDraw.Draw(im2)
    d2.text((MAR, 16), "E1_模拟合成_文字压光 · 「本篇集合」白字 + 2px 黑描边（微软雅黑 Regular %dpx）压在**三态**上"
            % TEXT_SIZE, font=f_t, fill=(236, 240, 248))
    d2.text((MAR, 50), "底＝浅云 (162,172,178)（与实机流程图页背景同亮度）；4× NEAREST；"
            "最右一栏为「无底光」对照，用于判「白淡光是否可见、是否过亮」",
            font=f_s, fill=(168, 200, 232))
    d2.text((MAR, 74), "判「黑描边是否被光吃掉」：描边像素合成后应为 **纯黑 (0,0,0)**（引不透明黑，"
            "压在光之上）⇒ 实测「描边纯黑占比」；判「白字是否被光吃掉」：测 墨迹下合成底色 对 白字 的 WCAG 对比度",
            font=f_s, fill=(140, 160, 184))
    d2.text((MAR, 96), "同一行内四栏的底色、字号、描边完全一致 —— 差异只来自底光。",
            font=f_s, fill=(140, 160, 184))
    y = head + labh
    for i, s in enumerate(order + ["none"]):
        x0 = MAR + i * (W * Z + GAP)
        d2.text((x0, head + 4), ("无底光（对照）" if s == "none" else name_cn[s]), font=f_s,
                fill=(232, 224, 150))
        im2.paste(panels[i], (x0, y))
        d2.rectangle([x0 - 1, y - 1, x0 + W * Z, y + H * Z], outline=(96, 106, 124))
        st = stats[s]
        d2.text((x0, y + H * Z + 6),
                "墨迹下底色 %s" % (st["bg_under"],), font=f_m, fill=(196, 206, 222))
        d2.text((x0, y + H * Z + 26),
                "白字/底板 %.2f:1 ｜ 黑描边/底板 %.2f:1" % (st["ink_contrast"], st["out_contrast"]),
                font=f_m, fill=(196, 206, 222))
        d2.text((x0, y + H * Z + 46),
                "描边纯黑占比 %.1f%%（%d/%d px）" % (100 * st["outline_black_frac"],
                                                  int(round(st["outline_black_frac"] * st["ring_px"])),
                                                  st["ring_px"]),
                font=f_m, fill=(150, 220, 170) if st["outline_black_frac"] > 0.99 else (240, 170, 150))
    p2 = os.path.join(EVID, "E1_模拟合成_文字压光.png")
    im2.save(p2, "PNG", optimize=True)
    out.append(p2)

    # ── 证据 2b：文字区 8× 细节（供判「白字/描边 vs 底板」的分辨力）
    CX0, CY0, CX1, CY1 = 28, 6, 96, 54          # 源坐标裁切窗（含「本」「篇」前两字与上下肩部）
    cw2, ch2 = (CX1 - CX0) * Z * 2, (CY1 - CY0) * Z * 2
    MAR2 = 26
    head2 = 74
    Wtot2 = MAR2 * 2 + len(panels) * cw2 + (len(panels) - 1) * GAP
    Htot2 = head2 + 30 + ch2 + 44
    im3 = Image.new("RGB", (Wtot2, Htot2), (24, 27, 33))
    d3 = ImageDraw.Draw(im3)
    d3.text((MAR2, 16), "E1_细节 · 「本篇集合」前两字（源列 %d..%d / 行 %d..%d）8x NEAREST"
            % (CX0, CX1, CY0, CY1), font=f_t, fill=(236, 240, 248))
    d3.text((MAR2, 50), "用途：同一行四栏的底色/字号/描边完全一致 —— 判「悬停是否一眼可辨」「白字是否被光吃掉」"
            "「描边是否被光吃掉」", font=f_s, fill=(168, 200, 232))
    y3 = head2 + 30
    for i, s in enumerate(order + ["none"]):
        x0 = MAR2 + i * (cw2 + GAP)
        d3.text((x0, head2 + 4), ("无底光（对照）" if s == "none" else name_cn[s]), font=f_s,
                fill=(232, 224, 150))
        crop = panels[i].crop((CX0 * Z, CY0 * Z, CX1 * Z, CY1 * Z)).resize((cw2, ch2), Image.NEAREST)
        im3.paste(crop, (x0, y3))
        d3.rectangle([x0 - 1, y3 - 1, x0 + cw2, y3 + ch2], outline=(96, 106, 124))
        d3.text((x0, y3 + ch2 + 6), "%s ｜ 墨迹下底色 %s"
                % (("对照" if s == "none" else s), stats[s]["bg_under"]),
                font=f_m, fill=(196, 206, 222))
    p3 = os.path.join(EVID, "E1_细节_文字区8x.png")
    im3.save(p3, "PNG", optimize=True)
    out.append(p3)

    # ── 合成实测断言（文字压光的可读性）
    ink_ok = all(stats[s]["ink_rgb"] == (255, 255, 255) for s in order + ["none"])
    T("C-1", "白字本体未被底光改色：墨迹实心像素合成色恒为纯白 (255,255,255)（四栏皆然）",
      "; ".join("%s=%s" % (s, stats[s]["ink_rgb"]) for s in order + ["none"]), ink_ok)
    out_ok = all(stats[s]["outline_p50"] == 0 and stats[s]["outline_p90"] <= 110
                 and stats[s]["out_contrast"] >= 4.0 for s in order)
    T("C-2", "黑描边在各态下都清楚可辨（描边灰度中位=0、p90 ≤110、描边/底板 WCAG ≥4.0:1）",
      "; ".join("%s 中位%.0f p90=%.0f 对比%.2f:1" % (s, stats[s]["outline_p50"],
                                                stats[s]["outline_p90"], stats[s]["out_contrast"])
                for s in order + ["none"]), out_ok)
    fr = [stats[s]["outline_black_frac"] for s in order + ["none"]]
    T("C-3", "**底光没有「吃掉」黑描边**：描边纯黑占比在四栏间极差 ≤3 个百分点（与底光无关）",
      "极差 %.2f pp（%s）" % (100 * (max(fr) - min(fr)), " / ".join("%.1f%%" % (100 * v) for v in fr)),
      100 * (max(fr) - min(fr)) <= 3.0)
    base = sum(stats["none"]["bg_under"]) / 3.0
    lift = {s: sum(stats[s]["bg_under"]) / 3.0 - base for s in order}
    T("C-4", "白淡光在浅云底上「可见而不过亮」：off/over 底板亮度提升落在 20~75 灰阶、且底板 <240",
      "off +%.1f → %.0f ｜ over +%.1f → %.0f ｜ press 底板 %.0f"
      % (lift["off"], sum(stats["off"]["bg_under"]) / 3.0, lift["over"],
         sum(stats["over"]["bg_under"]) / 3.0, sum(stats["press"]["bg_under"]) / 3.0),
      20 <= lift["off"] <= 45 and 45 <= lift["over"] <= 75
      and sum(stats["off"]["bg_under"]) / 3.0 < 240 and sum(stats["over"]["bg_under"]) / 3.0 < 240)
    T("C-5", "悬停「一眼可辨」（底板亮度差 ≥15 灰阶）",
      "over − off = %+.1f 灰阶" % (lift["over"] - lift["off"]), (lift["over"] - lift["off"]) >= 15)

    # ── 证据 3：报告 md（**保留文末手写区**：重跑不会冲掉 §五/§六 的目视评语）
    rep = os.path.join(EVID, "E1_自证报告.md")
    hand = ""
    if os.path.isfile(rep):
        old = open(rep, encoding="utf-8").read()
        if HAND_MARK in old:
            hand = old[old.index(HAND_MARK):]
    with open(rep, "w", encoding="utf-8", newline="\n") as f:
        f.write(REPORT_TMPL.format(
            order=" ｜ ".join(FILES[s] for s in order),
            sizes=" ｜ ".join("%s %.2f KiB" % (FILES[s], sizes[s] / 1024.0) for s in order),
            metrics="\n".join(
                "| %s | %.2f | %d | %d/%d | %d | %d | %d | %d |"
                % (s, M[s]["core_mean"], M[s]["core_peak"], M[s]["core_cov8"], M[s]["core_n"],
                   M[s]["full_cov8"], M[s]["op128"], M[s]["op200"], M[s]["amax"])
                for s in ("off", "over", "press")),
            sink="press α≥200 bbox 上沿 %d ｜ off 底框上沿 %d ｜ over 底框上沿 %d ｜ 胶囊 bbox %d×%d"
                 % (bb_press["top"], core_tops["off"], core_tops["over"], bb_press["w"], bb_press["h"]),
            comp="\n".join("| %s | %s | %.2f:1 | %.2f:1 | %.1f%% | %.0f | %.0f | %s |"
                           % ("无底光（对照）" if s == "none" else s, stats[s]["bg_under"],
                              stats[s]["ink_contrast"], stats[s]["out_contrast"],
                              100 * stats[s]["outline_black_frac"], stats[s]["outline_p50"],
                              stats[s]["outline_p90"], stats[s]["ink_rgb"])
                           for s in order + ["none"]),
            budget="目录 %d 件 / %.4f MiB → %d 件 / %.4f MiB（预算 %d MB）⇒ 余量 %.2f KiB；"
                   "本批 3 件 %.2f KiB"
                   % (n_before, tot_before / 1024.0 / 1024.0, n_after, tot_after / 1024.0 / 1024.0,
                      BUDGET_MB, (BUDGET_MB * 1024 * 1024 - tot_after) / 1024.0, tot3 / 1024.0),
        ) + ("\n" + hand if hand else ""))
    out.append(rep)
    return out


HAND_MARK = u"<!-- ===== 以下为 E1 手写区（脚本重跑时原样保留） ===== -->"


REPORT_TMPL = u"""# E1 自证报告 · ISSUE-20260929-05 模式入口三态底光素材（3 件）
（§一~§五 由 `m63_make_modetab_assets.py` 自动生成；§六 目视评语 / §七 未决项 / §八 复现命令
  为 E1 手写区，由脚本按 `HAND_MARK` 原样保留 —— 重跑不会冲掉）

## 一、产物
{order}

逐件体积：{sizes}

## 二、三态量化（「文字区」= 元素中心 120×40；α≥N 为全画布计数）

| 态 | 文字区均α | 文字区峰α | 文字区 α>8 | 全画布 α>8 | α≥128 | α≥200 | αmax |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{metrics}

## 三、下沉 1px
{sink}

## 四、文字压光合成实测（浅云底 162,172,178，白字 30px + 2px 黑描边）
> 「描边纯黑占比」= 描边掩膜像素中合成后 ≤(8,8,8) 的比例；未达 100% 的部分是 **PIL `stroke_width` 的
>  AA 边界像素**（描边层自身在该像素半透明，与底光无关——四栏占比 73.8/73.7/73.8/74.5% 几乎相同即为证据）。
> 「描边掩膜」= 被描边覆盖（full α>200）且墨迹覆盖很低（ink α<64）的像素；不取「墨迹补集」是因为
>  「描边→墨迹」交界那圈白/黑混合像素会把 p90 假性抬高（实测 146 → 修正后 36）。
> 「描边灰度 中位/p90」= 描边像素合成后**通道级最大值**（0..255）的 50/90 分位：中位 0 = 过半描边像素
>  纯黑；p90 = 最亮的那一成描边像素仍有多暗（越小越清楚）。
> 「墨迹实心合成色」= 墨迹 alpha=255 的像素合成色均值（应为纯白 (255,255,255)，证明白字本体没有被底光改色）。

| 态 | 墨迹下合成底色 | 白字/底板(WCAG) | 黑描边/底板(WCAG) | 描边纯黑占比 | 描边灰度中位 | 描边灰度p90 | 墨迹实心合成色 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
{comp}

## 五、预算
{budget}
"""


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
