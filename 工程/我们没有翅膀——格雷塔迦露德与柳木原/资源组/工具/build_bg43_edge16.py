# -*- coding: utf-8 -*-
r"""
build_bg43_edge16.py —— 4:3 → 16:9 补边构建器（ISSUE-20261002-07）

两条路线（用户 2026-10-02 裁定；混合路线经编程组 2026-10-02 回执三确认）：
  A    补左右      ：原内容 1:1 居中，左右 AI 生成
                     → 1600×1200 件输出 2133×1200（左 266 / 右 267）
  mix  混合 1920×1080：原内容 1:1 居中但上下各裁 60px，左右各补 160px AI 生成
                     → 输出恰好 1920×1080（仅适用宽 ≤1920 的件）

口径（与任务书 §二 及编程组新验收②一致）：
  * 内容区一律 1:1：落盘前逐像素断言 = 输入（含 offset 区域）；不重采样。
  * 输出 JPG quality=92、subsampling=0、原名原扩展名（探针实测内容区 PSNR≈59dB）。
  * 生成方式：LaMa（lama-manga-dynamic.onnx，ONNX），掩码外扩 PAD=64 防边界糊化，
    推理张量向上取到 8 的倍数后裁回画布。
  * 引擎：默认 onnxruntime-directml，初始化/推理失败自动回落 CPU。

用法：
    set OUTPAINT_DML=1
    python build_bg43_edge16.py --sample bg82e.jpg            # 样张两版 → 交付_16比9\_样张\{A,混合}\
    python build_bg43_edge16.py --names bg01a.jpg --route A   # 单件单路线（批量用）
"""
import sys, os, time, argparse, csv, io

WS = r"E:\ZCode Workspace\Galgame"
PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
SRC_DIR = os.path.join(PROJ, "编程组", "移交资源组_画幅补边", "输入素材", "背景4比3")
LIST_TSV = os.path.join(PROJ, "编程组", "移交资源组_画幅补边", "清单.tsv")
OUT_ROOT = os.path.join(PROJ, "资源组", "美术统一_交付_16比9")
EVID_DIR = os.path.join(WS, "子代理工作区", "ISSUE-20261002-07", "样张证据")
MODEL = os.path.join(WS, "工具", "outpaint", "models", "lama-manga-dynamic.onnx")

sys.path.insert(0, os.path.join(WS, "工具", "outpaint", "pylibs"))
if os.environ.get("OUTPAINT_DML", "1") == "1":
    # 必须放最前面：两个 onnxruntime 同名，顺序错了会静默用错版本
    sys.path.insert(0, os.path.join(WS, "工具", "outpaint", "pylibs_dml"))

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PAD = 64
QUALITY = 92
SUBSAMP = 0

_sess = None
_sess_prov = None


def session():
    global _sess, _sess_prov
    if _sess is None:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = 6
        want_dml = os.environ.get("OUTPAINT_DML", "1") == "1"
        prov = ["DmlExecutionProvider", "CPUExecutionProvider"] if want_dml else ["CPUExecutionProvider"]
        try:
            _sess = ort.InferenceSession(MODEL, so, providers=prov)
        except Exception as e:
            sys.stderr.write("[WARN] DirectML 初始化失败，回落 CPU：%r\n" % (e,))
            _sess = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"])
        _sess_prov = _sess.get_providers()[0]
        print("[engine] providers = %s" % _sess.get_providers(), flush=True)
    return _sess


def force_cpu():
    global _sess, _sess_prov
    import onnxruntime as ort
    so = ort.SessionOptions(); so.intra_op_num_threads = 6
    _sess = ort.InferenceSession(MODEL, so, providers=["CPUExecutionProvider"])
    _sess_prov = "CPUExecutionProvider"
    print("[engine] 已切 CPU", flush=True)


# --------------------------------------------------------------- 几何
def _align8(v):
    """向下取到 8 的倍数：内容区必须与 JPEG 的 8×8 块网格对齐，
    否则再编码误差被放大——实测内容区 PSNR 42.4dB（错位）vs 探针 59dB（对齐），
    达不到编程组验收②的 ≥45 dB 线。"""
    return v // 8 * 8


