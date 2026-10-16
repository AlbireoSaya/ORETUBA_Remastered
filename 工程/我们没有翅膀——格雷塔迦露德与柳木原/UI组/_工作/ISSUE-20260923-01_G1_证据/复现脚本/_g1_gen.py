# -*- coding: utf-8 -*-
r"""G1 · 快捷条 12 圆图标 · 生图（图生图 /images/edits，返回真 alpha PNG）

**已探明的接口事实**（见 API能力探测.txt）：
  - `/v1/images/edits` **可用**（POST 200），`image` 字段传脚手架 PNG（multipart）。
  - `response_format=b64_json` + `output_format=png` ⇒ **返回 RGBA PNG，真 alpha**（实测 alpha==0 占 95.7%）。
  - **`background:"transparent"` 传给 edits 会让连接直接断（RemoteDisconnected）** —— edits 路径禁传该参数。
  - `gpt-image-2.5-sunburst` 走 edits 返回 **RGB（无 alpha）** ⇒ 本任务只用 `gpt-image-2.5-1k`。

产物：_工作\ISSUE-20260923-01_G1_证据\原始大图\sheet_<state>_v<n>.png
"""
import base64, io, json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image

CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
EV = (os.path.dirname(HERE) if os.path.basename(HERE) == "复现脚本"
      else os.path.join(HERE, "ISSUE-20260923-01_G1_证据"))   # 本脚本可原位跑，也可在 证据\复现脚本\ 里跑
RAW = os.path.join(EV, "原始大图")
os.makedirs(RAW, exist_ok=True)
SCAFFOLD = os.path.join(EV, "脚手架_grid_4x3.png")
MODEL = "gpt-image-2.5-1k"
SIZE = "1536x1024"


def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]
    raise SystemExit("no key")


GRID = ("This is a guide sheet: twelve thin grey square guide boxes arranged in a strict grid of "
        "FOUR COLUMNS by THREE ROWS. Inside every guide box there is a faint grey pencil sketch of "
        "one icon, and a small grey number is printed in the gutter OUTSIDE each box (1 to 12, "
        "reading left to right, top to bottom). "
        "Redraw EVERY guide box as one round button, keeping the exact same grid position, the same "
        "size and the same order: box 1 stays top-left, box 4 top-right of the first row, box 12 "
        "bottom-right of the last row. Never move, swap, mirror, rotate, duplicate, resize or omit "
        "any icon, and never merge two boxes into one. ")

GLYPH = ("Inside each disc, redraw exactly the pictogram shown by the grey pencil sketch in that "
         "same box, as a crisp flat line-art glyph, well centred, with the same meaning, the same "
         "shape and the same orientation as the sketch. Keep every glyph at the same visual weight "
         "and the same size within its disc, and keep a generous empty margin between the glyph and "
         "the disc rim. ")

STYLE = ("Style: a clean minimal modern UI icon set, thin uniform strokes with rounded ends, flat "
         "single-colour glyphs, no gradient inside the glyph, no bevel, no 3D, perfectly upright, "
         "one consistent family look across all twelve buttons.")

BAN = ("ABSOLUTELY NO text, NO letters, NO numbers, NO digits, NO Chinese characters, NO labels, "
       "NO watermark, NO signature. Do NOT draw the grey guide squares and do NOT draw the grey "
       "gutter numbers in the output. NO snowflake, NO ice crystal, NO frost star, NO star sparkle, "
       "NO glitter, NO sparkles, NO dots, NO particles, NO feather, NO ribbon. NO square, "
       "rectangular, rounded-rectangle, capsule, plate, panel, tile or badge shape of any kind - "
       "every button must be a PERFECT CIRCLE.")

PROMPTS = {
    "off": (
        "Transparent background with a real alpha channel. Everything outside the round buttons is "
        "fully transparent and completely empty. "
        + GRID +
        "Each round button is a soft frosted ice-glass disc that exactly fills its guide box: almost "
        "white at the top fading gently to pale ice-blue at the bottom (top #EDF4FC, bottom #E2EDFA), "
        "laced with a thin 2-3 pixel cyan-blue rim (#7CB7FD) and a very soft pale ice-blue outer glow, "
        "with a faint diagonal frosted sheen sweeping down from the top-left corner. Airy, glassy, "
        "restful, low contrast. "
        + GLYPH +
        "The glyph is drawn in deep sea-blue (#2E6BB4). " + STYLE + " " + BAN),
    "on": (
        "Transparent background with a real alpha channel. Everything outside the round buttons is "
        "fully transparent and completely empty. "
        + GRID +
        "Each round button is a BRIGHT GLOWING frosted ice-glass disc that exactly fills its guide "
        "box: a luminous near-white core (#F4FAFF) falling to a clear bright ice-blue toward the "
        "bottom (#BEDDFB), ringed by a thicker, clearly visible saturated cyan-blue rim (#71AAF3), "
        "and surrounded by a strong bright pale-cyan outer glow halo that spills well beyond the disc "
        "edge; a bright diagonal frosted sheen sweeps across the top-left of the disc. This is the "
        "ILLUMINATED HOVER state: obviously brighter, bluer and more saturated than a resting button. "
        + GLYPH +
        "The glyph is drawn in deep bright sea-blue (#2E6BB4) with a faint pale halo around the "
        "strokes so it still reads clearly on the bright disc. " + STYLE + " " + BAN),
}


