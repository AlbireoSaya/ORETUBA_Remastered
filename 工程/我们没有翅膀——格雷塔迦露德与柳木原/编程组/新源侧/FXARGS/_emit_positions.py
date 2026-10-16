#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_emit_positions.py —— 生成 `效果族参数位.tsv` + `效果族参数位_未证.tsv`。

数据来源（全部**运行时计算**，不手抄）：
  * 读位       ← `_probe_frame_args.analyse()`（帧口径：i = (X - d - 8)/4）
  * argc/值域  ← `_probe_corpus_argc.scan()`（全库 412 文件，项目自带解码器）
  * 剧情值域   ← `_probe_value_stats`（解出_{ot,otr}.tsv，括号感知切分）
  * PSV 对拍   ← `_probe_psv_join.join()`（时间线.tsv，六口径含置换基线）

来源分档（**写死**，`_verify_positions.py` 会逐条校验）：
  * `PSV对拍` —— 金标字段证实语义（本批只有「时长(ms)」一类）：
                门槛 = exact ≥ 0.90 且 样本 ≥ 10（非退化口径），或 seq ≥ 0.90 且样本 ≥ 20；
                且相对**置换基线**增益 ≥ 0.15。
  * `PC自证` —— 源侧**直证**（不依赖金标）：
                ① 控制流角色（TABJMP 索引）；② 值域为**常量**（去重 1 ⇒ 无信息）；
                ③ 值为**已知控制 token**（方向串）；④ 值为**素材路径**。
  * `未证`   —— 其余一切，**含「值域像 X」（颜色/倍率/振幅/坐标/w-h/位掩码/槽号）与「仅被转发」**。
                `语义` 列只在未证行写「未证（…）」并要求 来源=未证（互斥由校验脚本强制）。

复跑（只读，写出本脚本同目录的两个 TSV）：
  python -X utf8 _emit_positions.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _probe_frame_args as FA          # noqa: E402
import _probe_corpus_argc as CA         # noqa: E402
import _probe_value_stats as VS         # noqa: E402
import _probe_psv_join as PJ            # noqa: E402

# ---- 目标（V, 既有定名标签；标签来自 标签表/M3/decode，只作阅读锚点）---------
TARGETS = [("0x1B888", "Flash"),
           ("0x1B69C", "EffectQuake"),
           ("0x19D58", "EffectQuakeEnd(候选)"),
           ("0x1C330", "EffectQuakeEnd(候选)"),
           ("0x1BD8C", "EffectQuake(候选)"),
           ("0x1B040", "InOut_Act"),
           ("0x1AEA0", "scroll/InOut_Act第二载体"),
           ("0x1A96C", "InOut(现名rule_in)"),
           ("0x19F9C", "FadeOut(fadeend载体)"),
           ("0x7480", "Window"),
           ("0x10150", "bg_move"),
           ("0xFDF4", "bg_zoom"),
           ("0x10980", "bg_zanime/bg_zoom"),
           ("0x12998", "dash/bg_blur"),
           ("0x12E94", "mdash/bg_blur"),
           ("0x13300", "bg_blur"),
           ("0x1107C", "bg_rot"),
           ("0x2A150", "cross"),
           ("0x1AD18", "EyeCatch/EyeCatchEnd"),
           ("0x10428", "SpriteMove/bg_anime")]

