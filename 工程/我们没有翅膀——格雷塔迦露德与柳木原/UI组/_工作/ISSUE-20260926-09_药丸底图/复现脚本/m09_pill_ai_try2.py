# -*- coding: utf-8 -*-
r"""ISSUE-20260926-09 · 药丸底图 生图 v2（渐变方向修正 + 条身纵向对齐后贴回原图 alpha）
v1 的错误：prompt 把渐变方向写成「顶部略暗、向底渐亮」，而原图是「底更暗」⇒ 方向翻转。
v2：prompt 改为与原图一致；并把 AI 画出的条（比原图高 6px）按「实心区中心」对齐回原图条位。
"""
import base64, io, json, os, statistics, time, urllib.error, urllib.request, uuid
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageFont, ImageStat

BASE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
UI   = os.path.join(BASE, "krkr", "assets", "ui")
EV   = os.path.join(BASE, "_工作", "ISSUE-20260926-09_药丸底图", "取证")
CFG  = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
API  = "https://api.lyaiapp.com/v1"
UA   = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SRC  = os.path.join(UI, "x_ui_psv_pill_c2_05.png")
S    = 1024

PROMPT = ("Edit this visual-novel system-UI image. It shows one horizontal option-row plate (a long "
 "bar with two pointed ends) on a plain white background. Inside the bar there are FAINT LEFTOVER "
 "MARKS and patches left over from erased text (small smudges, pale rectangles and ghost strokes). "
 "Task: remove ALL those leftovers and rebuild the bar's interior as a perfectly clean, smooth, "
 "uniform VERTICAL gradient that continues the untouched areas exactly. IMPORTANT — the gradient "
 "runs like this: the bar is slightly LIGHTER near its TOP edge and becomes gradually, subtly "
 "DARKER toward its BOTTOM (a gentle darkening of about 20 levels, from about 161 at the top to "
 "about 140 at the bottom, with the brightest band a few pixels below the top edge). Preserve this "
 "direction and amplitude; do not invert it and do not increase the contrast. Hard constraints: "
 "keep the bar's exact size, position, shape, its two pointed ends and its thin edge lines "
 "completely unchanged and pixel-aligned; do not move, redraw, rescale or rotate anything; do not "
 "add any text, symbol, icon, noise, grain or new element; leave the white background pure white.")

def key():
    d = json.load(io.open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        c = r.get("config", {})
        if "lyaiapp" in (c.get("api") or {}).get("baseUrl", ""):
            return (c.get("access") or {}).get("apiKey")
    raise SystemExit("no lyai key")

def edits(p, prompt):
    b = uuid.uuid4().hex; parts = []
    def f(n, v): parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (b, n, v)).encode("utf-8"))
    f("model", "gpt-image-2.5-sunburst"); f("prompt", prompt); f("response_format", "b64_json"); f("n", "1"); f("size", "auto")
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\nContent-Type: image/png\r\n\r\n" % (b, os.path.basename(p))).encode("utf-8"))
    parts.append(open(p, "rb").read()); parts.append(("\r\n--%s--\r\n" % b).encode("utf-8"))
    req = urllib.request.Request(API + "/images/edits", data=b"".join(parts), method="POST",
        headers={"Authorization": "Bearer " + key(), "Content-Type": "multipart/form-data; boundary=" + b,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time() - t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:300], time.time() - t0)
    except Exception as e:
        return ("err", repr(e)[:300], time.time() - t0)

def own_extent(im, x0=150, x1=470):
    px = im.load(); rows = []
    for y in range(im.height):
        v = [sum(px[x, y][:3]) / 3 for x in range(x0, x1)]
        rows.append(sum(v) / len(v))
    solid = [y for y, l in enumerate(rows) if l < 235]
    return solid[0], solid[-1]

def main():
    src = Image.open(SRC).convert("RGBA"); W, H = src.size
    sq = os.path.join(EV, "_sq.png")
    st, resp, dt = None, None, 0
    for a in range(3):
        st, resp, dt = edits(sq, PROMPT); print("attempt %d -> %s (%.1fs)" % (a + 1, st, dt))
        if st == "ok": break
        time.sleep(6 * (a + 1))
    if st != "ok": print("API 失败：", resp); return
    raw = base64.b64decode(resp["data"][0]["b64_json"])
    open(os.path.join(EV, "_ai2_raw.png"), "wb").write(raw)
    ai = Image.open(io.BytesIO(raw)).convert("RGB")
    sx, sy = ai.width / float(S), ai.height / float(S)
    flat = Image.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)), src).convert("RGB")
    ox, oy = (S - W) // 2, (S - H) // 2
    crop = ai.crop((int(ox * sx), int(oy * sy), int((ox + W) * sx), int((oy + H) * sy))).resize((W, H), Image.LANCZOS)
    crop.save(os.path.join(EV, "_ai2_crop.png"))
    # 纵向对齐：AI 自绘条的实心区中心 → 原图 alpha 实心区中心
    a0, a1 = own_extent(crop); o0, o1 = own_extent(src)
    dy = int(round(((o0 + o1) / 2.0) - ((a0 + a1) / 2.0)))
    print("AI 条实心区 y%d..%d（中心 %.1f）  原图 y%d..%d（中心 %.1f） ⇒ 对齐位移 dy=%+d" % (a0, a1, (a0+a1)/2., o0, o1, (o0+o1)/2., dy))
    aligned = Image.new("RGB", (W, H), (255, 255, 255)); aligned.paste(crop, (0, dy))
    fit = aligned.convert("RGBA"); fit.putalpha(src.getchannel("A"))
    fit.save(os.path.join(EV, "_ai2_fit.png"))
    # 指标
    def vprof(im, x=280):
        px = im.load(); return [(y, sum(px[x, y][:3]) // 3) for y in range(H)]
    o = vprof(src); n = vprof(fit)
    print("原图 实心区 顶/底 亮度: %d / %d    修正版: %d / %d" % (o[13][1], o[58][1], n[13][1], n[58][1]))
    d = ImageChops.difference(src.convert("RGB"), fit.convert("RGB")); s = ImageStat.Stat(d)
    print("修正版 vs 原图 mean|Δ| = %.2f" % (sum(s.mean) / 3))
    # 三态对照（全条 1:1 + 中段 ×3）
    a1fit = Image.open(os.path.join(EV, "_ai_fit.png")).convert("RGBA")
    try: F = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 19)
    except Exception: F = ImageFont.load_default()
    h3 = (H + 30) * 4 + 40
    sheet = Image.new("RGB", (W * 2 + 60, h3), (26, 26, 30)); dd = ImageDraw.Draw(sheet); y = 10
    for tag, im in [("① 输入 c2_05", src), ("② 生图 v1（方向被写反，你已看过）", a1fit),
                    ("③ 生图 v2（方向修正 + 条身对齐）", fit)]:
        dd.text((20, y), tag, font=F, fill=(255, 255, 255)); y += 28
        sheet.paste(im.convert("RGB"), (20, y)); y += H + 10
    y = 10
    for tag, im in [("② v1 中段×3", a1fit), ("③ v2 中段×3", fit)]:
        sheet.paste(im.convert("RGB").crop((40, 8, 360, 68)).resize((960, 180), Image.NEAREST), (W + 40, y + 28))
        dd.text((W + 40, y), tag, font=F, fill=(150, 220, 255)); y += 200
    sheet.save(os.path.join(EV, "对照_v4_v1vs修正.png"))
    print("对照图:", os.path.join(EV, "对照_v4_v1vs修正.png"))

main()
