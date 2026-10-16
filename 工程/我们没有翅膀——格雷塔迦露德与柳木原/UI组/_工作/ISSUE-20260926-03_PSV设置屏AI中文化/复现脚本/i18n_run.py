# -*- coding: utf-8 -*-
r"""ISSUE-20260926-03 · 用户方法正式跑：全图白底垫方 → sunburst 图生图日译中 → 裁回原位
输出：工具\lyai-image-api\out_i18n\{bgc01_cn.png, bgc02_cn.png}（960×833 / 960×761，1×）
"""
import base64, json, os, time, urllib.request, urllib.error, uuid
from PIL import Image

HERE = r"E:\ZCode Workspace\Galgame\工具\lyai-image-api"
CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
BASE = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT = os.path.join(HERE, "out_i18n"); os.makedirs(OUT, exist_ok=True)
PSV = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\PSV系统UI参考"

PROMPT_COMMON = (
 "Edit this visual-novel system CONFIG screen sprite sheet. Replace ONLY the Japanese text "
 "with the Simplified Chinese text given below. Keep absolutely everything else unchanged and "
 "pixel-identical: the snowflake artwork, the frosted glass panel, panel borders, slider "
 "grooves, the English word CONFIG, L/R arrows, button shapes, pill button shapes, layout, "
 "colors, lighting, and every non-text pixel. Render each replacement in the same font style, "
 "size, color and soft glow as the Japanese text it replaces, at the same position. The small "
 "pill buttons and value words in the lower sprite strip are Japanese too and must be "
 "translated with the same mapping.\n"
 "Replacements (Japanese -> Simplified Chinese):\n"
 "基本設定 -> 基本设置\n"
 "サウンド設定 -> 声音设置\n"
 "シーンスキップ機能 -> 场景跳过功能\n"
 "音声スキップ -> 语音跳过\n"
 "スキップモード -> 跳过模式\n"
 "選択後のスキップ -> 选择后的跳过\n"
 "選んだ選択肢の色を変更 -> 更改已选选项的颜色\n"
 "自動クイックセーブ -> 自动快速存档\n"
 "メッセージ速度 -> 消息速度\n"
 "ウィンドウの不透明度 -> 窗口不透明度\n"
 "Voice ボリューム -> Voice 音量\n"
 "BGM ボリューム -> BGM 音量\n"
 "SE ボリューム -> SE 音量\n"
 "システムボリューム -> 系统音量\n"
 "音声再生時に BGM 音量を下げる -> 语音播放时降低 BGM 音量\n"
 "キャラクター音声 -> 角色语音\n"
 "する -> 开启\n"
 "しない -> 关闭\n"
 "既読のみ -> 仅限已读\n"
 "全て -> 全部\n"
 "全て ON -> 全部 ON\n"
 "全て OFF -> 全部 OFF\n"
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
 "Do not translate or alter the English words CONFIG, ON, OFF, Voice, BGM, SE. "
 "Do not add, remove, move or restyle any element. Do not add new text."
)

PROMPT_C1_EXTRA = (
 "CRITICAL per-row value layout of THIS image (counts and languages must match exactly; "
 "every value stays in its own row, never borrow words from another row):\n"
 "Row 1 场景跳过功能: exactly two values, the English words \"ON\" and \"OFF\" (unchanged).\n"
 "Row 2 语音跳过: \"开启\" and \"关闭\".\n"
 "Row 3 跳过模式: \"仅限已读\" and \"全部\".\n"
 "Row 4 选择后的跳过: \"持续\" and \"解除\".\n"
 "Row 5 更改已选选项的颜色: the English words \"ON\" and \"OFF\" (unchanged).\n"
 "Row 6 自动快速存档: four values \"逐个选项\", \"逐场景\", \"选项+场景\", \"关闭\".\n"
 "Row 7 消息速度: four values \"慢\", \"普通\", \"快\", \"统一\".\n"
 "Row 8 窗口不透明度: only the slider groove, no words.\n"
 "Sprite strip row 1: exactly two sprites, \"ON\" and \"OFF\".\n"
 "Sprite strip row 5: exactly two sprites, \"ON\" and \"OFF\".\n"
 "THIS IMAGE DOES NOT CONTAIN 全て ON or 全て OFF anywhere - never render 全部 ON or 全部 OFF."
)
PROMPT_C1 = PROMPT_COMMON + PROMPT_C1_EXTRA
PROMPT = PROMPT_C1

def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]

def pad_square(src_rgba, out_path, S=1024):
    """白底垫到 1024×1024，原图左上对齐（页面区上缘贴顶，底部白与页面霜白衔接）"""
    canvas = Image.new("RGB", (S, S), (255, 255, 255))
    flat = Image.alpha_composite(Image.new("RGBA", src_rgba.size, (255, 255, 255, 255)), src_rgba).convert("RGB")
    canvas.paste(flat, (0, 0))
    canvas.save(out_path)
    return canvas

def edits(png_path, model="gpt-image-2.5-sunburst", prompt=PROMPT):
    boundary = uuid.uuid4().hex
    parts = []
    def field(name, val):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, name, val)).encode("utf-8"))
    field("model", model); field("prompt", prompt)
    field("response_format", "b64_json"); field("n", "1"); field("size", "auto")
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % (boundary, os.path.basename(png_path))).encode("utf-8"))
    parts.append(open(png_path, "rb").read())
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    req = urllib.request.Request(BASE + "/images/edits", data=b"".join(parts), method="POST",
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "multipart/form-data; boundary=" + boundary,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time()-t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:200], time.time()-t0)
    except Exception as e:
        return ("err", repr(e)[:200], time.time()-t0)

def run(name, out_name, prompt=PROMPT):
    src = Image.open(os.path.join(PSV, name)).convert("RGBA")
    sq = os.path.join(OUT, "sq_" + name)
    pad_square(src, sq)
    for attempt in range(6):
        st, resp, dt = edits(sq, prompt=prompt)
        print(name, "attempt", attempt+1, "→", st, "%.1fs" % dt)
        if st == "ok":
            raw = base64.b64decode(resp["data"][0]["b64_json"])
            p = os.path.join(OUT, "sq_out_" + name)
            open(p, "wb").write(raw)
            im = Image.open(p).convert("RGB")
            print("  output:", im.size)
            # 裁回原位（若输出为 1024×1024 则 1:1；否则按比例映射）
            sx, sy = im.width / 1024.0, im.height / 1024.0
            crop = im.crop((0, 0, int(src.width * sx), int(src.height * sy)))
            crop = crop.resize((src.width, src.height), Image.LANCZOS)
            out = os.path.join(OUT, out_name)
            crop.save(out)
            print("  ->", out, crop.size)
            return out
        time.sleep(30)
    raise SystemExit("failed: " + name)

if __name__ == "__main__":
    run("otv_bg_config_01.png", "bgc01_cn.png", prompt=PROMPT_C1)
    run("otv_bg_config_02.png", "bgc02_cn.png")
