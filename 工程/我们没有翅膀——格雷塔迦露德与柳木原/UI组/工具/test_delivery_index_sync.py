#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付总纲数字闸门 —— `UI组/UI组_交付总纲.md` 里的数字必须与磁盘真值一致。

为什么需要它：`UI组_交付总纲.md` 是给别人读的「口径副本」，里面写着
资源族件数/字节、逐屏元素数、三处产物 md5、素材预算余量。**凡人读的口径副本
必须有闸门断言它与机器真值一致**（本工程既有通例：凡人读的口径副本必须有闸门盯着，否则会静默过期）；
否则它会静默过期，读者按旧数办事。

用法
  python 工具/test_delivery_index_sync.py            # 校验（退出码 0＝一致，1＝不一致，2＝环境错）
  python 工具/test_delivery_index_sync.py --report   # 只打印磁盘真值（写文档时用）
  python 工具/test_delivery_index_sync.py --selfcheck # 变异自证：把解析值改坏必须报不一致

闸门范围：只校验文档里被 `<!-- GATE:<name> -->` … `<!-- /GATE:<name> -->` 包住的那几张表
（可见表格即真值副本），不校验散文。
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)                       # …\UI组

DOC = os.path.join(UI, "UI组_交付总纲.md")
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
FACE = os.path.join(UI, "krkr", "assets", "face")
SCREENS = os.path.join(UI, "layout", "screens")
VERIFY_UI = os.path.join(HERE, "verify_ui.py")

PRODUCTS = [
    ("layout/ui_layout.json", os.path.join(UI, "layout", "ui_layout.json")),
    ("krkr/game/ui_layout.tjs", os.path.join(UI, "krkr", "game", "ui_layout.tjs")),
    ("复刻/ui_layout.js", os.path.join(UI, "复刻", "ui_layout.js")),
]

# 资源族：**有序**、最长前缀优先；末尾用「未归类」兜底并断言为 0
# （新增任何前缀族而不登记 ⇒ 本闸门立刻报「未归类件数 > 0」，不会静默漏算）
FAMILIES = [
    ("x_gal", "x_gal", "CG 鉴赏缩略图（程序化生成，703 件）"),
    ("x_ui", "x_ui", "通用 UI 件（面板/按钮/图标/PSV 换皮/配置/回想/鉴赏/快捷条…）"),
    ("x_mask", "x_mask", "转场遮罩（`_full`＝满幅 1920×1080；`_1x`＝旧 4:3 内容区 1440×816——D-04 后已无对应框，18 件休眠无消费方）"),
    ("x_gen", "x_gen", "AI 生图/派生整页件（对话框无框前素材、番外/鉴赏整页、logo）"),
    ("x_bg", "x_bg", "满幅背景（`x_bg_system` / `x_bg_flowchart`）"),
    ("tl2", "tl2", "标题底（历史族）"),
    ("panel_frame.png", "panel_frame.png", "九宫格边框（由 `if_*` 八件拼合，无前缀）"),
]


def md5_of(path):
    r"""盘面文件 md5 —— **★ LF 规范化**（先把 `\r\n` 折成 `\n`）后再算。

    为什么必须规范化（本工程已踩第三次）：仓库 `core.autocrlf=true` ⇒ **同一份 blob**
    在不同 worktree、或同一 worktree 在「生成器写过 LF」与「git 检出成 CRLF」两种状态下，
    落盘字节不同；按原始字节算 md5 会让**同一份内容得到两个 md5**
    ⇒ 「人读口径副本 vs 磁盘真值」这类闸门在**换检出面**时报**假失败**
    （前两次：`m06` 总账、总纲数字闸门；第三次：2026-10-01 `ISSUE-20261001-11` 合并后
      主工作树上的 `交付包校验收据` 闸门 —— `ui_flow_data.tjs` / `gen_flow_layout.py`
      在工作树里是 LF、主工作树检出成 CRLF）。
    """
    with open(path, "rb") as fh:
        data = fh.read().replace(b"\r\n", b"\n")
    return hashlib.md5(data).hexdigest()


def scan_tree(root):
    """返回 (文件数, 总字节, [(相对名, 字节)])；目录不存在则抛错。"""
    if not os.path.isdir(root):
        raise RuntimeError("目录不存在：%s" % root)
    names = []
    total = 0
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            size = os.path.getsize(fp)
            total += size
            names.append((os.path.relpath(fp, root).replace("\\", "/"), size))
    return len(names), total, names


def disk_families():
    count, total, names = scan_tree(ASSETS)
    rows = []
    claimed = set()
    for label, prefix, _use in FAMILIES:
        files = [(n, s) for n, s in names if n.startswith(prefix)]
        for n, _s in files:
            claimed.add(n)
        rows.append((label, len(files), sum(s for _n, s in files)))
    orphans = [n for n, _s in names if n not in claimed]
    return rows, count, total, orphans


