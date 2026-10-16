# -*- coding: utf-8 -*-
r"""psv_make_assets.py —— PSV 换皮 · A 基础组三屏（21 确认框 / 22 加载 / 36 选择支）素材入库。

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）｜ 依据：`PSV换皮_素材与文字处置清单.md` §一 + §七。
**幂等**：同一输入每次产出逐字节相同的输出；末尾自带断言（尺寸 / 件数 / 预算）。

素材去向（`krkr\assets\ui\`）：

1. **21 确认框 · 22 张中文弹窗**（源 `PSV系统UI参考\AI中文化\2x\otv_dlg_bg_<NN>_cn.png`）
   → `x_ui_psv_cfm_<NN>.png`（`NN` = 板号 `01..12 / 20..25 / 42..45`，与 `vis_when` 一致）。
   · **★ 修复轮（ISSUE-20260926-06 · A 基础组修复）：15 张 602 高板裁为 1044×540（取顶部 540 行）**。
     602 高件 = 板体（y6..534）＋**板体之外底部左侧那对白羽 YES/NO 徽章带（y541..602）**；后者与板内
     烘焙 YES/NO **重复**、且落在压暗底上悬空（vision 判【高】）。裁剪窗 `(0,0,1044,540)` **完整保留板体
     y6..534 与板内烘焙 YES/NO（板内 y336..368）**，只去掉 y540..601 那 62 行徽章带。
     ★ **实测订正**：板内烘焙 YES/NO 在 y336..368 ⊂ 窗内 ⇒ **裁剪后仍在**（不属于被裁掉的部分）；
     故 15 张板**不补我方按钮**——按 `PSV换皮_素材与文字处置清单.md` 七、line 136 的用户裁决
     「01–12/25/43/44 已含烘焙 YES/NO（**加透明热区覆盖**），20–24/42/45 无 YES/NO（**补我方是/否按钮**）」。
   · **1:1 不缩放**：PSV 2× 件即本作画布口径（PSV 960×544 ×2 = 1920×1088 ≈ 本作 1920×1080）。
   · **降色深（每通道 8→6 bit，`v & 0xFC`）**：清单 §七 用户裁决「素材预算：先优化（PNG 量化/降色深，
     不改尺寸），不够再议」。22 件原件 10.78 MB，直接入库会顶爆 `verify_ui [6]` 的 96 MB 预算
     （实测入库前 88.28 MB，余量 7.7 MB）⇒ 先做**不改尺寸**的降色深。
     实测（板 01）：507 KB → 207 KB（−59%）；逐通道 RMSE R2.20/G2.21/B2.34/A1.19、最大偏差 3/255，
     **alpha 包围盒仅内缩约 2–3 px**（α≤3 的不可见外缘），可见范围与观感不变。
   · 不做调色板（`convert('P')`）量化：实测 FASTOCTREE 会把**全透明像素**（α=0）也塞进调色板
     ⇒ alpha 包围盒由 (3,6,1037,602) 变 (0,0,1044,602)、透明边被"污染"成有 α 的薄雾，
     且本资产集现存 **0 件 P 模式**（1268 RGBA / 4 RGB），引入索引色是未验证的新类别 ⇒ 不用。

2. **22 加载提示**（源 `AI中文化\2x\otv_loading_cn.png`，640×240）
   → `x_ui_psv_loading.png`（**逐字节复制**，体积仅 0.07 MB，无需优化）。
   · 墨迹实测 `x69..574 × y68..172`（505×104），**在 640×240 画布内居中**（左 69 / 右 66、上 68 / 下 68）
     ⇒ 画布居中摆放即墨迹居中。图上烘焙文字经放大复核为「**载入中…**」（三字 + 空心圆省略号，字形完整）。

3. **36 选择支**（源 `超分2x\otv_selwin.png`，1300×386）
   → `x_ui_psv_choice_2state.png`（**逐字节复制**，源的留档）。
   → 拆两态 `x_ui_psv_choice_norm.png`（蓝紫＝常态）/ `x_ui_psv_choice_sel.png`（粉＝悬停/按下）。
   · **拆件铁律（会话交接_20260920_UI组 §5）**：「压缩素材必须整图统一倍率缩放后按网格切分，
     禁止逐件裁 bbox 再逐个归一化」。本件 **统一倍率 = 1.0**（PSV 2× 即本作画布口径，1:1 上屏）
     ⇒ 只做**整数像素裁切 + 居中对齐到公共画布**，全程无重采样。
   · ★ **修复轮（ISSUE-20260926_06 A 基础组修复）重裁两态**：x/y 用**两个独立 α 阈值**取窗 ——
     · **水平 α≥2（`CHOICE_X_TH=1`）**：把胶囊**端帽与羽尖的柔光全含**（旧版 α≥16 在
       `norm` 右端切掉 7px、`sel` 左端切掉 7px 的羽尖柔光 ⇒ vision 判「端帽破口＝白缺＋第二道轮廓」）。
       实测该窗 `sel x4..1241`（1238）、`norm x54..1287`（1234），均 ≤ 公共画布宽 1240。
     · **纵向 α≥11（`CHOICE_Y_TH=10`）**：128 行是**画布硬约束**（`item_h=128` ⇒ 6 行 = 6×128+5×2 = 778
       才落在画布内；`item_h` 一旦 >130 则 6 行必溢出 1080）⇒ 取「仍能整窗装进 128 行」的最小阈值。
       实测该阈值下两态纵向**恰好 128 行**（`sel y8..135` / `norm y167..294`），被舍掉的只有 α≤10
       （0.4% 不透明度、不可见）的边行。
     两态仍**居中到公共画布**：贴后两态内容中心同为画布 x619.5（水平零跳位，沿用旧口径）。
     ★ 残留（**如实登记，本轮未改**）：源图内两胶囊**纵向位置本身相差 4px**（板体 114 高：粉画布 y5..118 /
       蓝 y9..122）⇒ 换态仍有 4px 纵向跳位。该 4px 来自源件构图、非拆件引入（旧版同值），且纵向窗已满
       128 行、无余量平移（平移即裁掉羽尖柔光）⇒ 交主代理裁决是否接受。
     旧版口径（α≥16 单阈值 + 各裁各居中）实测：粉 `x11..1237 × y9..133`、蓝 `x57..1279 × y169..293`。
   · ★ 公共画布而非各裁各放：两胶囊在源图内**水平相差 44 px**（粉中心 x624 / 蓝中心 x668），
     各裁各放会让蓝紫条比粉条右移 44 px、悬停即"跳一下"。
   · 底部一排 **5 枚羽毛光标翼**（y≈319..378）**不拆**：本作选择支无该组件（悬停态即整条换图）。

用法（**在 UI 组根目录**跑）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\psv_make_assets.py [--check]
      --check  只比对磁盘现状与将要写出的结果（不落盘），差异即退出码 1
"""
from __future__ import annotations

