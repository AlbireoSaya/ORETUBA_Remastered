# -*- coding: utf-8 -*-
"""
W12 · 消除跨目录同名不同图隐患：给「系统UI」侧撞名文件加 `ui_` 前缀
==================================================================
问题（已实测）：
  `美术统一\\系统UI\\` 与 `美术统一\\立绘\\` / `美术统一\\CG背景\\` 之间存在**同名不同图**：
    立绘\\asu01.png  md5 1b6d77b2…  ｜  系统UI\\asu01.png  md5 6d3c98e2…
  按 basename 取素材会**静默取错**（超分管线已因此产生过 58 件错误产物，见 `美术统一_超分\\超分说明.md` §4.1）。
  实测撞名：与 `立绘` 50 个、与 `CG背景` 331 个，**并集 381 个**（`立绘 ∩ CG背景 = 0`）。

规则（唯一口径）：
  对 `美术统一\\系统UI\\` 下每个文件，**若其 basename 也存在于 `美术统一\\立绘\\` 或 `美术统一\\CG背景\\`**，
  则改名为 `ui_` + basename；其余文件**保持原名不动**。
  **同一规则同步施加到 `美术统一_超分\\系统UI\\`**（超分产物文件名与 `美术统一\\` 逐字节相同，只改一边会失配）。

纪律：
  - **只改名（rename），不改任何像素内容**；脚本对每个改名文件做**改名前后 md5 比对**，不一致即报错中止。
  - **只碰 `系统UI\\` 两个目录**；`立绘\\` / `CG背景\\` 一律不读不写（仅 `listdir` 取文件名集合）。
  - **幂等**：已加前缀者 basename 不在撞名集合内，再跑不会重复加；`--check` 只校验不写盘。

用途（管线中的位置）：
  `unify_sys.py` 等生成器若被重跑，会**重新产出无前缀的旧名**；本脚本是生成器之后**必须补跑的一步**。
  管线顺序（见 `美术统一\\README_交付超分.md` §八）：
    生成器（unify_sys.py / w11g_*.py …） → **w12_apply_ui_prefix.py（本脚本）** → 自检

用法：
  # 只改 PNG（默认），自动探测资源组根
  python w12_apply_ui_prefix.py
  # 只校验不写盘
  python w12_apply_ui_prefix.py --check
  # 同时同步受控清单 TSV（统一名列）
  python w12_apply_ui_prefix.py --only all
  # 把清单同步到另一个根（本 issue 的 worktree：PNG 在主工作树、清单在 worktree）
  python w12_apply_ui_prefix.py --only tsv --res "<主工作树资源组>" --tsv-res "<worktree 资源组>"

退出码：0 = 成功/无待办；1 = 校验失败或 md5 不一致；2 = 路径解析失败。
"""
import argparse
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

PROJ_NAME = "我们没有翅膀——格雷塔迦露德与柳木原"
DEFAULT_RES = os.path.join(r"E:\ZCode Workspace\Galgame", "工程", PROJ_NAME, "资源组")

SUB_UI = os.path.join("美术统一", "系统UI")
SUB_UI_SR = os.path.join("美术统一_超分", "系统UI")
REF_DIRS = [os.path.join("美术统一", "立绘"), os.path.join("美术统一", "CG背景")]
REF_DIRS_SR = [os.path.join("美术统一_超分", "立绘"), os.path.join("美术统一_超分", "CG背景")]

PREFIX = "ui_"

# 受控清单： (相对路径, 文件名列, 类别列 或 None, 需要匹配的类别值)
TSV_SPECS = [
    (os.path.join("美术统一", "清单_系统UI.tsv"), "统一名", "类别", "系统UI"),
    (os.path.join("美术统一", "交付清单.tsv"), "统一名", "类别", "系统UI"),
    (os.path.join("美术统一_超分", "超分清单.tsv"), "统一名", "类别", "系统UI"),
    (os.path.join("美术统一", "待复核_系统UI.tsv"), "统一名", None, None),
]


def md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def resolve_res(explicit):
    """按序探测含 `美术统一/系统UI` 的资源组根。"""
    cands = []
    if explicit:
        cands.append(explicit)
    if os.environ.get("GRETA_RES"):
        cands.append(os.environ["GRETA_RES"])
    here = os.path.dirname(os.path.abspath(__file__))
    cands.append(os.path.dirname(here))          # 脚本所在树的 资源组
    cands.append(DEFAULT_RES)                    # 主工作树（PNG 只在这里）
    for c in cands:
        c = os.path.abspath(c)
        if os.path.isdir(os.path.join(c, SUB_UI)):
            return c
    return None


def name_set(root, rels):
    out = set()
    for rel in rels:
        d = os.path.join(root, rel)
        if os.path.isdir(d):
            out |= set(os.listdir(d))
    return out


def collision_set(ref_names, ui_names):
    return {n for n in ui_names if n in ref_names}


