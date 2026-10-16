# -*- coding: utf-8 -*-
"""M3 交付生成器：效果/转场类命令「参数位 -> 语义」表 + 未解清单（TSV）。

输出（默认写到 子代理工作区/ISSUE-20261008-04/M3/）：
  效果类参数_位表.tsv     逐 (V,实参位) 一行：语义 / 证据类别 / 命中率 / 覆盖
  效果类参数_未解清单.tsv 未解位与「缺什么证据」
可复跑：python -X utf8 _m3_emit.py --out <dir>
"""
import os, sys, io, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _m3_hitrate as H

# 规格表：src, V, 名称, argc, pos, 语义, 证据类别, 对拍字段, 变换, 期望type, 覆盖口径
# 证据类别：PSV旁证 = 有 PSV 金标字段对拍；PC自证 = 只有源侧值分布/串（无金标字段）
# 覆盖口径：nz=非默认值口径；all=全部节点
SPEC = [
    # ---- 已解出（PSV 旁证：时长）----
    ("ot", 0x1B69C, "EffectQuake", 6, 5, "时长(毫秒)", "PSV旁证", "time", "ms",
     {"EffectQuake", "SpriteQuake"}, "nz"),
    ("otr", 0x1B69C, "EffectQuake", 6, 5, "时长(毫秒)", "PSV旁证", "time", "ms",
     {"EffectQuake", "SpriteQuake"}, "nz"),
    ("ot", 0x1B040, "InOut_Act", 5, 3, "时长(毫秒)", "PSV旁证", "time", "ms",
     {"InOut_Act", "InOut"}, "nz"),
    ("otr", 0x1B040, "InOut_Act", 5, 3, "时长(毫秒)", "PSV旁证", "time", "ms",
     {"InOut_Act", "InOut"}, "nz"),
    ("ot", 0x1AEA0, "?(InOut_Act 第二载体)", 3, 2, "时长(毫秒)", "PSV旁证", "time", "ms",
     {"InOut_Act"}, "nz"),
    ("ot", 0x1A96C, "?(InOut／现名 rule_in)", 3, 2, "时长(毫秒)", "PSV旁证", "time", "ms",
     {"InOut"}, "nz"),
    # ---- 时长位「反面」（自证能失败）----
    ("ot", 0x1B69C, "EffectQuake", 6, 4, "【变异对照】邻位非时长", "PSV旁证", "time", "ms",
     {"EffectQuake", "SpriteQuake"}, "nz"),
    ("ot", 0x1B040, "InOut_Act", 5, 2, "【变异对照】邻位非时长", "PSV旁证", "time", "ms",
     {"InOut_Act", "InOut"}, "nz"),
    # ---- PC 自证（无金标字段）----
    ("ot", 0x1B888, "Flash", 2, 0, "强度/时长(未定；PSV无字段)", "PC自证", "time", "ms",
     {"Flash"}, "nz"),
    ("ot", 0x1B888, "Flash", 2, 1, "颜色 RGB(0xRRGGBB)", "PC自证", "time", "ms",
     {"Flash"}, "nz"),
    ("ot", 0x1B69C, "EffectQuake", 6, 3, "振幅 x（默认30）", "PC自证", "time", "ms",
     {"EffectQuake", "SpriteQuake"}, "nz"),
    ("ot", 0x1B69C, "EffectQuake", 6, 4, "振幅 y（默认30）", "PC自证", "time", "ms",
     {"EffectQuake", "SpriteQuake"}, "nz"),
    ("ot", 0x1B040, "InOut_Act", 5, 4, "类型/图案选择子（0..6）", "PC自证", "time", "ms",
     {"InOut_Act", "InOut"}, "nz"),
    ("ot", 0x10150, "bg_move", 2, 1, "方向 token（串 l/r/d/u/c）", "PC自证", "time", "ms",
     {"SpriteMove", "SpriteBS", "Sprite"}, "nz"),
    ("ot", 0x186C8, "sp_move", 3, 1, "控制串（l<2/r>2/b l<2）", "PC自证", "time", "ms",
     {"SpriteMove", "SpriteBS", "Sprite"}, "nz"),
    ("ot", 0xFDF4, "bg_zoom", 4, 1, "缩放倍率（串 2/1.5/2.5/3/4/10）", "PC自证", "time", "ms",
     {"SpriteMove"}, "nz"),
    ("ot", 0xFDF4, "bg_zoom", 4, 2, "目标宽/矩形 w", "PC自证", "time", "ms", {"SpriteMove"}, "nz"),
    ("ot", 0xFDF4, "bg_zoom", 4, 3, "目标高/矩形 h", "PC自证", "time", "ms", {"SpriteMove"}, "nz"),
    ("ot", 0x13300, "bg_blur", 5, 1, "模式（串 \"0\"）", "PC自证", "time", "ms", {"SpriteMove"}, "nz"),
    ("ot", 0x13300, "bg_blur", 5, 2, "模糊量（串 1.5/2/3/4）", "PC自证", "time", "ms", {"SpriteMove"}, "nz"),
    ("ot", 0x2A150, "cross", 5, 3, "时长候选(ms，仅系统脚本)", "PC自证", "time", "ms", set(), "nz"),
    ("ot", 0x1AD18, "EyeCatch/End", 5, 4, "卡面路径 PIC\\EC*.ELG", "PC自证", "image", "id",
     {"EyeCatch", "EyeCatchEnd"}, "nz"),
]