import argparse
import io
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
PSV = os.path.join(UI, "PSV系统UI参考")
OUT = os.path.join(UI, "krkr", "assets", "ui")

# ---- 21 确认框：22 张板（高 602 = 含板外底部白羽 YES/NO 徽章带；高 540 = 无）----
CFM = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
       "20", "21", "22", "23", "24", "25", "42", "43", "44", "45"]
CFM_WITH_YESNO = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
                  "25", "43", "44"}          # 15 张，源件高 602（含**板外**徽章带）→ 裁为 540
CFM_CROP_H = 540                              # 板体 y6..534 全含；丢掉 y540..601 的板外徽章带
COLOR_DEPTH_KEEP = 6                          # 每通道保留高 6 位（v & 0xFC）

SELWIN = os.path.join(PSV, "超分2x", "otv_selwin.png")
CHOICE_X_TH = 1                               # 水平窗阈值：α≥2（端帽/羽尖柔光全含）
CHOICE_Y_TH = 10                              # 纵向窗阈值：α≥11（128 行画布硬约束下的最小阈值）
CHOICE_CANVAS = (1240, 128)                   # 两态公共画布（>= 各自实测窗）
CHOICE_BANDS = {                              # 名 → (y0, y1) 纵向分带（源图内，互不重叠）
    "norm": (163, 315),                       # 蓝紫＝常态
    "sel":  (1, 160),                         # 粉  ＝悬停/按下
}


