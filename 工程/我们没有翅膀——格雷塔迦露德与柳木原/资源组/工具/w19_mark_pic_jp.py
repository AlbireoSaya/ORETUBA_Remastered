# -*- coding: utf-8 -*-
"""
W19 · 「图片化日文」列补标（幂等）

口径（本脚本唯一依据，见 03_资源总账_全量现状.md §5.3 更新块 / 美术规范.md §六）：
  `图片化日文` = 是  ⟺  该件像素中烘焙有「界面/内容文字」（日文为主，含作为 UI 文案的
  拉丁文与数字），汉化时改文本文件无效，须重绘或改引擎绘字。

  两个子族（处置不同）：
    A 功能性文字 —— 系统UI 菜单/按钮/标签/曲名/页号/日期 等，须重绘或改引擎绘字
    B 片尾 STAFF —— `sr0–sr4_*` / `sr2_t*` / `sl_*` / `end_staff`（真人名，可保留原文）

  不计入：纯符号（× / ▼ / ▲ / ✓）、装饰渐变条、纯遮罩/粒子、九宫格边框、
          纯缩略图（无字）、背景内的「世界观招牌」（如 ALBAN / Alexander，
          属 §5.4 背景装饰子族，另用 `分片角色` 列登记）、
          **纯品牌标识**（`brandlogo_5pb.png` / `criware1280x720sw.png` /
          `sr_logo.png`，汉化保留原样、不需重绘）。

本脚本只改 4 张 TSV 的 `图片化日文` 列，其余列逐行原样保留（按行做单元格替换，
不重写整表，保证其它单元格字节不变）。

用法：
  python w19_mark_pic_jp.py --check     # 只读校验：列出将变更的行与统计，不改文件
  python w19_mark_pic_jp.py --apply     # 幂等写入
"""
import os
import re
import sys
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 资源组\
ART = os.path.join(ROOT, "美术统一")
SUP = os.path.join(ROOT, "美术统一_超分")

FILES = [
    (os.path.join(ART, "交付清单.tsv"), "统一名", "图片化日文", "类别"),
    (os.path.join(ART, "清单_CG背景.tsv"), "统一名", "图片化日文", "类别"),
    (os.path.join(ART, "清单_系统UI.tsv"), "统一名", "图片化日文", "类别"),
    (os.path.join(SUP, "超分清单.tsv"), "统一名", "图片化日文", "类别"),
]

YES = "是"

# ---------------------------------------------------------------- 系统UI 是集

UI_NOT_TL = {"tl_bg.png", "tl_bg2.png", "tl_chk.png", "tl_down.png", "tl_info.png", "tl_up.png"}
UI_IF_YES = {"if_ok.png", "if_ok2.png", "if_yes.png", "if_no.png", "if_cancl.png"}
UI_CF_NOT = {"cf_bar.png", "cf_frame.png", "cf_frm_a.png", "cf_speed.png", "cf_vbar.png"}
UI_SV_NOT = {"sv_bg.png", "sv_mchk.png", "sv_over.png"}
UI_LD_NOT = {"ld_bg.png", "ld_mchk.png", "ld_over.png"}
UI_GL_NOT = {"gl_bg.png", "gl_frame.png", "gl_name.png", "gl_slash.png", "gl_pgcr.png", "gl_num2.png"}
UI_SS_YES = {"ss_load.png", "ss_log.png", "ss_name1.png", "ss_name2.png", "ss_name3.png",
             "ss_name4.png", "ss_name5.png", "ss_no.png", "ss_qload.png", "ss_qsave.png",
             "ss_s_ret.png", "ss_save.png", "ss_stext.png", "ss_sys.png", "ss_yes.png"}
UI_EX_NOT = {"ex_bg.png", "ex_frame.png"}
UI_GA_NOT = {"ga_frame.png", "ga_slash.png", "ga_up.png"}

EC_DATE = re.compile(r"^ec_\d{4}\.png$")
EC_NAME = re.compile(r"^ec\d+_name\d*\.png$")
EC_CHAP = re.compile(r"^ec\d+_chap\.png$")
EC_WING = re.compile(r"^ec\d+_wing\d*\.png$")
EC_LOGO = re.compile(r"^ec\d+_logo\.png$")
EC_EP = re.compile(r"^ec\d+_ep\.png$")
EC_DAY = re.compile(r"^ec\d+_day\.png$")
EC_BG_CARD = re.compile(r"^ec\d+_bg\.png$")      # 1013x658 章节卡（底部有 STAFF 小字）
EC_EXTRA = {"ec_epi.png", "ec_pro.png", "ec5_1_bg.png", "ec5_2_bg.png"}


