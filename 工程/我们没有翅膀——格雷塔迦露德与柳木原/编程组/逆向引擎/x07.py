#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""x07.py — op 0x07（变长表跳）定位与表形态检视（只读）。

引擎语义（handler VA 0x433720，直读）：
    0x00433720  mov eax, dword ptr [edi]              ; idx = *op
    0x00433722  mov ecx, dword ptr [edi + eax*4 + 4]  ; t = table[idx]
    0x00433726  mov dword ptr [esi + 8], ecx          ; pc = t
    （edi = 操作数区 = 0x07 之后第一个字；pc 直接改，无 fallthrough）

⇒ 磁盘形态 `[07][idx][t0][t1]…[tN][0xFFFFFFFF]`，表基址 = idx 字 + 1 字。
  表尾哨兵 0xFFFFFFFF。

本脚本：
  * 用引擎 VM 长度表线性走查每个 .sob，遇 0x07 时：读 idx，扫到 0xFFFFFFFF 取表，
    从表尾之后继续走查（不中断）。
  * 报每个 0x07 站点：cell 号 / 字节偏移 / idx / 表项数 / 每项属于哪张 maps（及其值）。
  * 判定 idx 字**是否**是任一 maps 的键（= 装载期是否会被重定位覆盖）。
  * `--dump <file>` 打印该文件 0x07 站点前后逐字（含 maps 标注）。

用法：
  python -X utf8 x07.py --all  "E:/.../解包/SCRIPT"
  python -X utf8 x07.py --file "E:/.../解包/SCRIPT/func_lib.sob"
  python -X utf8 x07.py --dump "E:/.../解包/SCRIPT/func_lib.sob" 0x<byteoff>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "工具"))
from decode_sob0 import Sob0  # noqa: E402

# 引擎 VM「操作数字数 + 1」= 项总字数（由各 handler 反汇编读出，同 xwalk.py）
VM_LEN = {0x00: 1, 0x01: 1, 0x02: 2, 0x03: 2, 0x04: 2, 0x05: 4, 0x06: 2,
          0x07: 0, 0x08: 2, 0x09: 2, 0x0A: 2, 0x0B: 2, 0x0C: 2, 0x0D: 4,
          0x0E: 4, 0x0F: 4, 0x10: 4, 0x11: 4, 0x12: 4, 0x13: 4, 0x14: 4,
          0x15: 4, 0x16: 3, 0x17: 3, 0x18: 4, 0x19: 4, 0x1A: 2, 0x1B: 2,
          0x1C: 2, 0x1D: 2, 0x1E: 3, 0x1F: 3, 0x20: 3, 0x21: 3, 0x22: 3,
          0x23: 3, 0x24: 3, 0x25: 3, 0x26: 3, 0x27: 3, 0x28: 3, 0x29: 4,
          0x2A: 4, 0x2B: 4, 0x2C: 4, 0x2D: 4, 0x2E: 4}
SENTINEL = 0xFFFFFFFF


def walk07(cells):
    """线性走查，返回 (sites, bad_positions, oob)。sites = [(cell_idx, idx, [table], end_idx)]"""
    i = 0
    n = len(cells)
    sites = []
    bad = []
    while i < n:
        t = cells[i]
        if t > 0x2E:
            bad.append((i, t))
            i += 1
            continue
        if t == 0x07:
            if i + 1 >= n:
                bad.append((i, "trunc-idx"))
                break
            idx = cells[i + 1]
            j = i + 2
            while j < n and cells[j] != SENTINEL:
                j += 1
            table = cells[i + 2:j]
            sites.append((i, idx, table, j))
            i = j + 1 if j < n else n
            continue
        i += VM_LEN.get(t, 1)
    return sites, bad


OPS = {i: "op%02X" % i for i in range(0x2F)}
# 各 op 的「写入型」操作数下标（据 执行模型.md §4.4 语义：*dst = …）
DEST_OPERAND = {0x03: 0, 0x0A: 0, 0x1F: 1, 0x20: 1, 0x21: 1, 0x23: 1,
                0x1A: 0, 0x1B: 0, 0x1C: 0, 0x1D: 0}


def decode_items(cells):
    """线性解码：返回 [(op_cell, op, [operand_cells])]（遇 0x07 时吞掉 idx+表+哨兵）。"""
    items = []
    i = 0
    n = len(cells)
    while i < n:
        t = cells[i]
        if t > 0x2E:
            break
        if t == 0x07:
            j = i + 2
            while j < n and cells[j] != SENTINEL:
                j += 1
            items.append((i, t, list(range(i + 1, j + 1))))
            i = j + 1 if j < n else n
            continue
        L = VM_LEN.get(t, 1) - 1
        ops = list(range(i + 1, min(i + 1 + L, n)))
        items.append((i, t, ops))
        i += VM_LEN.get(t, 1)
    return items


