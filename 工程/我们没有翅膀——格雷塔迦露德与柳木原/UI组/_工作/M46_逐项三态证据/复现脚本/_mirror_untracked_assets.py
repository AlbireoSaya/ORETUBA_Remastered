# -*- coding: utf-8 -*-
r"""镜像补丁 · **gitignored 可再生产物**的同步（补齐 `_mirror_to_main_worktree.py` 的盲区）

■ 为什么需要它（2026-09-24 实测踩到）
  `_mirror_to_main_worktree.py` 按 `git diff --name-status` 工作 ⇒ **只同步被 git 跟踪的文件**。
  而 `UI组\krkr\assets\face\`（361 张 / ~50 MB）是**可再生产物、按设计不入库**（`.gitignore`）。
  于是 2026-09-24 出现这个现象：**主工作树（用户看编辑器/演示的那份）里 `face/` 还是 M44 旧集**，
  而布局数据（`cfg.pv_name_*` 等）已同步 ⇒ 用户在编辑器里看到「名字换了、头像没换」。
  （核对证据：`hiy01.png` 工作树 `b10b9151…` vs 主工作树 `e1ab1eb8…`。）

■ 做法
  对**显式列出的目录**逐个文件按 **md5** 比较，不一致或缺失就复制（单向：本 worktree → 主工作树）；
  只增不删（不做反向删除——主工作树里可能有别的东西）。复制完再复核一遍 md5 并打印统计。

■ 用法（在 `UI组\` 下）
    python _工作\M46_逐项三态证据\复现脚本\_mirror_untracked_assets.py            :: 同步默认清单
    python _工作\M46_逐项三态证据\复现脚本\_mirror_untracked_assets.py --check    :: 只比对不复制
    python _工作\M46_逐项三态证据\复现脚本\_mirror_untracked_assets.py krkr/assets/face  :: 指定相对 UI组 的目录

■ 何时要跑
  **任何重制了 gitignored 素材的轮次**（目前就是 `face/`）；跑完顺手在工程记录里登记。
"""
import hashlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # …\UI组
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))         # …\wt-qbicons
MAIN_WT = r"E:\ZCode Workspace\Galgame"                            # 用户看的那份（另一分支）

# 默认清单：相对 `UI组\` 的、**按设计不入库**的可再生产物目录
DEFAULT_DIRS = ("krkr/assets/face",)


def md5(p):
    h = hashlib.md5()
    with io.open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sync(rel, check_only=False):
    src = os.path.join(UI, rel.replace("/", os.sep))
    dst = os.path.join(MAIN_WT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原", "UI组",
                       rel.replace("/", os.sep))
    if not os.path.isdir(src):
        print("  [跳过] 源目录不存在：%s" % src)
        return 0, 0, 0
    copied = same = 0
    for name in sorted(os.listdir(src)):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if not os.path.isfile(s):
            continue
        if os.path.isfile(d) and md5(s) == md5(d):
            same += 1
            continue
        if check_only:
            print("  [需同步] %s/%s" % (rel, name))
        else:
            if not os.path.isdir(dst):
                os.makedirs(dst)
            shutil.copy2(s, d)
        copied += 1
    # 复核
    bad = []
    for name in sorted(os.listdir(src)):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isfile(s) and (not os.path.isfile(d) or md5(s) != md5(d)):
            bad.append(name)
    print("  %s：件数 %d ｜ %s %d ｜ 本就一致 %d ｜ 复核不一致 %d %s"
          % (rel, len([x for x in os.listdir(src) if os.path.isfile(os.path.join(src, x))]),
             "需同步" if check_only else "已复制", copied, same, len(bad), bad[:5]))
    return copied, same, len(bad)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv[1:]
    dirs = tuple(args) if args else DEFAULT_DIRS
    print("镜像（未跟踪素材，单向 %s → %s）" % (WT, MAIN_WT))
    total_bad = 0
    for rel in dirs:
        _, _, bad = sync(rel, check_only)
        total_bad += bad
    print("结论：%s" % ("全部一致 ✓" if total_bad == 0 else "**仍有 %d 件不一致**" % total_bad))
    return 0 if total_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())