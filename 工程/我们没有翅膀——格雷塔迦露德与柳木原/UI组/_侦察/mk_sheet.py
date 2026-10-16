# -*- coding: utf-8 -*-
"""生成 UI 素材接触印相表（供主代理目视判读）。只读源素材。"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

SRC = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\美术统一\系统UI"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))

BG = (40, 40, 48)
PAD = 6
LABEL_H = 16

def sheet(names, cols, cell_w, cell_h, outname, title):
    rows = (len(names) + cols - 1) // cols
    W = cols * (cell_w + PAD) + PAD
    H = rows * (cell_h + PAD + LABEL_H) + PAD + 24
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 11)
        ft = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
    except Exception:
        f = ImageFont.load_default(); ft = f
    d.text((PAD, 4), title, fill=(255, 220, 120), font=ft)
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        x = PAD + c * (cell_w + PAD)
        y = 24 + PAD + r * (cell_h + PAD + LABEL_H)
        p = os.path.join(SRC, n)
        if not os.path.exists(p):
            d.text((x, y), "MISSING " + n, fill=(255, 80, 80), font=f); continue
        src = Image.open(p)
        # 透明底画成棋盘格，便于看 alpha
        box = Image.new("RGB", src.size, (0, 0, 0))
        chk = Image.new("RGB", src.size, (110, 110, 118))
        dd = ImageDraw.Draw(chk)
        for yy in range(0, src.size[1], 8):
            for xx in range(0, src.size[0], 8):
                if ((xx // 8) + (yy // 8)) % 2:
                    dd.rectangle([xx, yy, xx + 7, yy + 7], fill=(150, 150, 158))
        if src.mode in ("RGBA", "LA"):
            box.paste(src.convert("RGB"), (0, 0), src.convert("RGBA").split()[-1])
            chk.paste(box, (0, 0), src.convert("RGBA").split()[-1])
            tile = chk
        else:
            tile = src.convert("RGB")
        # 1:1 优先，放不下才缩
        if tile.size[0] > cell_w or tile.size[1] > cell_h:
            k = min(cell_w / tile.size[0], cell_h / tile.size[1])
            tile = tile.resize((max(1, int(tile.size[0] * k)), max(1, int(tile.size[1] * k))), Image.LANCZOS)
        im.paste(tile, (x, y))
        d.rectangle([x - 1, y - 1, x + tile.size[0], y + tile.size[1]], outline=(90, 90, 100))
        d.text((x, y + cell_h + 2), "%s %dx%d" % (n, src.size[0], src.size[1]), fill=(200, 200, 210), font=f)
    im.save(os.path.join(OUT, outname))
    print("saved", outname, im.size)

sheet(["ms_frm_a.png","ms_frm_b.png","ms_frm_g.png","nm_frm_a.png","nm_frm_b.png","ms_cursr.png",
       "if_lt.png","if_rt.png","if_lb.png","if_rb.png","if_tbar.png","if_lbar.png","if_ok.png","if_yes.png","if_no.png","if_cancl.png",
       "cf_frame.png","cf_frm_a.png","cf_bar.png","cf_vbar.png","cf_ret.png",
       "sel00a.png","sel00b.png","sel00g.png","sel01b.png","sel02b.png"],
      5, 240, 130, "sheet1_dialog_frame.png", "1/4 对话框/名字框/边框/九宫格件")

sheet(["op_01.png","op_02.png","op_03.png","op_11.png","op_12.png","op_13.png","op_14.png","op_15.png","op_16.png",
       "op_21.png","op_22.png","op_23.png","op_24.png","op_25.png","op_57.png",
       "sm_save.png","sm_load.png","sm_cfg.png","sm_skip.png","sm_auto.png",
       "sm_win.png","sm_log.png","sm_ret.png","sm_title.png","sm_end.png"],
      5, 300, 60, "sheet2_buttons.png", "2/4 选项按钮 op_* / 菜单条 sm_*（查是否有日文烘焙）")

sheet(["sm_base.png","sm_base2.png","th_asu.png","th_ai.png","th_close.png","th_bar.png",
       "sv_data.png","ld_data.png","sv_chk.png","sv_pg01.png","sv_f1.png","sv_memo.png",
       "sv_bg.png","ld_over.png","cf_disp1.png","cf_bgm.png","cf_dfrm.png","cf_aon.png","cf_aoff.png",
       "tl_01.png","tl1_logo.png","tl2_logo.png","tl1_bg1.png","tl1_bg.png","tl2_bg1.png"],
      5, 300, 130, "sheet3_saveload_title.png", "3/4 存读档 / 配置件 / 标题（查日文烘焙）")

sheet(["dlg_bg_26.png","dlg_bg_01.png","dlg_bg_20.png","meswin.png","selwin.png","sys_menu.png",
       "ss_bg1_full.png","ss_bg1_base.png","bg_config_01.png","title_bg.png","gm_bg1.png","mu_bg.png","mv_bg.png","sl_data.png",
       "ec1_bg.png","ec1_name.png","ec_1121.png","ec_bg01.png","ui_bg01.png","gc_asu01.png","sc_50_1.png","ex_10.png","sr_01.png","ev_asu.png",
       "gl_chr1.png","gl_bgm01.png","mc_bgm01.png","ga_frame.png","rule000.png","paper_0.png","snow_0.png","skp1_icon.png"],
      5, 260, 140, "sheet4_psv_screens.png", "4/4 PSV 系统画面 / 章节卡 / 画廊音乐 / 遮罩粒子")
