# -*- coding: utf-8 -*-
r"""m53_psv_ui_assets.py —— PSV 系统 UI 素材入库整流（ISSUE-20260926-06 / M53）

**做什么**：把 `PSV系统UI参考\`（参考区，**只读**）里的 PSV 系统 UI 件，按我方口径
裁切/整流后落盘到 `krkr\assets\ui\`（引擎目录），文件名统一加 `x_ui_psv_` 前缀，
登记进 `工具\emit_asset_index.py` 的 `GROUPS`（否则会落进「其它」组）。

**口径依据**（不得凭印象改）：
  · `UI组\PSV换皮_素材与文字处置清单.md` §七「用户裁决」（2026-09-26，优先于该文建议）
  · `UI组\layout\_schema.md`（元素/素材契约：无 nine 时 w/h 必须 == PNG 实尺寸）
  · `UI组\会话交接_20260924_UI优化开工.md`（闸门与纪律）

**画布口径**：PSV 全屏 2× = 1920×1088（960×544 ×2）；我方画布 1920×1080
  ⇒ 上下各去 4px（`SCREEN_2X = 1088`、`CROP_Y = (1088-1080)//2 = 4`）。

★ **与派单原文的一处有据偏离（bklog 裁切）**：派单写「上下各去 35px」（1150→1080）。
  实测该裁法把 `otv_bklog.png` 的**屏下 overscan 区**（源 y1089..1150，含页脚日文两枚图标，
  见 `evidence\` 对比图）带进画面：裁后**底部 26 行有 86% 的像素为全透明**（整行全透明 1 行），
  = 全屏底图底部一条透明带；且内容板中心落到 y509（偏离画面中心 31px），
  与派单自述的「以内容板为中心」不符。
  **本脚本按屏区裁**：`0..1088` 对称去 4px ⇒ 内容板 146..934（中心 540 = 精确居中）、
  全透明行 0、滚动条完整。偏离的几何证据由 `--evidence` 产出，已随交付报告上报主代理。

**优化口径**（派单要求：超预算时「先优化（PNG 量化/降色深，不改尺寸），把新增体积压到最低」）：
  · 一律 **PNG-32 真 alpha（RGBA，绝不落 P 模式）**，尺寸不改；
  · `--mode q2`（默认）：RGB 三通道**各量化到 step=2**（每通道最大误差 **1/255**），
    alpha 通道**逐像素原样保留**（不量化）⇒ 深色/软渐变底图可读性不变，肉眼不可辨；
  · `--mode lossless`：只做 `optimize=True, compress_level=9`。
  两种模式的逐件体积都会打印，便于主代理复核「优化前后体积」。

**只读保证**：脚本**不写参考区**（运行时记录参考区源件 md5，结束再校验一次，不一致即报错）。

用法：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\m53_psv_ui_assets.py                 :: 落盘（默认 q2）
    python 工具\m53_psv_ui_assets.py --mode lossless :: 仅重压缩
    python 工具\m53_psv_ui_assets.py --dry-run       :: 只算体积，不写盘
    python 工具\m53_psv_ui_assets.py --evidence      :: 顺带产出裁切几何证据图
"""
import argparse
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))          # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                           # <UI组>
REF = os.path.join(UI_GROUP, "PSV系统UI参考")                # 参考区（只读）
OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")        # 引擎目录（写入）
EVID = os.path.join(UI_GROUP, "_工作", "ISSUE-20260926-06_PSV素材入库")

SCREEN_W, SCREEN_H = 1920, 1088     # PSV 全屏 2× 实尺寸
CANVAS_W, CANVAS_H = 1920, 1080     # 我方画布
CROP_Y = (SCREEN_H - CANVAS_H) // 2  # = 4，上下各去 4px