def scan(root):
    """只读扫描，返回 (pending, done, ref, ui_names)。

    pending = 撞名但**尚未**加前缀的 basename（需改名的）
    done    = 撞名且**已加**前缀的 basename（`ui_<name>` 存在、且 `<name>` 在参考集合内）
    两者并集 = 应带 `ui_` 前缀的 basename 全集（供清单同步使用；含已完成的，故幂等）。
    """
    ui_names = set(os.listdir(os.path.join(root, SUB_UI)))
    ref = name_set(root, REF_DIRS)

    # 独立复算超分侧参考集合，与主集合比对（应逐字节相同）
    ref_sr = name_set(root, REF_DIRS_SR)
    if ref_sr:
        assert ref_sr == ref, "超分侧参考集合与主侧不一致，请人工核查"

    pending = collision_set(ref, ui_names)
    done = {n for n in ref if (PREFIX + n) in ui_names}

    # 二次撞名自检：ui_<name> 不得与任何现存名冲突
    new_names = {PREFIX + n for n in pending}
    assert not (new_names & ui_names), "加前缀后与系统UI现存名二次撞名"
    assert not (new_names & ref), "加前缀后与立绘/CG背景二次撞名"
    assert len(new_names) == len(pending), "撞名集合内部有重复"
    # 已加前缀者不得与参考集合二次撞名（即 ref 内不应出现 ui_*）
    assert not (done & pending), "同一 basename 同时处于 pending 与 done"

    return pending, done, ref, ui_names


def build_plan(root):
    """返回 (碰撞集合, [(旧路径, 新路径, basename)], 统计信息)。只读。"""
    pending, done, ref, ui_names = scan(root)

    plan = []
    for sub in (SUB_UI, SUB_UI_SR):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if n in pending:
                plan.append((os.path.join(d, n), os.path.join(d, PREFIX + n), n))

    info = dict(ui=len(ui_names), ref=len(ref), collide=len(pending),
                done=len(done), unchanged=len(ui_names) - len(pending) - len(done))
    return pending, plan, info


def target_names(root):
    """应带 `ui_` 前缀的 basename 全集（pending ∪ done）。"""
    pending, done, _, _ = scan(root)
    return pending | done


def do_png(root, check):
    coll, plan, info = build_plan(root)
    print(f"[png] 资源组根 = {root}")
    print(f"[png] 系统UI 文件数 = {info['ui']} ｜ 立绘∪CG背景 名字数 = {info['ref']}")
    print(f"[png] 待加前缀 = {info['collide']} ｜ 已加前缀 = {info['done']} ｜ 保持原名 = {info['unchanged']}")
    print(f"[png] 待改名（含超分侧）= {len(plan)} 条")
    if check:
        for old, new, _ in plan[:5]:
            print(f"      CHECK 将改：{os.path.relpath(old, root)} -> {os.path.basename(new)}")
        if len(plan) > 5:
            print(f"      ...（其余 {len(plan) - 5} 条略）")
        return 0
    if not plan:
        print("[png] 无待改名（已幂等：前缀已就位）")
        return 0
    bad = 0
    for old, new, base in plan:
        if os.path.exists(new):
            print(f"[png] !! 目标已存在，跳过：{new}")
            bad += 1
            continue
        before = md5(old)
        os.rename(old, new)
        after = md5(new)
        if before != after:
            print(f"[png] !! md5 不一致：{old} -> {new}")
            bad += 1
    print(f"[png] 改名完成 = {len(plan)} 条 ｜ md5 不一致/异常 = {bad} 条")
    return 1 if bad else 0


def _read_lines(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    trailing = text.endswith(nl)
    lines = text.split(nl)
    if trailing:
        lines = lines[:-1]
    return lines, bom, nl, trailing


def _write_lines(path, lines, bom, nl, trailing):
    text = nl.join(lines) + (nl if trailing else "")
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    tmp = path + ".tmp_w12"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def do_tsv(res, tsv_res, coll, check):
    print(f"[tsv] 清单根 = {tsv_res}（撞名集合取自 {res}）")
    total = 0
    for rel, namecol, catcol, catval in TSV_SPECS:
        p = os.path.join(tsv_res, rel)
        if not os.path.isfile(p):
            print(f"[tsv] 跳过（不存在）：{rel}")
            continue
        lines, bom, nl, trailing = _read_lines(p)
        hdr = lines[0].split("\t")
        if namecol not in hdr:
            print(f"[tsv] 跳过（无 `{namecol}` 列）：{rel}")
            continue
        ni = hdr.index(namecol)
        ci = hdr.index(catcol) if (catcol and catcol in hdr) else None
        changed = 0
        for i in range(1, len(lines)):
            f = lines[i].split("\t")
            if ni >= len(f):
                continue
            if ci is not None and (ci >= len(f) or f[ci] != catval):
                continue
            if f[ni] in coll:
                f[ni] = PREFIX + f[ni]
                lines[i] = "\t".join(f)
                changed += 1
        print(f"[tsv] {rel}：{'将改' if check else '已改'} {changed} 行")
        if changed and not check:
            _write_lines(p, lines, bom, nl, trailing)
        total += changed
    print(f"[tsv] 合计 {'待改' if check else '已改'} = {total} 行")
    return total


def main():
    ap = argparse.ArgumentParser(description="给系统UI撞名文件加 ui_ 前缀（幂等）")
    ap.add_argument("--res", default=None, help="PNG 资源组根（默认自动探测）")
    ap.add_argument("--tsv-res", default=None, help="清单资源组根（默认与 --res 相同）")
    ap.add_argument("--only", choices=["png", "tsv", "all"], default="png", help="执行哪一部分，默认 png")
    ap.add_argument("--check", action="store_true", help="只校验不写盘")
    a = ap.parse_args()

    res = resolve_res(a.res)
    if not res:
        print("[fatal] 未找到含 `美术统一/系统UI` 的资源组根，请用 --res 指定")
        return 2
    tsv_res = os.path.abspath(a.tsv_res) if a.tsv_res else res

    rc = 0
    if a.only in ("png", "all"):
        rc |= do_png(res, a.check)
    if a.only in ("tsv", "all"):
        do_tsv(res, tsv_res, target_names(res), a.check)
    return rc


if __name__ == "__main__":
    sys.exit(main())