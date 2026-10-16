#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_flow_data.py -- 离线自检工具（不参与 XP3 打包，放在 flow/tools/ 下）

它做的事（在没有 GUI、不能实机运行的前提下，把能静态验证的都验证掉）：
  1. 数据表检查：列数、空 id、重复 id、边端点是否存在、x/y 是否为数字。
  2. 布局检查：节点盒是否落在客户区内、是否压到抬头/底部面板。
  3. 文本覆盖检查：flow_nodes.csv 的 (storage,label) 在 flow_scene.tjs 里都有文本。
  4. 解锁可达性模拟：用 flow_lib.tjs 里同一套规则（visited + reqFlag/setFlag），
     模拟「只靠点击跳转 + 走掉一条已成立的入边」，验证整张图是否都能走到。
  5. TJS 语法卫生：括号/引号配平、函数是否都已定义（防止漏定义/拼错）。
     —— 这不是 TJS 解释器，只是把明显的手误挡住；真正的语法校验只能靠实机。

用法：python check_flow_data.py <flow\\game 目录>
退出码 0 = 全部通过，1 = 有失败项。
"""
import os
import re
import sys

BOX_W = 96
BOX_H = 42
WIN_W = 1000
WIN_H = 640
PANEL_TOP = 474          # flow_draw.tjs 里 flowDrawPanel 的 top
CHART_TOP_MIN = 66       # flowDrawHeader 下端

fails = []
warns = []


def fail(msg):
    fails.append(msg)
    print("  [FAIL] %s" % msg)


def warn(msg):
    warns.append(msg)
    print("  [WARN] %s" % msg)


def ok(msg):
    print("  [ ok ] %s" % msg)


def read_lines(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    return raw.decode("utf-8").splitlines()


def csv_rows(path):
    rows = []
    for i, line in enumerate(read_lines(path), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        rows.append((i, [c.strip() for c in s.split(",")]))
    return rows


def load_tables(game_dir):
    nodes = []
    for ln, f in csv_rows(os.path.join(game_dir, "flow_nodes.csv")):
        if len(f) < 10:
            fail("flow_nodes.csv:%d 列数不足(%d)" % (ln, len(f)))
            continue
        if f[0] == "id":
            continue                      # 表头（flow_lib.tjs 里也有同样的跳过逻辑）
        nodes.append(dict(id=f[0], title=f[1], route=f[2], level=f[3], x=f[4], y=f[5],
                          story=f[6], inFlag=f[7], storage=f[8], label=f[9], line=ln))
    edges = []
    for ln, f in csv_rows(os.path.join(game_dir, "flow_edges.csv")):
        if len(f) < 7:
            fail("flow_edges.csv:%d 列数不足(%d)" % (ln, len(f)))
            continue
        if f[0] == "id":
            continue
        edges.append(dict(id=f[0], src=f[1], dst=f[2], label=f[3], req=f[4],
                          setf=f[5], key=f[6], line=ln))
    return nodes, edges


def check_tables(nodes, edges):
    print("[1] 数据表检查")
    ids = set()
    for n in nodes:
        if not re.match(r"^[A-Za-z0-9_]+$", n["id"]):
            fail("节点 id 非法: %r" % n["id"])
        if n["id"] in ids:
            fail("节点 id 重复: %s" % n["id"])
        ids.add(n["id"])
        for k in ("x", "y", "level"):
            if not re.match(r"^-?\d+$", n[k]):
                fail("节点 %s 的 %s 不是整数: %r" % (n["id"], k, n[k]))
        if not n["title"]:
            fail("节点 %s 没有 title" % n["id"])
        if n["storage"] != "flow_scene.tjs":
            warn("节点 %s 的 storage=%r 不是 flow_scene.tjs" % (n["id"], n["storage"]))
        if "," in n["story"]:
            fail("节点 %s 的 story 含逗号（会被切列）" % n["id"])

    eids = set()
    for e in edges:
        if e["id"] in eids:
            fail("边 id 重复: %s" % e["id"])
        eids.add(e["id"])
        if e["src"] not in ids:
            fail("边 %s 的 from 节点不存在: %s" % (e["id"], e["src"]))
        if e["dst"] not in ids:
            fail("边 %s 的 to 节点不存在: %s" % (e["id"], e["dst"]))
        if e["key"] and not re.match(r"^[1-9]$", e["key"]):
            warn("边 %s 的 key=%r 不是 1..9 的数字键" % (e["id"], e["key"]))
    if len(nodes) < 10 or len(nodes) > 14:
        fail("节点数 %d 不在验收要求（10~14）内" % len(nodes))
    ok("节点 %d 个 / 边 %d 条" % (len(nodes), len(edges)))
    routes = sorted(set(n["route"] for n in nodes))
    ends = [n["id"] for n in nodes if n["route"] == "END"]
    omk = [n["id"] for n in nodes if n["route"] == "OMK"]
    ok("路线标记 = %s ；结局 %d 个 %s ；后日谈 %s" % (routes, len(ends), ends, omk))
    if len(ends) < 2:
        fail("结局节点少于 2 个")
    if len(omk) < 1:
        fail("没有后日谈节点")
    if not (set("AB") <= set(n["route"] for n in nodes)):
        fail("没有同时出现 A / B 两条路线")


def check_layout(nodes):
    print("[2] 布局检查（节点盒 %dx%d，客户区 %dx%d，面板顶边 y=%d）"
          % (BOX_W, BOX_H, WIN_W, WIN_H, PANEL_TOP))
    for n in nodes:
        x, y = int(n["x"]), int(n["y"])
        if x < 2 or x + BOX_W > WIN_W - 2:
            fail("节点 %s 横向越界: x=%d..%d" % (n["id"], x, x + BOX_W))
        if y < CHART_TOP_MIN or y + BOX_H > PANEL_TOP - 4:
            fail("节点 %s 纵向越界: y=%d..%d" % (n["id"], y, y + BOX_H))
    boxes = [(n["id"], int(n["x"]), int(n["y"])) for n in nodes]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[1] < b[1] + BOX_W and b[1] < a[1] + BOX_W and \
               a[2] < b[2] + BOX_H and b[2] < a[2] + BOX_H:
                fail("节点盒重叠: %s 与 %s" % (a[0], b[0]))
    ok("全部 %d 个节点盒都在画布内且互不重叠" % len(nodes))


def check_scene(nodes, game_dir):
    print("[3] 场景文本覆盖检查")
    src = open(os.path.join(game_dir, "flow_scene.tjs"), "rb").read().decode("utf-8")
    keys = set(re.findall(r'"([A-Za-z0-9_]+)"\s*=>', src))
    miss = []
    for n in nodes:
        if n["label"] not in keys:
            miss.append("%s(%s)" % (n["id"], n["label"]))
    if miss:
        fail("以下节点的 label 在 flow_scene.tjs 里没有文本: %s" % ", ".join(miss))
    else:
        ok("flow_scene.tjs 提供 %d 条文本，覆盖全部 %d 个节点" % (len(keys), len(nodes)))


def simulate(nodes, edges):
    print("[4] 解锁可达性模拟（与 flow_lib.tjs 同一套规则）")
    by_id = dict((n["id"], n) for n in nodes)
    out_e = dict((n["id"], []) for n in nodes)
    in_e = dict((n["id"], []) for n in nodes)
    for e in edges:
        out_e[e["src"]].append(e)
        in_e[e["dst"]].append(e)
    roots = [n["id"] for n in nodes if not in_e[n["id"]]]
    if len(roots) != 1:
        fail("根节点（无入边）应当恰好 1 个，实际 %d 个: %s" % (len(roots), roots))
        return
    visited = set(roots)
    taken = set()
    flags = set()
    for f in (by_id[roots[0]]["inFlag"],):
        if f:
            flags.add(f)

    def satisfied(e):
        return e["src"] in visited and (not e["req"] or e["req"] in flags)

    def unlocked(nid):
        if nid in visited:
            return True
        return any(satisfied(e) for e in in_e[nid]) or not in_e[nid]

    # 初始快照（必须在推进之前取）
    init_vis = sorted(visited)
    init_unl = [n["id"] for n in nodes if unlocked(n["id"])]

    step = 0
    while True:
        step += 1
        if step > 200:
            fail("模拟未收敛")
            return
        moved = False
        for n in nodes:                                    # 表顺序 = 数字键顺序
            nid = n["id"]
            if nid in visited or not unlocked(nid):
                continue
            cand = [e for e in in_e[nid] if satisfied(e) and e["id"] not in taken]
            if not cand:
                continue
            e = cand[0]
            taken.add(e["id"])
            if e["setf"]:
                flags.add(e["setf"])
            visited.add(nid)
            if n["inFlag"]:
                flags.add(n["inFlag"])
            moved = True
            break
        if not moved:
            break

    stuck = [n["id"] for n in nodes if n["id"] not in visited]
    print("      点击式推进后：已到达 %d/%d ；已走分支 %d/%d ；标记 %d 个"
          % (len(visited), len(nodes), len(taken), len(edges), len(flags)))
    if stuck:
        fail("只看点击永远走不到的节点: %s" % ", ".join(stuck))
    else:
        ok("全部 %d 个节点都能只靠点击跳转走到（含 %d 个结局与后日谈）"
           % (len(nodes), len([n for n in nodes if n["route"] in ("END", "OMK")])))

    # 反向检查：初始状态必须只有根已到达、只有它的直接后继解锁
    print("      初始状态：已到达 %s ；解锁 %s" % (init_vis, init_unl))
    if init_vis != sorted(roots):
        fail("初始已到达集合异常")
    missing_next = [e["dst"] for e in out_e[roots[0]] if e["dst"] not in init_unl]
    if missing_next:
        fail("根节点的直接后继没有解锁: %s" % missing_next)
    if len(init_unl) >= len(nodes):
        fail("初始状态就把所有节点解锁了（三态演示会失效）")
    else:
        ok("初始状态存在未解锁节点（灰态可见），三态着色可演示"
           "：已到达 %d / 已解锁 %d / 未解锁 %d"
           % (len(init_vis), len(init_unl), len(nodes) - len(init_unl)))


TJS_KEYWORDS = set("""
function class extends if else for while do switch case default break continue return
var new delete typeof instanceof in this super null true false void try catch finally throw
""".split())

CTOR_WHITELIST = set(["Timer", "Array", "Dictionary", "Layer", "Window", "Bitmap"])

# Window / Layer 的继承方法（本工程自己的类方法会由 function 定义被收进 defined）
INHERITED_METHODS = set(["add", "setInnerSize", "close", "finalize"])


def strip_tjs(src):
    out = []
    i, n = 0, len(src)
    state = None
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state = "line"
                i += 2
                continue
            if c == "/" and nxt == "*":
                state = "block"
                i += 2
                continue
            if c == '"' or c == "'":
                state = c
                out.append(" ")
                i += 1
                continue
            out.append(c)
            i += 1
        elif state == "line":
            if c == "\n":
                state = None
                out.append(c)
            i += 1
        elif state == "block":
            if c == "*" and nxt == "/":
                state = None
                i += 2
                continue
            if c == "\n":
                out.append("\n")
            i += 1
        else:  # 字符串字面量
            if c == "\\":
                i += 2
                continue
            if c == state or c == "\n":
                state = None
            i += 1
    return "".join(out)


def check_tjs(game_dir):
    print("[5] TJS 脚本静态检查（括号/引号配平、函数是否都已定义）")
    files = ["flow_lib.tjs", "flow_scene.tjs", "flow_draw.tjs", "startup.tjs"]
    codes = {}
    for fn in files:
        p = os.path.join(game_dir, fn)
        if not os.path.exists(p):
            fail("缺少脚本文件 %s" % fn)
            continue
        codes[fn] = strip_tjs(open(p, "rb").read().decode("utf-8"))

    defined = set()
    for fn, code in codes.items():
        defined |= set(re.findall(r"\bfunction\s+([A-Za-z_]\w*)\s*\(", code))
        defined |= set(re.findall(r"\bvar\s+([A-Za-z_]\w*)", code))

    for fn, code in codes.items():
        pairs = {"(": ")", "{": "}", "[": "]"}
        stack = []
        line = 1
        for ch in code:
            if ch == "\n":
                line += 1
            elif ch in pairs:
                stack.append((ch, line))
            elif ch in pairs.values():
                if not stack or pairs[stack[-1][0]] != ch:
                    fail("%s:%d 括号不配平（多余的 %s）" % (fn, line, ch))
                    break
                stack.pop()
        if stack:
            fail("%s:%d 括号未闭合（%s）" % (fn, stack[-1][1], stack[-1][0]))
        else:
            ok("%s 括号配平" % fn)

        unknown = []
        for m in re.finditer(r"([A-Za-z_]\w*)\s*\(", code):
            name = m.group(1)
            pre = code[max(0, m.start() - 6):m.start()]
            if name in TJS_KEYWORDS or name in defined or name in CTOR_WHITELIST:
                continue
            if name in INHERITED_METHODS:
                continue
            if re.search(r"(\.|\bnew\s*)$", pre):
                continue
            unknown.append((name, code[:m.start()].count("\n") + 1))
        if unknown:
            fail("%s 里出现未定义的函数调用: %s"
                 % (fn, ", ".join("%s()@%d" % (a, b) for a, b in unknown)))
        else:
            ok("%s 里所有函数调用都有定义" % fn)

    # 未定义但被引用的全局变量（只看本工程自己的 FLOW_/flow 前缀）
    all_code = "\n".join(codes.values())
    for name in sorted(set(re.findall(r"\bFLOW_[A-Z_]+", all_code))):
        if name not in defined:
            fail("用到了未定义的常量 %s" % name)
    if not fails:
        ok("FLOW_* 常量全部有定义")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    game_dir = os.path.abspath(sys.argv[1])
    print("=" * 70)
    print("flow 演示工程 静态自检 : %s" % game_dir)
    print("=" * 70)
    nodes, edges = load_tables(game_dir)
    check_tables(nodes, edges)
    check_layout(nodes)
    check_scene(nodes, game_dir)
    simulate(nodes, edges)
    check_tjs(game_dir)
    print("=" * 70)
    print("结果：%d 项失败 / %d 项告警" % (len(fails), len(warns)))
    if fails:
        for f in fails:
            print("  FAIL : %s" % f)
    print("=" * 70)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
