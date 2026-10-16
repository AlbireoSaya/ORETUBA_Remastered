# -*- coding: utf-8 -*-
r"""m09_archive_pills.py —— ISSUE-20260926-09 任务 A（第 2 步）：14 个旧药丸壳**移动**归档

把 `krkr\assets\ui\x_ui_psv_pill_c1_01..08.png` / `x_ui_psv_pill_c2_01..06.png`
**移动**（不删除）到 `_工作\ISSUE-20260926-09_药丸底图\旧素材归档\`，并写 README.md
（原因 / 日期 / issue / 原路径 / 替换件名 / md5 前后一致）。

幂等：已在归档目录且原位置不存在 ⇒ 只报不写；两处都不存在 ⇒ 报错。

用法（在 <UI组>\ 下）：
    python "_工作\ISSUE-20260926-09_config\复现脚本\m09_archive_pills.py"
"""
import hashlib
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
ARCH = os.path.join(UI, "_工作", "ISSUE-20260926-09_药丸底图", "旧素材归档")
NAMES = (["x_ui_psv_pill_c1_%02d.png" % n for n in range(1, 9)]
         + ["x_ui_psv_pill_c2_%02d.png" % n for n in range(1, 7)])
REPL = "x_ui_psv_pill_blank.png"
DATE = "2026-09-26"
ISSUE = "ISSUE-20260926-09"


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main():
    os.makedirs(ARCH, exist_ok=True)
    rows, moved, noop = [], 0, 0
    for n in NAMES:
        src = os.path.join(ASSETS, n)
        dst = os.path.join(ARCH, n)
        if os.path.isfile(src) and os.path.isfile(dst):
            raise SystemExit("!! 源与归档同时存在（状态不明，停手）：%s" % n)
        if os.path.isfile(src):
            m_before = md5(src)
            shutil.move(src, dst)
            m_after = md5(dst)
            if m_before != m_after:
                raise SystemExit("!! 移动后 md5 变化：%s" % n)
            rows.append((n, m_before, m_after, os.path.getsize(dst), "已移动"))
            moved += 1
        elif os.path.isfile(dst):
            m = md5(dst)
            rows.append((n, m, m, os.path.getsize(dst), "no-op（已在归档）"))
            noop += 1
        else:
            raise SystemExit("!! 源与归档都不存在：%s" % n)

    readme = []
    readme.append("# 旧素材归档 · 14 个 PSV 药丸壳（`x_ui_psv_pill_c1_*` / `c2_*`）\n")
    readme.append("| 项 | 值 |")
    readme.append("| --- | --- |")
    readme.append("| Issue | `%s` |" % ISSUE)
    readme.append("| 日期 | %s |" % DATE)
    readme.append("| 处置 | **移动**（未删除，字节不变）；归档于此，原位置清空 |")
    readme.append("| 替换件 | `krkr\\assets\\ui\\%s`（560×72 RGBA，**一支共用**） |" % REPL)
    readme.append("| 原因 | 这 14 件是从 PSV 原版页按行带切出的**独立文件**，各自带去字残留"
                  "（补块亮斑 + 残存笔画）；用户 %s 裁定**改用一支干净底图**"
                  "（生图去字版）、14 件合 1 支 |" % DATE)
    readme.append("| 源件出处 | `PSV系统UI参考\\去字件\\2x\\bgc01_pill_%02d.png`（页1 8 件 / 页2 6 件）"
                  "→ 工具 `工具\\m53_psv_ui_assets.py` |")
    readme.append("| 新件出处 | `_工作\\ISSUE-20260926-09_药丸底图\\取证\\_ai_fit.png`"
                  "（纹理=生图去字、alpha=原图 560×72）→ `复现脚本\\m09_pill_blank.py` |")
    readme.append("")
    readme.append("## md5 前后一致自证（移动前后逐件核对）\n")
    readme.append("| 文件 | md5（移动前） | md5（移动后） | 字节 | 动作 |")
    readme.append("| --- | --- | --- | ---: | --- |")
    for n, a, b, sz, act in rows:
        readme.append("| `%s` | `%s` | `%s` | %d | %s |" % (n, a, b, sz, act))
    readme.append("")
    readme.append("**结论：14 / 14 件移动前后 md5 逐件一致（字节未变，未删除）。**")
    readme.append("")
    txt = "\n".join(readme)
    with open(os.path.join(ARCH, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)

    print("=" * 100)
    print("m09 任务 A · 旧药丸壳归档")
    print("=" * 100)
    for n, a, b, sz, act in rows:
        print("  %-26s %s  %7d B  %s" % (n, a[:12], sz, act))
    print("-" * 100)
    print("本次移动 %d 件 ｜ no-op %d 件 ｜ 合计 %d 件 ｜ README：%s"
          % (moved, noop, len(rows), os.path.join(ARCH, "README.md")))
    print("md5 前后一致：14 / 14 ✓" if moved or noop else "")
    left = [f for f in os.listdir(ASSETS) if f.startswith("x_ui_psv_pill_c")]
    print("assets/ui 内残留 pill_c* 件数 = %d（应为 0）" % len(left))


if __name__ == "__main__":
    main()
