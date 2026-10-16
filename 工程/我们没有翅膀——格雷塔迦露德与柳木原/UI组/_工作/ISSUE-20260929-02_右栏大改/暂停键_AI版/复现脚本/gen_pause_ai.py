# -*- coding: utf-8 -*-
r"""E5 · AI 生图版暂停键 —— 候选生成（图生图 /images/edits）

落盘：UI组\_工作\ISSUE-20260929-02_右栏大改\暂停键_AI版\候选\
幂等：已存在且未加 --force 的候选跳过，不重复烧钱。
并发：默认 2（本工程实测并发 7 → 5 失败；接口冻结书写明「并发不要超过 2」）。

用法：
    python gen_pause_ai.py                # 跑全部候选（跳过已有）
    python gen_pause_ai.py --force        # 全部重跑
    python gen_pause_ai.py --only C1,C3   # 只跑指定候选

参考图准备（三种）：
    REF4X  源图 4× LANCZOS（476×476）居中贴到 1024×1024 透明画布
    REF1X  源图 1:1（119×119）居中贴到 1024×1024 透明画布
    REF8X  源图 8× LANCZOS（952×952）居中贴到 1024×1024 透明画布

★ 本工程实测坑（必读，勿重踩）：
    ① `background:"transparent"` 这个 API 参数单独给**不生效**；真 alpha 靠 prompt 里
       **前置的指令式**「Transparent background with a real alpha channel.」
    ② User-Agent 必须伪装浏览器，否则 Cloudflare 403 / error code 1010
    ③ 模型不遵守 prompt 里的左右/顺序描述 ⇒ 件名一律目视指派
"""
import base64, io, json, os, sys, time, hashlib, urllib.request, urllib.error, uuid
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

HERE = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\_工作\ISSUE-20260929-02_右栏大改\暂停键_AI版"
SRC  = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\krkr\assets\ui\x_ui_pbkick_off.png"
CFG  = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
PROVIDER = "new-provider-2"          # API key 明文在 provider_config.json 的该条目
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

CAND = os.path.join(HERE, "候选")
REFD = os.path.join(CAND, "_ref")
LOG  = os.path.join(CAND, "_http_log.jsonl")
os.makedirs(REFD, exist_ok=True)

# ─────────────────────────────────────────────────────────── key
def load_key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == PROVIDER:
            return r["config"]["access"]["apiKey"]
    raise SystemExit("provider not found: " + PROVIDER)

