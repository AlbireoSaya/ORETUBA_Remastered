#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
emit_chibi.py —— Q 版人物进游戏（ISSUE-20261005-06）
================================================================================
源：`资源组\用户生图素材\成品\素材\*.png`（38 图，每图 2×2 四姿势，RGBA 真透明底，
    含 AI 残留的半透明噪点碎片）
出：
  krkr\game\eyecatch\chibi\s{1,2,3}\cNNN.png   按槽位**预缩放**的单件（3×N；引擎运行期只换 asset+矩形，不缩放）
  krkr\game\story\_eyecatch_chibi.tjs          只定义 uiEyecatchChibiFill(o)（TJS2 跨存储赋全局会抛错）
  krkr\game\eyecatch\chibi\_总览.png           全件拼图（s1 槽产物，供目视核对切分）
  编程组\Q版素材映射.tsv                       索引 → 源文件/源内序号/三槽产物与矩形
口径（用户 2026-10-05 定稿）：
  · 提取＝整图 alpha>64 的 8 邻连通域，面积 ≥ 最大件 **5%**（噪点碎片 ≤6.3k px、真人物 ≥105k px，
    断崖明显；1% 会把噪点当人物）。**绝不按 N×M 硬切**（会把越过分格线的人物切出「挂件」）。
  · 槽位（1920 画布）：上(1754,246)／中(1574,556)／下(1759,896)；
    每槽宽上限 cap_w = 2×min(cx−1448, 1912−cx)（左右各留 8px）⇒ 316/252/306。
  · 缩放 k = min(293/h, cap_w/w)；x = cx−w2//2，y = cy−h2//2。
    实测 149 件 × 3 槽＝447 次落位**零越界、零位移**（不压虚线 x=1440、不出画布右沿）。
  · **每次显示**由引擎随机抽 3 件不同素材（本工具只供池与矩形，不做随机）。
  · ★ 矩形口径：全部按 **1920×1080 主层绝对坐标**（与全 UI 体系一致；`UI_W/UI_H` 缩放口径
    在本工程未启用——若将来启用，此处矩形需随之换算，见 ui_story.tjs 过场卡 contain 逻辑）。
缓存：`chibi\_cache.json`＝源文件(名,大小,mtime) + 参数 + 本工具 md5 ⇒ 未变则跳过提取（全量约 2 分钟）；
  命中时会**核对三槽全部文件存在**，缺任何一件 ⇒ 视为失效重提（防「缓存说有、盘上没有」）。
