# -*- coding: utf-8 -*-
r"""ISSUE-20260926-04 · PSV 带日文 UI 件全量日译中（用户方法批量）
35 张唯一图（61 个文件名；「ロード中…」同图 19 名只跑 1 次再复制）。
每件：白底垫方 1024×1024 → /v1/images/edits（sunburst，逐件 prompt）→ 裁回原位 → AI中文化\1x\<name>_cn.png
断点续跑：已存在的 *_cn.png 跳过。日志：_证据\batch_log.txt
"""
import base64, json, os, time, urllib.request, urllib.error, uuid
from PIL import Image

BASE_DIR = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
SRC  = os.path.join(BASE_DIR, "PSV系统UI参考")
OUT1 = os.path.join(BASE_DIR, "PSV系统UI参考", "AI中文化", "1x")
EV   = os.path.join(BASE_DIR, "_工作", "ISSUE-20260926-04_PSV全量日译中", "_证据")
os.makedirs(OUT1, exist_ok=True); os.makedirs(EV, exist_ok=True)
CFG = r"E:\ZCode Workspace\.zcode\v2\provider_config.json"
API = "https://api.lyaiapp.com/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

BASE_INSTR = ("Edit this visual-novel UI image. Replace ONLY the Japanese text with the Simplified "
 "Chinese text given below, at the same position, in the same font style, size, color and soft "
 "glow. Keep absolutely everything else unchanged and pixel-identical: artwork, panels, borders, "
 "snowflakes, icons, English words, layout and colors. Do not add or remove any element. "
 "Do not alter English words.\nReplacements (Japanese -> Simplified Chinese):\n")

def dlg_prompt(jp, cn):
    return (BASE_INSTR +
        "This is a hexagonal confirmation dialog. The Japanese message inside the panel is:\n"
        '"' + jp + '"\n'
        "Replace it with this Simplified Chinese message (keep the same line breaks and text alignment):\n"
        '"' + cn + '"\n'
        "Keep the YES/NO buttons, the hexagonal frosted panel, the snow bottom edge and all "
        "snowflake artwork unchanged. YES and NO stay in English.")

JOBS = {}
# ── 22 张确认弹窗 ──
JOBS["otv_dlg_bg_01.png"] = dlg_prompt(
 "サインインしていないため、セーブできません。それでもゲームを開始しますか？",
 "由于尚未登录，无法存档。\\n仍要开始游戏吗？")
JOBS["otv_dlg_bg_02.png"] = dlg_prompt(
 "ストレージ/デバイスを選択しないと、セーブが出来ません。それでもゲームを開始しますか？",
 "未选择存储设备的话，将无法存档。\\n仍要开始游戏吗？")
JOBS["otv_dlg_bg_03.png"] = dlg_prompt(
 "このセーブデータをロードするとセーブされていないところまでのプレイデータが失われます。よろしいですか？",
 "读取此存档后，未存档部分的游玩数据将会丢失。\\n确定吗？")
JOBS["otv_dlg_bg_04.png"] = dlg_prompt(
 "セーブデータが残っています。新しいセーブデータで上書きしますか？",
 "已有存档数据。\\n要用新的存档数据覆盖吗？")
JOBS["otv_dlg_bg_05.png"] = dlg_prompt(
 "このデータをロードします。よろしいですか？",
 "将读取此数据。\\n确定吗？")
JOBS["otv_dlg_bg_06.png"] = dlg_prompt(
 "タイトルに戻ります。セーブされていないところまでのプレイデータが失われます。よろしいですか？",
 "将返回标题。未存档部分的游玩数据将会丢失。\\n确定吗？")
JOBS["otv_dlg_bg_07.png"] = dlg_prompt(
 "システムデータを保存しますか？",
 "要保存系统数据吗？")
JOBS["otv_dlg_bg_08.png"] = dlg_prompt(
 "セーブデータを上書きします。よろしいですか？",
 "将覆盖存档数据。\\n确定吗？")