def q6(im: Image.Image) -> Image.Image:
    """**板块族既有约定**：四通道一律降 6bit（`v & 0xFC`，**不改尺寸**、不动布局）。

    ★ 为什么板块沿用「含 alpha 的 6bit」而不改口径：这是本族**盘上现状**（22 张板入库时即此口径，
      实测逐通道 RMSE ≤2.34、最大偏差 3/255，alpha 包围盒仅内缩约 2–3 px 的 α≤3 不可见外缘）。
      **本轮只裁高度、不重定编码口径** ⇒ 裁后各板 alpha 与**裁前盘上 alpha 逐字节相同**
      （`& 0xFC` 与 `crop` 可交换，断言见 `main()`）⇒ **本轮零新增 alpha 损失**。
    """
    return im.point(lambda v: v & 0xFC)


def q6_rgb(im: Image.Image) -> Image.Image:
    """RGB 三通道降 6bit（`v & 0xFC`），**alpha 逐像素原样保留**（不许有损）。

    用于本轮**新产出/重裁**的件（22 加载、36 两态）——盘上这两族现状即此口径
    （实测 RGB 最大偏差 3/255、alpha 偏差 0）⇒ 重跑**逐字节幂等**。
    """
    out = im.convert("RGB").point(lambda v: v & 0xFC).convert("RGBA")
    out.putalpha(im.getchannel("A"))
    return out


def png_bytes(im: Image.Image) -> bytes:
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def band_extent(im: Image.Image, y0: int, y1: int, x_th: int, y_th: int):
    """在 y0..y1 分带内取**双阈值**窗：x 用 `x_th`、y 用 `y_th`（**按阈值扫像素**）。

    ⚠️ 不能用 `alpha.crop().getbbox()`：它把**任何非零 α** 都算墨迹 ⇒ 会把整条极淡的外晕
    （α=1..15）也框进来（旧版实测 th=16 得 1227×126，而 getbbox 版会得 1238×137、并撞上公共画布）。
    ★ 为何 x/y 用两个阈值：水平要**把端帽与羽尖的柔光全含**（vision 判「破口」的两端），
      纵向则受 128 行画布硬约束 —— 详见模块 docstring §3 修复轮说明。
    返回 (x0, y0, x1, y1)（右下开区间）。
    """
    px = im.load()
    W = im.size[0]
    x0 = x1 = None
    ya0, ya1 = None, None
    for y in range(y0, y1):
        for x in range(W):
            a = px[x, y][3]
            if a > x_th:
                if x0 is None or x < x0:
                    x0 = x
                if x1 is None or x + 1 > x1:
                    x1 = x + 1
            if a > y_th:
                if ya0 is None or y < ya0:
                    ya0 = y
                if ya1 is None or y + 1 > ya1:
                    ya1 = y + 1
    if x0 is None or ya0 is None:
        raise SystemExit("[FAIL] 分带 y=%d..%d 内没有 α>x=%d / α>y=%d 的像素" % (y0, y1, x_th, y_th))
    return (x0, ya0, x1, ya1)


