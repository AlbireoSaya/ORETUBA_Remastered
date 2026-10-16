# -*- coding: utf-8 -*-
import json, glob, os, collections

ROOT = r"E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
SCREENS = os.path.join(ROOT, "layout", "screens")
ASSETS = os.path.join(ROOT, "krkr", "assets", "ui")
OUT = os.path.join(ROOT, "_工作", "M34_资产引用矩阵.tsv")

def norm(s):
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    if s.startswith("ui/"):
        s = s[3:]
    # only keep if looks like a file
    return s

# collect refs: filename -> list of (screen, elem_id, kind, field)
refs = collections.defaultdict(list)
screens = sorted(glob.glob(os.path.join(SCREENS, "*.json")))
for f in screens:
    base = os.path.basename(f)
    if base == "_index.json":
        continue
    d = json.load(open(f, encoding="utf-8"))
    sid = d.get("id", base)
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "asset" and isinstance(v, str):
                    n = norm(v)
                    if n: refs[n].append((sid, path, k))
                elif k == "asset_frames" and isinstance(v, list):
                    for it in v:
                        n = norm(it)
                        if n: refs[n].append((sid, path, k))
                elif k == "state_assets" and isinstance(v, dict):
                    for st, it in v.items():
                        n = norm(it)
                        if n: refs[n].append((sid, path, k+":"+st))
                elif k == "item_frame" and isinstance(v, dict) and isinstance(v.get("asset"), str):
                    n = norm(v["asset"])
                    if n: refs[n].append((sid, path, "item_frame.asset"))
                else:
                    walk(v, path)
        elif isinstance(obj, list):
            for it in obj:
                walk(it, path)
    # bg
    bg = d.get("bg")
    if isinstance(bg, dict) and isinstance(bg.get("asset"), str):
        n = norm(bg["asset"])
        if n: refs[n].append((sid, "bg", "bg.asset"))
    for el in d.get("elements", []):
        walk(el, el.get("id", "?"))

# physical files
phys = {}
for fn in os.listdir(ASSETS):
    p = os.path.join(ASSETS, fn)
    if os.path.isfile(p):
        phys[fn] = os.path.getsize(p)

# write TSV
with open(OUT, "w", encoding="utf-8") as w:
    w.write("素材文件名\t体积(bytes)\t引用屏数\t引用屏\t引用元素(屏/元素id/字段)\n")
    for fn in sorted(phys):
        rs = refs.get(fn, [])
        scs = sorted(set(r[0] for r in rs))
        det = "; ".join("%s/%s/%s" % r for r in rs)
        w.write("%s\t%d\t%d\t%s\t%s\n" % (fn, phys[fn], len(scs), ",".join(scs), det))

# summary
print("TOTAL_PHYS", len(phys), "TOTAL_BYTES", sum(phys.values()))
print("REFERENCED_FILES", len(refs))
missing = [k for k in refs if k not in phys]
print("MISSING(引用但文件不存在):", missing)
unused = [k for k in phys if k not in refs]
print("UNREFERENCED(count)", len(unused))
# refs pointing to non-ui files
weird = [k for k in refs if k not in phys]
print("WEIRD", weird)
