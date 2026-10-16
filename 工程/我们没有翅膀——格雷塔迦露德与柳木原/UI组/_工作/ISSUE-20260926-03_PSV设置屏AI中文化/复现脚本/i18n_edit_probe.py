# -*- coding: utf-8 -*-
r"""ISSUE-20260926-03 · 用户方法验证：原图页区 → gpt-image-2.5-sunburst 图生图日译中
调用方式探针：A) /images/edits (multipart)  B) /images/generations + image 字段(b64)
输入：PSV系统UI参考\otv_bg_config_01.png 页面区 (0,0,960,544)（不透明部分，剥离雪碧条）
输出：工具\lyai-image-api\out_i18n\probe_*.png
"""
import base64, json, os, time, urllib.request, urllib.error, io, uuid

HERE = r"E:\ZCode Workspace\Galgame\工具\lyai-image-api"
CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT = os.path.join(HERE, "out_i18n"); os.makedirs(OUT, exist_ok=True)

def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]

PROMPT = (
 "Edit this visual-novel system CONFIG screen. Replace ONLY the Japanese text with the "
 "Simplified Chinese text given below. Keep absolutely everything else unchanged and "
 "pixel-identical: the snowflake artwork, the frosted glass panel, panel borders, the slider "
 "groove, the English word CONFIG, the L/R arrows, button shapes, layout, colors, lighting. "
 "Render each replacement in the same font style, size, color and soft glow as the original "
 "Japanese text it replaces, at the same position.\n"
 "Replacements (Japanese -> Simplified Chinese):\n"
 "基本設定 -> 基本设置\n"
 "シーンスキップ機能 -> 场景跳过功能\n"
 "音声スキップ -> 语音跳过\n"
 "スキップモード -> 跳过模式\n"
 "選択後のスキップ -> 选择后的跳过\n"
 "選んだ選択肢の色を変更 -> 更改已选选项的颜色\n"
 "自動クイックセーブ -> 自动快速存档\n"
 "メッセージ速度 -> 消息速度\n"
 "ウィンドウの不透明度 -> 窗口不透明度\n"
 "する -> 开启\n"
 "しない -> 关闭\n"
 "既読のみ -> 仅限已读\n"
 "全て -> 全部\n"
 "持続 -> 持续\n"
 "解除 -> 解除\n"
 "選択肢毎 -> 逐个选项\n"
 "シーン毎 -> 逐场景\n"
 "選択肢+シーン毎 -> 选项+场景\n"
 "遅い -> 慢\n"
 "普通 -> 普通\n"
 "早い -> 快\n"
 "一律 -> 统一\n"
 "デフォルト設定 -> 默认设置\n"
 "選択 -> 选择\n"
 "戻る -> 返回\n"
 "Do not translate or alter the English words CONFIG, ON, OFF. Do not add or remove any element."
)

def save_b64(resp, name):
    it = resp["data"][0]
    raw = base64.b64decode(it["b64_json"]) if it.get("b64_json") else None
    if raw is None and it.get("url"):
        with urllib.request.urlopen(urllib.request.Request(it["url"], headers={"User-Agent": UA}), timeout=240) as r:
            raw = r.read()
    p = os.path.join(OUT, name)
    open(p, "wb").write(raw)
    from PIL import Image
    im = Image.open(p)
    return p, im.mode, im.size

def try_edits(png_path, model="gpt-image-2.5-sunburst"):
    boundary = uuid.uuid4().hex
    fn = os.path.basename(png_path)
    parts = []
    def field(name, val):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, name, val)).encode("utf-8"))
    field("model", model); field("prompt", PROMPT)
    field("response_format", "b64_json"); field("n", "1"); field("size", "auto")
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % (boundary, fn)).encode("utf-8"))
    parts.append(open(png_path, "rb").read())
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    body = b"".join(parts)
    req = urllib.request.Request(BASE + "/images/edits", data=body, method="POST",
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "multipart/form-data; boundary=" + boundary,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time()-t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:400], time.time()-t0)
    except Exception as e:
        return ("err", repr(e)[:300], time.time()-t0)

def try_gen_with_image(png_path, model="gpt-image-2.5-sunburst"):
    b64 = base64.b64encode(open(png_path, "rb").read()).decode()
    body = json.dumps({"model": model, "prompt": PROMPT, "image": [b64], "n": 1,
                       "response_format": "b64_json"}).encode("utf-8")
    req = urllib.request.Request(BASE + "/images/generations", data=body,
        headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time()-t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:400], time.time()-t0)
    except Exception as e:
        return ("err", repr(e)[:300], time.time()-t0)

if __name__ == "__main__":
    from PIL import Image
    src = Image.open(os.path.join(SRC_DIR := r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\PSV系统UI参考",
                                  "otv_bg_config_01.png")).convert("RGBA")
    page = src.crop((0, 0, 960, 544)).convert("RGB")
    p1 = os.path.join(OUT, "page_01_input.png"); page.save(p1)
    print("input:", page.size)
    st, resp, dt = try_edits(p1)
    print("A /images/edits →", st, "%.1fs" % dt, str(resp)[:200])
    if st == "ok":
        print("saved:", save_b64(resp, "probe_edits_01.png"))
        raise SystemExit
    st, resp, dt = try_gen_with_image(p1)
    print("B generations+image →", st, "%.1fs" % dt, str(resp)[:200])
    if st == "ok":
        print("saved:", save_b64(resp, "probe_genimg_01.png"))