def index_writers(sob, site_cell):
    """找「把值写进 0x07 的 idx 槽（byte=site_cell*4+4）」的指令。

    idx 槽字节偏移 = (site_cell+1)*4；其 maps[4] 目标值 = 该偏移（若被引用）。
    逐条解码，检查 dest 操作数是否为指向该偏移的 maps[4] 引用。
    """
    idx_off = (site_cell + 1) * 4
    out = []
    for (oc, op, ops) in decode_items(sob.cells):
        d = DEST_OPERAND.get(op)
        if d is None or d >= len(ops):
            continue
        oc2 = ops[d]
        site = oc2 * 4
        if site in sob.maps[4] and sob.maps[4][site] == idx_off:
            src = ops[0] if len(ops) > 0 else None
            srcv = sob.cells[src] if src is not None else None
            srcmap = map_of(sob, src) if src is not None else []
            out.append((oc, op, oc2, "src_cell=%s val=0x%X maps=%s"
                        % (src, srcv if srcv is not None else 0, srcmap)))
        # 0x22/0x24/0x25 的 (sp-op) 形成是针对栈，不指向代码槽，跳过
    return out


def refs_to(sob, byte_off):
    """统计指向该代码字节偏移的 maps[4] code 引用（站址列表）。"""
    return [site for site, v in sob.maps[4].items()
            if v == byte_off and byte_off < sob.ss]


def collect_entries(script_dir):
    """扫全部 .sob 的 maps[3] 值（= func_lib 子程序入口偏移）并集。"""
    vals = set()
    for fn in sorted(os.listdir(script_dir)):
        if not fn.lower().endswith(".sob"):
            continue
        try:
            s = Sob0(os.path.join(script_dir, fn))
        except Exception:
            continue
        for v in s.maps[3].values():
            vals.add(v)
    return vals


def map_of(sob, cell_idx):
    """cell 号 → 该字在哪些 maps 里（键 = cell_idx*4）。"""
    site = cell_idx * 4
    hits = []
    for name, m in zip(("maps0", "maps1", "maps2", "maps3", "maps4"), sob.maps):
        if site in m:
            hits.append("%s=0x%X" % (name, m[site]))
    return hits


def target_of(sob, cell_idx):
    """若该字是引用字，返回重定位后的目标描述（相对 header_end 的偏移）。"""
    site = cell_idx * 4
    if site in sob.maps[4]:
        v = sob.maps[4][site]
        kind = "str" if sob.ss <= v < sob.se else "code"
        return "%s@0x%X" % (kind, v)
    return None


def report_file(path, dump_off=None, dec_from=None):
    try:
        sob = Sob0(path)
    except Exception as e:
        print("  [skip] %s : %s" % (os.path.basename(path), e))
        return None
    sites, bad = walk07(sob.cells)
    print("== %s  cells=%d  header_end=0x%X ss=0x%X se=0x%X  bad=%d  0x07_sites=%d"
          % (os.path.basename(path), len(sob.cells), sob.header_end, sob.ss, sob.se,
             len(bad), len(sites)))
    for (i, idx, table, endj) in sites:
        print("   * 0x07 @cell[%d] byte=0x%X | idx=%d (0x%X) | table=%d entries | end@cell[%d]"
              % (i, i * 4, idx, idx, len(table), endj))
        print("       idx word maps: %s" % (map_of(sob, i + 1) or "(none -> stays %d at runtime)" % idx))
        for k, w in enumerate(table):
            print("         t[%d] = 0x%08X  maps=%s  -> %s"
                  % (k, w, map_of(sob, i + 2 + k) or "-", target_of(sob, i + 2 + k) or "-"))
        w = index_writers(sob, i)
        print("       idx-slot writers (store into idx word): %s"
              % (w if w else "NONE"))
        r_op = refs_to(sob, i * 4)
        r_idx = refs_to(sob, (i + 1) * 4)
        print("       code-refs to 0x07 opcode offset : %s"
              % ([hex(x) for x in r_op] if r_op else "NONE -> only reachable via straight-line store"))
        print("       code-refs to idx-slot offset    : %s"
              % ([hex(x) for x in r_idx] if r_idx else "NONE"))
    if dump_off is not None:
        w0 = dump_off // 4
        print("  -- dump around byte 0x%X (cell %d) --" % (dump_off, w0))
        for c in range(max(0, w0 - 10), min(len(sob.cells), w0 + 30)):
            mk = " <== 0x07" if c == w0 else ""
            print("     cell[%d] byte=0x%X = 0x%08X%s  %s"
                  % (c, c * 4, sob.cells[c], mk, map_of(sob, c)))
    if dec_from is not None:
        print("  -- decode from cell %d --" % dec_from)
        for (oc, op, ops) in decode_items(sob.cells):
            if oc < dec_from:
                continue
            if oc > dec_from + 60:
                break
            ann = []
            for k, o in enumerate(ops):
                ann.append("[%d]=0x%X %s" % (k, sob.cells[o], map_of(sob, o) or ""))
            print("     cell[%d] %s  %s" % (oc, OPS.get(op, "?"), "  ".join(ann)))
    return sites


def enclosing_sub(sobs, target_byte):
    """给定目标字节偏移，返回 func_lib 内「允许的最晚入口 V ≤ target」——即所在子程序入口。"""
    entries = sorted(v for v in sobs if 0 <= v <= target_byte)
    return entries[-1] if entries else None


