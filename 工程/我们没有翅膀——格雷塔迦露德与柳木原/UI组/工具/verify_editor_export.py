# -*- coding: utf-8 -*-
r"""verify_editor_export.py —— 编辑器导出件的「一键入库 + 检验」

用途：在 `复刻\editor.html` 里改完 → 点「导出 JSON」（浏览器会把文件下载为
      `screens/*.json` 的原文件名，如 `01_title.json`）→ 跑本脚本。

本脚本做四件事：
  1. **定位导出件**：默认扫 `~/Downloads`；也可 `--from <目录>` 指定，或直接给文件路径。
  2. **先备份再覆盖**：把 `layout/screens/` 里被覆盖的旧文件存到
     `_工作\M35_编辑器回滚\<时间戳>\`（**只增不改，可随时还原**）。
  3. **重跑生成与校验**：`gen_layout.py` → `verify_ui.py`（六项硬校验）。
  4. **出结构 diff**：逐 id 列出「新增 / 删除 / 移动 / 改属性」，一眼看清改了什么。
  5. **两道静默流失守门**（放行开关 `--allow-drop`）：
     ① `@palette.` 引用数只许持平/增加；
     ② 每一件元素的 `state_group` 与 `state_assets` **分别判定**，任一丢失即**拒绝写入**并打印
        「元素 id + 丢的字段名」逐条明细（M4 修 Major-2：原实现只查「两件都没了」，只丢一件会放行）。

用法：
    python verify_editor_export.py                 # 自动扫 Downloads（取最新的）
    python verify_editor_export.py --from 临时\导出
    python verify_editor_export.py 01_title.json 21_confirm.json
    python verify_editor_export.py --dry           # 只看 diff，不落盘、不跑校验
    python verify_editor_export.py --list          # 只列出候选导出件
    python verify_editor_export.py --allow-drop    # 守门拦下时强行入库（仍逐条打印丢失明细）

退出码：0 = 校验通过；1 = 有硬失败或输入有问题。
"""
import os, sys, io, json, glob, shutil, subprocess, datetime, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCREENS = os.path.join(UI, "layout", "screens")
ROLLBACK = os.path.join(UI, "_工作", "M35_编辑器回滚")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

GEOM_KEYS = ("x", "y", "w", "h")
# ★ M4：守门按**字段粒度**比对的字段集（逐字段判定，逐条打印丢失明细）
STATE_FIELDS = ("state_group", "state_assets")
# ★ M46（一审 Minor-6）：**嵌套**状态字段 —— `list` 的逐项态图挂在 `item_frame` 下，
#   浅层比较（只看元素顶层键）看不见它。今天编辑器是整元素 JSON 往返（不会丢），
#   但守门必须与守卫粒度一致：任一层缺键即拒绝入库。用「路径.子路径」取值。
STATE_FIELDS_NESTED = ("item_frame.state_assets",)


def screen_names():
    """screens/*.json 的合法文件名集合。"""
    return {os.path.basename(p) for p in glob.glob(os.path.join(SCREENS, "[0-9]*.json"))}


def find_candidates(src_dir, only=None):
    names = screen_names()
    cands = []
    for p in glob.glob(os.path.join(src_dir, "*.json")):
        b = os.path.basename(p)
        if b.startswith("_"):
            continue
        if only and b not in only:
            continue
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and "elements" in d and "id" in d:
            cands.append(p)
    # 若不是标准屏名（浏览器可能加了 (1) 后缀），也认——只要结构对
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return cands


