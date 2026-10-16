# -*- coding: utf-8 -*-
r"""M44 · 对话框头像批量生成器（定稿版，可复现）

产出：`krkr\assets\face\<源名>.png`（361 张，35 族 × 每族 1 个基底的每种表情），统一 **360×450**。

几何口径（用户 2026-09-23 裁定「B 方案」：只到肩膀下方一点点 + 放大观感）：
  · **以头宽归一**：`crop_w = head_w × 0.97`、`crop_h = crop_w × 1.25`（锁定 276:345＝4:5，头约占画框宽 103%）
  · **按 (族, 基底) 用基准图算一次框**，同基底的表情**不再重新认头**，而是与基准图的**头部区域做互相关**求平移
    —— 否则抬手/戴帽姿态会让「顶部最宽行」量到手臂（实测 `ten01a` 在 y133 从 168 跳到 337 ⇒ 同族头像差近 2 倍）
  · **合理性闸门**：头宽/墨迹高必须落在 18%–75%，越界不硬猜，改用默认比例 0.30 并写入 `_需人工定框.tsv`
像素来源：`资源组\美术统一_超分\立绘\<名>.png`（2× 超分件，与 1× 同名同内容、实测恰 2.00×）
  取 2× 上的对应区域后重采样到 276×345（实测系数 0.68–1.67、中位 0.88；160/361 张为轻度放大插值）
排除：1280×720 整屏图 259 件、`f_mis` 面部特写 60 件、其它非竖构图 32 件
"""
import os, re, collections, io
from PIL import Image

BASE = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组"
D1 = os.path.join(BASE, "美术统一", "立绘")
D2 = os.path.join(BASE, "美术统一_超分", "立绘")
OUT = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作\M44_头像裁切方案\_批量产物"
os.makedirs(OUT, exist_ok=True)
BOX_W, BOX_H, SC = 276, 345, 4
PAT = re.compile(r"^([a-z_]+?)(\d*)([a-z_]*)$")


def rows_of(im):
    a = im.getchannel("A"); W, H = im.size
    out = []
    for y in range(H):
        xs = [x for x in range(0, W, 2) if a.getpixel((x, y)) > 8]
        out.append((y, xs[0], xs[-1], xs[-1] - xs[0] + 1) if len(xs) >= 2 else (y, 0, 0, 0))
    return [r for r in out if r[3] > 0]