# 未解清单：V, pos, 名称, 说明（卡在哪）
UNRESOLVED = [
    (0x1B888, -1, "Flash", "pos0 强度/时长语义未定：PSV Flash 行 **无任何参数列**（time 0/461），无金标字段可对"),
    (0x1B69C, 0, "EffectQuake", "pos0 恒 1（const）——语义未定"),
    (0x1B69C, 1, "EffectQuake", "pos1 串 '0'/'1'——语义未定（无金标字段）"),
    (0x1B69C, 2, "EffectQuake", "pos2 恒 0（const）——语义未定"),
    (0x7480, 0, "Window", "pos0 恒 0（300 仅 1 例）——无携带信息；PSV Window time 仅 20/1559 行"),
    (0x7480, 1, "Window", "pos1 恒 0（1 仅 4 例）——无携带信息"),
    (0x1B040, 0, "InOut_Act", "pos0 ∈{0,768,2048}——疑似位掩码/效果选择，无金标字段"),
    (0x1B040, 1, "InOut_Act", "pos1 ∈{0,64,550,32,200,128…}——疑似位掩码，无金标字段"),
    (0x1B040, 2, "InOut_Act", "pos2 ∈{0..3}——无金标字段"),
    (0x1B040, 4, "InOut_Act", "pos4 ∈{0..6}——类型选择子语义未定"),
    (0x1A96C, 0, "?(rule_in/InOut)", "pos0 ∈{0,500,300,120…} 的**第二个时长样值集**——In/Out 两段之一？未裁"),
    (0x1A96C, 1, "?(rule_in/InOut)", "pos1 ∈{0xFFFFFFFF,40,41,47,48,65}——位掩码/串常量？未定"),
    (0x1AEA0, 0, "?(InOut_Act)", "pos0 恒 2（const）"),
    (0x1AEA0, 1, "?(InOut_Act)", "pos1 ∈{0,2}——未定"),
    (0xFDF4, 0, "bg_zoom", "pos0 恒 1（const）"),
    (0x13300, 0, "bg_blur", "pos0 恒 1（const）"),
    (0x13300, 3, "bg_blur", "pos3/pos4 语义未定（疑 w/h，无金标）"),
    (0x13300, 4, "bg_blur", "pos3/pos4 语义未定（疑 w/h，无金标）"),
    (0x186C8, 0, "sp_move", "pos0 ∈{1,0,300}——未定"),
    (0x186C8, 2, "sp_move", "pos2 ∈{0..5}——疑槽位，无金标"),
    (0x10150, 0, "bg_move", "pos0 恒 1（const）"),
    (0x2A150, 1, "cross", "pos1 = 代码引用(C)/0——回调地址，无金标"),
    (0x2A150, 2, "cross", "pos2 ∈{0,32,35}——未定"),
    (0x2A150, 4, "cross", "pos4 ∈{0,8,2}——未定"),
    (0x19D58, -1, "EffectQuakeEnd", "argc=2，pos0/pos1 恒 0/1——**无参数**；PSV EffectQuakeEnd 亦无参数列"),
    (0x1C8D0, -1, "SceneTitle", "argc=1，pos0 = 场标题串（PC自证；PSV SetSceneName 仅 24 行，无法对拍）"),
]


