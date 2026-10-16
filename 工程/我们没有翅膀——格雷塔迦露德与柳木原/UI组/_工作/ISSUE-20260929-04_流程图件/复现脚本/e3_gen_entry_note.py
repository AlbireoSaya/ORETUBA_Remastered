# -*- coding: utf-8 -*-
r"""E3 · 流程图屏「番外入口」标记（`x_ui_entry_note.png`）正式美术生图。

ISSUE-20260929-04 ｜ 接口冻结 §A 第 3 行 ｜ 规格：86×48 RGBA 真 alpha，书签／折角便签形状，纯图形无文字。

用法：
    python e3_gen_entry_note.py list                # 列出候选条目（含完整提示词）
    python e3_gen_entry_note.py all                 # 跑全部候选（并发 2）
    python e3_gen_entry_note.py only E3-A E3-C      # 跑指定候选
    python e3_gen_entry_note.py all --force         # 覆盖已存在的产物

幂等：默认跳过已存在的 PNG（不重复计费）。元数据一律追加/合并进 `生图\_meta.json`。
key 读取：`E:\ZCode Workspace\.zcode\v2\provider_config.json` 的 `new-provider-2` 条目（不打印内容）。
"""
import base64, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_DIR = os.path.dirname(HERE)                       # …\_工作\ISSUE-20260929-04_流程图件
OUT = os.path.join(ITEM_DIR, "生图")
os.makedirs(OUT, exist_ok=True)
META = os.path.join(OUT, "_meta.json")

CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# ============================================================
# 风格锚点（取自本工程既有 AI 素材实测口径：审查报告 §二 ＋ ui_gen.py STYLE）
#   ★ TRANS 必须前置：实测「指令式」要求透明才出真 alpha，「描述式」只得到 RGB（审查报告 §4.1）
#   ★ 2026-09-21 用户裁定：不再加雪花/冰晶要素 → 雪花类全部进负面词
# ============================================================
TRANS = "Transparent background with a real alpha channel. "
NOTEXT = ("The image is a PURE GRAPHIC SHAPE ONLY: absolutely NO text, NO letters, NO numbers, "
          "NO words and NO symbols are written on it or anywhere in the image. ")
STYLE = ("Frosted ice glass style on a pale glacier palette: translucent ice-blue gradient from "
         "near-white #F1F7FC to soft pale ice-blue #E3EDF9, frosted white panel fill gradient "
         "#EDF4FC to #E2EDFA, delicate cyan-blue rim #7CB7FD to #A0C9F7 about 3 px wide with a "
         "soft 10 px outer glow halo, smooth rounded corners, a gentle diagonal frosted-glass "
         "sheen sweeping from the top-left, airy, luminous, clean and minimal, uncluttered. "
         "STRICTLY AVOID: snowflakes, snowflake patterns, frost crystal ornaments, star sparkles, "
         "glitter, dark or charcoal colors, hard dark outlines, black drop shadows, neon cyan, "
         "any text, letters, numbers or watermark.")


def P(desc):
    return TRANS + NOTEXT + desc.strip() + " " + STYLE


