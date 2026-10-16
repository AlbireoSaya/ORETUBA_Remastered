# -*- coding: utf-8 -*-
r"""psv_fix_save_badge.py —— 23/24 右上页码徽章：**删除上一轮的「抹字补丁」**（恢复 PSV 原图，烘焙「/10」保留）

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮）· **未愈缺陷修复轮**（派单缺陷 ②）。
对象：`krkr\assets\ui\x_ui_psv_save_bg.png`（23 存档）/ `x_ui_psv_load_bg.png`（24 读档）。

■ 上一轮做了什么、为什么算缺陷
  上一轮（A 基础组修复轮）用「上下锚行线性补底」程序化抹掉底图右上徽章里烘焙的「/10」
  （补底矩形 x1763..1845 / y80..140），改由屏内引擎文本绘「N / 10」。vision 复审判不达标：
  补区纹理被抹平（stdev 16.2 vs 区外 20.3）、跨边一枚雪晶被截断、有竖条痕、硬竖边 x≈1846。

■ 本轮结论：**补丁删除，恢复原图**（派单备选路径；直接依据如下）
  1. **同族像素拷贝（派单首选）实测不可用** —— 候选件在徽章带内与本屏不对齐：
     | 候选件                | 徽章带 y55..160 x1650..1919（排除字形） | 徽章带外 y160..260 | y500..700 x600..1200 |
     | `x_ui_psv_gal_shell`  | mean **2.93** p95 16.0 n>4=3678/20340 (18%) | mean 0.11 | mean 0.00 |
     | `x_ui_psv_dress_bg`   | mean 8.75                                 | mean 6.19 | mean 6.12 |
     | `x_ui_psv_music_bg`   | mean 12.05                                | mean 6.42 | mean 14.48 |
     | `x_ui_psv_backlog_bg` | mean 2.82（上方邻带）/ 14.61（补带）      | —         | mean 8.39 |
     （dy=+4 最优；gal_shell 因 BOX_TOP_1080 未裁 4px ⇒ 差一行，见 m53 SPEC）
     ⇒ gal_shell 在**徽章带之外**几乎逐像素相同（|Δ| 0.11 / 0.00），差异**只集中在徽章内**：
        ALBUM 屏徽章自带另一套装饰（自己的「／」在 x1740..1765、大雪花居中 ≈x1800），
        与本屏徽章（「／」x1763..1792、页数 x1796..1848）**不是同坐标同物**。
     ⇒ 按派单口径「对齐（|Δ|≤2）才整带拷贝」，本带 **不满足**（2.93 > 2）⇒ 首选路径作废；
        强行拷贝会把 ALBUM 屏的「／」搬到本屏徽章（并叠上引擎文本的第二个「／」）。
  2. **二维结构感知填充要凭空补出被字形遮住的雪花臂尖端**（y118..131）——正是上一轮失败的成因；
     而徽章里的「／」在 ALBUM 屏徽章里同样存在（同一枚装饰的另一种摆位）⇒ 不能靠「同族件无此物」抹掉。
  3. **PSV 原图本身就预留了前导页数字的干净槽位**：徽章内 x1690..1757 / y84..132 为干净霜面、
     无任何烘焙数字（对照 `PSV系统UI参考\超分2x\otv_save_bg.png` 同区，实测两者逐像素相同）
     ⇒ 原设计即「**烘焙 /10 ＋ 引擎绘前导页数字**」。
  ⇒ 采派单**备选**：「保留烘焙「/10」，只在它左侧用引擎补前导页数字（此时删除补丁、字号/基线与烘焙形对齐）」。
     屏内数据侧：`sv.pgnum_01..10` 样文由 `N / 10` 改为 `N`、几何贴到「／」左槽（见
     `_工作\ISSUE-20260926-06_未愈缺陷修复\复现脚本\psv_fix_saveload_badge.py`）。

■ 恢复口径（可复算、幂等）
  原图 = `Q8( 参考区 AI中文化\2x\otv_{save,load}_bg_cn.png 上下各去 4px )`，其中
      Q8(v) = min(248, 8*((v+1)//8))          （= m53 入库时对该件所用的 5bit/step8 量化）
  **实测自证**：该重建式与**盘上现件**在「旧补丁矩形之外」逐像素相同
  （save/load 均 0 处不同）⇒ 证明「重建 = 改前原图」，本脚本的改动**仅限于删掉旧补丁**。

■ 体积 / 编码
  只重编码该 PNG（`optimize=True, compress_level=9`）。入参已在 Q8（step8）栅格上，
  而 step8 值**都是 4 的倍数** ⇒ 再套 `& 0xFC` 是**恒等变换**（脚本内断言零变化）；alpha 全图 255，逐像素原样。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python 工具\psv_fix_save_badge.py                # 删补丁、恢复原图（幂等）
    python 工具\psv_fix_save_badge.py --dry-run      # 只算、不写盘
    python 工具\psv_fix_save_badge.py --variant donor  # 备查：同族像素拷贝变体（本轮**不采用**，实测 |Δ| 2.93>2）
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                       # noqa: E402
from PIL import Image                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))          # <UI组>\工具
UI = os.path.dirname(HERE)                                 # <UI组>
OUT = os.path.join(UI, "krkr", "assets", "ui")
REF = os.path.join(UI, "PSV系统UI参考", "AI中文化", "2x")
EVID = os.path.join(UI, "_工作", "ISSUE-20260926-06_未愈缺陷修复", "取证")

CROP_Y = 4                              # 1088 → 1080（与 m53 的 BOX_SCREEN_1088 同口径）
# 参考区只读锚：本重建式的唯一输入，必须逐字节不变（变了就报错，不做静默降级）
SRC_MD5 = {
    "x_ui_psv_save_bg.png": "otv_save_bg_cn.png",
    "x_ui_psv_load_bg.png": "otv_load_bg_cn.png",
}
# 旧补丁矩形（屏坐标，右下开区间）——上一轮 `ERASE`，也是本轮「掩码外逐像素相同」的掩码
OLD_PATCH = (1763, 80, 1846, 141)
# 徽章带（自证对齐度用；排除字形）
BADGE_BAND = (slice(55, 161), slice(1650, 1920))
GLYPH_BOX = (slice(76, 146), slice(1745, 1866))            # 字形（含抗锯齿）排除区
NEIGH_BANDS = [("above y60..79", (slice(60, 80), slice(1700, 1920))),
               ("below y141..165", (slice(141, 166), slice(1700, 1920))),
               ("around y160..260", (slice(160, 261), slice(1650, 1920))),
               ("mid y500..700", (slice(500, 701), slice(600, 1200)))]
DONOR = "x_ui_psv_gal_shell.png"
DONOR_DY = 4                            # gal_shell = Q8(otv_gm_bg1[0:1080])；本屏源上下各去 4px ⇒ 差 4 行


def Q8(a):
    """m53 对该件所用的 5bit/step8 量化（实测复现：与盘上件在补丁矩形外逐像素相同）。"""
    return np.minimum(248, 8 * ((np.asarray(a).astype(np.int32) + 1) // 8)).astype(np.uint8)


def md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_pristine(asset_name):
    src_name = SRC_MD5[asset_name]
    p = os.path.join(REF, src_name)
    assert os.path.isfile(p), "参考区源件缺失（不得静默按现图猜）：%s" % p
    im = Image.open(p).convert("RGB")
    assert im.size == (1920, 1088), "%s 尺寸 %s != (1920,1088)" % (src_name, im.size)
    return Q8(np.asarray(im.crop((0, CROP_Y, 1920, CROP_Y + 1080))))


def donor_plate():
    """同族候选件（gal_shell），按 DY 下移对齐本屏（gal_shell[y+4] == 本屏[y]）。"""
    im = Image.open(os.path.join(OUT, DONOR)).convert("RGB")
    a = np.asarray(im).astype(np.uint8)
    out = np.empty_like(a)
    out[:1080 - DONOR_DY] = a[DONOR_DY:]
    out[1080 - DONOR_DY:] = a[1079]
    return out


def align_probe(cur, asset_name):
    """出对齐实测表（派单步骤①）：候选件在本带/上下邻带的 |Δ| 均值/p95。"""
    lines = ["", "对齐实测 · %s（pristine vs 候选件，RGB 三通道 max|Δ|；徽章带排除字形区 "
             "[x%d..%d y%d..%d]）" % (asset_name, GLYPH_BOX[1].start, GLYPH_BOX[1].stop,
                                      GLYPH_BOX[0].start, GLYPH_BOX[0].stop)]
    rows = [("x_ui_psv_gal_shell.png(dy=+4)", donor_plate())]
    for fn in ("x_ui_psv_dress_bg.png", "x_ui_psv_music_bg.png", "x_ui_psv_backlog_bg.png"):
        rows.append((fn, np.asarray(Image.open(os.path.join(OUT, fn)).convert("RGB")).astype(np.uint8)))
    for nm, cand in rows:
        d = np.abs(cur.astype(np.int32) - cand.astype(np.int32)).max(axis=2)
        badge = d[BADGE_BAND]
        m = np.ones(badge.shape, bool)
        m[GLYPH_BOX[0].start - BADGE_BAND[0].start:GLYPH_BOX[0].stop - BADGE_BAND[0].start,
          GLYPH_BOX[1].start - BADGE_BAND[1].start:GLYPH_BOX[1].stop - BADGE_BAND[1].start] = False
        seg = badge[m]
        line = ("  %-34s 徽章带 mean=%5.2f p95=%5.1f n>4=%5d/%5d" %
                (nm, seg.mean(), np.percentile(seg, 95), int((seg > 4).sum()), seg.size))
        for bn, (sy, sx) in NEIGH_BANDS:
            line += " ｜ %s mean=%.2f" % (bn, d[sy, sx].mean())
        lines.append(line)
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只算、不写盘")
    ap.add_argument("--variant", choices=["restore", "donor"], default="restore",
                    help="restore（默认，本轮采用）= 删除补丁、恢复 PSV 原图；"
                         "donor = 同族像素拷贝变体（实测徽章带 |Δ| 2.93>2 ⇒ 未采用）")
    ap.add_argument("--print-md5", action="store_true", help="打印参考区源件 md5（供回填 SRC_MD5 锚）")
    a = ap.parse_args()

    if a.print_md5:
        for an, sn in sorted(SRC_MD5.items()):
            print("%-24s %-24s %s" % (an, sn, md5(os.path.join(REF, sn))))
        return 0

    print("=" * 118)
    print("23/24 页码徽章：删除「抹字补丁」、恢复 PSV 原图（烘焙「/10」保留；前导页数字改由屏内引擎绘）")
    print("  变体 %s ｜ 旧补丁矩形 %s ｜ 重建式 Q8(参考区 AI中文化\\2x\\otv_*_bg_cn.png 上下各去 4px)"
          % (a.variant, OLD_PATCH))
    print("=" * 118)

    os.makedirs(EVID, exist_ok=True)
    src_before = {sn: md5(os.path.join(REF, sn)) for sn in SRC_MD5.values()}
    probe_lines = []

    for asset_name in sorted(SRC_MD5):
        fp = os.path.join(OUT, asset_name)
        with open(fp, "rb") as f:
            on_disk_bytes = f.read()
        cur = np.asarray(Image.open(io.BytesIO(on_disk_bytes)).convert("RGB")).astype(np.uint8)
        pristine = load_pristine(asset_name)
        probe_lines.append(align_probe(pristine, asset_name))

        x0, y0, x1, y1 = OLD_PATCH
        mask = np.zeros(cur.shape[:2], bool)
        mask[y0:y1, x0:x1] = True

        # ── 前置自证 0：重建式 == 盘上现件（补丁矩形之外），0 处不同 ──
        d_out = np.abs(pristine.astype(np.int32) - cur.astype(np.int32)).max(axis=2)
        n_out = int((d_out[~mask] > 0).sum())
        assert n_out == 0, ("%s：重建式与盘上件在补丁矩形外有 %d 处不同 ⇒ 重建式不成立，停止"
                            "（不得静默降低口径）" % (asset_name, n_out))

        # restore（本轮采用）：整幅恢复原图；donor（备查变体）：仅把补丁矩形换成同族件的同坐标像素
        out = pristine.copy()
        if a.variant == "donor":
            plate = donor_plate()
            out[y0:y1, x0:x1] = plate[y0:y1, x0:x1]

        # ── 编码：optimize + compress_level 9；& 0xFC 在 step8 栅格上是恒等（断言） ──
        assert ((out.astype(np.int32) & 0xFC) == out.astype(np.int32)).all(), \
            "%s：& 0xFC 非恒等（入参不在 step8 栅格）" % asset_name
        buf = io.BytesIO()
        Image.fromarray(out, "RGB").save(buf, "PNG", optimize=True, compress_level=9)
        data = buf.getvalue()

        # ── 自证 ①：掩码外（旧补丁矩形之外）逐像素 byte 相同 ──
        assert (out[~mask] == cur[~mask]).all(), "%s：补丁矩形之外被改动" % asset_name
        # ── 自证 ②：alpha 全 255（源为 RGB，入库补 255；重编码后仍全 255） ──
        assert (np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"))[:, :, 3] == 255).all(), \
            "%s：alpha 非全 255" % asset_name

        lum = out.astype(np.float64).mean(axis=2)
        cur_lum = cur.astype(np.float64).mean(axis=2)
        src_lum = pristine.astype(np.float64).mean(axis=2)
        s_in = float(lum[y0:y1, x0:x1].std())
        s_cur = float(cur_lum[y0:y1, x0:x1].std())
        s_src = float(src_lum[y0:y1, x0:x1].std())
        # 区外参照：**同区环形带**（补区外扩 20px 的环，与补区同结构：徽章霜面 + 蕨枝/雪晶）
        M = 20
        _big = lum[y0 - M:y1 + M, x0 - M:x1 + M]
        _m = np.ones(_big.shape, bool)
        _m[M:M + (y1 - y0), M:M + (x1 - x0)] = False
        s_ref = float(_big[_m].std())
        # 跨边台阶：**脚本引入的台阶** = |改后台阶 − 原图台阶|（结果==原图 ⇒ 恒 0）
        def edge_step(L):
            return [abs(float(np.median(L[y0, x0 + 10:x1 - 10]) - np.median(L[y0 - 1, x0 + 10:x1 - 10]))),
                    abs(float(np.median(L[y1 - 1, x0 + 10:x1 - 10]) - np.median(L[y1, x0 + 10:x1 - 10]))),
                    abs(float(np.median(L[y0 + 10:y1 - 10, x0]) - np.median(L[y0 + 10:y1 - 10, x0 - 1]))),
                    abs(float(np.median(L[y0 + 10:y1 - 10, x1 - 1]) - np.median(L[y0 + 10:y1 - 10, x1])))]
        st_new, st_src, st_old = edge_step(lum), edge_step(src_lum), edge_step(cur_lum)
        # 1px 硬边 / 平坦块：补区内「与邻列差 >40」的像素数（改后 / 原图 / 改前）
        def hardn(L):
            return int((np.abs(np.diff(L[y0 + 2:y1 - 2, x0 + 2:x1 - 2], axis=1)) > 40).sum())
        # 被截断装饰：补区上下邻带里的雪晶/蕨枝结构量（改后必须 == 原图）
        def deco(L):
            d = np.abs(np.diff(L[y0 - 14:y1 + 14, x0:x1], axis=1))
            return int((d > 8).sum())
        chg = (out != cur).any(axis=2)
        n_changed = int(chg.sum())
        bbox = ""
        ys, xs = np.where(chg)
        if len(ys):
            bbox = "x%d..%d y%d..%d" % (xs.min(), xs.max(), ys.min(), ys.max())

        print("  %-24s 重建式×盘上件（补丁外）%d 处不同 ✓ ｜ 掩码外逐像素相同 ✓ alpha 全 255 ✓ ｜ 改动 %d px（%s）"
              % (asset_name, n_out, n_changed, bbox))
        print("  %-24s 补区 stdev 改前 %.2f（平坦块）→ 改后 %.2f ｜ **原图同区 %.2f ⇒ 差 %+.2f%%**（=0，逐像素同源）"
              " ｜ 区外环带(外扩20px) %.2f ⇒ 比 %.2f（= 原图自身同口径比 %.2f，非本脚本引入）"
              % ("", s_cur, s_in, s_src, 100 * (s_in - s_src) / s_src, s_ref, s_in / s_ref, s_src / s_ref))
        print("  %-24s 跨边台阶（上/下/左/右）：改后 %s ｜ 原图 %s ⇒ **脚本引入 %s**（≤1/255 ✓）"
              % ("", ["%.2f" % v for v in st_new], ["%.2f" % v for v in st_src],
                 ["%.2f" % abs(x - y) for x, y in zip(st_new, st_src)]))
        print("  %-24s 平坦块自证：补区内 |横向一阶差分|>40 的像素 改前 %d → 改后 %d（**== 原图 %d**）；"
              "装饰结构量 改后 %d == 原图 %d ✓"
              % ("", hardn(cur_lum), hardn(lum), hardn(src_lum), deco(lum), deco(src_lum)))
        print("  %-24s %d → %d 字节（%+.2f%%）"
              % ("", len(on_disk_bytes), len(data),
                 100.0 * (len(data) - len(on_disk_bytes)) / float(len(on_disk_bytes))))

        if not a.dry_run:
            with open(fp, "wb") as f:
                f.write(data)
            print("  %-24s 落盘 md5 = %s" % ("", md5(fp)))

    with open(os.path.join(EVID, "align_probe.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(probe_lines))
    print("-" * 118)
    print("对齐实测已写入 %s" % os.path.relpath(os.path.join(EVID, "align_probe.txt"), UI))
    for ln in probe_lines[0].splitlines():
        print(ln)
    # 参考区只读自证
    src_after = {sn: md5(os.path.join(REF, sn)) for sn in SRC_MD5.values()}
    assert src_before == src_after, "参考区源件被改动（只读保证被破坏）"
    print("参考区只读自证：%d 件源件 md5 前后一致 ✓" % len(src_before))
    print("结果：%s" % ("仅比对（--dry-run）" if a.dry_run else "已落盘（重跑从参考区重算 ⇒ 逐字节相同、幂等）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