def build_choice_states():
    """拆两态 → ([(名, 输出画布, 源窗), ...], 源尺寸, 自证行清单)。"""
    im = Image.open(SELWIN).convert("RGBA")
    cw, ch = CHOICE_CANVAS
    out, report = [], []
    for name, (y0, y1) in CHOICE_BANDS.items():
        w = band_extent(im, y0, y1, CHOICE_X_TH, CHOICE_Y_TH)
        crop = im.crop(w)
        if crop.size[0] > cw or crop.size[1] > ch:
            raise SystemExit("[FAIL] %s 裁件 %s 超出公共画布 %s" % (name, crop.size, CHOICE_CANVAS))
        canvas = Image.new("RGBA", CHOICE_CANVAS, (0, 0, 0, 0))
        ox, oy = (cw - crop.size[0]) // 2, (ch - crop.size[1]) // 2
        canvas.paste(crop, (ox, oy))
        # ── 自证：窗**外**残留的最大 α（水平按 X 阈值、纵向按 Y 阈值分别复算）──
        px = im.load()
        rest_x = rest_y = 0
        for y in range(y0, y1):
            for x in range(im.size[0]):
                a = px[x, y][3]
                if a > CHOICE_X_TH and not (w[0] <= x < w[2]):
                    rest_x = max(rest_x, a)
                if a > CHOICE_Y_TH and not (w[1] <= y < w[3]):
                    rest_y = max(rest_y, a)
        assert rest_x == 0 and rest_y == 0, (
            "%s：裁窗之外仍有 α>x=%d / α>y=%d 的像素（水平 max α=%d、纵向 max α=%d）"
            % (name, CHOICE_X_TH, CHOICE_Y_TH, rest_x, rest_y))
        # 纵向被舍掉的（α≤Y_TH）像素：计数 + 最大 α（口径自证）
        drop_n, drop_max = 0, 0
        for y in range(y0, y1):
            if w[1] <= y < w[3]:
                continue
            for x in range(im.size[0]):
                a = px[x, y][3]
                if a > 0:
                    drop_n += 1
                    drop_max = max(drop_max, a)
        report.append("端帽自证      ：%-4s 源窗 x%d..%d（%d×%d）→ 画布 (x+%d, y+%d)；"
                      "纵向舍 %d px（最大 α=%d ≤ %d）"
                      % (name, w[0], w[2] - 1, crop.size[0], crop.size[1], ox, oy,
                         drop_n, drop_max, CHOICE_Y_TH))
        out.append((name, canvas, w))
    return out, im.size, report


