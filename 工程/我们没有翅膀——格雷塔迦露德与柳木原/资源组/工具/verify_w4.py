# -*- coding: utf-8 -*-
r"""
W4 验收自证脚本（6 项）
用法：python verify_w4.py
只读：不修改任何文件。
"""
import collections
import filecmp
import json
import os
import random
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect_assets import SOURCES, LIB  # noqa

KEYS = ["otr", "otp", "np"]
NAME_RE = re.compile(r"^[^/]+/[^/]+/(otr|otp|np)_[a-z0-9_.\-]+\.(png|ogg|mpg|mp4|txt|dat|gmp|lag)$")


def main():
    print("=" * 78)
    print("W4 验收自证")
    print("=" * 78)

    # ---------- 1. 文件数 ----------
    print("\n[1] 文件数（清单 == 磁盘 == 源素材数）")
    all_ok = True
    for k in KEYS:
        root = os.path.join(LIB, k)
        disk = [os.path.join(dp, f) for dp, _, fs in os.walk(root)
                for f in fs if not f.startswith("_")]
        man = json.load(open(os.path.join(root, "_清单.json"), encoding="utf-8"))
        src_n = 0
        for sub, kind, archive in SOURCES[k]["dirs"]:
            sd = os.path.join(SOURCES[k]["root"], sub)
            src_n += len([f for f in os.listdir(sd) if os.path.isfile(os.path.join(sd, f))])
        ok = len(disk) == len(man) == src_n
        all_ok &= ok
        print("    %-4s 源素材=%d  清单=%d  磁盘=%d  %s" % (
            k, src_n, len(man), len(disk), "OK" if ok else "MISMATCH"))
    print("    -> %s" % ("全部一致" if all_ok else "存在不一致"))

    # ---------- 2. 零字节 ----------
    print("\n[2] 零字节文件数")
    zero = []
    for k in KEYS:
        for dp, _, fs in os.walk(os.path.join(LIB, k)):
            for f in fs:
                if f.startswith("_"):
                    continue
                p = os.path.join(dp, f)
                if os.path.getsize(p) == 0:
                    zero.append(p)
    print("    零字节文件数 = %d  %s" % (len(zero), "OK" if not zero else "FAIL"))
    for z in zero[:20]:
        print("      ", z)

    # ---------- 3. 命名合规 ----------
    print("\n[3] 命名合规（前缀 + 小写 + 允许扩展名）")
    files = []
    for k in KEYS:
        root = os.path.join(LIB, k)
        for dp, _, fs in os.walk(root):
            for f in fs:
                if f.startswith("_"):
                    continue
                rel = os.path.relpath(os.path.join(dp, f), LIB).replace("\\", "/")
                files.append(rel)
    files.sort()
    bad = [f for f in files if not NAME_RE.match(f)]
    print("    检查文件数 = %d" % len(files))
    print("    违规数 = %d  %s" % (len(bad), "OK" if not bad else "FAIL"))
    for b in bad[:20]:
        print("      ", b)
    # 任务书字面版正则（不含 kind 子目录层）——与强制布局不符，一并统计
    lit_re = re.compile(r"^[^/]+/(otr|otp|np)_[a-z0-9_.\-]+\.(png|ogg|mpg|mp4|txt|dat|gmp|lag)$")
    lit_bad = [f for f in files if not lit_re.match(f)]
    print("    （任务书字面版正则违规数 = %d / %d —— 因强制布局含 kind 子目录，见报告「正则口径说明」）"
          % (len(lit_bad), len(files)))

    # ---------- 4. 原字节保真抽查 ----------
    print("\n[4] 原字节保真抽查（每源随机 20 个，cmp 源 vs 归集）")
    random.seed(20260918)
    total_checked = 0
    mism = []
    for k in KEYS:
        arch2sub = {a: s for s, kind, a in SOURCES[k]["dirs"]}
        root = os.path.join(LIB, k)
        man = json.load(open(os.path.join(root, "_清单.json"), encoding="utf-8"))
        sample = random.sample(man, min(20, len(man)))
        okc = 0
        for e in sample:
            src = os.path.join(SOURCES[k]["root"], arch2sub[e["archive"]], e["orig_name"])
            dst = os.path.join(root, e["out_relpath"])
            total_checked += 1
            if filecmp.cmp(src, dst, shallow=False):
                okc += 1
            else:
                mism.append((src, dst))
        print("    %-4s 抽查 20，相同 %d  %s" % (k, okc, "OK" if okc == 20 else "FAIL"))
    print("    -> 合计抽查 %d，不同 %d  %s" % (
        total_checked, len(mism), "OK" if not mism else "FAIL"))
    for m in mism:
        print("      DIFF", m)

    # ---------- 5. 清单自洽 ----------
    print("\n[5] 清单自洽（条数==磁盘 / out_relpath 存在 / 无重复）")
    for k in KEYS:
        root = os.path.join(LIB, k)
        man = json.load(open(os.path.join(root, "_清单.json"), encoding="utf-8"))
        disk_n = len([f for dp, _, fs in os.walk(root) for f in fs if not f.startswith("_")])
        missing = [e["out_relpath"] for e in man
                   if not os.path.isfile(os.path.join(root, e["out_relpath"]))]
        rel = [e["out_relpath"] for e in man]
        dup = [x for x, c in collections.Counter(rel).items() if c > 1]
        keys_ok = all(set(e.keys()) == {"archive", "orig_name", "kind", "src_bytes",
                                        "out_relpath", "out_bytes"} for e in man)
        print("    %-4s 条数=%d 磁盘=%d 缺失=%d 重复=%d 字段一致=%s %s" % (
            k, len(man), disk_n, len(missing), len(dup), keys_ok,
            "OK" if (len(man) == disk_n and not missing and not dup and keys_ok) else "FAIL"))
        for m in missing[:5]:
            print("      MISS", m)

    # ---------- 6. 冲突报告 ----------
    print("\n[6] 冲突报告")
    d = json.load(open(os.path.join(LIB, "_冲突数据.json"), encoding="utf-8"))
    print("    总文件=%d 跨源同名组=%d 同名不同内容组=%d 同名相同内容组=%d" % (
        d["total_files"], d["cross_source_stems"], d["diff_groups"], d["same_groups"]))
    print("    必查项 8 个：")
    for stem, m in d["must_check"].items():
        srcs = sorted(set(r["src"] for r in m["entries"]))
        print("      %-8s %-22s %s" % (stem, ",".join(srcs), "不同" if not m["same"] else "相同"))
    print("    报告文件：_冲突报告.md / _同名冲突明细.tsv / _冲突数据.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())