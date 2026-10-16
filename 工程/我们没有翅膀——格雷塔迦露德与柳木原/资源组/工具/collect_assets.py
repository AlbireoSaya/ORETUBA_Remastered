# -*- coding: utf-8 -*-
r"""
W4 六源素材归集（后三源：otr / otp / np）
================================================
把三个尚未归集的源工程素材「复制 + 改名」进统一 krkr 素材库：

    krkr素材库\otr\   <- 工程\我们没有翅膀R\亜衣线资源\      (仅亚衣线)
    krkr素材库\otp\   <- 工程\我们没有翅膀 前奏诗\素材提取\
    krkr素材库\np\    <- 工程\涅布＊普拉斯\素材提取\

命名规范（总纲 §七 I1）：<来源代号>_<原名>，统一小写。
out_relpath 相对各源根目录，形如 `chr/otr_ai_01.png`（与 ot/_清单.json 约定一致）。

纪律：
  * 源工程一律只读，只用 shutil.copyfile（绝不 mv / 绝不写入源）。
  * 可复跑：目标文件若已存在且字节数一致则跳过（幂等）；不一致则报错。
  * 清单字段：{archive, orig_name, out_relpath, src_bytes, out_bytes, kind}

用法：
    python collect_assets.py            # 执行归集
    python collect_assets.py --dry-run  # 只扫描不写盘
"""
import argparse
import json
import os
import shutil
import sys
import time

# ---------------------------------------------------------------- 配置
WS = r"E:\ZCode Workspace\Galgame"
LIB = os.path.join(WS, r"工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\krkr素材库")

SOURCES = {
    "otr": {
        "root": os.path.join(WS, r"工程\我们没有翅膀R\亜衣线资源"),
        "label": "亜衣线资源",
        "note": "审计报告 §3.4 与本模块任务书写的「3,055 文件」含 `剧本\\` 下 60 个文件"
                "（55 个 s03c_*.tob + 清单），**其中 55 个 .tob 是剧本、非素材**，"
                "不在 krkr 素材库归集范围（属 W6/编程组）。"
                "本模块只归集 图像/语音/音效/BGM，故实测素材数为 353+156+2226+135+125 = 2995。",
        # (源子目录, 目标 kind 子目录, archive 标识)
        "dirs": [
            (r"图像\CHR", "chr", "亜衣线资源/图像/CHR"),
            (r"图像\PIC", "pic", "亜衣线资源/图像/PIC"),
            (r"语音",     "voice", "亜衣线资源/语音"),
            (r"音效",     "se",   "亜衣线资源/音效"),
            (r"BGM",      "bgm",  "亜衣线资源/BGM"),
        ],
    },
    "otp": {
        "root": os.path.join(WS, r"工程\我们没有翅膀 前奏诗\素材提取"),
        "label": "前奏诗",
        "dirs": [
            (r"图像\CHR",   "chr",   "前奏诗/素材提取/图像/CHR"),
            (r"图像\PIC",   "pic",   "前奏诗/素材提取/图像/PIC"),
            (r"图像\SYS",   "sys",   "前奏诗/素材提取/图像/SYS"),
            (r"音频\BGM",   "bgm",   "前奏诗/素材提取/音频/BGM"),
            (r"音频\SE",    "se",    "前奏诗/素材提取/音频/SE"),
            (r"音频\VOICE", "voice", "前奏诗/素材提取/音频/VOICE"),
            (r"影片\DATA",  "movie", "前奏诗/素材提取/影片/DATA"),
            (r"系统数据\SYS", "sys", "前奏诗/素材提取/系统数据/SYS"),
        ],
    },
    "np": {
        "root": os.path.join(WS, r"工程\涅布＊普拉斯\素材提取"),
        "label": "涅布",
        "dirs": [
            (r"图片\立绘", "chr",   "涅布/素材提取/图片/立绘"),
            (r"图片\CG",   "pic",   "涅布/素材提取/图片/CG"),
            (r"图片\背景", "pic",   "涅布/素材提取/图片/背景"),
            (r"图片\演出", "pic",   "涅布/素材提取/图片/演出"),
            (r"音频\BGM",  "bgm",   "涅布/素材提取/音频/BGM"),
            (r"音频\语音", "voice", "涅布/素材提取/音频/语音"),
            (r"音频\音效", "se",    "涅布/素材提取/音频/音效"),
            (r"影像",      "movie", "涅布/素材提取/影像"),
        ],
    },
}