# ============================================================
# 候选表：(编号, 模型, size, 输出名, 构图族, 描述)
#   三种构图族：bookmark（书签）/ folded（折角便签）/ bookmark_hole（带小圆点孔的书签）
# ============================================================
ITEMS = [
    ("E3-A", "gpt-image-2.5-1k", "1536x1024", "E3-A_书签_燕尾正立",
     "bookmark",
     "A single elegant BOOKMARK shape, centered: a slim vertical rectangle whose lower end is "
     "cut into a symmetric inverted V-shaped notch (a swallow-tail ribbon end), and a small "
     "punched round hole near its upper end. Only this one bookmark graphic, upright."),

    ("E3-B", "gpt-image-2.5-1k", "1536x1024", "E3-B_书签_燕尾斜置",
     "bookmark",
     "A single elegant BOOKMARK shape: a slim rectangle with a symmetric inverted V-shaped notch "
     "at its lower end and a small punched round hole near its upper end. The bookmark is tilted "
     "about 30 degrees so that it leans diagonally across the frame, centered. "
     "Only this one bookmark graphic."),

    ("E3-C", "gpt-image-2.5-1k", "1536x1024", "E3-C_折角便签_右下折角",
     "folded",
     "A single folded-corner NOTE CARD: a wide horizontal memo sheet, slightly wider than tall, "
     "whose bottom-right corner is folded over toward the viewer so that a small triangular "
     "dog-ear flap with a soft crease shows on the front face. The face of the note is completely "
     "blank. Only this one note graphic, centered, seen flat and front-facing."),

    ("E3-D", "gpt-image-2-1k", "1536x1024", "E3-D_折角便签_右上折角",
     "folded",
     "A single folded-corner NOTE: a soft rounded sheet whose top-right corner is curled over "
     "toward the viewer, showing a small triangular folded flap and a delicate crease line, like "
     "a paper note with a dog-eared corner. The face is completely blank. Centered, "
     "seen flat and front-facing."),

    ("E3-E", "gpt-image-2.5-1k", "1536x1024", "E3-E_书签孔_窄带圆点孔",
     "bookmark_hole",
     "A single narrow BOOKMARK ribbon: a very slim flat strip with parallel long edges, a small "
     "punched round hole at the top, and a shallow triangular point at the bottom. No tassel, "
     "no cord. Only this one strip graphic, upright, centered."),

    ("E3-F", "gpt-image-2", "1536x1024", "E3-F_入口牌_横置带孔",
     "bookmark_hole",
     "A single horizontal ENTRY TAG PLAQUE, wider than tall: a rounded horizontal tag whose right "
     "end is cut into a symmetric inverted V notch and which has a small punched round hole at "
     "its left end, like a luggage tag or a bookmark lying on its side. Only this one tag "
     "graphic, centered, horizontal."),

    ("E3-G", "gpt-image-2.5-1k", "1536x1024", "E3-G_折角便签_折角带折痕",
     "folded",
     "A single folded NOTE SHEET, wider than tall, lying flat: a clean rectangular sheet with a "
     "crisp diagonal fold across its lower-right corner, the folded triangular corner lifting "
     "slightly toward the viewer with a fine crease and a soft shadow line along the fold. "
     "The sheet face is completely blank. Only this one sheet graphic, centered."),

    # ── 精修二件：对领先两种构图的二次冲击（更粗的冰蓝描边 + 更贴合 86:48 槽位）──
    ("E3-H", "gpt-image-2.5-1k", "1536x1024", "E3-H_横置书签_精修粗描边",
     "bookmark_hole",
     "A single horizontal BOOKMARK TAG, about 1.8 times wider than tall, made as one flat tag "
     "shape: a small round punched hole near its LEFT end and a deep symmetric inverted V-shaped "
     "notch cut into its RIGHT end, so it reads as a ribbon bookmark laid on its side. "
     "A distinctly BOLD and thick clear ice-blue outline runs along the whole silhouette, and the "
     "outline width is at least 2 percent of the tag width so that it stays clearly visible.",
     ),

    ("E3-I", "gpt-image-2.5-1k", "1536x1024", "E3-I_折角便签_大折角",
     "folded",
     "A single NOTE SHEET, about 1.7 times wider than tall: a flat paper sheet whose whole "
     "BOTTOM-RIGHT corner is turned up and back, so that a LARGE triangular folded flap about "
     "one third of the sheet width lies over the upper face, meeting the two edges at sharp "
     "clean diagonal cut lines. The remaining face is completely blank. "
     "A distinctly BOLD and thick clear ice-blue outline follows the silhouette and the fold, "
     "at least 2 percent of the sheet width, so it stays clearly visible when small. "
     "Only this one sheet graphic, centered."),

    # ── 精修第三件：把「书签」的整幅外接矩形直接按目标槽位 86:48 定比例 ──
    ("E3-J", "gpt-image-2.5-1k", "1536x1024", "E3-J_横置书签_槽位比例",
     "bookmark_hole",
     "A single horizontal BOOKMARK TAG, whose whole outer bounding box is a clean rectangle "
     "about 1.8 times wider than tall (a 9:5 proportion, roughly the shape of a wide name tag). "
     "Its content: a small round punched hole near the LEFT end, and a deep symmetric inverted "
     "V-shaped notch cut into the RIGHT end, so that it reads as a ribbon bookmark lying on its "
     "side. A distinctly BOLD and thick clear ice-blue outline at least 2 percent of the tag "
     "width runs along the entire silhouette, so the outline stays clearly visible when the "
     "graphic is displayed small. The tag is centered and fills the frame with only a narrow "
     "margin around it."),
]

BY_KEY = {it[0]: it for it in ITEMS}


def load_key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]
    raise SystemExit("未找到 new-provider-2 的 apiKey")


def load_meta():
    if os.path.exists(META):
        try:
            return json.load(open(META, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_meta(m):
    with open(META, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)


def call(model, prompt, size, key, timeout=420):
    body = json.dumps({
        "model": model, "prompt": prompt, "size": size, "n": 1,
        "background": "transparent", "output_format": "png",
        "response_format": "b64_json",
    }).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/images/generations", data=body,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8")), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), time.time() - t0
    except Exception as e:
        return None, "EXC: %r" % (e,), time.time() - t0


