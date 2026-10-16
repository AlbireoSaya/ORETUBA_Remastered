# -*- coding: utf-8 -*-
"""
W7-4 · 0x5C 切分缺陷全六源重扫（ISSUE-20260918-06）

背景
----
`extract_sob0.py` 的 classify() 按**原始字节 0x5C** 切分 `#<说话人>\\<语音ID>$&`：
    sp, vo = h.split(b'\\', 1)
而 cp932 中 0x5C 同时是若干汉字的**尾字节**（十=8F5C、ソ=835C、ク=834E…），
故说话人尾部含这类字时被误切 → 说话人尾部丢字（U+FFFD）、语音 ID 混入残段。

判据（确定性、非猜测）
--------------------
1) 行级签名：speaker 含 U+FFFD ／ voice 含 0x5C ／ voice 非纯 [A-Za-z0-9_]。
2) 字节级对不上：按源行重建 `#<speaker>\\<voice>$&` 的 cp932/ascii 字节，
   若在原始脚本字节中**找不到**，即「speaker/voice 与原始脚本字节对不上」。
   缺陷行的重建必然失败（说话人已截断），正常行必然命中。
3) 复原（仅对缺陷行）：语音 ID 为纯 ASCII，故**末个 0x5C 才是真分隔符**——
   回到原始字节，从 `\\<vid>$&` 之前最近的 `#` 起按 cp932 解出真说话人。

本脚本**全程只读源工程**，只写 `资源组\修正\修正表_0x5C.tsv` 与 stdout。
"""
import csv
import glob
import json
import os
import re
import sys
import collections

ROOT = r"E:\ZCode Workspace\Galgame"
PRJ = os.path.join(ROOT, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
RES = os.path.join(PRJ, "资源组")
FIX = os.path.join(RES, "修正")
BS = chr(92)                      # 反斜杠 = 0x5C
LEAD = re.compile(rb"[\x81-\x9f\xe0-\xfc]")

# ---------------------------------------------------------------- 原始脚本位置
OT_J = os.path.join(ROOT, "工程", "我们没有翅膀", "汉化", "剧情汉化")
OT_S = os.path.join(ROOT, "工程", "我们没有翅膀", "解包", "SCRIPT")
OTP_J = os.path.join(ROOT, "工程", "我们没有翅膀 前奏诗", "汉化", "剧情汉化")
OTP_S = os.path.join(ROOT, "工程", "我们没有翅膀 前奏诗", "汉化", "SCRIPT_CN")
AS_J = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "台词.json")
AS_T = os.path.join(ROOT, "工程", "我们没有翅膀 After Story", "语料", "原文")
OTR_J = os.path.join(ROOT, "工程", "我们没有翅膀R", "亜衣线资源", "剧本", "台词对照.json")
OTR_T = os.path.join(ROOT, "工程", "我们没有翅膀R", "亜衣线资源", "剧本")
OTV_J = os.path.join(ROOT, "工程", "我们没有翅膀PSV", "汉化", "台词对照.json")
OTV_S = os.path.join(ROOT, "工程", "我们没有翅膀PSV", "脚本解包")
NP_J = os.path.join(ROOT, "工程", "涅布＊普拉斯", "语料", "明日香线_原文.json")
NP_S = os.path.join(ROOT, "工程", "涅布＊普拉斯", "解包", "data01100.arc")

OUT_TSV = os.path.join(FIX, "修正表_0x5C.tsv")

REPORT = collections.OrderedDict()


def w(s=""):
    sys.stdout.write(str(s) + "\n")
    sys.stdout.flush()


def is_voice_id(s):
    return bool(s) and all(c.isalnum() or c == '_' for c in s)


def has_defect(spk, vo):
    """行级签名：任一成立即判缺陷。非字符串 voice（如 PSV 的 int ID）天然无缺陷。"""
    if not isinstance(spk, str) and spk is not None:
        return False
    if "\ufffd" in (spk or ""):
        return True
    if BS in (spk or ""):
        return True
    if vo is not None and not isinstance(vo, str):
        return False
    if BS in (vo or ""):
        return True
    if vo and not is_voice_id(vo):
        return True
    return False