def sub_report(func_lib, script_dir, target_byte, nops=60):
    sob = Sob0(func_lib)
    entries_all = collect_entries(script_dir)
    entries = sorted(v for v in entries_all if 0 <= v < sob.ss)
    print("== func_lib=%s  ss=0x%X  entries(∈func_lib)=%d =="
          % (os.path.basename(func_lib), sob.ss, len(entries)))
    ent = enclosing_sub(entries, target_byte)
    print("   target byte 0x%X -> enclosing entry V = 0x%X" % (target_byte, ent) if ent is not None
          else "   target 0x%X: no enclosing entry" % target_byte)
    # 也列出目标附近的入口
    near = [v for v in entries if abs(v - target_byte) < 0x400]
    print("   entries within 0x400: %s" % [hex(v) for v in near])
    # 场景入口不够时：找 func_lib 内部引用指向 [target-0x1000, target] 的候选入口
    cand = sorted({v for v in sob.maps[4].values()
                   if target_byte - 0x1000 <= v <= target_byte and v < sob.ss})
    print("   internal code-ref targets in [target-0x1000,target]: %s"
          % [hex(v) for v in cand[-12:]])
    # 收集 func_lib 内部 op 0x04 CALL 的目标（maps[3] 或 maps[4] code ref）
    call_targets = set(entries)
    for (oc, op, ops) in decode_items(sob.cells):
        if op == 0x04 and ops:
            site = ops[0] * 4
            for m in (sob.maps[3], sob.maps[4]):
                if site in m and m[site] < sob.ss:
                    call_targets.add(m[site])
    print("   CALL-derived entries (incl internal) = %d" % len(call_targets))
    ent2 = enclosing_sub(sorted(call_targets), target_byte)
    print("   enclosing CALL-entry = %s" % (hex(ent2) if ent2 is not None else "NONE"))
    if ent is None:
        ent = ent2
        print("   -> use CALL-entry: %s" % (hex(ent) if ent is not None else "NONE"))
    if ent is None:
        return
    print("   -- decode from entry 0x%X --" % ent)
    for (oc, op, ops) in decode_items(sob.cells):
        if oc * 4 < ent:
            continue
        if oc * 4 > ent + nops * 4:
            break
        ann = []
        for k, o in enumerate(ops):
            ann.append("[%d]=0x%X %s" % (k, sob.cells[o], map_of(sob, o) or ""))
        print("     cell[%d] byte=0x%X %s  %s" % (oc, oc * 4, OPS.get(op, "?"), "  ".join(ann)))


def walk07_mut(cells, delta):
    """变异走查：表尾判定偏移 delta（0=正确哨兵；+1=把哨兵当表项；-1=少读一项）。
    返回 (bad_count, end_ok)。"""
    i, n = 0, len(cells)
    bad = 0
    while i < n:
        t = cells[i]
        if t > 0x2E:
            bad += 1
            i += 1
            continue
        if t == 0x07:
            j = i + 2
            while j < n and cells[j] != SENTINEL:
                j += 1
            j += delta
            if j < i + 2 or j >= n:
                return bad, False
            i = j + 1
            continue
        i += VM_LEN.get(t, 1)
    return bad, (i == n or True)


def selftest(script_dir):
    names = ["eyecatch.sob", "func_lib.sob", "gallery.sob", "main.sob",
             "scskip.sob", "ssskip.sob"]
    for fn in names:
        p = os.path.join(script_dir, fn)
        if not os.path.exists(p):
            continue
        sob = Sob0(p)
        r0 = walk07_mut(sob.cells, 0)
        rp = walk07_mut(sob.cells, +1)
        rm = walk07_mut(sob.cells, -1)
        print("  %-14s correct(+0): bad=%d | +1(include sentinel): bad=%d | -1(short): bad=%d"
              % (fn, r0[0], rp[0], rm[0]))


def main():
    a = sys.argv[1:]
    if "--selftest" in a:
        print("== op 0x07 table-end mutation self-test (only files containing 0x07) ==")
        selftest(a[a.index("--selftest") + 1])
        return
    if "--sub" in a:
        fl = a[a.index("--sub") + 1]
        sd = a[a.index("--scriptdir") + 1]
        tb = int(a[a.index("--target") + 1], 0)
        sub_report(fl, sd, tb)
        return
    if "--all" in a:
        root = a[a.index("--all") + 1]
        ext = a[a.index("--ext") + 1] if "--ext" in a else ".sob"
        tot = 0
        for fn in sorted(os.listdir(root)):
            if fn.lower().endswith(ext):
                s = report_file(os.path.join(root, fn))
                if s:
                    tot += len(s)
        print("== total 0x07 sites = %d ==" % tot)
    elif "--file" in a:
        p = a[a.index("--file") + 1]
        off = int(a[a.index("--dump") + 1], 0) if "--dump" in a else None
        dec = (int(a[a.index("--decode") + 1], 0) // 4) if "--decode" in a else None
        report_file(p, off, dec)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