JOBS["otv_dlg_bg_09.png"] = dlg_prompt(
 "タイトルに戻ります。",
 "将返回标题。")
JOBS["otv_dlg_bg_10.png"] = dlg_prompt(
 "システムデータを上書きします。よろしいですか？保存されてゲームを終了するとデータが失われます。",
 "将覆盖系统数据。确定吗？\\n若保存后退出游戏，数据将会丢失。")
JOBS["otv_dlg_bg_11.png"] = dlg_prompt(
 "このままだとセーブデータをロードするとここまでのプレイデータが失われます。よろしいですか？",
 "这样下去，读取存档后到此为止的\\n游玩数据将会丢失。确定吗？")
JOBS["otv_dlg_bg_12.png"] = dlg_prompt(
 "設定をデフォルトに戻します。よろしいですか？",
 "将设置恢复为默认。\\n确定吗？")
JOBS["otv_dlg_bg_20.png"] = dlg_prompt(
 "保存しています。本体の電源を切らないでください。",
 "正在保存。\\n请不要关闭主机电源。")
JOBS["otv_dlg_bg_21.png"] = dlg_prompt(
 "セーブデータが壊れています。",
 "存档数据已损坏。")
JOBS["otv_dlg_bg_22.png"] = dlg_prompt(
 "セーブデータについて／ゲーム中に「クイックセーブ」したデータは、「セーブ」「ロード」画面を選んだことで「システムデータ」の保存を行わないとストレージ/デバイスに保存されませんのでご注意ください。",
 "关于存档数据\\n游戏中「快速存档」的数据，若未通过\\n「存档」「读档」画面执行「系统数据」的保存，\\n就不会被保存到存储设备中，敬请注意。\\n（红色与白色的文字颜色分布必须与原文完全一致）")
JOBS["otv_dlg_bg_23.png"] = dlg_prompt(
 "プレイデータを保存するストレージ/デバイスを選択してください。「俺たちに翼はない」のデータを保存するには、約７ＭＢの空き容量が必要となります。",
 "请选择保存游玩数据的存储设备。\\n要保存《我们没有翅膀》的数据，\\n需要约 7MB 的可用空间。\\n（约 7MB 为红色，其余白色，颜色分布与原文一致）")
JOBS["otv_dlg_bg_24.png"] = dlg_prompt(
 "セーブに失敗しました。ストレージデバイスの空き容量が足りません。",
 "存档失败。\\n存储设备的可用空间不足。")
JOBS["otv_dlg_bg_25.png"] = dlg_prompt(
 "セーブデータを削除します。",
 "将删除存档数据。")
JOBS["otv_dlg_bg_42.png"] = dlg_prompt(
 "ストレージデバイスの空き容量が足りません。",
 "存储设备的可用空间不足。")
JOBS["otv_dlg_bg_43.png"] = dlg_prompt(
 "システムデータを上書きします。よろしいですか？保存せずにゲームを終了するとデータは失われます。",
 "将覆盖系统数据。确定吗？\\n若不保存就退出游戏，数据将会丢失。")
JOBS["otv_dlg_bg_44.png"] = dlg_prompt(
 "システムデータを読み込みます。よろしいですか？保存されていないデータは消去されます。",
 "将读取系统数据。确定吗？\\n未保存的数据将被清除。")
JOBS["otv_dlg_bg_45.png"] = dlg_prompt(
 "システムデータを作成します。",
 "将创建系统数据。")
# ── 加载字家族代表（1 张 → 19 个文件名） ──
JOBS["otv_dm00.png"] = (BASE_INSTR +
 "This image contains only the Japanese text ロード中… on a transparent/white background. "
 "Replace it with the Simplified Chinese 载入中… in the same white serif-ish font style, same "
 "size and position, keeping the three dots. Nothing else exists in the image.")
# ── saving ──
JOBS["otv_saving.png"] = (BASE_INSTR +
 "This image contains only the Japanese text セーブ中… on a transparent/white background. "
 "Replace it with the Simplified Chinese 存档中… in the same white serif-ish font style, same "
 "size and position, keeping the three dots.")
