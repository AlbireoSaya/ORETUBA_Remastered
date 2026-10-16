# -*- coding: utf-8 -*-
r"""M46 镜像：把本任务的改动同步到主工作树（用户用编辑器/演示读的那份）

主工作树（`E:\ZCode Workspace\Galgame`）当前停在**另一个会话的分支**上，本工程目录在那里是
**未跟踪副本**（mirror）—— 用户从那里打开 `UI组\复刻\editor.html` 看当前状态。
本脚本按 `git diff --name-only <旧 main>..<新 main>` 的清单**逐个文件**同步：

  · 源在 → 复制（含缺失的父目录）；
  · 源不在（删除项，如 `34_sysbar.json`）→ 删除目标；
  · 只镜像本作品目录（`工程\我们没有翅膀——格雷塔迦露德与柳木原\`），**不动** `Galgame.md` /
    `工程记录\`（那两个是给 git 看的文档，且主工作树里那份是另一分支的跟踪文件，覆盖会污染他人工作树）。

用法：python _工作\M46_逐项三态证据\复现脚本\_mirror_to_main_worktree.py <旧main> <新main>
"""
import io
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))           # …/UI组
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))             # …/wt-qbicons
REPO = os.path.dirname(WT)                                             # …/Galgame
MAIN_WT = os.path.join(REPO, "工程")                                   # 占位，稍后覆盖
MAIN_WT = r"E:\ZCode Workspace\Galgame"
SCOPE = "工程/我们没有翅膀——格雷塔迦露德与柳木原"


def main():
    old, new = sys.argv[1], sys.argv[2]
    # ★ 必须用 --name-status：**重命名**（如 `34_sysbar.json` → `_工作\M46_旧素材归档\….snapshot`，
    #   git 判为 R100）在 `--name-only` 里只出现**目标**路径，源路径的删除会被漏掉 ⇒
    #   镜像里那份旧屏文件删不掉（M46 实跑踩到：复制的 61 个路径里没有它，手删了一次）。
    out = subprocess.run(["git", "-C", WT, "diff", "--name-status", "%s..%s" % (old, new), "--", SCOPE],
                         stdout=subprocess.PIPE, check=True).stdout.decode("utf-8")
    paths = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        st = parts[0]
        if st.startswith("R") and len(parts) >= 3:
            paths.append(parts[1])          # 重命名的**源**：镜像里要删
            paths.append(parts[2])          # 目标：要复制
        elif len(parts) >= 2:
            paths.append(parts[1])
    print("待镜像 %d 个路径（%s..%s）" % (len(paths), old, new))
    # ★ 重要（M46 实跑踩到）：主工作树里**已被 git 跟踪且正被修改**的文件，绝不能覆盖 ——
    #   那是**另一个会话的在建改动**（用户常同时开多个 ZCode 会话共享这个工作树）。
    #   M46 首次镜像把 `作品skill/SKILL.md` 盖成了 main 版，覆盖了对方的未提交编辑（不可恢复）。
    #   这里先问目标工作树自己：该路径是否 tracked-dirty？是 → 跳过并告警。
    dirty = subprocess.run(["git", "-C", MAIN_WT, "diff", "--name-only"],
                           stdout=subprocess.PIPE).stdout.decode("utf-8", "replace").splitlines()
    dirty = set(x for x in dirty if x.strip())
    tracked = subprocess.run(["git", "-C", MAIN_WT, "ls-files"],
                             stdout=subprocess.PIPE).stdout.decode("utf-8", "replace").splitlines()
    tracked = set(x for x in tracked if x.strip())
    copied = removed = missing = skipped = 0
    for rel in paths:
        if rel in dirty:
            print("  ⚠ 跳过（主工作树里该文件被跟踪且**正在修改**，可能是他人未提交改动）：" + rel)
            skipped += 1
            continue
        if rel in tracked:
            print("  ⚠ 跳过（主工作树里该文件被跟踪，非镜像副本）：" + rel)
            skipped += 1
            continue
        src = os.path.join(WT, rel)
        dst = os.path.join(MAIN_WT, rel)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
        else:
            if os.path.exists(dst):
                os.remove(dst)
                removed += 1
            else:
                missing += 1
    print("复制 %d ｜ 删除 %d ｜ 目标本就不存在 %d ｜ 跳过（跟踪/在建） %d"
          % (copied, removed, missing, skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
