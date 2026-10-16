# -*- coding: utf-8 -*-
r"""
`test_staging_line_endings.py` · 逐行演出表「行尾口径」回归测试（ISSUE-20261001-14，只读、幂等）

**为什么需要它**
    本仓库 `core.autocrlf=true` 且无 `.gitattributes` ⇒ **blob 是 LF，检出到盘面却是 CRLF**
    （字节数恰好多出行数，见 `交接说明.md` C12）。合并后在主工作树首次实跑时，校验器曾报
    `演出_ot.tsv 含 CR（契约要求 LF）` ——即「只在别处检出的那台机器上才会红」。本测试把
    该行为**钉成判据**，防止再犯。

判据（任一失败 ⇒ 退出码 1）
    1 `read_tsv()` 对 **LF** 文件：解析成功、`line_ending == "LF"`、行数不变；
    2 对 **CRLF** 文件：解析成功、`line_ending == "CRLF"`、**行数与 LF 版相同**（规范化生效）；
    3 对**裸 `CR`**（`CR` 后不接 `LF`）**必须 `SystemExit`**（真失败）；
    4 对**带 BOM** 的文件**必须 `SystemExit`**；
    5 `_index.json` 的 `sha256` 口径：对同一内容，**LF 与 CRLF 两态算出的 sha256 必须相同**
       （因为它算在 LF 规范化字节上）——这条直接守住「台账与检出形态无关」；
    6 **在隔离镜像里**造「全套交付件皆 CRLF」的检出，四个生成器与两个 `emit_*` 的 `--check`
       必须全部 PASS —— 这条守的是本批真栽过的那一类：`--check` 曾用**裸字节**读盘比对，于是
       **只在 LF 检出通过、在 `core.autocrlf=true` 的主工作树必失败**（四个生成器 + 台账生成器全 exit 1）。

**只读**：真交付件全程只读（判据 6 跑在 `临时\line_ending_test\` 下的**镜像**里，工具/表都另拷一份）；
临时文件写在 `<checkout>\临时\line_ending_test\`，结束时删除该叶子目录（**不删共用的 `临时\`**）。

复跑：
    python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/test_staging_line_endings.py"
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                          # <checkout>\工程\<作品>\资源组
WS = os.path.dirname(os.path.dirname(os.path.dirname(RES)))   # <checkout>（RES 之上还隔着 <作品> 与 工程）
TMP = os.path.join(WS, "临时", "line_ending_test")
OUT = os.path.join(RES, "演出")
VERIFY = os.path.join(HERE, "verify_staging.py")
INDEX = os.path.join(OUT, "_index.json")

FAILS = []


def rec(name, ok, detail=""):
    print("[%s] %s%s" % ("OK" if ok else "FAIL", name, (" — " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def load_verify_module():
    spec = importlib.util.spec_from_file_location("verify_staging_under_test", VERIFY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def raises(fn):
    try:
        fn()
    except SystemExit:
        return True
    except Exception:                                   # noqa: BLE001
        return False
    return False


def main():
    src = os.path.join(OUT, "演出_ot.tsv")
    if not os.path.isfile(src):
        raise SystemExit("!! 缺 %s（请先跑 build_staging_sob0.py）" % src)
    os.makedirs(TMP, exist_ok=True)
    mod = load_verify_module()

    lf_bytes = open(src, "rb").read().replace(b"\r\n", b"\n")
    p_lf = os.path.join(TMP, "lf.tsv")
    p_crlf = os.path.join(TMP, "crlf.tsv")
    p_cr = os.path.join(TMP, "bare_cr.tsv")
    p_bom = os.path.join(TMP, "bom.tsv")
    open(p_lf, "wb").write(lf_bytes)
    open(p_crlf, "wb").write(lf_bytes.replace(b"\n", b"\r\n"))
    open(p_cr, "wb").write(lf_bytes.replace(b"\n", b"\r", 1))
    open(p_bom, "wb").write(b"\xef\xbb\xbf" + lf_bytes)

    head_lf, rows_lf, _, nl_lf = mod.read_tsv(p_lf)
    head_cr, rows_cr, _, nl_cr = mod.read_tsv(p_crlf)

    rec("1 LF 文件可解析且 line_ending=LF", nl_lf == "LF" and len(rows_lf) > 1000,
        "nl=%s rows=%d" % (nl_lf, len(rows_lf)))
    rec("2 CRLF 文件可解析、line_ending=CRLF、行数与 LF 版相同",
        nl_cr == "CRLF" and len(rows_cr) == len(rows_lf) and head_cr == head_lf,
        "nl=%s rows=%d vs %d" % (nl_cr, len(rows_cr), len(rows_lf)))
    rec("3 裸 CR 必须被拒（SystemExit）", raises(lambda: mod.read_tsv(p_cr)))
    rec("4 带 BOM 必须被拒（SystemExit）", raises(lambda: mod.read_tsv(p_bom)))

    # 5 _index.json 的 sha256 口径：台账记的必须是 **LF 规范化**后的值，
    #   故「同一内容、两种盘面形态」规范化后应得到**同一个** sha256，且台账与之相等。
    if os.path.isfile(INDEX):
        import hashlib
        idx = json.load(io.open(INDEX, encoding="utf-8"))
        ent = idx["sources"]["ot"]
        norm = lambda b: b.replace(b"\r\n", b"\n")     # noqa: E731
        raw_crlf = lf_bytes.replace(b"\n", b"\r\n")
        s_lf = hashlib.sha256(norm(lf_bytes)).hexdigest()
        s_crlf = hashlib.sha256(norm(raw_crlf)).hexdigest()
        s_raw_crlf = hashlib.sha256(raw_crlf).hexdigest()
        rec("5 台账 sha256 == LF 规范化值；两种盘面形态规范化后同值（且 ≠ 未规范化的 CRLF 值）",
            ent["sha256"] == s_lf == s_crlf and s_raw_crlf != s_crlf,
            "index=%s lf=%s crlf-norm=%s crlf-raw=%s"
            % (ent["sha256"][:12], s_lf[:12], s_crlf[:12], s_raw_crlf[:12]))
        rec("5b 台账只记与检出无关的事实（bytes_lf_normalized ＋ line_ending_canonical）",
            ent.get("line_ending_canonical", "").startswith("LF")
            and ent.get("bytes_lf_normalized") == len(norm(open(src, "rb").read()))
            and "bytes_raw_at_generation" not in ent
            and "line_ending_at_generation" not in ent,
            "canonical=%r bytes_lf=%r 无 *_at_generation=%s"
            % (ent.get("line_ending_canonical", "")[:6], ent.get("bytes_lf_normalized"),
               "bytes_raw_at_generation" not in ent))
    else:
        rec("5 _index.json 存在（应由 emit_staging_index.py 生成）", False, INDEX)

    # 6 在**隔离镜像**里造「全件 CRLF」的检出，六个 `--check` 必须全 PASS。
    #   ⚠️ **真交付件全程只读**（一审指出：早先的实现把真表就地转 CRLF 再还原，若进程被强杀
    #   则 `finally` 不执行、交付件静默留在 CRLF 盘面——而 `git status` 在 autocrlf 下看不出来）。
    #   镜像结构：`<临时>\line_ending_test\<作品>\资源组\{工具,演出}`——工具按 `__file__` 推导
    #   `OUT_DIR`，故天然指向镜像；`WS_LOCAL` 退到 `<checkout>\临时`，边界断言照样通过。
    import shutil
    import subprocess
    PY = [sys.executable, "-X", "utf8"]
    prj = os.path.basename(os.path.dirname(RES))
    MIR = os.path.join(TMP, prj, "资源组")
    all_art = ["演出_ot.tsv", "演出_ota.tsv", "演出_otp.tsv", "演出_otr.tsv",
               "演出_otv.tsv", "演出_np.tsv", "头像族判读.tsv", "_index.json"]
    jobs = ["build_staging_sob0.py", "build_staging_otv.py", "build_staging_tob.py",
            "build_staging_np.py", "emit_staging_index.py", "emit_face_family_verdict.py"]
    try:
        os.makedirs(os.path.join(MIR, "工具"))
        os.makedirs(os.path.join(MIR, "演出"))
        for f in sorted(os.listdir(HERE)):
            if f.endswith(".py"):
                shutil.copy2(os.path.join(HERE, f), os.path.join(MIR, "工具", f))
        for a in all_art:
            b = open(os.path.join(OUT, a), "rb").read()
            with open(os.path.join(MIR, "演出", a), "wb") as g:
                g.write(b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        for script in jobs:
            r = subprocess.run(PY + [os.path.join(MIR, "工具", script), "--check"],
                               capture_output=True, text=True, encoding="utf-8", cwd=WS)
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            rec("6 %s --check 在「镜像·全件 CRLF」下 PASS" % script, r.returncode == 0,
                "exit=%d %s" % (r.returncode, (tail[-1][:110] if tail else "")))
    finally:
        shutil.rmtree(os.path.join(TMP, prj), ignore_errors=True)

    for f in (p_lf, p_crlf, p_cr, p_bom):
        if os.path.isfile(f):
            os.remove(f)
    # 只删本次自建的叶子目录。**不删父目录 `临时\`**——它是共用目录（别的会话/别的 worktree
    # 都在里面），按「临时目录清理确权」只清自己建的那一份。
    try:
        os.rmdir(TMP)
    except OSError:
        pass

    ok = not FAILS
    print()
    if FAILS:
        print("失败项 %d 个：%s" % (len(FAILS), FAILS))
    print("ALL_PASS = %s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
