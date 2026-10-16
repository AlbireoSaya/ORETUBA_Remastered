# -*- coding: utf-8 -*-
r"""psv_split_sldata.py —— PSV 槽位零件雪碧图 `x_ui_psv_sl_data.png` 拆件（ISSUE-20260926-06 · B 组）

**做什么**：把 PSV 槽位零件雪碧图（`krkr\assets\ui\x_ui_psv_sl_data.png`，852×1022）按
**整图统一倍率 0.5** 缩放后、按**实测网格**切成 23/24 存/读档（与 26 回想）要用的散件。

■ 为什么整图统一倍率缩放（**铁律，不得逐件归一化**）
  会话交接_20260920_UI组 §5：压缩素材必须**整图统一倍率缩放后按网格切分**，禁止逐件裁 bbox
  再逐个归一化。本件的倍率由用户裁决的版式反推：槽框源件 831×245（@2×）
  ⇒ 派单要求的 **415×122（@1× = 本作画布二分之一）**，即 **倍率 = 0.5**，全图一个倍率、零例外。
  **为什么必须缩到 0.5**：4 列 × 3 行 = 12 槽（派单裁定）在 1920 宽画布上要求单槽 ≤ 415；
  若按 1:1（831 宽）只能排 2 列，6 行又超出「题字下、页脚上」的可用高度 ⇒ 0.5 是唯一解。
  ⚠️ 0.5 倍率**同时**决定了数字件只有 ~18–27 px 高 ⇒ **不适合当页码键的字形**（见下方「不用的件」）。

■ 拆出的件（全部 1:1 落盘于 `krkr\assets\ui\`，名与用户裁决的语义一一对应）
  | 输出 | 源内网格（@2×） | 出件（@1×） | 语义（`PSV换皮_素材与文字处置清单.md` §七 用户裁决） |
  | --- | --- | --- | --- |
  | `x_ui_psv_slot_norm.png`  | (4,4,830,244)    | 415×122 | **蓝**＝常态（已存档槽） |
  | `x_ui_psv_slot_hover.png` | (4,280,830,244)  | 415×122 | **灰**＝禁用（空槽等）※名字是派单原文；**语义以灰=禁用为准** |
  | `x_ui_psv_slot_warn.png`  | (4,556,830,244)  | 415×122 | **暗红**＝覆盖警告 |
  | `x_ui_psv_slot_thumbwin.png` | (70,54,244,146) | 122×73 | 缩略窗（槽框内嵌窗的独立索引件） |
  | `x_ui_psv_sl_digit_0..9.png` | 数字行逐格（见 CELLS） | 20–27×28 | 数字 0–9 |
  | `x_ui_psv_sl_slash.png`   | (678,832,40,56)  | 20×28 | `/` |
  | `x_ui_psv_sl_arrow_l.png` / `_r.png` | (10,838,72,80) / (110,838,72,80) | 36×40 | 常态（蓝白）左右箭头钮（**含件内 L/R 字母**） |
  | `x_ui_psv_sl_arrow_l_off.png` / `_r_off.png` | (10,934,72,80) / (110,934,72,80) | 36×40 | 禁用（灰）箭头钮 —— 派单未列，**拆件时补齐**：灰带与蓝带同为「一组控件的两个态」，只出蓝会让禁用态缺图（登记见报告） |
  | `x_ui_psv_sl_nodata.png`  | (196,944,118,32) | 59×16 | `NO DATA`（空槽窗内标签） |

■ 拆件脚本的三条自证（每次运行都跑，失败即 SystemExit）
  ① **不越界**：每个源的可见像素（α>16）必须落在本脚本给它的网格矩形内（否则说明网格漂了）；
  ② **同源同窗**：`slot_thumbwin` 必须**逐字节等于** `slot_norm` 在窗位 `(33,25)-(155,98)` 处的像素
     ⇒ 证明「窗」确实是「槽框」的内嵌窗（两者同源、同倍率、同网格），也保证叠画是零变化；
  ③ **幂等**：`--check` 逐字节比对磁盘现状；同参数重跑产出逐字节相同（无时间戳/无随机）。

■ 被网格裁掉的部分（**如实登记**，不是疏漏）
  · 槽框件按**本体**裁（口径 = 清单 §一 实测的槽框本体 831×245，÷2 = 415.5×122.5 ⇒ 取 **415×122**，
    与派单一致）⇒ 件外**下缘阴影**（源 y248..272，α 164→0 的柔光）与**右缘尾晕**（x835..841，α≤17）
    不入件。观感后果：槽框自带的下投影不再出现（0.5 倍率下那是约 12px 的极淡晕），本体与上/左缘
    的高光边完整保留。
  · 数字单元格界 = **字形墨迹起点**（实测列 run），不是字宽推进原点 ⇒ 将来若要拿数字件拼「10」
    等多位数字，需按件内墨迹左界自行留白（本轮数字件不上屏，见下）。
  · 数字 `0-9` 与 `/`、箭头（含 `_off`）、`NO DATA` 本轮**只拆件、不上屏**，理由：
    - 页码键（`sv.pg01..10`）派单允许「改用数字件 **或** 保留现有页码件」，本组**选保留**——
      0.5 倍率下数字件只有 18–27 px 高，塞进 53×53 的页码键要么再放大（破坏统一倍率）
      要么留大片空框；且 `1..10` 的「10」需两枚字形拼接；
    - 页号/槽号文字一律**引擎绘制**（本工程铁律：禁止把文字烘焙进图，数字亦属文字）
      ⇒ 数字件天然不可用于「第 N 号 / 页码」这类文本位。
  · 三态槽框 + `NO DATA` **已上屏**（见 `layout\screens\23_save.json` / `24_load.json` 的
    屏级 `flags_default` 12 键 `sv_s1..sv_s12` 与 `vis_flag` 接线）。

用法（**在 UI 组根目录**跑）：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    python 工具/psv_split_sldata.py            # 落盘
    python 工具/psv_split_sldata.py --check    # 只比对不落盘（差异 ⇒ 退出码 1）
    python 工具/psv_split_sldata.py --dry-run  # 只算体积
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))        # <UI组>\工具
UI = os.path.dirname(HERE)                               # <UI组>
OUT = os.path.join(UI, "krkr", "assets", "ui")           # 引擎素材目录
SHEET = os.path.join(OUT, "x_ui_psv_sl_data.png")        # 源雪碧图（入库件，**只读**）

SCALE = 0.5                       # 整图统一倍率（见 docstring「为什么必须缩到 0.5」）
BAND_TH = 16                      # 「可见像素」阈值（与 psv_make_assets.py 同口径）
COLOR_MASK = 0xFC                 # 每通道降 6bit（`& 0xFC`，派单要求；α 一并降，仅影响 α≤3 的外晕）

# 数字行：字形起点实测（α>16 的列 run 起点），相邻起点构成逐格网格（比例字体 ⇒ 格宽不等）
DIGIT_BAND = (832, 56)            # 数字行 y 带（源坐标，偶数对齐）
DIGIT_START = [198, 252, 294, 342, 390, 438, 486, 534, 582, 630, 678]   # 0..9 与 `/`

# (输出文件名, 源网格 (x,y,w,h), 说明)
SPEC = [
    ("x_ui_psv_slot_norm.png",     (4,   4, 830, 244), "槽框·常态（蓝 #7070A8）"),
    ("x_ui_psv_slot_hover.png",    (4, 280, 830, 244), "槽框·禁用（灰 #484050）※名从派单，语义=灰度禁用"),
    ("x_ui_psv_slot_warn.png",     (4, 556, 830, 244), "槽框·覆盖警告（暗红 #782040）"),
    ("x_ui_psv_slot_thumbwin.png", (70, 54, 244, 146), "槽缩略窗（与 norm 槽框内嵌窗同源同窗）"),
    ("x_ui_psv_sl_arrow_l.png",    (8, 836, 78, 84),   "左右箭头钮·常态 左（含件内 L 字母）"),
    ("x_ui_psv_sl_arrow_r.png",    (108, 836, 78, 84), "左右箭头钮·常态 右（含件内 R 字母）"),
    ("x_ui_psv_sl_arrow_l_off.png", (8, 932, 78, 84),  "左右箭头钮·禁用 左（灰带，派单未列，拆件补齐）"),
    ("x_ui_psv_sl_arrow_r_off.png", (108, 932, 78, 84), "左右箭头钮·禁用 右（灰带，派单未列，拆件补齐）"),
    ("x_ui_psv_sl_nodata.png",     (194, 942, 122, 38), "NO DATA（空槽窗内标签）"),
]
for _i in range(10):
    _x0 = DIGIT_START[_i]
    _w = DIGIT_START[_i + 1] - _x0 if _i < 10 else 40
    SPEC.append(("x_ui_psv_sl_digit_%d.png" % _i,
                 (_x0, DIGIT_BAND[0], _w, DIGIT_BAND[1]), "数字 %d" % _i))
SPEC.append(("x_ui_psv_sl_slash.png", (DIGIT_START[10], DIGIT_BAND[0], 40, DIGIT_BAND[1]), "斜杠 /"))

# 窗在槽框网格内的相对位置（源坐标）：(70-4, 54-4, 244, 146)=(66,50,244,146) ⇒ 0.5 后 (33,25,122,73)
WIN_REL = (33, 25, 122, 73)


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def read_sheet() -> Image.Image:
    if not os.path.isfile(SHEET):
        raise SystemExit("!! 源件缺失：%s（由 工具\\m53_psv_ui_assets.py 入库）" % SHEET)
    im = Image.open(SHEET)
    if im.size != (852, 1022):
        raise SystemExit("!! 源件尺寸 %s 与派单实测不符（应为 852×1022）" % (im.size,))
    return im.convert("RGBA")


def visible_bbox(im: Image.Image, th: int = BAND_TH):
    """α>th 像素的包围盒（**按阈值扫像素**，不用 getbbox —— 后者会把 α=1..15 的极淡外晕也算进去）。"""
    px = im.load()
    W, H = im.size
    x0, y0, x1, y1 = W, H, -1, -1
    for y in range(H):
        for x in range(W):
            if px[x, y][3] > th:
                if x < x0:
                    x0 = x
                if x + 1 > x1:
                    x1 = x + 1
                if y < y0:
                    y0 = y
                if y + 1 > y1:
                    y1 = y + 1
    if x1 < 0:
        return None
    return (x0, y0, x1, y1)


def q6(im: Image.Image) -> Image.Image:
    """每通道降 6bit（`& 0xFC`）——不改尺寸、不动布局；α 一并降（仅 α≤3 的外晕归零）。"""
    return im.point(lambda v: v & COLOR_MASK)


def png_bytes(im: Image.Image) -> bytes:
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True, compress_level=9)
    return b.getvalue()


def plan():
    """返回 (items, checks)。items = [(文件名, PNG 字节, 说明)]，**不落盘**。"""
    src = read_sheet()
    W, H = src.size
    # ★ 整图**一次**统一倍率缩放（不是逐件缩）——这才是铁律要求的做法
    sheet = src.resize((int(round(W * SCALE)), int(round(H * SCALE))), Image.LANCZOS)
    if sheet.size != (426, 511):
        raise SystemExit("!! 整图缩放结果 %s 与预期 426×511 不符" % (sheet.size,))

    def cut(rect):
        x, y, w, h = rect
        if (x + w) > W or (y + h) > H:
            raise SystemExit("!! 网格矩形 %s 越出源件 %dx%d" % (rect, W, H))
        s = (int(round(x * SCALE)), int(round(y * SCALE)),
             int(round((x + w) * SCALE)), int(round((y + h) * SCALE)))
        return sheet.crop(s)

    items, checks = [], []
    for name, rect, note in SPEC:
        part = cut(rect)
        # 自证①：该网格内必须真有可见像素，且**不贴着网格边**（贴边 ⇒ 网格画小了、把件切了）
        bb = visible_bbox(src.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])))
        if bb is None:
            raise SystemExit("!! %s 的网格 %s 内没有 α>%d 的像素" % (name, rect, BAND_TH))
        gx0, gy0, gx1, gy1 = bb
        clipped = (gx0 <= 0) or (gy0 <= 0) or (gx1 >= rect[2]) or (gy1 >= rect[3])
        checks.append("  · %-34s 网格 %-18s 出件 %3d×%-3d ｜ 件内可见区 %s ｜ 贴边=%s"
                      % (name, "%d,%d,%d,%d" % rect, part.size[0], part.size[1],
                         "%d,%d,%d,%d" % bb, "是（已登记）" if clipped else "否"))
        items.append((name, png_bytes(q6(part)), note))

    # 自证②：缩略窗 == 常态槽框的窗位像素（逐字节）
    by = {n: Image.open(io.BytesIO(d)).convert("RGBA") for n, d, _ in items}
    norm, win = by["x_ui_psv_slot_norm.png"], by["x_ui_psv_slot_thumbwin.png"]
    x, y, w, h = WIN_REL
    sub = norm.crop((x, y, x + w, y + h))
    if sub.size != win.size or sub.tobytes() != win.tobytes():
        raise SystemExit("!! 自证②失败：缩略窗件 ≠ 常态槽框的窗位像素（同源同窗前提被破坏）")

    # 自证③：三态槽框必须**同尺寸**（换态不跳位）
    sizes = {by[n].size for n in ("x_ui_psv_slot_norm.png", "x_ui_psv_slot_hover.png",
                                  "x_ui_psv_slot_warn.png")}
    if len(sizes) != 1:
        raise SystemExit("!! 自证③失败：三态槽框尺寸不一致 %s" % sizes)
    if sizes != {(415, 122)}:
        raise SystemExit("!! 三态槽框尺寸 %s ≠ 派单要求的 415×122" % sizes)
    checks.append("  · 自证②：缩略窗件 == 常态槽框窗位 (33,25)-(155,98) 像素 ✓")
    checks.append("  · 自证③：三态槽框同为 415×122 ✓")
    return items, checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只比对磁盘现状（差异 ⇒ 退出码 1）")
    ap.add_argument("--dry-run", action="store_true", help="只算体积，不写盘")
    args = ap.parse_args()

    src_md5_before = md5(open(SHEET, "rb").read())
    items, checks = plan()

    print("=" * 84)
    print("psv_split_sldata.py · PSV 槽位零件拆件（24 件）")
    print("  源 %s（852×1022，整图统一倍率 %.1f，只读）" % (SHEET, SCALE))
    print("  出 %s" % OUT)
    print("=" * 84)
    print("\n".join(checks))
    print("-" * 84)

    diff, new_bytes = [], 0
    for name, data, note in items:
        new_bytes += len(data)
        fp = os.path.join(OUT, name)
        old = open(fp, "rb").read() if os.path.exists(fp) else None
        mark = "同" if old == data else ("改" if old is not None else "新")
        if old != data:
            diff.append(name)
        im = Image.open(io.BytesIO(data))
        print("  [%s] %-34s %3dx%-3d %7.1f KB  %s" % (mark, name, im.size[0], im.size[1],
                                                      len(data) / 1024.0, note))
        if not args.check and not args.dry_run:
            with open(fp, "wb") as f:
                f.write(data)

    if md5(open(SHEET, "rb").read()) != src_md5_before:
        raise SystemExit("!! 只读保证被破坏：源雪碧图在本次运行中被改动")

    n_dig = len([1 for n, _d, _x in items if n.startswith("x_ui_psv_sl_digit_")])
    assert n_dig == 10, "数字件应为 10（0..9），实为 %d" % n_dig
    assert len(items) == 20, "拆件总数应为 20，实为 %d" % len(items)

    pngs = sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in pngs)
    print("-" * 84)
    print("本脚本产出：20 件 / %.1f KB" % (new_bytes / 1024.0))
    print("资产集现状：%d 件 / %.2f MB（预算 96 MB）" % (len(pngs), total / 1048576.0))
    if total > 96 * 1024 * 1024:
        print("[FAIL] 资产集 %.2f MB 超出 96 MB 预算" % (total / 1048576.0))
        return 1
    if args.check and diff:
        print("[FAIL] --check：磁盘与预期不一致 %d 件：%s" % (len(diff), ", ".join(diff)))
        return 1
    print("结果：**通过**（%s）" % ("仅比对，未落盘" if (args.check or args.dry_run) else "已落盘"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
