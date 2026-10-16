# -*- coding: utf-8 -*-
"""D12：核对「layout/screens/35_quickbar.json」是否与生成器 m34_build_screens.build_quickbar() 一致。
做法：import 生成器（其 __main__ 有 guard，import 不写盘），把模块内的 write() 换成内存捕获，
再调 build_quickbar()。绝不落盘。"""
import io, json, os, sys, importlib.util

TOOLS = r"E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/工具"
SCR = os.path.join(os.path.dirname(TOOLS), "layout", "screens")
sys.path.insert(0, TOOLS)
spec = importlib.util.spec_from_file_location("m34b", os.path.join(TOOLS, "m34_build_screens.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

captured = {}
m.write = lambda name, sid, title, note, els, extra=None: captured.update(
    {"name": name, "doc": {"id": sid, "title_cn": title, "owner": "M34", "note": note,
                           "elements": els, **(extra or {})}})

m.build_quickbar()
gen = captured["doc"]
disk = json.load(io.open(os.path.join(SCR, "35_quickbar.json"), encoding="utf-8"))

print("生成器产出：%s  元素 %d 件" % (captured["name"], len(gen["elements"])))
print("磁盘文件：  35_quickbar.json  元素 %d 件" % len(disk["elements"]))
print("磁盘顶层键：", sorted(disk.keys()))
print("生成器顶层键：", sorted(gen.keys()))


def norm(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


same_all = norm(gen) == norm(disk)
print("\n整体一致（含 note 全文）:", same_all)
if not same_all:
    # 逐字段定位差异
    for k in sorted(set(list(gen.keys()) + list(disk.keys()))):
        if norm(gen.get(k)) == norm(disk.get(k)):
            continue
        print("  顶层键差异 [%s]" % k)
        if k == "note":
            g, d = gen.get(k) or "", disk.get(k) or ""
            print("    生成器 note 长度 %d / 磁盘 note 长度 %d" % (len(g), len(d)))
            import difflib
            for line in difflib.unified_diff([g], [d], lineterm="", n=0):
                print("    ", line[:400])
        elif k == "elements":
            ge = {e["id"]: e for e in gen[k]}
            de = {e["id"]: e for e in disk[k]}
            print("    仅在生成器:", sorted(set(ge) - set(de)))
            print("    仅在磁盘 :", sorted(set(de) - set(ge)))
            for eid in sorted(set(ge) & set(de)):
                if norm(ge[eid]) != norm(de[eid]):
                    fk = sorted(set(list(ge[eid].keys()) + list(de[eid].keys())))
                    diff = [f for f in fk if norm(ge[eid].get(f)) != norm(de[eid].get(f))]
                    print("      %-22s 差异字段: %s" % (eid, diff))
        else:
            print("    生成器:", str(gen.get(k))[:200])
            print("    磁盘  :", str(disk.get(k))[:200])

# 关键新字段是否在生成器里有代码
for f in ("flags_default", "reveal", "vis_flag", "vis_when"):
    print("生成器源码含 %-14s : %s" % (f, f in io.open(os.path.join(TOOLS, "m34_build_screens.py"), encoding="utf-8").read()))
