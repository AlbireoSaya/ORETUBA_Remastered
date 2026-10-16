# -*- coding: utf-8 -*-
r"""ISSUE-20260926-09 · 药丸底图：同一行输入 → 生图去字 vs 程序化重建 对照
输入 = 最脏的一行 krkr\assets\ui\x_ui_psv_pill_c2_05.png（560x72）
生图：白底垫方 1024² → /v1/images/edits（gpt-image-2.5-sunburst）→ 裁回原位
程序化：取同一行，中段按「每 y 横向中位色」重建
输出：_工作\ISSUE-20260926-09_药丸底图\取证\{_in,_ai_raw,_ai_fit,_proc}.png + 对照图
"""
import base64, io, json, os, statistics, time, urllib.error, urllib.request, uuid
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageStat

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
UI   = os.path.join(BASE, "krkr", "assets", "ui")
WORK = os.path.join(BASE, "_工作", "ISSUE-20260926-09_药丸底图")
EV   = os.path.join(WORK, "取证")
CFG  = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
API  = "https://api.lyaiapp.com/v1"
UA   = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SRC  = os.path.join(UI, "x_ui_psv_pill_c2_05.png")   # 最脏的一行
S    = 1024

PROMPT = ("Edit this visual-novel system-UI image. It shows one horizontal option-row plate (a long "
 "bar with two pointed ends) on a plain white background. Inside the bar there are FAINT LEFTOVER "
 "MARKS and patches left over from erased text (small smudges, pale rectangles and ghost strokes). "
 "Task: remove ALL of those leftovers and rebuild the bar's interior as a perfectly clean, smooth, "
 "uniform VERTICAL gradient (the bar is slightly darker at the top edge, lighter toward the bottom), "
 "exactly continuing the untouched areas around them. Hard constraints: keep the bar's exact size, "
 "position, shape, its two pointed ends and its thin top/bottom edge lines completely unchanged and "
 "pixel-aligned; do not move, redraw, rescale or rotate anything; do not add any text, symbol, "
 "icon, noise, grain or new element; leave the white background pure white and unchanged.")

def key():
    d = json.load(io.open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        c = r.get("config", {})
        base = (c.get("api") or {}).get("baseUrl", "")
        if "lyaiapp" in base:
            return ((c.get("access") or {}).get("apiKey"))
    raise SystemExit("no lyai key")

def edits(png_path, prompt):
    b = uuid.uuid4().hex; parts = []
    def field(n, v):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, n, v)).encode("utf-8"))
    field("model", "gpt-image-2.5-sunburst"); field("prompt", prompt)
    field("response_format", "b64_json"); field("n", "1"); field("size", "auto")
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % (b, os.path.basename(png_path))).encode("utf-8"))
    parts.append(open(png_path, "rb").read())
    parts.append(("\r\n--%s--\r\n" % b).encode("utf-8"))
    req = urllib.request.Request(API + "/images/edits", data=b"".join(parts), method="POST",
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "multipart/form-data; boundary=" + b,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time() - t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:300], time.time() - t0)
    except Exception as e:
        return ("err", repr(e)[:300], time.time() - t0)

def proc_rebuild(im, X0=120, X1=470, T=3):
    """程序化：中段按每 y 的横向中位色重建（几何/alpha 不动）"""
    out = im.copy(); px = out.load(); W, H = im.size
    P = []
    for y in range(H):
        vals = [px[x, y][:3] for x in range(X0, X1) if px[x, y][3] >= 250]
        P.append(tuple(int(statistics.median([v[k] for v in vals])) for k in range(3)) if vals else (0, 0, 0))
    for y in range(H):
        for x in range(X0, X1):
            c = px[x, y]
            if c[3] >= 250 and sum(abs(c[k] - P[y][k]) for k in range(3)) > T:
                px[x, y] = (P[y][0], P[y][1], P[y][2], c[3])
    return out

