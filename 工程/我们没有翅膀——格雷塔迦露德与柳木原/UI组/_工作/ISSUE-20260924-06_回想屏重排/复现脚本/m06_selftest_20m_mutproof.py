# -*- coding: utf-8 -*-
r"""M06 一审 A2 · ⑳m **变异自证**：证明「坏按钮不画」这条断言**真的会 FAIL**。

■ 背景（一审原话）
  旧断言用 `[data-ui-item-btn=""]` 兜「缺 key」那一条，但 `btnSysKey` 对缺 key **恒返回
  `#<下标>`** ⇒ 该选择器永不匹配，断言是**空断言**。一审变异证明：把 `replica.js` 里
  「非法项不画」放行 `#` 开头键后，DOM 出现 4 个 `data-ui-item-btn="#4"`，⑳m 仍打印
  「坏按钮 DOM 节点=0」ALL PASS。

■ 本脚本（与 m06_editor_probe_mut.py 同一套路：备份 → 变异 → 跑 → 逐字节还原）
  1. 备份 `复刻\replica.js`（md5 记账）；
  2. 变异：`if (btnBad[bk]) return;` → 对 `#` 开头的键**放行**（只改这一行）；
  3. 跑 m39 自检 A（`_selftest_states.html`，含 ⑳m），抽 ⑳m 判定；
  4. **逐字节还原**并核 md5；
  5. 打印结论：变异下 ⑳m 必须 FAIL（否则断言仍是空断言）；还原后必须 PASS。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\复现脚本\m06_selftest_20m_mutproof.py
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(ISSUE))
REP = os.path.join(UI, "复刻")
REPLICA = os.path.join(REP, "replica.js")
BACKUP = os.path.join(ISSUE, "证据", "_mut_20m_replica.js.bak")
M39 = os.path.join(UI, "_工作", "ISSUE-20260923-01_M39_证据", "复现脚本", "m39_run_html_selftests.py")

ORIG = "if (btnBad[bk]) return;"
MUT = "if (btnBad[bk] && String(bk).charAt(0) !== '#') return;"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def run_selftest_a():
    r = subprocess.run([sys.executable, M39, "--only", "A"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=UI)
    return r.stdout.decode("utf-8", "replace")


def line_20m(txt):
    """⑳m 的**整行**（含 `SELFTEST OK/FAIL` 前缀 —— say() 把判定写在名字之前）。"""
    m = re.search(r"SELFTEST (?:OK|FAIL) +⑳m[^<\n]*", txt)
    if m:
        return m.group(0).strip()
    m = re.search(r"⑳m[^<\n]*", txt)
    return m.group(0).strip() if m else "(未找到 ⑳m 行)"


def verdict_20m(txt):
    l = line_20m(txt)
    if l.startswith("SELFTEST FAIL"):
        return "FAIL"
    if l.startswith("SELFTEST OK"):
        return "PASS"
    return "?"


def main():
    before = md5(REPLICA)
    # ★ 一律**按字节**读写：文本模式读会把 CRLF 折成 LF，写出时又把 LF 落盘 ⇒ 变异窗口里
    #   被跟踪文件的行尾被改写（本工程已登记的同款隐患）。字节操作则行尾原样不动。
    src = open(REPLICA, "rb").read()
    orig_b, mut_b = ORIG.encode("utf-8"), MUT.encode("utf-8")
    if orig_b not in src:
        print("找不到变异点，原样未动。查找：", ORIG)
        return 2
    shutil.copyfile(REPLICA, BACKUP)

    print("replica.js md5（改前）= %s" % before)
    print("变异点：%s\n     -> %s" % (ORIG, MUT))
    try:
        open(REPLICA, "wb").write(src.replace(orig_b, mut_b, 1))
        out_mut = run_selftest_a()
        print("\n[变异版] ⑳m：", line_20m(out_mut))
        v_mut = verdict_20m(out_mut)
        print("[变异版] ⑳m 判定 =", v_mut, "（期望 FAIL —— 变异放行了 # 键，坏按钮真的被画出来了）")
    finally:
        shutil.copyfile(BACKUP, REPLICA)
    after = md5(REPLICA)
    print("\n还原后 replica.js md5 = %s" % after)
    print("逐字节还原 =", after == before)

    out_ok = run_selftest_a()
    print("\n[还原版] ⑳m：", line_20m(out_ok))
    v_ok = verdict_20m(out_ok)
    print("[还原版] ⑳m 判定 =", v_ok, "（期望 PASS）")
    for line in re.findall(r"SELFTEST[^<\n]*", out_ok):
        print("  " + line.strip())

    ok = (v_mut == "FAIL" and v_ok == "PASS" and after == before)
    if os.path.exists(BACKUP):
        os.remove(BACKUP)
    print("\n=== 变异自证结论：%s ===" % ("通过（断言非空：变异下 FAIL、还原后 PASS、md5 逐字节一致）"
                                          if ok else "不通过"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())