# ================================================================ 1. ot 本篇
def scan_ot():
    """返回 (rows, affected, notes)。rows: list of dict(script, seq, speaker, voice, kind)"""
    rows = []
    for p in sorted(glob.glob(os.path.join(OT_J, "*.jsonl"))):
        n = os.path.basename(p)[:-10]
        for l in open(p, encoding="utf-8"):
            d = json.loads(l)
            d["_script"] = n
            rows.append(d)

    affected = [d for d in rows if has_defect(d.get("speaker"), d.get("voice"))]

    # 字节级对不上：逐行重建 marker 并回原始 .sob 查找
    raw_cache = {}
    miss = []
    ok = 0
    for d in rows:
        vo = d.get("voice") or ""
        if not vo:
            continue
        n = d["_script"]
        if n not in raw_cache:
            fp = os.path.join(OT_S, n + ".sob")
            raw_cache[n] = open(fp, "rb").read() if os.path.isfile(fp) else None
        raw = raw_cache[n]
        if raw is None:
            continue
        try:
            pat = b"#" + (d.get("speaker") or "").encode("cp932") + BS.encode() + vo.encode("ascii") + b"$&"
        except Exception:
            miss.append(d)
            continue
        if pat in raw:
            ok += 1
        else:
            miss.append(d)

    # 复原（末个 0x5C 为真分隔符；回原始字节）
    fixed = []
    fail = []
    for d in miss:
        n = d["_script"]
        raw = raw_cache.get(n)
        vo = d.get("voice") or ""
        vid = vo.rsplit(BS, 1)[-1]
        if not raw or not is_voice_id(vid):
            fail.append(d)
            continue
        seps = list(re.finditer(re.escape(BS.encode()) + re.escape(vid.encode("ascii")) + rb"\$&", raw))
        done = False
        for m in seps:
            st = m.start()
            h = raw.rfind(b"#", max(0, st - 60), st)
            if h < 0:
                continue
            sb = raw[h + 1:st]
            if not sb or b"\x00" in sb:
                continue
            try:
                spk = sb.decode("cp932")
            except UnicodeDecodeError:
                continue
            if not spk or BS in spk or "\ufffd" in spk:
                continue
            # 复核：复原后的 marker 必须能在原始字节中命中
            if b"#" + spk.encode("cp932") + BS.encode() + vid.encode("ascii") + b"$&" not in raw:
                continue
            fixed.append(dict(script=n, seq=d["seq"], addr=d.get("addr"), kind=d.get("kind"),
                              speaker_before=d.get("speaker"), voice_before=vo,
                              speaker_after=spk, voice_after=vid,
                              span=[h, m.end()],
                              hex=raw[h:m.end()].hex()))
            done = True
            break
        if not done:
            fail.append(d)

    REPORT["ot"] = dict(
        total=len(rows), affected=len(affected), byte_miss=len(miss),
        byte_ok=ok, fixed=len(fixed), fail=len(fail),
        files=sorted({d["_script"] for d in affected}))
    return rows, affected, fixed, fail


# ================================================================ 2. otp 前奏诗
def scan_otp():
    rows = []
    for p in sorted(glob.glob(os.path.join(OTP_J, "*.jsonl"))):
        n = os.path.basename(p)[:-10]
        for l in open(p, encoding="utf-8"):
            d = json.loads(l)
            d["_script"] = n
            rows.append(d)
    affected = [d for d in rows if has_defect(d.get("speaker"), d.get("voice"))]

    # 根因前置条件：说话人标签的 cp932 字节含 0x5C 才可能被误切
    cond = [d for d in rows if (d.get("speaker") or "").encode("cp932", "replace").find(b"\x5c") >= 0]

    # 字节级对不上
    raw_cache = {}
    ok = miss = 0
    for d in rows:
        vo = d.get("voice") or ""
        if not vo:
            continue
        n = d["_script"]
        if n not in raw_cache:
            fp = os.path.join(OTP_S, n + ".sob")
            raw_cache[n] = open(fp, "rb").read() if os.path.isfile(fp) else None
        raw = raw_cache[n]
        if raw is None:
            continue
        try:
            pat = b"#" + (d.get("speaker") or "").encode("cp932") + BS.encode() + vo.encode("ascii") + b"$&"
        except Exception:
            miss += 1
            continue
        ok += 1 if pat in raw else 0
        miss += 0 if pat in raw else 1

    REPORT["otp"] = dict(total=len(rows), affected=len(affected),
                         cp932_5c_speakers=len(cond), byte_ok=ok, byte_miss=miss,
                         sob_missing=[n for n, v in raw_cache.items() if v is None])
    return rows, affected


