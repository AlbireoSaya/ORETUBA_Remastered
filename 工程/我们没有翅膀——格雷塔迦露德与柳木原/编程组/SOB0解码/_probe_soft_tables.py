# -*- coding: utf-8 -*-
"""SOB0 六张软表探针 · ISSUE-20261007-09（**只读**，不写任何文件）

用途：把 SOB0 容器六张表的语义以「可复算的断言」固定下来，供后续解码器引用。
本工具**不产出数据**，只做核验与统计；`--check` 失败即 exit 1。

用法（路径一律给正斜杠即可）：
  python -X utf8 编程组/SOB0解码/_probe_soft_tables.py --root <ot脚本目录>
  python -X utf8 编程组/SOB0解码/_probe_soft_tables.py --root <ot脚本目录> --check
  python -X utf8 编程组/SOB0解码/_probe_soft_tables.py --root <ot目录> --alt <otr目录>

结论（本工具核验的就是这几条，详见同目录「软表解出_说明.md」）：
  1. 容器恒等式：header_end == table_size + 16；header_end + strings_end == 文件长度。
  2. maps[1][k] == cells[k//4] - 1   （立即数标记，值冗余）
  3. maps[3][k] == cells[k//4]       （立即数标记，值冗余）
  4. keys(maps[0]) 与 keys(maps[4]) 构成「页引用字（高 12 位 0x017/0x018）」的**精确二分**：
     两集合不相交，并集恰等于全部页引用站点。
  5. 命令节点判据可由 maps[3] 背书：V 字是 maps[3] 的键 ⇒ 真命令；
     另一族（k==4 且非 maps[3] 键）是**跳转**；其余为形态假阳性。
"""
import argparse
import collections
import os
import struct
import sys

MAGICS = (b"SOB0", b"SOB1", b"SOB2")
PAGE_HIGH = (0x017, 0x018)   # 页引用字的高 12 位

# 系统脚本（非剧情）：代码区混有**数据数组**，故「页引用站点精确二分」这条恒等式
# 在这些文件上**不成立**（maps[0]/maps[4] 键会比站点多出若干）。这是已知例外，
# 必须**逐名列出**，不得笼统说"个别文件例外"。
SYSTEM_SCRIPTS = frozenset((
    "config1", "config2", "eyecatch", "func_lib", "gallery", "history", "logo",
    "movieplay", "saveload", "scskip", "ssskip", "title", "title2",
))


def is_system(fn):
    return os.path.splitext(fn)[0].lower() in SYSTEM_SCRIPTS


def parse_container(path):
    b = open(path, "rb").read()
    magic = b[:4]
    if magic not in MAGICS:
        raise ValueError("not SOB: %r" % magic)
    table_size = struct.unpack_from("<I", b, 4)[0]
    off = 8
    tabs = []
    for _ in range(6):
        n = struct.unpack_from("<I", b, off)[0]
        d = {}
        for k in range(n):
            key, val = struct.unpack_from("<II", b, off + 4 + k * 8)
            d[key] = val
        tabs.append(d)
        off += 4 + n * 8
    ss, se = struct.unpack_from("<II", b, off)
    header_end = off + 8
    return dict(raw=b, magic=magic, table_size=table_size, maps=tabs,
                ss=ss, se=se, header_end=header_end)


def cells_of(c):
    """代码区 = [header_end, header_end + strings_start)，每 4 字节一字。"""
    code = c["raw"][c["header_end"]: c["header_end"] + c["ss"]]
    n = len(code) // 4
    return struct.unpack_from("<%dI" % n, code)


def ref_sites(cells):
    """全部「页引用字」的字节偏移（高 12 位 ∈ {0x017,0x018}）。"""
    out = set()
    for i, w in enumerate(cells):
        if (w >> 20) in PAGE_HIGH:
            out.add(i * 4)
    return out


def scan_commands(c):
    """把 [04][V][0C][k][03][REF] 分成 命令 / 跳转 / 假阳性。

    判据（两条互相独立）：
      · 背书位：`(i+1)*4 ∈ keys(maps[3])`（V 字是引擎自带的「立即数」位）。
      · 尾 REF：`maps[4][(i+5)*4]` 落在**串区** ⇒ 命令（尾为空串）；
                落在**代码区** ⇒ 跳转（尾是 CREF）。
    两者组合：命令 = 背书 ∧ 尾在串区；跳转 = 背书 ∧ 尾在代码区；假阳性 = 无背书。
    """
    cells = cells_of(c)
    m3, m4 = c["maps"][3], c["maps"][4]
    ss, se = c["ss"], c["se"]
    raw = c["raw"]
    he = c["header_end"]
    cmd = collections.Counter()
    disp = collections.Counter()      # 跳转族：尾 REF 目标相对本站的字节位移
    n_jump = n_fake = n_classic = 0
    for i in range(len(cells) - 6):
        if cells[i] != 4 or cells[i + 2] != 0x0C or cells[i + 4] != 3:
            continue
        tail = m4.get((i + 5) * 4)
        # 旧判据（形态启发式，不要求 maps[3] 背书）：尾 REF → 空串
        if tail is not None and ss <= tail < se and raw[he + tail] == 0:
            n_classic += 1
        if (i + 1) * 4 not in m3:
            n_fake += 1
            continue
        if tail is not None and ss <= tail < se:
            cmd[cells[i + 1]] += 1
        elif tail is not None and tail < ss and cells[i + 3] == 4:
            n_jump += 1          # 跳转族还要求 k == 0x04（单实参）
            disp[tail - (i + 5) * 4] += 1
        else:
            n_fake += 1
    return cmd, n_jump, n_fake, n_classic, disp


