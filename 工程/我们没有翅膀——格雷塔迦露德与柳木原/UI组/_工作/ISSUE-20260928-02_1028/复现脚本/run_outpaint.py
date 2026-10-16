# -*- coding: utf-8 -*-
r"""
run_outpaint.py —— 4:3 → 16:9 补边跑批驱动（ISSUE-20260928-02 · E6 模块）

设计口径（一律照抄 `.zcode\skills\asset-outpaint\outpaint_verify.py`，不自创）：
    2× 超分源 (1600×1200)
      → 居中放进 16:9 画布 (高×16/9，宽向上取到 8 的倍数 → 2136×1200)
      → 四周各外扩 PAD=64 px 填黑（PAD_MODE=black）
      → 掩码：原图区 0 / 其余 255 → 推理张量 2264×1328
      → LaMa(lama-manga-dynamic.onnx) 推理
      → 裁掉 PAD → 2136×1200
      → Lanczos 降到 1920×1080

引擎：优先 onnxruntime-directml（需 OUTPAINT_DML=1），失败自动回落 CPU。
      --engine lama 走 torch JIT big-lama.pt（慢，备用）。

特性：幂等（已存在且合法的输出默认跳过）、可断点续跑、参数化、
      逐件落盘断言（存在 / IHDR==1920×1080 / w/h 与 16/9 偏差<0.01）、
      失败件写入 失败清单.tsv 并继续、跑完刷新 尺寸回传变更表。

用法（见 RUN_640.md）：
    set OUTPAINT_DML=1
    python run_outpaint.py                      # 全量 640 件（跳过已有）
    python run_outpaint.py --tier T2            # 只跑 T2
    python run_outpaint.py --names ld_bg.png,sl_01.png
    python run_outpaint.py --pilot              # 固定 10 件 pilot 集
    python run_outpaint.py --emit-tsv           # 只刷新变更表，不推理
    python run_outpaint.py --dry-run            # 只列件不推理
"""
import sys, os, time, csv, json, struct, argparse, ctypes, ctypes.wintypes

# ---------------------------------------------------------------- 路径
WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
WT_PROJ = os.path.join(WS, "临时", "wt-qbicons", "工程", "我们没有翅膀——格雷塔迦露德与柳木原")

HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)                       # ...\ISSUE-20260928-02_1028

sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
sys.path.insert(0, os.path.join(WS, "工具", "outpaint", "pylibs"))
if os.environ.get("OUTPAINT_DML") == "1":
    # 必须放最前面：两个 onnxruntime 同名文件，放错顺序会静默用错版本
    sys.path.insert(0, os.path.join(WS, "工具", "outpaint", "pylibs_dml"))

import numpy as np
from PIL import Image, ImageDraw, ImageFont

LIST_TSV = os.path.join(MAIN_PROJ, "资源组", "美术", "4比3待重制清单.tsv")
MANGA_ONNX = os.path.join(WS, "工具", "outpaint", "models", "lama-manga-dynamic.onnx")
LAMA_PT = os.path.join(WS, "工具", "outpaint", "models", "big-lama.pt")

TARGET = (1920, 1080)
PAD = 64
PAD_MODE = "black"
ALPHA_MODE = "keep-edge"   # keep-edge | keep-zero | drop（见报告「alpha 件」一节）

PILOT_T2 = ["ld_over.png", "sv_bg.png", "hiy65.png", "miy12b.png", "ai_07.png"]
PILOT_T3 = ["sl_03.png", "sl_01.png", "sr0_01.png", "sr2_03.png", "sr4_19.png"]