def f2(pair):
    return "%s/%s=%s" % (pair[0], pair[1], ("%.3f" % (pair[0] / pair[1])) if pair[1] else "-")


HEADER = ["src", "V", "name", "argc", "pos", "semantics", "evidence", "field",
          "transform", "expect_types", "coverage", "n_nodes_default",
          "exact", "seq", "scene", "base", "values", "note"]

# PC 自证（无金标字段）行的源侧值域/串集合——这些行不填命中率（填 `-`）
VALUES = {
    ("ot", 0x1B888, 0): "N 值域[50,800] top=100(464/524),200(49),50(6)",
    ("ot", 0x1B888, 1): "N 颜色 RGB top=0xFFFFFF(463),0x6C22AD(44),0x1E43,0xDAA020,0xD70DB5,0",
    ("ot", 0x1B69C, 3): "N 值域[0,50] top=30(574),20(118),0(65),10(65),50(56)",
    ("ot", 0x1B69C, 4): "N 值域[0,80] top=30(543),0(139),20(117),10(70),50(55)",
    ("ot", 0x1B040, 4): "N 值域[0,6] top=6(114),1(45),3(44),2(18),0(12)",
    ("ot", 0x10150, 1): "S 集合 l(82),d(65),r(60),u(19),c(18),-16(4)",
    ("ot", 0x186C8, 1): "S 集合 l<2(94),r>2(88),b l<2(46),b r>2(46),<2(8),>2(8)",
    ("ot", 0xFDF4, 1): "S 集合 2(10),1.5(4),3(4),2.5(2),4(2),10(2)",
    ("ot", 0xFDF4, 2): "N 值域[0,600] top=300(8),200(4),600(2),120(2),250(2)",
    ("ot", 0xFDF4, 3): "N 值域[120,800] top=400(7),800(4),380(3),240(3),340(3)",
    ("ot", 0x13300, 1): "S 集合 0(12)",
    ("ot", 0x13300, 2): "S 集合 2(6),3(3),1.5(2),4(1)",
    ("ot", 0x13300, 3): "N 值域[100,400] top=100(7),200(2),400(2),300(1)",
    ("ot", 0x13300, 4): "N 值域[100,400] top=400(7),300(2),200(2),100(1)",
    ("ot", 0x2A150, 3): "N 值域[8,1200] top=8(8),750(5),1200(5),600(2),400(1)（仅系统脚本）",
    ("ot", 0x1AD18, 4): "S 路径 PIC\\EC28.ELG(543),EC27(2),EC29(2),EC08(2)…",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-04\M3")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for src, V, name, argc, pos, sem, ev, fld, tf, types, cov in SPEC:
        vals = VALUES.get((src, V, pos), "")
        if ev == "PC自证":
            # 无金标字段：不填命中率，只给源侧值域/串集合
            rows.append([src, "0x%X" % V, name, argc, pos, sem, ev, "-", "-",
                         "-", cov, "-", "-", "-", "-", "-", vals,
                         "PC自证：无金标字段可对"])
            continue
        r = H.compute(src, V, pos, fld, tf, types)
        if cov == "nz":
            ex, sq, sc, n = r["nexact"], r["nseq"], r["nscene"], r["nseq"][1]
        else:
            ex, sq, sc, n = r["exact"], r["seq"], r["scene"], r["seq"][1]
        note = ""
        if r["nodes"] == 0:
            note = "本语料无节点"
        elif r["nseq"][1] == 0:
            note = "无可用对拍样本"
        rows.append([src, "0x%X" % V, name, argc, pos, sem, ev, fld, tf,
                     "+".join(sorted(types)) if types else "ALL", cov, n,
                     f2(ex), f2(sq), f2(sc), "%.3f" % r["base"], vals, note])
    p1 = os.path.join(a.out, "效果类参数_位表.tsv")
    with io.open(p1, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(HEADER) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    p2 = os.path.join(a.out, "效果类参数_未解清单.tsv")
    with io.open(p2, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(["V", "pos", "name", "卡在哪（缺什么证据）"]) + "\n")
        for V, pos, name, why in UNRESOLVED:
            f.write("0x%X\t%s\t%s\t%s\n" % (V, pos, name, why))
    print("写入:\n  %s\n  %s" % (p1, p2))
    for r in rows:
        print("  %-4s %-8s p%-2s %-28s %-8s %s" % (r[0], r[1], r[4], r[5], r[6], r[12]))


if __name__ == "__main__":
    main()
