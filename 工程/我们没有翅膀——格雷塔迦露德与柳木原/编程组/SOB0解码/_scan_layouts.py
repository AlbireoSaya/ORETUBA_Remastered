# -*- coding: utf-8 -*-
"""_scan_layouts.py — 只读探针：扫描各源命令节点里「含控制串/含 chr 名」的 (V,argc,argkinds) 形态。"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "工具"))
sys.dont_write_bytecode = True
import decode_sob0 as D  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "..", "资源组", "工具"))
import _staging_common as SC  # noqa: E402

ctrl_b = D.CTRL_BYTES
ctrl_txt = D.CTRL_STRINGS


def main():
    ledger = D.Ledger(D.LEDGER)
    fam = SC.ArtFamilies.load()
    for src in ("ot", "otp", "otr"):
        spec = D.SOURCES[src]
        scene_path = os.path.join(D.SCENE_DIR, spec["scene"])
        lay = collections.Counter()
        chrn = collections.Counter()
        nscene = 0
        with io.open(scene_path, encoding="utf-8") as f:
            for line in f:
                o = json.loads(line)
                script = o["script"]
                if spec["prefix"] and not script.lower().startswith(spec["prefix"]):
                    continue
                p = os.path.join(spec["dir"], script + spec["ext"])
                if not os.path.isfile(p):
                    continue
                try:
                    sob = D.Sob0(p)
                except ValueError:
                    continue
                nscene += 1
                for i in sob.command_nodes():
                    V = sob.cells[i + 1]
                    args = sob.node_args(i)
                    kinds = "".join(k for k, _ in args)
                    has_ctrl = any(k == "S" and (v or "").encode("cp932", "replace") in ctrl_b
                                   or (k == "S" and D.COORD_RE.match(v or ""))
                                   for k, v in args)
                    if has_ctrl:
                        lay[(V, len(args), kinds)] += 1
                    # chr 名 token（S 值能在 chr 账里命中 或符合差分令牌形态）
                    for idx, (k, v) in enumerate(args):
                        if k != "S":
                            continue
                        tgt = ledger.target("chr", SC.os.path.splitext(SC.os.path.basename(
                            (v or "").upper()))[0], src) if False else None
                        f = SC.family_of(v) if v else None
                        if f:
                            chrn[(V, len(args), idx, kinds)] += 1
                            break
        print("=== %s (scenes=%d) ===" % (src, nscene))
        print("-- ctrl-bearing node layouts (V,argc,argkinds) --")
        for (V, argc, kinds), n in lay.most_common(30):
            print("   V=0x%X argc=%d kinds=%s n=%d" % (V, argc, kinds, n))
        print("-- chr-name-bearing node layouts (V,argc,idx,argkinds) --")
        for (V, argc, idx, kinds), n in chrn.most_common(30):
            print("   V=0x%X argc=%d nameIdx=%d kinds=%s n=%d" % (V, argc, idx, kinds, n))


if __name__ == "__main__":
    main()
