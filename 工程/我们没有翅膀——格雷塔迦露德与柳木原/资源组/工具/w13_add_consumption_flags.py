# -*- coding: utf-8 -*-
"""W13 · 交付清单「消费侧标记列」+ 两处清单缺陷修复（2026-09-19）。

本脚本只做**列/字段级的加法**，不动任何 PNG、不动任何既有单元格内容：

  1. `美术统一\\交付清单.tsv` / `清单_立绘.tsv` / `清单_CG背景.tsv` / `清单_系统UI.tsv`
     / `美术统一_超分\\超分清单.tsv`
     —— 新增 `图片化日文` 列（放在 `判读类别` 右侧；`超分清单` 无该列故放 `类别` 右侧）。
     取值 `是` / 空。判据（**必须限定 `类别 == "CG背景"`**）：
         `类别 == "CG背景"` 且（`统一名` 匹配 `^cit` 或 `^sr2_t` 或 `== "end_staff.png"`）
     实测 = 42 件（`cit` 34 + `sr2_t` 7 + `end_staff` 1）。
     ⚠ **朴素 `^cit` 过滤（不限类别）会多纳 15 件真立绘**（`cit001` / `cit01a`–`cit01n`，
     它们留在 `立绘\\`），故 `类别` 限定是**语义必需**，不是保险措施。

  2. `清单_CG背景.tsv` / `交付清单.tsv` —— 追加 `分片角色` 列（取值 `分片成员` / `独立`）。
     判据：`清单_CG背景.tsv` 的 `组名` 非空 → `分片成员`（实测 48 件 = 6 组 × 8 片）。
     ⚠ 前缀遍历陷阱：`bg06c.png` / `bg07c.png` 是 **800×600 独立背景、不是切片**
     （`组名` 为空），按 `^bg06` / `^bg07` 前缀遍历会把它们误当第 9 片。
     正确取法：`awk -F'\\t' '$分片角色=="分片成员"'`。

  3. `美术\\分片背景.tsv` —— **只补第 9 列表头** `系列类型`（数据 658 行本就是 9 列，
     表头只有 8 列 → 按表头解析会错位丢列）。数据一字不动。

  4. `美术统一\\待复核_立绘.tsv` —— 32 行 `统一名` 缺 `.png` 后缀（如 `asu_b03s`），
     按名 join 主清单会失败 → 补全后缀。其余两表（`待复核_CG背景` / `待复核_系统UI`）
     实测无此问题，不动。

幂等：列/后缀已存在时**只校验、不写盘**（`--check` 亦然，绝不写盘）。
用法：
    set PYTHONPATH=E:\\ZCode Workspace\\Galgame\\工具\\pylibs
    python w13_add_consumption_flags.py            # 执行（幂等）
    python w13_add_consumption_flags.py --check    # 只校验，不写盘
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))          # <游戏工程目录>
UNI = os.path.join(PROJ, "资源组", "美术统一")
SUP = os.path.join(PROJ, "资源组", "美术统一_超分")
ART = os.path.join(PROJ, "资源组", "美术")
assert os.path.isdir(UNI), UNI

COL_JP = "图片化日文"
COL_SPLIT = "分片角色"
SPLIT_MEMBER = "分片成员"
SPLIT_STANDALONE = "独立"

CHECK_ONLY = "--check" in sys.argv

JP_CIT = re.compile(r"^cit")
JP_SR2T = re.compile(r"^sr2_t")
JP_END = "end_staff.png"


def read_tsv(path):
    """返回 (header_list, rows_list_of_list, eol)。保留原行尾风格。"""
    raw = open(path, "rb").read()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    assert text.endswith(eol), "文件不以换行结尾：%s" % path
    lines = text.split(eol)[:-1]
    assert all(ln != "" for ln in lines), "存在空行：%s" % path
    return lines[0].split("\t"), [ln.split("\t") for ln in lines[1:]], eol


def atomic_write(path, hdr, rows, eol):
    tmp = path + ".tmp_w13"
    with open(tmp, "wb") as f:
        f.write(eol.join(["\t".join(hdr)] + ["\t".join(r) for r in rows]).encode("utf-8"))
        f.write(eol.encode("utf-8"))
    os.replace(tmp, path)


def is_jp_pict(cat, name):
    """图片化日文判据：必须限定类别 == CG背景。"""
    return cat == "CG背景" and bool(JP_CIT.match(name) or JP_SR2T.match(name) or name == JP_END)


# ---------------------------------------------------------------- 1) 交付清单
def add_jp_column(path, after, rows_key, report):
    hdr, rows, eol = read_tsv(path)
    assert len(hdr) == len(rows[0]), "表头/数据列数不符：%s" % path
    if COL_JP in hdr:
        i = hdr.index(COL_JP)
        bad = 0
        for r in rows:
            cat, name = rows_key(hdr, r)
            if r[i] != ("是" if is_jp_pict(cat, name) else ""):
                bad += 1
        n = sum(1 for r in rows if r[i] == "是")
        if bad == 0:
            report.append("[SKIP] %s 已含 `%s`（%d 行，是=%d，校验一致）"
                          % (os.path.basename(path), COL_JP, len(rows), n))
            return hdr, rows, eol, i
        for r in rows:
            cat, name = rows_key(hdr, r)
            r[i] = "是" if is_jp_pict(cat, name) else ""
        if not CHECK_ONLY:
            atomic_write(path, hdr, rows, eol)
        report.append("[FIX]  %s `%s` 重算（%d 行，是=%d，原错 %d 处）"
                      % (os.path.basename(path), COL_JP, len(rows), n, bad))
        return hdr, rows, eol, i
    assert after in hdr, "%s 缺定位列 `%s`" % (path, after)
    pos = hdr.index(after) + 1
    new_hdr = hdr[:pos] + [COL_JP] + hdr[pos:]
    new_rows = []
    n = 0
    for r in rows:
        cat, name = rows_key(hdr, r)
        v = "是" if is_jp_pict(cat, name) else ""
        if v:
            n += 1
        new_rows.append(r[:pos] + [v] + r[pos:])
    assert all(len(r) == len(new_hdr) for r in new_rows)
    if not CHECK_ONLY:
        atomic_write(path, new_hdr, new_rows, eol)
    report.append("[OK]   %s +`%s`（%d 行，是=%d）" % (os.path.basename(path), COL_JP, len(new_rows), n))
    return new_hdr, new_rows, eol, pos


def add_split_column(path, hdr, rows, eol, report, name_idx):
    gi = hdr.index("组名") if "组名" in hdr else None

    def expect(r):
        if gi is not None:
            return SPLIT_MEMBER if r[gi] != "" else SPLIT_STANDALONE
        return SPLIT_MEMBER if r[name_idx] in SLICE_NAMES else SPLIT_STANDALONE

    if COL_SPLIT in hdr:
        i = hdr.index(COL_SPLIT)
        bad = sum(1 for r in rows if r[i] != expect(r))
        n = sum(1 for r in rows if r[i] == SPLIT_MEMBER)
        if bad == 0:
            report.append("[SKIP] %s 已含 `%s`（%d 行，分片成员=%d，校验一致）"
                          % (os.path.basename(path), COL_SPLIT, len(rows), n))
            return hdr, rows, eol, i
        for r in rows:
            r[i] = expect(r)
        if not CHECK_ONLY:
            atomic_write(path, hdr, rows, eol)
        report.append("[FIX]  %s `%s` 重算（%d 行，分片成员=%d，原错 %d 处）"
                      % (os.path.basename(path), COL_SPLIT, len(rows), n, bad))
        return hdr, rows, eol, i
    new_hdr = hdr + [COL_SPLIT]
    new_rows = []
    n = 0
    for r in rows:
        v = expect(r)
        if v == SPLIT_MEMBER:
            n += 1
        new_rows.append(r + [v])
    assert all(len(r) == len(new_hdr) for r in new_rows)
    if not CHECK_ONLY:
        atomic_write(path, new_hdr, new_rows, eol)
    report.append("[OK]   %s +`%s`（%d 行，分片成员=%d）" % (os.path.basename(path), COL_SPLIT, len(new_rows), n))
    return new_hdr, new_rows, eol, len(new_hdr) - 1


def main():
    report = []

    # 分片成员名单（来源：清单_CG背景 的 `组名` 非空）—— 必须在改写前读出
    cg_hdr, cg_rows, cg_eol = read_tsv(os.path.join(UNI, "清单_CG背景.tsv"))
    gi = cg_hdr.index("组名")
    ni = cg_hdr.index("统一名")
    global SLICE_NAMES
    SLICE_NAMES = {r[ni] for r in cg_rows if r[gi] != ""}
    assert len(SLICE_NAMES) == 48, "分片成员应为 48，实测 %d" % len(SLICE_NAMES)
    report.append("[BASE] 分片成员名单 = %d 件（来自 `清单_CG背景.tsv` 的 `组名` 非空行）" % len(SLICE_NAMES))

    def key_cat_name(hdr, r):
        return r[hdr.index("类别")], r[hdr.index("统一名")]

    def key_name_cat(hdr, r):
        return r[hdr.index("类别")], r[hdr.index("统一名")]

    # 1) 三张分表
    add_jp_column(os.path.join(UNI, "清单_立绘.tsv"), "判读类别", key_name_cat, report)
    h2, r2, e2, _ = add_jp_column(os.path.join(UNI, "清单_CG背景.tsv"), "判读类别", key_name_cat, report)
    add_jp_column(os.path.join(UNI, "清单_系统UI.tsv"), "判读类别", key_name_cat, report)

    # 2) 分片角色（清单_CG背景）
    add_split_column(os.path.join(UNI, "清单_CG背景.tsv"), h2, r2, e2, report, h2.index("统一名"))

    # 3) 交付清单
    dh, dr, de, _ = add_jp_column(os.path.join(UNI, "交付清单.tsv"), "判读类别", key_cat_name, report)
    add_split_column(os.path.join(UNI, "交付清单.tsv"), dh, dr, de, report, dh.index("统一名"))

    # 4) 超分清单（无 `判读类别`，放 `类别` 右侧，与交付清单相对次序一致）
    add_jp_column(os.path.join(SUP, "超分清单.tsv"), "类别", key_cat_name, report)

    # 5) 待复核_立绘 补 .png 后缀
    p = os.path.join(UNI, "待复核_立绘.tsv")
    hdr, rows, eol = read_tsv(p)
    ci = hdr.index("统一名")
    fixed = [r for r in rows if not r[ci].endswith(".png")]
    if not fixed:
        report.append("[SKIP] 待复核_立绘.tsv 无缺后缀行")
    else:
        if not CHECK_ONLY:
            for r in rows:
                if not r[ci].endswith(".png"):
                    r[ci] = r[ci] + ".png"
            atomic_write(p, hdr, rows, eol)
        report.append("[OK]   待复核_立绘.tsv 补 `.png` 后缀 %d 行" % len(fixed))
    for other in ("待复核_CG背景.tsv", "待复核_系统UI.tsv"):
        h, rr, _ = read_tsv(os.path.join(UNI, other))
        c = h.index("统一名")
        bad = [r[c] for r in rr if not r[c].endswith(".png")]
        report.append("[CHK]  %s 缺后缀 %d 行%s" % (other, len(bad), (" -> " + ",".join(bad[:5])) if bad else ""))

    # 6) 分片背景.tsv 表头补第 9 列
    p = os.path.join(ART, "分片背景.tsv")
    hdr, rows, eol = read_tsv(p)
    ncols = {len(r) for r in rows}
    assert len(ncols) == 1, "分片背景.tsv 数据列数不一致：%s" % sorted(ncols)
    nd = ncols.pop()
    if len(hdr) == nd:
        report.append("[SKIP] 分片背景.tsv 表头已与数据同列数（%d）" % nd)
    else:
        assert len(hdr) == 8 and nd == 9, "分片背景.tsv 意外列数：表头 %d / 数据 %d" % (len(hdr), nd)
        hdr = hdr + ["系列类型"]
        if not CHECK_ONLY:
            atomic_write(p, hdr, rows, eol)
        report.append("[OK]   分片背景.tsv 表头补 `系列类型`（表头 8 -> 9，数据 658 行 9 列未动）")

    print("\n".join(report))
    print("\n--check 模式：未写盘" if CHECK_ONLY else "\n已写盘（原子替换）")


if __name__ == "__main__":
    main()