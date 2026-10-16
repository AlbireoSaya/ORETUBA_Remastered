# -*- coding: utf-8 -*-
r"""t1 · 落地：把 B 路页脚中文贴到 7 张整屏底图（krkr\assets\ui\x_ui_psv_*.png）

几何来源（**不得照抄坐标，须由源头推导**）——`工具\m53_psv_ui_assets.py` 的裁切口径：
  · `x_ui_psv_{save_bg,load_bg,quick_load_bg}.png` ← `AI中文化/2x/otv_*_cn.png`，`BOX_SCREEN_1088=(0,4,1920,1084)`
      ⇒ 画布 y0 = 源 y4 ⇒ **源 y940 → 画布 y936**
  · `x_ui_psv_backlog_bg.png` ← `超分2x/otv_bklog.png`，`BOX_BKLOG=(0,4,1920,1084)` 同款 ⇒ **源 y940 → 画布 y936**
  · `x_ui_psv_{gal_shell,music_bg,replay_bg}.png` ← `超分2x/otv_{gm_bg1,mu_bg,mv_bg}.png`，`BOX_TOP_1080=(0,0,1920,1080)`
      ⇒ 画布 y0 = 源 y0 ⇒ **源 y940 → 画布 y940**
  ⇒ 粘贴基线 y = 940 − 源裁切偏移；行数 = 1080 − y（**不是统一的 936/144**，见报告「几何推导」）。
  ★ 每个文件的实际偏移由**实测复核**（脚本内 `detect_off()`：用页脚**上方**共享区 y880..930 与源件做
    两假设比对，取残差小者），表值只作交叉验证；两者不一致即报错退出。

B 路裁片 = 源件 (880,940)-(1904,1088) 的 1024×148 RGB（`_复核_20260926\页脚双路\*_B_生图.png`）。
粘贴：**只贴 RGB 三通道**，目标件 alpha 原样保留（实测页脚带 alpha 全 255）；
      贴入前对裁片做 `& 0xFC`（= 现有资产的既有口径，见下），再 `optimize=True, compress_level=9` 存盘。
      · 现有 7 件 RGB **本就是 step-4 量化**（脚本自证 max(v%4)=0）⇒ 对裁片做 &0xFC 后，
        「页脚带」与「带外」量化口径**完全一致**，不存在派单担心的跨边界 ≤3/255 台阶。

用法：python t1_paste_footer.py --dry     # 只算不改（打印几何/偏移实测/体积）
      python t1_paste_footer.py            # 落盘（先自动备份原件到 原形备份\）
"""
import sys, os, json, shutil, io
sys.path.append(r"E:\ZCode Workspace\Galgame\工具\pylibs")
import numpy as np
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
UI = os.path.join(BASE, "krkr", "assets", "ui")
SRC = os.path.join(BASE, "PSV系统UI参考", "超分2x")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-06_页脚双路")
BAK = os.path.join(WORK, "原形备份"); os.makedirs(BAK, exist_ok=True)
PICK = os.path.join(WORK, "footer_B_pick.json")
FX0, FY0 = 880, 940          # B 裁片在**源件**上的原点
FW, FH = 1024, 148

# (目标件, 源件, m53 裁切偏移)  —— 偏移 = 源 y0 在画布上的对应（BOX_SCREEN_1088/BOX_BKLOG=4，BOX_TOP_1080=0）
SPEC = [
    ("x_ui_psv_save_bg.png",       "otv_save_bg.png",       4),
    ("x_ui_psv_load_bg.png",       "otv_load_bg.png",       4),
    ("x_ui_psv_quick_load_bg.png", "otv_quick_load_bg.png", 4),
    ("x_ui_psv_backlog_bg.png",    "otv_bklog.png",         4),
    ("x_ui_psv_gal_shell.png",     "otv_gm_bg1.png",        0),
    ("x_ui_psv_music_bg.png",      "otv_mu_bg.png",         0),
    ("x_ui_psv_replay_bg.png",     "otv_mv_bg.png",         0),
]