# ── 存/读档页脚 ──
FOOT = "This is the bottom footer strip of a save screen. The Japanese button hints are: ⊙決定 ⊗データ削除 ⊗戻る. Replace them with ⊙确定 ⊗删除数据 ⊗返回 at the same positions and style. Keep the icons, colors and everything else unchanged."
JOBS["otv_save_bg.png"] = BASE_INSTR + FOOT + " (The English word SAVE at top-left is outside this crop area; ignore if absent.)"
JOBS["otv_load_bg.png"] = BASE_INSTR + FOOT
JOBS["otv_quick_load_bg.png"] = (BASE_INSTR +
 "This is the bottom footer strip of a quick-load screen. The Japanese button hints are: ⊙決定 ⊗戻る. "
 "Replace them with ⊙确定 ⊗返回 at the same positions and style. Keep the icons, colors and everything else unchanged.")
# ── gm_bg1 ──
JOBS["otv_gm_bg1.png"] = (BASE_INSTR +
 "If any small Japanese footer text exists at the bottom of this album screen, translate it to "
 "Simplified Chinese in the same tiny style. Everything else stays unchanged.")
# ── mu_bg（全曲名长卷，逐条映射不现实 → 通用指示） ──
JOBS["otv_mu_bg.png"] = (BASE_INSTR +
 "This is a music album long list. Translate ALL Japanese text (album/track titles, labels, "
 "button hints) into Simplified Chinese, keeping every line at its exact position, with the same "
 "font style, size and color. Keep all artwork, panels, snowflakes and English words unchanged. "
 "Keep the number of text lines identical.")
# ── title_bg ──
JOBS["otv_title_bg.png"] = (BASE_INSTR +
 "This title-screen sprite sheet contains menu items. Translate the Japanese items only:\n"
 "俺たちに翼はない -> 我们没有翅膀\n"
 "始めから -> 从头开始\n"
 "ある日の林田美咲 -> 某日的林田美咲\n"
 "ある日の渡来明日香 -> 某日的渡来明日香\n"
 "ある日の香田亜衣 -> 某日的香田亚衣\n"
 "ある日の凤鳴 -> 某日的凤鸣\n"
 "For any other ある日の… episode title, translate あるの日 pattern as 某日的<人名> and keep "
 "personal names in their kanji form. Keep the English words (QUICK LOAD, LOAD, START, GALLERY, "
 "CONFIG, ALBUM, MOVIE, MUSIC, PRESS START BUTTON), the ?????? placeholders, the logo artwork, "
 "characters and everything else unchanged.")
# ── ec1-4（章节卡：EN 章节名 + 左侧日文日程日历） ──
EC = ("This is a chapter card with an English title (Chapter : ...) and a Japanese schedule "
 "calendar panel. Translate the Japanese calendar dates into Simplified Chinese format: "
 "11月21日（火） -> 11月21日（周二）, using 周一/周二/周三/周四/周五/周六/周日 for the weekday "
 "kanji. Keep every date at its position, same font and color. Keep the English title, the "
 "item illustration, borders and everything else unchanged.")
for f in ["otv_ec1_bg.png","otv_ec2_bg.png","otv_ec3_bg.png","otv_ec4_bg.png"]:
    JOBS[f] = BASE_INSTR + EC
# ── ec5 封面（霓虹艺术字标题） ──
NEON = ("This is a chapter-cover artwork with a stylized neon Japanese title. The title reads "
 "伊丹 伽楼羅 編 (or 伊丹 加護羅 編 in the dark variant). Replace the kanji 羅 with 罗 and 編 with 篇 "
 "so the title reads 伊丹 伽楼罗 篇 / 伊丹 加护罗 篇 in Simplified Chinese, rendering it in exactly "
 "the same neon art style, colors, outline and position. Keep the English 'Chapter : Karura Itami' "
 "and all background artwork unchanged.")
JOBS["otv_ec5_1_bg.png"] = BASE_INSTR + NEON
JOBS["otv_ec5_2_bg.png"] = BASE_INSTR + NEON

