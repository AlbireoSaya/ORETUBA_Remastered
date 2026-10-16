# -*- coding: utf-8 -*-
"""
W11f · 全源图像元数据缓存（含 alpha 内容 bbox / 覆盖率）
=========================================================
用途：为 W11f 的「新度量（内容面积）复核」与「撞名全量扫描」提供统一、可复跑的
      元数据基础。**只读源**，缓存只写 子代理工作区\\ISSUE-20260918-06\\W11f\\。

输出：<WORK>\\_meta_cache.json
  { "<src>|<kind>|<fn>": {src,kind,name,w,h,mode,bytes,md5,bbox:[x0,y0,x1,y1],
                          cov:覆盖率(alpha>0 占比), has_alpha:bool, opaque:bool} }

内容 bbox 定义（规格 §3.2）：
  - 图像含有效 alpha（RGBA/LA/P+tRNS/PA）→ alpha>0 像素的外接矩形
  - 否则（RGB/L 无 alpha）→ bbox == 画布 (0,0,w,h)，即不透明图
"""
import os, sys, json, hashlib, time

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
LIB = os.path.join(PROJ, "资源组", "krkr素材库")
WORK = os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11f")
WORK = os.path.abspath(WORK)
assert WORK.startswith(r"E:\ZCode Workspace\Galgame"), "写入边界越界: " + WORK
CACHE = os.path.join(WORK, "_meta_cache.json")

SRCS = ["ot", "ota", "otp", "otr", "otv", "np"]
# (kind, 子目录)
LAYOUT = [("chr", "chr"), ("pic", "pic"), ("sys", "sys"), ("etc", "etc")]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def meta_one(p):
    from PIL import Image
    with Image.open(p) as im:
        w, h = im.size
        mode = im.mode
        has_alpha = mode in ("RGBA", "LA", "PA", "P")
        if has_alpha:
            a = im.convert("RGBA").getchannel("A")
            bb = a.getbbox()
            hist = a.histogram()
            tot = w * h
            cov = (tot - hist[0]) / tot if tot else 0.0
            if bb is None:
                bb = (0, 0, w, h)
            # 若 alpha 全 255（含 P 无透明）→ 视为不透明
            if cov >= 0.999999:
                bb = (0, 0, w, h)
                has_alpha = False
        else:
            bb = (0, 0, w, h)
            cov = 1.0
            has_alpha = False
    return dict(w=w, h=h, mode=mode, bytes=os.path.getsize(p), md5=md5_file(p),
                bbox=list(bb), cov=round(cov, 6), has_alpha=has_alpha)


def main():
    os.makedirs(WORK, exist_ok=True)
    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    t0 = time.time()
    n_new = 0
    for src in SRCS:
        for kind, sub in LAYOUT:
            d = os.path.join(LIB, src, sub)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.lower().endswith(".png"):
                    continue
                key = "%s|%s|%s" % (src, kind, fn)
                p = os.path.join(d, fn)
                if key in cache and cache[key].get("bytes") == os.path.getsize(p):
                    continue
                m = meta_one(p)
                m.update(src=src, kind=kind, name=fn, path=p)
                cache[key] = m
                n_new += 1
    # 清理已不存在的
    for k in list(cache):
        if not os.path.exists(cache[k]["path"]):
            del cache[k]
    with open(CACHE + ".tmp", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(CACHE + ".tmp", CACHE)
    from collections import Counter
    print("cache entries:", len(cache), "new:", n_new, "elapsed %.1fs" % (time.time() - t0))
    print("by src/kind:", dict(Counter("%s/%s" % (v["src"], v["kind"]) for v in cache.values())))


if __name__ == "__main__":
    main()