def run_one(k, key, force=False):
    it = BY_KEY[k]
    _, model, size, name, family, desc = it
    prompt = P(desc)
    png = os.path.join(OUT, name + ".png")
    rec = {"id": k, "model": model, "size_requested": size, "family": family,
           "out": os.path.basename(png), "prompt": prompt}
    if os.path.exists(png) and not force:
        rec["skipped"] = True
        rec["note"] = "产物已存在（幂等跳过）"
        return (k, True, "SKIP 已存在 %s" % os.path.basename(png), rec)
    st, resp, el = call(model, prompt, size, key)
    rec["http"] = st
    rec["seconds"] = round(el, 1)
    if st != 200:
        rec["error"] = str(resp)[:400]
        return (k, False, "HTTP=%s %.1fs %s" % (st, el, str(resp)[:160]), rec)
    try:
        d0 = resp["data"][0]
    except Exception as e:
        rec["error"] = "响应无 data: %r" % e
        return (k, False, "响应无 data %r" % (e,), rec)
    raw = None
    if d0.get("b64_json"):
        raw = base64.b64decode(d0["b64_json"])
    elif d0.get("url"):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(d0["url"], headers={"User-Agent": UA}),
                    timeout=240) as r:
                raw = r.read()
        except Exception as e:
            rec["error"] = "下载失败 %r" % (e,)
            return (k, False, "下载失败 %r" % (e,), rec)
    if raw is None:
        rec["error"] = "无 b64/url"
        return (k, False, "无 b64/url", rec)
    open(png, "wb").write(raw)
    rec["bytes"] = len(raw)
    info = ""
    try:
        from PIL import Image
        with Image.open(png) as im:
            rec["mode"] = im.mode
            rec["image_size"] = list(im.size)
            if im.mode == "RGBA":
                lo, hi = im.getchannel("A").getextrema()
                rec["alpha_extrema"] = [lo, hi]
            info = "mode=%s size=%s" % (im.mode, tuple(im.size))
            if im.mode == "RGBA":
                info += " alpha=%d..%d" % tuple(rec.get("alpha_extrema", [0, 0]))
    except Exception as e:
        info = "PIL 失败 %r" % e
    return (k, True, "%.1fs %s %d B %s" % (el, os.path.basename(png), len(raw), info), rec)


def run(keys, workers=2, force=False):
    key = load_key()
    meta = load_meta()
    print("模型档：%s ｜ 待跑 %d 件 ｜ 并发 %d ｜ 输出 %s"
          % (sorted({BY_KEY[k][1] for k in keys}), len(keys), workers, OUT), flush=True)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one, k, key, force): k for k in keys}
        for fu in as_completed(futs):
            k, good, msg, rec = fu.result()
            rec["key_present"] = "new-provider-2"
            meta[k] = rec
            if not good:
                # 失败也留档：模型档不可用是可复现的事实，不能被下一次成功覆盖
                meta.setdefault("_failures", []).append(
                    {"id": k, "model": rec.get("model"), "http": rec.get("http"),
                     "seconds": rec.get("seconds"), "error": (rec.get("error") or "")[:300],
                     "at": time.strftime("%Y-%m-%d %H:%M:%S")})
            save_meta(meta)
            if good:
                ok += 1
                print("[OK  ] %-5s %s" % (k, msg), flush=True)
            else:
                fail += 1
                print("[FAIL] %-5s %s" % (k, msg), flush=True)
    print("完成：成功 %d ｜ 失败 %d" % (ok, fail), flush=True)
    return ok, fail


def main():
    a = sys.argv[1:]
    force = "--force" in a
    a = [x for x in a if x != "--force"]
    if not a or a[0] == "list":
        for k, model, size, name, fam, desc in ITEMS:
            print("=" * 78)
            print("%-5s 模型=%s  size=%s  族=%s  产物=%s.png" % (k, model, size, fam, name))
            print(P(desc))
        return
    if a[0] == "all":
        keys = [it[0] for it in ITEMS]
    elif a[0] == "only":
        keys = a[1:]
    else:
        raise SystemExit("用法：e3_gen_entry_note.py [list|all|only <keys...>] [--force]")
    bad = [k for k in keys if k not in BY_KEY]
    if bad:
        raise SystemExit("未知条目：%s" % bad)
    run(keys, workers=2, force=force)


if __name__ == "__main__":
    main()
