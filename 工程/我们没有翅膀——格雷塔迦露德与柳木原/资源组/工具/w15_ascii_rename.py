# -*- coding: utf-8 -*-
r"""W15 · 统一产物名 ASCII 化（只改名，不改像素）

背景
----
`美术统一\系统UI\` 下有 10 个**含中文**的文件名（非 ASCII），来自 W11d 的 `ss_bg1`–`ss_bg5`
粒度拆分（`_底板` = 场景选择底板 / `_整页` = 含日期列表的整页）。
非 ASCII 路径在旧引擎字串表、部分打包器、GBK/UTF-8 编码边界与 260 字符路径限制下可能异常
（详见 `美术统一\统一说明_系统UI.md` §十七、`美术统一_规格.md` §2.5）。

用户 2026-09-19 裁决：**统一产物名一律 ASCII**，故本脚本把这两个中缀改为 ASCII：

    _底板 -> _base
    _整页 -> _full

规则（唯一口径）
----------------
1. 只处理 `美术统一\{立绘,CG背景,系统UI}\` 与 `美术统一_超分\{立绘,CG背景,系统UI}\` 六个目录；
2. 只对**basename 含非 ASCII 字符**的文件施加替换表（其余文件名一字不动）；
3. **两侧同步**：`美术统一_超分\` 是 `美术统一\` 的超分产物，两侧文件名必须逐字节一致，
   故同一条重命名在两侧各执行一次；
4. **只改名、不改像素**：每个文件改名前后各算一次 md5，不一致立即中止（非零退出）；
5. **目标名占用即中止**：若目标名已被同目录既有文件占用（且该文件不是本次的改名源），
   报错退出，绝不覆盖；
6. **幂等**：已 ASCII 化的目录再跑，命中 0 件、写盘 0 次；
7. **清单同步**：把 `统一名` 列里等于旧名的单元格改成新名，**其余列一字不动**。
   涉及 `美术统一\交付清单.tsv`、`美术统一\清单_系统UI.tsv`、`美术统一\待复核_系统UI.tsv`、
   `美术统一_超分\超分清单.tsv`（四份均含 `统一名` 列）。

用法
----
    # 只校验不写盘（列出待改名件、撞名、md5）
    python w15_ascii_rename.py --check

    # 执行（幂等）
    python w15_ascii_rename.py

    # 素材在别处（例：本脚本所在 worktree 无 PNG，素材在主工作树）
    python w15_ascii_rename.py \
        --assets-root   "E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组" \
        --manifest-root "E:/ZCode Workspace/Galgame/临时/wt-19-07/工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组"

    # 追加机器可读报告
    python w15_ascii_rename.py --report 临时/w15_报告.tsv

退出码
------
    0 = 成功（含 --check 且无待处理项 / 有待处理项）
    1 = 撞名、规则未命中、md5 前后不一致、清单列缺失等硬错误
    2 = 参数错误
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# ── 规则表 ────────────────────────────────────────────────────────────────────
RENAME_RULES: list[tuple[str, str]] = [
    ("_底板", "_base"),
    ("_整页", "_full"),
]

SIDES = ("美术统一", "美术统一_超分")
KINDS = ("立绘", "CG背景", "系统UI")

# 需要同步 `统一名` 列的清单（相对 manifest-root）
MANIFESTS = (
    ("美术统一", "交付清单.tsv"),
    ("美术统一", "清单_系统UI.tsv"),
    ("美术统一", "待复核_系统UI.tsv"),
    ("美术统一_超分", "超分清单.tsv"),
)
NAME_COLUMN = "统一名"


def is_ascii(s: str) -> bool:
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def new_name(name: str) -> str:
    """施加替换表。未命中任何规则时返回原样（由调用方判定为「规则未命中」）。"""
    out = name
    for old, new in RENAME_RULES:
        out = out.replace(old, new)
    return out


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(assets_root: Path) -> tuple[dict, list[str]]:
    """返回 ({(side,kind): [文件名...]}, 问题清单)。只读。"""
    listing: dict[tuple[str, str], list[str]] = {}
    problems: list[str] = []
    for side in SIDES:
        for kind in KINDS:
            d = assets_root / side / kind
            if not d.is_dir():
                problems.append(f"[缺目录] {d}")
                listing[(side, kind)] = []
                continue
            listing[(side, kind)] = sorted(p.name for p in d.iterdir() if p.is_file())
    return listing, problems


def plan(listing: dict) -> tuple[list[dict], list[str]]:
    """算出改名计划 + 撞名/未命中问题。只读。"""
    plan_items: list[dict] = []
    problems: list[str] = []
    for (side, kind), names in listing.items():
        nameset = set(names)
        sources = {n for n in names if not is_ascii(n)}   # 本次会被改走的旧名
        targets: dict[str, str] = {}
        for n in names:
            if is_ascii(n):
                continue
            t = new_name(n)
            if t == n:
                problems.append(f"[规则未命中] {side}/{kind}/{n}（含非 ASCII 但不在替换表内）")
                continue
            if t in nameset and t not in sources:
                problems.append(f"[撞名] {side}/{kind}/{n} -> {t}：目标名已被既有文件占用")
                continue
            if t in targets:
                problems.append(f"[撞名] {side}/{kind}: {n} 与 {targets[t]} 都指向 {t}")
                continue
            targets[t] = n
            plan_items.append({"side": side, "kind": kind, "old": n, "new": t})
    return plan_items, problems


def check_side_parity(listing: dict) -> list[str]:
    """两侧文件名集合逐字节一致（只读校验）。"""
    problems: list[str] = []
    for kind in KINDS:
        a = set(listing.get(("美术统一", kind), []))
        b = set(listing.get(("美术统一_超分", kind), []))
        if a != b:
            problems.append(
                f"[两侧不一致] {kind}: 仅美术统一 {len(a - b)} 件 / 仅超分 {len(b - a)} 件"
            )
    return problems


def do_rename(items: list[dict], assets_root: Path) -> list[dict]:
    """执行改名（逐件 md5 前后比对，不一致即中止）。返回带 md5 的记录。"""
    records: list[dict] = []
    for it in items:
        src = assets_root / it["side"] / it["kind"] / it["old"]
        dst = assets_root / it["side"] / it["kind"] / it["new"]
        if not src.exists():
            raise RuntimeError(f"源不存在：{src}")
        if dst.exists():
            raise RuntimeError(f"目标已存在，拒绝覆盖：{dst}")
        before = md5_file(src)
        os.replace(src, dst)          # 同目录改名，原子
        after = md5_file(dst)
        if before != after:
            raise RuntimeError(
                f"md5 前后不一致（已改名，需人工回滚）：{src.name} -> {dst.name} "
                f"before={before} after={after}"
            )
        rec = dict(it)
        rec.update({"md5_before": before, "md5_after": after, "ok": True})
        records.append(rec)
        print(f"  [改名] {it['side']}/{it['kind']}: {it['old']} -> {it['new']}  md5={before}")
    return records


def sync_manifests(manifest_root: Path, mapping: dict[str, str], apply: bool) -> tuple[int, list[str]]:
    """把四份清单 `统一名` 列里等于旧名的单元格改成新名，其余列一字不动。

    返回 (改动单元格数, 问题清单)。apply=False 时只统计不写盘。
    """
    changed = 0
    problems: list[str] = []
    for side, rel in MANIFESTS:
        path = manifest_root / side / rel
        if not path.exists():
            problems.append(f"[清单缺失] {path}")
            continue
        raw = path.read_bytes()
        # 保留原始行尾：以 bytes 切行
        lines = raw.split(b"\n")
        header = lines[0].decode("utf-8").rstrip("\r").split("\t")
        if NAME_COLUMN not in header:
            problems.append(f"[无 {NAME_COLUMN} 列] {path}")
            continue
        idx = header.index(NAME_COLUMN)
        out_lines = [lines[0]]
        for ln in lines[1:]:
            if not ln:
                out_lines.append(ln)
                continue
            cr = b"\r" if ln.endswith(b"\r") else b""
            body = ln[:-1] if cr else ln
            cells = body.decode("utf-8").split("\t")
            if idx < len(cells) and cells[idx] in mapping:
                cells[idx] = mapping[cells[idx]]
                changed += 1
                out_lines.append("\t".join(cells).encode("utf-8") + cr)
            else:
                out_lines.append(ln)
        new_raw = b"\n".join(out_lines)
        if new_raw != raw:
            if apply:
                path.write_bytes(new_raw)
            print(f"  [清单] {side}/{rel}: {NAME_COLUMN} 列改动")
        else:
            print(f"  [清单] {side}/{rel}: 无改动（已同步）")
    return changed, problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description="W15 · 统一产物名 ASCII 化（_底板->_base / _整页->_full），只改名不改像素"
    )
    ap.add_argument("--check", action="store_true", help="只校验不写盘")
    ap.add_argument("--assets-root", type=Path, default=None,
                    help="含 美术统一\\ 与 美术统一_超分\\ 的资源组目录（默认=脚本所在目录的上一级）")
    ap.add_argument("--manifest-root", type=Path, default=None,
                    help="含四份清单的资源组目录（默认=与 --assets-root 相同）")
    ap.add_argument("--no-manifest", action="store_true", help="不同步清单，只改名")
    ap.add_argument("--report", type=Path, default=None, help="把逐件记录写成 TSV")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent          # …\资源组\工具\
    default_root = here.parent                      # …\资源组\
    assets_root = (args.assets_root or default_root).resolve()
    manifest_root = (args.manifest_root or assets_root).resolve()

    print(f"[W15] 模式 = {'check（只校验）' if args.check else 'apply（写盘）'}")
    print(f"[W15] assets-root   = {assets_root}")
    print(f"[W15] manifest-root = {manifest_root}")
    print()

    listing, problems = scan(assets_root)
    print("── 1. 六目录计数 ──")
    for side in SIDES:
        tot = 0
        for kind in KINDS:
            n = len(listing[(side, kind)])
            tot += n
            print(f"   {side}/{kind}: {n}")
        print(f"   {side} 合计: {tot}")

    print()
    print("── 2. 非 ASCII 文件名（改前） ──")
    n_bad = 0
    for (side, kind), names in listing.items():
        bad = [n for n in names if not is_ascii(n)]
        n_bad += len(bad)
        for n in bad:
            print(f"   [{side}/{kind}] {n}")
    print(f"   非 ASCII 合计: {n_bad}")

    items, plan_problems = plan(listing)
    problems += plan_problems

    print()
    print("── 3. 改名计划 ──")
    if not items:
        print("   （无待改名件——已 ASCII 化）")
    for it in items:
        print(f"   {it['side']}/{it['kind']}: {it['old']} -> {it['new']}")

    parity = check_side_parity(listing)
    problems += parity

    if problems:
        print()
        print("── 硬错误 ──")
        for p in problems:
            print(f"   {p}")
        if any(p.startswith(("[撞名]", "[规则未命中]", "[缺目录]", "[两侧不一致]")) for p in problems):
            print("\n[W15] 中止：存在硬错误，未写盘。")
            return 1

    if args.check:
        print()
        print("[W15] check 完成：未写盘。")
        return 0

    print()
    print("── 4. 执行改名（逐件 md5 前后比对） ──")
    records = do_rename(items, assets_root)

    if not args.no_manifest:
        print()
        print("── 5. 同步清单 `统一名` 列 ──")
        mapping = {it["old"]: it["new"] for it in items}
        changed, mproblems = sync_manifests(manifest_root, mapping, apply=True)
        print(f"   改动单元格: {changed}")
        if mproblems:
            for p in mproblems:
                print(f"   {p}")

    if args.report:
        cols = ["side", "kind", "old", "new", "md5_before", "md5_after", "ok"]
        with args.report.open("w", encoding="utf-8", newline="\n") as f:
            f.write("\t".join(cols) + "\n")
            for r in records:
                f.write("\t".join(str(r[c]) for c in cols) + "\n")
        print(f"\n[W15] 报告已写出: {args.report}")

    print()
    print(f"[W15] 完成：改名 {len(records)} 件，md5 前后全部一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())