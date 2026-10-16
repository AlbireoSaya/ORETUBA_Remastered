#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
gate_story_assets.py —— 发布闸门：剧本引用 vs story_assets 实件（**硬失败**）
=================================================================================
ISSUE-20261008-01 / M7。这是本缺陷（99 件背景素材未随剧本落盘、影响 111 场）的
**直接拦截器**：`assemble_game.py` 与 `deploy_product.py` 在落盘/部署前都必须过它。

口径（**与 `子代理工作区\ISSUE-20261008-01\M6\scan_missing_assets.py` 完全一致**）
----------------------------------------------------------------------------------
  · 引用口径：`<game>\story\scene_*.tjs` 文本上跑正则 `story_assets/[^"']+`；
  · 以 `<game>` 为基准判 `os.path.exists(<game>\<引用>)` ⇒ 不存在者即「缺件」。
  · 只要缺 1 件即**非零退出**，并把**全部缺件名**与首现场景打到 stderr。

边界（如实声明）
----------------
  · 只扫 `scene_*.tjs`（与上述 M6 口径一致）。M6 已另补扫其余 7 个 `story\_*.tjs`
    （`_intro`/`_eyecatch`/`_flowgeom`/`_flowpages`/`_index`/`_music`/`_eyecatch_chibi`），
    实测闭合 0 缺；若将来这些文件也引用素材，本闸门**不覆盖**（勿误以为已全量网住）。
  · 本模块**只读**，不写任何文件。

为什么需要它（缺陷成因，直证）
-----------------------------
  `build_story.py` 生成剧本（含 `story_assets/…` 引用）与 `story_assets\` 两块产物，
  引用名与落盘名恒等（同一 `flat` 变量），**源侧存在性校验只在源侧**；
  而**发布链（assemble / deploy）只做增量复制、不做「引用 ⊆ 实件」对账**。
  2026-10-07 的生产装配带了 `assemble_game.py --no-story-assets`（跳过整棵 story_assets），
  `deploy_product.py` 的 `sync()` 只增不删、又只剪 `story\scene_*.tjs`，**发现不了**，
  于是新剧本配旧 payload ⇒ 99 件悬空引用进了成品。
  ⇒ 唯一能拦住的是本闸门：**已发布 payload ⊇ 已发射引用**。
"""
import os
import re
import sys

REF_RE = re.compile(r"story_assets/[^\"']+")
SCENE_RE = re.compile(r"^scene_.*\.tjs$")

# 诊断构建标记：`assemble_game.py --no-story-assets --diagnostic-build` 会在装配根写此文件，
# `deploy_product.py` 见到它就**拒绝部署**（诊断产物不得当成品）。
MARKER = ".no_story_assets"

GATE_EXIT = 4


def scan_missing(game_dir):
    """返回 (scene 数, 引用处数, missing)。

    `missing` = {引用名: [首现场景, …]}；引用名形如 `story_assets/bg__xxx.png`。
    """
    story = os.path.join(game_dir, "story")
    if not os.path.isdir(story):
        raise SystemExit("[gate] 缺 story 目录：%s" % story)
    scenes = sorted(f for f in os.listdir(story) if SCENE_RE.match(f))
    missing = {}
    n_refs = 0
    for fn in scenes:
        sid = fn[len("scene_"):-len(".tjs")]
        try:
            txt = open(os.path.join(story, fn), encoding="utf-8", errors="replace").read()
        except OSError as e:
            raise SystemExit("[gate] 读场景失败 %s：%s" % (fn, e))
        for m in REF_RE.finditer(txt):
            n = m.group(0)
            n_refs += 1
            if os.path.exists(os.path.join(game_dir, n.replace("/", os.sep))):
                continue
            missing.setdefault(n, [])
            if sid not in missing[n]:
                missing[n].append(sid)
    return len(scenes), n_refs, missing


def enforce_gate(game_dir, label="发布闸门", exit_code=GATE_EXIT):
    """硬闸门：缺一件即打印全部缺件并 sys.exit(exit_code)。全齐则打印一行通过。"""
    game_dir = os.path.abspath(game_dir)
    n_scene, n_refs, missing = scan_missing(game_dir)
    if missing:
        miss = sorted(missing)
        sys.stderr.write(
            "[gate][FATAL] %s：%d 个引用在 story_assets 中无实件"
            "（扫描 %s 的 %d 个 scene_*.tjs / %d 处引用）\n"
            % (label, len(miss), os.path.join(game_dir, "story"), n_scene, n_refs))
        for n in miss:
            sys.stderr.write("   缺件 %s  ← 首现场景 %s\n"
                             % (n, ",".join(missing[n][:8])))
        sys.stderr.write(
            "[gate] 口径：story\\scene_*.tjs 正则 story_assets/[^\"']+ 逐名判存在"
            "（同 子代理工作区\\ISSUE-20261008-01\\M6\\scan_missing_assets.py）\n"
            "[gate] 这就是 99 件背景素材未落盘的同类缺陷；发布链禁止在缺件状态下继续。\n")
        sys.exit(exit_code)
    sys.stderr.write("[gate] %s：story\\scene_*.tjs 引用 %d 处，story_assets 实件齐备（0 缺件）\n"
                     % (label, n_refs))
    return 0


if __name__ == "__main__":
    # 供命令行单独复核：python gate_story_assets.py <game 目录>
    if len(sys.argv) < 2:
        print("用法：python gate_story_assets.py <game 目录>", file=sys.stderr)
        sys.exit(2)
    enforce_gate(sys.argv[1], label="独立复核")
