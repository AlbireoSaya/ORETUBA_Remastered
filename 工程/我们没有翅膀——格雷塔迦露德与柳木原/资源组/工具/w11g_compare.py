# -*- coding: utf-8 -*-
"""W11g · 38 组候选的客观比对：md5 / 亮度 / 两两 MAD（拉伸到 96x96 后的平均绝对差）。
用于佐证目视终裁，不替代目视。只读，print 摘要。"""
import os, re, json, hashlib, sys
from PIL import Image, ImageChops, ImageStat

sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
SRC = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g"))
assert WORK.startswith(r"E:\ZCode Workspace\Galgame")
PREF = {"CG背景": ["pic", "chr", "sys", "etc"], "系统UI": ["sys", "etc", "pic", "chr"]}


def find_cand(src, fname, cat):
    root = os.path.join(SRC, src)
    for sub in PREF.get(cat, []):
        p = os.path.join(root, sub, fname)
        if os.path.isfile(p):
            return p
    for dp, dn, fn in os.walk(root):
        if fname in fn:
            return os.path.join(dp, fname)
    return None


def load_rgb(p):
    im = Image.open(p)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg.convert("RGB")
    else:
        im = im.convert("RGB")
    return im


def main():
    gs = json.load(open(os.path.join(WORK, "_38组清单.json"), encoding="utf-8"))
    out = {}
    for g in gs:
        cat, name, cands = g["类别"], g["统一名"], g["候选"]
        items = []
        for it in [c.strip() for c in cands.split(";")]:
            m = re.match(r"(\w+):(\S+)\s+(\d+)x(\d+)\s+ar=([\d.]+)", it)
            if m:
                items.append((m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), float(m.group(5))))
        info = []
        smalls = []
        for src, fname, w, h, ar in items:
            p = find_cand(src, fname, cat)
            md5 = hashlib.md5(open(p, "rb").read()).hexdigest()[:8] if p else "-"
            im = load_rgb(p)
            st = ImageStat.Stat(im)
            bright = sum(st.mean) / 3
            smalls.append((src + ":" + fname, im.resize((96, 96), Image.BILINEAR)))
            info.append((src, fname, w, h, ar, md5, round(bright, 1)))
        print("\n### %s / %s  (n=%d)" % (cat, name, len(items)))
        for src, fname, w, h, ar, md5, br in info:
            print("   %-4s %-22s %5dx%-5d ar=%-8.4f md5=%s 亮度=%.1f" % (src, fname, w, h, ar, md5, br))
        # 两两 MAD
        for i in range(len(smalls)):
            for j in range(i + 1, len(smalls)):
                d = ImageChops.difference(smalls[i][1], smalls[j][1])
                mad = sum(ImageStat.Stat(d).mean) / 3
                print("   MAD(%s , %s) = %.1f" % (smalls[i][0], smalls[j][0], mad))
        out[name] = {"info": info, "n": len(items)}
    p = os.path.join(WORK, "_compare.json")
    tmp = p + ".tmp"
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)


if __name__ == "__main__":
    main()