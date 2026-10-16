# -*- coding: utf-8 -*-
"""
《我们没有翅膀》PS Vita (PCSG00299) 林田美咲线 —— 音频提取与转码
---------------------------------------------------------------------------
只读源（严格只读）:
  E:\\ZCode Workspace\\Galgame\\工程\\我们没有翅膀PSV\\解密\\PCSG00299\\media\\{VOICE,BGM,SE}.AWB
清单:
  工程\\我们没有翅膀PSV\\美咲线清单\\音频提取清单.json
输出:
  工程\\我们没有翅膀PSV\\素材\\美咲线\\audio\\{voice,bgm,se}\\*.ogg
  + 音频清单.tsv

编解码（已探测）:
  VOICE.AWB = AFS2/AWB 容器，条目 HCA (v512, ciph type0 = 未加密)
  BGM.AWB / SE.AWB = CPK 容器（magic "CPK "），条目为 ADX（少数为 HCA）
用法:
  python extract_audio.py            # 全流程
  python extract_audio.py --dry      # 只探测，不写文件
"""
import os
import re
import sys
import json
import time
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\pylibs")

ROOT = r"E:\ZCode Workspace\Galgame"
MEDIA = os.path.join(
    ROOT, r"工程\我们没有翅膀PSV\解密\PCSG00299\media"
)
MANIFEST = os.path.join(ROOT, r"工程\我们没有翅膀PSV\美咲线清单\音频提取清单.json")
OUTROOT = os.path.join(ROOT, r"工程\我们没有翅膀PSV\素材\美咲线\audio")
TSV = os.path.join(ROOT, r"工程\我们没有翅膀PSV\美咲线清单\音频清单.tsv")
TMP = os.path.join(ROOT, r"临时\audio_tmp")

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

# (类别, 容器文件名, 容器类型, 质量, 命名模板)
CATS = [
    ("voice", "VOICE.AWB", "awb", 2),
    ("bgm", "BGM.AWB", "cpk", 3),
    ("se", "SE.AWB", "cpk", 3),
]

DRY = "--dry" in sys.argv
JOBS = int(os.environ.get("JOBS", "8"))


def log(*a):
    print(*a, flush=True)


def sniff(b):
    """返回 (扩展名, 编解码名)"""
    if b[:4] == b"HCA\x00":
        return ".hca", "HCA"
    if len(b) >= 2 and b[0] == 0x80 and b[1] == 0x00:
        return ".adx", "ADX"
    if b[:4] == b"CPK ":
        return ".cpk", "CPK"
    return ".bin", "UNKNOWN"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def probe_duration(path):
    p = run([FFPROBE, "-hide_banner", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path])
    if p.returncode != 0:
        return None, p.stderr.decode("utf-8", "replace").strip()
    try:
        return float(p.stdout.decode().strip()), None
    except ValueError:
        return None, "unparsable duration: %r" % p.stdout