# ---------------------------------------------------------------- 内存采样
class _PMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def peak_ws_mb():
    try:
        fn = ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(_PMC), ctypes.wintypes.DWORD]
        fn.restype = ctypes.wintypes.BOOL
        pmc = _PMC(); pmc.cb = ctypes.sizeof(_PMC)
        fn(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        return round(pmc.PeakWorkingSetSize / 1048576.0, 1)
    except Exception:
        return None


# ---------------------------------------------------------------- 画布 / 掩码（照抄 outpaint_verify.py）
def make_canvas(img, pad8=True):
    W, H = img.size
    NW = int(round(H * 16 / 9))
    if pad8:
        NW += (8 - NW % 8) % 8
        H = H + (8 - H % 8) % 8
    ox = (NW - W) // 2
    canvas = Image.new("RGB", (NW, H), (0, 0, 0))
    canvas.paste(img, (ox, 0))
    mask = Image.new("L", (NW, H), 255)
    mask.paste(Image.new("L", (W, img.size[1]), 0), (ox, 0))
    return canvas, mask, ox, (NW, H)


def _pad_canvas(img, pad, pad_mode="black"):
    canvas, mask, ox, csize = make_canvas(img)
    if pad:
        W, H = canvas.size
        NW, NH = W + 2 * pad, H + 2 * pad
        if pad_mode == "mirror":
            c2 = canvas.transpose(Image.FLIP_LEFT_RIGHT).resize((NW, NH), Image.BILINEAR)
            c2.paste(canvas, (pad, pad))
        else:
            c2 = Image.new("RGB", (NW, NH), (0, 0, 0)); c2.paste(canvas, (pad, pad))
        m2 = Image.new("L", (NW, NH), 255); m2.paste(mask, (pad, pad))
        NW += (8 - NW % 8) % 8
        NH += (8 - NH % 8) % 8
        if (NW, NH) != c2.size:
            c3 = Image.new("RGB", (NW, NH), (0, 0, 0)); c3.paste(c2, (0, 0))
            m3 = Image.new("L", (NW, NH), 255); m3.paste(m2, (0, 0))
            c2, m2 = c3, m3
        canvas, mask, ox, csize = c2, m2, ox + pad, (NW, NH)
    return canvas, mask, ox, csize, pad


def _unpad(im, csize, pad):
    if pad:
        return im.crop((pad, pad, csize[0] - pad, csize[1] - pad))
    return im


# ---------------------------------------------------------------- 模型（ONNX 优先 / torch 备用）
_sess = None
_sess_provider = None
_sess_tried_dml = False
_lama = None


def _build_onnx(use_dml):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = 6
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    prov = ["DmlExecutionProvider", "CPUExecutionProvider"] if use_dml else ["CPUExecutionProvider"]
    return ort.InferenceSession(MANGA_ONNX, so, providers=prov)


def onnx_session(allow_dml_fallback=True):
    """懒加载；DML 初始化失败时回落 CPU（一次性）。"""
    global _sess, _sess_provider, _sess_tried_dml
    if _sess is not None:
        return _sess
    want_dml = os.environ.get("OUTPAINT_DML") == "1"
    if want_dml:
        _sess_tried_dml = True
        try:
            s = _build_onnx(True)
            _sess, _sess_provider = s, "DmlExecutionProvider"
            print("[engine] ORT providers = %s" % s.get_providers(), flush=True)
            return _sess
        except Exception as e:
            sys.stderr.write("[WARN] DirectML 初始化失败，回落 CPU：%r\n" % (e,))
    _sess, _sess_provider = _build_onnx(False), "CPUExecutionProvider"
    print("[engine] ORT providers = %s" % _sess.get_providers(), flush=True)
    return _sess


def force_cpu_session():
    """推理期 DML 报错时切 CPU 并重来（只切一次）。"""
    global _sess, _sess_provider
    _sess, _sess_provider = _build_onnx(False), "CPUExecutionProvider"


def lama_model():
    global _lama
    if _lama is None:
        import torch
        torch.set_num_threads(6)
        with open(LAMA_PT, "rb") as f:          # 非 ASCII 路径必须走文件对象
            _lama = torch.jit.load(f, map_location="cpu")
        _lama.eval()
    return _lama


def outpaint_onnx(img, pad=PAD, pad_mode=PAD_MODE):
    canvas, mask, ox, csize, pad = _pad_canvas(img, pad, pad_mode)
    a = np.asarray(canvas).astype(np.float32) / 255.0
    m = (np.asarray(mask).astype(np.float32) / 255.0)
    m = np.where(m > 0.5, 1.0, 0.0).astype(np.float32)
    it = a.transpose(2, 0, 1)[None, ...].copy()
    mt = m[None, None, ...].copy()
    t0 = time.time()
    try:
        out = onnx_session().run(None, {"image": it, "mask": mt})[0]
    except Exception as e:
        if _sess_provider == "DmlExecutionProvider":
            sys.stderr.write("[WARN] DML 推理失败，切 CPU 重试：%r\n" % (e,))
            force_cpu_session()
            out = onnx_session().run(None, {"image": it, "mask": mt})[0]
        else:
            raise
    dt = time.time() - t0
    res = (np.clip(out[0].transpose(1, 2, 0), 0, 1) * 255).astype(np.uint8)
    return _unpad(Image.fromarray(res), csize, pad), dt, ox, csize


def outpaint_torch(img, pad=PAD, pad_mode=PAD_MODE):
    import torch
    canvas, mask, ox, csize, pad = _pad_canvas(img, pad, pad_mode)
    a = np.asarray(canvas).astype(np.float32) / 255.0
    m = np.asarray(mask).astype(np.float32) / 255.0
    it = torch.from_numpy(a).permute(2, 0, 1).unsqueeze(0).contiguous()
    mt = torch.from_numpy(m).unsqueeze(0).unsqueeze(0).contiguous()
    with torch.no_grad():
        t0 = time.time()
        out = lama_model()(it, mt)
        dt = time.time() - t0
    res = (out[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).astype(np.uint8)
    return _unpad(Image.fromarray(res), csize, pad), dt, ox, csize


# ---------------------------------------------------------------- 几何
def canvas_geom(W, H, pad=0):
    """16:9 画布几何（与 _pad_canvas 内的算法同源）。返回 (NW, Hp, ox)。"""
    NW = int(round(H * 16 / 9))
    NW += (8 - NW % 8) % 8
    Hp = H + (8 - H % 8) % 8
    ox = (NW - W) // 2
    return NW, Hp, ox


def out_seams(W, H):
    """内容区（原图像素）在 1920×1080 输出坐标系中的左/右边界 x。
    注意：**不是** 1080*4/3=1440 —— 画布宽取 8 的倍数（2136）使横向缩放略小于纵向，
    真实内容区 = [round(ox*1920/NW), round((ox+W)*1920/NW)]。"""
    NW, Hp, ox = canvas_geom(W, H)
    return int(round(ox * TARGET[0] / NW)), int(round((ox + W) * TARGET[0] / NW))


def alpha169(alpha, mode=ALPHA_MODE):
    """把原图 alpha 扩到 16:9 并降到 1920×1080。
    keep-edge：左右新增条沿用最近的内容列 alpha（延续叠加层的外框/暗角）；
    keep-zero：新增条 alpha=0（叠加层止于原 4:3 边界）。
    """
    W, H = alpha.size
    NW, Hp, ox = canvas_geom(W, H)
    c = Image.new("L", (NW, Hp), 0)
    c.paste(alpha, (ox, 0))
    if mode == "keep-edge" and ox > 0:
        c.paste(alpha.crop((0, 0, 1, H)).resize((ox, Hp)), (0, 0))
        c.paste(alpha.crop((W - 1, 0, W, H)).resize((NW - ox - W, Hp)), (ox + W, 0))
    return c.resize(TARGET, Image.LANCZOS)



# ---------------------------------------------------------------- 落盘断言
def png_ihdr(path):
    with open(path, "rb") as f:
        head = f.read(33)
    if len(head) < 33 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError("非合法 PNG / 无 IHDR")
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def assert_output(path):
    """返回 (w, h)；不合规抛异常。"""
    if not os.path.exists(path):
        raise AssertionError("输出不存在: %s" % path)
    w, h = png_ihdr(path)
    if (w, h) != TARGET:
        raise AssertionError("IHDR %dx%d != %dx%d" % (w, h, TARGET[0], TARGET[1]))
    if abs(w / h - 16.0 / 9.0) >= 0.01:
        raise AssertionError("宽高比偏差 %.5f >= 0.01" % abs(w / h - 16.0 / 9.0))
    return w, h


# ---------------------------------------------------------------- 清单
def load_rows(project_root):
    if not os.path.exists(LIST_TSV):
        raise SystemExit("清单不存在: %s" % LIST_TSV)
    rows = list(csv.DictReader(open(LIST_TSV, encoding="utf-8"), delimiter="\t"))
    out = []
    for r in rows:
        if r["建议策略(重制/补边/裁切)"] != "补边":
            continue
        src = os.path.join(project_root, r["超分版路径"])
        out.append({"name": r["统一名"], "tier": r["建议档位(T1/T2/T3)"],
                    "cat": r["类别"], "cls": r["判读类别"], "src": src})
    return out


def resolve_project_root(forced=None):
    if forced:
        return forced
    if os.path.isdir(os.path.join(MAIN_PROJ, "资源组", "美术统一_超分")):
        return MAIN_PROJ
    return WT_PROJ


# ---------------------------------------------------------------- pilot 对照图
def _font(sz=18):
    for p in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
              r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def _panel(im, h, label):
    w = max(1, int(round(im.width * h / im.height)))
    t = im.resize((w, h), Image.LANCZOS)
    bar = 26
    out = Image.new("RGB", (w, h + bar), (24, 24, 24))
    out.paste(t, (0, bar))
    ImageDraw.Draw(out).text((6, 4), label, fill=(255, 220, 80), font=_font(17))
    return out


def make_pilot_figure(stem, src1x, ai1920, out_path, extra="", seams=None):
    """三联横向拼图：原图 4:3 / 补边后 16:9（标真实接缝位）/ 接缝 4× 裁图（左缝+右缝）。
    seams = 内容区在输出坐标的左/右边界（见 out_seams，**不是** 1440）。"""
    if seams is None:
        W, H = src1x.size
        seams = out_seams(W, H)
    xl, xr = seams
    H = 460
    p1 = _panel(src1x, H, "ORIGINAL 4:3 (%dx%d)" % src1x.size)
    # 16:9 面板上标出真实接缝位置
    marks = ai1920.copy()
    d = ImageDraw.Draw(marks)
    for x in (xl, xr):
        d.line([(x, 0), (x, 1080)], fill=(255, 40, 40), width=3)
    p2 = _panel(marks, H, "OUTPAINT 16:9 %dx%d %s" % (ai1920.size[0], ai1920.size[1], extra))
    # 接缝 4×（以真实缝为中心取 160×115 窗口，4× → 640×460）
    crop_y = 540 - 57
    zs = []
    for xc, lab in ((xl, "SEAM L 4x @x=%d" % xl), (xr, "SEAM R 4x @x=%d" % xr)):
        x0 = max(0, min(ai1920.width - 160, xc - 80))
        c = ai1920.crop((x0, crop_y, x0 + 160, crop_y + 115))
        zs.append(_panel(c.resize((640, 460), Image.NEAREST), H, lab))
    gap = 6
    W = p1.width + p2.width + sum(z.width for z in zs) + gap * 4
    canvas = Image.new("RGB", (W, H + 26), (12, 12, 12))
    x = 0
    for p in (p1, p2, zs[0], zs[1]):
        canvas.paste(p, (x, 0)); x += p.width + gap
    canvas.save(out_path)
    return out_path


# ---------------------------------------------------------------- 变更表
def scan_alpha(rows):
    """扫出「源带 alpha」与「源非 1600×1200」的例外件（进 待裁决_alpha件.tsv）。"""
    import numpy as _np
    out = []
    for r in rows:
        if not os.path.exists(r["src"]):
            out.append([r["name"], r["tier"], r["cat"], "", "源缺失", "", "", ""])
            continue
        im = Image.open(r["src"])
        size, mode = im.size, im.mode
        if mode in ("RGBA", "LA", "P") or size != (1600, 1200):
            a0 = a1 = am = ""
            if mode in ("RGBA", "LA", "P"):
                A = _np.asarray(im.split()[-1]).astype(_np.float32)
                a0 = "%.1f%%" % ((A == 0).mean() * 100)
                a1 = "%.1f%%" % ((A >= 255).mean() * 100)
                am = "%.1f" % A.mean()
            out.append([r["name"], r["tier"], r["cat"], "%dx%d" % size, mode,
                        a0, a1, am])
        im.close()
    return out


def emit_tsv(rows, out_dir, tsv_path):
    """按磁盘实际产物刷新 4比3重制_尺寸回传.tsv（640 行）。"""
    n_ok = 0
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "新尺寸(w,h)", "新内容bbox", "新字节", "新分类",
                    "改了哪一侧", "备注"])
        for r in rows:
            p = os.path.join(out_dir, r["name"])
            nbytes = ""
            if os.path.exists(p):
                try:
                    assert_output(p)
                    nbytes = os.path.getsize(p)
                    n_ok += 1
                except AssertionError:
                    nbytes = ""
            w.writerow([r["name"], "1920x1080", "1920x1080", nbytes,
                        cls_of(r["name"]), "美术统一_超分", "补边产物待原位替换"])
    # 例外件（alpha / 非标尺寸）单列，供主代理裁决
    ex = scan_alpha(rows)
    with open(os.path.join(os.path.dirname(tsv_path), "待裁决_alpha件.tsv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "档位", "类别", "源尺寸", "源模式",
                    "alpha==0 占比", "alpha==255 占比", "alpha 均值"])
        w.writerows(ex)
    return n_ok