def src_flat(name):
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    return np.asarray(Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
                      .convert("RGB")).astype(np.int16)


def detect_off(target_rgb, src_rgb):
    """用页脚**上方**共享区（画布 y0..930，页脚带 936/940 起，故该区不受粘贴影响）在两假设下取残差小者。
    取整段 0..930 而非近带 880..930：近带是纯霜面（无结构），两假设残差几乎并列（实测 save_bg 3.41 vs 3.55）；
    整段含题字 SAVE/LOAD、徽章 /10、边饰等高结构像素，七件全部一次分清（余量 ≥5%，见报告）。"""
    tgt = target_rgb[0:930, :, :]
    d0 = float(np.abs(tgt - src_rgb[0:930, :, :]).mean())
    d4 = float(np.abs(tgt - src_rgb[4:934, :, :]).mean())
    return (0, d0, d4) if d0 < d4 else (4, d4, d0)


def enc(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def main():
    dry = "--dry" in sys.argv
    pick = json.load(open(PICK, encoding="utf-8"))
    tot_before = tot_after = 0
    print("=" * 104)
    print("B 路页脚落地%s" % ("（dry-run，不写盘）" if dry else ""))
    print("=" * 104)
    print("%-30s %-24s %-5s %-9s %-5s %10s %10s %9s" %
          ("目标件", "B 裁片来源", "偏移", "粘贴y", "行数", "贴前(B)", "贴后(B)", "Δ(B)"))
    for tgt, src, off_tab in SPEC:
        tp = os.path.join(UI, tgt)
        im = Image.open(tp)
        rgb = np.asarray(im.convert("RGB")).astype(np.int16)
        alpha = np.asarray(im.convert("RGBA"))[:, :, 3].copy() if im.mode == "RGBA" else None
        s = src_flat(src)
        off, d_ok, d_bad = detect_off(rgb, s)
        assert off == off_tab, "!! %s 实测偏移 %d ≠ m53 口径 %d（残差 %.2f vs %.2f）" % (tgt, off, off_tab, d_ok, d_bad)
        py = FY0 - off
        rows = 1080 - py
        b = Image.open(pick[src]["path"]).convert("RGB")
        assert b.size == (FW, FH), "B 裁片尺寸异常 %s" % (b.size,)
        crop = np.asarray(b.crop((0, 0, FW, rows))).astype(np.int16) & 0xFC
        out = rgb.copy()
        out[py:py + rows, FX0:FX0 + FW, :] = crop
        before = os.path.getsize(tp)
        if alpha is None:
            res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
        else:
            res = Image.merge("RGBA", tuple(Image.fromarray(np.clip(out[:, :, c], 0, 255).astype(np.uint8))
                                            for c in range(3)) + (Image.fromarray(alpha),))
        data = enc(res)
        after = len(data)
        tot_before += before; tot_after += after
        if not dry:
            if not os.path.exists(os.path.join(BAK, tgt)):
                shutil.copyfile(tp, os.path.join(BAK, tgt))
            with open(tp, "wb") as fh:
                fh.write(data)
        print("%-30s %-24s %-5d %-9d %-5d %10d %10d %+9d%s" %
              (tgt, os.path.basename(pick[src]["path"]), off, py, rows, before, after, after - before,
               "" if not dry else "  (dry)"))
    print("-" * 104)
    print("合计 贴前 %.4f MB → 贴后 %.4f MB（Δ %+.4f MB）" % (tot_before / 1048576, tot_after / 1048576,
                                                          (tot_after - tot_before) / 1048576))
    fb = [f for f in os.listdir(UI) if f.lower().endswith(".png")]
    t = sum(os.path.getsize(os.path.join(UI, f)) for f in fb)
    print("assets/ui 现况：%d 件 / %.3f MB（预算 96 MB）" % (len(fb), t / 1048576.0))


if __name__ == "__main__":
    main()
