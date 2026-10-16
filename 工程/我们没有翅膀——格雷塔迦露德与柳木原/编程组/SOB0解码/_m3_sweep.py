# -*- coding: utf-8 -*-
"""M3 只读探针 7：全目标 V × 全实参位 × 全字段 × 变换 的命中率扫描。

只打印「有判别力的候选」（非零口径 seq/scene ≥ 阈值 或 exact 高）。
用法：python -X utf8 _m3_sweep.py --src ot [--min 0.30]
"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _m3_hitrate as H

TARGET = {
    0x1B888: ("Flash", {"Flash"}),
    0x1B69C: ("EffectQuake", {"EffectQuake", "SpriteQuake"}),
    0x19D58: ("EffectQuakeEnd", {"EffectQuakeEnd", "EffectEnd"}),
    0x1C330: ("EffectQuakeEnd*", {"EffectQuakeEnd"}),
    0x1BD8C: ("EffectQuake*", {"EffectQuake", "SpriteQuake"}),
    0xEFF0: ("?quake", {"EffectQuake"}),
    0x7480: ("Window", {"Window"}),
    0x1B040: ("InOut_Act", {"InOut_Act", "InOut"}),
    0x186C8: ("sp_move", {"SpriteMove", "SpriteBS", "Sprite"}),
    0x10150: ("bg_move", {"SpriteMove", "SpriteBS", "Sprite"}),
    0x1AD18: ("EyeCatch/End", {"EyeCatch", "EyeCatchEnd"}),
    0x1C8D0: ("SceneTitle", {"SetSceneName"}),
    0x11784: ("EffectStart?", {"EffectStart"}),
    0x11B0C: ("EffectStart*", {"EffectStart"}),
}
FIELDS = ["time", "rule", "fade", "priority", "cpri", "cx", "cy", "x", "y"]
TFS = ["ms", "id", "ms2"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="ot")
    ap.add_argument("--min", type=float, default=0.30)
    a = ap.parse_args()
    for V, (name, types) in sorted(TARGET.items()):
        rows = []
        for pos in range(12):
            for fld in FIELDS:
                for tf in TFS:
                    r = H.compute(a.src, V, pos, fld, tf, types)
                    if r["nseq"][1] < 5:
                        continue
                    nseq = r["nseq"][0] / r["nseq"][1]
                    nsc = r["nscene"][0] / r["nscene"][1]
                    nex = (r["nexact"][0] / r["nexact"][1]) if r["nexact"][1] else 0
                    if max(nseq, nsc, nex) >= a.min and max(nseq, nsc) > r["base"] * 0.8:
                        rows.append((max(nsc, nseq), pos, fld, tf, r["nseq"][1], nex,
                                     r["nexact"][1], nseq, nsc, r["base"]))
        rows.sort(reverse=True)
        print("\n=== V=0x%X %s  节点 %d ===" % (V, name, H.compute(a.src, V, 0, "time", "id", types)["nodes"]))
        if not rows:
            print("   （无非零判据达阈的位）")
        for t in rows[:10]:
            print("   pos%-2d %-8s %-3s 非零n=%-4d exact=%d/%d  seq=%.3f scene=%.3f base=%.3f" %
                  (t[1], t[2], t[3], t[4], int(t[5] * t[6] + 0.5), t[6], t[7], t[8], t[9]))


if __name__ == "__main__":
    main()
