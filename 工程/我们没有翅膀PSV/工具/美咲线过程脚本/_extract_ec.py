# -*- coding: utf-8 -*-
import os, sys, json
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\pylibs")
MEDIA = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\解密\PCSG00299\media"
OUT   = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\images\eyecatch"
os.chdir(MEDIA)
import cricodecs as C

want = [
  ("CG.cpk",        "EC28.png"),
  ("CG.cpk",        "EC34.png"),
  ("CG.cpk",        "EC35.png"),
  ("CG.cpk",        "EC37.png"),
  ("SystemData.cpk","ec_bg31B.png"),
  ("SystemData.cpk","ec_bg19.png"),
  ("SystemData.cpk","ec_bg19C.png"),
  ("SystemData.cpk","ec_bg15A.png"),
  ("SystemData.cpk","ec_bg39.png"),
  ("SystemData.cpk","ec_bg70.png"),
  ("SystemData.cpk","ec_bg44A.png"),
  ("SystemData.cpk","ec_bg44B.png"),
]
cache = {}
res = []
for cpk, name in want:
    if cpk not in cache:
        cache[cpk] = C.load(cpk)
    c = cache[cpk]
    hit = None
    for i, e in enumerate(c.file_infos()):
        if e.filename == name:
            hit = i; break
    if hit is None:
        print("MISSING", cpk, name); res.append((name, None)); continue
    data = c.file_bytes(hit)
    dst = os.path.join(OUT, name)
    with open(dst, "wb") as fh: fh.write(data)
    res.append((name, len(data)))
    print("OK  %-16s <- %-16s %8d bytes" % (name, cpk, len(data)))
json.dump(res, open(os.path.join(OUT, "_manifest.json"), "w"), indent=1)