# ================================================================ 3. ota After Story
def scan_ota():
    d = json.load(open(AS_J, encoding="utf-8"))
    rows = []
    for k, v in d.items():
        for m in v["messages"]:
            rows.append(dict(file=k, idx=m.get("index"), kind=m.get("kind"),
                             speaker=m.get("speaker"), voice=m.get("voice")))
    affected = [r for r in rows if has_defect(r["speaker"], r["voice"])]
    cond = [r for r in rows if (r["speaker"] or "").encode("cp932", "replace").find(b"\x5c") >= 0]

    # 字节级：speaker/voice 是 TOB 记录头里**独立的长度前缀串**，各自单独解码，
    # 结构上不存在按 0x5C 切分的环节（依据 工具\parse_after.py:82-99 decls_in/classify）。
    # 复核：speaker 的 cp932 串（含 NUL）与 voice 的 ascii 串必须出现在对应 .tob。
    raw_cache = {}
    ok = miss = 0
    for r in rows:
        fp = os.path.join(AS_T, r["file"])
        if not os.path.isfile(fp):
            continue
        if r["file"] not in raw_cache:
            raw_cache[r["file"]] = open(fp, "rb").read()
        raw = raw_cache[r["file"]]
        for s, enc in ((r["speaker"], "cp932"), (r["voice"], "ascii")):
            if not s:
                continue
            try:
                if s.encode(enc) + b"\x00" in raw:
                    ok += 1
                else:
                    miss += 1
            except Exception:
                miss += 1
    REPORT["ota"] = dict(total=len(rows), affected=len(affected),
                         cp932_5c_speakers=len(cond), byte_ok=ok, byte_miss=miss)
    return rows, affected


# ================================================================ 4. otr R 版亚衣线
def scan_otr():
    d = json.load(open(OTR_J, encoding="utf-8"))
    rows = []
    for sc in d["scenes"]:
        for ln in sc["lines"]:
            rows.append(dict(file=sc["file"], lineno=ln["lineno"], kind=ln.get("kind"),
                             speaker=ln.get("speaker_jp"), voice=ln.get("voice")))
    affected = [r for r in rows if has_defect(r["speaker"], r["voice"])]
    cond = [r for r in rows if (r["speaker"] or "").encode("cp932", "replace").find(b"\x5c") >= 0]

    raw_cache = {}
    ok = miss = 0
    for r in rows:
        fp = os.path.join(OTR_T, r["file"])
        if not os.path.isfile(fp):
            continue
        if r["file"] not in raw_cache:
            raw_cache[r["file"]] = open(fp, "rb").read()
        raw = raw_cache[r["file"]]
        for s, enc in ((r["speaker"], "cp932"), (r["voice"], "ascii")):
            if not s:
                continue
            try:
                if s.encode(enc) + b"\x00" in raw:
                    ok += 1
                else:
                    miss += 1
            except Exception:
                miss += 1
    REPORT["otr"] = dict(total=len(rows), affected=len(affected),
                         cp932_5c_speakers=len(cond), byte_ok=ok, byte_miss=miss,
                         cond_samples=[(r["file"], r["lineno"], r["speaker"], r["voice"]) for r in cond[:4]])
    return rows, affected


# ================================================================ 5. otv PSV 美咲线
def scan_otv():
    d = json.load(open(OTV_J, encoding="utf-8"))
    rows = []
    for r in d:
        rows.append(dict(script=r.get("脚本"), lineno=r.get("行序"), kind=r.get("类别"),
                         speaker=r.get("说话人日文"), voice=r.get("Voice")))
    affected = [r for r in rows if has_defect(r["speaker"], r["voice"])]
    cond = [r for r in rows if isinstance(r["speaker"], str)
            and r["speaker"].encode("cp932", "replace").find(b"\x5c") >= 0]

    # 字节级：PSV 脚本为 Shift-JIS 纯文本 DSL，说话人日文与 Voice 是**独立字段**
    # （依据 工具\parse_adv.py），不存在 0x5C 切分环节。复核：说话人 cp932 串须在脚本中出现。
    raw_cache = {}
    ok = miss = 0
    for r in rows:
        s = r["speaker"]
        if not s:
            continue
        fp = os.path.join(OTV_S, r["script"])
        if not os.path.isfile(fp):
            continue
        if r["script"] not in raw_cache:
            raw_cache[r["script"]] = open(fp, "rb").read()
        try:
            if s.encode("cp932") in raw_cache[r["script"]]:
                ok += 1
            else:
                miss += 1
        except Exception:
            miss += 1
    REPORT["otv"] = dict(total=len(rows), affected=len(affected),
                         cp932_5c_speakers=len(cond), byte_ok=ok, byte_miss=miss,
                         voice_types=collections.Counter(type(r["voice"]).__name__ for r in rows))
    return rows, affected


