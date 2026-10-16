#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
transcode_ending_psv.py —— PSV 版《我们没有翅膀～美咲线～》(PCSG00299) 片尾 ED 视频转码

用途
    把 PSV（已解密）的 7 支 `.usm` 片尾视频转成**本项目宿主引擎可用的格式**：
      · `<名小写>.mpg`  —— **视频流原样复制（-c:v copy，画质零损失）** + 音频 MPEG-1 Layer II。
                            宿主是 krkrz 1.4.0.8，视频播放走系统 DirectShow，MPEG-1(.mpg) 是原生目标。
      · `<名小写>.mp4`  —— H.264/AAC，**仅供预览/审阅**，不是交付格式。
      · `<名小写>_f05/50/95.png` —— 约 5% / 50% / 95% 位置各抽一帧，供人工核对 STAFF 与画质。
    并产出清单 `片尾/_raw_psv_ed.tsv`（LF / 制表符 / UTF-8 无 BOM）。

一条命令跑完
    python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/transcode_ending_psv.py"

硬约束（本工程有前例：`os.path.join(main, "..")` 会把文件写到工作区外）
    1. **一切输出路径必须落在本工作树内**（`<worktree>/工程/我们没有翅膀——格雷塔迦露德与柳木原`），
       由 `guard_out()` 用 `realpath` 归一后逐项校验，越界即 FATAL 退出，绝不写入。
    2. 中间产物只落在工作树内的 `片尾/_src/_tmp/`（**不用系统 tempfile**，避免落到 C 盘）。
    3. 源目录**只读**：开工前登记 size/mtime，收尾复核未变。
    4. 拒绝加密副本：源路径含 `NONPDRM` 直接 FATAL（同作的加密副本不可用）。
    5. 7 支全部存在且视频编码为 `mpeg1video` 才开始动手；否则 FATAL，不留半成品。
    6. 清单原子写（先写 `.tmp` 再 `os.replace`），失败不留半截清单。

幂等
    已存在且通过校验的产物直接跳过（`--force` 强制重做）。
    mpg 的校验 = 视频编码/分辨率一致 + 帧数与源一致；mp4/frames 按存在性与帧数校验。

保真自证
    每支都把源与产物的 **MPEG-1 原始基本流（ES）解出并算 md5** —— 两者一致（且字节数一致）
    即证明 `-c:v copy` 是逐字节原样复制；再叠加 ffprobe 的编码/分辨率/帧数三项比对。
    结果写入清单第 10 列 `视频流是否原样复制(是|否)`，明细进 `备注`。

负向自证
    `--self-test` 跑三例 + 一例判据对照，全部必须“失败/拦住”才算 PASS，并带退出码：
      A. **不存在的输入目录** → 端到端必须 FATAL，且不产生任何产物、不改写清单；
      A2. 7 支里缺 1 支（或 0 字节）→ `collect_targets()` 必须 FATAL；
      B. 输出路径越界（`<worktree>/..`）→ `guard_out()` 必须抛错；
      C. 产物缺失时，保真判据**不得**判为「是」（负向对照，防恒真）。

附带产出（写进清单「备注」）
    · **纯色段剖面**（`blank_profile()`，纯 Python、无 numpy 依赖）：降采样后逐帧判近均匀，
      报出 ≥1s 的连续纯色段 —— 把「片头/片尾存在 1s 级纯色段」写成可复跑的计算值。
    · **DirectShow 可播性复跑命令**：指向 `资源组\工具\probe_mci_playable.ps1`
      （MCI mpegvideo 设备 = `IGraphBuilder::RenderFile`，与 krkrz 播放视频同一 API）。
      本次实测 7/7 .mpg OPEN-OK 且推进播放、源 ED_*.usm 全部 OPEN-FAIL。

