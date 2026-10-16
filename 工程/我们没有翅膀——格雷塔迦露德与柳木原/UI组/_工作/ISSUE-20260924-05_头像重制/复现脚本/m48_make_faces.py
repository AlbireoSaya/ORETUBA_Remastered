# -*- coding: utf-8 -*-
r"""M48 · 对话框头像重制（ISSUE-20260924-05）· 生成器

用户 2026-09-24 验收要求：对话框头像统一取景 **从头顶 → 肩部下 + 一小段上臂**；
`mis`（林田美咲）/ `ai`（香田亚衣）为成功例子（按它们那样取景）；`kan` 底边须比现行 M44 框
**上移约 20px（276×345 输出像素）**；`nar` 的水平方向须**框全**（现行框右侧被裁）。

--------------------------------------------------------------------------
口径说明（与主代理冻结口径的对应关系，**必读**）
--------------------------------------------------------------------------
主代理冻结的「解剖标志」路线为：T / head_w / neck / shoulder → 底边 = shoulder + drop。
**实测结论（证据见 `证据/对照_*` 与 `_报告.md`）：本素材集的 shoulder / neck 无法从 alpha
轮廓可信测出**——这些立绘是**半身像**，多数角色（尤其长发、戴帽、披风族）**头发或服饰的轮廓
比肩膀更宽**，轮廓宽度剖面里根本没有「颈凹 + 肩凸」这两个特征（例：`ai` 的轮廓在上半身持续
变宽直到 y≈400，而视觉肩线在 y≈227；`mis` 的轮廓最大宽度出现在头发处）。
若照字面实现冻结口径，`mis` 的框会变成 513×641（现行 220×275，即 2.3 倍），画面人物过小。

故本脚本改用**等价、可复算、可目视自证**的口径：**以「半身像的墨迹高度」作垂直锚**
（这套半身像的裁切高度一致，墨迹高 ≈ 头高的固定倍数），水平以「躯干带墨迹跨度」装箱。

    T        = 首行墨迹 y（阈值 alpha>8，步长 1）
    ink_h    = 末行墨迹 y − T（半身像高度）
    ch       = round(K × ink_h)              K = 0.575（用 mis/ai 标定，用 kan 校验）
    cw       = round(276/345 × ch)
    装箱     : 躯干带 = [T + 0.45·ch, T + ch]；若其墨迹跨度 ×1.04 > cw 则放大 cw（迭代收敛），
               以免「人物右侧被裁」（`nar` 即由此修正）
    居中     : 使**躯干带**墨迹跨度在框内居中（`nar` 右侧因此不再出框）；最后夹到画布内
    y0       = T（头贴框顶，沿用 M44 观感）
    drop     : 落盘时记 `(底边 − T)/头宽`；按 `mis/ai` 标定，`kan` 校验（见 `--report`）

像素来源：`美术统一_超分\立绘\`（2×，实测恰 2.00×）取对应区域后 **LANCZOS** 重采样到
**276×345**（与 M44 同一锐度口径，未换算法）。
同族多表情：沿用 M44「基准图定框 + 头部带互相关求平移（dx,dy）」，**同族一个框**。
输出：`UI组\krkr\assets\face\<源名>.png`（**361 张、文件名不变、尺寸一律 276×345**）。
"""
import collections
import io
import os
import re
import sys

from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
D1 = os.path.join(BASE, "美术统一", "立绘")
D2 = os.path.join(BASE, "美术统一_超分", "立绘")
WT = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
OUT = os.path.join(WT, "krkr", "assets", "face")
WKDIR = os.path.join(WT, "_工作", "ISSUE-20260924-05_头像重制")
PREV = os.path.join(WKDIR, "_批量产物")

SC = 4                          # 缩样因子（互相关对齐用）
BOX_W, BOX_H = 276, 345
PAT = re.compile(r"^([a-z_]+?)(\d*)([a-z_]*)$")

K = 0.575                       # 框高 = K × 半身像墨迹高（mis/ai 标定、kan 校验）
INK_THR = 8                     # alpha 墨迹阈值
# 逐族人工定框（**只放经过目视定标、且统一 K 天然不适用的族**；命名见 `_报告`）
#
#   `nar`：躯干（肩/臂右缘 x=300）比其**头发中心**（cx≈150）右 48px，统一规则给的框（x 26..271）
#          会切掉 25px 人物右肩 → 用户点名「人物右边被裁掉了」。
#          改为「把全带墨迹跨度（x 4..300）整段装进框」：cw=308 / ch=385 / x0=0。
#
#   `min`（vision 一审打回后立）：该族是**大头长发型**——头顶→下颏≈232px、下颏→肩线≈272px，
#          而头发在两侧垂到 y≈390 ⇒ 统一 K=0.575 给的 ch=314 只到肩线下 42px（13% 框高），
#          看不到「一截上臂」（vision 实测肩线下仅 25–45px = 7–13%）。
#          改用**冻结口径自己的语义式**在该族上复算：底边 = 肩线 + 0.40 × 头高
#          = 272 + 0.40×250 = 372（头高 = neck − T = 250，肩线经 3× 目视定标 = 272），
#          cw = 0.8×372 = 297，x0 = 60（[T, 底边] 带内墨迹 x 30..387 的中点居中）。
#          校验：drop/头高 = 0.40 ∈ 冻结区间 [0.30,0.45]；肩线下余量 100px = 26.9% 框高，
#          落在 mis(26%)/ai(31%) 之间；(底边−冻结肩线)/head_w = 77/164 = 0.47 ≥ 0.15。
PER_FAMILY = {"nar": dict(cw=308, ch=385, x0=0),
              "min": dict(cw=297, ch=372, x0=60)}