# ---- PSV 对拍规格（本表**唯一**的判据来源；校验脚本从同一处读）----------------
# (V, pos, types, nz_default, gold_nz)
SPECS = [
    ("0x1B69C", 5, "EffectQuake+SpriteQuake", 0, True),
    ("0x1B040", 3, "InOut_Act", 0, True),
    ("0x1AEA0", 2, "InOut_Act", 0, True),
    ("0x1A96C", 2, "InOut", 0, True),
    ("0x10428", 4, "SpriteMove", 0, True),
    ("0x19F9C", 0, "FadeOut", 0, True),
]
# 已尝试、**未达门槛**的对拍（同样计算，数值进表作「不硬凑」的证据）
NEG_SPECS = [
    ("0x1B69C", 0, "EffectQuake+SpriteQuake", 0, True),
    ("0x1B69C", 2, "EffectQuake+SpriteQuake", 0, True),
    ("0x1B69C", 3, "EffectQuake+SpriteQuake", 0, True),
    ("0x1B69C", 4, "EffectQuake+SpriteQuake", 0, True),
    ("0x1B040", 0, "InOut_Act", 0, True),
    ("0x1B040", 1, "InOut_Act", 0, True),
    ("0x1B040", 2, "InOut_Act", 0, True),
    ("0x1B040", 4, "InOut_Act", 0, True),
    ("0x1AEA0", 0, "InOut_Act", 0, True),
    ("0x1AEA0", 1, "InOut_Act", 0, True),
    ("0x1A96C", 0, "InOut", 0, True),
    ("0x1A96C", 1, "InOut", 0, True),
    ("0x19F9C", 0, "FadeIn", 0, True),
    ("0x10980", 1, "SpriteBG+Sprite+SpriteBS", 0, True),
    ("0x12998", 10, "SpriteBG+Sprite+SpriteBS", 0, True),
    ("0x12E94", 10, "SpriteBG+Sprite+SpriteBS", 0, True),
    ("0x1107C", 1, "SpriteBG+Sprite+SpriteBS", 0, True),
    ("0x1BD8C", 8, "EffectQuake+SpriteQuake", 0, True),
    ("0x1B888", 0, "SpriteBG+Sprite+SpriteBS", 0, True),
    ("0x1B888", 1, "SpriteBG+Sprite+SpriteBS", 0, True),
    ("0x7480", 0, "Window", 0, True),
    ("0x7480", 1, "Window", 0, True),
    ("0x1AD18", 3, "EyeCatch+EyeCatchEnd", 0, True),   # 金标该 type 无 time 列
    ("0x1AD18", 0, "EyeCatch+EyeCatchEnd", 0, True),
    ("0x2A150", 3, "SpriteBG+Sprite+SpriteMove", 0, True),  # 不在剧情语料
]

SRC = "ot,otr"