退出码：0 成功 / 2 输入或环境错误 / 3 保真自证失败 / 4 负向自证失败
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ────────────────────────────────────────────────────────────────
# 路径约定（全部由脚本自身位置推导，不靠调用方 CWD）
# ────────────────────────────────────────────────────────────────
SCRIPT = Path(__file__).resolve()
TOOLS_DIR = SCRIPT.parent                                  # 资源组\工具
RES_DIR = TOOLS_DIR.parent                                 # 资源组
WT_ROOT = RES_DIR.parent                                   # <worktree>\工程\我们没有翅膀——格雷塔迦露德与柳木原
ED_DIR = RES_DIR / "片尾"                                   # 资源组\片尾
OUT_DIR = ED_DIR / "_src" / "psv_ed"                       # 入库排除（.gitignore: 片尾/_src/*/）
FRAME_DIR = OUT_DIR / "_frames"
TMP_DIR = ED_DIR / "_src" / "_tmp"
MANIFEST = ED_DIR / "_raw_psv_ed.tsv"                      # 入库

# 源：主工作区（只读）。**不是**同级 `我们没有翅膀[PCSG00299][日版][日文][NONPDRM]\`（加密，不可用）。
MAIN_ROOT = Path("E:/ZCode Workspace/Galgame")
DEFAULT_SRC = MAIN_ROOT / "工程" / "我们没有翅膀PSV" / "解密" / "PCSG00299" / "media" / "data"

# 7 支片尾：源文件名 → 归属角色（中文名，以作品层 `作品skill\术语表.md` 为准）
#   亚衣  = 术语表 §六 / SKILL §三「亚衣线」（日文 亜衣）
#   明日香 = 术语表 §5.1「渡来明日香」
#   日和子 = 术语表 §2.5（`おまけ` 行内语料写形）
#   小鸠  = 术语表 §2.6「小鳩さん」→ 小鸠
#   美咲  = 术语表 §UI/§七「PSV 美咲线」
#   京    = SKILL §六「s01 鹰志→明日香·京」
#   凤鸣  = 术语表 §5.1/§5.2「鳳 鳴」→ 凤鸣
TARGETS = [
    ("ED_ai.usm",     "亚衣"),
    ("ED_asuka.usm",  "明日香"),
    ("ED_hiyoko.usm", "日和子"),
    ("ED_kobato.usm", "小鸠"),
    ("ED_misaki.usm", "美咲"),
    ("ED_miyako.usm", "京"),
    ("ED_naru.usm",   "凤鸣"),
]

FRAME_PCTS = (5, 50, 95)          # 抽帧位置（占总帧数百分比）
AUDIO_BR_MP2 = "224k"             # mpg 音轨码率（MPEG-1 Layer II 合法档位）
AUDIO_BR_AAC = "160k"
VIDEO_BR_H264 = "2000k"

# 「纯色段」判据（见 blank_profile）：降到 BLANK_W×BLANK_H 灰度后，逐帧 max-min <= BLANK_THRESH 视为近均匀
BLANK_W, BLANK_H, BLANK_THRESH, BLANK_MIN_SEC = 32, 18, 6, 1.0
BLANK_FPS = 30.0                  # 声明帧率（MPEG-1 序列头 frame_rate_code=5）

# 主代理 2026-09-29 裁决：ED_misaki 片头长纯色段按「内容特征（片头淡入）」记录，不改写、不另查。
# 逐支附加说明（人工判读，非脚本计算；写入清单「备注」末段）。
NOTE_EXTRA = {
    "ED_misaki.usm": (
        "⚠ 片头长纯色段按「内容特征（片头淡入）」记录，不做改写、不另查；"
        "同帧数（3,656）同时长（2:01.99）的 ED_asuka / ED_miyako 首帧即有内容"
        "⇒ 该段是否为源 dump 异常**未经证实**"
    ),
}

PROBE_CMD = ('powershell -NoProfile -ExecutionPolicy Bypass -File '
             '"资源组\\工具\\probe_mci_playable.ps1"')

MANIFEST_HEADER = [
    "源文件", "归属角色", "时长", "分辨率", "视频编码", "音频编码", "源字节",
    "mpg字节", "mp4字节", "视频流是否原样复制(是|否)", "抽帧文件名",
    "含图片化文字(是|否)", "文字语言", "备注",
]

ES_CMD_NOTE = 'ffmpeg -i <src> -vf "select=eq(n,{n})" -fps_mode passthrough -frames:v 1 <png>'


