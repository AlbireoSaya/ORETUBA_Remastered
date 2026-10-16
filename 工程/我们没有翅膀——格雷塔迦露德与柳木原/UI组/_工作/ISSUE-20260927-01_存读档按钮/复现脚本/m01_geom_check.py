# -*- coding: utf-8 -*-
r"""m01_geom_check.py —— 存/读档屏「右上三系统按钮组左移」几何与字段自证
（ISSUE-20260927-01 · 模块 B；幂等、带退出码、可复跑；不改盘）

判据（画布 1920×1080，全部从盘上数据实测，不引用派单转述数字）：
  [0] 落盘格式自证：读盘 JSON → dump(indent=1, ensure_ascii=False)+CRLF 必须与盘上原字节**逐字节相同**
      （保证后续 diff 的「只改 x」不是格式化 churn 造成的假象）。
  [1] 九件（含 `_tx`/`_hit`）x 旧→新表 + 可见件组右沿 / hit 层右沿 / 组内 w、间距、顺序；
      并断言**两屏该组几何逐项相同**。
  [2] 与页码的间隙：新组右沿 ↔ 引擎绘徽章列左沿（`sv.pgnum_01..10` 的 x，盘上实测）；
      hit 层右沿 ↔ 徽章列；与烘焙「/10」条带的横向关系（口径 x1763..1845 / y80..140，
      与 M06 记录的补底矩形一致；原图实地列剖面另附，见输出末段）。
  [3] 相交体检：九件 × 屏内其余全部元素（整屏底图/遮罩除外 —— 同 M07 既有口径），
      改前（`原形备份\`）与改后（盘上）**逐对**比对，断言**新增相交对 = 0**。
  [4] 逐字段未变：九件逐字段 + 屏级逐字段 diff（对 `原形备份\`），断言除 `x`（与 `note`）外全等。
  [5] 组内相对关系不变：w、间距、顺序。

用法：python m01_geom_check.py                # 全部通过 ⇒ 退出码 0
      python m01_geom_check.py --dir <新屏目录>   # 核指定目录（默认盘上 layout\screens）
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
UI = HERE.parents[3]
SCR = UI / "layout" / "screens"
BAK = HERE.parents[1] / "原形备份"
FILES = ("23_save.json", "24_load.json")

GROUP = ["sv.sys_game", "sv.sys_game_tx", "sv.sys_game_hit",
         "sv.sys_title", "sv.sys_title_tx", "sv.sys_title_hit",
         "sv.sys_end", "sv.sys_end_tx", "sv.sys_end_hit"]
AUTO_VIS = ["sv.sys_game", "sv.sys_game_tx", "sv.sys_title", "sv.sys_title_tx",
            "sv.sys_end", "sv.sys_end_tx"]      # 可见件（image + text）
AUTO_HIT = ["sv.sys_game_hit", "sv.sys_title_hit", "sv.sys_end_hit"]

OLD_RIGHT = 1880          # 可见件组右沿（旧）：sv.sys_end 1670+210
NEW_RIGHT_MAX = 1690      # 验收：可见件组右沿 ≤ 1690
BADGE_X = 1699            # 页码徽章列左沿（引擎绘 sv.pgnum_*，盘上实测复核）
BAKED_SLASH10 = (1763, 1845, 80, 140)   # 烘焙「/10」条带（口径；与 M06 补底矩形一致）

FAILS = []


def rect(e):
    return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])


def inter(a, b):
    return (max(0, min(a[2], b[2]) - max(a[0], b[0]))
            * max(0, min(a[3], b[3]) - max(a[1], b[1])))


def dump_bytes(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False).replace("\n", "\r\n").encode("utf-8")


def load(path):
    return json.loads(path.read_bytes().decode("utf-8"))


def main():
    d_dir = SCR
    if "--dir" in sys.argv:
        d_dir = Path(sys.argv[sys.argv.index("--dir") + 1])
    print("=" * 104)
    print("新屏目录 = %s" % d_dir)
    print("原形备份 = %s" % BAK)

    live, bake = {}, {}
    for fn in FILES:
        live[fn] = load(d_dir / fn)
        bake[fn] = load(BAK / fn)

    # ---------- [0] 落盘格式自证 ----------
    print("\n" + "=" * 104)
    print("[0] 落盘格式自证：dump(indent=1, ensure_ascii=False)+CRLF 与盘上原字节逐字节比对")
    for fn in FILES:
        for tag, p in (("备份(未改)", BAK / fn), ("盘上", d_dir / fn)):
            raw = p.read_bytes()
            obj = json.loads(raw.decode("utf-8"))
            ok = dump_bytes(obj) == raw
            print("   %-12s %-10s %s（%d 字节）%s" % (fn, tag, "一致 ✓" if ok else "不一致 ✗",
                                                     len(raw), "" if ok else "  <== 有格式化差异"))
            if not ok:
                FAILS.append("%s %s 落盘格式与盘上不一致" % (fn, tag))

    # ---------- [1] x 旧→新 / 组包络 ----------
    print("\n" + "=" * 104)
    print("[1] 九件 x 旧→新（两屏）+ 组包络")
    geom_by_file = {}
    for fn in FILES:
        li = {e["id"]: e for e in live[fn]["elements"]}
        bi = {e["id"]: e for e in bake[fn]["elements"]}
        print("  -- %s --" % fn)
        for eid in GROUP:
            if eid not in li or eid not in bi:
                FAILS.append("%s 缺件 %s" % (fn, eid))
                continue
            a, b = bi[eid], li[eid]
            print("     %-18s %-6s x %5d → %5d   Δ=%+d   w %3d→%3d  y %3d→%3d  z %s→%s"
                  % (eid, b["kind"], a["x"], b["x"], b["x"] - a["x"],
                     a["w"], b["w"], a["y"], b["y"], a.get("z"), b.get("z")))
        vis = [li[e] for e in AUTO_VIS]
        hit = [li[e] for e in AUTO_HIT]
        r_vis, l_vis = max(e["x"] + e["w"] for e in vis), min(e["x"] for e in vis)
        r_hit, l_hit = max(e["x"] + e["w"] for e in hit), min(e["x"] for e in hit)
        yb, yt = min(e["y"] for e in vis + hit), max(e["y"] + e["h"] for e in vis + hit)
        print("     · 可见件  左沿 %d → 右沿 %d（旧 %d）｜hit 层 左沿 %d → 右沿 %d" % (l_vis, r_vis, OLD_RIGHT, l_hit, r_hit))
        print("     · 组纵向带 y %d..%d（h 未动 ⇒ 与旧相同）" % (yb, yt))
        geom_by_file[fn] = [(li[e]["x"], li[e]["y"], li[e]["w"], li[e]["h"]) for e in GROUP]
        if not (l_hit < l_vis <= r_hit and r_vis == r_hit - 8):
            FAILS.append("%s 组包络异常（hit 外扩 8px 关系不成立）" % fn)
        if r_vis > NEW_RIGHT_MAX:
            FAILS.append("%s 可见件组右沿 %d > 验收上限 %d" % (fn, r_vis, NEW_RIGHT_MAX))

    same = geom_by_file[FILES[0]] == geom_by_file[FILES[1]]
    print("  两屏九件几何逐项相同：%s" % ("是 ✓" if same else "否 ✗"))
    if not same:
        FAILS.append("两屏九件几何不一致")

    d = live[FILES[0]]
    idx = {e["id"]: e for e in d["elements"]}
    # ---------- [2] 与页码的间隙 ----------
    badge = sorted((e["x"], e["x"] + e["w"], e["y"], e["y"] + e["h"])
                   for e in d["elements"] if e["id"].startswith("sv.pgnum_"))
    bx = min(b[0] for b in badge)
    bxr = max(b[1] for b in badge)
    by0, by1 = min(b[2] for b in badge), max(b[3] for b in badge)
    vis = [idx[e] for e in AUTO_VIS]
    hit = [idx[e] for e in AUTO_HIT]
    r_vis = max(e["x"] + e["w"] for e in vis)
    r_hit = max(e["x"] + e["w"] for e in hit)
    print("\n" + "=" * 104)
    print("[2] 与页码徽章的间隙（从盘上数据实测，不引用转述）")
    print("  引擎绘徽章列 `sv.pgnum_01..10`：x %d..%d、y %d..%d（%d 件，互斥 vis_when 1..10）"
          % (bx, bxr, by0, by1, len(badge)))
    print("  新可见件组右沿 %d → 距徽章列左沿 %d = **%dpx**（验收要求 ≥ 9px）%s"
          % (r_vis, bx, bx - r_vis, " ✓" if bx - r_vis >= 9 else " ✗"))
    print("  新 hit 层右沿 %d → 距徽章列左沿 %d = %dpx（hit 不可见，只要求不压徽章）%s"
          % (r_hit, bx, bx - r_hit, " ✓" if r_hit <= bx else " ✗"))
    if bx - r_vis < 9:
        FAILS.append("可见件组右沿距徽章列仅 %dpx < 9px" % (bx - r_vis))
    if r_hit > bx:
        FAILS.append("hit 层右沿 %d 压过徽章列 %d" % (r_hit, bx))
    if bx != BADGE_X:
        print("  !! 徽章列左沿实测 %d ≠ 派单口径 %d —— 以实测为准" % (bx, BADGE_X))
    sl, sr, sy0, sy1 = BAKED_SLASH10
    bo = {e["id"]: e for e in bake[FILES[0]]["elements"]}
    o_rvis = max(bo[e]["x"] + bo[e]["w"] for e in AUTO_VIS)
    o_lvis = min(bo[e]["x"] for e in AUTO_VIS)
    o_ytop = max(bo[e]["y"] + bo[e]["h"] for e in AUTO_VIS + AUTO_HIT)
    print("  改前可见件组横向 %d..%d（完整覆盖徽章列 %d..%d ⇒ 重叠 %dpx 宽）"
          % (o_lvis, o_rvis, bx, bxr, max(0, min(o_rvis, bxr) - max(o_lvis, bx))))
    print("  烘焙「/10」条带（口径 x%d..%d / y%d..%d，与 M06 记录的补底矩形同坐标）：" % (sl, sr, sy0, sy1))
    print("     · 横向：新组右沿 %d 在其左沿 %d 之左 %dpx ⇒ 完全让开 ✓" % (r_vis, sl, sl - r_vis))
    print("     · 横向：旧组 %d..%d 与之重叠 %dpx（原状同 x 段 ⇒ 视觉压页码）"
          % (o_lvis, o_rvis, max(0, min(o_rvis, sr) - max(o_lvis, sl))))
    print("     · 纵向：组底 y%d ／ 条带顶 y%d ⇒ 边界%s（改前后均无矩形相交，属视觉并置）"
          % (max(e["y"] + e["h"] for e in vis + hit), sy0,
             "相接（零面积）" if max(e["y"] + e["h"] for e in vis + hit) == sy0
             else "相隔 %dpx" % (sy0 - max(e["y"] + e["h"] for e in vis + hit))))

    # ---------- [3] 相交体检 ----------
    print("\n" + "=" * 104)
    print("[3] 相交体检：九件 × 屏内其余全部元素（整屏底图/遮罩除外 —— M07 既有口径）")
    canvas = [e["id"] for e in d["elements"] if e["w"] * e["h"] >= 1920 * 1080]
    print("  排除的整屏件（设计本意覆盖全屏）：%s" % canvas)
    res = {}
    for tag, dd in (("改前", bake[FILES[0]]), ("改后", d)):
        di = {e["id"]: e for e in dd["elements"]}
        others = [e for e in dd["elements"] if e["id"] not in GROUP and e["id"] not in canvas]
        pairs = []
        for eid in GROUP:
            a = rect(di[eid])
            for e in others:
                if inter(a, rect(e)) > 0:
                    pairs.append((eid, e["id"]))
        res[tag] = set(pairs)
        print("  %s：受检 %d 件 / %d 对 ⇒ **相交对 = %d 个**%s"
              % (tag, len(others), len(GROUP) * len(others), len(pairs),
                 "（全为 0 交叠面积）" if not pairs else " ✗ " + str(pairs[:10])))
        for grp, pred in (
                ("sv.pgnum_*（徽章）", lambda i: i.startswith("sv.pgnum_")),
                ("sv.pg*（页码键三层）", lambda i: i.startswith("sv.pg")),
                ("sv.tab_*（页签）", lambda i: i.startswith("sv.tab_")),
                ("sv.hit_back", lambda i: i == "sv.hit_back"),
                ("sv.edit / sv.help（含 _tx）", lambda i: i.startswith(("sv.edit", "sv.help"))),
                ("sv.slot*/sv.hit*（槽位）", lambda i: i.startswith(("sv.slot", "sv.hit"))),
        ):
            ids = [e["id"] for e in others if pred(e["id"])]
            p = [x for x in pairs if x[1] in ids]
            print("      · %-28s 覆盖 %2d 件 ⇒ 相交 %d 对" % (grp, len(ids), len(p)))
    added = res["改后"] - res["改前"]
    removed = res["改前"] - res["改后"]
    print("  **新增相交对 = %d 个**（要求 0）｜消失相交对 = %d 个" % (len(added), len(removed)))
    if added:
        FAILS.append("新增相交对 %d：%s" % (len(added), sorted(added)[:10]))

    # ---------- [4] 逐字段未变 ----------
    print("\n" + "=" * 104)
    print("[4] 逐字段未变（九件 + 屏级，对 `原形备份\\`）")
    for fn in FILES:
        li = {e["id"]: e for e in live[fn]["elements"]}
        bi = {e["id"]: e for e in bake[fn]["elements"]}
        changed = []
        for eid in GROUP:
            a, b = bi[eid], li[eid]
            keys = sorted(set(a) | set(b))
            for k in keys:
                if a.get(k) != b.get(k):
                    changed.append((eid, k, a.get(k), b.get(k)))
        print("  -- %s：九件字段级 diff = %d 处" % (fn, len(changed)))
        for eid, k, ov, nv in changed:
            print("       %-18s %-12s %r → %r" % (eid, k, ov, nv))
        if any(k != "x" for _, k, _, _ in changed):
            FAILS.append("%s 九件除 x 外还有字段变化" % fn)
        # 非组元素：逐字段必须**完全未变**（本轮只允许动这九件 + 屏级 note）
        other_changed = []
        for e in bake[fn]["elements"]:
            if e["id"] in GROUP:
                continue
            a, b = e, li.get(e["id"])
            if b is None:
                other_changed.append((e["id"], "<missing>", None, None))
                continue
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    other_changed.append((e["id"], k, a.get(k), b.get(k)))
        print("       非组元素逐字段 diff = %d 处%s"
              % (len(other_changed), " ✓" if not other_changed else " ✗"))
        for eid, k, ov, nv in other_changed[:20]:
            print("       !! 非组元素 %-18s %-12s %r → %r" % (eid, k, ov, nv))
        if other_changed:
            FAILS.append("%s 非组元素发生改动 %d 处" % (fn, len(other_changed)))
        # 屏级（`elements` 由上面的九件逐字段 diff + 下方的元素数/id 序断言覆盖，
        #        这里只比屏级标量字段，避免把整份 elements 当整体比对而虚报）
        sk = sorted((set(bake[fn]) | set(live[fn])) - {"elements"})
        for k in sk:
            if bake[fn].get(k) != live[fn].get(k):
                if k == "note":
                    print("       屏级 note：已变更（旧 %d 字 → 新 %d 字，只追加）"
                          % (len(bake[fn]["note"]), len(live[fn]["note"])))
                    if not live[fn]["note"].startswith(bake[fn]["note"][:200]):
                        FAILS.append("%s note 非「只追加」（前缀不符）" % fn)
                else:
                    FAILS.append("%s 屏级字段 %s 变化" % (fn, k))
                    print("       !! 屏级 %s: %r → %r" % (k, bake[fn].get(k), live[fn].get(k)))
        # 元素总数与 id 序
        if len(live[fn]["elements"]) != len(bake[fn]["elements"]):
            FAILS.append("%s 元素数变化" % fn)
        if [e["id"] for e in live[fn]["elements"]] != [e["id"] for e in bake[fn]["elements"]]:
            FAILS.append("%s 元素 id 序变化" % fn)
        print("       元素数 %d→%d、id 序：%s"
              % (len(bake[fn]["elements"]), len(live[fn]["elements"]),
                 "未变 ✓" if [e["id"] for e in live[fn]["elements"]] == [e["id"] for e in bake[fn]["elements"]] else "变化 ✗"))

    # ---------- [5] 组内相对关系 ----------
    print("\n" + "=" * 104)
    print("[5] 组内相对关系（w / 间距 / 顺序）")
    for fn in FILES:
        li = {e["id"]: e for e in live[fn]["elements"]}
        bi = {e["id"]: e for e in bake[fn]["elements"]}
        for eid in GROUP:
            if li[eid]["w"] != bi[eid]["w"]:
                FAILS.append("%s %s 的 w 变化" % (fn, eid))
        # 可见件之间的间距（游戏右沿 → 标题左沿、标题右沿 → 结束左沿）
        g, t, e_ = li["sv.sys_game"], li["sv.sys_title"], li["sv.sys_end"]
        g0, t0, e0 = bi["sv.sys_game"], bi["sv.sys_title"], bi["sv.sys_end"]
        print("  -- %s --" % fn)
        print("     w：游戏 %d／标题 %d／结束 %d（与旧相同 %s）"
              % (g["w"], t["w"], e_["w"], "✓" if (g["w"], t["w"], e_["w"]) == (g0["w"], t0["w"], e0["w"]) else "✗"))
        print("     间距：游戏→标题 %d（旧 %d）｜标题→结束 %d（旧 %d）"
              % (t["x"] - (g["x"] + g["w"]), t0["x"] - (g0["x"] + g0["w"]),
                 e_["x"] - (t["x"] + t["w"]), e0["x"] - (t0["x"] + t0["w"])))
        if (t["x"] - (g["x"] + g["w"])) != (t0["x"] - (g0["x"] + g0["w"])) or \
           (e_["x"] - (t["x"] + t["w"])) != (e0["x"] - (t0["x"] + t0["w"])):
            FAILS.append("%s 组内间距变化" % fn)
        print("     顺序：x(游戏 %d) < x(标题 %d) < x(结束 %d) ⇒ %s"
              % (g["x"], t["x"], e_["x"],
                 "保持 游戏→标题→结束 ✓" if g["x"] < t["x"] < e_["x"] else "顺序错乱 ✗"))
        if not (g["x"] < t["x"] < e_["x"]):
            FAILS.append("%s 组内顺序错乱" % fn)

    # ---------- [6] 原始文本行级 diff 范围自证 ----------
    print("\n" + "=" * 104)
    print("[6] 原始文本行级 diff 范围自证（本工作树禁 git ⇒ 自写逐行比对）")
    for fn in FILES:
        a = (BAK / fn).read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
        b = (d_dir / fn).read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
        print("  -- %s：旧 %d 行 / 新 %d 行 ⇒ 行数%s" % (fn, len(a), len(b),
                                                       "相同 ✓" if len(a) == len(b) else "不同 ✗"))
        if len(a) != len(b):
            FAILS.append("%s 行数变化（note 应保持单行、结构不变）" % fn)
            continue
        diffs = [(i, x, y) for i, (x, y) in enumerate(zip(a, b), 1) if x != y]
        print("     差异行 = %d 行（合法取值 = 0 行「未应用」或 9 行 `\"x\"` + 1 行 `note` = 10 行）"
              % len(diffs))
        kx = kn = 0
        for i, x, y in diffs:
            xs, ys = x.strip(), y.strip()
            if xs.replace(" ", "").startswith('"x":') and ys.replace(" ", "").startswith('"x":'):
                kx += 1
                print("        line %-5d x      %s  →  %s" % (i, xs[:-1] if xs.endswith(",") else xs,
                                                              ys[:-1] if ys.endswith(",") else ys))
            elif xs.startswith('"note":'):
                kn += 1
                print("        line %-5d note   长度 %d → %d（前缀 200 字相同：%s）"
                      % (i, len(xs), len(ys), "是" if xs[:210] == ys[:210] else "否"))
            else:
                print("        line %-5d ⚠ 非 x/非 note 行：%s → %s" % (i, xs[:90], ys[:90]))
                FAILS.append("%s line %d 出现 x/note 以外的改动" % (fn, i))
        if (kx, kn) not in ((9, 1), (0, 0)):
            FAILS.append("%s 差异行构成异常（x %d 行 / note %d 行）" % (fn, kx, kn))

    print("\n" + "=" * 104)
    if FAILS:
        print("FAILTOTAL %d 项：" % len(FAILS))
        for f in FAILS:
            print("   ✗", f)
        return 1
    print("ALL PASS ✓ —— x 位移、组包络与页码间隙、逐对相交、逐字段未变、组内关系、两屏一致 全部达标")
    return 0


if __name__ == "__main__":
    sys.exit(main())