def collect(src_key, dry_run=False):
    cfg = SOURCES[src_key]
    out_root = os.path.join(LIB, src_key)
    entries, failures = [], []
    per_dir = []
    t0 = time.time()

    for sub, kind, archive in cfg["dirs"]:
        src_dir = os.path.join(cfg["root"], sub)
        if not os.path.isdir(src_dir):
            failures.append({"archive": archive, "reason": "源目录不存在", "path": src_dir})
            per_dir.append({"archive": archive, "kind": kind, "entries": 0, "ok": 0,
                            "fail": 1, "out_bytes": 0, "seconds": 0.0})
            continue
        files = sorted(os.listdir(src_dir))
        files = [f for f in files if os.path.isfile(os.path.join(src_dir, f))]
        ok = fail = 0
        out_bytes = 0
        d0 = time.time()
        if not dry_run:
            os.makedirs(os.path.join(out_root, kind), exist_ok=True)

        for f in files:
            src_path = os.path.join(src_dir, f)
            src_bytes = os.path.getsize(src_path)
            new_name = src_key + "_" + f.lower()
            out_rel = kind + "/" + new_name
            out_path = os.path.join(out_root, kind, new_name)
            try:
                if not dry_run:
                    if os.path.exists(out_path):
                        if os.path.getsize(out_path) != src_bytes:
                            raise RuntimeError("目标已存在且字节数不同：%s" % out_path)
                    else:
                        shutil.copyfile(src_path, out_path)
                    out_bytes_now = os.path.getsize(out_path)
                else:
                    out_bytes_now = src_bytes
                entries.append({
                    "archive": archive,
                    "orig_name": f,
                    "kind": kind,
                    "src_bytes": src_bytes,
                    "out_relpath": out_rel,
                    "out_bytes": out_bytes_now,
                })
                ok += 1
                out_bytes += out_bytes_now
            except Exception as e:  # noqa
                fail += 1
                failures.append({"archive": archive, "orig_name": f,
                                 "src": src_path, "reason": str(e)})

        per_dir.append({"archive": archive, "kind": kind, "entries": len(files),
                        "ok": ok, "fail": fail, "out_bytes": out_bytes,
                        "seconds": round(time.time() - d0, 1)})

    # 清单内部去重自检
    seen = {}
    dup = []
    for e in entries:
        if e["out_relpath"] in seen:
            dup.append(e["out_relpath"])
        seen[e["out_relpath"]] = 1

    if not dry_run:
        os.makedirs(out_root, exist_ok=True)
        with open(os.path.join(out_root, "_清单.json"), "w", encoding="utf-8") as fp:
            json.dump(entries, fp, ensure_ascii=False, indent=1)

    total_seconds = round(time.time() - t0, 1)
    return {
        "key": src_key, "root": cfg["root"], "out": out_root, "cfg": cfg,
        "entries": entries, "failures": failures, "per_dir": per_dir,
        "dup_out_relpath": dup, "seconds": total_seconds,
    }


def write_summary(res):
    out_root = res["out"]
    cfg = res.get("cfg", {})
    n = len(res["entries"])
    total_bytes = sum(e["out_bytes"] for e in res["entries"])
    lines = []
    lines.append("# %s 素材归集摘要" % res["key"])
    lines.append("# 生成: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("# 源（只读）: %s" % res["root"])
    lines.append("# 输出: %s" % out_root)
    lines.append("# 命名: %s_<原名小写>  (总纲 §七 I1)" % res["key"])
    lines.append("")
    lines.append("%-28s %8s %8s %8s %12s" % ("来源子目录", "条目数", "成功", "失败", "输出(MB)"))
    for p in res["per_dir"]:
        lines.append("%-28s %8d %8d %8d %12.2f" % (
            p["archive"], p["entries"], p["ok"], p["fail"], p["out_bytes"] / 1048576.0))
    lines.append("-" * 70)
    lines.append("%-28s %8d %8d %8d %12.2f" % (
        "合计", n, n - len(res["failures"]), len(res["failures"]), total_bytes / 1048576.0))
    lines.append("")
    if cfg.get("note"):
        lines.append("口径说明：")
        lines.append("  " + cfg["note"])
        lines.append("")
    lines.append("清单条目数：%d（_清单.json）" % n)
    lines.append("重复 out_relpath：%d" % len(res["dup_out_relpath"]))
    if res["dup_out_relpath"]:
        for d in res["dup_out_relpath"]:
            lines.append("  DUP %s" % d)
    lines.append("失败条目：%d" % len(res["failures"]))
    for f in res["failures"]:
        lines.append("  FAIL %s :: %s :: %s" % (f.get("archive"), f.get("orig_name", f.get("path", "")), f["reason"]))
    lines.append("")
    lines.append("总耗时 %.1f 秒" % res["seconds"])
    with open(os.path.join(out_root, "_提取摘要.txt"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default=None, help="只处理某源（otr/otp/np）")
    args = ap.parse_args()

    keys = [args.only] if args.only else list(SOURCES.keys())
    for k in keys:
        res = collect(k, dry_run=args.dry_run)
        print("[%s] entries=%d fail=%d dup=%d bytes=%d %.1fs" % (
            k, len(res["entries"]), len(res["failures"]),
            len(res["dup_out_relpath"]),
            sum(e["out_bytes"] for e in res["entries"]), res["seconds"]))
        if not args.dry_run:
            write_summary(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())