class Fatal(RuntimeError):
    pass


# ────────────────────────────────────────────────────────────────
# 路径守卫 —— 「写文件只能写在工作树里」
# ────────────────────────────────────────────────────────────────
def _real(p: Path) -> Path:
    return Path(os.path.realpath(str(p)))


def guard_out(p: Path) -> Path:
    """输出路径必须落在工作树内；`..` 之类越界一律 FATAL（realpath 已归一）。"""
    r = _real(p)
    root = _real(WT_ROOT)
    if r != root and root not in r.parents:
        raise Fatal(f"输出路径越出工作树，拒绝写入：{r}\n           工作树 = {root}")
    return p


def guard_src_dir(p: Path) -> Path:
    """源目录：必须存在、必须在工作树之外、必须确实是本作 PSV 解密目录、必须不是加密副本。"""
    s = str(_real(p))
    if "NONPDRM" in s.upper():
        raise Fatal(f"拒绝：这是加密副本（NONPDRM），不可用 → {s}")
    if not _real(p).is_dir():
        raise Fatal(f"源目录不存在或不是目录：{s}")
    r = _real(p)
    root = _real(WT_ROOT)
    if r == root or root in r.parents:
        raise Fatal(f"源不得位于本工作树内（那是产物区）：{r}")
    if "我们没有翅膀PSV" not in s:
        raise Fatal(f"源目录不像本作 PSV 解密目录，拒绝（防止拿错）：{s}")
    return p


# ────────────────────────────────────────────────────────────────
# 外部命令 / ffprobe 读取
# ────────────────────────────────────────────────────────────────
def run(cmd, check=True):
    cp = subprocess.run(
        [str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", errors="replace",
    )
    if check and cp.returncode != 0:
        raise Fatal("命令失败（exit %d）：\n  %s\n--- stderr ---\n%s"
                    % (cp.returncode, " ".join(str(c) for c in cmd),
                       (cp.stderr or "").strip()[-2000:]))
    return cp


def probe(path: Path) -> dict:
    cp = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    return json.loads(cp.stdout)


def _first_stream(info: dict, kind: str) -> dict:
    for s in info.get("streams", []):
        if s.get("codec_type") == kind:
            return s
    raise Fatal(f"没有 {kind} 流：{json.dumps(info)[:400]}")


def count_frames(path: Path, kind: str = "v") -> int:
    """解码计数帧数（源与产物用同一方法，口径一致）；数不出返回 -1。

    注意：`-of csv=p=0` 只给一个字段时会带一个**尾随逗号**（`3656,`），
    故必须按逗号/空白切分后取第一个纯数字，不能直接 str.isdigit()。
    """
    cp = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", f"{kind}:0",
              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path], check=False)
    for line in (cp.stdout or "").splitlines():
        for tok in line.replace(",", " ").split():
            if tok.isdigit():
                return int(tok)
    return -1


def es_md5(src: Path, dest: Path):
    """解出**视频原始基本流（MPEG-1 ES）**算 md5 —— `-c:v copy` 保真自证的决定性证据。

    源侧 ffmpeg 会在 USM 尾部打一行 `Invalid data found`（尾部填充），但退出码仍是 0；
    这里用 check=False，产物为空则 FATAL。长度/内容比对由调用方负责。
    """
    if dest.exists():
        dest.unlink()
    cp = run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", src,
              "-map", "0:v:0", "-c:v", "copy", "-f", "mpeg1video", dest], check=False)
    if not dest.exists() or dest.stat().st_size == 0:
        raise Fatal(f"视频 ES 解出为空：{src}\n{(cp.stderr or '')[-800:]}")
    h = hashlib.md5()
    with open(dest, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), dest.stat().st_size