def open_parse(root):
    return parse_container(root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="ot（SOB0）脚本目录")
    ap.add_argument("--alt", default="", help="可选对照源（如 otr）目录，用于比对命令 V 集合")
    ap.add_argument("--check", action="store_true", help="断言恒等式；失败 exit 1")
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(a.root) if f.lower().endswith(".sob"))
    tot = collections.Counter()
    tot_disp = collections.Counter()
    fails = []
    vs_all = collections.Counter()
    vs_story = collections.Counter()

    for fn in files:
        p = os.path.join(a.root, fn)
        try:
            c = parse_container(p)
        except Exception as e:
            tot["skip"] += 1
            continue
        if c["magic"] == b"SOB1":
            tot["sob1"] += 1
            continue
        tot["files"] += 1
        cells = cells_of(c)
        m = c["maps"]

        # 恒等式 1
        if c["header_end"] != c["table_size"] + 16:
            fails.append((fn, "header_end != table_size+16"))
        if c["header_end"] + c["se"] != len(c["raw"]):
            fails.append((fn, "header_end+strings_end != filesize"))

        # 恒等式 2 / 3
        for ti, delta in ((1, 1), (3, 0)):
            bad = 0
            for k, v in m[ti].items():
                i = k // 4
                if i >= len(cells) or cells[i] - delta != v:
                    bad += 1
            tot["map%d_keys" % ti] += len(m[ti])
            tot["map%d_bad" % ti] += bad
            if bad and a.check:
                fails.append((fn, "maps[%d] 非恒等 %d 处" % (ti, bad)))

        # 恒等式 4：maps[0] ∪ maps[4] == 页引用站点（系统脚本按设计不成立，见 SYSTEM_SCRIPTS）
        k0, k4, sites = set(m[0]), set(m[4]), ref_sites(cells)
        tot["sites"] += len(sites)
        if (k0 | k4) != sites or (k0 & k4):
            if is_system(fn):
                tot["sys_exc"] += 1
            else:
                fails.append((fn, "页引用站点未被 maps[0]/maps[4] 精确二分：|并|=%d |sites|=%d 交=%d"
                              % (len(k0 | k4), len(sites), len(k0 & k4))))

        cmd, n_jump, n_fake, n_classic, disp = scan_commands(c)
        tot_disp.update(disp)
        tot["cmd"] += sum(cmd.values())
        tot["jump"] += n_jump
        tot["fake"] += n_fake
        tot["classic"] += n_classic
        vs_all.update(cmd)
        if not is_system(fn):
            vs_story.update(cmd)

    print("== 容器统计 ==")
    for k in ("files", "sob1", "skip", "sites", "classic", "cmd", "jump", "fake", "sys_exc",
              "map1_keys", "map3_keys", "map1_bad", "map3_bad"):
        if tot[k]:
            print("  %-10s %d" % (k, tot[k]))
    print("  （sys_exc = 恒等式 4 在系统脚本上的已知例外数，应为 %d）" % len(SYSTEM_SCRIPTS))
    if tot_disp:
        print("== 跳转族尾 REF 位移（相对本站，字节）==")
        for d, n in tot_disp.most_common(6):
            print("  %+5d  %d" % (d, n))
    print("== 命令 V ==")
    print("  全库不同 V = %d（节点 %d）" % (len(vs_all), sum(vs_all.values())))
    print("  剧情脚本口径不同 V = %d（节点 %d）" % (len(vs_story), sum(vs_story.values())))

    if a.alt:
        alt_vs, alt_story = collections.Counter(), collections.Counter()
        for fn in sorted(f for f in os.listdir(a.alt) if f.lower().endswith(".sob")):
            try:
                c = parse_container(os.path.join(a.alt, fn))
            except Exception:
                continue
            if c["magic"] == b"SOB1":
                continue
            cmd = scan_commands(c)[0]
            alt_vs.update(cmd)
            if not is_system(fn):
                alt_story.update(cmd)
        st = lambda d: set(d)
        print("== 对照（两套口径都要看）==")
        for tag, x, y in (("全库", vs_all, alt_vs), ("剧情（剔系统脚本）", vs_story, alt_story)):
            print("  %-14s root=%d alt=%d 交集=%d 差(root-alt)=%d 差(alt-root)=%d"
                  % (tag, len(x), len(y), len(st(x) & st(y)),
                     len(st(x) - st(y)), len(st(y) - st(x))))

    if a.check:
        if fails:
            print(">>> FAIL：%d 处" % len(fails))
            for fn, msg in fails[:20]:
                print("   ", fn, msg)
            return 1
        print(">>> PASS（全部恒等式成立）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