# dm00 的输出要复制到的同图文件名（md5 同）
DM_SIBLINGS = ["otv_config.png","otv_loading.png"] + ["otv_dm%02d.png"%i for i in range(1,12)] + \
              ["otv_gm_bg%d.png"%i for i in range(2,7)]

def key():
    d = json.load(open(CFG, encoding="utf-8"))
    for r in d["config"]["providerConfigRules"]["providerRules"]:
        if r["providerId"] == "new-provider-2":
            return r["config"]["access"]["apiKey"]

def edits(png_path, prompt):
    boundary = uuid.uuid4().hex
    parts = []
    def field(name, val):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, name, val)).encode("utf-8"))
    field("model", "gpt-image-2.5-sunburst"); field("prompt", prompt)
    field("response_format", "b64_json"); field("n", "1"); field("size", "auto")
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\n"
                  "Content-Type: image/png\r\n\r\n" % (boundary, os.path.basename(png_path))).encode("utf-8"))
    parts.append(open(png_path, "rb").read())
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    req = urllib.request.Request(API + "/images/edits", data=b"".join(parts), method="POST",
        headers={"Authorization": "Bearer " + key(),
                 "Content-Type": "multipart/form-data; boundary=" + boundary,
                 "Accept": "application/json", "User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return ("ok", json.loads(r.read().decode("utf-8")), time.time()-t0)
    except urllib.error.HTTPError as e:
        return ("http%d" % e.code, e.read().decode("utf-8", "replace")[:150], time.time()-t0)
    except Exception as e:
        return ("err", repr(e)[:150], time.time()-t0)

def process(name, prompt):
    out_path = os.path.join(OUT1, name.replace(".png", "_cn.png"))
    if os.path.exists(out_path):
        return "skip"
    src = Image.open(os.path.join(SRC, name)).convert("RGBA")
    W, H = src.size
    S = 1024
    flat = Image.alpha_composite(Image.new("RGBA", (W, H), (255,255,255,255)), src).convert("RGB")
    ox, oy = (S-W)//2, (S-H)//2
    canvas = Image.new("RGB", (S, S), (255,255,255,255) if False else (255,255,255))
    canvas.paste(flat, (max(0,ox), max(0,oy)))
    sq = os.path.join(EV, "_sq_" + name); canvas.save(sq)
    for attempt in range(4):
        st, resp, dt = edits(sq, prompt)
        if st == "ok":
            raw = base64.b64decode(resp["data"][0]["b64_json"])
            tmp = os.path.join(EV, "_out_" + name)
            open(tmp, "wb").write(raw)
            im = Image.open(tmp).convert("RGB")
            sx, sy = im.width/float(S), im.height/float(S)
            # 反向映射回原图位（居中粘贴 → 居中裁回）
            cx0, cy0 = int(ox*sx), int(oy*sy)
            crop = im.crop((cx0, cy0, int(cx0 + W*sx), int(cy0 + H*sy))).resize((W, H), Image.LANCZOS)
            crop.save(out_path)
            os.remove(tmp)
            return "ok %.0fs out=%s" % (dt, im.size)
        time.sleep(30)
    return "FAIL " + st

if __name__ == "__main__":
    log = open(os.path.join(EV, "batch_log.txt"), "a", encoding="utf-8")
    for name, prompt in JOBS.items():
        r = process(name, prompt)
        line = "%s %s" % (name, r)
        print(line, flush=True); log.write(line + "\n"); log.flush()
    # dm 家族复制
    dm_src = os.path.join(OUT1, "otv_dm00_cn.png")
    if os.path.exists(dm_src):
        for s in DM_SIBLINGS:
            dst = os.path.join(OUT1, s.replace(".png", "_cn.png"))
            if not os.path.exists(dst):
                Image.open(dm_src).save(dst)
        log.write("dm family replicated x%d\n" % len(DM_SIBLINGS)); log.flush()
    print("ALL DONE", flush=True)