"""
import argparse
import collections
import glob
import hashlib
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))                  # 工程\我们没有翅膀——…
RES = os.path.join(PROJ, "资源组")
SRC_SUB = os.path.join("用户生图素材", "成品", "素材")

THR = 64
MIN_RATIO = 0.05
MIN_AREA = 1500
MAXH = 293
MARGIN = 8
STRIP_X, STRIP_W = 1440, 480
SLOT_DEFS = [("s1", 1754, 246), ("s2", 1574, 556), ("s3", 1759, 896)]
FONT_CJK = r"C:\Windows\Fonts\msyh.ttc"


# ---------------------------------------------------------------- 提取
def components(mask_bin):
    px = mask_bin.load(); w, h = mask_bin.size
    seen = bytearray(w * h); out = []
    idx = lambda x, y: y * w + x
    for sx in range(w):
        for sy in range(h):
            if px[sx, sy] and not seen[idx(sx, sy)]:
                q = collections.deque([(sx, sy)]); seen[idx(sx, sy)] = 1
                mnx = mxx = sx; mny = mxy = sy; n = 0; pts = set()
                while q:
                    x, y = q.popleft(); n += 1; pts.add((x, y))
                    if x < mnx: mnx = x
                    if x > mxx: mxx = x
                    if y < mny: mny = y
                    if y > mxy: mxy = y
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < w and 0 <= ny < h and px[nx, ny] and not seen[idx(nx, ny)]:
                                seen[idx(nx, ny)] = 1; q.append((nx, ny))
                out.append({"n": n, "bbox": (mnx, mny, mxx, mxy), "pts": pts})
    out.sort(key=lambda c: -c["n"])
    return out


def split_file(path, thr=THR, min_ratio=MIN_RATIO, min_area=MIN_AREA):
    """→ ([(序号, 裁剪件, 面积)], 连通域总数)。裁剪件已把 bbox 内不属于本域的像素 alpha 清零。"""
    im = Image.open(path).convert("RGBA")
    a = im.split()[-1]
    cs = components(a.point(lambda v: 255 if v > thr else 0))
    if not cs:
        return [], 0
    big = cs[0]["n"]
    keep = [c for c in cs if c["n"] >= max(big * min_ratio, min_area)]
    keep.sort(key=lambda c: (0 if (c["bbox"][1] + c["bbox"][3]) / 2 < im.size[1] / 2 else 1, c["bbox"][0]))
    out = []
    for i, c in enumerate(keep, 1):
        x0, y0, x1, y1 = c["bbox"]
        crop = im.crop((x0, y0, x1 + 1, y1 + 1))
        al = crop.split()[-1].load()
        local = {(px - x0, py - y0) for (px, py) in c["pts"]}
        w, h = crop.size
        for yy in range(h):
            for xx in range(w):
                if (xx, yy) not in local:
                    al[xx, yy] = 0
        out.append((i, crop, c["n"]))
    return out, len(cs)


def slot_caps():
    out = []
    for tag, cx, cy in SLOT_DEFS:
        half = min(cx - (STRIP_X + MARGIN), (STRIP_X + STRIP_W - MARGIN) - cx)
        out.append((tag, cx, cy, max(2 * half, 1)))
    return out


# ---------------------------------------------------------------- 主流程
def emit(assets_dir, story_dir, res_root, tsv_path, quiet=False, log=print):
    src = os.path.join(res_root, SRC_SUB)
    files = sorted(glob.glob(os.path.join(src, "*.png")))
    if not files:
        log("[chibi][ERR] 源目录没有 png：%s" % src)
        return 1
    chibi_dir = os.path.join(assets_dir, "chibi")
    os.makedirs(chibi_dir, exist_ok=True)
    cache_p = os.path.join(chibi_dir, "_cache.json")

    with io.open(__file__, "rb") as f:
        tool_md5 = hashlib.md5(f.read()).hexdigest()
    sig = json.dumps({
        "files": [[os.path.basename(f), os.path.getsize(f), int(os.path.getmtime(f))] for f in files],
        "thr": THR, "min_ratio": MIN_RATIO, "min_area": MIN_AREA, "maxh": MAXH,
        "margin": MARGIN, "slots": SLOT_DEFS, "tool": tool_md5,
    }, ensure_ascii=False)

    caps = slot_caps()
    items = None

    def assets_ok():
        # ★ 三槽全部核对（一审 Minor：只查 s1 会漏掉 s2/s3 缺件）
        for it in items:
            for sl in it["slots"]:
                rel = sl["file"][len("eyecatch/"):]          # 剥引擎相对前缀 → assets 目录内相对路径
                if not os.path.isfile(os.path.join(assets_dir, rel.replace("/", os.sep))):
                    return False
        return True

    old = None
    if os.path.isfile(cache_p):
        try:
            with io.open(cache_p, "r", encoding="utf-8") as f:
                j = json.load(f)
            old = j.get("sig"); items = j.get("items")
        except Exception:
            old = None; items = None
    if old == sig and items and assets_ok():
        log("[chibi] 源与参数未变且盘上件齐全 ⇒ 跳过提取（%d 件，缓存 %s）" % (len(items), cache_p))
    else:
        if old != sig:
            log("[chibi] 源/参数/工具变化 ⇒ 重新提取")
        else:
            log("[chibi] 缓存命中但盘上缺件 ⇒ 重新提取")
        for tag, _, _, _ in caps:                     # ★先清空：避免新旧件静默混用
            d = os.path.join(chibi_dir, tag)
            os.makedirs(d, exist_ok=True)
            for f in glob.glob(os.path.join(d, "c*.png")):
                os.remove(f)
        items = []
        for k, f in enumerate(files, 1):
            sp, raw = split_file(f)
            for (i, crop, n) in sp:
                it = {"idx": len(items) + 1, "src": os.path.basename(f), "sub": i,
                      "w": crop.size[0], "h": crop.size[1], "slots": []}
                for (tag, cx, cy, cap) in caps:
                    kk = min(MAXH / crop.size[1], cap / crop.size[0])
                    w2, h2 = max(int(crop.size[0] * kk), 1), max(int(crop.size[1] * kk), 1)
                    x, y = cx - w2 // 2, cy - h2 // 2
                    rel = "chibi/%s/c%03d.png" % (tag, it["idx"])
                    it["slots"].append({"tag": tag, "file": "eyecatch/" + rel,
                                        "x": x, "y": y, "w": w2, "h": h2})
                    crop.resize((w2, h2), Image.LANCZOS).save(os.path.join(chibi_dir, tag, "c%03d.png" % it["idx"]))
                items.append(it)
            log("[chibi] f%02d %-32s 连通域%-3d 保留%-2d" % (k, os.path.basename(f)[:32], raw, len(sp)))
        log("[chibi] 合计 **%d 件**（源 %d 图）" % (len(items), len(files)))
        with io.open(cache_p, "w", encoding="utf-8") as f:
            json.dump({"sig": sig, "items": items}, f, ensure_ascii=False)

    if not quiet:
        _write_tjs(items, story_dir)
        _write_tsv(items, tsv_path)
        _write_sheet(items, chibi_dir)
    log("[chibi] %d 件 × %d 槽 = %d 个预缩放件 ⇒ %s" % (len(items), len(caps), len(items) * len(caps), chibi_dir))
    return 0


def _write_tjs(items, story_dir):
    caps = slot_caps()
    lines = ["// 生成物（build_story.py → emit_chibi.py）——勿手改：Q 版人物池与槽位矩形",
             "// 形式：只定义 uiEyecatchChibiFill(o)（TJS2 跨存储给全局赋值会抛「未找到 Member」）",
             "function uiEyecatchChibiFill(o)",
             "{",
             "\to.slots = [" + ",".join("%%[x:%d,y:%d,w:%d,h:%d]" % (cx, cy, cap, MAXH)
                                       for tag, cx, cy, cap in caps) + "];"]
    for si, (tag, cx, cy, cap) in enumerate(caps):
        lines.append("\to.files[%d] = [%s];" % (si, ",".join('"%s"' % it["slots"][si]["file"] for it in items)))
        lines.append("\to.rects[%d] = [%s];" % (si, ",".join(
            "%%[x:%d,y:%d,w:%d,h:%d]" % (it["slots"][si]["x"], it["slots"][si]["y"],
                                         it["slots"][si]["w"], it["slots"][si]["h"]) for it in items)))
    lines.append("\treturn o.files[0].count;")
    lines.append("}")
    os.makedirs(story_dir, exist_ok=True)
    with io.open(os.path.join(story_dir, "_eyecatch_chibi.tjs"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def _write_tsv(items, tsv_path):
    if not tsv_path:
        return
    os.makedirs(os.path.dirname(tsv_path), exist_ok=True)
    with io.open(tsv_path, "w", encoding="utf-8", newline="") as f:
        f.write("索引\t源文件\t源内序号\t源尺寸\ts1产物\ts2产物\ts3产物\t三槽矩形(x,y,w,h)\n")
        for it in items:
            f.write("%d\t%s\t%d\t%dx%d\t%s\t%s\t%s\t%s\n" % (
                it["idx"], it["src"], it["sub"], it["w"], it["h"],
                it["slots"][0]["file"], it["slots"][1]["file"], it["slots"][2]["file"],
                " | ".join("%d,%d,%d,%d" % (sl["x"], sl["y"], sl["w"], sl["h"]) for sl in it["slots"])))


def _write_sheet(items, chibi_dir):
    p = os.path.join(chibi_dir, "_总览.png")
    cw, cols = 150, 10
    tiles = []
    for it in items:
        fp = os.path.join(chibi_dir, "s1", "c%03d.png" % it["idx"])
        if not os.path.isfile(fp):
            return
        im = Image.open(fp).convert("RGBA")
        b = Image.new("RGB", im.size, (255, 255, 255)); b.paste(im, (0, 0), im)
        tiles.append(("c%03d" % it["idx"], b.resize((cw, max(int(im.size[1] * cw / im.size[0]), 1)), Image.LANCZOS)))
    if not tiles:
        return
    ch = max(t[1].size[1] for t in tiles) + 20
    rows = (len(tiles) + cols - 1) // cols
    sh = Image.new("RGB", (cw * cols + 6 * (cols + 1), ch * rows + 6 * (rows + 1)), (238, 238, 238))
    d = ImageDraw.Draw(sh); f = ImageFont.truetype(FONT_CJK, 14)
    for i, (nm, t) in enumerate(tiles):
        r, c = divmod(i, cols); x = 6 + c * (cw + 6); y = 6 + r * ch
        d.text((x + 2, y + 2), nm, font=f, fill=(20, 20, 20)); sh.paste(t, (x, y + 16))
    sh.save(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default=RES, help="资源组目录（worktree 常无重资产 ⇒ 指向主工作树）")
    ap.add_argument("--assets", default=os.path.join(PROJ, "编程组", "krkr", "game", "eyecatch"))
    ap.add_argument("--story", default=os.path.join(PROJ, "编程组", "krkr", "game", "story"))
    ap.add_argument("--tsv", default=os.path.join(PROJ, "编程组", "Q版素材映射.tsv"))
    a = ap.parse_args()
    return emit(a.assets, a.story, a.res, a.tsv)


if __name__ == "__main__":
    sys.exit(main())