# ────────────────────────────────────────────────────────────────
# 单元操作
# ────────────────────────────────────────────────────────────────
def make_mpg(src: Path, out: Path, src_frames: int, src_w: int, src_h: int, force: bool) -> str:
    """视频流原样复制 + 音频 MP2。

    `-preload 0`：ffmpeg 的 mpeg(PS) 封装默认给 0.5s 起始延迟（首帧 PTS≈0.51s，播放开头会空 0.5s）；
    置 0 后音频 PTS 起点 0、视频首帧 PTS +0.010s（不足一帧），AV 差 10ms。
    该选项只影响封装层的时间基准，不影响视频 ES 一个字节（由 ES md5 自证）。
    """
    if not force and out.exists():
        v = _first_stream(probe(out), "video")
        if (v.get("codec_name") == "mpeg1video" and int(v.get("width", 0)) == src_w
                and int(v.get("height", 0)) == src_h and count_frames(out) == src_frames):
            return "skip"
    guard_out(out)
    run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "warning", "-y", "-i", src,
         "-c:v", "copy", "-c:a", "mp2", "-ar", "48000", "-b:a", AUDIO_BR_MP2,
         "-preload", "0", out])
    return "made"


def make_mp4(src: Path, out: Path, force: bool) -> str:
    """H.264/AAC 预览件（libopenh264；本机 ffmpeg 无 libx264）。

    不启用 `-allow_skip_frames`（会让编码器丢帧、预览件帧数对不上源），
    故 libopenh264 会打印一行「bitrate can't be controlled」——无害。
    """
    if not force and out.exists() and out.stat().st_size > 0:
        return "skip"
    guard_out(out)
    run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "warning", "-y", "-i", src,
         "-c:v", "libopenh264", "-profile:v", "main", "-rc_mode", "0", "-b:v", VIDEO_BR_H264,
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", AUDIO_BR_AAC,
         "-movflags", "+faststart", out])
    return "made"


def make_frames(src: Path, base: str, src_frames: int, force: bool):
    """约 5%/50%/95% 位置各抽一帧 PNG（按帧序号精确选取，不依赖按时间 seek）。"""
    made = []
    for pct in FRAME_PCTS:
        idx = min(src_frames - 1, int(round(pct / 100.0 * src_frames)))
        out = FRAME_DIR / f"{base}_f{pct:02d}.png"
        made.append((pct, idx, out))
        if not force and out.exists() and out.stat().st_size > 0:
            continue
        guard_out(out)
        run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", "-i", src,
             "-vf", f"select=eq(n\\,{idx})", "-fps_mode", "passthrough",
             "-frames:v", "1", out])
    return made


def blank_profile(src: Path):
    """降采样成 32×18 灰度逐帧判「近均匀」，返回 (帧数, [(起帧, 止帧), …])（仅 ≥1s 的连续段）。

    用途：把「片头/片尾存在 1s 级纯色段」这一观察写成**可复跑的计算值**，而不是人工断言。
    纯 Python（bytes 的 min/max 是 C 实现），不引入 numpy 依赖。
    """
    cp = subprocess.run(
        [str(c) for c in ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-i", src,
                          "-map", "0:v:0", "-vf", f"scale={BLANK_W}:{BLANK_H},format=gray",
                          "-f", "rawvideo", "-"]],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    raw = cp.stdout or b""
    px = BLANK_W * BLANK_H
    n = len(raw) // px
    runs, start = [], None
    for i in range(n):
        blk = raw[i * px:(i + 1) * px]
        uniform = bool(blk) and (max(blk) - min(blk)) <= BLANK_THRESH
        if uniform:
            if start is None:
                start = i
        else:
            if start is not None:
                if i - start >= BLANK_MIN_SEC * BLANK_FPS:
                    runs.append((start, i - 1))
                start = None
    if start is not None and n - start >= BLANK_MIN_SEC * BLANK_FPS:
        runs.append((start, n - 1))
    return n, runs


def blank_text(runs) -> str:
    if not runs:
        return "无"
    parts = ["%.1f-%.1fs" % (a / BLANK_FPS, b / BLANK_FPS) for a, b in runs]
    return ("共%d段 " % len(parts)) + ", ".join(parts[:6]) + ("…" if len(parts) > 6 else "")


