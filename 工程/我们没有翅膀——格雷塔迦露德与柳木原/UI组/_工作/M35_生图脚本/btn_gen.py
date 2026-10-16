# -*- coding: utf-8 -*-
r"""系统页按钮文字 · 正式批次生成（M35 续）

背景（承接 `test_sunburst.py` 已跑通的方案）：
  一张竖版图 **7 行 × 一行一词 × 每字一个方框**，模型 = `gpt-image-2.5-sunburst`，
  canvas = 1024×1536。实测方框脚手架把字高极差从 13%–45% 压到 **0 px**。

用户 2026-09-22 追加两条：
  ①「羽毛单独生成一层，放在字体下方」→ 正文字层**不再烘焙羽毛**，羽毛另出独立素材层；
  ②「正式生成所有按钮字体素材，生成两批」→ 本次出 **两批** 正文层（光晕档位不同）。

产物：
  out_btn\BATCH2_7rows.png   光晕「强」档（与独立羽毛层配合的主方案）
  out_btn\BATCH3_7rows.png   光晕「中」档 + 少量羽毛烘入（自包含备选）
  out_btn\FEATHER_sheet.png  独立羽毛层（白色羽毛散落、真 alpha、无字）
"""
import base64, json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT = os.path.join(HERE, "out_btn")
os.makedirs(OUT, exist_ok=True)

WORDS = [("开始游戏", 4), ("继续游戏", 4), ("读取存档", 4), ("流程图", 3),
         ("设置", 2), ("画廊", 2), ("离开游戏", 4)]

GLYPH_STYLE = ("Each character is drawn in a clean bold Chinese gothic style with frosted "
               "ice-glass lettering, filled by a pale ice-blue to near-white vertical gradient "
               "(#DCEBFB at the bottom to #FFFFFF at the top) and outlined by a thin cyan-blue "
               "edge (#7CB7FD).")

TIERS = {
    "2": ("光晕「强」", "a clear bright white glow halo"),
    "3": ("光晕「中」+轻羽毛", "a soft white glow halo"),
}


def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]
    raise SystemExit("no key")


