# -*- coding: utf-8 -*-
"""交叉复核：新表 vs 既有 资源组\\演出\\演出_ota.tsv（独立生成器的产物）"""
import io, collections, json, sys
import os

OLD = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\演出\演出_ota.tsv"
# ★ 2026-10-09 订正：本表入库后位于**脚本同目录**（`新源侧\TOB0\`）；旧开发位置
#   （`子代理工作区\ISSUE-20261008-09\TOB0\`）= **历史副本，勿用**（原硬编码旧位置已改为脚本相对路径）。
NEW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "演出新源_ota.tsv")


def load(path):
    with io.open(path, encoding="utf-8") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        rows = [dict(zip(head, ln.rstrip("\r\n").split("\t"))) for ln in f if ln.strip()]
    return head, rows


def main():
    ho, ro = load(OLD)
    hn, rn = load(NEW)
    print("old rows", len(ro), "cols", ho)
    print("new rows", len(rn), "cols", len(hn))

    def trip(rows, opcol, tcol, ops):
        s = set()
        for r in rows:
            if r.get(opcol) in ops:
                s.add((r["scene_id"], r["seq"], r[tcol]))
        return s

    old_tr = trip(ro, "op", "target", {"bg"})
    new_tr = trip(rn, "op", "tgt", {"bg"})
    print("\n[bg]   old triples %d / new %d / old⊆new %s / new-old %d / old-new %d"
          % (len(old_tr), len(new_tr), old_tr <= new_tr, len(new_tr - old_tr), len(old_tr - new_tr)))
    for t in sorted(old_tr - new_tr)[:10]:
        print("   old-not-in-new:", t)

    old_se = trip(ro, "op", "target", {"se"})
    new_se = trip(rn, "op", "tgt", {"se"})
    print("[se]   old %d / new %d / old⊆new %s / new-old %d / old-new %d"
          % (len(old_se), len(new_se), old_se <= new_se, len(new_se - old_se), len(old_se - new_se)))
    for t in sorted(old_se - new_se)[:10]:
        print("   old-not-in-new:", t)

    old_ch = trip(ro, "op", "target", {"chr_add", "chr_expr"})
    new_ch = trip(rn, "op", "tgt", {"chr_add"})
    print("[chr]  old %d / new(chr_add) %d / old⊆new %s / old-new %d"
          % (len(old_ch), len(new_ch), old_ch <= new_ch, len(old_ch - new_ch)))
    for t in sorted(old_ch - new_ch)[:10]:
        print("   old-not-in-new:", t)

    # 新表槽位/参数统计
    slot = collections.Counter(r["slot"] for r in rn if r["slot"])
    print("\nslot 填充:", dict(slot))
    pok = collections.Counter(r["param_ok"] for r in rn)
    print("param_ok:", dict(pok))
    print("dul_ms 非空:", sum(1 for r in rn if r["dur_ms"]))
    print("x_src 非空:", sum(1 for r in rn if r["x_src"]))
    print("slot 非空:", sum(1 for r in rn if r["slot"]))
    print("layer 非空:", sum(1 for r in rn if r["layer"]))
    print("x/y 非空:", sum(1 for r in rn if r["x"] or r["y"]))
    # ref_missing
    print("ref_missing 行:", sum(1 for r in rn if "ref_missing" in r["evidence"]))


if __name__ == "__main__":
    main()