def route_geom(route, w, h):
    """返回 (canvas_w, canvas_h, cut_top, cut_bottom, paste_x)。
    所有偏移取 8 的倍数（见 _align8）：A 路线左 264/右 269（总 +533 不变，仅左右分配微调）；
    混合路线上裁 56/下裁 64（总损失仍 120px，与提案「上下各 60px」的差异仅 4px）。"""
    if route == "A":
        cw = int(round(h * 16 / 9))
        return cw, h, 0, 0, _align8((cw - w) // 2)
    if route == "mix":
        if w > 1920:
            raise ValueError("混合路线需 w<=1920（本件 %d）" % w)
        cut = h - 1080
        if cut < 0:
            raise ValueError("混合路线需 h>=1080（本件 %d）" % h)
        top = _align8(cut // 2)
        return 1920, 1080, top, cut - top, _align8((1920 - w) // 2)
    raise ValueError(route)


def build_canvas(img, route):
    w, h = img.size
    cw, ch, top, bot, px = route_geom(route, w, h)
    content = img.crop((0, top, w, h - bot))
    canvas = Image.new("RGB", (cw, ch), (0, 0, 0))
    canvas.paste(content, (px, 0))
    mask = Image.new("L", (cw, ch), 255)
    mask.paste(Image.new("L", content.size, 0), (px, 0))
    return canvas, mask, {"canvas": (cw, ch), "paste_x": px, "cut_top": top,
                          "cut_bottom": bot, "content": content.size}


def pad_for_lama(img, mask, pad=PAD):
    w, h = img.size
    nw, nh = w + 2 * pad, h + 2 * pad
    nw += (8 - nw % 8) % 8
    nh += (8 - nh % 8) % 8
    c = Image.new("RGB", (nw, nh), (0, 0, 0)); c.paste(img, (pad, pad))
    m = Image.new("L", (nw, nh), 255); m.paste(mask, (pad, pad))
    return c, m


def inpaint(canvas, mask):
    c, m = pad_for_lama(canvas, mask)
    a = np.asarray(c).astype(np.float32) / 255.0
    mk = np.asarray(m).astype(np.float32) / 255.0
    mk = np.where(mk > 0.5, 1.0, 0.0).astype(np.float32)
    it = a.transpose(2, 0, 1)[None, ...].copy()
    mt = mk[None, None, ...].copy()
    t0 = time.time()
    try:
        out = session().run(None, {"image": it, "mask": mt})[0]
    except Exception as e:
        if _sess_prov == "DmlExecutionProvider":
            sys.stderr.write("[WARN] DML 推理失败，切 CPU 重试：%r\n" % (e,))
            force_cpu()
            out = session().run(None, {"image": it, "mask": mt})[0]
        else:
            raise
    dt = time.time() - t0
    res = (np.clip(out[0].transpose(1, 2, 0), 0, 1) * 255).astype(np.uint8)
    full = Image.fromarray(res)
    w, h = canvas.size
    return full.crop((PAD, PAD, PAD + w, PAD + h)), dt


def psnr_max(a, b):
    a = a.astype(np.float32); b = b.astype(np.float32)
    mse = float(((a - b) ** 2).mean())
    return (10 * np.log10(255.0 * 255.0 / max(mse, 1e-9)),
            int(np.abs(a - b).max()))


# --------------------------------------------------------------- 色调匹配
# 核心照抄 ISSUE-20260928-02 的 tonematch_pass_v2（缝处 u=0 严格不动缝邻域、
# 纯 offset 斜坡 + 亮度残差归零、内容区逐像素恒等）。
TONEMATCH_REF_SHIFT = 10
FAR = REF = 8
SMOOTH_R = 16
OFF_CLAMP = 80.0


def _box_smooth_cols(a, r):
    H = a.shape[0]
    if r <= 0:
        return a
    cs = np.cumsum(np.vstack([np.zeros((1, a.shape[1]), a.dtype), a]), axis=0)
    idx = np.arange(H)
    lo = np.clip(idx - r, 0, H); hi = np.clip(idx + r + 1, 0, H)
    return (cs[hi] - cs[lo]) / (hi - lo)[:, None]


def _smoothstep(u):
    return u * u * (3.0 - 2.0 * u)


def _luma(a):
    """支持 (H,W,3) 与 (N,3) 两种形状。"""
    if a.ndim == 2:
        return 0.299 * a[:, 0] + 0.587 * a[:, 1] + 0.114 * a[:, 2]
    return 0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]


def tonematch(rgb, xl, xr, ref_shift=TONEMATCH_REF_SHIFT):
    """扩展区色调对齐。参考带 = 内容 [xl+shift, xl+shift+8)（右缝对称）；
    缝处 u=0（缝邻域逐位不变）⇒ 不引入新台阶；只改扩展区。"""
    H, W, _ = rgb.shape
    out = rgb.copy()
    info = {}
    for side in ("L", "R"):
        if side == "L":
            ext, far = slice(0, xl), slice(0, FAR)
            ref = slice(xl + ref_shift, min(W, xl + ref_shift + REF))
            n_ext = xl
        else:
            ext, far = slice(xr, W), slice(max(0, W - FAR), W)
            ref = slice(max(0, xr - ref_shift - REF), xr - ref_shift)
            n_ext = W - xr
        if n_ext < 8 or ref.stop - ref.start < REF:
            info[side] = {"skip": True}
            continue
        ext_far = rgb[:, far, :].mean(axis=1).astype(np.float32)
        ctn_ref = rgb[:, ref, :].mean(axis=1).astype(np.float32)
        off_far = _box_smooth_cols(np.clip(ctn_ref - ext_far, -OFF_CLAMP, OFF_CLAMP), SMOOTH_R)
        t = np.arange(n_ext, dtype=np.float32)
        d = (n_ext - 1 - t) if side == "L" else t
        u = _smoothstep(np.clip(d / max(n_ext - 1, 1), 0, 1))[None, :, None]
        out[:, ext, :] = np.clip(rgb[:, ext, :] + u * off_far[:, None, :], 0, 255)
        tgt = float(_luma(rgb[:, ref, :]).mean())
        cur = float(_luma(out[:, far, :]).mean())
        resid = tgt - cur
        if abs(resid) > 1e-6:
            out[:, ext, :] = np.clip(out[:, ext, :] + u * resid, 0, 255)
        info[side] = {"off_far_mean": round(float(np.abs(off_far).mean()), 3),
                      "resid": round(resid, 3)}
    return out, info


def seam_stats(a, xl, xr):
    """自算接缝指标：缝内参考带（内容侧内移 10 列）vs 缝外远带（扩展区最外 8 列）的逐行亮度/逐通道差。
    （样张用途；正式批量将改用工程既有 quality_axes_v3 的 ramp/ramp_ch/bandmed_ch 口径。）"""
    def band(i0, i1):
        return a[:, i0:i1, :].mean(axis=1)
    res = {}
    for side, (iin, iout) in (("L", ((xl + 10, xl + 18), (0, FAR))),
                              ("R", ((xr - 18, xr - 10), (a.shape[1] - FAR, a.shape[1])))):
        bi, bo = band(*iin), band(*iout)
        d = np.abs(_luma(bi) - _luma(bo))
        dc = np.abs(bi - bo).mean(axis=1)
        res[side] = {"ramp_mean": round(float(d.mean()), 2), "ramp_max": round(float(d.max()), 2),
                     "ramp_ch_mean": round(float(dc.mean()), 2), "ramp_ch_max": round(float(dc.max()), 2)}
    return res


# --------------------------------------------------------------- 校验
def verify(out_path, src_path, route):
    """返回 (指标 dict)。内容区按偏移区域逐像素比对（编程组 2026-10-02 新口径）。"""
    src = Image.open(src_path).convert("RGB")
    w, h = src.size
    cw, ch, top, bot, px = route_geom(route, w, h)
    out = Image.open(out_path).convert("RGB")
    if out.size != (cw, ch):
        raise AssertionError("尺寸 %s != %s" % (out.size, (cw, ch)))
    ratio = cw / ch
    if abs(ratio - 16 / 9) >= 0.002:
        raise AssertionError("宽高比偏差 %.5f" % abs(ratio - 16 / 9))
    region_out = out.crop((px, 0, px + w, ch))
    region_src = src.crop((0, top, w, h - bot))
    a = np.asarray(region_src); b = np.asarray(region_out)
    p, mx = psnr_max(a, b)
    # 编程组 2026-10-02 新验收②：PSNR >= 45 dB **或** maxdiff <= 3；两者都不满足即硬失败。
    # ★ 这条断言才是拦住「偏移未取 8 的倍数」的那一道（一审打回项-1：错位时 PSNR 42.4 dB，必须抛错而不是静默放行）。
    if p < 45.0 and mx > 3:
        raise AssertionError("内容区再编码误差超线：PSNR %.2f dB / maxdiff %d"
                             "（口径：PSNR>=45dB 或 maxdiff<=3）" % (p, mx))
    return {"out_size": "%dx%d" % (cw, ch), "ratio": round(ratio, 6),
            "content_region": "%dx%d@(%d,%d)" % (region_out.size[0], region_out.size[1], px, top),
            "content_psnr_db": round(p, 2), "content_maxdiff": mx,
            "bytes": os.path.getsize(out_path)}


def seam_fig(out_path, route, dst):
    """左右接缝 1:1 与 2× 目视条（每侧以缝为中心取 80px 窗）。"""
    im = Image.open(out_path).convert("RGB")
    w, h = im.size
    src_w, src_h = Image.open(SRC_DIR and os.path.join(SRC_DIR, os.path.basename(out_path))).size
    cw, ch, top, bot, px = route_geom(route, src_w, src_h)
    xl, xr = px, px + src_w
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
    except Exception:
        font = ImageFont.load_default()
    panels = []
    for xc, lab in ((xl, "左缝 x=%d" % xl), (xr, "右缝 x=%d" % xr)):
        x0 = max(0, xc - 40)
        crop = im.crop((x0, 0, min(w, x0 + 80), h))
        z = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
        panels.append((z, lab))
    bar = 30
    W = sum(p[0].width for p in panels) + 30
    H = max(p[0].height for p in panels) + bar
    fig = Image.new("RGB", (W, H), (16, 16, 20))
    d = ImageDraw.Draw(fig)
    x = 0
    for z, lab in panels:
        fig.paste(z, (x, bar))
        d.line([(x, bar), (x, bar + z.height)], fill=(255, 60, 60), width=2)
        d.text((x + 4, 5), "%s | %dx%d %s" % (os.path.basename(out_path), w, h, lab),
               fill=(255, 220, 90), font=font)
        x += z.width + 30
    fig.save(dst)
    return dst


# --------------------------------------------------------------- 主流程
def load_names():
    rows = {}
    with open(LIST_TSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows[r["文件名"].strip()] = r
    return rows


def run_one(name, route, out_dir, do_fig=True, metrics=None, tm_on=True):
    src = os.path.join(SRC_DIR, name)
    if not os.path.isfile(src):
        raise SystemExit("副本不存在: %s" % src)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, name)
    img = Image.open(src)
    if img.mode != "RGB":
        img = img.convert("RGB")
    canvas, mask, geo = build_canvas(img, route)
    xl, xr = geo["paste_x"], geo["paste_x"] + geo["content"][0]
    # 落盘前断言：内容区逐像素 == 输入（1:1 硬不变量）
    region = canvas.crop((xl, 0, xr, geo["canvas"][1]))
    src_region = img.crop((0, geo["cut_top"], img.size[0], img.size[1] - geo["cut_bottom"]))
    if np.abs(np.asarray(region, np.int16) - np.asarray(src_region, np.int16)).max() != 0:
        raise AssertionError("内容区落盘前逐像素不一致")
    t0 = time.time()
    out, dt = inpaint(canvas, mask)
    tm_stats = None
    if tm_on:
        a_before = np.asarray(out).astype(np.float32)
        tm_stats = {"before": seam_stats(a_before, xl, xr)}
        a_after, tm_info = tonematch(a_before, xl, xr)
        if np.abs(a_after[:, xl:xr, :] - a_before[:, xl:xr, :]).max() != 0:
            raise AssertionError("色调匹配改动了内容区")
        out = Image.fromarray(np.clip(np.rint(a_after), 0, 255).astype(np.uint8), "RGB")
        tm_stats["after"] = seam_stats(np.asarray(out).astype(np.float32), xl, xr)
        tm_stats["info"] = tm_info
    out.save(dst, "JPEG", quality=QUALITY, subsampling=SUBSAMP, optimize=True)
    total = time.time() - t0
    met = verify(dst, src, route)
    met.update({"route": route, "infer_s": round(dt, 2), "total_s": round(total, 2),
                "engine": _sess_prov, "canvas": "%dx%d" % geo["canvas"],
                "paste_x": geo["paste_x"], "cut_top": geo["cut_top"], "cut_bottom": geo["cut_bottom"],
                "content_pre_encode_exact": True, "tonematch": tm_stats})
    if tm_stats:
        for side in ("L", "R"):
            b, a = tm_stats["before"][side], tm_stats["after"][side]
            print("     [TM] %s: ramp_mean %.2f→%.2f  ramp_ch_mean %.2f→%.2f"
                  % (side, b["ramp_mean"], a["ramp_mean"], b["ramp_ch_mean"], a["ramp_ch_mean"]),
                  flush=True)
    print("[OK] %s %-4s -> %s  %s  content PSNR=%.2f dB maxdiff=%d  infer=%.1fs"
          % (name, route, dst, met["out_size"], met["content_psnr_db"], met["content_maxdiff"], dt),
          flush=True)
    if do_fig:
        os.makedirs(EVID_DIR, exist_ok=True)
        fig = os.path.join(EVID_DIR, "%s_接缝_%s.png" % (os.path.splitext(name)[0], route))
        seam_fig(dst, route, fig)
        met["seam_fig"] = fig
    if metrics is not None:
        metrics.append(met)
    return met


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default=None, help="样张件名（如 bg82e.jpg）：同出 A 与 mix 两版 → _样张\\")
    ap.add_argument("--names", default=None, help="逗号分隔文件名（批量）")
    ap.add_argument("--route", default="A", choices=["A", "mix", "both"])
    ap.add_argument("--out-root", default=OUT_ROOT)
    ap.add_argument("--no-fig", action="store_true")
    ap.add_argument("--no-tonematch", action="store_true",
                    help="关掉扩展区色调对齐（默认开，移植自 ISSUE-20260928-02 tonematch_pass_v2）")
    args = ap.parse_args()
    tm_on = not args.no_tonematch

    metrics = []
    if args.sample:
        name = args.sample.strip()
        for route, sub in (("A", "A"), ("mix", "混合")):
            run_one(name, route, os.path.join(args.out_root, "_样张", sub), not args.no_fig, metrics, tm_on)
    else:
        if not args.names:
            raise SystemExit("需要 --sample 或 --names")
        routes = ["A", "mix"] if args.route == "both" else [args.route]
        for name in [n.strip() for n in args.names.split(",") if n.strip()]:
            for route in routes:
                run_one(name, route, os.path.join(args.out_root, "CG背景"), not args.no_fig, metrics, tm_on)

    print("\n== 汇总 ==")
    for m in metrics:
        print("  %-14s %-4s %s  PSNR=%.2f maxdiff=%d  bytes=%d  infer=%.1fs (%s)"
              % (os.path.basename(m.get("seam_fig", "")), m["route"], m["out_size"],
                 m["content_psnr_db"], m["content_maxdiff"], m["bytes"], m["infer_s"], m["engine"]))


if __name__ == "__main__":
    main()