def plan():
    """返回 ([(输出文件名, PNG 字节, 说明)], [自证行])，**不落盘**。"""
    items = []
    for nn in CFM:
        src = os.path.join(PSV, "AI中文化", "2x", "otv_dlg_bg_%s_cn.png" % nn)
        if not os.path.exists(src):
            raise SystemExit("[FAIL] 缺源件 %s" % src)
        with Image.open(src) as im:
            im = im.convert("RGBA")
            want_src_h = 602 if nn in CFM_WITH_YESNO else 540
            if im.size != (1044, want_src_h):
                raise SystemExit("[FAIL] %s 尺寸 %s 与板型不符（602=含板外白羽徽章带 / 540=无）"
                                 % (src, im.size))
            cropped = ""
            if nn in CFM_WITH_YESNO:
                # ★ 修复轮：裁掉板体之外那对白羽 YES/NO 徽章带（y540..601）→ 1044×540。
                #   窗 (0,0,1044,540) 完整保留板体（y6..534）与**板内**烘焙 YES/NO（板内 y336..368）。
                b_full = len(png_bytes(q6(im)))
                im = im.crop((0, 0, 1044, CFM_CROP_H))
                cropped = "＋裁板外徽章带"
            data = png_bytes(q6(im))
            if nn in CFM_WITH_YESNO:
                cropped += "（%d→%d 字节，−%.0f%%）" % (
                    b_full, len(data), 100.0 * (1 - len(data) / float(b_full)))
            items.append(("x_ui_psv_cfm_%s.png" % nn, data,
                          "PSV 中文弹窗板 %s（%dx%d%s，降 6bit%s）"
                          % (nn, im.size[0], im.size[1],
                             "，板内仍含烘焙 YES/NO" if nn in CFM_WITH_YESNO else "，无 YES/NO",
                             cropped)))
    # 加载件：**重编码**为 6bit（RGB 6bit / alpha 原样）——与盘上现状逐字节相同（体积 43 KB，不必再省）
    lsrc = os.path.join(PSV, "AI中文化", "2x", "otv_loading_cn.png")
    with Image.open(lsrc) as li:
        items.append(("x_ui_psv_loading.png", png_bytes(q6_rgb(li.convert("RGBA"))),
                      "PSV「载入中…」加载牌 640×240（RGB 6bit / alpha 原样；与盘上现状逐字节相同）"))
    # ★ 两态源件 `x_ui_psv_choice_2state.png` **本脚本不写**：该**同名件已由姊妹脚本**
    #   `工具\m53_psv_ui_assets.py`（同一 ISSUE-20260926-06 的素材入库件）从**同一源**
    #   （`超分2x\otv_selwin.png` 1300×386）产出，且它做了一轮降色深（110,566 → 80,436 字节）。
    #   两个脚本写同一路径 ⇒ 谁后跑谁覆盖、内容在两种编码间摆动 ⇒ **本脚本退让，单写者 = m53**。
    #   本脚本的两个拆件**直接从参考区源件裁**（不经该入库件）⇒ 与本件是否被优化无关。
    states, sheet, report = build_choice_states()
    for name, canvas, w in states:
        items.append(("x_ui_psv_choice_%s.png" % name, png_bytes(q6_rgb(canvas)),
                      "PSV 选择支条·%s（源 %s 内窗 %s ⊂ 公共画布 %s；水平α≥%d / 纵向α≥%d；RGB 6bit / alpha 原样）"
                      % ({"norm": "常态(蓝紫)", "sel": "悬停/按下(粉)"}[name], sheet, w, CHOICE_CANVAS,
                         CHOICE_X_TH + 1, CHOICE_Y_TH + 1)))
    return items, report, states


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只比对、不落盘")
    args = ap.parse_args()

    items, report, states = plan()
    print("=" * 78)
    print("PSV 换皮素材入库（21 确认框 / 22 加载 / 36 选择支）")
    print("  源 %s" % PSV)
    print("  出 %s" % OUT)
    print("=" * 78)

    new_bytes = 0
    diff = []
    for fn, data, note in items:
        new_bytes += len(data)
        fp = os.path.join(OUT, fn)
        old = None
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                old = f.read()
        with Image.open(io.BytesIO(data)) as im:
            w, h = im.size
        mark = "同" if old == data else ("改" if old is not None else "新")
        if old != data:
            diff.append(fn)
        print("  [%s] %-30s %4dx%-4d %8.0f KB  %s" % (mark, fn, w, h, len(data) / 1024.0, note))
        if not args.check:
            os.makedirs(OUT, exist_ok=True)
            with open(fp, "wb") as f:
                f.write(data)

    # ---- 断言 ----
    print("-" * 78)
    n_cfm = len([1 for fn, _d, _n in items if fn.startswith("x_ui_psv_cfm_")])
    assert n_cfm == 22, "确认框板数应为 22，实为 %d" % n_cfm
    # ★ 修复轮断言 1：22 张板一律 1044×540（板体 y6..534 全含；板外徽章带已裁）
    for fn, data, _n in items:
        if not fn.startswith("x_ui_psv_cfm_"):
            continue
        with Image.open(io.BytesIO(data)) as im:
            assert im.size == (1044, CFM_CROP_H), "%s 应为 1044x%d，实为 %s" % (fn, CFM_CROP_H, im.size)
    # ★ 修复轮断言 2：两态拆件的水平端帽全含、纵向只丢不可见柔光（见下方「端帽自证」行）
    for line in report:
        print(line)
    # ★ 修复轮断言 3：**alpha 口径自证**（派单纪律：alpha 不许有损）
    #   · 板块族：alpha = 源 alpha & 0xFC（**盘上现状即此**，逐字节相同的可复算断言）
    #   · 加载/两态（本轮新产出）：alpha 逐像素 == 源 alpha（零损失）
    import numpy as _np
    for fn, data, _n in items:
        if fn.startswith("x_ui_psv_cfm_"):
            srcp = os.path.join(PSV, "AI中文化", "2x", "otv_dlg_bg_%s_cn.png" % fn[13:-4])
            with Image.open(srcp) as _s, Image.open(io.BytesIO(data)) as _o:
                _sa = _np.array(_s.convert("RGBA").getchannel("A")).astype(int)[0:CFM_CROP_H]
                _oa = _np.array(_o.getchannel("A")).astype(int)
            assert _oa.tolist() == ((_sa & 0xFC).tolist()), "%s 板块族 alpha 口径不符（应为 srcA & 0xFC）" % fn
        elif fn == "x_ui_psv_loading.png":
            with Image.open(os.path.join(PSV, "AI中文化", "2x", "otv_loading_cn.png")) as _s, \
                    Image.open(io.BytesIO(data)) as _o:
                assert (_np.array(_s.convert("RGBA").getchannel("A"))
                        == _np.array(_o.getchannel("A"))).all(), "%s alpha 有损" % fn
        elif fn.startswith("x_ui_psv_choice_"):
            _nm = "norm" if fn.endswith("norm.png") else "sel"
            _w = dict((n, w) for (n, _c, w) in states)[_nm]
            with Image.open(SELWIN) as _s, Image.open(io.BytesIO(data)) as _o:
                _sa = _np.array(_s.convert("RGBA").crop(_w).getchannel("A")).astype(int)
                _oa = _np.array(_o.getchannel("A")).astype(int)
            _oy, _ox = (CHOICE_CANVAS[1] - _sa.shape[0]) // 2, (CHOICE_CANVAS[0] - _sa.shape[1]) // 2
            _sub = _oa[_oy:_oy + _sa.shape[0], _ox:_ox + _sa.shape[1]]
            assert _sub.tolist() == _sa.tolist(), "%s alpha 有损（应与源逐像素相同）" % fn
            _pad_a = _oa[: _oy] if _oy else None
            assert _pad_a is None or _pad_a.max() == 0, "%s 画布上留白非全透明" % fn
    print("alpha 自证    ：板块族 = 源A & 0xFC（**与盘上现状逐字节相同 ⇒ 本轮零新增 alpha 损失**）；"
          "加载/两态 = 源 A 逐像素相同（零损失）")
    assert len([1 for fn, _d, _n in items if fn.startswith("x_ui_psv_choice_")]) == 2   # norm/sel 两态
    # ★ 修复轮（2026-09-26）改判：`x_ui_psv_choice_2state.png`（m53 的源件留档）**当前不在库中**
    #   —— 它在 `layout/screens/*.json`、`layout/ui_layout.json`、`复刻/asset_index.js` 中**零引用**
    #   （asset_index 只有被引用件），属 2026-09-26 06:15 之后被清理的未引用留档；
    #   本脚本两个拆件**直接从参考区源件裁**（不经该留档）⇒ 不构成依赖 ⇒ 由 assert 降级为提示，
    #   且**不代 m53 写该件**（单写者纪律：两个脚本写同一路径会互相覆盖）。
    if not os.path.exists(os.path.join(OUT, "x_ui_psv_choice_2state.png")):
        print("提示          ：x_ui_psv_choice_2state.png（m53 留档）不在库中 —— 本轮零引用、"
              "非本脚本依赖（两态直接从参考区源件裁），不代 m53 补写")
    pngs = sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in pngs)
    psv = [f for f in pngs if f.startswith("x_ui_psv_")]
    psv_b = sum(os.path.getsize(os.path.join(OUT, f)) for f in psv)
    print("本轮新增/更新：%d 件 / %.2f MB（其中确认框 %d 件）" % (len(items), new_bytes / 1048576.0, n_cfm))
    print("资产集现状    ：%d 件 / %.2f MB（预算 96 MB）｜ 其中 x_ui_psv_* %d 件 / %.2f MB"
          % (len(pngs), total / 1048576.0, len(psv), psv_b / 1048576.0))
    if os.path.exists(os.path.join(OUT, "x_ui_psv_cfm_01.png")):
        # 降色深自证：实测字节数（相对源件）
        src_b = os.path.getsize(os.path.join(PSV, "AI中文化", "2x", "otv_dlg_bg_01_cn.png"))
        got_b = os.path.getsize(os.path.join(OUT, "x_ui_psv_cfm_01.png"))
        print("降色深自证    ：板 01 源 %.0f KB → 出 %.0f KB（−%.0f%%）"
              % (src_b / 1024.0, got_b / 1024.0, 100.0 * (1 - got_b / float(src_b))))
    if total > 96 * 1024 * 1024:
        print("[FAIL] 资产集 %.2f MB 超出 96 MB 预算" % (total / 1048576.0))
        return 1
    if args.check and diff:
        print("[FAIL] --check：磁盘与预期不一致 %d 件：%s" % (len(diff), ", ".join(diff)))
        return 1
    print("结果：**通过**（%s）" % ("仅比对，未落盘" if args.check else "已落盘"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