# ---- 手写语义表：{(V,pos): (语义, 来源, 备注)} ---------------------------------
# 未在此表出现的位：由自动规则填（常量 ⇒ PC自证「常量，无信息」；否则 ⇒ 未证）。
SEM = {
    # ---- PSV对拍（语义在 SPECS 里判，这里只写备注语义描述）----
    ("0x1B69C", 5): ("时长(ms)", "PSV对拍", "对拍 PSV EffectQuake（SpriteQuake 无增量：单 EffectQuake 亦 23/23=1.000）"),
    ("0x1B040", 3): ("时长(ms)", "PSV对拍", "代码 EQZ→默认 1000；对拍 PSV InOut_Act"),
    ("0x1AEA0", 2): ("时长(ms)", "PSV对拍", "代码 EQZ→默认 1000；对拍 PSV InOut_Act；错 type InOut 仅 scene 0.509"),
    ("0x1A96C", 2): ("时长(ms)", "PSV对拍", "对拍 PSV InOut；**位歧义已解**：同 V pos0 值域重叠但置换基线=自身（无信号）"),
    ("0x10428", 4): ("时长(ms)", "PSV对拍", "对拍 PSV SpriteMove；换 type（SpriteBG 0.133 / Sprite 0.000）即塌陷 ⇒ 定 type 成立"),
    ("0x19F9C", 0): ("时长(ms)（FadeOut 段）", "PSV对拍",
                     "对拍 PSV FadeOut（对 FadeIn 0.000 ⇒ 归 FadeOut）；非退化口径（金标 time=0 剔出分母）"),
    # ---- PC自证 ----
    ("0x1B040", 4): ("转场图案选择子（0..6，7 路）", "PC自证",
                     "代码：LD_STK arg4 → LT 0 / GT 6 越界即 RET → TABJMP 7 分支；分支名串依次 "
                     "zoomflip/wave/mosaic/rotaxis/rotcenter/addsub/hblur（`过程`内嵌串）"),
    ("0x10150", 1): ("方向 token（串 l/r/u/d/c）", "PC自证",
                     "引擎按串消费；值域 S l82/d65/r60/u19/c18（**订正 skill 只记 d/u**，实测 5 种）"),
    ("0x1AD18", 4): ("素材路径（PIC\\EC*.ELG）", "PC自证",
                     "543/561 = PIC\\EC28.ELG；PSV EyeCatch 只有 image 列、**无路径列** ⇒ 无对拍"),
    # ---- 未证（值域像 X，无判据）----
    ("0x1B888", 0): ("未证（值域 50..800、众 100、去重 6；疑强度或时长）", "未证",
                     "代码 EQZ→ST_STK 600（默认 600）；PSV Flash 461 行 **0 个参数字段** ⇒ 无判据"),
    ("0x1B888", 1): ("未证（值域 0..16777215、众 0xFFFFFF、去重 9；疑 RGB 颜色）", "未证",
                     "去重值 9 个：0xFFFFFF×463 / 0x6C272D×44 / 0x001E43×4 / 0xDAA520×3 / 0x000000×3 / "
                     "0xD70035×2 / 0xEDDC44×2 / 0xFF1493×2 / 0x0000FF×1，多为**可命名色**"
                     "（deep pink / goldenrod / dark navy 一带）⇒ 强烈倾向 RGB；但 **PSV Flash 无参数字段**"
                     "⇒ 无判据、不升档（`值域像色` 不等于 `已解`）"),
    ("0x1B69C", 0): ("未证（值域 {0,1}、众 1；仅转交 native#251）", "未证",
                     "代码里 +1 后作 native#251 实参；含义无判据"),
    ("0x1B69C", 1): ("未证（串 '0'×853 / '1'×86；仅转交 native#251）", "未证", "value 为串 ⇒ 无数值可对拍"),
    ("0x1B69C", 2): ("未证（值域 {0,1}、众 0；仅转交 native#251）", "未证", ""),
    ("0x1B69C", 3): ("未证（值域 0..50、众 30；疑振动振幅 x）", "未证",
                     "PSV EffectQuake **只有 time 一列**、无振幅列 ⇒ 只能看值域，不升档"),
    ("0x1B69C", 4): ("未证（值域 0..80、众 30；疑振动振幅 y）", "未证", "同上；位变异后 PSV 对拍塌到 0/628"),
    ("0x19D58", 0): ("未证（二元选择子：命中选择常量 2 / 3 写入局部槽）", "未证",
                     "值域 {0,1} 众 0；PSV EffectQuakeEnd 918 行**无 time** ⇒ 无对拍"),
    ("0x1BD8C", 0): ("未证（值域 {0,1}、众 1）", "未证", "PSV 对拍不达门槛（见 未证表）"),
    ("0x1BD8C", 4): ("未证（串 '0'×107/'1'×7/'0.2'×4/'0.8'×2）", "未证", ""),
    ("0x1BD8C", 5): ("未证（值域 0..64、众 30；疑振幅 x）", "未证", ""),
    ("0x1BD8C", 6): ("未证（值域 0..100、众 30；疑振幅 y）", "未证", ""),
    ("0x1BD8C", 7): ("未证（值域 0..25、众 0）", "未证", ""),
    ("0x1BD8C", 8): ("未证（值域 {0,-1,200,300,500,…}、众 0；**疑 ms**）", "未证",
                     "值域像 ms 含 -1=默认，但 PSV 对拍不达门槛（exact 11/26=0.423、seq 0.523 vs 置换基线 0.409）⇒ **不硬凑**"),
    ("0x1B040", 0): ("未证（值域 {0,768,2048}、众 0）", "未证", "转交 native#251；对拍 0/10"),
    ("0x1B040", 1): ("未证（值域 0..1000、众 0、去重 15）", "未证", "转交 native#251"),
    ("0x1B040", 2): ("未证（值域 0..3、众 0）", "未证", "转交 native#251；对拍 0/42"),
    ("0x1AEA0", 1): ("未证（值域 {0,2}、众 2）", "未证", "转交 native#251；对拍 0/47"),
    ("0x1A96C", 0): ("未证（值域 0..1000、众 0、去重 9；**与 pos2 同值域但无对拍信号**）", "未证",
                     "**解掉 decode 的 `rule_in` pos0/pos2 歧义**：pos0 exact 314/418=0.751 vs 置换基线 312/418=0.746（Δ=0.005 ⇒ 无信号）；pos2 0.931 vs 0.607（Δ=0.324）⇒ ms = pos2"),
    ("0x1A96C", 1): ("未证（值域 4..-1、众 -1、去重 38；疑位掩码）", "未证", "对拍 0/634"),
    ("0x7480", 0): ("未证（值域 {0,300}、众 0）", "未证",
                     "代码：arg0 ≠ 0 ⇒ HALT_OK 中止；PSV Window 1559 行**仅 20 行有 time**（12..120），PC 侧无对应值域 ⇒ 无对拍样本"),
    ("0x7480", 1): ("未证（值域 {0,1}、众 0）", "未证", "经 native#721 写入；疑与循环上界/开关有关，无判据"),
    ("0xFDF4", 1): ("未证（串 '2'/'1.5'/'3'/'2.5'/'4'/'10'；疑缩放倍率）", "未证",
                     "同过程内嵌串 `bg_zoom` 是**命令名**、不是该位名；PSV **无 bg_zoom type** ⇒ 无对拍"),
    ("0xFDF4", 2): ("未证（值域 0..600、众 300、去重 12；疑 w）", "未证", "对拍 1/7=0.143（样本小）"),
    ("0xFDF4", 3): ("未证（值域 120..800、众 400、去重 10；疑 h）", "未证", "对拍 0/7"),
    ("0x10980", 0): ("未证（值域 {0,1}、众 0）", "未证",
                     "代码链 MOV(&var#820)+MUL(4)+ADD ⇒ 作 **var#820 数组下标**（用位直证，但下标含义未证）"),
    ("0x10980", 1): ("未证（值域 200..1500、众 200、去重 9）", "未证",
                     "decode 记 `bg_zanime` pos1（上游宏配对口径 .846），但**本批 PSV 对拍不达门槛**：exact 9/20=0.450、seq 9/26=0.346、scene 34/58=0.586（置换基线 28/58=0.483）"),
    ("0x10980", 2): ("未证（串 '0'/'−2'/'2'/'1'…）", "未证", "转交 native#214('bg_zoom')"),
    ("0x10980", 3): ("未证（串 '2.0'/'1'/'1.5'…）", "未证", ""),
    ("0x10980", 4): ("未证（值域 0..600、众 0、去重 14）", "未证", "对拍 2/14=0.143"),
    ("0x10980", 5): ("未证（值域 0..800、众 0、去重 16）", "未证", "对拍 0/14"),
    ("0x12998", 2): ("未证（值域 {0}；代码直证：作 var#820 数组下标）", "未证",
                     "代码链 MOV(&var#820)+MUL(4)+ADD ⇒ 下标；下标含义未证"),
    ("0x12998", 3): ("未证（值域 {0}）", "未证", ""),
    ("0x12998", 4): ("未证（值域 {0}）", "未证", ""),
    ("0x12998", 5): ("未证（值域 {0}）", "未证", ""),
    ("0x12998", 6): ("未证（值域 {0}）", "未证", ""),
    ("0x12998", 7): ("未证（值域 {0}）", "未证", ""),
    ("0x12998", 8): ("未证（串 '0'/'3'/'6'/'2'）", "未证", ""),
    ("0x12998", 9): ("未证（值域 {128}）", "未证", ""),
    ("0x12998", 10): ("未证（值域 100..800、众 150、去重 8；**疑 ms**）", "未证",
                      "decode 记 `dash` pos10（上游宏配对口径 .815），但**本批 PSV 对拍不达门槛**：exact 3/17=0.176、seq 6/29=0.207、scene 24/57=0.421（置换基线 23/57=0.404）"),
    ("0x12998", 11): ("未证（串 '0'/'0.8'/'0.5'/'1'）", "未证", ""),
    ("0x12998", 12): ("未证（串 '1'/'2'/'3'/'10.0'/'1.5'）", "未证", ""),
    ("0x12998", 13): ("未证（串 '0'/'1.0'）", "未证", ""),
    ("0x12998", 14): ("未证（串 '1'/'3'/'1.0'/'2'/'10.0'）", "未证", ""),
    ("0x12998", 15): ("未证（值域 0..550、众 300、去重 16）", "未证", "对拍 3/18（样本小）"),
    ("0x12998", 16): ("未证（值域 0..800、众 400、去重 15）", "未证", "对拍 0/20"),
    ("0x12E94", 5): ("未证（值域 {0,1}）", "未证", ""),
    ("0x12E94", 6): ("未证（值域 {0,1}）", "未证", ""),
    ("0x12E94", 8): ("未证（串 '0'/'2'/'3'）", "未证", ""),
    ("0x12E94", 10): ("未证（值域 200..400、众 200、去重 3；**疑 ms**）", "未证",
                      "decode 记 `mdash` pos10（上游宏配对口径 .867 / otr 1.00），但**本批 PSV 对拍不达门槛**：exact 1/1（样本小）、seq 12/19=0.632、scene 20/24=0.833（置换基线 20/24=0.833 ⇒ 零增益）"),
    ("0x12E94", 11): ("未证（值域 {1,3}）", "未证", ""),
    ("0x12E94", 12): ("未证（坐标串集 '(x,y,p)(x,y,q)'，28 例；疑两段裁剪窗）", "未证",
                      "PSV 无 bg_blur/坐标串字段 ⇒ 无对拍；串内生 ',' 与 '(' 是「126 行非贪婪正则会解析错」的实例"),
    ("0x13300", 2): ("未证（串 '2'/'3'/'1.5'/'4'；疑模糊量）", "未证", "PSV 无 bg_blur type"),
    ("0x13300", 3): ("未证（值域 100..400、众 100、去重 4；疑 ms 或 w）", "未证", "样本 7（**样本小**），对拍 0/3"),
    ("0x13300", 4): ("未证（值域 100..400、众 400、去重 4；疑 h）", "未证", "样本 7（**样本小**），对拍 0/3"),
    ("0x1107C", 1): ("未证（值域 {300,500}；**疑 ms**）", "未证",
                     "decode 记 `bg_ranime` pos1（上游宏配对口径 7/7=1.000），但**本批样本 7（样本小）且置换基线 7/7=1.000 ⇒ 零增益**，不升档"),
    ("0x1107C", 2): ("未证（串 '2.0'/'0'）", "未证", ""),
    ("0x1107C", 3): ("未证（串 '1.0'/'1.5'/'1.8'/'2.5'）", "未证", ""),
    ("0x1107C", 4): ("未证（值域 {0,-64}、众 0）", "未证", ""),
    ("0x1107C", 5): ("未证（值域 {0,-200}、众 0）", "未证", ""),
    ("0x1107C", 6): ("未证（值域 {0,100}）", "未证", ""),
    ("0x2A150", 1): ("未证（值域 {0}）", "未证", "cross **不在剧情语料**（21 节点全在系统脚本）⇒ 无从与剧情金标对拍"),
    ("0x2A150", 2): ("未证（值域 {0,32,35}、众 0）", "未证", "转交 native#251('cross')"),
    ("0x2A150", 3): ("未证（值域 {8,400,750,1200}、众 8；**疑 ms**）", "未证",
                     "转交 native#251('cross')；gallery 侧组合最像「时长+标志」，但**系统脚本无金标** ⇒ 不升档"),
    ("0x2A150", 4): ("未证（值域 {0,8,2}、众 0）", "未证", "**本过程未读取该位**（读位 = 0,1,2,3）"),
    ("0x1AD18", 1): ("未证（值域 {0,1}、众 0）", "未证", "PSV EyeCatch 只有 image 列 ⇒ 无 time 可对"),
    ("0x1AD18", 3): ("未证（值域 {300,400,500}、众 300；**疑 ms**）", "未证",
                     "PSV EyeCatch **847 行只有 image 列、无 time** ⇒ 无可对拍字段（试对 EyeCatch 得 0 样本）"),
    ("0x10428", 5): ("未证（方向 token 串 r/a0 r/l/d/u/c…）", "未证",
                     "值形同方向 token（与 0x10150 pos1 同源），但该 V 的 PSV 对拍（SpriteMove :Time）已在 pos4 用掉 ⇒ 本批**不另立 PC自证**，避免把「同源」当直证"),
    ("0x19D58", 1): ("未证（值域 {1}）", "未证", "**本过程未读取该位**（读位 = 0）"),
    ("0x12998", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x12998", 1): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x12E94", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x12E94", 1): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x12E94", 2): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x12E94", 3): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x12E94", 4): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x12E94", 7): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x12E94", 9): ("常量，无信息（值域去重 1）", "PC自证", "恒 128"),
    ("0x1C330", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 1；PSV EffectQuakeEnd 无 time ⇒ 无对拍"),
    ("0x1BD8C", 1): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x1BD8C", 2): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x1BD8C", 3): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x1AEA0", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 2"),
    ("0x10150", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0xFDF4", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x13300", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 1"),
    ("0x13300", 1): ("常量，无信息（值域去重 1）", "PC自证", "恒串 '0'"),
    ("0x1107C", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x2A150", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 0；代码：arg0 ≠ 0 ⇒ 走分支建对象"),
    ("0x1AD18", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x1AD18", 2): ("常量，无信息（值域去重 1）", "PC自证", "恒 86"),
    ("0x10428", 0): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x10428", 1): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x10428", 2): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
    ("0x10428", 3): ("常量，无信息（值域去重 1）", "PC自证", "恒 0"),
}

