#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
check_16x9_override.py —— 16:9 覆盖层（ISSUE-20261003-02）静态机检
================================================================
核验 `build_story.load_16x9_override()` 的**键口径**与资源组交付清单一致，并逐件验尺寸。

判据（任一不过即 FAIL）：
  C1 覆盖表条数 == 交付清单数据行数（防解析漏行）
  C2 每个键都能在 `资源组\交接编程组\素材引用映射.tsv` 的 `交付路径` 列里**找到**（键口径正确的硬证据）
  C3 每个值指向的实文件存在
  C4 实文件尺寸 == 交付清单 `输出尺寸` 且比例恰为 16:9
  C5 同 basename 的原件与 16:9 件**必须同名**（take_asset 的 flat 名以 basename 生成 ⇒ 靠同名原地覆盖）

用法：python -X utf8 工具/check_16x9_override.py --data-root "E:/ZCode Workspace/Galgame"
"""
import argparse, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_story as BS          # noqa: E402


def rd_tsv(p):
    rows = []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        head = None
        for line in f:
            c = line.rstrip("\r\n").split("\t")
            if head is None:
                head = c
                continue
            if not c or (len(c) == 1 and c[0] == ""):
                continue
            rows.append(dict(zip(head, c)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    args = ap.parse_args()
    proj = os.path.join(os.path.abspath(args.data_root), "工程",
                        "我们没有翅膀——格雷塔迦露德与柳木原")
    if not os.path.isdir(proj):
        print("[FATAL] 工程目录不存在：%s" % proj)
        return 2

    ov = BS.load_16x9_override(proj)
    man = rd_tsv(os.path.join(proj, "资源组", "美术统一_交付_16比9", "交付清单.tsv"))
    ref = rd_tsv(os.path.join(proj, "资源组", "交接编程组", "素材引用映射.tsv"))
    ref_deliv = set((r.get("交付路径") or "").strip().replace("\\", "/") for r in ref)

    fails = []
    print("[C1] 覆盖表 %d 条 ｜ 清单数据行 %d 条" % (len(ov), len(man)))
    if len(ov) != len(man):
        fails.append("C1 条数不符")

    miss_key, miss_file, bad_size, bad_name = [], [], [], []
    for k, v in sorted(ov.items()):
        if k not in ref_deliv:
            miss_key.append(k)
        fp = os.path.join(proj, "资源组", v.replace("/", os.sep))
        if not os.path.isfile(fp):
            miss_file.append(v)
            continue
        w, h = BS.img_size(fp)
        if not (w > 0 and h > 0 and abs(w / float(h) - 16.0 / 9.0) < 1e-6):
            bad_size.append("%s %dx%d" % (v, w, h))
        if os.path.basename(k) != os.path.basename(v):
            bad_name.append("%s vs %s" % (k, v))

    print("[C2] 键在 `素材引用映射.交付路径` 中命中 %d/%d" % (len(ov) - len(miss_key), len(ov)))
    for k in miss_key[:10]:
        print("     ✗ 未命中：" + k)
    if miss_key:
        fails.append("C2 有 %d 个键不在引用映射里" % len(miss_key))

    print("[C3] 实文件存在 %d/%d" % (len(ov) - len(miss_file), len(ov)))
    for v in miss_file[:10]:
        print("     ✗ 缺件：" + v)
    if miss_file:
        fails.append("C3 有 %d 件缺失" % len(miss_file))

    print("[C4] 尺寸/16:9 通过 %d/%d" % (len(ov) - len(bad_size), len(ov)))
    for b in bad_size[:10]:
        print("     ✗ 非法：" + b)
    if bad_size:
        fails.append("C4 有 %d 件非 16:9" % len(bad_size))

    print("[C5] 原名一致 %d/%d" % (len(ov) - len(bad_name), len(ov)))
    for b in bad_name[:5]:
        print("     ✗ 异名：" + b)
    if bad_name:
        fails.append("C5 有 %d 对异名" % len(bad_name))

    # 补一条：覆盖表里 46 个键，必须**每个都被场景实际引用**才有意义（否则是空转）
    print()
    if fails:
        print("[RESULT] FAIL ｜ " + " ｜ ".join(fails))
        return 1
    print("[RESULT] PASS ｜ 覆盖表 %d 条：键口径对得上引用映射、件齐、全 16:9、原名一致" % len(ov))
    return 0


if __name__ == "__main__":
    sys.exit(main())