_CLS_CACHE = None


def cls_of(name):
    global _CLS_CACHE
    if _CLS_CACHE is None:
        _CLS_CACHE = {}
        p = os.path.join(MAIN_PROJ, "资源组", "美术统一", "交付清单.tsv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"):
                _CLS_CACHE[r["统一名"]] = r["分类"]
    return _CLS_CACHE.get(name, "")


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--out-dir", default=os.path.join(ISSUE_DIR, "outpaint"))
    ap.add_argument("--tsv", default=os.path.join(ISSUE_DIR, "4比3重制_尺寸回传.tsv"))
    ap.add_argument("--fail-tsv", default=os.path.join(ISSUE_DIR, "失败清单.tsv"))
    ap.add_argument("--names", default=None, help="逗号分隔的统一名；排他于 --tier/--pilot")
    ap.add_argument("--tier", default=None, help="T2 或 T3 或 T2,T3")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--engine", default="manga", choices=["manga", "lama"])
    ap.add_argument("--pad", type=int, default=PAD)
    ap.add_argument("--pad-mode", default=PAD_MODE, choices=["black", "mirror"])
    ap.add_argument("--force", action="store_true", help="重跑并覆盖已有输出")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--emit-tsv", action="store_true", help="只刷新变更表")
    ap.add_argument("--alpha-mode", default=ALPHA_MODE,
                    choices=["keep-edge", "keep-zero", "drop"],
                    help="源带 alpha 时的处理：keep-edge 保留 alpha（新增条沿用边缘列）/ "
                         "keep-zero 保留 alpha（新增条全透明）/ drop 丢 alpha 转 RGB")
    ap.add_argument("--fig-dir", default=os.path.join(ISSUE_DIR, "证据", "pilot_对照图"))
    ap.add_argument("--fig", action="store_true", help="产出三联对照图")
    ap.add_argument("--fig-only", action="store_true", help="不推理，只按已有产物重画对照图")
    args = ap.parse_args()

    proj = resolve_project_root(args.project_root)
    rows = load_rows(proj)
    by_name = {r["name"]: r for r in rows}
    print("清单补边件数: %d  (project_root=%s)" % (len(rows), proj), flush=True)

    if args.emit_tsv:
        n = emit_tsv(rows, args.out_dir, args.tsv)
        print("变更表已刷新: %s  （已有合格产物 %d/%d 件）" % (args.tsv, n, len(rows)))
        return

    # 选件
    jobs = None
    if args.pilot:
        names = PILOT_T2 + PILOT_T3
        miss = [n for n in names if n not in by_name]
        if miss:
            raise SystemExit("pilot 件不在补边清单: %s" % miss)
        jobs = [by_name[n] for n in names]
    elif args.names:
        names = [n.strip() for n in args.names.split(",") if n.strip()]
        miss = [n for n in names if n not in by_name]
        if miss:
            raise SystemExit("件不在补边清单: %s" % miss)
        jobs = [by_name[n] for n in names]
    else:
        jobs = rows
        if args.tier:
            want = {t.strip() for t in args.tier.split(",") if t.strip()}
            jobs = [r for r in jobs if r["tier"] in want]
    if args.limit:
        jobs = jobs[:args.limit]

    print("本次计划件数: %d  engine=%s pad=%d pad_mode=%s DML=%s"
          % (len(jobs), args.engine, args.pad, args.pad_mode,
             os.environ.get("OUTPAINT_DML") == "1"), flush=True)
    if args.dry_run:
        for r in jobs:
            print("  %-18s %s %s -> %s (src exists=%s)"
                  % (r["name"], r["tier"], r["cat"], os.path.join(args.out_dir, r["name"]),
                     os.path.exists(r["src"])))
        return

    os.makedirs(args.out_dir, exist_ok=True)
    if args.fig or args.fig_only:
        os.makedirs(args.fig_dir, exist_ok=True)

    # --fig-only：不推理，只按已有产物重画对照图
    if args.fig_only:
        n = 0
        for r in jobs:
            dst = os.path.join(args.out_dir, r["name"])
            if not os.path.exists(dst):
                print("  skip(无产物) %s" % r["name"]); continue
            s1 = os.path.join(proj, "资源组", "美术统一", r["cat"], r["name"])
            if os.path.exists(s1):
                src1x = Image.open(s1)
                if src1x.mode not in ("RGB", "RGBA", "L"):
                    src1x = src1x.convert("RGB")
            else:
                src1x = Image.open(r["src"]).convert("RGB")
            out = Image.open(dst)
            if out.mode == "RGBA":
                out = out.convert("RGB")
            fig = os.path.join(args.fig_dir,
                               "pilot_%s_三联.png" % os.path.splitext(r["name"])[0])
            seams = out_seams(*src1x.size)
            # 注：源 2× 尺寸决定接缝；此处用 1× 尺寸算出的比例一致（同宽高比同画布公式）
            make_pilot_figure(r["name"], src1x, out, fig,
                              extra="manga 4x-seam", seams=out_seams(
                                  *Image.open(r["src"]).size))
            n += 1
            print("  fig -> %s (seams=%s)" % (os.path.basename(fig),
                                              out_seams(*Image.open(r["src"]).size)))
        print("对照图 %d 张 -> %s" % (n, args.fig_dir))
        return

    fails, done, skip = [], 0, 0
    met = []
    t_start = time.time()
    for i, r in enumerate(jobs):
        dst = os.path.join(args.out_dir, r["name"])
        # 幂等：已有合法输出直接跳过
        if not args.force and os.path.exists(dst):
            try:
                assert_output(dst)
                skip += 1
                continue
            except AssertionError:
                pass
        rec = {"name": r["name"], "tier": r["tier"], "cat": r["cat"]}
        try:
            if not os.path.exists(r["src"]):
                raise AssertionError("源不存在: %s" % r["src"])
            t0 = time.time()
            src_im = Image.open(r["src"])
            has_alpha = src_im.mode in ("RGBA", "LA", "P")
            alpha_src = src_im.split()[-1].copy() if has_alpha else None
            img = src_im.convert("RGB")
            rec["src_size"] = "%dx%d" % img.size
            rec["src_mode"] = src_im.mode
            if args.engine == "manga":
                canvas169, dt, ox, csize = outpaint_onnx(img, args.pad, args.pad_mode)
            else:
                canvas169, dt, ox, csize = outpaint_torch(img, args.pad, args.pad_mode)
            rec["csize"] = "%dx%d" % csize
            final = canvas169.resize(TARGET, Image.LANCZOS)
            if alpha_src is not None and args.alpha_mode != "drop":
                final = final.convert("RGBA")
                final.putalpha(alpha169(alpha_src, args.alpha_mode))
                rec["alpha"] = args.alpha_mode
            final.save(dst)
            w, h = assert_output(dst)
            saved = Image.open(dst)
            rec.update({"infer_s": round(dt, 2), "total_s": round(time.time() - t0, 2),
                        "out_size": "%dx%d" % (w, h), "out_mode": saved.mode,
                        "bytes": os.path.getsize(dst),
                        "peak_ws_mb": peak_ws_mb()})
            saved.close()
            if args.fig:
                # 用 1× 原图做展示（找不到就退回 2× 源）
                s1 = os.path.join(proj, "资源组", "美术统一", r["cat"], r["name"])
                src1x = Image.open(s1) if os.path.exists(s1) else img
                fig = os.path.join(args.fig_dir, "pilot_%s_三联.png" % os.path.splitext(r["name"])[0])
                figim = final
                make_pilot_figure(r["name"], src1x, figim, fig,
                                  extra="%s infer=%.1fs %s" % (args.engine, dt, rec["out_mode"]),
                                  seams=out_seams(*img.size))
                rec["fig"] = fig
            done += 1
            met.append(rec)
            el = time.time() - t_start
            eta = (el / max(done, 1)) * (len(jobs) - i - 1 - skip)
            print("[%3d/%3d] OK   %-18s %s %s  infer=%5.2fs total=%5.2fs  bytes=%s  %s  peakWS=%sMB  用时%5.1fs 余量ETA=%5.1fmin"
                  % (i + 1, len(jobs), r["name"], r["tier"], r["cat"], dt, rec["total_s"],
                     rec["bytes"], rec["out_mode"], rec["peak_ws_mb"], el, eta / 60), flush=True)
        except Exception as e:
            rec["error"] = repr(e)
            fails.append(rec)
            print("[%3d/%3d] FAIL %-18s %s" % (i + 1, len(jobs), r["name"], e), flush=True)

    # 失败清单（覆盖写，保证与本次一致）
    with open(args.fail_tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "档位", "类别", "错误"])
        for x in fails:
            w.writerow([x["name"], x["tier"], x["cat"], x["error"]])

    n_ok = emit_tsv(rows, args.out_dir, args.tsv)
    print("\n== 汇总 ==")
    print("计划 %d ｜ 新做 %d ｜ 跳过(已有) %d ｜ 失败 %d ｜ 用时 %.1f min"
          % (len(jobs), done, skip, len(fails), (time.time() - t_start) / 60))
    print("变更表 %s（已有合格产物 %d/%d）" % (args.tsv, n_ok, len(rows)))
    print("失败清单 %s（%d 行）" % (args.fail_tsv, len(fails)))
    if met:
        bs = [m["bytes"] for m in met if "bytes" in m]
        ts = [m["total_s"] for m in met if "total_s" in m]
        print("单件：字节 min/mean/max = %d / %.0f / %d；总耗时 mean = %.2f s"
              % (min(bs), sum(bs) / len(bs), max(bs), sum(ts) / len(ts)) if bs and ts else "")
        json.dump(met, open(os.path.join(ISSUE_DIR, "证据", "_last_run_metrics.json"), "w",
                            encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