def norm_name(path):
    """把 `01_title (1).json` 之类还原成 `01_title.json`。"""
    b = os.path.basename(path)
    stem = b[:-5] if b.lower().endswith(".json") else b
    for suf in (" (1)", " (2)", " (3)", " (4)", " (5)", "-1"):
        if stem.endswith(suf):
            stem = stem[: -len(suf)]
    return stem + ".json"


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def diff_elements(old, new):
    """逐 id 比较，返回 (新增, 删除, 移动, 改属性) 四个列表。"""
    o = {e.get("id"): e for e in (old or {}).get("elements", [])}
    n = {e.get("id"): e for e in (new or {}).get("elements", [])}
    added = [k for k in n if k not in o]
    removed = [k for k in o if k not in n]
    moved, changed = [], []
    for k in n:
        if k not in o:
            continue
        a, b = o[k], n[k]
        g = [f for f in GEOM_KEYS if a.get(f) != b.get(f)]
        others = [f for f in set(a) | set(b)
                  if f not in GEOM_KEYS and f not in ("id",) and a.get(f) != b.get(f)]
        if g:
            moved.append((k, {f: (a.get(f), b.get(f)) for f in g}))
        if others:
            changed.append((k, others))
    return added, removed, moved, changed


def run(script, cwd):
    p = subprocess.run([sys.executable, script], cwd=cwd,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def load_palette():
    """与 gen_layout.load_palette 同一口径：colors.<k>.value → {k: 值}。"""
    p = os.path.join(UI, "layout", "palette.json")
    try:
        raw = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return {}
    return {k: v.get("value") for k, v in raw.get("colors", {}).items()}


def restore_palette_refs(new_node, old_node, palette, report, path=""):
    """★ M35b 修（编辑器往返缺陷）：把导出件里**被解析成字面值**的调色板引用还原回 `@palette.<key>`。

    成因：`gen_layout.py` 的 `resolve_deep()` 会把 `@palette.*` 解析成实际值再写进
    `复刻/ui_layout.js`（编辑器唯一能读到的数据源，`file://` 下无法读 layout/screens/*.json），
    于是编辑器**只见过字面值**，导出时把字面值写回 ⇒ 每跑一次「编辑器导出 → 入库」，
    版面源里的调色板间接层就被抹掉一层（实测 `@palette.node_locked` → `#4A4A56`）。

    还原规则（**只认「旧源同一路径原本就是引用」的情形，绝不猜**）：
      旧源该路径是 `@palette.<key>`，且导出件的值 == resolve(`@palette.<key>`)
      ⇒ 写回旧源的 `@palette.<key>`。
    这样既无歧义（`#000000` 同时对应 shadow 与 backdrop，反查表法会猜错），
    也不会把用户新填的字面色误改成引用。

    ★★ M35b 一审 Major-2 修：**列表必须按 `id` 配对，不能按下标**。
      按下标配对会在「元素顺序变化」时错配 —— 本轮实测真丢过 2 处引用：
      第二次入库的基线是被 v1 脚本改乱过的 24 元素版（`copyright` 在下标 9，
      而导出件下标 9 已是 `title.menu_txt_start`），下标配对照不上旧引用 ⇒ 静默漏还原，
      `title.text_copyright.font` 的 `@palette.text_small` / `@palette.shadow` 被留成字面色值。
      现在：两表都带 `id` 时按 id 建索引配对；缺 id 才回落下标。
    """
    if isinstance(new_node, dict) and isinstance(old_node, dict):
        old_by_id = None
        if isinstance(old_node.get("elements"), list) and isinstance(new_node.get("elements"), list):
            old_by_id = {}
            for o in old_node["elements"]:
                if isinstance(o, dict) and o.get("id"):
                    old_by_id[o["id"]] = o
        for k, v in list(new_node.items()):
            ov = old_node.get(k)
            # 按 id 重定位「对应的旧元素」（仅当两边都是元素数组时才启用）
            if (k == "elements" and old_by_id and isinstance(v, list)):
                for i, ne in enumerate(v):
                    if not isinstance(ne, dict):
                        continue
                    oe = old_by_id.get(ne.get("id"))
                    if oe is None:
                        continue
                    restore_palette_refs(ne, oe, palette, report, "%s.elements[%s]" % (path, ne.get("id")))
                continue
            if isinstance(v, str) and isinstance(ov, str) and ov.startswith("@palette."):
                key = ov[len("@palette."):]
                if key in palette and palette[key] == v:
                    new_node[k] = ov
                    report.append("%s.%s: %s → %s" % (path, k, v, ov))
                    continue
            restore_palette_refs(v, ov, palette, report, "%s.%s" % (path, k))
    elif isinstance(new_node, list) and isinstance(old_node, list):
        for i, v in enumerate(new_node):
            ov = old_node[i] if i < len(old_node) else None
            restore_palette_refs(v, ov, palette, report, "%s[%d]" % (path, i))


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("files", nargs="*", help="导出件路径（省略则自动扫描 --from）")
    ap.add_argument("--from", dest="src", default=None, help="导出件所在目录（默认 ~/Downloads）")
    ap.add_argument("--dry", action="store_true", help="只出 diff，不落盘、不跑校验")
    ap.add_argument("--list", action="store_true", help="只列出候选导出件")
    ap.add_argument("--no-depalette", action="store_true",
                    help="不还原被编辑器解析掉的 @palette 引用（默认**还原**，见 restore_palette_refs）")
    ap.add_argument("--allow-drop", action="store_true",
                    help="允许守门放行：即使导出件会减少 @palette 引用或丢掉 state_group/state_assets 也照常入库"
                         "（放行时仍逐条打印丢失明细）")
    args = ap.parse_args()

    # ── 1. 定位导出件 ──
    if args.files:
        paths = [os.path.abspath(p) for p in args.files]
        for p in paths:
            if not os.path.exists(p):
                print("!! 文件不存在：%s" % p); return 1
    else:
        src = args.src or DOWNLOADS
        if not os.path.isdir(src):
            print("!! 目录不存在：%s（用 --from 指定导出目录）" % src); return 1
        paths = find_candidates(src)
        if not paths:
            print("!! 在 %s 里没找到编辑器导出件（需含 id/elements 字段的 JSON）" % src); return 1
        # 同屏只取最新一份
        best, seen = [], set()
        for p in paths:
            k = norm_name(p)
            if k in seen:
                continue
            seen.add(k); best.append(p)
        paths = best

    if args.list:
        print("候选导出件（%d 件）：" % len(paths))
        for p in paths:
            print("  %-28s  %s" % (norm_name(p), datetime.datetime.fromtimestamp(
                os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")))
        return 0

    # ── 2. 先算 diff（拿现有文件当基线）──
    plan = []
    for p in paths:
        name = norm_name(p)
        cur = os.path.join(SCREENS, name)
        if not os.path.exists(cur):
            print("!! %s 在 layout/screens/ 里没有对应文件（新屏？）—— 跳过" % name)
            continue
        try:
            newd = load(p)
        except Exception as e:
            print("!! %s 解析失败：%r" % (p, e)); continue
        oldd = load(cur)
        plan.append((p, name, cur, oldd, newd))

    if not plan:
        print("没有可处理的导出件。"); return 1

    print("=" * 78)
    print("编辑器导出件检验 ｜ %d 个屏" % len(plan))
    print("=" * 78)
    total_err = 0
    for p, name, cur, oldd, newd in plan:
        print("\n## %s   ←  %s" % (name, p))
        a, r, m, c = diff_elements(oldd, newd)
        print("   元素数 %d → %d" % (len(oldd.get("elements", [])), len(newd.get("elements", []))))
        if not (a or r or m or c):
            print("   （与本屏现有 JSON 完全一致，无改动）")
        for k in a[:20]:
            e = [x for x in newd["elements"] if x.get("id") == k][0]
            print("   ＋ 新增 %-26s %-6s x%s y%s w%s h%s" % (k, e.get("kind"), e.get("x"), e.get("y"), e.get("w"), e.get("h")))
        if len(a) > 20: print("   …新增还有 %d 个" % (len(a) - 20))
        for k in r[:20]:
            print("   － 删除 %s" % k)
        if len(r) > 20: print("   …删除还有 %d 个" % (len(r) - 20))
        for k, g in m[:30]:
            print("   ↔ 移动 %-26s %s" % (k, "  ".join("%s %s→%s" % (f, g[f][0], g[f][1]) for f in g)))
        if len(m) > 30: print("   …移动还有 %d 个" % (len(m) - 30))
        for k, fs in c[:14]:
            print("   * 改属性 %-24s %s" % (k, ",".join(sorted(fs))))
        if len(c) > 14: print("   …改属性还有 %d 个" % (len(c) - 14))

    # ── 2.5 ★ M35b：还原被编辑器解析掉的调色板引用（见 restore_palette_refs 注释）──
    if not args.no_depalette:
        palette = load_palette()
        total = []
        for p, name, cur, oldd, newd in plan:
            rep = []
            restore_palette_refs(newd, oldd, palette, rep, name)
            if rep:
                print("\n★ 调色板引用还原（%s）：%d 处" % (name, len(rep)))
                for line in rep[:12]:
                    print("   " + line)
                if len(rep) > 12:
                    print("   …还有 %d 处" % (len(rep) - 12))
            total += rep
        if total:
            print("  合计还原 %d 处 —— 不还原的话，版面源会被逐步去调色板化" % len(total))
        else:
            print("\n调色板引用还原：无需还原（无「旧源是引用、导出变字面值」的字段）")

    # ── 2.6 ★ M35b 守门（一审 Major-2 / Minor-6）；M4 修 Major-2（按字段粒度）──
    #     ① `@palette.` 引用数只能持平或增加，减少即报错（否则去调色板化会一路绿灯——
    #        verify_ui 比的是解析值，任何工具都不会报）。
    #     ② 元素不得丢失 `state_group` / `state_assets` —— **两件分别判定**，任一件丢失即拦截。
    def count_palette(node):
        if isinstance(node, dict):
            return sum(count_palette(v) for v in node.values())
        if isinstance(node, list):
            return sum(count_palette(v) for v in node)
        return 1 if (isinstance(node, str) and node.startswith("@palette.")) else 0

    #     ★★ M4（2026-09-22）修 Major-2：**按字段粒度**判定，不再按「两件都没了」。
    #      原实现 `state_carriers(old) - state_carriers(new)` 把 state_group / state_assets
    #      合并成一个 id 集合比较 ⇒ **只丢其中一件仍会放行**（独立复审实测：只丢
    #      `state_assets`、保留 `state_group` 的导出件被放行并实际覆盖落盘，rc=0）。
    #      现在逐元素、逐字段比对，丢失即拒绝写入，并打印「元素 id + 丢的字段名」清单。
    def state_fields(node):
        """导出件里每个元素的 id → 它**实际持有**的状态字段集合（逐字段判定）。"""
        out = {}

        def present(v):
            """空串 / None / 空字典视为「未持有」（与引擎侧「无组」「无态图」同口径）。"""
            if v is None:
                return False
            if isinstance(v, str):
                return v.strip() != ""
            if isinstance(v, dict):
                return len(v) > 0
            return True

        def nested_present(node, path):
            cur = node
            for k in path.split("."):
                if not isinstance(cur, dict) or k not in cur:
                    return False
                cur = cur[k]
            return present(cur)

        def walk(n):
            if isinstance(n, dict):
                eid = n.get("id")
                if isinstance(eid, str) and eid:
                    got = set(f for f in STATE_FIELDS if present(n.get(f)))
                    got |= set(f for f in STATE_FIELDS_NESTED if nested_present(n, f))
                    if got:
                        out[eid] = frozenset(got)
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(node)
        return out

    def lost_state_fields(old_map, new_map):
        """返回 [(id, 字段名), …]：逐元素逐字段比对（元素整件消失 = 两个字段都算丢）。"""
        out = []
        for eid in sorted(old_map):
            got = new_map.get(eid, frozenset())
            for f in list(STATE_FIELDS) + list(STATE_FIELDS_NESTED):
                if f in old_map[eid] and f not in got:
                    out.append((eid, f))
        return out

    gate, detail = [], []
    for p, name, cur, oldd, newd in plan:
        n_old, n_new = count_palette(oldd), count_palette(newd)
        if n_new < n_old:
            gate.append("调色板引用减少：%s（%d → %d）——版面源被去调色板化" % (name, n_old, n_new))
        lost = lost_state_fields(state_fields(oldd), state_fields(newd))
        if lost:
            gate.append("状态字段丢失：%s —— %d 处（逐条明细见下）" % (name, len(lost)))
            for eid, f in lost:
                detail.append("元素 %-30s 丢失字段 %s" % (eid, f))
    if gate:
        print("\n" + "!" * 78)
        if args.allow_drop:
            print("!! 守门告警（**--allow-drop 已放行，将继续落盘**）：导出件会造成静默流失")
        else:
            print("!! 守门拦截：导出件会造成静默流失，**未落盘**")
        for g in gate:
            print("   · " + g)
        if detail:
            print("   —— 逐条丢失明细（元素 id + 字段名）——")
            for line in detail:
                print("     · " + line)
        print("   （`@palette.` 引用数只允许持平或增加；**每一件元素的 `state_group` 与 `state_assets`"
              " 分别判定**，任一字段丢失即拦截。")
        print("     多为「编辑器页面用的是旧 ui_layout.js」→ 请在编辑器里点『重载』或刷新页面后重新导出；")
        print("     确认要强行入库时加 --allow-drop）")
        print("!" * 78)
        if not args.allow_drop:
            return 1
        print("（--allow-drop：已放行，上述逐条明细仍全部打印，**请据此核对后再提交**）")
        if detail:
            for line in detail:
                print("     · 放行项 " + line)

    if args.dry:
        print("\n（--dry：未落盘、未跑校验）")
        return 0

    # ── 3. 备份 + 覆盖 ──
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bakdir = os.path.join(ROLLBACK, stamp)
    os.makedirs(bakdir, exist_ok=True)
    for p, name, cur, oldd, newd in plan:
        shutil.copy2(cur, os.path.join(bakdir, name))
        with io.open(cur, "w", encoding="utf-8", newline="\n") as f:
            json.dump(newd, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print("\n已覆盖 %d 个屏；旧文件备份在：%s" % (len(plan), bakdir))
    print("（还原：把该目录里的文件拷回 layout/screens/ 即可）")

    # ── 4. gen_layout + verify_ui ──
    print("\n" + "-" * 78)
    print("重跑 gen_layout.py …")
    rc1, out1 = run(os.path.join(HERE, "gen_layout.py"), HERE)
    tail = [l for l in out1.strip().splitlines() if l.strip()][-6:]
    print("\n".join("   " + l for l in tail))
    if rc1 != 0:
        print("!! gen_layout.py 失败（退出码 %d）—— 校验中止" % rc1)
        return 1

    print("\n重跑 verify_ui.py …")
    rc2, out2 = run(os.path.join(HERE, "verify_ui.py"), HERE)
    keep = [l for l in out2.splitlines()
            if ("[1]" in l or "[2]" in l or "[3]" in l or "[4]" in l or "[5]" in l
                or "[6]" in l or "汇总" in l or "结果" in l or "资产" in l or "!!" in l)]
    print("\n".join("   " + l for l in keep[-30:]))
    if rc2 != 0:
        print("\n!! verify_ui.py 未通过（退出码 %d）—— 见上面「!!」行" % rc2)
        total_err += 1

    print("\n" + "=" * 78)
    if total_err == 0:
        print("结果：**校验通过** —— 改动已入库（layout/screens/），生成物已同步")
        print("回滚：copy \"%s\\*\" \"%s\\\"" % (bakdir, SCREENS))
    else:
        print("结果：**未通过** —— 改动已入库但校验失败，建议先按上面的 !! 修，或直接回滚")
        print("回滚：copy \"%s\\*\" \"%s\\\"" % (bakdir, SCREENS))
    print("=" * 78)
    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())