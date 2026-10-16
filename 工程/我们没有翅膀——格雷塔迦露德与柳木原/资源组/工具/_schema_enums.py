# -*- coding: utf-8 -*-
r"""
`scene.jsonl` 枚举值域常量（**六源校验器共用的唯一来源**）

依据：`资源组\剧本\schema.md` §三.5（W10b 2026-09-19 定稿：`phase` 由三值扩展为八值域）。
用途：六源校验器（`verify_scene_jsonl.py` / `verify_scene_ot.py` / `verify_scene_ota.py` /
      `verify_scene_otp.py` / `verify_scene_otv.py` / `verify_scene_np.py`）一律 import 本模块，
      **统一按同一值域校验，越界即报错**；不得各自硬编码、更不得放宽为「不校验」。

本模块**只读、无副作用**，不写任何文件。

复跑无意义（常量模块）；改动须同步更新 `schema.md` §三.5 的「六源实际取值表」。
"""

# `phase` 值域（八值闭集）。`None` 是合法值，语义＝「未归入任何已定义剧情阶段层」。
# 实测六源取值（W10b 扫描，合计 712 场景）：
#   ot  序1/个人线285/结局9/真相72                       = 367
#   otr 序1/个人线53/结局1                               =  55
#   ota 序4/个人线109/结局6/null53                        = 172
#   otp 序1/个人线18/结局2/主线32/框架2/系统4             =  59
#   otv 序1/个人线28/结局2                               =  31
#   np  序2/个人线19/结局7                               =  28
PHASE_ALLOWED = ("序", "个人线", "结局", "真相", "主线", "框架", "系统", None)


def phase_ok(value):
    """`phase` 是否在值域内。注意 `None` 合法，故不可写成 `if value in PHASE_ALLOWED and value`。"""
    return value in PHASE_ALLOWED


def phase_violations(scenes):
    """返回 `[(scene_id, phase)]`，列出所有越界取值（空列表＝全部合规）。"""
    return [(s.get("scene_id") or s.get("script"), s.get("phase"))
            for s in scenes if not phase_ok(s.get("phase"))]