def post_edit(image_bytes, prompt, model=MODEL, size=SIZE, timeout=480):
    boundary = "----G1Gen"
    buf = io.BytesIO()
    fields = {"model": model, "prompt": prompt, "size": size, "n": 1,
              "response_format": "b64_json", "output_format": "png"}
    for k, v in fields.items():
        buf.write(("--%s\r\n" % boundary).encode())
        buf.write(('Content-Disposition: form-data; name="%s"\r\n\r\n' % k).encode())
        buf.write(str(v).encode("utf-8") + b"\r\n")
    buf.write(("--%s\r\n" % boundary).encode())
    buf.write(b'Content-Disposition: form-data; name="image"; filename="scaffold.png"\r\n')
    buf.write(b"Content-Type: image/png\r\n\r\n")
    buf.write(image_bytes + b"\r\n")
    buf.write(("--%s--\r\n" % boundary).encode())
    req = urllib.request.Request(BASE + "/images/edits", data=buf.getvalue(), headers={
        "Authorization": "Bearer " + key(),
        "Content-Type": "multipart/form-data; boundary=" + boundary,
        "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as e:
        return {"__err": e.code, "body": e.read().decode("utf-8", "replace")[:600]}, time.time() - t0
    except Exception as e:
        return {"__err": repr(e)}, time.time() - t0


def fetch(resp):
    it = resp["data"][0]
    if it.get("b64_json"):
        return base64.b64decode(it["b64_json"])
    with urllib.request.urlopen(urllib.request.Request(it["url"], headers={"User-Agent": UA}),
                               timeout=300) as r:
        return r.read()


def run(state, ver):
    name = "sheet_%s_v%d" % (state, ver)
    resp, el = post_edit(open(SCAFFOLD, "rb").read(), PROMPTS[state])
    if "__err" in resp:
        return "%-16s FAIL %5.1fs  %s" % (name, el, str(resp)[:220])
    try:
        b = fetch(resp)
    except Exception as e:
        return "%-16s FAIL fetch %s" % (name, e)
    p = os.path.join(RAW, name + ".png")
    open(p, "wb").write(b)
    im = Image.open(p)
    im.load()
    msg = "%-16s OK   %5.1fs  %s %s %s  %.0f KB" % (name, el, im.size, im.format, im.mode, len(b) / 1024.0)
    if im.mode in ("RGBA", "LA"):
        import numpy as np
        a = np.array(im.convert("RGBA"))[..., 3]
        msg += "  alpha=0 占 %.1f%%" % ((a == 0).mean() * 100)
    else:
        msg += "  **无 alpha**"
    return msg


def dump_prompts():
    """把**实际发出的 prompt 原文**（非手抄）落盘到证据目录。"""
    out = ["# G1 · 快捷条 12 圆图标 · 生图提示词原文（从源码直出，非手抄）", "",
           "## 调用参数", "", "```http",
           "POST https://api.lyaiapp.com/v1/images/edits      (multipart/form-data)",
           "Authorization: Bearer <E:\\ZCode Workspace\\.zcode\\v2\\provider_config.json → new-provider-2 → config.access.apiKey>",
           "User-Agent: " + UA, "```", "",
           "表单字段：`model=%s` / `size=%s` / `n=1` / `response_format=b64_json` /" % (MODEL, SIZE),
           "`output_format=png` / `image=脚手架_grid_4x3.png`（**图生图输入基底**）", "",
           "★ **禁传 `background:\"transparent\"`**：edits 路径带该参数会直接 RemoteDisconnected；",
           "  真 alpha 靠 `output_format=png` + `response_format=b64_json` + prompt 里**前置**的指令式透明要求。",
           "★ **无 seed 参数**（该接口未暴露 seed）。",
           "★ 脚手架 = 程序画的 4 列 × 3 行方框网格，每格内嵌该格目标图标的**淡灰铅笔稿**（最强位置+语义约束）。", "",
           "## 网格骨架段 GRID（两态共用，逐字）", "", "```text", GRID.strip(), "```", "",
           "## 圆底 / 描边段（逐字）", ""]
    for k in ("off", "on"):
        out += ["### 态 = `%s`" % k, "", "```text", PROMPTS[k].strip(), "```", ""]
    out += ["## 固定风格段 STYLE（逐字）", "", "```text", STYLE, "```", "",
            "## 禁用段 BAN（逐字）", "", "```text", BAN, "```", "",
            "## 字数", "",
            "- GRID %d 字 / STYLE %d 字 / BAN %d 字" % (len(GRID), len(STYLE), len(BAN)),
            "- PROMPTS[off] 全长 **%d 字**；PROMPTS[on] 全长 **%d 字**" % (len(PROMPTS["off"]), len(PROMPTS["on"])),
            "- 本批张数：常态 2 张（v1/v2）+ 悬停 2 张（v1 请求断连失败 / v2 成功）= 实际生成 3 张可用" + "",
            ""]
    p = os.path.join(EV, "生图提示词_原文.md")
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("→ %s" % p)


if __name__ == "__main__":
    if sys.argv[1:2] == ["dump"]:
        dump_prompts()
        raise SystemExit(0)
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(s, v) for s in ("off", "on") for v in (1, 2)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for m in ex.map(lambda a: run(*a), jobs):
            print(m, flush=True)