# 参考区原件（必须逐字节不变）
SRC_FILES = [
    "AI中文化/2x/otv_save_bg_cn.png",
    "AI中文化/2x/otv_load_bg_cn.png",
    "AI中文化/2x/otv_quick_load_bg_cn.png",
    "超分2x/otv_bklog.png",
    "去字件/2x/bgc01_page.png",
    "去字件/2x/bgc02_page.png",
    "超分2x/otv_dlg_bg_26.png",
    "超分2x/otv_selwin.png",
    "超分2x/otv_gm_bg1.png",
    "超分2x/otv_mu_bg.png",
    "超分2x/otv_mv_bg.png",
    "超分2x/otv_gm_bg.png",
    "超分2x/otv_sl_data.png",
] + ["去字件/2x/bgc01_pill_%02d.png" % n for n in range(1, 9)] \
  + ["去字件/2x/bgc02_pill_%02d.png" % n for n in range(1, 7)] \
  + ["去字件/2x/bgc01_slider_01.png"] \
  + ["去字件/2x/bgc02_slider_%02d.png" % n for n in range(1, 5)]

# 屏区裁切（上下各去 4px）——save/load/quick_load/cfg 两页
BOX_SCREEN_1088 = (0, CROP_Y, SCREEN_W, CROP_Y + CANVAS_H)
# 只取屏区 y0..1080（长卷类，派单原文；屏区为 0..1088，故只丢屏底 8px 背景）
BOX_TOP_1080 = (0, 0, SCREEN_W, CANVAS_H)
# bklog：源 1150 高 = 屏区 0..1088 ＋ 屏下 overscan 31px ⇒ 按屏区对称去 4px
BOX_BKLOG = (0, CROP_Y, SCREEN_W, CROP_Y + CANVAS_H)

# (目标文件名, 源相对路径, 裁切框 or None, 期望尺寸, 用途说明)
SPEC = [
    ("x_ui_psv_save_bg.png",        "AI中文化/2x/otv_save_bg_cn.png",       BOX_SCREEN_1088, (1920, 1080), "23 存档页底（中文页脚版）"),
    ("x_ui_psv_load_bg.png",        "AI中文化/2x/otv_load_bg_cn.png",       BOX_SCREEN_1088, (1920, 1080), "24 读档页底（中文页脚版）"),
    ("x_ui_psv_quick_load_bg.png",  "AI中文化/2x/otv_quick_load_bg_cn.png", BOX_SCREEN_1088, (1920, 1080), "快速读档页底（中文页脚版）"),
    ("x_ui_psv_backlog_bg.png",     "超分2x/otv_bklog.png",                 BOX_BKLOG,       (1920, 1080), "26 通话记录底（屏区裁，内容板居中）"),
    ("x_ui_psv_cfg_page1.png",      "去字件/2x/bgc01_page.png",             BOX_SCREEN_1088, (1920, 1080), "25 设置页1底（去字件）"),
    ("x_ui_psv_cfg_page2.png",      "去字件/2x/bgc02_page.png",             BOX_SCREEN_1088, (1920, 1080), "25 设置页2底（去字件）"),
    ("x_ui_psv_confirm_blank.png",  "超分2x/otv_dlg_bg_26.png",             None,            (1044, 540),  "21 确认框空白板（无字）"),
    ("x_ui_psv_choice_2state.png",  "超分2x/otv_selwin.png",                None,            (1300, 386),  "36 选择支两态条"),
    ("x_ui_psv_gal_shell.png",      "超分2x/otv_gm_bg1.png",                BOX_TOP_1080,    (1920, 1080), "39 鉴赏外壳（只取屏区）"),
    ("x_ui_psv_music_bg.png",       "超分2x/otv_mu_bg.png",                 BOX_TOP_1080,    (1920, 1080), "28 BGM 鉴赏结构（只取屏区）"),
    ("x_ui_psv_replay_bg.png",      "超分2x/otv_mv_bg.png",                 BOX_TOP_1080,    (1920, 1080), "38 情景回想结构（只取屏区）"),
    ("x_ui_psv_dress_bg.png",       "超分2x/otv_gm_bg.png",                 BOX_TOP_1080,    (1920, 1080), "37 立绘鉴赏结构（只取屏区）"),
    ("x_ui_psv_sl_data.png",        "超分2x/otv_sl_data.png",               None,            (852, 1022),  "23/24 槽位零件（原件入库，拆件留槽位模块）"),
]
# ★ 2026-09-27（ISSUE-20260926-09）退册：14 件药丸已并入一支共用件 x_ui_psv_pill_blank.png（旧件已归档）
# SPEC += [("x_ui_psv_pill_c1_%02d.png" % n, "去字件/2x/bgc01_pill_%02d.png" % n, None, (560, 72),
#           "25 设置页1 无字药丸壳") for n in range(1, 9)]
# ★ 2026-09-27（ISSUE-20260926-09）退册：14 件药丸已并入一支共用件 x_ui_psv_pill_blank.png（旧件已归档）
# SPEC += [("x_ui_psv_pill_c2_%02d.png" % n, "去字件/2x/bgc02_pill_%02d.png" % n, None, (560, 72),
#           "25 设置页2 无字药丸壳") for n in range(1, 7)]
SPEC += [("x_ui_psv_slider_c1.png", "去字件/2x/bgc01_slider_01.png", None, (720, 60), "25 设置页1 滑槽")]
SPEC += [("x_ui_psv_slider_c2_%02d.png" % n, "去字件/2x/bgc02_slider_%02d.png" % n, None, (720, 60),
          "25 设置页2 滑槽") for n in range(1, 5)]