def call(model, prompt, size="1024x1536"):
    body = json.dumps({"model": model, "prompt": prompt, "size": size, "n": 1,
                       "background": "transparent", "output_format": "png",
                       "response_format": "b64_json"}).encode("utf-8")
    req = urllib.request.Request(BASE + "/images/generations", data=body,
                                 headers={"Authorization": "Bearer " + key(),
                                          "Content-Type": "application/json",
                                          "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=420) as r:
            return json.loads(r.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as e:
        return {"__err": e.code, "body": e.read().decode("utf-8", "replace")[:400]}, time.time() - t0
    except Exception as e:
        return {"__err": repr(e)}, time.time() - t0


def save(resp, name):
    if "__err" in resp:
        return None, str(resp)[:300]
    it = resp["data"][0]
    raw = base64.b64decode(it["b64_json"]) if it.get("b64_json") else None
    if raw is None and it.get("url"):
        with urllib.request.urlopen(urllib.request.Request(
                it["url"], headers={"User-Agent": UA}), timeout=240) as r:
            raw = r.read()
    if raw is None:
        return None, "no data"
    p = os.path.join(OUT, name + ".png")
    open(p, "wb").write(raw)
    return p, "saved"


# ─────────────────────────── 正文层（7 行方框脚手架） ───────────────────────────

def sheet_prompt(glow, feathers):
    rows = []
    for i, (zh, n) in enumerate(WORDS, 1):
        assign = ", ".join("box %d = %s" % (j + 1, c) for j, c in enumerate(zh))
        rows.append("Row %d has %d boxes reading %s (%s)" % (i, n, zh, assign))
    layout = ("The seven rows are stacked top to bottom with a clear empty gap between adjacent "
              "rows, and every row starts at the same left edge so that box 1 of every row is "
              "vertically aligned in one column.")
    return (
        "A PNG image showing SEVEN horizontal rows of faint thin guide boxes. "
        + "; ".join(rows) + ". "
        + layout + " "
        "Each box is a square drawn as a thin cyan-blue outline about 1/48 of the box width, and "
        "the boxes inside one row are laid out left to right with a small empty gap between "
        "adjacent box edges (the gap is about 1/12 of one box width). "
        "Inside EACH box, centered and FILLING that box edge to edge with no padding, write "
        "exactly the one Chinese character assigned to it. " + GLYPH_STYLE + " All characters are "
        "the same size, the same stroke weight and the same optical height, sitting on the same "
        "baseline within their row. Every character must be spelled correctly and completely. "
        "Behind and around the characters in the whole image: " + glow + ". " + feathers +
        "Transparent background with a real alpha channel; the ONLY visible things are the thin "
        "box outlines and the characters inside them plus the glow and feathers just described. "
        "Do NOT draw any button, badge, chip, pill, tag, label, card, plate, banner, panel or "
        "filled rectangle behind the characters.")
    

FEATHER_NONE = ("No feathers at all: do not draw any feather anywhere in the image. ")


def feather_prompt():
    return (
        "A PNG image of many separate small white feathers drifting and scattered across a "
        "completely empty transparent background, seen as if slowly falling. "
        "About 24 individual feathers of clearly different sizes, each feather is a soft fluffy "
        "white feather with a visible central quill and fine airy barb lines, drawn in a "
        "delicate semi-transparent white, some slightly angled, some almost horizontal, none of "
        "them touching each other, spread out with generous empty space between them so that "
        "every feather is isolated and can be cut out individually. "
        "The feathers are pure white to very pale ice-blue (#FFFFFF to #EAF3FD) with soft edges. "
        "Transparent background with a real alpha channel: every pixel that is not part of a "
        "feather is fully transparent. "
        "ABSOLUTELY NO text, no letters, no numbers, no Chinese characters, no symbols, no "
        "watermark, no frame, no border, no background colour, no gradient wash, no snow, no "
        "snowflakes, no stars, no sparkles, no glitter, no dots.")


def gen_sheet(name, glow, feathers):
    r, el = call("gpt-image-2.5-sunburst", sheet_prompt(glow, feathers))
    p, msg = save(r, name)
    if p is None:
        return None, "%.0fs HTTP/%s" % (el, msg)
    im = Image.open(p).convert("RGBA")
    return p, "%.0fs  %d×%d  %s" % (el, im.size[0], im.size[1], audit(im))


def audit(im):
    """结构自检：alpha 行投影应切出 7 段；每段列投影段数应等于词长。"""
    import numpy as np
    al = np.array(im)[..., 3]
    rows = (al > 40).sum(axis=1)
    nz = np.nonzero(rows)[0]
    if len(nz) == 0:
        return "空图！"
    bands = []
    s = prev = nz[0]
    for v in nz[1:]:
        if v - prev > 3:
            bands.append((int(s), int(prev)))
            s = v
        prev = v
    bands.append((int(s), int(prev)))
    if len(bands) != 7:
        return "行数=%d（期望 7）✗" % len(bands)
    detail = []
    ok = True
    for (y0, y1), (zh, n) in zip(bands, WORDS):
        cols = (al[y0:y1 + 1] > 40).sum(axis=0)
        cnz = np.nonzero(cols)[0]
        seg = 1
        p2 = cnz[0]
        for v in cnz[1:]:
            if v - p2 > 3:
                seg += 1
            p2 = v
        detail.append("%s=%d" % (zh, seg))
        if seg != n:
            ok = False
    return "行 7 ✓ 逐行格数 %s %s" % (" ".join(detail), "✓" if ok else "✗")


if __name__ == "__main__":
    which = sys.argv[1:] or ["2", "3", "feather"]
    log = open(os.path.join(HERE, "btn_gen.log"), "a", encoding="utf-8")

    def w(m):
        print(m, flush=True)
        log.write(m + "\n")

    for t in which:
        if t == "feather":
            w("\n===== 独立羽毛层 =====")
            r, el = call("gpt-image-2.5-sunburst", feather_prompt(), "1024x1024")
            p, msg = save(r, "FEATHER_sheet")
            if p is None:
                w("  FAIL %.0fs %s" % (el, msg))
            else:
                im = Image.open(p).convert("RGBA")
                a = im.split()[-1]
                bb = a.point(lambda v: 255 if v > 40 else 0).getbbox()
                w("  OK %s  %.0fs  %d×%d  bbox=%s" % (p, el, im.size[0], im.size[1], bb))
            continue
        glow = TIERS[t][1]
        w("\n===== BATCH%s（%s）=====" % (t, TIERS[t][0]))
        p, msg = gen_sheet("BATCH%s_7rows" % t, glow,
                           "a light scattering of small faint white feathers. " if t == "3" else FEATHER_NONE)
        w("  OK %s  %s" % (p, msg) if p else "  FAIL %s" % msg)
