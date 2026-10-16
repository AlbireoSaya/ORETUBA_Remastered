# -*- coding: utf-8 -*-
"""M3 只读探针 1：PSV 金标「效果/转场类 Tasktype」的列填充画像。

目的：对每个效果/转场类 `:Tasktype`，看清**哪些列有值**、值域与分布，
作为「PC 实参位 → 语义」对拍的**金标字段清单**。
只读 `时间线.tsv`；不写任何产物（由调用方重定向 stdout）。
"""
import csv, io, os, sys, collections

T = os.environ.get("PSV_TIMELINE",
    r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\PSV演出\时间线.tsv")

EFFECT_TYPES = [
    "EffectQuake", "EffectQuakeEnd", "EffectStart", "EffectEnd", "SpriteQuake",
    "InOut", "InOut_Act", "Flash", "Window",
    "EyeCatch", "EyeCatchEnd",
    "FadeIn", "FadeOut",
    "Tag", "Jump_Tag", "FlagSwitch_Tag", "MessageSwitch_Tag",
    "GlobalFlagSwitch_Tag", "GlobalFlagOperation", "FlagOperation",
    "TimeWait", "SceneJumpDialog", "SceneJumpDialogEnd",
    "NextScene", "End", "Achievement", "SetSceneName",
    "SpriteMove", "SpriteMoveEnd", "SpriteDelete", "SpriteDeleteBG",
    "SpriteBS", "Sprite", "SpriteBG", "SpritePriority",
    "MoviePlay", "MovieStop", "CharacterStop",
    "BacklogMessage",
]
# 有实义参数的列（其余列恒空/无关）
FIELDS = ["x", "y", "cx", "cy", "cpri", "priority", "time", "rule", "fade",
          "name", "kind", "layer", "op", "se", "bgm", "voice", "image", "movie",
          "nameid", "msg_ord"]


def main():
    rows = list(csv.DictReader(io.open(T, encoding="utf-8"), delimiter="\t"))
    by = collections.defaultdict(list)
    for r in rows:
        by[r["type"]].append(r)
    print("== PSV 列填充画像（仅效果/转场类 type）==")
    print("总行 %d ｜ 类型 %d" % (len(rows), len(by)))
    for t in EFFECT_TYPES:
        rs = by.get(t)
        if not rs:
            print("\n### %-22s (无行)" % t)
            continue
        print("\n### %-22s 行=%d" % (t, len(rs)))
        for f in FIELDS:
            vals = [r.get(f, "") for r in rs]
            nz = [v for v in vals if v != ""]
            if not nz:
                continue
            c = collections.Counter(nz)
            top = c.most_common(6)
            nums = []
            for v in nz:
                try:
                    nums.append(int(v))
                except ValueError:
                    pass
            rng = ""
            if nums:
                rng = " 值域[%d,%d]" % (min(nums), max(nums))
            print("   %-9s 非空 %4d/%4d%s  top=%s" % (f, len(nz), len(rs), rng, top))


if __name__ == "__main__":
    main()
