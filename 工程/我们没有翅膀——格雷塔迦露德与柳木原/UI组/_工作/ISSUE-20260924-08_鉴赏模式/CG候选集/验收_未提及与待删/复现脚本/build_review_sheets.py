# -*- coding: utf-8 -*-
r"""ISSUE-20260924-08 · 看图裁决用三张小接触印相表（只读源，只写本目录）

输入（只读）：
  CG候选集\清单.tsv                      —— 363 组
  CG候选集\代表图\<序号>_<组名>.png       —— 代表图（md5 用于「同图」判定）
  CG候选集\用户新顺序_20260924.txt        —— 用户给定的新顺序 + 删除清单
  资源组\美术统一\CG背景\<统一名>          —— 原图（B 的候选列用）

输出（本目录）：
  sheet_未提及19件.png     A · 19 个用户清单未提及的旧组（+ 红/绿同图判定）
  sheet_待删4件.png        B · 删除清单里无同图孪生的 4 件 + 疑似孪生候选
  sheet_重复4行.png        C · 同一旧 ID 在用户清单出现两次的 4 处
  待确认清单.tsv            A/B/C 三类合并清单

口径：「旧ID」= 本包（CG候选集，363 组）的组序号。
      同图判定 = **代表图 md5 逐字节相同**。
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
import re

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))              # 验收_未提及与待删
CG = os.path.abspath(os.path.join(OUT, ".."))                # CG候选集
ROOT = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
RES = os.path.join(ROOT, "资源组")
assert os.path.isdir(RES), RES
assert os.path.isfile(os.path.join(CG, "清单.tsv")), CG
MANIFEST = os.path.join(CG, "清单.tsv")
REPDIR = os.path.join(CG, "代表图")
CGDIR = os.path.join(RES, "美术统一", "CG背景")
USERLIST = os.path.join(CG, "用户新顺序_20260924.txt")

MARGIN = 16
SHEET_W = 2400
BG = (16, 17, 20)
BG_CELL = (34, 36, 41)
BORDER = (72, 78, 90)
FG = (236, 238, 242)
FG_DIM = (150, 156, 168)
GREEN = (92, 214, 132)
RED = (246, 96, 96)
AMBER = (240, 190, 90)
BG_BADGE = (0, 0, 0, 150)

FONTS = (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf")


def font(sz):
    for p in FONTS:
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------- 数据
class Data:
    def __init__(self):
        rows = list(csv.DictReader(io.open(MANIFEST, encoding="utf-8-sig"), delimiter="\t"))
        self.by = {int(r["组序号"]): r for r in rows}
        self.name = {i: self.by[i]["组名"] for i in self.by}
        self.n = {i: int(self.by[i]["差分件数"]) for i in self.by}
        self.size = {i: self.by[i]["代表图尺寸"] for i in self.by}
        self.unis = {i: self.by[i]["统一名列表"].split("、") for i in self.by}
        self.rep = {i: md5(os.path.join(REPDIR, "%03d_%s.png" % (i, self.name[i]))) for i in self.by}
        self.diffs = {i: {u: md5(os.path.join(CGDIR, u)) for u in self.unis[i]} for i in self.by}

        self.new2old, self.merged, self.mentioned, self.deleted = self._parse_userlist()
        # A：未提及（也不在删除清单）
        self.unmentioned = sorted(i for i in self.by if i not in self.mentioned and i not in self.deleted)
        # 代表图孪生
        self.rep_twin = {i: sorted(j for j in self.by if j != i and self.rep[j] == self.rep[i]) for i in self.by}
        # 任一差分孪生（补充信息）
        self.any_twin = {}
        for i in self.by:
            hits = {}
            for u, h in self.diffs[i].items():
                for j in self.by:
                    if j == i:
                        continue
                    for uu, hh in self.diffs[j].items():
                        if hh == h:
                            hits.setdefault(j, []).append((u, uu))
            self.any_twin[i] = hits
        # B：删除清单里「段一未出现 且 代表图无孪生」
        self.b4 = [i for i in self.deleted if i not in self.mentioned and not self.rep_twin[i]]
        # C：同一旧ID在段一被引用两次
        cnt = {}
        for nid, oid in self.new2old.items():
            cnt.setdefault(oid, []).append(nid)
        self.dup = sorted((oid, sorted(v)) for oid, v in cnt.items() if len(v) > 1)

    def _parse_userlist(self):
        new2old, merged, mentioned, deleted = {}, {}, set(), []
        seg = 1
        for line in io.open(USERLIST, encoding="utf-8"):
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                if u"段二" in s:
                    seg = 2
                continue
            if seg == 1:
                m = re.match(r"^(\d+)\.(\d+)\s*(?:\(\+(.*)\))?\s*$", s)
                assert m, s
                nid, oid = int(m.group(1)), int(m.group(2))
                new2old[nid] = oid
                mentioned.add(oid)
                if m.group(3):
                    extra = [int(x) for x in re.split(r"[+\s]+", m.group(3).strip()) if x]
                    merged[nid] = extra
                    mentioned.update(extra)
            else:
                m = re.match(r"^(\d+)\.(\d+)\s*$", s)
                assert m, s
                deleted.append(int(m.group(2)))
        return new2old, merged, mentioned, deleted


# ---------------------------------------------------------------- 绘图基元
def fit(path, max_edge):
    im = Image.open(path).convert("RGB")
    k = min(max_edge / im.width, max_edge / im.height)
    return im.resize((max(1, int(round(im.width * k))), max(1, int(round(im.height * k)))), Image.LANCZOS)


def badge(d, x, y, text, f):
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    bw, bh = tw + 16, th + 8
    layer = Image.new("RGBA", (bw, bh), BG_BADGE)
    d._image.paste(layer, (x, y), layer)
    d.text((x + 8 - bb[0], y + 4 - bb[1]), text, font=f, fill=FG)


def draw_cell(canvas, x0, y0, w, h, rep_path, idx_text, name, lines, thumb_max, highlight=None):
    """lines: [(text, color), …] 画在缩略图下方。highlight: 边框颜色。"""
    cell = Image.new("RGB", (w, h), BG_CELL)
    cd = ImageDraw.Draw(cell)
    cd.rectangle([0, 0, w - 1, h - 1], outline=highlight or BORDER, width=3 if highlight else 1)

    im = fit(rep_path, thumb_max)
    bx, by = (w - im.width) // 2, 8
    cd.rectangle([bx, by, bx + im.width - 1, by + im.height - 1], fill=(10, 10, 12))
    cell.paste(im, (bx, by))
    badge(cd, bx + 5, by + 5, idx_text, font(26))

    ty = by + im.height + 10
    for text, color in lines:
        cd.text((10, ty), text, font=font(22), fill=color)
        ty += 28
    canvas.paste(cell, (x0, y0))


def sheet_header(d, title, legend):
    d.text((MARGIN + 4, MARGIN + 6), title, font=font(34), fill=FG)
    d.text((MARGIN + 4, MARGIN + 46), legend, font=font(20), fill=FG_DIM)


# ---------------------------------------------------------------- A
def build_A(data):
    items = data.unmentioned
    COLS, ROWS = 5, 4
    GAP = 10
    CW = (SHEET_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
    CH = 380
    HEAD = 84
    H = MARGIN + HEAD + ROWS * CH + (ROWS - 1) * GAP + MARGIN
    sh = Image.new("RGB", (SHEET_W, H), BG)
    d = ImageDraw.Draw(sh)
    sheet_header(d,
                 u"A · 用户新清单里未提及的旧组  %d 件" % len(items),
                 u"绿=该组代表图与另一组逐字节同图（删掉不丢图） ｜ 红=无同图孪生（删掉该图即消失） ｜ 「旧ID」=本包 363 组的组序号")

    for j, i in enumerate(items):
        r, c = divmod(j, COLS)
        x0 = MARGIN + c * (CW + GAP)
        y0 = MARGIN + HEAD + r * (CH + GAP)
        t = data.rep_twin[i]
        if t:
            line = (u"与 %s 逐字节同图" % u"、".join("%03d" % x for x in t), GREEN)
            hl = None
        else:
            line = (u"无同图孪生", RED)
            hl = RED
        draw_cell(sh, x0, y0, CW, CH,
                  os.path.join(REPDIR, "%03d_%s.png" % (i, data.name[i])),
                  "%03d" % i, data.name[i],
                  [(data.name[i], FG),
                   (u"差%d ｜ %s" % (data.n[i], data.size[i]), FG_DIM),
                   line],
                  300, highlight=hl)
    p = os.path.join(OUT, u"sheet_未提及19件.png")
    sh.save(p, optimize=True)
    return p


# ---------------------------------------------------------------- B
def build_B(data):
    COLS = 4
    GAP = 12
    CW = (SHEET_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
    CH = 380
    HEAD = 84
    H = MARGIN + HEAD + len(data.b4) * (CH + GAP) + MARGIN
    sh = Image.new("RGB", (SHEET_W, H), BG)
    d = ImageDraw.Draw(sh)
    sheet_header(d,
                 u"B · 用户删除清单里「代表图无同图孪生」的 4 件  +  按文件名前缀/尺寸找出的疑似孪生候选",
                 u"第 1 格=待删件（红框） ｜ 右侧=疑似孪生候选，请肉眼比对是否同一张画 ｜ 找不到候选则如实写「无候选」")

    for r, i in enumerate(data.b4):
        y0 = MARGIN + HEAD + r * (CH + GAP)
        x0 = MARGIN
        draw_cell(sh, x0, y0, CW, CH,
                  os.path.join(REPDIR, "%03d_%s.png" % (i, data.name[i])),
                  "%03d" % i, data.name[i],
                  [(data.name[i], FG),
                   (u"待删 · 差%d ｜ %s" % (data.n[i], data.size[i]), RED),
                   (u"无同图孪生", RED)],
                  300, highlight=RED)

        cands = data.cands.get(i, [])
        for k in range(COLS - 1):
            x = x0 + (k + 1) * (CW + GAP)
            if k < len(cands):
                j, why = cands[k]
                draw_cell(sh, x, y0, CW, CH,
                          os.path.join(REPDIR, "%03d_%s.png" % (j, data.name[j])),
                          "%03d" % j, data.name[j],
                          [(data.name[j], FG),
                           (u"候选 ｜ 差%d ｜ %s" % (data.n[j], data.size[j]), AMBER),
                           (why, FG_DIM)],
                          300)
            elif k == 0 and not cands:
                cell = Image.new("RGB", (CW, CH), BG_CELL)
                cd = ImageDraw.Draw(cell)
                cd.rectangle([0, 0, CW - 1, CH - 1], outline=BORDER, width=1)
                cd.text((16, CH // 2 - 16), u"无候选", font=font(34), fill=FG_DIM)
                sh.paste(cell, (x, y0))
    p = os.path.join(OUT, u"sheet_待删4件.png")
    sh.save(p, optimize=True)
    return p


# ---------------------------------------------------------------- C
def build_C(data):
    COLS = 2
    GAP = 12
    CW = (SHEET_W - 2 * MARGIN - (COLS - 1) * GAP) // COLS
    CH = 560
    HEAD = 84
    ROWLAB = 40
    H = MARGIN + HEAD + len(data.dup) * (ROWLAB + CH + GAP) + MARGIN
    sh = Image.new("RGB", (SHEET_W, H), BG)
    d = ImageDraw.Draw(sh)
    sheet_header(d,
                 u"C · 同一旧 ID 在用户新清单里出现两次的 4 处（请确认是否为笔误）",
                 u"每处一行两格：两个新 ID 各一格，显示的是同一张代表图 ｜ 两格指向同一旧组，代表图 md5 相同")

    for r, (oid, nids) in enumerate(data.dup):
        y0 = MARGIN + HEAD + r * (ROWLAB + CH + GAP)
        d.text((MARGIN + 4, y0 + 4),
               u"旧 %03d（%s）  ←  新 %s" % (oid, data.name[oid], u" 与 新 ".join(str(x) for x in nids)),
               font=font(26), fill=AMBER)
        for k, nid in enumerate(nids[:COLS]):
            x = MARGIN + k * (CW + GAP)
            draw_cell(sh, x, y0 + ROWLAB, CW, CH,
                      os.path.join(REPDIR, "%03d_%s.png" % (oid, data.name[oid])),
                      u"新 %d" % nid, data.name[oid],
                      [(u"新 ID %d  →  旧 %03d（%s）" % (nid, oid, data.name[oid]), FG),
                       (u"差%d ｜ %s" % (data.n[oid], data.size[oid]), FG_DIM),
                       (u"与同排另一格同一旧组，代表图 md5 相同", GREEN),
                       (data.rep[oid][:16] + u"…", FG_DIM)],
                      460, highlight=AMBER)
    p = os.path.join(OUT, u"sheet_重复4行.png")
    sh.save(p, optimize=True)
    return p


# ---------------------------------------------------------------- TSV
def write_tsv(data, paths):
    p = os.path.join(OUT, u"待确认清单.tsv")
    with io.open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\r\n")
        w.writerow([u"类别", u"旧ID", u"组名", u"差分件数", u"尺寸", u"同图判定", u"疑似孪生", u"备注"])

        for i in data.unmentioned:
            t = data.rep_twin[i]
            if t:
                verdict = u"与 %s 逐字节同图" % u"、".join("%03d" % x for x in t)
                twin = u"、".join("%03d %s" % (x, data.name[x]) for x in t)
            else:
                verdict = u"无同图孪生"
                twin = u"—"
            note = u"用户清单未提及；不在删除清单"
            at = data.any_twin[i]
            if not t and at:
                note += u"；代表图虽无孪生，但差分 %s 与 %s 逐字节同图" % (
                    u"、".join(u for j in at for u, _ in at[j]),
                    u"、".join("%03d %s" % (j, data.name[j]) for j in at))
            w.writerow([u"A", "%03d" % i, data.name[i], data.n[i], data.size[i], verdict, twin, note])

        for i in data.b4:
            cands = data.cands.get(i, [])
            twin = u"；".join(u"%03d %s（%s）" % (j, data.name[j], why) for j, why in cands) or u"无候选"
            w.writerow([u"B", "%03d" % i, data.name[i], data.n[i], data.size[i],
                        u"无同图孪生", twin,
                        u"用户删除清单；段一未出现（删掉该图即消失）"])

        for oid, nids in data.dup:
            w.writerow([u"C", "%03d" % oid, data.name[oid], data.n[oid], data.size[oid],
                        u"两新ID指向同一旧组，代表图 md5 相同",
                        u"新 %s" % u" / 新 ".join(str(x) for x in nids),
                        u"疑为笔误，请用户确认"])

        f.write(u"\r\n".join([u"# 口径：旧ID = 本包（CG候选集 363 组）组序号；同图判定 = 代表图 md5 逐字节相同"]) + u"\r\n")
        f.write(u"# 另注：删除清单 078 e_asu01 / 079 e_asu02 / 095 e_nar01 亦代表图无孪生，"
                u"但它们在段一已被并入（078→新1、079→新2、095→新116），故不计入本次待删 4 件。" + u"\r\n")
        f.write(u"# 生成：" + u"、".join(os.path.basename(x) for x in paths) + u"\r\n")
    return p


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    data = Data()
    print(u"本包组数 %d ｜ 用户新ID %d ｜ 段一提及旧ID %d ｜ 删除清单 %d"
          % (len(data.by), len(data.new2old), len(data.mentioned), len(data.deleted)))
    print(u"A 未提及 %d 件（有孪生 %d / 无 %d）"
          % (len(data.unmentioned), sum(1 for i in data.unmentioned if data.rep_twin[i]),
             sum(1 for i in data.unmentioned if not data.rep_twin[i])))
    print(u"B 待删（段一未出现且无孪生）%d 件: %s"
          % (len(data.b4), [("%03d" % i, data.name[i]) for i in data.b4]))
    print(u"C 重复行 %d 处: %s" % (len(data.dup), [("%03d" % o, n) for o, n in data.dup]))

    # B 的候选：优先「差分逐字节同图」的同画异名件，再取同族近邻
    name2id = {data.name[i]: i for i in data.by}
    data.cands = {}
    for i in data.b4:
        n = data.name[i]
        out = []
        # ① 差分逐字节同图者（最强证据）
        for j in sorted(data.any_twin[i]):
            u = data.any_twin[i][j]
            out.append((j, u"差分 %s 与 %s 逐字节相同" % (u[0][0], u[0][1])))
        # ② 去/加 e_ 前缀同号
        alt = n[2:] if n.startswith("e_") else "e_" + n
        if alt in name2id and name2id[alt] not in [x[0] for x in out]:
            out.append((name2id[alt], u"同号异名（e_ 前缀）"))
        # ③ 同族近邻
        m = re.match(r"^(?:e_)?([a-z]+)(\d+)$", n)
        if m:
            pre = m.group(1)
            for j in sorted(data.by):
                if len(out) >= 3:
                    break
                if j == i or j in [x[0] for x in out]:
                    continue
                if re.match(r"^(?:e_)?%s(\d+)$" % re.escape(pre), data.name[j]):
                    out.append((j, u"同族近邻"))
        data.cands[i] = out[:3]
        print(u"  B %03d %-10s 候选: %s" % (i, n, [("%03d" % j, w) for j, w in data.cands[i]]))

    paths = [build_A(data), build_B(data), build_C(data)]
    for x in paths:
        print(u"-> %s  %s  %.1f MB" % (x, Image.open(x).size, os.path.getsize(x) / 1048576.0))
    print(u"TSV -> %s" % write_tsv(data, paths))


if __name__ == "__main__":
    main()