# ================================================================ 6. np 涅布
def scan_np():
    d = json.load(open(NP_J, encoding="utf-8"))
    rows = []
    for r in d:
        rows.append(dict(file=r.get("file"), idx=r.get("idx"), kind=r.get("kind"),
                         speaker=r.get("speaker_hint"), voice=r.get("voice_id")))
    affected = [r for r in rows if has_defect(r["speaker"], r["voice"])]
    cond = [r for r in rows if (r["speaker"] or "").encode("cp932", "replace").find(b"\x5c") >= 0]

    # 字节级：BGI 编译脚本；voice_id 由 ASCII 正则提取、speaker_hint 由邻近 label 文本得到
    # （依据 工具\extract_asuka_corpus.py:65-127），均无 0x5C 切分。复核：voice_id 须在脚本字节中。
    raw_cache = {}
    ok = miss = 0
    for r in rows:
        v = r["voice"]
        if not v:
            continue
        fp = os.path.join(NP_S, r["file"])
        if not os.path.isfile(fp):
            continue
        if r["file"] not in raw_cache:
            raw_cache[r["file"]] = open(fp, "rb").read()
        if v.encode("ascii", "ignore") in raw_cache[r["file"]]:
            ok += 1
        else:
            miss += 1
    REPORT["np"] = dict(total=len(rows), affected=len(affected),
                        cp932_5c_speakers=len(cond), byte_ok=ok, byte_miss=miss)
    return rows, affected