# ────────────────────────────────────────────────────── 参考图
def make_ref(scale, tag, clip=False):
    """源图 RGBA 等比放大 scale 倍，居中贴到 1024×1024 透明画布。
    clip=True 时先把 α<48 的羽边归零（削掉柔外发光，给模型一个「环即最外缘」的干净靶）。"""
    p = os.path.join(REFD, "ref_%s%s.png" % (tag, "_clean" if clip else ""))
    if os.path.exists(p):
        return p
    src = Image.open(SRC).convert("RGBA")
    S = 1024
    if clip:
        a = src.getchannel("A").point(lambda v: 0 if v < 48 else v)
        src.putalpha(a)
    if scale != 1.0:
        w = int(round(src.width * scale)); h = int(round(src.height * scale))
        src = src.resize((w, h), Image.LANCZOS)
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(src, ((S - src.width) // 2, (S - src.height) // 2), src)
    canvas.save(p)
    return p

# ─────────────────────────────────────────────── 提示词（前置透明指令）
# 目标：盘面（外发光 + 盘体 + 环）保持与参考图一致，只把中央 ▶ 换成两条竖直圆角条 ‖。
# 参考图实测常量（写在 prompt 里给模型算比例）：
#   圆盘外半径 54 → 环外径 108；环厚 3；盘面填充 #E7F0FD（α237）；
#   环 / 字形 #A7CBF1(字形) #929FB7(环)；外发光 #7AB0E8
#   两条合计宽 48 = 环外径 108 的 44.4%；高 54 = 直径的 50%；条宽 16 = 组宽的 1/3；间隙 16
P_STYLE = (
 "Transparent background with a real alpha channel - every pixel outside the round button's "
 "soft outer glow must be fully transparent with alpha = 0; do NOT paint a white, black, "
 "grey, coloured or checkerboard background behind the button.\n"
)
P_TASK = (
 "You are given one image: a small round pause/play button sprite from a Japanese visual novel UI. "
 "It is a perfectly circular disc: a very pale ice-blue to near-white vertical gradient fill "
 "(about #E7F0FD), a 3-pixel grey-blue ring border (about #929FB7) around the rim, and a soft "
 "cyan-blue outer glow halo (about #7AB0E8) fading out past the rim. In the middle of the disc "
 "there is a single solid light-blue triangle (a PLAY arrow, about #A7CBF1).\n"
 "TASK: change ONLY the symbol in the middle. Replace the PLAY triangle with a PAUSE symbol made "
 "of exactly TWO vertical rounded bars (a double vertical bar, like the pause icon ||). "
 "Do not touch anything else.\n"
 "KEEP COMPLETELY UNCHANGED - redraw them exactly as in the input image, same position, same size, "
 "same radius, same thickness, same colours, same soft anti-aliased edges: the circular pale-blue "
 "disc, the grey-blue ring border, and the feathered outer glow halo. The disc must stay centred "
 "in the canvas with the same margin as the input image.\n"
 "PAUSE SYMBOL GEOMETRY (proportions measured on the input image; follow them closely): the two "
 "bars are vertical, rectangular with small rounded corners (corner radius about 2 pixels at this "
 "size), parallel, identical in size, separated by a gap. Bar height is about 50% of the disc "
 "diameter (i.e. about 54 px on a 108 px disc). The two bars plus the gap together are about 44% "
 "of the disc diameter (about 48 px on a 108 px disc), so each bar is about 16 px wide and the gap "
 "between them is about 16 px - the gap is as wide as a bar. The whole two-bar group is centred in "
 "the disc (do not shift it left or right). The bars are filled with the same flat light-blue "
 "colour as the play triangle (about #A7CBF1) with clean anti-aliased edges, no outline, no "
 "shadow, no gradient, no glow on the bars themselves.\n"
 "TRANSPARENT BACKGROUND: this is a game UI sprite; it MUST have a real alpha channel. "
 "Everything outside the soft feathered glow around the disc is fully transparent. Do not add any "
 "square plate, card, panel, frame, border, box, rounded rectangle, background wash, drop shadow "
 "rectangle or watermark. Do not add any text, letters, numbers smiley, logo or decorative "
 "element. Output only the single round button sprite, centred, nothing else.\n"
)

P_LIGHT = (
 "Transparent background with a real alpha channel: the PNG must have genuine transparency - "
 "every pixel outside the soft glow of the button is fully transparent (alpha = 0). "
 "Do not place the button on any opaque backdrop.\n"
 "Redraw this exact round UI button, keeping its look identical, but swap its centre symbol: the "
 "existing play triangle must become a pause symbol = two parallel vertical rounded bars. Keep the "
 "frosted pale-blue disc body, its grey-blue circular outline ring and its soft blurred outer glow "
 "exactly as they are in the reference; only the middle symbol changes. The two bars are thin "
 "vertical rounded rectangles of equal width, the same height as the old triangle (about half the "
 "disc diameter), close to each other with a narrow gap about as wide as one bar, together about "
 "44% of the disc width, the pair perfectly centred inside the disc. Flat light-blue colour, same "
 "tint as the old triangle, smooth anti-aliased edges. Keep the icon a single round button sprite "
 "on transparent background, no panel, no box, no frame, no text, no extra decoration."
)

P_TIGHT = (
 "Transparent background, real alpha channel, alpha = 0 everywhere outside the button's soft glow.\n"
 "Input: one round play-button sprite (pale blue-white frosted disc + grey-blue ring + soft blue "
 "outer glow, with a light-blue play triangle in the centre).\n"
 "Output: the SAME sprite pixel for pixel, except that the light-blue play triangle is deleted and "
 "replaced by the pause symbol: exactly two vertical rounded bars, side by side, equal size, flat "
 "light-blue fill (#A7CBF1), rounded corners, no outline. Measurements relative to the disc: disc "
 "diameter 108 units; each bar 16 units wide, 54 units tall, 16 units apart; the pair occupies 48 "
 "units total, perfectly centred both horizontally and vertically inside the disc. Nothing else "
 "changes: no new glow, no new ring, no border, no panel, no shadow, no text, no background. "
 "The final image is a single round button icon floating on full transparency."
)

# 「盘面口径」加强段 —— 前四个候选的实测偏差都是「外发光给太浓 + 环不在最外缘」，
# 本段专门压这两项，并钉住盘面占画布的比例。
P_FAINT = (
 "Transparent background with a real alpha channel - alpha = 0 on every pixel outside the "
 "button's faint glow. Do NOT place the button on any opaque or coloured backdrop.\n"
 "Redraw this round UI button keeping its look, but replace the middle play triangle with a pause "
 "symbol = two parallel vertical rounded bars.\n"
 "CRITICAL STYLE CONSTRAINTS - the input image is pale, flat and whisper-quiet; the output must be "
 "the same, not a saturated glossy icon:\n"
 "1) The outer glow is VERY FAINT: only a soft, barely-visible pale white-blue feathering a few "
 "pixels wide just outside the rim, low opacity, fading to fully transparent quickly. Do NOT draw "
 "a thick bright saturated blue halo, a glowing neon ring, a wide blue band or a coloured "
 "backdrop around the button.\n"
 "2) The circular outline ring is a THIN flat grey-blue line (about 3 px on a 108 px disc) sitting "
 "exactly on the outer rim of the disc - the outermost edge of the disc body. It is NOT a band, "
 "NOT a double ring, NOT placed inside the disc with blue between the ring and the rim.\n"
 "3) The disc body is nearly flat and very pale: only a very slight vertical gradient from "
 "near-white at the top (#F2F7FE) to pale ice blue at the bottom (#E4EFFC). No strong shading, no "
 "glossy highlight, no inner shadow.\n"
 "4) The disc keeps the same size and the same margin inside the canvas as the input: its outer "
 "rim spans about 91% of the canvas width, leaving a narrow margin of about 5% on each side.\n"
 "5) Keep the disc perfectly circular and centred.\n"
 "PAUSE SYMBOL: two identical vertical bars with small rounded corners (radius about 2 px at "
 "108 px disc size), each bar about 16 px wide and 54 px tall, separated by a gap about as wide as "
 "one bar (about 16 px), the pair about 48 px wide in total, perfectly centred in the disc. Flat "
 "pale-blue fill about #A7CBF1, no outline and no glow on the bars. "
 "The image contains only this single round button on full transparency: no panel, no card, no "
 "frame, no box, no text, no letters, no numbers, no watermark, no decoration."
)

# 「消除外发光 + 环贴外缘」极限口径 —— 前十个候选的共同偏差都是「给了一个明显光晕 / 把盘面
# 立体化」，而基准件的盘面近乎是平的、几乎无外发光，环就是最外缘那条 3px 硬边。本段写成禁令。
P_FLAT = (
 "Transparent background, real alpha channel - alpha = 0 everywhere outside the 1-2 pixel "
 "anti-aliasing feather of the button's edge.\n"
 "Draw a FLAT, MATTE, MINIMAL game UI icon - a plain round button, NOT a glossy 3D orb:\n"
 "The plate is an almost perfectly flat circular disc in one single very pale ice-blue tint "
 "(#E7F0FD), uniform to the eye, with at most a barely perceptible vertical lightness variation of "
 "2-3 percent; NO three-dimensional shading, NO specular highlight, NO inner shadow, NO glossy "
 "reflection, NO bevel, NO elevation, NO drop shadow.\n"
 "The whole outline of the plate is ONE thin solid grey-blue circular stroke (#929FB7), about 3 "
 "units thick on a 108-unit diameter plate, drawn exactly ON the outer circumference of the plate: "
 "it IS the outermost edge of the button. There is NO margin, band, rim or second ring outside this "
 "stroke, and no pale ring between the stroke and the plate inside.\n"
 "OUTER GLOW IS FORBIDDEN: do not draw any halo, glow, bloom, blur, aura, vignette or soft shadow "
 "around the button. Immediately outside that grey-blue stroke the image is fully transparent with "
 "alpha = 0 (only a 1-2 pixel anti-aliasing feather is allowed).\n"
 "Centre symbol: replace the play triangle of the input image with the pause symbol = two vertical "
 "bars with only slightly rounded corners. Each bar is about 16 units wide and 54 units tall, "
 "separated by a gap about 16 units wide, the pair about 48 units wide in total, centred exactly in "
 "the plate. Fill them with one flat uniform pale blue (#A7CBF1): no gradient, no outline, no "
 "shadow, no glow.\n"
 "The image contains only this one flat round button icon on full transparency: no panel, no card, "
 "no frame, no box, no background, no text, no letters, no numbers, no watermark."
)

# 符号「填充率」两次加码 —— 实测前十个候选的 ‖ 全都明显偏小（组宽 28–39 vs 规格 48；条高 42–54 vs 54；
# 间隙 7.5–10 vs 16），故把符号段**前置**再写一遍（C13），并试一次**超量下注**（C14：按 20/20/20
# 与 62 高下单，指望落回 16/16/16 @54 —— 属工程标定，不是规格变更，交付仍按实测如实登记）。
_SYM_STRONG = (
 "Centre symbol: the play triangle of the input image must be replaced by the pause symbol = EXACTLY "
 "TWO vertical bars with slightly rounded corners (corner radius at most 1/8 of the bar width).\n"
 "SIZE - the symbol must be as large as the play triangle it replaces and fill the middle of the "
 "plate boldly, NOT a small or skinny glyph: the two bars plus the gap between them span about 44 "
 "percent of the plate diameter (48 of 108 units), each bar is about 54 units tall (about half the "
 "plate diameter), so each bar is about 16 units wide and the empty vertical slot between them is "
 "about 16 units wide - exactly as wide as one bar. The pair is centred exactly in the plate both "
 "horizontally and vertically. Flat uniform pale blue (#A7CBF1), no gradient, no outline, no "
 "shadow, no glow.\n"
)
_SYM_OVER = (
 "Centre symbol: replace the play triangle with the pause symbol = EXACTLY TWO vertical bars with "
 "slightly rounded corners.\n"
 "GEOMETRY - follow these numbers literally: plate diameter 108 units; EACH BAR 20 units wide and 62 "
 "units tall; the empty vertical slot between the two bars 20 units wide; so the two bars plus the "
 "slot span 60 units in total (55 percent of the plate diameter) and the whole pair is centred "
 "exactly in the middle of the plate, both horizontally and vertically. Make the symbol bold and "
 "generous: it must occupy the middle of the plate clearly, never a small, short or skinny glyph. "
 "Flat uniform pale blue (#A7CBF1), no gradient, no outline, no shadow, no glow.\n"
)
P_FLAT2 = _SYM_STRONG + P_FLAT
P_FLAT3 = _SYM_OVER + P_FLAT
# 第三次下注：条宽 / 条高已被 C14 的超量下注标定住（实测 15.9 / 55.8），只剩**间隙**一直偏窄
# （下单 16 → 实测 10.5；下单 20 → 实测 10.7，几乎不动）⇒ 这次把间隙单独超量到 30 再试一次。
_SYM_GAP = (
 "Centre symbol: replace the play triangle with the pause symbol = EXACTLY TWO vertical bars with "
 "slightly rounded corners.\n"
 "GEOMETRY - follow these numbers literally: plate diameter 108 units; EACH BAR 20 units wide and 62 "
 "units tall; the EMPTY VERTICAL SLOT between the two bars is 30 units wide, i.e. clearly WIDER than "
 "one bar - the two bars are well separated and must never look crowded, touching or merged. The two "
 "bars plus the wide slot span 70 units in total and the whole pair is centred exactly in the middle "
 "of the plate, both horizontally and vertically. Make the symbol bold and generous. Flat uniform "
 "pale blue (#A7CBF1), no gradient, no outline, no shadow, no glow.\n"
)
P_FLAT4 = _SYM_GAP + P_FLAT

# 候选表：tag → (model, size, ref_scale, prompt)
CANDS = {
    "C1": dict(model="gpt-image-2.5-1k", size="1024x1024", ref=4.0, prompt=P_TASK,
               note="4× 参考 + 几何规格详尽段；**两次尝试都返回 RGB**（含重试）——"
                    "用来证明「无 alpha」与 prompt 里透明指令的位置无关，是随机事件"),
    "C2": dict(model="gpt-image-2.5-1k", size="1024x1024", ref=4.0, prompt=P_LIGHT,
               note="4× 参考 + 轻措辞（前置透明指令 + 强调同风格）"),
    "C3": dict(model="gpt-image-2.5-1k", size="1024x1024", ref=1.0, prompt=P_TASK,
               note="1:1 参考（保盘面尺度）+ 几何规格段"),
    "C4": dict(model="gpt-image-2.5-sunburst", size="1024x1024", ref=4.0, prompt=P_TIGHT,
               note="换模型 sunburst + 极简指令式措辞（**上游 500，无产物**）"),
    "C5": dict(model="gpt-image-2.5-1k", size="1024x1024", ref=8.0, prompt=P_TIGHT,
               note="8× 参考（大图给模型更多像素）+ 极简措辞"),
    "C6": dict(model="gpt-image-2", size="1024x1024", ref=4.0, prompt=P_TASK,
               note="换模型 gpt-image-2（原生 1024×1024）+ 几何规格段"),
    "C7": dict(model="gpt-image-2", size="1024x1024", ref=4.0, prompt=P_FAINT,
               note="盘面口径加强段（压外发光/环贴最外缘/钉盘面占画布 91%）+ gpt-image-2"),
    "C8": dict(model="gpt-image-2.5-1k", size="1024x1024", ref=4.0, prompt=P_FAINT,
               note="盘面口径加强段 + gpt-image-2.5-1k"),
    "C9": dict(model="gpt-image-2", size="1024x1024", ref=1.0, prompt=P_FAINT,
               note="盘面口径加强段 + 1:1 参考（试把「盘面占画布 91%」这条压住）"),
    "C10": dict(model="gpt-image-2", size="1024x1024", ref=2.0, prompt=P_FAINT,
                note="盘面口径加强段 + 2× 参考（盘面 / 图形都比 4× 更小，留出更多画布余量）"),
    "C11": dict(model="gpt-image-2", size="1024x1024", ref=4.0, prompt=P_FLAT, clip=True,
                note="「禁外发光 + 环贴外缘」极限口径 + **参考图先削掉弱 alpha 羽边**（ref_4x_clean）"),
    "C12": dict(model="gpt-image-2.5-1k", size="1024x1024", ref=4.0, prompt=P_FLAT, clip=True,
                note="同上口径，换 gpt-image-2.5-1k"),
    "C13": dict(model="gpt-image-2", size="1024x1024", ref=4.0, prompt=P_FLAT2, clip=True,
                note="P_FLAT + 符号段前置重写（钉 16/16/16 @54、明令「不得偏小」）"),
    "C14": dict(model="gpt-image-2", size="1024x1024", ref=4.0, prompt=P_FLAT3, clip=True,
                note="P_FLAT + 符号段前置**超量下注**（按 20/20/20 @62 下单，指望落回 16/16/16 @54）"),
    "C15": dict(model="gpt-image-2", size="1024x1024", ref=4.0, prompt=P_FLAT4, clip=True,
                note="P_FLAT + 符号段前置、**间隙单独超量下注**（20/30/20 @62，专治间隙一直偏窄）"),
}

# ─────────────────────────────────────────────────────── multipart + POST
def build_body(fields, files):
    b = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields:
        out += ("--%s\r\n" % b).encode()
        out += ('Content-Disposition: form-data; name="%s"\r\n\r\n' % k).encode()
        out += str(v).encode("utf-8") + b"\r\n"
    for k, fn, data in files:
        out += ("--%s\r\n" % b).encode()
        out += ('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (k, fn)).encode()
        out += b"Content-Type: image/png\r\n\r\n"
        out += data + b"\r\n"
    out += ("--%s--\r\n" % b).encode()
    return b, bytes(out)


def edits(ref_png, model, prompt, size, key):
    # ★ 真 alpha 的**充分条件（本次实测发现，本轮登记）**：
    #   `background:"transparent"` **必须与 `output_format:"png"` 一起给** 才出 RGBA。
    #   单给 background（本工程旧结论）→ RGB；再加 output_format=png → RGBA。
    #   实测四组见 复现脚本\_probe_alpha.py 与 候选\_probe\_probe_alpha.json。
    fields = [("model", model), ("prompt", prompt), ("n", "1"),
              ("size", size), ("response_format", "b64_json"),
              ("background", "transparent"), ("output_format", "png")]
    files = [("image", os.path.basename(ref_png), open(ref_png, "rb").read())]
    b, body = build_body(fields, files)
    req = urllib.request.Request(
        BASE + "/images/edits", data=body, method="POST",
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "multipart/form-data; boundary=" + b,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            return r.status, json.loads(r.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:800], time.time() - t0
    except Exception as e:
        return -1, repr(e)[:400], time.time() - t0


def log(rec):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_one(tag, key, force=False):
    c = CANDS[tag]
    dst = os.path.join(CAND, "pause_AI_cand_%s.png" % tag)
    meta_p = os.path.join(CAND, "pause_AI_cand_%s.meta.json" % tag)
    if os.path.exists(dst) and not force:
        print("[skip] %s 已存在" % tag); return tag, "skip"
    ref = make_ref(c["ref"], "%gx" % c["ref"], c.get("clip", False))
    attempts = []
    # ★ 实测：即便 background=transparent + output_format=png + prompt 明确要求，
    #   仍**偶发**返回 RGB（棋盘格烘焙进像素）——本轮 10 次里 2 次。
    #   ⇒ 必须逐件验 mode，无 alpha 就重试（最多 3 次取首个 RGBA）。
    for k in range(3):
        st, resp, dt = edits(ref, c["model"], c["prompt"], c["size"], key)
        rec = dict(tag=tag, attempt=k + 1, model=c["model"], size=c["size"],
                   ref=os.path.basename(ref), ref_scale=c["ref"], http=st, sec=round(dt, 1),
                   prompt_sha1=hashlib.sha1(c["prompt"].encode()).hexdigest()[:12],
                   note=c["note"], prompt=c["prompt"], out=None, mode=None, err=None)
        print("[call] %s#%d model=%s size=%s http=%s %.1fs" % (tag, k + 1, c["model"], c["size"], st, dt))
        if st != 200:
            rec["err"] = resp if isinstance(resp, str) else json.dumps(resp)[:800]
            log(rec); attempts.append(rec); print("   !! %s" % str(rec["err"])[:200]); break
        try:
            raw = base64.b64decode(resp["data"][0]["b64_json"])
        except Exception as e:
            rec["err"] = "decode: " + repr(e)[:300]; log(rec); attempts.append(rec); break
        tmp = dst + ".tmp"
        open(tmp, "wb").write(raw)
        # ★ Windows：PIL 惰性读取会占住文件句柄，之后 os.replace 会 WinError 32
        #   ⇒ 用 BytesIO 验 mode/size，不要 Image.open(路径)
        with Image.open(io.BytesIO(raw)) as im:
            mode = im.mode; sz = list(im.size)
        rec.update(mode=mode, actual_size=sz, bytes=len(raw))
        if "A" in mode:
            os.replace(tmp, dst)
            rec["out"] = os.path.basename(dst)
            json.dump(rec, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            log(rec); print("   -> RGBA ✓ %s %sx%s" % (os.path.basename(dst), sz[0], sz[1]))
            return tag, "ok"
        # 无 alpha：留档为 *_rgb 证据，继续重试
        rgbp = os.path.join(CAND, "pause_AI_cand_%s_attempt%d_RGB.png" % (tag, k + 1))
        os.replace(tmp, rgbp)
        rec["out"] = os.path.basename(rgbp)
        log(rec); attempts.append(rec)
        print("   -> RGB ✗（无 alpha，棋盘格烘焙风险）留档 %s，重试…" % os.path.basename(rgbp))
    print("   xx %s 未取得 RGBA" % tag)
    return tag, "no-alpha"


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    only = None
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    key = load_key()
    todo = [t for t in CANDS if (only is None or t in only)]
    with ThreadPoolExecutor(max_workers=2) as ex:      # ★ 并发放宽上限 2
        for tag, r in ex.map(lambda t: run_one(t, key, force), todo):
            print("== %s -> %s" % (tag, r))
    print("\n候选目录：", CAND)


if __name__ == "__main__":
    main()