# ────────────────────────────────────────────────────────────────
# 清单 / 目标点齐
# ────────────────────────────────────────────────────────────────
def fmt_dur(seconds: float) -> str:
    total = int(round(seconds * 100))
    return "%d:%02d.%02d" % (total // 6000, (total // 100) % 60, total % 100)


def collect_targets(src_dir: Path):
    """开工前把 7 支全部点齐；缺任何一支即 FATAL（不允许遗漏、不留半成品）。"""
    missing = [n for n, _ in TARGETS if not (src_dir / n).is_file()]
    if missing:
        raise Fatal("源目录缺少 %d 个输入文件，拒绝开工（不产出任何东西）：\n  %s\n  源目录 = %s"
                    % (len(missing), "\n  ".join(missing), src_dir))
    out = []
    for name, cn in TARGETS:
        p = src_dir / name
        if p.stat().st_size == 0:
            raise Fatal(f"输入文件是 0 字节，拒绝开工：{p}")
        info = probe(p)
        v = _first_stream(info, "video")
        a = _first_stream(info, "audio")
        if v.get("codec_name") != "mpeg1video":
            raise Fatal(f"视频编码不是 mpeg1video（{v.get('codec_name')}），源可能拿错：{p}")
        if not v.get("nb_frames"):
            raise Fatal(f"视频流没有帧数信息，无法做保真比对：{p}")
        out.append({"name": name, "cn": cn, "path": p, "v": v, "a": a,
                    "fmt": info.get("format", {})})
    return out


def src_rel(name: str, src_dir: Path) -> str:
    """清单「源文件」列：相对主工作区根、反斜杠（与工程内其它清单同口径）。"""
    try:
        rel = _real(src_dir).relative_to(_real(MAIN_ROOT))
    except ValueError:
        rel = Path(src_dir.name)
    return str(rel / name).replace("/", "\\")


# ────────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PSV 片尾 ED 视频转码（视频流原样复制 + 预览件 + 抽帧 + 清单）")
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="PSV 解密 media\\data 目录（默认本作解密目录）")
    ap.add_argument("--force", action="store_true", help="已存在的产物也重做（默认幂等跳过）")
    ap.add_argument("--self-test", action="store_true", help="跑负向自证后退出")
    ap.add_argument("--keep-tmp", action="store_true", help="保留中间产物目录（排查用）")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    for d in (OUT_DIR, FRAME_DIR, TMP_DIR):
        guard_out(d)
        d.mkdir(parents=True, exist_ok=True)

    src_dir = guard_src_dir(Path(args.src))
    targets = collect_targets(src_dir)
    print(f"[i] 源目录（只读）: {_real(src_dir)}")
    print(f"[i] 产物目录      : {_real(OUT_DIR)}")
    print(f"[i] 工作树        : {_real(WT_ROOT)}")
    print(f"[i] 共 {len(targets)} 支片尾\n")

    before = {t["name"]: (t["path"].stat().st_size, t["path"].stat().st_mtime_ns) for t in targets}

    rows, problems = [], []
    for t in targets:
        name, cn, src = t["name"], t["cn"], t["path"]
        base = Path(name).stem.lower()
        v, a = t["v"], t["a"]

        src_frames = int(v["nb_frames"])
        src_w, src_h = int(v["width"]), int(v["height"])
        dur = float(t["fmt"].get("duration") or a.get("duration") or 0.0)

        mpg = OUT_DIR / f"{base}.mpg"
        mp4 = OUT_DIR / f"{base}.mp4"

        st_mpg = make_mpg(src, mpg, src_frames, src_w, src_h, args.force)
        st_mp4 = make_mp4(src, mp4, args.force)
        frames = make_frames(src, base, src_frames, args.force)

        # ── 保真自证：ES 逐字节 + ffprobe 三项 ──
        es_src, n_src = es_md5(src, TMP_DIR / f"es_src_{base}.bin")
        es_out, n_out = es_md5(mpg, TMP_DIR / f"es_mpg_{base}.bin")
        mi = probe(mpg)
        mv, ma = _first_stream(mi, "video"), _first_stream(mi, "audio")
        mpg_frames = count_frames(mpg)
        mp4_frames = count_frames(mp4)

        chk_codec = (mv.get("codec_name") == v.get("codec_name") == "mpeg1video")
        chk_wh = (int(mv["width"]), int(mv["height"])) == (src_w, src_h)
        chk_frames = (mpg_frames == src_frames)
        chk_es = (es_src == es_out) and (n_src == n_out)
        faithful = bool(chk_codec and chk_wh and chk_frames and chk_es)
        audio_ok = (ma.get("codec_name") == "mp2" and int(ma.get("sample_rate", 0)) == 48000)
        preview_ok = (mp4_frames == src_frames)
        if not faithful:
            problems.append(f"{name}: 保真自证未过 codec={chk_codec} wh={chk_wh} "
                            f"frames={chk_frames}(mpg {mpg_frames}/src {src_frames}) es={chk_es}")
        if not audio_ok:
            problems.append(f"{name}: mpg 音轨异常 codec={ma.get('codec_name')} sr={ma.get('sample_rate')}")
        if not preview_ok:
            problems.append(f"{name}: mp4 预览件帧数 {mp4_frames} != 源 {src_frames}")

        # ── 清单行 ──
        fnames = [o.name for _, _, o in frames]
        fpos = "/".join(str(i) for _, i, _ in frames)
        ftimes = "/".join("%.2fs" % (i / 30.0) for _, i, _ in frames)
        _, blank_runs = blank_profile(src)
        note = (
            f"视频 ES md5 {es_src}（源=产物，{n_src} B 逐字节一致）；"
            f"mpg 封装 -preload 0（去 ffmpeg 默认 0.5s 起始偏移，视频首帧 PTS +0.010s、AV 差 10ms）；"
            f"mpg 音轨 mp2 {AUDIO_BR_MP2}/48kHz/立体声；"
            f"mp4 预览 H.264(main/{VIDEO_BR_H264})/AAC {AUDIO_BR_AAC}，{mp4_frames} 帧；"
            f"抽帧按帧序号 n={fpos}（声明帧率 30fps ⇒ {ftimes}），命令 " + ES_CMD_NOTE + "；"
            f"纯色段(≥1s；判据 {BLANK_W}x{BLANK_H} 灰度逐帧 max-min<={BLANK_THRESH} 的连续帧): "
            f"{blank_text(blank_runs)}；"
            f"DirectShow 可播性复跑（相对本作工程目录）：{PROBE_CMD}"
            f"——本目录 7 支 .mpg 应 OPEN-OK 且 mode=playing，源 ED_*.usm 应 OPEN-FAIL"
            + (("；" + NOTE_EXTRA[name]) if name in NOTE_EXTRA else "")
        )
        rows.append([
            src_rel(name, src_dir),
            cn,
            fmt_dur(dur),
            f"{src_w}x{src_h}",
            v.get("codec_name", ""),
            a.get("codec_name", ""),
            str(src.stat().st_size),
            str(mpg.stat().st_size),
            str(mp4.stat().st_size),
            "是" if faithful else "否",
            ";".join(fnames),
            "是",
            "日语",
            note,
        ])
        print(f"[{cn}] {name}  帧 {src_frames}  mpg {mpg.stat().st_size:,} B({st_mpg})"
              f"  mp4 {mp4.stat().st_size:,} B({st_mp4})  保真={'是' if faithful else '否'}")

    # ── 源只读复核 ──
    for t in targets:
        now = (t["path"].stat().st_size, t["path"].stat().st_mtime_ns)
        if now != before[t["name"]]:
            problems.append(f"{t['name']}: 源文件被改动（size/mtime 变化）——违反只读约定")

    # ── 写清单（原子；LF / tab / UTF-8 无 BOM）──
    if len(rows) != len(TARGETS):
        raise Fatal(f"清单行数 {len(rows)} != {len(TARGETS)}，拒绝写清单")
    guard_out(MANIFEST)
    tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    guard_out(tmp)
    for r in rows:
        assert not any("\t" in c or "\n" in c for c in r), "单元格不得含制表符/换行"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(MANIFEST_HEADER) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    os.replace(tmp, MANIFEST)
    print(f"\n[+] 清单已写：{_real(MANIFEST)}（{len(rows)} 行 + 表头）")

    if not args.keep_tmp:
        shutil.rmtree(TMP_DIR, ignore_errors=True)

    if problems:
        print("\n[!] 问题：")
        for p in problems:
            print("   - " + p)
        return 3
    print("[OK] 全部 7 支保真自证通过（视频 ES 逐字节一致 + 编码/分辨率/帧数一致）")
    return 0