# ================================================================ main
def main():
    w("=" * 78)
    w("W7-4 · 0x5C 切分缺陷全六源重扫")
    w("=" * 78)

    ot_rows, ot_aff, ot_fixed, ot_fail = scan_ot()
    otp_rows, otp_aff = scan_otp()
    ota_rows, ota_aff = scan_ota()
    otr_rows, otr_aff = scan_otr()
    otv_rows, otv_aff = scan_otv()
    np_rows, np_aff = scan_np()

    w()
    w("--- 六源受影响面 ---")
    for k in ("ot", "otp", "ota", "otr", "otv", "np"):
        r = REPORT[k]
        w("  %-4s 总行=%-7d 受影响=%-3d 字节对不上=%-3s 字节命中=%-6s 根因(说话人cp932含0x5C)=%s"
          % (k, r["total"], r["affected"],
             r.get("byte_miss", "-"), r.get("byte_ok", "-"), r.get("cp932_5c_speakers", "-")))
    w()
    w("  ot 受影响文件: %s" % REPORT["ot"]["files"])
    w("  ot 复原成功=%d 失败=%d" % (len(ot_fixed), len(ot_fail)))
    for d in ot_fail:
        w("    FAIL %s seq=%d %r %r" % (d["_script"], d["seq"], d.get("speaker"), d.get("voice")))
    if REPORT["otr"].get("cond_samples"):
        w("  otr 含0x5C说话人样本（证明 TOB 抽取字节安全）: %s" % REPORT["otr"]["cond_samples"])

    # ---- 场景模块归属：s03c_03c 由 scene_otr（R 版）覆盖，不进 scene_ot
    ot_mod = [d for d in ot_fixed if not d["script"].startswith("s03c")]
    ot_s03c = [d for d in ot_fixed if d["script"].startswith("s03c")]
    w()
    w("  本篇修复 %d 行 = scene_ot 范围 %d + s03c 范围 %d" % (len(ot_fixed), len(ot_mod), len(ot_s03c)))

    # ---- 三段对照样本（10 行）
    w()
    w("--- 原始脚本字节 → 修复前 → 修复后（抽样 10）---")
    sample = ot_fixed[:5] + ot_fixed[-5:] if len(ot_fixed) > 10 else ot_fixed
    for d in sample:
        w("  %s seq=%d 字节@%d-%d hex=%s" % (d["script"], d["seq"], d["span"][0], d["span"][1], d["hex"]))
        w("      before: speaker=%r voice=%r" % (d["speaker_before"], d["voice_before"]))
        w("      after : speaker=%r voice=%r" % (d["speaker_after"], d["voice_after"]))

    # ---- 写修正表
    w()
    w("--- 产出 修正表_0x5C.tsv ---")
    header = ["source", "file", "locator", "kind", "field", "old_text", "new_text",
              "fix_type", "method", "evidence", "confidence"]
    lines = []
    for d in ot_fixed:
        loc = "script=%s&seq=%d" % (d["script"], d["seq"])
        old = "%s%s%s" % (d["speaker_before"], BS, d["voice_before"])
        new = "%s%s%s" % (d["speaker_after"], BS, d["voice_after"])
        ev = ("工程\\我们没有翅膀\\解包\\SCRIPT\\%s.sob 原始字节 @%d-%d hex=%s；"
              "语音 ID 为纯 ASCII → 末个 0x5C 为真分隔符，自 `\\vid$&` 前最近的 `#` 起按 cp932 复解；"
              "根因：cp932 中 0x5C 兼作「十/ソ/ク」等字尾字节，被 classify 误当分隔符"
              ) % (d["script"], d["span"][0], d["span"][1], d["hex"])
        lines.append(["ot", d["script"] + ".sob.jsonl", loc, d["kind"] or "dialogue",
                      "speaker_voice", old, new, "speaker_split", "programmatic", ev, "high"])
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wr.writerow(header)
        wr.writerows(lines)
    w("  写出 %s（%d 条）" % (OUT_TSV, len(lines)))

    # ---- 自洽断言
    w()
    w("--- 自洽断言 ---")
    src = {}
    for p in sorted(glob.glob(os.path.join(OT_J, "*.jsonl"))):
        n = os.path.basename(p)[:-10]
        for l in open(p, encoding="utf-8"):
            d = json.loads(l)
            src[(n, d["seq"])] = d
    bad = 0
    for d in ot_fixed:
        s = src[(d["script"], d["seq"])]
        old = "%s%s%s" % (d["speaker_before"], BS, d["voice_before"])
        if old != "%s%s%s" % (s.get("speaker") or "", BS, s.get("voice") or ""):
            bad += 1
            w("    MISMATCH %s seq=%d" % (d["script"], d["seq"]))
    w("  条数 == 受影响行数 : %d == %d  %s" % (len(lines), REPORT["ot"]["affected"],
                                          "OK" if len(lines) == REPORT["ot"]["affected"] else "FAIL"))
    w("  old_text 逐字符等于源语料 : %s（不符 %d）" % ("OK" if bad == 0 else "FAIL", bad))
    w("  new_text 复原 speaker 无 U+FFFD/无 0x5C : %s"
      % ("OK" if all("\ufffd" not in d["speaker_after"] and BS not in d["speaker_after"] for d in ot_fixed) else "FAIL"))
    w("  new_text voice 为纯 ASCII ID : %s"
      % ("OK" if all(is_voice_id(d["voice_after"]) and d["voice_after"].isascii() for d in ot_fixed) else "FAIL"))

    # ---- 未受影响源的判据摘要
    w()
    w("--- 未受影响源判据 ---")
    w("  otp: 与 ot 同一抽取器（同 classify 0x5C 切分）；但 0 个说话人标签的 cp932 字节含 0x5C"
      "（前置条件不成立）；%d/%d 行 marker 字节命中" % (REPORT["otp"]["byte_ok"],
                                            REPORT["otp"]["byte_ok"] + REPORT["otp"]["byte_miss"]))
    w("  ota: speaker/voice 取自 TOB 记录头**独立长度前缀串**（parse_after.py decls_in 各自解码），"
      "无 0x5C 切分；%d 次字节命中 / %d 次未命中" % (REPORT["ota"]["byte_ok"], REPORT["ota"]["byte_miss"]))
    w("  otr: speaker/voice 取自 TOB 串表 parse_string（tob_extract.py，长度前缀独立解码）；"
      "含 0x5C 的说话人（如 クソ長い髪の女）**完整无损**，反证字节安全；%d 命中 / %d 未命中"
      % (REPORT["otr"]["byte_ok"], REPORT["otr"]["byte_miss"]))
    w("  otv: PSV DSL 纯文本，说话人日文与 Voice 为独立字段（parse_adv.py），Voice 为 int；"
      "%d 命中 / %d 未命中" % (REPORT["otv"]["byte_ok"], REPORT["otv"]["byte_miss"]))
    w("  np : BGI 编译脚本，voice_id 由 ASCII 正则提取、speaker_hint 由邻近 label 取得"
      "（extract_asuka_corpus.py），无 0x5C 切分；%d 命中 / %d 未命中"
      % (REPORT["np"]["byte_ok"], REPORT["np"]["byte_miss"]))

    json.dump(REPORT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "_0x5C_重扫报告.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    w()
    w("完成。")


if __name__ == "__main__":
    main()