def is_ui_pic_jp(n: str) -> bool:
    if re.match(r"^op_[0-9a-f]+\.png$", n):
        return True
    if n.startswith("sm_"):
        return True
    if n.startswith("tl_"):
        return n not in UI_NOT_TL
    if n.startswith("if_"):
        return n in UI_IF_YES
    if n.startswith("th_"):
        return False
    if n.startswith("cf_"):
        return n not in UI_CF_NOT
    if n.startswith("sv_"):
        return n not in UI_SV_NOT and not re.match(r"^sv_f\d\.png$", n)
    if n.startswith("ld_"):
        return n not in UI_LD_NOT and not re.match(r"^ld_f\d\.png$", n)
    if n.startswith("gl_"):
        return n not in UI_GL_NOT
    if n.startswith("mc_"):
        return n != "mc_bg.png"
    if n.startswith("ss_"):
        if re.match(r"^ss_1[12]\d\d\.png$", n):
            return True
        if re.match(r"^ss_bg\d_full\.png$", n):
            return True
        return n in UI_SS_YES
    if n.startswith("sc_"):
        return True
    if n.startswith("ex_"):
        return n not in UI_EX_NOT
    if re.match(r"^dm\d\d\.png$", n):
        return True
    if re.match(r"^gm_bg[1-6]\.png$", n):
        return True
    if n.startswith("ga_"):
        return n not in UI_GA_NOT
    if n.startswith("ec"):
        return bool(EC_DATE.match(n) or EC_NAME.match(n) or EC_CHAP.match(n)
                    or EC_WING.match(n) or EC_LOGO.match(n) or EC_EP.match(n)
                    or EC_DAY.match(n) or EC_BG_CARD.match(n)) or n in EC_EXTRA
    if n.startswith("ui_"):
        return False                      # ui_ec_bg* 等经目视复核为无 UI 文字
    if n.startswith("gc_") or n.startswith("ev_") or n.startswith("cg_"):
        return False
    if n.startswith("sr"):
        return n == "sr.png"            # sr_logo.png = 品牌标识，不重绘
    if n.startswith("rule") or n.startswith("paper") or n.startswith("snow") \
            or n.startswith("gr_") or n.startswith("sel") or n.startswith("ms_") \
            or n.startswith("nm_") or n.startswith("noise") or n.startswith("rain") \
            or n.startswith("hana") or n.startswith("lightball") or n.startswith("shine") \
            or n.startswith("white") or n.startswith("yellow") or n.startswith("red") \
            or n.startswith("black") or n.startswith("brown") or n.startswith("bklog") \
            or n.startswith("meswin") or n.startswith("tl1_fr"):
        return False
    if n.startswith("_"):
        return False
    if n.startswith("dlg"):
        return n not in {"dlg_bg_26.png", "dlg_bg_27.png", "dlg_bg_28.png"}  # 三件纯空白对话窗
    if n.startswith("buru") or n.startswith("cm_") or n.startswith("cfg") \
            or n.startswith("bg_config"):
        return True
    if n in {"no_data.png", "no_img.png", "skp1_icon.png", "sl_data.png", "sys_menu.png",
             "title_bg.png", "tl1_bg2.png", "tl1_logo.png", "tl2_logo.png", "load_bg.png",
             "loading.png", "save_bg.png", "saving.png", "quick_load_bg.png", "quick-save.png",
             "op.png", "notice2.png", "mu_bg.png", "mv_bg.png", "config.png"}:
        return True
    if n in {"brandlogo_5pb.png", "criware1280x720sw.png"}:
        return False                      # 纯品牌标识，汉化保留原样
    if re.match(r"^\d\d_.*\.png$", n):
        return True                       # 00_qsave / 03_save / 08_sys 等菜单条
    return False


# ---------------------------------------------------------------- CG背景 是集

def is_cg_pic_jp(n: str) -> bool:
    if re.match(r"^sr[0-4]_\d+\.png$", n):
        return True                       # sr0–sr4 片尾 STAFF 页
    if re.match(r"^sr2_t\d+\.png$", n):
        return True                       # 歌词条（原已标）
    if re.match(r"^sl_\d+\.png$", n):
        return True
    if n == "end_staff.png":
        return True
    return False


def is_pic_jp(kind: str, n: str) -> bool:
    if kind == "系统UI":
        return is_ui_pic_jp(n)
    if kind == "CG背景":
        return is_cg_pic_jp(n)
    return False


# ---------------------------------------------------------------- 表格读写

def read_tsv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        raw = f.read()
    return raw


def split_lines(raw):
    # 保留行尾符：按 \n 切，记录是否 \r\n
    parts = raw.split("\n")
    return parts


def col_index(header_cells, name):
    for i, c in enumerate(header_cells):
        if c == name:
            return i
    raise KeyError(name)


def process(path, name_col, flag_col, kind_col, apply_changes):
    raw = read_tsv(path)
    parts = raw.split("\n")
    header = parts[0].split("\t")
    ci_name = col_index(header, name_col)
    ci_flag = col_index(header, flag_col)
    ci_kind = col_index(header, kind_col)

    changed = []
    n_yes = 0
    per_kind = {}
    out = [parts[0]]
    for line in parts[1:]:
        if line == "":
            out.append(line)
            continue
        cells = line.split("\t")
        kind = cells[ci_kind]
        nm = cells[ci_name]
        want = is_pic_jp(kind, nm)
        cur = cells[ci_flag]
        if want:
            n_yes += 1
            per_kind[kind] = per_kind.get(kind, 0) + 1
            if cur != YES:
                changed.append((nm, kind, cur))
                if apply_changes:
                    cells[ci_flag] = YES
        out.append("\t".join(cells))
    if apply_changes and changed:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(out))
    return changed, n_yes, per_kind


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    total_changed = 0
    for path, name_col, flag_col, kind_col in FILES:
        rel = os.path.relpath(path, os.path.dirname(ROOT))
        changed, n_yes, per_kind = process(path, name_col, flag_col, kind_col, a.apply)
        total_changed += len(changed)
        print("=" * 72)
        print("%s  →  图片化日文==是 : %d 件" % (rel, n_yes))
        for k in sorted(per_kind):
            print("      %-8s %d" % (k, per_kind[k]))
        if changed:
            print("   本次变更 %d 行（空 → 是）:" % len(changed))
            for nm, kind, cur in changed[:400]:
                print("      + %-28s [%s] %r" % (nm, kind, cur))
            if len(changed) > 400:
                print("      ... 另 %d 行" % (len(changed) - 400))
        else:
            print("   本次变更 0 行（已是最新口径）")
    print("=" * 72)
    print("合计变更 %d 行 ｜ 模式=%s" % (total_changed, "apply" if a.apply else "check"))
    return 0


if __name__ == "__main__":
    sys.exit(main())