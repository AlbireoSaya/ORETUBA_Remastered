# -*- coding: utf-8 -*-
"""W11g-schema · 修复「清单可用性缺陷」：把三份分表里**重载的 `类别` 列**拆为
`类别`（纯大类：立绘 / CG背景 / 系统UI）+ `判读类别`（子分类）。

背景（一审实测）：
  - `清单_立绘.tsv`  的 `类别` 取值 = 立绘 1410 / 头像 60 / 未识别 182
  - `清单_CG背景.tsv` 的 `类别` 取值 = CG 648 / 背景 295 / 未判定 221 / 其他 23
  - `清单_系统UI.tsv` 的 `类别` 取值 = 其他 713 / 菜单 277 / 标题 234 / 存档 156 /
                                    转场遮罩 116 / 消息窗 46 / 图标 27
  合并成 `交付清单.tsv` 时子分类被替换为三值大类 → 信息丢失；
  分表自身 `类别=="立绘"` 过滤会漏掉 182 行「未识别」。

本脚本只做**列语义搬迁**，不动任何行、不动任何 PNG：
  - 行数、行序、`统一名` 一律不变；
  - `判读类别` 的取值 = 搬迁前 `类别` 的取值（逐行原样带出，不凭空填）；
  - 幂等：表头已含 `判读类别` 时**只校验、不写盘**（可重复执行）。

用法：
    cd 资源组\\工具
    set PYTHONPATH=E:\\ZCode Workspace\\Galgame\\工具\\pylibs
    python w11g_fix_schema.py            # 执行（幂等）
    python w11g_fix_schema.py --check    # 只校验，绝不写盘
"""
import os
import sys
import shutil

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
UNI = os.path.join(PROJ, "资源组", "美术统一")
BACKUP = os.path.abspath(os.path.join(PROJ, "..", "..", "子代理工作区", "ISSUE-20260918-06", "W11g", "_backup_W11g_schema"))
assert UNI.startswith(r"E:\ZCode Workspace\Galgame")
assert BACKUP.startswith(r"E:\ZCode Workspace\Galgame")

# (分表文件名, 纯大类, 子分类列名, 期望子分类取值集合)
SHEETS = [
    ("清单_立绘.tsv", "立绘", "判读类别", {"立绘", "头像", "未识别"}),
    ("清单_CG背景.tsv", "CG背景", "判读类别", {"CG", "背景", "未判定", "其他"}),
    ("清单_系统UI.tsv", "系统UI", "判读类别", {"其他", "菜单", "标题", "存档", "转场遮罩", "消息窗", "图标"}),
]

NEWCOL = "判读类别"
CHECK_ONLY = "--check" in sys.argv


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    assert "\r" not in text, "意外的 CR：%s" % path
    assert text.endswith("\n"), "文件不以换行结尾：%s" % path
    lines = text.split("\n")[:-1]
    assert all(ln != "" for ln in lines), "存在空行：%s" % path
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]]


def atomic_write(path, hdr, rows):
    text = "\t".join(hdr) + "\n" + "\n".join("\t".join(r) for r in rows) + "\n"
    tmp = path + ".tmp_w11g_schema"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def main():
    if not CHECK_ONLY:
        os.makedirs(BACKUP, exist_ok=True)
    summary = {}
    for fn, big, subcol, expect in SHEETS:
        p = os.path.join(UNI, fn)
        hdr, rows = read_tsv(p)
        ncol = {len(r) for r in rows}
        assert len(ncol) == 1 and len(hdr) == ncol.pop(), "列数不一致：%s" % fn

        if subcol in hdr:
            # 已迁移 —— 幂等分支：只校验
            ix = {c: i for i, c in enumerate(hdr)}
            cats = {r[ix["类别"]] for r in rows}
            subs = {}
            for r in rows:
                subs[r[ix[subcol]]] = subs.get(r[ix[subcol]], 0) + 1
            assert cats == {big}, "%s 的 `类别` 非纯大类：%s" % (fn, sorted(cats))
            # 幂等分支只校验「取值在允许枚举内」（子集）——W12 判读后 `未识别` / `未判定` 已归零，
            # 若此处仍要求「全等」，本脚本会在 W12 之后**必然误报**（2026-09-19 W13 实测发现并修正）。
            assert set(subs) <= expect, "%s 的 `%s` 取值越界（允许 %s）：%s" % (
                fn, subcol, sorted(expect), sorted(subs))
            summary[fn] = {"状态": "已迁移（跳过写盘）", "行数": len(rows), "子分类": subs,
                           "缺失子分类": sorted(expect - set(subs))}
            print("[SKIP] %-20s 已含 `%s`，%d 行，子分类 %s" % (fn, subcol, len(rows),
                                                              " / ".join("%s %d" % (k, v) for k, v in sorted(subs.items()))))
            continue

        ix = {c: i for i, c in enumerate(hdr)}
        assert "类别" in ix, "%s 缺 `类别` 列" % fn
        ci = ix["类别"]
        subs = {}
        for r in rows:
            subs[r[ci]] = subs.get(r[ci], 0) + 1
        assert set(subs) == expect, "%s 的 `类别` 取值与预期不符：%s" % (fn, sorted(subs))

        if CHECK_ONLY:
            summary[fn] = {"状态": "待迁移（--check 未写盘）", "行数": len(rows), "子分类": subs}
            print("[CHECK] %-20s 待迁移：%d 行，类别 %s" % (fn, len(rows),
                                                          " / ".join("%s %d" % (k, v) for k, v in sorted(subs.items()))))
            continue

        # 备份 → 迁移 → 原子写
        shutil.copyfile(p, os.path.join(BACKUP, fn))
        new_hdr = hdr[:ci + 1] + [subcol] + hdr[ci + 1:]
        new_rows = []
        for r in rows:
            sub = r[ci]
            new_rows.append(r[:ci] + [big, sub] + r[ci + 1:])
        assert len(new_rows) == len(rows)
        assert all(len(r) == len(new_hdr) for r in new_rows)
        atomic_write(p, new_hdr, new_rows)
        summary[fn] = {"状态": "已迁移", "行数": len(rows), "子分类": subs}
        print("[OK]   %-20s %d 行：`类别` -> %s（纯大类），新增 `%s` = %s"
              % (fn, len(rows), big, subcol,
                 " / ".join("%s %d" % (k, v) for k, v in sorted(subs.items()))))

    print("\n新表头：")
    for fn, _, _, _ in SHEETS:
        hdr, _ = read_tsv(os.path.join(UNI, fn))
        print("  %-20s %s" % (fn, " | ".join(hdr)))
    if not CHECK_ONLY:
        print("\n备份：%s" % BACKUP)


if __name__ == "__main__":
    main()