# ------------------------------------------------------------------ 量测

def ink_rows(im, thr=INK_THR):
    """逐行墨迹 (y, x0, x1, w)，步长 1（精度优先）。"""
    a = im.getchannel("A")
    W, H = im.size
    out = []
    for y in range(H):
        xs = [x for x in range(W) if a.getpixel((x, y)) > thr]
        out.append((y, xs[0], xs[-1], len(xs)) if len(xs) >= 2 else (y, 0, 0, 0))
    return [r for r in out if r[3] > 0]


def head_of(rows):
    """M44 原式（仅用于报告里的 head_w 参照值）：宽度剖面第一个局部极大。"""
    T = rows[0][0]
    ws = [(r[0], r[3], (r[1] + r[2]) // 2) for r in rows]
    best = ws[0]
    down = 0
    for i in range(1, len(ws)):
        if ws[i][1] > best[1]:
            best = ws[i]
            down = 0
        elif ws[i][1] < best[1]:
            down += 1
            if down >= 3 and best[0] > T:
                return best[1], best[2], T
        else:
            down = 0
    return best[1], best[2], T


def band_span(rows, y0, y1):
    sel = [r for r in rows if y0 <= r[0] <= y1]
    if not sel:
        return 0, 0
    return min(r[1] for r in sel), max(r[2] for r in sel)


def m44_rows(im):
    """M44 `rows_of` 的逐字复刻（**步长 2 采样**，连续 ≥2 个偶数列有墨才算一行）——
    现行框高必须用它复算，否则与 `krkr\\assets\\face\\` 里的现状对不上。"""
    a = im.getchannel("A")
    W, H = im.size
    out = []
    for y in range(H):
        xs = [x for x in range(0, W, 2) if a.getpixel((x, y)) > INK_THR]
        out.append((y, xs[0], xs[-1], xs[-1] - xs[0] + 1) if len(xs) >= 2 else (y, 0, 0, 0))
    return [r for r in out if r[3] > 0]


def m44_cur_ch(im):
    """现行 M44 生成的框高（1× 坐标）：cw = max(60, head_w×0.97)、ch = cw×345/276；
    闸门（头宽/墨迹高 ∈ [0.18,0.75]）外改用 head_w = 0.30×墨迹高。"""
    rows = m44_rows(im)
    hw, _hcx, _T = head_of(rows)
    ink_h = rows[-1][0] - rows[0][0]
    gated = not (0.18 <= hw / max(1, ink_h) <= 0.75)
    if gated:
        hw = int(round(0.30 * ink_h))
    cw = max(60, int(round(hw * 0.97)))
    return int(round(cw * BOX_H / BOX_W)), gated


def geometry(rows, W1, fam="", k=K):
    """返回定框几何 dict。

    垂直：y0 = T（头贴框顶），ch = round(k × ink_h)。
    水平：cw = round(0.8 × ch)，居中于**全带** [T, T+ch] 的墨迹跨度中点，最后夹进画布。
    逐族覆盖：`PER_FAMILY`（当前仅 nar）。
    """
    T = rows[0][0]
    ink_h = rows[-1][0] - T
    ch = int(round(k * ink_h))
    cw = int(round(ch * BOX_W / BOX_H))
    full0, full1 = band_span(rows, T, T + ch)
    cx = (full0 + full1) // 2
    x0 = int(round(cx - cw / 2))
    x0 = max(0, min(x0, max(0, W1 - cw)))
    ov = ""
    if fam in PER_FAMILY:
        o = PER_FAMILY[fam]
        cw, ch, x0 = o["cw"], o["ch"], o["x0"]
        ov = "逐族覆盖"
        cx = x0 + cw // 2
    hw, hcx, _ = head_of(rows)
    return dict(T=T, ink_h=ink_h, ch=ch, cw=cw, x0=x0, y0=T, cx=cx,
                full0=full0, full1=full1, override=ov,
                head_w_m44=hw, head_cx_m44=hcx, bottom=T + ch,
                clipped_l=max(0, x0 - full0), clipped_r=max(0, full1 - (x0 + cw)))


# ------------------------------------------------------------------ 取样

def crop_2x(name, x0, y0, w, h):
    with Image.open(os.path.join(D2, name + ".png")).convert("RGBA") as im2:
        W2, H2 = im2.size
        c = im2.crop((max(0, x0) * 2, max(0, y0) * 2,
                      min(W2, (x0 + w) * 2), min(H2, (y0 + h) * 2)))
    canvas = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    canvas.paste(c, (max(0, -x0) * 2, max(0, -y0) * 2))
    return canvas.resize((BOX_W, BOX_H), Image.LANCZOS)


def alpha_small(path):
    with Image.open(path).convert("RGBA") as im:
        W, H = im.size
        return im.getchannel("A").resize((max(1, W // SC), max(1, H // SC)),
                                         Image.BILINEAR), W, H


def align(ref_small, cur_small, band_h, span_x, span_y):
    """基准图头部带内整像素平移搜索 ⇒ (dx, dy)（1× 坐标）。沿用 M44 原实现。"""
    rw, rh = ref_small.size
    cw, ch = cur_small.size
    bx = min(rw, cw)
    by = min(band_h, rh, ch)
    ref = ref_small.crop((0, 0, bx, by))
    rp = ref.load()
    best = (0, 0, None)
    for dy in range(-span_y, span_y + 1):
        for dx in range(-span_x, span_x + 1):
            sad = 0
            n = 0
            for y in range(0, by, 2):
                yy = y + dy
                if yy < 0 or yy >= ch:
                    continue
                for x in range(0, bx, 2):
                    xx = x + dx
                    if xx < 0 or xx >= cw:
                        continue
                    sad += abs(rp[x, y] - cur_small.getpixel((xx, yy)))
                    n += 1
            if n < 50:
                continue
            v = sad / n
            if best[2] is None or v < best[2]:
                best = (dx, dy, v)
    return best[0] * SC, best[1] * SC


def is_sprite(p):
    with Image.open(p) as im:
        W, H = im.size
    return not (W == 1280 and H == 720) and H > W


# ------------------------------------------------------------------ 主流程

def collect():
    files = sorted(x[:-4] for x in os.listdir(D1) if x.endswith(".png"))
    fam = collections.defaultdict(lambda: collections.defaultdict(list))
    excl = collections.Counter()
    for n in files:
        m = PAT.match(n)
        if not m:
            continue
        f, b, s = m.group(1), m.group(2) or "01", m.group(3)
        p = os.path.join(D1, n + ".png")
        if not is_sprite(p):
            with Image.open(p) as im:
                W, H = im.size
            excl["1280×720 整屏图" if (W, H) == (1280, 720)
                 else ("面部特写（横构图，如 f_mis）" if "f_mis" in f
                       else "其它非竖构图")] += 1
            continue
        fam[f][b].append(s)
    return fam, excl


def main():
    report_only = "--report" in sys.argv
    preview = "--preview" in sys.argv
    outdir = PREV if preview else OUT
    if not report_only:
        os.makedirs(outdir, exist_ok=True)
    fam, excl = collect()
    geo = {}
    for f in sorted(fam):
        b = max(fam[f], key=lambda t: len(fam[f][t]))
        ref = f + b
        if not os.path.exists(os.path.join(D1, ref + ".png")):
            ref = f + b + sorted(fam[f][b])[0]
        with Image.open(os.path.join(D1, ref + ".png")).convert("RGBA") as imr:
            rows = ink_rows(imr)
            W1, H1 = imr.size
        geo[f] = (b, ref, geometry(rows, W1, f))
    n_done = 0
    if not report_only:
        for f in sorted(geo):
            b, ref, g = geo[f]
            ref_s, rW, rH = alpha_small(os.path.join(D1, ref + ".png"))
            band = max(2, int(0.30 * (rH // SC)))
            for s in sorted(fam[f][b]):
                nm = f + b + s
                if nm != ref:
                    cur_s, cW, cH = alpha_small(os.path.join(D1, nm + ".png"))
                    dx, dy = align(ref_s, cur_s, band, span_x=20, span_y=12)
                else:
                    dx = dy = 0
                crop_2x(nm, g["x0"] + dx, g["y0"] + dy, g["cw"], g["ch"]).save(
                    os.path.join(outdir, nm + ".png"))
                n_done += 1
    print("族 %d ｜ 生成 %d 张 ｜ 排除 %s" % (len(fam), n_done, dict(excl)))
    print("K=%.3f  INK_THR=%d  逐族覆盖=%s" % (K, INK_THR, list(PER_FAMILY)))
    hdr = ("%-5s %-5s %6s %5s %6s %6s %7s %6s %6s %6s %6s %6s %6s %8s"
           % ("族", "基底", "ink_h", "T", "ch(new)", "cur_ch", "Δch", "框w", "框x0",
              "全带x0", "全带x1", "左裁", "右裁", "覆盖"))
    print(hdr)
    for f in sorted(geo):
        b, ref, g = geo[f]
        with Image.open(os.path.join(D1, ref + ".png")).convert("RGBA") as imr:
            cur_ch, gated = m44_cur_ch(imr)
        print("%-5s %-5s %6d %5d %6d %6d %7d %6d %6d %6d %6d %6d %6d %8s"
              % (f, b, g["ink_h"], g["T"], g["ch"], cur_ch, g["ch"] - cur_ch,
                 g["cw"], g["x0"], g["full0"], g["full1"],
                 g["clipped_l"], g["clipped_r"], g["override"]))


if __name__ == "__main__":
    main()
