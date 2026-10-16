# -*- coding: utf-8 -*-
r"""mk_probe.py —— 为「长标题 × 已读对勾」出一张**实机对照图**（零间隙 vs 补硬断行）

背景（实测事实，决定了本探针必须标注为「模拟未来态」）：
  · `_read`（已读对勾）**只在主干节点上产生**（生成器里就是 `fc.node.%s_read`），
    番外独立层（`fc.frag*`）**没有任何运行态**（裁决 4：不写 `flow_state`、不产 `_dim`/`_new`）。
  · 而**全部 20 条长标题（12 条已硬断行 + 8 条零间隙边界簇）都是番外/归档标题**
    ⇒ **在当前实现里，对勾与这些长标题不可能同框**。
  · 所以这张对照图展示的是**未来态**：假设番外层也有了已读对勾（挂在**层旗标** `fc_layer` 上，
    用巡演的真实 flag 机制驱动，不伪造运行态），长标题与对勾的**相对位置**长什么样。

三个子命令：
    python mk_probe.py save       # 把四件生成物原样存到 _pristine/
    python mk_probe.py apply A    # 注入 `_read` ×2（标题保持现状＝零间隙）
    python mk_probe.py apply B    # 注入 `_read` ×2 ＋ 两条标题按「（」断行
    python mk_probe.py restore    # 从 _pristine/ 还原并核对 md5

顶点（交付样例里唯一在册的两条零间隙标题，均 **236px / 首行墨迹左缘 +30.00**）：
    `42_3`  fc.frag4.0008  「格兰·玛尼耶（ＥＡＧＬＥ）」
    `42_4`  fc.frag4.0009  「格兰玛·露尼耶（ＦＡＬＣＯＮ）」

注入几何＝主干 `_read` 的**同一口径**：节点 +10/+12、20×20、1:1 无 nine、
`asset="ui/x_ui_read_check.png"`、`opacity 255`、`z = 节点z + 6`。
`vis_flag:"fc_layer"` + `vis_when:"frag4"`（与同层节点件同旗标）⇒ 由 `run_autotour.bat frag4` 的
真实层旗标驱动显示。
"""
import io
import json
import os
import shutil
import subprocess
import sys

UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 复现脚本 → ISSUE 目录 → _工作 → UI组
HERE = os.path.dirname(os.path.abspath(__file__))
assert os.path.basename(UI) == "UI组", UI
PRISTINE = os.path.join(HERE, "_pristine")
SCREEN = os.path.join(UI, "layout", "screens", "32_flowchart.json")
ARTIFACTS = [SCREEN,
             os.path.join(UI, "layout", "ui_layout.json"),
             os.path.join(UI, "krkr", "game", "ui_layout.tjs"),
             os.path.join(UI, "复刻", "ui_layout.js")]
TARGETS = [("fc.frag4.0008", "格兰·玛尼耶", "（ＥＡＧＬＥ）"),
           ("fc.frag4.0009", "格兰玛·露尼耶", "（ＦＡＬＣＯＮ）")]


def md5(p):
    import hashlib
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def cmd_save():
    os.makedirs(PRISTINE, exist_ok=True)
    for p in ARTIFACTS:
        shutil.copyfile(p, os.path.join(PRISTINE, os.path.basename(p)))
    for p in ARTIFACTS:
        print("saved %-42s %s" % (os.path.basename(p), md5(p)[:16]))


def cmd_restore():
    for p in ARTIFACTS:
        shutil.copyfile(os.path.join(PRISTINE, os.path.basename(p)), p)
    bad = 0
    for p in ARTIFACTS:
        a = md5(p)
        b = md5(os.path.join(PRISTINE, os.path.basename(p)))
        print("restore %-42s %s %s" % (os.path.basename(p), a[:16], "OK" if a == b else "MISMATCH"))
        bad += (a != b)
    return 1 if bad else 0


def cmd_apply(variant):
    sc = json.load(io.open(os.path.join(PRISTINE, os.path.basename(SCREEN)), encoding="utf-8"))
    els = {e["id"]: e for e in sc["elements"]}
    added = []
    for nid, l1, l2 in TARGETS:
        cell = els[nid]
        rid = nid + "_read"
        assert rid not in els, "已存在 " + rid
        els[rid] = {
            "id": rid, "kind": "image", "z": cell["z"] + 6, "visible_default": True,
            "asset": "ui/x_ui_read_check.png",
            "x": cell["x"] + 10, "y": cell["y"] + 12, "w": 20, "h": 20, "opacity": 255,
            "vis_flag": "fc_layer", "vis_when": "frag4",
            "source": "素材组产出（★ ISSUE-20260928-03）：绿对勾 20×20（1:1、无 nine）—— "
                      "本探针仅把它挂到番外层的层旗标上做**未来态对照**，不入库",
            "note": "★ 探针注入（不入库）：模拟番外层的已读对勾 —— 几何＝主干 `_read` 同口径（+10/+12、20×20、z=节点z+6）",
        }
        added.append(rid)
        if variant.upper() == "B":
            tx = els[nid + "_tx"]
            joined = l1 + l2
            src = (tx.get("sample") or "").replace("\n", "")
            assert src == joined, "文本不符：%r ≠ %r" % (src, joined)
            tx["sample"] = l1 + "\n" + l2
            print("  断行 %s_tx：%s" % (nid, tx["sample"].replace("\n", "⏎")))
    order = [e for e in sc["elements"] if e["id"] not in added] + [els[i] for i in added]
    sc["elements"] = order
    sc["note"] = (sc.get("note") or "") + "\n· ★ 探针变体 %s（不入库）：注入 %s 的 `_read`（模拟番外层已读对勾）" % (variant.upper(), added)
    io.open(SCREEN, "w", encoding="utf-8", newline="").write(
        json.dumps(sc, ensure_ascii=False, indent=1) + "\n")
    r = subprocess.run([sys.executable, os.path.join(UI, "工具", "gen_layout.py")],
                       cwd=UI, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:]); print(r.stderr[-2000:]); return 1
    print("变体 %s 已生成；元素 %d → %d" % (variant.upper(), len(els) - len(added), len(els)))
    print("ui_layout.tjs md5 = %s" % md5(ARTIFACTS[2])[:16])
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1] if len(sys.argv) > 1 else ""
    if a == "save":
        cmd_save()
    elif a == "restore":
        sys.exit(cmd_restore())
    elif a == "apply":
        sys.exit(cmd_apply(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(2)