def resid(im, box=(150, 5, 470, 68)):
    rgb = im.convert("RGB"); sm = rgb.filter(ImageFilter.MedianFilter(9))
    d = ImageChops.difference(rgb, sm).convert("L").crop(box)
    h = d.histogram(); n = sum(h)
    return sum(h[16:]) * 100.0 / n, sum(h[32:]) * 100.0 / n

def main():
    src = Image.open(SRC).convert("RGBA"); W, H = src.size
    src.save(os.path.join(EV, "_in.png"))
    # 白底垫方 1024²
    flat = Image.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), src).convert("RGB")
    ox, oy = (S - W) // 2, (S - H) // 2
    canvas = Image.new("RGB", (S, S), (255, 255, 255)); canvas.paste(flat, (ox, oy))
    sq = os.path.join(EV, "_sq.png"); canvas.save(sq)
    st, resp, dt = None, None, 0
    for a in range(3):
        st, resp, dt = edits(sq, PROMPT)
        print("attempt %d -> %s (%.1fs)" % (a + 1, st, dt))
        if st == "ok": break
        time.sleep(6 * (a + 1))
    if st != "ok":
        print("API 失败：", resp); return
    raw = base64.b64decode(resp["data"][0]["b64_json"])
    open(os.path.join(EV, "_ai_raw.png"), "wb").write(raw)
    ai = Image.open(io.BytesIO(raw)).convert("RGB")
    sx, sy = ai.width / float(S), ai.height / float(S)
    box = (int(ox * sx), int(oy * sy), int((ox + W) * sx), int((oy + H) * sy))
    ai_crop = ai.crop(box).resize((W, H), Image.LANCZOS)
    ai_crop.save(os.path.join(EV, "_ai_crop.png"))
    # 混合件：纹理取 AI，alpha 取原图（AI 输出无 alpha）
    ai_fit = ai_crop.convert("RGBA"); ai_fit.putalpha(src.getchannel("A"))
    ai_fit.save(os.path.join(EV, "_ai_fit.png"))
    proc = proc_rebuild(src); proc.save(os.path.join(EV, "_proc.png"))
    # 指标
    print("残差（>16 / >32 占比）：输入 %.2f%%/%.2f%%  生图 %.2f%%/%.2f%%  程序化 %.2f%%/%.2f%%" %
          (resid(src) + resid(ai_fit) + resid(proc)))
    d_ai = ImageChops.difference(src.convert("RGB"), ai_fit.convert("RGB")); s = ImageStat.Stat(d_ai)
    print("生图 vs 原图 全条 mean|Δ| = %.2f  max|Δ| = %d" % (sum(s.mean) / 3, max(d_ai.getextrema(), key=lambda t: t[1])[1]))
    # 对照图：1:1 三条 + 中段 4× 三格
    X0, X1 = 260, 400; Y0, Y1 = 20, 60
    rows = [("① 输入（最脏的一行 c2_05）", src), ("② 生图去字（纹理取 AI、alpha 取原图）", ai_fit), ("③ 程序化重建", proc)]
    cw, ch = X1 - X0, Y1 - Y0
    try: F = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 20)
    except Exception: F = ImageFont.load_default()
    sheet = Image.new("RGB", (max(W, cw * 4) + 40, (H + 34) * 3 + 510), (26, 26, 30)); dd = ImageDraw.Draw(sheet)
    y = 10
    for tag, im in rows:
        dd.text((20, y), tag, font=F, fill=(255, 255, 255)); y += 30
        sheet.paste(im.convert("RGB"), (20, y)); y += H + 12
    dd.text((20, y), "上三行的中段 ×4 放大（同一区域，便于看残留/补块）", font=F, fill=(150, 220, 255)); y += 30
    for tag, im in rows:
        sheet.paste(im.convert("RGB").crop((X0, Y0, X1, Y1)).resize((cw * 4, ch * 4), Image.NEAREST), (20, y))
        y += ch * 4 + 14
    sheet.save(os.path.join(EV, "对照_整条与局部.png"))
    print("对照图：", os.path.join(EV, "对照_整条与局部.png"))

main()