# 机型校验锚（派单表里的源尺寸，实测不符即报错——防止参考区被上游改动后静默错裁）
SRC_SIZE_EXPECT = {
    "AI中文化/2x/otv_save_bg_cn.png": (1920, 1088),
    "AI中文化/2x/otv_load_bg_cn.png": (1920, 1088),
    "AI中文化/2x/otv_quick_load_bg_cn.png": (1920, 1088),
    "超分2x/otv_bklog.png": (1920, 1150),
    "去字件/2x/bgc01_page.png": (1920, 1088),
    "去字件/2x/bgc02_page.png": (1920, 1088),
    "超分2x/otv_dlg_bg_26.png": (1044, 540),
    "超分2x/otv_selwin.png": (1300, 386),
    "超分2x/otv_gm_bg1.png": (1920, 1318),
    "超分2x/otv_mu_bg.png": (1920, 3252),
    "超分2x/otv_mv_bg.png": (1920, 1764),
    "超分2x/otv_gm_bg.png": (1920, 3398),
    "超分2x/otv_sl_data.png": (852, 1022),
}

# 派单口径的版面几何（2× 源码坐标），用于「裁后不丢件」断言
BKLOG_BOARD = (157, 150, 1761, 938)      # 内容板高光边框
BKLOG_SCROLLBAR = (1712, 231, 1734, 880)  # 滚动条槽


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def load_src(rel):
    p = os.path.join(REF, rel)
    if not os.path.isfile(p):
        raise SystemExit("!! 源件缺失：%s" % p)
    im = Image.open(p)
    exp = SRC_SIZE_EXPECT.get(rel)
    if exp and im.size != exp:
        raise SystemExit("!! 源件尺寸与派单表不符：%s 实测 %s，派单 %s" % (rel, im.size, exp))
    return im


def to_rgba(im, box):
    if box is not None:
        im = im.crop(box)
    if im.mode != "RGBA":
        im = im.convert("RGBA")     # otv_save_bg_cn.png 为 RGB ⇒ 补不透明 alpha（源本身无透明信息）
    return im