def head_of(rows):
    """宽度剖面的第一个局部极大 ⇒ (head_w, head_cx, T)。"""
    T = rows[0][0]
    ws = [(r[0], r[3], (r[1] + r[2]) // 2) for r in rows]
    best = ws[0]; down = 0
    for i in range(1, len(ws)):
        if ws[i][1] > best[1]: best = ws[i]; down = 0
        elif ws[i][1] < best[1]:
            down += 1
            if down >= 3 and best[0] > T: return best[1], best[2], T
        else: down = 0
    return best[1], best[2], T


def alpha_small(path):
    with Image.open(path).convert("RGBA") as im:
        W, H = im.size
        return im.getchannel("A").resize((max(1, W // SC), max(1, H // SC)), Image.BILINEAR), W, H


def align(ref_small, cur_small, band_h, span_x, span_y):
    """基准图头部带内整像素平移搜索 ⇒ (dx, dy)（1× 坐标）。"""
    rw, rh = ref_small.size; cw, ch = cur_small.size
    bx = min(rw, cw); by = min(band_h, rh, ch)
    ref = ref_small.crop((0, 0, bx, by)); rp = ref.load()
    best = (0, 0, None)
    for dy in range(-span_y, span_y + 1):
        for dx in range(-span_x, span_x + 1):
            sad = 0; n = 0
            for y in range(0, by, 2):
                yy = y + dy
                if yy < 0 or yy >= ch: continue
                for x in range(0, bx, 2):
                    xx = x + dx
                    if xx < 0 or xx >= cw: continue
                    sad += abs(rp[x, y] - cur_small.getpixel((xx, yy))); n += 1
            if n < 50: continue
            v = sad / n
            if best[2] is None or v < best[2]: best = (dx, dy, v)
    return best[0] * SC, best[1] * SC


def is_sprite(p):
    with Image.open(p) as im:
        W, H = im.size
    return not (W == 1280 and H == 720) and H > W


def crop_from_2x(name, cx, top, cw, ch):
    with Image.open(os.path.join(D2, name + ".png")).convert("RGBA") as im2:
        W2, H2 = im2.size
        x0 = cx - cw // 2; y0 = top
        c = im2.crop((max(0, x0) * 2, max(0, y0) * 2, min(W2, (x0 + cw) * 2), min(H2, (y0 + ch) * 2)))
    canvas = Image.new("RGBA", (cw * 2, ch * 2), (0, 0, 0, 0))
    canvas.paste(c, (max(0, -x0) * 2, max(0, -y0) * 2))
    return canvas.resize((BOX_W, BOX_H), Image.LANCZOS)


def main():
    files = sorted(x[:-4] for x in os.listdir(D1) if x.endswith(".png"))
    fam = collections.defaultdict(lambda: collections.defaultdict(list))
    excl = collections.Counter()
    for n in files:
        m = PAT.match(n)
        if not m: continue
        f, b, s = m.group(1), m.group(2) or "01", m.group(3)
        p = os.path.join(D1, n + ".png")
        if not is_sprite(p):
            with Image.open(p) as im: W, H = im.size
            excl["1280×720 整屏图" if (W, H) == (1280, 720) else ("面部特写（横构图，如 f_mis）" if "f_mis" in f else "其它非竖构图")] += 1
            continue
        fam[f][b].append(s)
    picked, NEEDS_HUMAN = [], []
    for f in sorted(fam):
        b = max(fam[f], key=lambda k: len(fam[f][k]))
        ref = f + b
        if not os.path.exists(os.path.join(D1, ref + ".png")): ref = f + b + sorted(fam[f][b])[0]
        with Image.open(os.path.join(D1, ref + ".png")).convert("RGBA") as imr:
            rowsr = rows_of(imr); hw, hcx, T = head_of(rowsr); ink_h = rowsr[-1][0] - rowsr[0][0]
        ratio = hw / max(1, ink_h)
        if not (0.18 <= ratio <= 0.75):
            NEEDS_HUMAN.append((f, hw, ink_h, round(ratio, 2))); hw = int(round(0.30 * ink_h))
        cw = max(60, int(round(hw * 0.97))); ch = int(round(cw * BOX_H / BOX_W))
        ref_s, rW, rH = alpha_small(os.path.join(D1, ref + ".png"))
        band = max(2, int(0.30 * (rH // SC)))
        for s in sorted(fam[f][b]):
            nm = f + b + s
            cur_s, cW, cH = alpha_small(os.path.join(D1, nm + ".png"))
            dx, dy = align(ref_s, cur_s, band, span_x=20, span_y=12)
            crop_from_2x(nm, hcx + dx, T + dy, cw, ch).save(os.path.join(OUT, nm + ".png"))
            picked.append((nm, f, b, hw, cw))
    tot = sum(os.path.getsize(os.path.join(OUT, n + ".png")) for n, *_ in picked)
    print("族 %d ｜ 生成 %d 张 ｜ %.2f MB ｜ 均值 %.0f KB ｜ 排除 %s"
          % (len(fam), len(picked), tot / 1048576, tot / len(picked) / 1024, dict(excl)))
    print("★ 需人工定框的族：", NEEDS_HUMAN)
    with io.open(os.path.join(OUT, "_清单.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("头像文件\t族\t基底\t1× 头宽\t裁框宽\n")
        for n, f, b, hw, cw in picked: fh.write("%s.png\t%s\t%s\t%d\t%d\n" % (n, f, b, hw, cw))
    with io.open(os.path.join(OUT, "_需人工定框.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("族\t自动量到的头宽\t墨迹高\t比值\n")
        for r in NEEDS_HUMAN: fh.write("%s\t%d\t%d\t%s\n" % r)


if __name__ == "__main__":
    main()