PSV_THRESHOLD = 0.90
BASELINE_GAIN = 0.15


def fmt_rate(a, b):
    return "%d/%d=%.3f" % (a, b, a / b) if b else "-"


def _rate_str(types, nz, gnz, allr):
    """主规格的命中率串（exact/seq/scene + 置换基线 + 样本小标注）。"""
    parts = []
    small = False
    for src, rr in allr:
        parts.append("[%s] exact %s；seq %s；scene %s（置换基线 %s）" % (
            src, fmt_rate(rr["exact"], rr["n_exact"]),
            fmt_rate(rr["seq"], rr["n_seq"]), fmt_rate(rr["scene"], rr["n_scene"]),
            fmt_rate(rr["null"]["exact"], rr["null"]["n_exact"])))
        if rr["n"] and rr["n"] < 10:
            small = True
    s = " | ".join(parts) or "-"
    return s + ("【样本小】" if small else "")


def main():
    # 1) 全库 argc/值域
    cor, nf, bad = CA.scan(CA.SCRIPTDIR)
    # 2) 读位（帧口径）
    read_map = {}
    for v, _name in TARGETS:
        ac = sorted(cor.get(v, {"argc": {}})["argc"].items())
        argv = ac[0][0] if ac else None
        r = FA.analyse(v, argv)
        read_map[v] = set()
        if r:
            for row in r["rows"]:
                if row["cls"] == "实参" and row["i"] is not None:
                    read_map[v].add(row["i"])

    # 3) PSV 对拍数值（**主规格优先**：命中率列取主规格；其余尝试写进备注）
    def run_spec(v, pos, types, nz, gnz):
        allr = []
        for src in SRC.split(","):
            rr = PJ.join(src, v, pos, types.split("+"), nz, gold_nz=gnz)
            if rr["n"]:
                allr.append((src, rr))
        return allr

    specn = {}     # (v,pos) -> {"main": ..., "neg": [...]}
    for (v, pos, types, nz, gnz) in SPECS:
        specn.setdefault((v, pos), {"main": None, "neg": []})
        specn[(v, pos)]["main"] = (types, nz, gnz, run_spec(v, pos, types, nz, gnz))
    for (v, pos, types, nz, gnz) in NEG_SPECS:
        specn.setdefault((v, pos), {"main": None, "neg": []})
        specn[(v, pos)]["neg"].append((types, nz, gnz, run_spec(v, pos, types, nz, gnz)))

    # 4) 逐位建行
    rows = []
    for v, name in TARGETS:
        acs = sorted(cor.get(v, {"argc": {}})["argc"].items())
        argc = acs[0][0] if acs else None
        acs_s = ",".join("%d×%d" % (k, c) for k, c in acs) or "-"
        if argc is None:
            continue
        for p in range(argc):
            sem, srcn, note = SEM.get((v, p), (None, None, ""))
            nread = p in read_map.get(v, set())
            note = (note + "；" if note else "") + ("本过程读该位" if nread else "本过程未读该位")
            # 自动兜底（手写表未覆盖的位）
            if sem is None:
                ar = cor[v]["argc"] and None
                sem, srcn = "未证（手写语义表未覆盖该位，值域见 效果族参数位_全库.tsv）", "未证"
            # PSV 对拍命中/样本（主规格优先，其余尝试进备注）
            n_s, rate_s, ctr_s = "-", "-", "-"
            entry = specn.get((v, p))
            if entry:
                chosen = entry["main"] or (entry["neg"][0] if entry["neg"] else None)
                if chosen:
                    types, nz, gnz, allr = chosen
                    rate_s = _rate_str(types, nz, gnz, allr)
                    n_s = "/".join("%s:%d" % (s, rr["n"]) for s, rr in allr) or "-"
                extras = [x for x in ([entry["main"]] if entry["main"] else []) + entry["neg"]
                          if x and x is not chosen]
                if extras:
                    note = (note + "；" if note else "") + "另已试对拍：" + "；".join(
                        "%s(nz=%s%s) %s" % (x[0], x[1],
                                            "，非退化" if x[2] else "", _rate_str(*x))
                        for x in extras)
                # 反例取主规格首条
                if chosen:
                    for src, rr in chosen[3]:
                        if rr["ex_lines"]:
                            e = rr["ex_lines"][0]
                            ctr_s = "解出_%s.tsv:%d vs 时间线.tsv:%d（ms=%s→帧 %s，金标 %s=%s）" % (
                                src, e[0], e[4], e[2], e[3], e[5], e[6])
                            break
            rows.append({"V": v, "命令名": name, "argc": acs_s, "位号": p,
                         "语义": sem, "来源": srcn, "对拍样本量": n_s,
                         "命中率": rate_s, "反例(文件:行)": ctr_s, "备注": note,
                         "_read": nread})

    cols = ["V", "命令名", "argc", "位号", "语义", "来源", "对拍样本量", "命中率",
            "反例(文件:行)", "备注"]
    out = os.path.join(HERE, "效果族参数位.tsv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    print("-> %s （%d 行 / %d V）" % (out, len(rows), len(TARGETS)))

    out2 = os.path.join(HERE, "效果族参数位_未证.tsv")
    nv = [r for r in rows if r["来源"] == "未证"]
    with open(out2, "w", encoding="utf-8", newline="") as f:
        f.write("V\t命令名\targc\t位号\t值域/证据\t对拍样本量\t命中率\t备注\n")
        for r in nv:
            print_vals = r["语义"].replace("未证（", "").rstrip("）")
            f.write("%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\n" % (
                r["V"], r["命令名"], r["argc"], r["位号"], print_vals,
                r["对拍样本量"], r["命中率"], r["备注"]))
    print("-> %s （%d 行，未证项单列）" % (out2, len(nv)))
    from collections import Counter
    print("来源分布：", dict(Counter(r["来源"] for r in rows)))
    print("全库扫描：文件 %d（跳过 %d）" % (nf, bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
