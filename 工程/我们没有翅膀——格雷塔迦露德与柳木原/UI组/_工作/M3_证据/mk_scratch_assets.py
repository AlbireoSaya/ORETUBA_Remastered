#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
mk_scratch_assets.py — M3 自检夹具生成器（**非交付物，仅存于 _工作/M3_证据/**）

目的：M1 的 krkr\assets\ui\ 资产集与本模块并行产出、尚未就位。为了让 M3 能
      **实际截图自证渲染器工作正常**（而不是只交一堆缺件占位），本脚本在
      _工作/M3_证据/ui_scratch/ 下生成一份**一次性**夹具：

        · 从 资源组\美术统一\系统UI\（只读）复制本页用到的原版贴图
        · 按 M1 的既定做法拼合 panel_frame.png（27×11 九宫格：if_lt/rt/lb/rb
          + if_tbar/bbar + if_lbar/rbar），用于验证 border-image 九宫格渲染

★ 该目录**不是交付物**，跑完截图后即删除；正式交付的 index.html 恒引用
  ../krkr/assets/ui/（M1 的唯一资产集，不复制第二份）。

用法：python mk_scratch_assets.py
"""
import io
import os
import shutil

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.abspath(os.path.join(HERE, '..', '..'))
REPO = os.path.abspath(os.path.join(UI_DIR, '..'))
SRC = os.path.join(REPO, '资源组', '美术统一', '系统UI')
# 本 worktree（临时\wt-ui）不携带 资源组\美术统一\系统UI（大体积素材不入库），
# 故本地缺件时回退到主工作树的**只读**路径取图。
SRC_FALLBACK = os.path.join(
    'E:\\ZCode Workspace\\Galgame\\工程\\我们没有翅膀——格雷塔迦露德与柳木原',
    '资源组', '美术统一', '系统UI')
DST = os.path.join(HERE, 'ui_scratch')

COPY = ['tl1_bg1.png', 'tl1_bg2.png', 'meswin.png', 'nm_frm_b.png',
        'ms_cursr.png', 'ui_bg01.png', 'gc_asu01.png']

PIECES = {
    'TL': 'if_lt.png', 'TR': 'if_rt.png', 'BL': 'if_lb.png', 'BR': 'if_rb.png',
    'T': 'if_tbar.png', 'B': 'if_bbar.png', 'L': 'if_lbar.png', 'R': 'if_rbar.png',
}


def build_panel_frame():
    """按 M1 既定做法拼合 27×11 九宫格边框件。"""
    imgs = {}
    for k, fn in PIECES.items():
        p = os.path.join(SRC, fn)
        imgs[k] = Image.open(p).convert('RGBA')
        print('  piece %-2s %-12s %s' % (k, fn, imgs[k].size))

    cw = imgs['TL'].size[0]        # 13
    ch = imgs['TL'].size[1]        # 5
    ew = imgs['T'].size[0]         # 1
    eh = imgs['L'].size[1]         # 1
    W, H = cw * 2 + ew, ch * 2 + eh
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(imgs['TL'], (0, 0))
    out.paste(imgs['T'], (cw, 0))
    out.paste(imgs['TR'], (cw + ew, 0))
    out.paste(imgs['L'], (0, ch))
    # 中央 (cw, ch) 留透明：面板填充由 layout 的 rect 元素负责
    out.paste(imgs['R'], (cw + ew, ch))
    out.paste(imgs['BL'], (0, ch + eh))
    out.paste(imgs['B'], (cw, ch + eh))
    out.paste(imgs['BR'], (cw + ew, ch + eh))
    p = os.path.join(DST, 'panel_frame.png')
    out.save(p)
    print('  panel_frame.png %s  ->  %s' % (out.size, p))
    return out.size


def main():
    global SRC
    if not os.path.isdir(SRC) and os.path.isdir(SRC_FALLBACK):
        print('  local 资源组\\美术统一\\系统UI absent -> fallback to main worktree (read-only):')
        print('   ', SRC_FALLBACK)
        SRC = SRC_FALLBACK
    if not os.path.isdir(SRC):
        raise SystemExit('source dir not found: %s' % SRC)
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    for fn in COPY:
        s = os.path.join(SRC, fn)
        if not os.path.isfile(s):
            print('  SKIP (missing) %s' % fn)
            continue
        shutil.copy2(s, os.path.join(DST, fn))
        print('  copy %s' % fn)
    build_panel_frame()
    print('scratch fixture ->', DST)


if __name__ == '__main__':
    main()