def disk_screens():
    rows = []
    total = 0
    for fn in sorted(os.listdir(SCREENS)):
        if not fn.endswith(".json") or fn == "_index.json":
            continue
        with open(os.path.join(SCREENS, fn), encoding="utf-8") as fh:
            data = json.load(fh)
        n = len(data.get("elements", []))
        rows.append((data.get("id", ""), fn, n))
        total += n
    return rows, total


def disk_face():
    count, total, _names = scan_tree(FACE)
    return count, total


def disk_budget():
    """预算从 `verify_ui.py` 的 DEF_BUDGET_MB 取（单一来源）；取不到就报错，不用默认值。"""
    src = open(VERIFY_UI, encoding="utf-8").read()
    m = re.search(r"^DEF_BUDGET_MB\s*=\s*([0-9.]+)", src, re.M)
    if not m:
        raise RuntimeError("在 %s 里找不到 DEF_BUDGET_MB（常量改名了？请同改本闸门）" % VERIFY_UI)
    budget_bytes = int(float(m.group(1)) * 1024 * 1024)
    _c, used, _n = scan_tree(ASSETS)
    return int(float(m.group(1))), used, budget_bytes - used


# ── 文档解析 ────────────────────────────────────────────────────────────────
def read_doc():
    if not os.path.isfile(DOC):
        raise RuntimeError("总纲不存在：%s" % DOC)
    with open(DOC, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def block(text, name):
    m = re.search(r"<!-- GATE:%s -->(.*?)<!-- /GATE:%s -->" % (name, name), text, re.S)
    if not m:
        raise RuntimeError("总纲里找不到闸门块 <!-- GATE:%s -->" % name)
    return m.group(1)


def table_rows(chunk):
    """取 markdown 表的数据行（跳过表头与分隔行），返回 [[cell,...]]。"""
    rows = []
    for line in chunk.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def num(s):
    return int(re.sub(r"[^0-9]", "", s) or "0")


def data_rows(chunk):
    """取 markdown 表的数据行（**丢掉表头**，跳过分隔行）。"""
    rows = table_rows(chunk)
    return rows[1:] if rows else rows


def kv_rows(chunk):
    """把 `| 键 | 值 |` 两列表读成 dict（值为数字，去掉千分位）。"""
    out = {}
    for cells in data_rows(chunk):
        if len(cells) >= 2:
            out[cells[0]] = num(cells[1])
    return out


def doc_families(text):
    rows = []
    for cells in data_rows(block(text, "asset_families")):
        if cells[0] == "合计":
            return rows, num(cells[1]), num(cells[2])
        rows.append((cells[0], num(cells[1]), num(cells[2])))
    raise RuntimeError("asset_families 表缺「合计」行")


def doc_face(text):
    kv = kv_rows(block(text, "face_set"))
    return kv["件数"], kv["字节"]


def doc_screens(text):
    rows = []
    for cells in data_rows(block(text, "screen_elements")):
        if cells[0] == "合计":
            return rows, num(cells[-1])
        rows.append((cells[0], cells[1].strip("`"), num(cells[-1])))
    raise RuntimeError("screen_elements 表缺「合计」行")


def doc_products(text):
    out = []
    for cells in data_rows(block(text, "products")):
        out.append((cells[0].strip("`"), cells[1].strip("`")))
    return out


def doc_budget(text):
    kv = kv_rows(block(text, "budget"))
    return kv["预算（MB）"], kv["余量（字节）"]


# ── 校验 ────────────────────────────────────────────────────────────────────
def collect(mutate=None):
    """把「文档声明」与「磁盘真值」两套值收集起来；mutate 用于变异自证。"""
    text = read_doc()
    f_rows, f_cnt, f_bytes, f_orphan = disk_families()
    s_rows, s_total = disk_screens()
    fa_cnt, fa_bytes = disk_face()
    p_rows = [(rel, md5_of(path)) for rel, path in PRODUCTS]
    b_mb, b_used, b_left = disk_budget()

    checks = []
    d_rows, d_cnt, d_bytes = doc_families(text)
    checks.append(("资源族件数合计", d_cnt, f_cnt))
    checks.append(("资源族字节合计", d_bytes, f_bytes))
    checks.append(("未归类文件数", 0, len(f_orphan)))
    for (lab, dc, db), (slab, sc, sb) in zip(d_rows, f_rows):
        checks.append(("族 %s 件数" % lab, dc, sc))
        checks.append(("族 %s 字节" % lab, db, sb))
    checks.append(("族行数", len(d_rows), len(f_rows)))

    ds_rows, ds_total = doc_screens(text)
    checks.append(("逐屏行数", len(ds_rows), len(s_rows)))
    checks.append(("逐屏元素合计", ds_total, s_total))
    for (dfn, did, dn), (sfn, sid, sn) in zip(ds_rows, s_rows):
        checks.append(("屏 %s 文件名" % dfn, dfn, sfn))
        checks.append(("屏 %s 件数" % dfn, dn, sn))

    dfa = doc_face(text)
    checks.append(("头像集件数", dfa[0], fa_cnt))
    checks.append(("头像集字节", dfa[1], fa_bytes))

    dp = doc_products(text)
    checks.append(("产物行数", len(dp), len(p_rows)))
    for (drel, dmd5), (srel, smd5) in zip(dp, p_rows):
        checks.append(("产物 %s 路径" % drel, drel, srel))
        checks.append(("产物 %s md5" % drel, dmd5.lower(), smd5.lower()))

    dmb, dleft = doc_budget(text)
    checks.append(("预算 MB", dmb, b_mb))
    checks.append(("预算余量字节", dleft, b_left))

    if mutate:
        checks = [(n, mutate(v) if n == mutate_key else v, s) for n, v, s in checks]

    bad = [(n, d, s) for n, d, s in checks if d != s]
    return checks, bad, dict(
        families=f_rows, families_total=(f_cnt, f_bytes), orphans=f_orphan,
        screens=s_rows, screens_total=s_total, face=(fa_cnt, fa_bytes),
        products=p_rows, budget=(b_mb, b_used, b_left),
    )


mutate_key = None


def disk_info():
    """只读磁盘真值（不读总纲）——写文档与 --report 用。"""
    f_rows, f_cnt, f_bytes, f_orphan = disk_families()
    s_rows, s_total = disk_screens()
    fa_cnt, fa_bytes = disk_face()
    p_rows = [(rel, md5_of(path)) for rel, path in PRODUCTS]
    b_mb, b_used, b_left = disk_budget()
    return dict(
        families=f_rows, families_total=(f_cnt, f_bytes), orphans=f_orphan,
        screens=s_rows, screens_total=s_total, face=(fa_cnt, fa_bytes),
        products=p_rows, budget=(b_mb, b_used, b_left),
    )


def main():
    global mutate_key
    argv = sys.argv[1:]
    if "--report" in argv:
        info = disk_info()
        print("=== 资源族（磁盘真值）===")
        for lab, c, b in info["families"]:
            print("| %s | %s | %s |" % (lab, format(c, ","), format(b, ",")))
        print("| 合计 | %s | %s |" % (format(info["families_total"][0], ","),
                                      format(info["families_total"][1], ",")))
        print("未归类：%d" % len(info["orphans"]))
        print("\n=== 逐屏（磁盘真值）===")
        for fn, sid, n in info["screens"]:
            print("| %s | %s | %s |" % (sid, fn, n))
        print("合计 %d" % info["screens_total"])
        print("\n=== 三处产物 ===")
        for rel, h in info["products"]:
            print("| %s | %s |" % (rel, h))
        print("\n=== 头像集 / 预算 ===")
        print("face 件数 %s 字节 %s" % info["face"])
        print("预算 %s MB ｜ 实测 %s B ｜ 余量 %s B" % info["budget"])
        return 0

    if "--selfcheck" in argv:
        # 变异自证：把「资源族件数合计」改坏 1，闸门必须报不一致（证明它真在校验）
        mutate_key = "资源族件数合计"
        _checks, bad, _info = collect(mutate=lambda v: v + 1)
        hit = [n for n, _d, _s in bad if n == mutate_key]
        print("[selfcheck] 变异「%s」⇒ 不一致条目 %d 条（命中 %d）" % (mutate_key, len(bad), len(hit)))
        if not info_ok(hit, bad):
            return 1
        # 再证「不改就一致」
        _c2, bad2, _i2 = collect()
        print("[selfcheck] 未变异 ⇒ 不一致条目 %d 条（应为 0）" % len(bad2))
        return 0 if not bad2 else 1
    try:
        checks, bad, _info = collect()
    except Exception as exc:                                  # noqa: BLE001
        print("环境错误：%s" % exc)
        return 2
    print("=== 交付总纲数字闸门（%d 项断言）===" % len(checks))
    for name, d, s in checks:
        flag = "OK  " if d == s else "FAIL"
        if flag == "FAIL":
            print("  %s %s：总纲写 %r ｜ 磁盘 %r" % (flag, name, d, s))
    print("------------------------------------------------------------------------------")
    print("结果：%s（不一致 %d 项）" % ("**全部通过**" if not bad else "**失败**", len(bad)))
    return 0 if not bad else 1


def info_ok(hit, bad):
    return bool(hit) and len(bad) >= 1


if __name__ == "__main__":
    sys.exit(main())
