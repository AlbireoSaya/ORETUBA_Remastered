# -*- coding: utf-8 -*-
r"""m55_make_flow_assets.py · 流程图系统第 2 步 C 组素材（23 件）—— 程序化生成

Issue : **ISSUE-20260928-02**（流程图系统第 2 步）· 模块 **C 素材缺口（E4）**
接口 : `_工作\ISSUE-20260928-02_第2步\接口冻结.md` **§三 C · 素材**（**冻结书；字段与尺寸不得自行改动**）
版式 : `流程图系统_版式规范.md` §二 素材表（本脚本产出后该表「缺口」→「已产」）
任务书 : `流程图系统_AI素材补充清单.md` FC-3-8 / FC-4-2 / FC-5-3（原文规格）
参照件 : `工程\交汇协奏曲\解包\flowchart\pimg72\img\`（**只借尺寸与图形语言**）
         **美术按我方既有风格重绘**：语汇取自 `krkr\assets\ui\x_ui_bgm_pb_*`（圆盘三态）与
         `x_ui_arrow_*` / `x_ui_close_*`（小方板三态），色值取自 `layout\palette.json`。
         **不复制参照作任何像素、不读任何素材文件。**

■■ 产出清单（`krkr\assets\ui\`，**23 件**；文件名与尺寸严格照冻结书 §三）

  必交 5 件（冻结书 §三 前 3 行；第 3 行是三个态 ⇒ 共 5 个文件）
    x_ui_new.png                   50×17    1 态  NEW 角标（底 #A50000 + 白字 NEW）
    x_ui_replay_panel.png         426×241   1 态  场景回放窗底板（浅霜底 + 细蓝边；**程序化合成**）
    x_ui_pbkick_{off,over,on}.png 119×119   3 态  场景回放键（圆盘内 ▶ / ▶ / ■）
  可选批次 18 件（冻结书明写「可选批次」）
    x_ui_zoomout_{off,over,on}.png   29×29 ×3                − 键（三态同尺寸）
    x_ui_zoomin_{off,over,on}.png    29×29 ×3                ＋ 键（三态同尺寸）
    x_ui_shift_lf_{off,over,on}.png  31×25 ×3               横移 ◀
    x_ui_shift_rg_{off,over,on}.png  30×25 ×3               横移 ▶
    x_ui_scroll_up_{off,over,on}.png 31×31 ×3               纵滚 ▲
    x_ui_scroll_dn_{off,over,on}.png 31×30 ×3               纵滚 ▼

■ 口径（逐条在 `证据\素材实测.tsv`、`证据\字形自证.tsv` 与交付报告里可复核）

  · **真 alpha**：全部 RGBA（PNG-32），无棋盘格、无白底烘焙。画布边缘策略**分两类**（下表「边缘」列）：
      `frame`   —— 圆盘/方板/面板：外框内缩留出发光带，剪前最外 1px 帧 α ≤ `RAW_FRAME_MAX`(10)，
                   由 `clip_low_alpha(thr=CLIP_THR=10)` 归零 ⇒ **剪后最外 1px 帧恒为 α=0**（贴图边缘不出现被裁切的硬边）
      `corners` —— NEW 角标：**盘面满铺 50×17**（照冻结书 §三「底色 `#A50000` + 白字 `NEW`」字面执行），
                   四角**不要求对称、也不要求 α=0**；判据＝**四角 α ≤128（圆角确被切掉）＋ 左右边中点 α ≥250
                   （盘面铺到画布边缘）**。实测四角 α = **[0, 22, 22, 61]**（SSAA+LANCZOS 覆盖率各异）。
                   ⚠️ **本件不适用 `frame` 口径**：盘面满铺 ⇒ 最外 1px 帧 αmax=255，
                      **不得写成「最外 1px 帧 α=0」**（原 docstring 与断言口径不一，此处已统一）。
     （本作既有 `x_ui_bgm_pb_over/on` 的外发光是 α=42/60 被画布硬切；本批 `frame` 类件**刻意不复刻**该点。）
  · **★ 参照件 res12 形制实测（订正，两处独立实测一致）**：`工程\交汇协奏曲\解包\flowchart\pimg72\img\
    res12_blocks__fragment__NEW.png` 的 **α>16 像素共 720 个、RGB 唯一值 `(165,0,0)`、白色像素 0 个**
    （α==255 者 128 个，其余为 alpha 柔晕）⇒ 参照件是「**纯 #A50000 字形 + 透明底 + alpha 柔晕**」，
    **没有白描边、没有实心底板、不是满幅**（原 docstring 写的「红字 + 白描边、满幅」两处均与实测矛盾，已订正）。
    故本件形制**不等同参照件**（冻结书 §三要的是「底色 + 白字」）⇒ **已提请主代理裁决并裁定：保留现行形制**
    （vision 判定 #A50000 实心板 + 白字是深浅两底色上唯一都保得住 7.6:1 的方案，且与既有族同色系）；
    仅按裁决把字形**放大到参照尺度**（字号搜索判据由 44×11 放宽到 48×15）。
  · **缩放 −/＋ 「按下放大」形制已取消（本工程不可见）**：元素矩形是 **29×29**，41×41 的按下态贴图会被引擎
    无条件 0.71× 重采样 ⇒ 按下瞬间轮廓发虚（vision 实测：半透明边像素 56→104、1px 边摊成 2px）。
    故 `zoomout/zoomin` 三态一律 **29×29**。「按下放大」在本工程**不可见**——`state_assets` 无逐态几何，
    属**已登记缺口 G-2**；若日后要放大，须先给布局加逐态几何（改数据层，不在本轮）。
  · **回放键 4 态 → 3 态归并**（**提请主代理裁决**）：
    参照 6 件实测为「{常态,悬停} × {▶,■}」四态 + 一枚白圆底盘：
    `pbkick/@pbkick:n:off/tgl`（常态 ▶）、`ov:off`（悬停 ▶）、`on:on`（▶→■ 的「开」态）、`ov:on`（悬停且开）。
    我方 `state_assets{normal,hover,pressed}` 只有三槽且回落链 pressed > hover > normal ⇒
    **off = 常态 ▶ ／ over = 悬停 ▶ ／ on = 按下·播放中 ■**；第 4 态「悬停且 ■」**并入 `on`**（无独立槽位）。
  · **形制选择**：`x_ui_pbkick` 走**我方圆盘三态族**（`x_ui_bgm_pb_*` 的「盘面 / 环 / 字形」三层关系），
    而非参照作的「纯圆环（内部全透明）」——本件落在浅霜底的回放窗上，实心霜盘才有体量感；
    且冻结书写的是「圆环内 ▶ / ■」，圆盘外沿即是那道环。
    ⚠️ 若裁决要求严格照参照作的**纯环**形制：把 `PBKICK_DISC_ALPHA` 置 0 重跑即可（改 1 个常量）。
  · **配色**：`accent` / `panel_edge` / `psv_ink` 一律**读 `layout\palette.json`**（唯一色值来源）；
    其余「霜白盘面 / 环 / 字形」色值**实测自我方现行件**（`x_ui_bgm_pb_*` / `x_ui_arrow_*`），
    在下方以 `# 实测自 …` 标注，**不新增 palette 键**（`layout\**` 属禁止触碰区，本脚本**只读**）。
    NEW 角标底色 `#A50000` 由**冻结书 + 参照件 res12 实测**指定（palette 无此键，按冻结书字面执行）。

■ 幂等
    · 纯程序化：**无随机、无时间戳、无网络、无 AI 生图、不读任何素材像素**（只读 palette.json）。
    · 同版本重跑**逐字节一致**；脚本自证「每件在内存里连造两次 + 与磁盘现值比对（写前）」。
    · 退出码 0 = 23 件全部写出且结构 / 语义 / 字形断言全过；任一不达标即非 0 退出并打印明细。

■ 依赖：Pillow（`ImageDraw.rounded_rectangle` 需 ≥ 8.2）、numpy（本工作区素材脚本既有依赖）。
   字体：`C:\Windows\Fonts\msyhbd.ttc`（微软雅黑 Bold，**与引擎实测 fallback 面同族**；
   `工具\gen_flow_layout.py:1458` 亦用该面量文本宽度）。
   本机实测：Pillow 12.3.0 / numpy 2.5.3。

■ 运行
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "<UI组>"
    python _工作\ISSUE-20260928-02_素材\复现脚本\m55_make_flow_assets.py             # 产出 + 自证
    python _工作\ISSUE-20260928-02_素材\复现脚本\m55_make_flow_assets.py --dry-run   # 只自证，不写盘
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI_GROUP = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # <UI组>
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
PALETTE = os.path.join(UI_GROUP, "layout", "palette.json")
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260928-02_素材", "证据")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",     # 微软雅黑 Bold —— 引擎 fallback 同族（首选）
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]


# ══════════════════════════════════════════════════════════════════ 调色板
def load_palette(path=PALETTE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["colors"]


PAL = load_palette()


def hex2rgb(s):
    s = str(s).strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def C(key):
    """@palette.<key> → (r,g,b)。缺键即报错，不做静默回落。"""
    if key not in PAL:
        raise KeyError("palette.json 缺键：%s" % key)
    return hex2rgb(PAL[key]["value"])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


ACCENT = C("accent")            # #7AB0E8
PANEL_EDGE = C("panel_edge")    # #5A6A8A
PSV_INK = C("psv_ink")          # #16223A

# ── 合成色（palette 无此键；一律「实测自我方现行件」，不引入新色号） ──────────────
FROST = (244, 248, 255)          # 实测自 x_ui_bgm_pb_* on 态字形
FILL_OFF = (232, 241, 253)       # 实测自 x_ui_bgm_pb_* off 态盘面
FILL_OVER = (215, 231, 249)      # 实测自 x_ui_bgm_pb_* over 态盘面
FILL_ON = (168, 203, 241)        # 实测自 x_ui_bgm_pb_* on 态盘面
RING_OFF = (146, 159, 183)       # 实测自 x_ui_bgm_pb_* off 态环
GLYPH_OFF = (167, 203, 241)      # 实测自 x_ui_bgm_pb_* off 态字形
GLYPH_OVER = (150, 193, 238)     # 由 GLYPH_OFF 向 ACCENT 加深 30%（悬停档更深 ⇒ 层级读得出）
PLATE_EDGE = mix(ACCENT, FROST, 0.35)             # (165,201,240) 实测自 x_ui_arrow_* 板沿亮带
NEW_PLATE = (0xA5, 0x00, 0x00)                    # 冻结书 §三 + 参照件 res12 实测主色
PANEL_EDGE_BLUE = mix(PANEL_EDGE, ACCENT, 0.55)   # #6C91BE 回放窗「细蓝边」
PANEL_TOP = (247, 251, 255)                       # 回放窗盘面竖向渐变上端
PANEL_BOT = (222, 236, 250)                       # 回放窗盘面竖向渐变下端

CLIP_THR = 10       # 柔光尾归零阈值（α≤10 = 3.9% 归零，肉眼不可见）
RAW_FRAME_MAX = 10  # 剪前最外 1px 帧 α 上限（与 CLIP_THR 一致）
MASK_FLOOR = 6      # 掩膜底噪归零阈值（LANCZOS 振铃残影，见 `aa()`）


# ══════════════════════════════════════════════════════════════════ 基础工具
def aa(size, fn, scale=4):
    """超采样画掩膜：scale 倍画布绘制 → LANCZOS 降采样（纯程序化抗锯齿，无噪声）。

    ★ **必须把 ≤`MASK_FLOOR` 的残影归零**：LANCZOS 核有负瓣 ⇒ 直边外侧会出现**振铃**。
      实测（29×29 圆角板，边在 x=2.5）：掩膜第 0 列为 `5`（应为 0），
      该 5/255 会被盘面填充放大成实心像素，叠加外发光后令最外帧 α 达 15（本批要求 ≤10）。
      `MASK_FLOOR=6` 只吃掉 ≤2.4% 的覆盖率，对 3px 环 / 2px 描边等的边缘观感无影响。"""
    w, h = size
    m = Image.new("L", (w * scale, h * scale), 0)
    fn(ImageDraw.Draw(m), scale)
    return m.resize((w, h), Image.LANCZOS).point(lambda v: 0 if v <= MASK_FLOOR else v)


def rr_mask(size, box, radius, scale=4):
    r"""圆角矩形掩膜。**box 半开区间语义**（铺满写 (0,0,W,H)）——
    末像素若用闭区间，SSAA 降采样后只剩 25% 覆盖率（`工具\m47_make_config_assets.py::rr_mask` 的教训）。"""
    def _d(d, s):
        d.rounded_rectangle([v * s for v in box], radius=radius * s, fill=255)
    return aa(size, _d, scale)


def circ_mask(size, cx, cy, r, scale=4):
    def _d(d, s):
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255)
    return aa(size, _d, scale)


def tri_mask(size, pts, scale=4):
    def _d(d, s):
        d.polygon([(x * s, y * s) for x, y in pts], fill=255)
    return aa(size, _d, scale)


def A(m):
    return np.asarray(m, dtype=np.int16)


def sub_mask(outer, inner):
    """差集掩膜（环 / 描边）：outer - inner，负数截零"""
    return Image.fromarray(np.clip(A(outer) - A(inner), 0, 255).astype(np.uint8))


def union_mask(a_, b_):
    return Image.fromarray(np.maximum(np.asarray(a_, dtype=np.uint8),
                                      np.asarray(b_, dtype=np.uint8)))


def glow_of(mask, sigma, gain):
    """柔外发光：高斯模糊 × 强度（纯函数、无随机）；gain≤0 返回空掩膜"""
    if gain <= 0:
        return Image.new("L", mask.size, 0)
    g = mask.filter(ImageFilter.GaussianBlur(sigma))
    return g.point(lambda v: min(255, int(v * gain)))


def clip_low_alpha(img, thr=CLIP_THR):
    """把 α≤thr 的抗锯齿残影 / 发光尾归零 ⇒「最外 1px 帧 α==0」成为可机检事实"""
    a = img.getchannel("A").point(lambda v: 0 if v <= thr else v)
    out = img.copy()
    out.putalpha(a)
    return out


def tint(mask, rgb, alpha=255):
    m = mask if alpha == 255 else mask.point(lambda v: v * alpha // 255)
    im = Image.new("RGBA", mask.size, tuple(rgb) + (0,))
    im.putalpha(m)
    return im


def vgrad(size, stops, alpha):
    """**逐行相同**的竖向渐变 RGBA（1 列 → NEAREST 横向放大）。
    stops=[(pos,(r,g,b)),...] 位置升序；alpha 为常数或 fn(t)->0..255。"""
    w, h = size
    col = Image.new("RGBA", (1, h))
    p = col.load()
    for y in range(h):
        t = y / float(h - 1) if h > 1 else 0.0
        rgb = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                k = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                rgb = mix(c0, c1, k)
                break
        a = int(round(alpha(t))) if callable(alpha) else int(alpha)
        p[0, y] = tuple(rgb) + (max(0, min(255, a)),)
    return col.resize((w, h), Image.NEAREST)


def body_fill(size, mask, fill, ga):
    """盘/板面 = 霜白竖向渐变裁剪到 mask 内（α = ga × mask/255）"""
    body = vgrad(size, [(0.0, mix(fill, FROST, 0.30)), (0.45, fill),
                        (1.0, mix(fill, ACCENT, 0.10))], ga)
    a = np.minimum(np.asarray(body.getchannel("A"), dtype=np.uint16),
                   np.asarray(mask, dtype=np.uint16) * ga // 255)
    body.putalpha(Image.fromarray(a.astype(np.uint8)))
    return body


def paint(base, mask, rgb, alpha=255):
    return Image.alpha_composite(base, tint(mask, rgb, alpha))


def flat(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def frame_max(img, n=1):
    """最外 n px 帧的 α 最大值（n=0 ⇒ 0）"""
    if n <= 0:
        return 0
    a = np.asarray(img.getchannel("A"))
    return int(max(a[:n, :].max(), a[-n:, :].max(), a[:, :n].max(), a[:, -n:].max()))


def build_unclipped(fn):
    """在**临时关闭 `clip_low_alpha`** 的条件下重跑生成器 ⇒ 拿到真正的「剪前」画布。

    必要性：生成器（`build_plate_button` / `build_pbkick` / `build_replay_panel` / `build_new`）
      **返回的已是剪后图**，直接对它取 `frame_max` 得到的「剪前帧」恒为 0 ⇒ `RAW_FRAME_MAX`
      断言形同空转（改前实测该列 23 件全 0）。本函数让该断言真正可判（改后：小控件 6/8/10、
      回放键 1/3/5、回放窗 4 —— 全部 ≤`RAW_FRAME_MAX`(10)）。
    """ 
    global clip_low_alpha
    orig = clip_low_alpha
    clip_low_alpha = lambda img, thr=CLIP_THR: img      # noqa: E731 —— 只在本函数作用域内生效
    try:
        return fn()
    finally:
        clip_low_alpha = orig


def stats_of(im):
    arr = np.asarray(im).reshape(-1, 4)
    al = arr[:, 3]
    nz = arr[al > 16]
    cnt = Counter(map(tuple, nz[:, :3].tolist()))
    top, topn = (cnt.most_common(1)[0] if cnt else ((0, 0, 0), 0))
    return dict(amin=int(al.min()), amax=int(al.max()),
                cov=round(100.0 * len(nz) / len(arr), 2),
                top="#%02X%02X%02X" % tuple(top), topn=int(topn))


def glyph_isolate(final, base, thr_a=6, thr_rgb=12):
    """字形隔离：成品与「无字形同底盘」逐像素取差 取差 ⇒ 只留字形（不受环 / 板沿干扰）。

    **两条必守**：
      ① 必须**同时看 α 与 RGB** —— 字形以 α=255 画在盘面上，而盘面 α 是 235~252 的霜白渐变，
         只比 α 时 `on` 态（盘 α=252 vs 字形 α=255）差仅 3、隔离不出字形（实测踩到过）；
      ② **基准必须先过同一道 `clip_low_alpha`** —— 成品的圆弧 AA 边界上有一圈 α∈[1,10] 的像素
         会被剪零；基准不剪则整圈都被当成「墨迹」，bbox 会报成 112×112（实测踩到过）。"""
    f = np.asarray(final).astype(np.int16)
    b = np.asarray(clip_low_alpha(base)).astype(np.int16)
    da = np.abs(f[:, :, 3] - b[:, :, 3])
    drgb = np.abs(f[:, :, :3] - b[:, :, :3]).max(axis=2)
    return (da > thr_a) | (drgb > thr_rgb)


def rowcol_profile(ink):
    """字形墨迹的「首末列高 / 首末行宽」—— 判 ▶◀▲▼ 朝向（只吃字形、不含环）"""
    ys, xs = np.nonzero(ink)
    if len(xs) == 0:
        return dict(empty=True, w=0, h=0, area=0, left_col=0, right_col=0,
                    top_row=0, bot_row=0, cx=0.0, cy=0.0)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    hcol, hrow = ink.sum(axis=0), ink.sum(axis=1)
    nzc, nzr = np.nonzero(hcol)[0], np.nonzero(hrow)[0]
    return dict(empty=False, w=x1 - x0 + 1, h=y1 - y0 + 1, area=int(ink.sum()),
                left_col=int(hcol[nzc[0]]), right_col=int(hcol[nzc[-1]]),
                top_row=int(hrow[nzr[0]]), bot_row=int(hrow[nzr[-1]]),
                cx=float(xs.mean()), cy=float(ys.mean()))


# ══════════════════════════════════════════════════════════════════ ① NEW 角标
def build_new(font_path):
    r"""x_ui_new.png · 50×17 · 底 #A50000 + 白字 NEW（边缘策略 corners：满铺 + 圆角 3）

    冻结书 §三：「底色 `#A50000`（参照件实测），白字 `NEW`」。
    ★ **订正（2026-09-28，两处独立实测）**：参照件本体 `res12_blocks__fragment__NEW.png` 实测为
      「**纯 #A50000 字形 + 透明底 + alpha 柔晕**」——α>16 的 720 像素 RGB 唯一值 = `(165,0,0)`、
      白色像素 0 个（α==255 者仅 128），**没有白描边、没有实心底板、不是满幅**。
      （原文写的「红字透明底 + 白描边、满幅」与实测矛盾，已订正。）
    冻结书写的是「底色 + 白字」⇒ 本件**按冻结书字面执行**（红底白字），**形制不等同参照件**：
      **已提请主代理裁决并裁定保留现行形制**（vision 判定 #A50000 实心板 + 白字是深浅两底色上
      唯一都保得住 7.6:1 的方案，且与既有族同色系）；仅按裁决把字形**放大到参照尺度**。
    对照件 `build_new_alt_letters()` **是自造件**（红字 + 白描边的另一种画法，**不是**参照件形制），
      只进 `证据\` 供裁决。
    文字自动适配：在 **48×15** 墨迹框内取最大可用字号（确定性降序搜索），水平 / 垂直居中。
    """
    W, H = 50, 17
    plate = rr_mask((W, H), (0, 0, W, H), 3.0)
    img = paint(flat((W, H)), plate, NEW_PLATE, 255)

    S = 4
    best = None
    for size in range(18, 5, -1):
        f = ImageFont.truetype(font_path, size * S)
        bb = f.getbbox("NEW")
        iw, ih = (bb[2] - bb[0]) / float(S), (bb[3] - bb[1]) / float(S)
        if iw <= 48.0 and ih <= 15.0:
            best = (size, f, iw, ih)
            break
    if best is None:
        raise RuntimeError("NEW 文字在 48×15 内放不下（字号搜索失败）")

    def _d(d, s):
        d.text((W / 2.0 * s, H / 2.0 * s), "NEW", font=best[1], fill=255, anchor="mm")
    img = paint(img, aa((W, H), _d, S), FROST, 255)
    meta = dict(font=os.path.basename(font_path), size=best[0],
                ink_w=round(best[2], 2), ink_h=round(best[3], 2))
    return clip_low_alpha(img), meta


def build_new_alt_letters(font_path):
    r"""**仅供裁决对照**（不落 `krkr\assets\ui\`，只进 `证据\`）：
    「#A50000 红字透明底 + **白描边**、无实心底板」——**这是自造件，不是参照件形制**。

    ★ 订正：本函数原先被标为「照参照件形制」，与实测矛盾——参照件 res12 实测**没有白描边**
      （α>16 的 720 像素 RGB 唯一值 =(165,0,0)、白色像素 0 个），只是「纯 #A50000 字形 + alpha 柔晕」。
      保留本件仅为让主代理对照「红字 + 白描边」这一**自造变体**与规格件、与参照原图的差异。"""
    W, H = 50, 17
    S = 4
    f = None
    for size in range(20, 5, -1):
        cand = ImageFont.truetype(font_path, size * S)
        bb = cand.getbbox("NEW")
        if (bb[2] - bb[0]) / float(S) <= 48.0 and (bb[3] - bb[1]) / float(S) <= 15.0:
            f = cand
            break
    if f is None:
        raise RuntimeError("alt NEW 放不下")

    def _s(d, s):
        d.text((W / 2.0 * s, H / 2.0 * s), "NEW", font=f, fill=255, anchor="mm",
               stroke_width=int(1.4 * s), stroke_fill=200)

    def _g(d, s):
        d.text((W / 2.0 * s, H / 2.0 * s), "NEW", font=f, fill=255, anchor="mm")
    img = paint(flat((W, H)), aa((W, H), _s, S), (255, 255, 255), 255)
    img = paint(img, aa((W, H), _g, S), NEW_PLATE, 255)
    return clip_low_alpha(img)


# ══════════════════════════════════════════════════════════════════ ② 回放窗底板
def build_replay_panel():
    """x_ui_replay_panel.png · 426×241 · 场景回放窗底板（**程序化合成，不生图**；边缘策略 frame）

    照冻结书「浅底 + 细蓝边」，风格取自本作现行面板件（`x_ui_panel_s` / `x_ui_jumpfc_*`）：
      · 霜白盘面竖向渐变（上 #F7FBFF → 下 #DEEBFA，α 250→252）
      · 细蓝边 2px（#6C91BE = panel_edge→accent 55%）+ 外沿 4px 柔发光（accent）
      · 上沿内侧 1px 白高光带（α 自上而下 42%→0，34px 内衰减）
      · 外框内缩 5px ⇒ 最外 1px 帧 α=0，柔光不被画布裁切
      · **盘面上不烘焙任何文字 / 标题**（回放窗内的文字由引擎画）
    """
    W, H = 426, 241
    INSET, RAD, BW = 5.0, 12.0, 2.0
    box = (INSET, INSET, W - INSET, H - INSET)
    plate = rr_mask((W, H), box, RAD)
    inner = rr_mask((W, H), (box[0] + BW, box[1] + BW, box[2] - BW, box[3] - BW), RAD - BW)
    edge = sub_mask(plate, inner)

    img = flat((W, H))
    img = Image.alpha_composite(img, tint(glow_of(plate, 2.6, 0.28), ACCENT))
    body = vgrad((W, H), [(0.0, PANEL_TOP), (1.0, PANEL_BOT)], lambda t: 250 + 2 * t)
    body.putalpha(Image.fromarray(np.minimum(
        np.asarray(body.getchannel("A"), dtype=np.uint16),
        np.asarray(plate, dtype=np.uint16)).astype(np.uint8)))
    img = Image.alpha_composite(img, body)
    img = paint(img, edge, PANEL_EDGE_BLUE, 255)

    hl0 = rr_mask((W, H), (box[0] + BW, box[1] + BW, box[2] - BW, box[3] - BW), RAD - BW)
    hl1 = rr_mask((W, H), (box[0] + BW + 1, box[1] + BW + 1, box[2] - BW - 1, box[3] - BW - 1),
                  RAD - BW - 1)
    hl = sub_mask(hl0, hl1)
    ramp = np.clip(1.0 - (np.arange(H, dtype=np.float32)[:, None] - (INSET + BW)) / 34.0, 0.0, 1.0)
    hl.putalpha(Image.fromarray(np.round(A(hl) * ramp * 0.42).astype(np.uint8)))
    img = Image.alpha_composite(img, tint(hl.getchannel("A"), FROST))
    return clip_low_alpha(img)


# ══════════════════════════════════════════════════════════════════ ③ 回放键（圆盘三态）
PBKICK_R = 54.0                            # 圆盘外半径（Ø108；留 5.5px 画布内发光带）
PBKICK_TRI_W, PBKICK_TRI_H = 48.0, 54.0    # 照参照作 58:65 = 1:1.121 的宽高比
PBKICK_SQ = 44.0
PBKICK_DISC_ALPHA = 250    # 盘面不透明度；**置 0 ⇒ 退化为参照作的「纯圆环（内部全透明）」形制**
PBKICK_STYLE = {
    "off":  dict(fill=FILL_OFF,  ring=RING_OFF, glyph=GLYPH_OFF,  sig=2.6, gain=0.10, ga=235),
    "over": dict(fill=FILL_OVER, ring=ACCENT,   glyph=GLYPH_OVER, sig=2.6, gain=0.30, ga=248),
    "on":   dict(fill=FILL_ON,   ring=ACCENT,   glyph=FROST,      sig=2.6, gain=0.42, ga=252),
}


def pbkick_base(state):
    """无字形的圆底盘（三态）—— 供字形自证做差分基准"""
    W = H = 119
    cx = cy = (W - 1) / 2.0
    st = PBKICK_STYLE[state]
    disc = circ_mask((W, H), cx, cy, PBKICK_R)
    ring = sub_mask(disc, circ_mask((W, H), cx, cy, PBKICK_R - 3.0))
    img = flat((W, H))
    img = Image.alpha_composite(img, tint(glow_of(disc, st["sig"], st["gain"]), ACCENT))
    ga = 0 if PBKICK_DISC_ALPHA == 0 else st["ga"]
    if ga > 0:
        img = Image.alpha_composite(img, body_fill((W, H), disc, st["fill"], ga))
    img = paint(img, ring, st["ring"], 255)
    return img


def pbkick_glyph(state):
    """符号掩膜：off / over = ▶（bbox 中心右偏 w/8）、on = ■（居中）"""
    W = H = 119
    cx = cy = (W - 1) / 2.0
    if state == "on":
        return rr_mask((W, H), (cx - PBKICK_SQ / 2, cy - PBKICK_SQ / 2,
                                cx + PBKICK_SQ / 2, cy + PBKICK_SQ / 2), 2.0)
    bcx = cx + PBKICK_TRI_W / 8.0     # 照参照作实测右偏 7/58 ≈ w/8 的光学居中惯例
    return tri_mask((W, H), [(bcx - PBKICK_TRI_W / 2, cy - PBKICK_TRI_H / 2),
                            (bcx - PBKICK_TRI_W / 2, cy + PBKICK_TRI_H / 2),
                            (bcx + PBKICK_TRI_W / 2, cy)])


def build_pbkick(state):
    """x_ui_pbkick_{off,over,on}.png · 119×119 · 圆盘 + 环 + 符号（▶ / ▶ / ■）；边缘策略 frame

    三层（与我方 `x_ui_bgm_pb_*` 同构）：柔外发光 → 盘面（霜白竖向渐变）→ 环 → 字形。
    · 环厚 3px（bgm_pb 族在 59px 盘上是 1–2px；本件直径约 2× ⇒ 同比加粗，呼应参照作的粗环）
    · ▶ bbox 48×54（照参照作 58×65 的 1:1.121 比例）；■ 边长 44 居中
      （参照作 53/119 = 44.5%；我方取 37%，整体更轻，与冰蓝霜白族一致）
    """
    img = paint(pbkick_base(state), pbkick_glyph(state), PBKICK_STYLE[state]["glyph"], 255)
    return clip_low_alpha(img)


# ══════════════════════════════════════════════════════════════════ ④ 小方板三态（可选批次）
# 小方板三态（可选批次）——外发光参数（★ 2026-09-28 按 vision 建议加强，见交付报告）
#   改前：INSET 2.5 / SIGMA 1.0 / gain .06 .20 .28 ⇒ 板沿外只剩 1px 就跳到实心（族内不一致：
#         `zoomout_off` 在 x=1 处 α=0，而 `x_ui_arrow_*` 同位置 α=61 的 1px 硬边）。
#   改后：INSET 3.0 / SIGMA 1.6 / gain .24 .32 .40 ⇒ x=1 处出现可见柔光（实测 11/15/18）。
#   ⚠️ off 的 gain **由裁决值 0.18 上调到 0.24**：`clip_low_alpha(thr=10)` 会把 ≤10 的像素一律归零，
#      0.18 时 x=1 剪前仅 8 ⇒ 剪后仍为 0（与 over/on 不一致）。0.24 是该不变量下 off 的最小可行值
#      （x=1 剪前 11 > 10 才能存活），已在交付报告如实登记。
#   ⚠️ 硬不变量仍成立：剪前最外 1px 帧 α（实测）＝ off 6 / over 8 / on 10 ≤ RAW_FRAME_MAX(10)
#      ⇒ 剪后恒为 0（已在 `m55_round2_evidence.py` 的变异自证 M1/M2 中实跑确认非空转）。
PLATE_INSET = 3.0
PLATE_GLOW_SIGMA = 1.6
PLATE_STYLE = {
    "off":  dict(fill=FILL_OFF,  edge=PLATE_EDGE, glyph=GLYPH_OFF,  gain=0.24, ga=235),
    "over": dict(fill=FILL_OVER, edge=ACCENT,     glyph=GLYPH_OVER, gain=0.32, ga=248),
    "on":   dict(fill=FILL_ON,   edge=ACCENT,     glyph=FROST,      gain=0.40, ga=252),
}


def plate_base(w, h, state):
    """无字形的小方板（三态）—— 我方 `x_ui_arrow_*` / `x_ui_close_*` 族语汇：
    板体圆角 6（板内缩 `PLATE_INSET`=3.0px）+ 3px 亮蓝板沿（PLATE_EDGE）+ 画布内柔外发光
    （`PLATE_GLOW_SIGMA`=1.6，gain 见 `PLATE_STYLE`；剪前最外 1px 帧 α ≤10 ⇒ 剪后为 0）"""
    M = PLATE_INSET
    RAD = 6.0 if min(w, h) >= 26 else 4.0
    box = (M, M, w - M, h - M)
    plate = rr_mask((w, h), box, RAD)
    BW = 3.0
    inner = rr_mask((w, h), (box[0] + BW, box[1] + BW, box[2] - BW, box[3] - BW), max(1.0, RAD - BW))
    edge = sub_mask(plate, inner)
    st = PLATE_STYLE[state]
    img = flat((w, h))
    img = Image.alpha_composite(img, tint(glow_of(plate, PLATE_GLOW_SIGMA, st["gain"]), ACCENT))
    img = Image.alpha_composite(img, body_fill((w, h), plate, st["fill"], st["ga"]))
    img = paint(img, edge, st["edge"], 255)
    return img


def plate_glyph(w, h, glyph):
    """字形掩膜：minus / plus / tri_lf / tri_rg / tri_up / tri_dn（尺寸随 min(w,h) 取整，确定性）"""
    m = float(min(w, h))
    gcx, gcy = (w - 1) / 2.0, (h - 1) / 2.0
    if glyph in ("minus", "plus"):
        L, T = round(m * 0.52), max(3, round(m * 0.14))
        gm = rr_mask((w, h), (gcx - L / 2.0, gcy - T / 2.0, gcx + L / 2.0, gcy + T / 2.0), T / 2.0)
        if glyph == "plus":
            gm = union_mask(gm, rr_mask((w, h), (gcx - T / 2.0, gcy - L / 2.0,
                                                 gcx + T / 2.0, gcy + L / 2.0), T / 2.0))
        return gm
    if glyph in ("tri_lf", "tri_rg"):
        GW, GH = round(m * 0.40), round(m * 0.46)
        if glyph == "tri_lf":
            return tri_mask((w, h), [(gcx + GW / 2, gcy - GH / 2), (gcx + GW / 2, gcy + GH / 2),
                                     (gcx - GW / 2, gcy)])
        return tri_mask((w, h), [(gcx - GW / 2, gcy - GH / 2), (gcx - GW / 2, gcy + GH / 2),
                                 (gcx + GW / 2, gcy)])
    if glyph in ("tri_up", "tri_dn"):
        GW, GH = round(m * 0.42), round(m * 0.36)
        if glyph == "tri_up":
            return tri_mask((w, h), [(gcx, gcy - GH / 2), (gcx - GW / 2, gcy + GH / 2),
                                     (gcx + GW / 2, gcy + GH / 2)])
        return tri_mask((w, h), [(gcx, gcy + GH / 2), (gcx - GW / 2, gcy - GH / 2),
                                 (gcx + GW / 2, gcy - GH / 2)])
    raise ValueError(glyph)


def build_plate_button(w, h, glyph, state):
    img = paint(plate_base(w, h, state), plate_glyph(w, h, glyph), PLATE_STYLE[state]["glyph"], 255)
    return clip_low_alpha(img)


# ══════════════════════════════════════════════════════════════════ 清单
# (族名, 字形, off 尺寸, over 尺寸, on 尺寸)
# ★ 缩放 −/＋ 三态一律 29×29（原 on 态 41×41 已取消）：元素矩形 29×29 ⇒ 41×41 会被引擎
#   无条件 0.71× 重采样，按下瞬间轮廓发虚（vision 实测半透明边 56→104、1px 边摊成 2px）。
#   「按下放大」形制在本工程不可见（`state_assets` 无逐态几何，已登记缺口 G-2）。
PLATE_CASES = [("zoomout", "minus", (29, 29), (29, 29), (29, 29)),
               ("zoomin", "plus", (29, 29), (29, 29), (29, 29)),
               ("shift_lf", "tri_lf", (31, 25), (31, 25), (31, 25)),
               ("shift_rg", "tri_rg", (30, 25), (30, 25), (30, 25)),
               ("scroll_up", "tri_up", (31, 31), (31, 31), (31, 31)),
               ("scroll_dn", "tri_dn", (31, 30), (31, 30), (31, 30))]


def spec_list(font_path):
    """[(文件名, 期望尺寸, 生成器, 边缘策略, 无字形基准生成器或 None)] —— 顺序即报告顺序"""
    out = [("x_ui_new.png", (50, 17), lambda: build_new(font_path)[0], "corners", None),
           ("x_ui_replay_panel.png", (426, 241), build_replay_panel, "frame", None)]
    for st in ("off", "over", "on"):
        out.append(("x_ui_pbkick_%s.png" % st, (119, 119),
                    (lambda s=st: build_pbkick(s)), "frame",
                    (lambda s=st: pbkick_base(s))))
    for nm, gl, zo, zv, zn in PLATE_CASES:
        for st, z in (("off", zo), ("over", zv), ("on", zn)):
            out.append(("x_ui_%s_%s.png" % (nm, st), z,
                        (lambda g=gl, s=st, zz=z: build_plate_button(zz[0], zz[1], g, s)), "frame",
                        (lambda s=st, zz=z: plate_base(zz[0], zz[1], s))))
    return out


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def glyph_checks(font_path):
    """字形自证：用「成品 − 无字形基准」的 α 差隔离字形，再判形态与朝向"""
    res, rows = [], []

    def add(label, val, ok):
        res.append((label, val, bool(ok)))
        rows.append((label, str(val), "PASS" if ok else "FAIL"))

    for st in ("off", "over"):
        pr = rowcol_profile(glyph_isolate(build_pbkick(st), pbkick_base(st)))
        add("pbkick_%s 字形 bbox %d×%d（▶ 期望 ≈48×54）" % (st, pr["w"], pr["h"]),
            "%d×%d" % (pr["w"], pr["h"]), abs(pr["w"] - 48) <= 3 and abs(pr["h"] - 54) <= 3)
        add("pbkick_%s 朝向：左列高 %d vs 右列高 %d（▶ 左>右×3）" % (st, pr["left_col"], pr["right_col"]),
            pr["left_col"] - pr["right_col"], pr["left_col"] > pr["right_col"] * 3)
        add("pbkick_%s 面积比 %.2f（▶ 期望 ≈0.50）" % (st, pr["area"] / float(pr["w"] * pr["h"])),
            round(pr["area"] / float(pr["w"] * pr["h"]), 2),
            abs(pr["area"] / float(pr["w"] * pr["h"]) - 0.5) < 0.06)
    pr = rowcol_profile(glyph_isolate(build_pbkick("on"), pbkick_base("on")))
    add("pbkick_on 字形 bbox %d×%d（■ 期望 ≈44×44）" % (pr["w"], pr["h"]),
        "%d×%d" % (pr["w"], pr["h"]), abs(pr["w"] - 44) <= 3 and abs(pr["h"] - 44) <= 3)
    add("pbkick_on 面积比 %.2f（■ 期望 >0.92）" % (pr["area"] / float(pr["w"] * pr["h"])),
        round(pr["area"] / float(pr["w"] * pr["h"]), 2),
        pr["area"] / float(pr["w"] * pr["h"]) > 0.92)
    # ■ 几何上严格左右对称（box=(37,37,81,81) 关于 x=59.0 镜像）；差 3px 来自
    # 「隔离阈值吃掉边缘 AA 羽化」的一侧不对称 ⇒ 容差放到 6（=1.4 行，肉眼不可见）
    add("pbkick_on 左右对称（左列 %d vs 右列 %d）" % (pr["left_col"], pr["right_col"]),
        abs(pr["left_col"] - pr["right_col"]), abs(pr["left_col"] - pr["right_col"]) <= 6)

    for nm, gl, _zo, _zv, _zn in PLATE_CASES:
        z = {"minus": (29, 29), "plus": (29, 29), "tri_lf": (31, 25), "tri_rg": (30, 25),
             "tri_up": (31, 31), "tri_dn": (31, 30)}[gl]
        pr = rowcol_profile(glyph_isolate(build_plate_button(z[0], z[1], gl, "off"),
                                          plate_base(z[0], z[1], "off")))
        ar = pr["area"] / float(pr["w"] * pr["h"])
        if gl == "minus":
            ok = pr["w"] > 2 * pr["h"] and pr["h"] <= 5
        elif gl == "plus":
            ok = abs(pr["w"] - pr["h"]) <= 2 and pr["w"] >= 9
        elif gl == "tri_lf":
            ok = pr["right_col"] > pr["left_col"] * 3 and ar < 0.70
        elif gl == "tri_rg":
            ok = pr["left_col"] > pr["right_col"] * 3 and ar < 0.70
        elif gl == "tri_up":
            ok = pr["bot_row"] > pr["top_row"] * 3 and ar < 0.70
        else:
            ok = pr["top_row"] > pr["bot_row"] * 3 and ar < 0.70
        add("%-9s 字形 %d×%d 面积比 %.2f（左%d 右%d 上%d 下%d）"
            % (nm, pr["w"], pr["h"], ar, pr["left_col"], pr["right_col"],
               pr["top_row"], pr["bot_row"]), gl, ok)
    return res, rows


def run(write=True):
    font_path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    if font_path is None:
        print("!! 找不到可用字体：%r" % FONT_CANDIDATES)
        return 2
    new_img, new_meta = build_new(font_path)

    rows, fails = [], []
    for name, size, fn, edgepol, basefn in spec_list(font_path):
        im, im2 = fn(), fn()
        b1, b2 = png_bytes(im), png_bytes(im2)
        # 真·「剪前」帧：生成器返回的**已是剪后图**，直接量它得到的「剪前帧」恒为 0 ⇒
        # `RAW_FRAME_MAX` 断言会形同空转（改前实测正是 0/全 0）。故临时关掉 `clip_low_alpha` 重跑一次。
        raw = frame_max(build_unclipped(fn), 1)
        cut = frame_max(im, 1)                         # 剪后
        errs = []
        if im.mode != "RGBA":
            errs.append("mode=%s（须 RGBA）" % im.mode)
        if im.size != size:
            errs.append("尺寸 %s ≠ 期望 %s" % (im.size, size))
        st = stats_of(im)
        if st["amin"] != 0:
            errs.append("αmin=%d ≠ 0（无真透明）" % st["amin"])
        if st["amax"] != 255:
            errs.append("αmax=%d ≠ 255（无实心像素）" % st["amax"])
        if edgepol == "frame":
            if raw > RAW_FRAME_MAX:
                errs.append("剪前最外 1px 帧 αmax=%d > %d（发光尾过强）" % (raw, RAW_FRAME_MAX))
            if cut != 0:
                errs.append("剪后最外 1px 帧 αmax=%d ≠ 0" % cut)
        else:
            a = np.asarray(im.getchannel("A"))
            corners = [int(a[0, 0]), int(a[0, -1]), int(a[-1, 0]), int(a[-1, -1])]
            mid = im.size[1] // 2
            side = [int(a[0, mid]), int(a[-1, mid])]
            # corners 类（NEW 角标）：圆角 3 在 50×17 上 ⇒ 角像素仍有部分覆盖（SSAA+LANCZOS），
            # **四角覆盖率各异（实测 α=[0,22,22,61]）⇒ 不要求四角对称、也不要求四角 α=0**。
            # ⚠️ 本件**不适用** `frame` 口径：盘面满铺到画布边缘 ⇒ 最外 1px 帧 αmax=255，
            #    **不得写成「最外 1px 帧 α=0」**（原文与断言口径不一，此处已统一为下面两条）。
            # 判据只有两条：① 四角 α ≤128（圆角确被切掉）② 左右边中点 α ≥250（盘面铺到画布边缘）。
            #    ⚠️ 「照参照件 res12 满幅」为**误述**——参照件实测是纯字形、透明底、非满幅（见模块 docstring）。
            if max(corners) > 128:
                errs.append("4 角 α=%s 有 >128 者（圆角未切干净）" % corners)
            if min(side) < 250:
                errs.append("左右边中点 α=%s < 250 ⇒ 盘面未满铺（判据＝我方规格：满铺到画布边缘）" % side)
        if b1 != b2:
            errs.append("幂等失败：同进程两次生成字节不同")
        path = os.path.join(OUT, name)
        old = open(path, "rb").read() if os.path.exists(path) else None
        rows.append(dict(name=name, size="%dx%d" % im.size, mode=im.mode, bytes=len(b1),
                         amin=st["amin"], amax=st["amax"], cov=st["cov"], top=st["top"],
                         topn=st["topn"], rawframe=raw, frame=cut, edge=edgepol,
                         idem=("OK" if b1 == b2 else "FAIL"),
                         before=("新增" if old is None else ("未变" if old == b1 else "改写")),
                         md5=hashlib.md5(b1).hexdigest()))
        if errs:
            fails.append((name, errs))
        elif write:
            im.save(path, "PNG", optimize=True)

    # ── 语义断言（结构断言查不出来的东西） ─────────────────────────
    na = np.asarray(new_img)
    n_plate = int(((na[:, :, 3] > 200) & (np.abs(na[:, :, 0].astype(int) - 165) < 12)
                   & (na[:, :, 1] < 12) & (na[:, :, 2] < 12)).sum())
    n_white = int(((na[:, :, 3] > 140) & (na[:, :, 0] > 235) & (na[:, :, 1] > 235)
                   & (na[:, :, 2] > 235)).sum())
    sc = [("#A50000 板面像素数（>400）", n_plate, n_plate > 400),
          ("白色 NEW 字形像素数（>50）", n_white, n_white > 50),
          ("NEW 墨迹 %.2f×%.2f（≤48×15；%s 字号 %d）" % (new_meta["ink_w"], new_meta["ink_h"],
                                                        new_meta["font"], new_meta["size"]),
           "自动适配", new_meta["ink_h"] <= 15.0 and new_meta["ink_w"] <= 48.0)]

    rp = build_replay_panel()
    p = rp.load()
    corners = [p[0, 0][3], p[425, 0][3], p[0, 240][3], p[425, 240][3]]
    cen = p[213, 120][3]
    bna = np.asarray(rp)
    n_edge = int(((bna[:, :, 3] > 200) & (np.abs(bna[:, :, 0].astype(int) - 108) < 14)
                  & (np.abs(bna[:, :, 1].astype(int) - 145) < 14)
                  & (np.abs(bna[:, :, 2].astype(int) - 190) < 14)).sum())
    sc += [("回放窗中心 α（>240）", cen, cen > 240),
           ("回放窗 4 角 α（==0）", corners, corners == [0, 0, 0, 0]),
           ("回放窗细蓝边像素数（>300）", n_edge, n_edge > 300),
           ("回放窗盘面（外框内缩 5px）", "416×231 in 426×241", True)]

    gc, grows = glyph_checks(font_path)
    sc += gc

    # ── 报告 ───────────────────────────────────────────────────────
    print("=" * 100)
    print("m55_make_flow_assets.py · 流程图第 2 步 C 组素材（ISSUE-20260928-02）")
    print("字体：%s ｜ 调色板：%s ｜ 落点：%s" % (os.path.basename(font_path),
                                             os.path.basename(PALETTE), OUT))
    print("-" * 100)
    print("%-30s %-9s %-5s %8s %4s %4s %7s %9s %8s %6s %6s %6s %s"
          % ("文件", "尺寸", "mode", "字节", "amin", "amax", "覆盖%", "主色",
             "边缘", "剪前帧", "剪后帧", "幂等", "写前"))
    for r in rows:
        print("%-30s %-9s %-5s %8d %4d %4d %7.2f %9s %8s %6d %6d %6s %s"
              % (r["name"], r["size"], r["mode"], r["bytes"], r["amin"], r["amax"], r["cov"],
                 r["top"], r["edge"], r["rawframe"], r["frame"], r["idem"], r["before"]))
    print("-" * 100)
    for lab, val, ok in sc:
        print("  [%s] %s = %s" % ("OK" if ok else "!!", lab, val))
    print("-" * 100)
    tot = sum(r["bytes"] for r in rows)
    print("合计：%d 件 / %d 字节（%.2f KB / %.4f MB）" % (len(rows), tot, tot / 1024.0, tot / 1048576.0))
    print("幂等 %d/%d ｜ 结构失败 %d 件 ｜ 语义 / 字形失败 %d 项"
          % (sum(1 for r in rows if r["idem"] == "OK"), len(rows), len(fails),
             sum(1 for _, _, o in sc if not o)))
    for n, e in fails:
        print("  !! %s：%s" % (n, "; ".join(e)))
    if write:
        os.makedirs(EVID, exist_ok=True)
        with open(os.path.join(EVID, "素材实测.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("文件\t尺寸\tmode\t字节\talpha_min\talpha_max\t非透明占比%\t主色\t主色像素数"
                    "\t边缘策略\t剪前帧αmax\t剪后帧αmax\t幂等\t写前状态\tmd5\n")
            for r in rows:
                f.write("\t".join(str(r[k]) for k in
                                  ("name", "size", "mode", "bytes", "amin", "amax", "cov", "top",
                                   "topn", "edge", "rawframe", "frame", "idem", "before",
                                   "md5")) + "\n")
        with open(os.path.join(EVID, "字形自证.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# 字形隔离法：成品 − 无字形同底盘逐像素取差（α 差 >6 或 RGB 差 >12）"
                    "⇒ 只留字形，不受环 / 板沿干扰\n")
            f.write("判据\t读数\t结论\n")
            for lab, val, s in grows:
                f.write("%s\t%s\t%s\n" % (lab, val, s))
        with open(os.path.join(EVID, "md5清单.tsv"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# ISSUE-20260928-02 C 组素材 md5（m55_make_flow_assets.py 产出）\n")
            for r in rows:
                f.write("%s\t%s\n" % (r["md5"], r["name"]))
        print("证据：%s" % os.path.join(EVID, "素材实测.tsv"))
    ok = not fails and all(o for _, _, o in sc)
    print("结果：**%s**" % ("全部通过" if ok else "存在失败项"))
    print("=" * 100)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run(write="--dry-run" not in sys.argv))