def main():
    t0 = time.time()
    os.makedirs(TMP, exist_ok=True)
    from cricodecs import awb as Cawb, cpk as Ccpk

    # cricodecs 的 C++ 读取器不支持非 ASCII 路径 -> chdir + 纯文件名
    os.chdir(MEDIA)

    with open(MANIFEST, encoding="utf-8") as f:
        man = json.load(f)

    log("== 阶段 A：从容器提取源条目（只读） ==")
    plan = []          # list of dict: cat, index, name, raw_path, out_path, codec
    for cat, container, ctype, q in CATS:
        loaders = {"awb": Cawb.load, "cpk": Ccpk.load}
        h = loaders[ctype](container)
        if ctype == "awb":
            n = h.file_count
            get = h.file_bytes
        else:
            n = h.file_count
            get = h.file_bytes
        log(f"-- {container}: 容器类型={ctype.upper()} 条目数={n}")

        if cat == "voice":
            items = [(x["index"], x.get("name")) for x in man["voice"]]
        else:
            items = [(i, None) for i in man[cat]]

        rawdir = os.path.join(TMP, "raw", cat)
        os.makedirs(rawdir, exist_ok=True)

        for idx, name in items:
            if idx >= n:
                plan.append(dict(cat=cat, index=idx, name=name, q=q,
                                 codec="OUT_OF_RANGE", raw=None, out=None,
                                 error=f"index {idx} >= container entry count {n}"))
                continue
            if cat == "voice":
                stem = f"{idx:05d}_{name}" if name else f"{idx:05d}"
            elif cat == "bgm":
                stem = f"bgm{idx:03d}"
            else:
                stem = f"se{idx:03d}"
            outp = os.path.join(OUTROOT, cat, stem + ".ogg")
            try:
                data = get(idx)
            except Exception as e:
                plan.append(dict(cat=cat, index=idx, name=name, q=q,
                                 codec="EXTRACT_FAIL", raw=None, out=outp, stem=stem,
                                 error=f"{type(e).__name__}: {e}"))
                continue
            ext, codec = sniff(data)
            rawp = os.path.join(rawdir, stem + ext)
            if not DRY:
                with open(rawp, "wb") as f:
                    f.write(data)
            plan.append(dict(cat=cat, index=idx, name=name, q=q, codec=codec,
                             raw=None if DRY else rawp, out=outp, stem=stem,
                             src_bytes=len(data), error=None))

    log(f"-- 计划条目数: {len(plan)}")
    if DRY:
        from collections import Counter
        for cat, _c, _t, _q in CATS:
            c = Counter(p["codec"] for p in plan if p["cat"] == cat)
            log(f"   {cat}: {dict(c)}")
        return

    # ---------------- 阶段 B：ffmpeg 转码 ----------------
    log("== 阶段 B：ffmpeg 转 OGG Vorbis ==")

    def transcode(p):
        if p.get("error"):
            return p
        p["_t0"] = time.time()
        cmd = [FFMPEG, "-hide_banner", "-v", "error", "-y", "-i", p["raw"],
               "-map_metadata", "-1", "-vn",
               "-c:a", "libvorbis", "-q:a", str(p["q"]), p["out"]]
        r = run(cmd)
        p["ffmpeg_rc"] = r.returncode
        if r.returncode != 0:
            p["error"] = "ffmpeg rc=%d: %s" % (
                r.returncode, r.stderr.decode("utf-8", "replace").strip()[:400])
            if os.path.exists(p["out"]):
                os.remove(p["out"])
            return p
        p["out_bytes"] = os.path.getsize(p["out"])
        # 转码成功即删源，控制临时占用
        try:
            os.remove(p["raw"])
        except OSError:
            pass
        p["raw"] = None
        return p

    todo = [p for p in plan if not p.get("error")]
    done = 0
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        for p in ex.map(transcode, todo):
            done += 1
            if done % 200 == 0 or done == len(todo):
                log(f"   转码 {done}/{len(todo)}  ({time.time() - t0:.0f}s)")

    # ---------------- 阶段 C：ffprobe 时长 ----------------
    log("== 阶段 C：ffprobe 校验 ==")

    def probe(p):
        if p.get("error"):
            return p
        p["_p0"] = time.time()
        ver = run([FFPROBE, "-hide_banner", "-v", "error",
                   "-show_entries",
                   "stream=codec_name,sample_rate,channels",
                   "-show_entries", "format=duration",
                   "-of", "json", p["out"]])
        if ver.returncode != 0:
            p["error"] = "ffprobe rc=%d: %s" % (ver.returncode,
                                                ver.stderr.decode("utf-8", "replace").strip()[:300])
            return p
        try:
            j = json.loads(ver.stdout.decode("utf-8", "replace"))
            st = (j.get("streams") or [{}])[0]
            p["probe_codec"] = st.get("codec_name")
            p["sample_rate"] = st.get("sample_rate")
            p["channels"] = st.get("channels")
            dur = (j.get("format") or {}).get("duration")
            p["duration"] = float(dur) if dur else None
            if not p["probe_codec"]:
                p["error"] = "ffprobe 未识别出音频流"
        except Exception as e:
            p["error"] = "probe parse: %s" % e
        return p

    ok = [p for p in plan if not p.get("error")]
    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        list(ex.map(probe, ok))

    # ---------------- 阶段 D：写 TSV ----------------
    log("== 阶段 D：写 manifest ==")
    name_cache = {}
    with open(TSV, "w", encoding="utf-8", newline="") as f:
        f.write("类别\t编号\t名字\t源容器\t源条目序号\t输出文件\t输出字节\t时长秒\n")
        for p in sorted(plan, key=lambda x: (x["cat"], x["index"])):
            cat = p["cat"]
            container = {"voice": "VOICE.AWB", "bgm": "BGM.AWB", "se": "SE.AWB"}[cat]
            nm = p.get("name") or "NULL"
            if p.get("error"):
                f.write(f"{cat}\t{p['index']}\t{nm}\t{container}\t{p['index']}\t"
                        f"\t\t\tFAILED: {p['error']}\n")
            else:
                rel = os.path.relpath(p["out"], OUTROOT).replace("\\", "/")
                dur = f"{p['duration']:.3f}" if p.get("duration") is not None else ""
                f.write(f"{cat}\t{p['index']}\t{nm}\t{container}\t{p['index']}\t"
                        f"{rel}\t{p.get('out_bytes', 0)}\t{dur}\n")
    log(f"   -> {TSV}")

    # ---------------- 汇总 ----------------
    log("\n== 汇总 ==")
    fails = [p for p in plan if p.get("error")]
    for cat, container, ctype, q in CATS:
        sub = [p for p in plan if p["cat"] == cat]
        bad = [p for p in sub if p.get("error")]
        tot = sum(p.get("out_bytes", 0) for p in sub)
        from collections import Counter
        cc = Counter(p["codec"] for p in sub)
        log(f"  {cat:6s}: 计划 {len(sub):5d}  成功 {len(sub) - len(bad):5d}  失败 {len(bad):3d}  "
            f"总字节 {tot:,}  源编码 {dict(cc)}")
    log(f"  合计: 计划 {len(plan)}  成功 {len(plan) - len(fails)}  失败 {len(fails)}")

    if fails:
        log("\n  --- 失败清单 ---")
        for p in fails:
            log(f"    {p['cat']}/{p['index']} {p.get('name') or ''}: {p['error']}")
    log(f"\n总耗时 {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