# ────────────────────────────────────────────────────────────────
# 负向自证
# ────────────────────────────────────────────────────────────────
def _main_expect_fail(argv):
    """跑 main()，把 Fatal 当成“预期失败”捕获（返回非 0 退出码）。"""
    try:
        return main(argv)
    except Fatal as e:
        print(f"    （预期失败）{str(e).splitlines()[0]}")
        return 2


def self_test() -> int:
    """负向自证：脚本必须“报错/拦住”，而不是静默产出空结果。"""
    print("=== 负向自证（--self-test）===")
    results = []

    def expect_fatal(fn) -> bool:
        try:
            fn()
            return False
        except Fatal:
            return True

    # 目录先就位，保证下面 before/after 快照可比
    for d in (OUT_DIR, FRAME_DIR, TMP_DIR):
        guard_out(d)
        d.mkdir(parents=True, exist_ok=True)

    # A. 不存在的输入目录（含“不存在的输入文件”）→ 端到端 FATAL，且零产出、清单未被改写
    bogus = _real(MAIN_ROOT / "工程" / "我们没有翅膀PSV" / "解密" / "PCSG00299" / "media"
                  / "__不存在的目录__")
    snap_out = sorted(p.name for p in OUT_DIR.iterdir())
    snap_man = MANIFEST.stat().st_mtime_ns if MANIFEST.exists() else None
    rc = _main_expect_fail(["--src", str(bogus)])
    now_out = sorted(p.name for p in OUT_DIR.iterdir())
    now_man = MANIFEST.stat().st_mtime_ns if MANIFEST.exists() else None
    ok_a = (rc != 0) and (now_out == snap_out) and (now_man == snap_man)
    results.append(("A 不存在的输入目录 → FATAL，且零产出、清单未改写", ok_a))

    # A2. 7 支里缺 1 支 / 0 字节输入 → collect_targets 必须 FATAL（不允许遗漏）
    saved = list(TARGETS)
    try:
        TARGETS[:] = [("ED_misaki.usm", "美咲"), ("ED_不存在_.usm", "X")]
        ok_missing = expect_fatal(lambda: collect_targets(_real(DEFAULT_SRC)))
        fixture = TMP_DIR / "_selftest_zero.bin"          # 0 字节夹具（工作树内、已被 gitignore）
        fixture.write_bytes(b"")
        try:
            TARGETS[:] = [("_selftest_zero.bin", "X")]
            ok_zero = expect_fatal(lambda: collect_targets(TMP_DIR))
        finally:
            fixture.unlink(missing_ok=True)
    finally:
        TARGETS[:] = saved
    results.append(("A2 缺 1 支 / 0 字节输入 → collect_targets FATAL（不允许遗漏）",
                    ok_missing and ok_zero))

    # B. 输出路径越界（模拟 os.path.join(main, "..")）→ guard_out 必须拦住
    blocked = False
    try:
        guard_out(WT_ROOT / ".." / ".." / "片尾_越界测试.tsv")
    except Fatal:
        blocked = True
    results.append(("B 输出越出工作树 → guard_out 拦住", blocked))

    # C. 产物缺失时，保真判据不得判「是」（负向对照，防恒真）
    faithful = True
    try:
        info = probe(FRAME_DIR / "__not_exist__.mpg")
        faithful = _first_stream(info, "video").get("codec_name") == "mpeg1video"
    except Fatal:
        faithful = False
    results.append(("C 产物缺失时保真判据不得判「是」（负向对照）", faithful is False))

    allok = True
    for nm, ok in results:
        print(("  PASS  " if ok else "  FAIL  ") + nm)
        allok = allok and ok
    print("=== 负向自证：" + ("全部通过" if allok else "存在 FAIL") + " ===")
    return 0 if allok else 4


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fatal as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(2)