def encode(im, step=0):
    """step=0 无损；step=2/4 把 RGB 三通道量化到该步长（alpha 通道原样保留）"""
    if step > 1:
        r, g, b, a = im.split()
        f = lambda v: min(255, ((v + step // 2) // step) * step)   # noqa: E731
        im = Image.merge("RGBA", (r.point(f), g.point(f), b.point(f), a))
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def check_source_untouched(before):
    now = {rel: md5(os.path.join(REF, rel)) for rel in SRC_FILES}
    bad = [r for r in SRC_FILES if before.get(r) != now[r]]
    if bad:
        raise SystemExit("!! 参考区源件被改动（只读保证被破坏）：%s" % ", ".join(bad))


def evidence(mode):
    """产出 bklog 裁切几何证据：35/35（派单原文） vs 4/4（本脚本，按屏区）"""
    os.makedirs(EVID, exist_ok=True)
    im = Image.open(os.path.join(REF, "超分2x/otv_bklog.png")).convert("RGBA")
    lines = []
    for tag, box in [("A_派单原文_上下各35", (0, 35, 1920, 1115)),
                     ("B_本脚本_按屏区_上下各4", BOX_BKLOG)]:
        c = im.crop(box)
        bottom = c.crop((0, 1000, 1920, 1080))
        flat = Image.new("RGBA", bottom.size, (255, 0, 255, 255))
        flat.alpha_composite(bottom)
        flat.convert("RGB").save(os.path.join(EVID, "bklog_%s_底80行.png" % tag))
        a = Image.frombytes("L", (c.width, c.height), c.tobytes()[3::4])
        trans = sum(1 for y in range(c.height) if a.crop((0, y, 1920, y + 1)).getbbox() is None)
        band = a.crop((0, c.height - 26, 1920, c.height))
        band_trans = sum(1 for v in band.tobytes() if v == 0) * 100.0 / (band.width * band.height)
        board_y = (BKLOG_BOARD[1] - box[1], BKLOG_BOARD[3] - box[1])
        scroll_y = (BKLOG_SCROLLBAR[1] - box[1], BKLOG_SCROLLBAR[3] - box[1])
        ok_in = 0 <= board_y[0] and board_y[1] <= c.height and 0 <= scroll_y[0] and scroll_y[1] <= c.height
        lines.append("%s：裁后尺寸 %s ｜ 整行全透明 %d 行 ｜ 末 26 行透明像素占比 %.2f%%"
                     " ｜ 内容板 y%d..%d（中心 %.1f，画面中心 540）"
                     " ｜ 滚动条 y%d..%d ｜ 板/条完整 %s"
                     % (tag, c.size, trans, band_trans, board_y[0], board_y[1],
                        (board_y[0] + board_y[1]) / 2.0, scroll_y[0], scroll_y[1], ok_in))
    txt = "bklog 裁切几何对比（源 1920x1150，PSV 屏区 = y0..1088）\n" + "\n".join(lines) + "\n"
    open(os.path.join(EVID, "bklog_裁切几何对比.txt"), "w", encoding="utf-8").write(txt)
    print(txt)
    print("证据图：%s" % EVID)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["lossless", "q2", "q4"], default="q2",
                    help="q2（默认）= RGB 通道量化 step=2（maxΔ=1）；q4 = step=4（maxΔ=2）；lossless = 只重压缩")
    ap.add_argument("--dry-run", action="store_true", help="只算体积，不写盘")
    ap.add_argument("--evidence", action="store_true", help="顺带产出 bklog 裁切几何证据")
    args = ap.parse_args()
    STEP = {"lossless": 0, "q2": 2, "q4": 4}[args.mode]

    if args.evidence:
        evidence(args.mode)

    src_before = {rel: md5(os.path.join(REF, rel)) for rel in SRC_FILES}
    rows, tot = [], {"lossless": 0, "q2": 0, "q4": 0, "src": 0, "out": 0}
    for dest, rel, box, exp, note in SPEC:
        im_src = load_src(rel)
        tot["src"] += os.path.getsize(os.path.join(REF, rel))
        im = to_rgba(im_src, box)
        if im.size != exp:
            raise SystemExit("!! 目标尺寸不符：%s 实测 %s，期望 %s" % (dest, im.size, exp))
        # ★ 契约：无 nine 时元素 w/h 必须 == PNG 实尺寸（_schema.md）
        if im.size[0] != exp[0] or im.size[1] != exp[1]:
            raise SystemExit("!! %s 尺寸断言失败" % dest)
        # ★ 全屏底图必须整幅覆盖：不得留全透明带（bklog 口径偏离的依据）
        if exp == (1920, 1080):
            a = im.getchannel("A")
            trans = sum(1 for y in range(im.height)
                        if a.crop((0, y, im.width, y + 1)).getbbox() is None)
            if trans:
                raise SystemExit("!! %s 裁后出现 %d 行全透明像素（全屏底图会露出透明带）" % (dest, trans))
        if dest == "x_ui_psv_backlog_bg.png":
            for nm, (x0, y0, x1, y1) in [("内容板", BKLOG_BOARD), ("滚动条", BKLOG_SCROLLBAR)]:
                if not (0 <= y0 - box[1] and y1 - box[1] <= im.height):
                    raise SystemExit("!! bklog 裁后 %s 纵向出界" % nm)
        b_ll, b_q2, b_q4 = encode(im, 0), encode(im, 2), encode(im, 4)
        tot["lossless"] += len(b_ll)
        tot["q2"] += len(b_q2)
        tot["q4"] += len(b_q4)
        data = {0: b_ll, 2: b_q2, 4: b_q4}[STEP]
        tot["out"] += len(data)
        p = os.path.join(OUT, dest)
        if not args.dry_run:
            with open(p, "wb") as fh:
                fh.write(data)
        rows.append((dest, im.size, len(b_ll), len(b_q2), len(b_q4), note))

    print("=" * 118)
    print("PSV 素材入库（模式 %s%s）" % (args.mode, "，dry-run" if args.dry_run else ""))
    print("=" * 118)
    print("%-30s %-11s %10s %10s %10s  %s" % ("目标文件", "尺寸", "无损(B)", "step2(B)", "step4(B)", "用途"))
    for dest, size, b_ll, b_q2, b_q4, note in rows:
        print("%-30s %-11s %10d %10d %10d  %s" % (dest, "%dx%d" % size, b_ll, b_q2, b_q4, note))
    print("-" * 118)
    print("件数 %d ｜ 源件合计 %.3f MB ｜ 无损 %.3f MB ｜ step2 %.3f MB ｜ step4 %.3f MB ｜ 本次落盘 %.3f MB"
          % (len(rows), tot["src"] / 1048576.0, tot["lossless"] / 1048576.0,
             tot["q2"] / 1048576.0, tot["q4"] / 1048576.0, tot["out"] / 1048576.0))
    # 无损 → 量化 的误差自证（最大每通道误差）
    probe = to_rgba(load_src("AI中文化/2x/otv_save_bg_cn.png"), BOX_SCREEN_1088)
    ref = Image.open(io.BytesIO(encode(probe, 0))).getchannel("R").tobytes()
    for st in (2, 4):
        q = Image.open(io.BytesIO(encode(probe, st))).getchannel("R").tobytes()
        print("量化自证（save_bg R 通道）：无损 vs step%d 最大逐像素差 = %d/255"
              % (st, max(abs(a - b) for a, b in zip(ref, q))))
    check_source_untouched(src_before)
    print("参考区只读自证：%d 件源件 md5 运行前后一致 ✓" % len(SRC_FILES))
    fb = [f for f in os.listdir(OUT) if f.lower().endswith(".png")]
    t = sum(os.path.getsize(os.path.join(OUT, f)) for f in fb)
    print("落盘后 assets/ui：%d 件 / %.2f MB（预算 96 MB）" % (len(fb), t / 1048576.0))
    if not args.dry_run:
        modes = set()
        for dest, *_ in rows:
            with Image.open(os.path.join(OUT, dest)) as im2:
                modes.add(im2.mode)
        print("落盘件模式：%s（非 P 模式 ✓）" % ",".join(sorted(modes)))


if __name__ == "__main__":
    main()
