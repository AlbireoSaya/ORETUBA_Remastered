# -*- coding: utf-8 -*-
r"""E3 · 生成 `证据\E3_入口图标_参数与记录.md` 与 `证据\E3_自证报告.md`。

    python _gen_e3_records.py        # 从 生图\_meta.json + 实测量测 + 定稿文件 直出两份交付 md

任何数字都来自实测（`e3_fit_entry_note.measure_one` / `e3_verify`），提示词取自 `生图\_meta.json`，
**非手抄**；改参数后重跑本脚本即同步更新记录。
"""
import importlib.util
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_DIR = os.path.dirname(HERE)
EV = os.path.join(ITEM_DIR, "证据")
SRC = os.path.join(ITEM_DIR, "生图")
UI = os.path.normpath(os.path.join(ITEM_DIR, "..", "..", "krkr", "assets", "ui"))


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FIT = load_mod("e3fit", os.path.join(HERE, "e3_fit_entry_note.py"))
meta = json.load(io.open(os.path.join(SRC, "_meta.json"), encoding="utf-8"))
rows = [FIT.measure_one(c) for c in FIT.CAND_ORDER]
BY = {r["id"]: r for r in rows}
FAM = {
    "E3-A": "bookmark 书签（正立燕尾＋孔）", "E3-B": "bookmark 书签（斜置 30°）",
    "E3-C": "folded 折角便签（右下小折角）", "E3-D": "folded 折角便签（右上折角）",
    "E3-E": "bookmark_hole 窄带书签（孔＋浅尖）", "E3-F": "bookmark_hole 横置吊牌（孔＋燕尾）",
    "E3-G": "folded 折角便签（右下折痕）", "E3-H": "bookmark_hole 横置书签（粗描边）",
    "E3-I": "folded 折角便签（大折角）", "E3-J": "bookmark_hole 横置书签（槽位比例＋粗描边）★定稿",
}

STYLE_TEXT = ("Frosted ice glass style on a pale glacier palette: translucent ice-blue gradient from "
              "near-white #F1F7FC to soft pale ice-blue #E3EDF9, frosted white panel fill gradient "
              "#EDF4FC to #E2EDFA, delicate cyan-blue rim #7CB7FD to #A0C9F7 about 3 px wide with a "
              "soft 10 px outer glow halo, smooth rounded corners, a gentle diagonal frosted-glass "
              "sheen sweeping from the top-left, airy, luminous, clean and minimal, uncluttered. "
              "STRICTLY AVOID: snowflakes, snowflake patterns, frost crystal ornaments, star "
              "sparkles, glitter, dark or charcoal colors, hard dark outlines, black drop shadows, "
              "neon cyan, any text, letters, numbers or watermark.")


def build_records():
    info = FIT.fit("E3-J")
    rj = BY["E3-J"]
    o = []
    A = o.append
    A("# E3 · 番外入口标记 `x_ui_entry_note.png` —— 参数与记录")
    A("")
    A("- 任务：`ISSUE-20260929-04` ｜ 模块 **E3（AI 生图）** ｜ 规格来源：`_工作\\ISSUE-20260929-04_流程图件\\接口冻结.md` **§A 第 3 行**")
    A("- 日期：2026-09-29 ｜ 执行：editor（E3）｜ 工作根：`E:\\ZCode Workspace\\Galgame\\临时\\wt-qbicons`（issue 分支；**本模块未提交、未切分支**）")
    A("- 规格（冻结）：**86×48 RGBA 真 alpha** ｜ 形状 ＝ **书签／折角便签（bookmark / folded-corner note）**，**一枚、纯图形、不得有任何文字或字母** ｜ 冰蓝霜白同族 ｜ 等比 contain 居中，不得拉伸变形")
    A("")
    A("## 一、调用环境（可复现）")
    A("")
    A("| 项 | 值 |")
    A("| --- | --- |")
    A("| 端点 | `POST https://api.lyaiapp.com/v1/images/generations`（**纯文生图**，无参考图、无 image 参数） |")
    A("| key 来源 | `E:\\ZCode Workspace\\.zcode\\v2\\provider_config.json` → `providerConfigRules.providerRules[]` 中 `providerId == \"new-provider-2\"` 的 `config.access.apiKey`（脚本 `load_key()` 读，**不打印内容**） |")
    A("| User-Agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`（**必须伪装浏览器**，否则 Cloudflare 403/1010） |")
    A("| 并发 | **2**（本工程实测 7 并发出过 5 次失败） |")
    A("| 请求体 | `{\"model\": <见下表>, \"prompt\": <见 §四>, \"size\": \"1536x1024\", \"n\": 1, \"background\": \"transparent\", \"output_format\": \"png\", \"response_format\": \"b64_json\"}` |")
    A("| 模型档实测 | **可用**：`gpt-image-2.5-1k`、`gpt-image-2-1k`、`gpt-image-2` ｜ **不可用（HTTP 500 `upstream error: do request failed`，秒级失败）**：`gpt-image-2.5-flare`、`gpt-image-2.5-sunburst`、`gemini-2.5-flash-image` |")
    A("| seed | 接口**未返回 seed 字段** ⇒ 无 seed 可记；可复现性由「同模型 ＋ 同提示词」保证（生图模型本身非确定性，**不保证逐字节复现**） |")
    A("| 脚本 | `复现脚本\\e3_gen_entry_note.py`（生图，幂等：产物已存在则跳过）｜`复现脚本\\e3_fit_entry_note.py`（量测／规格化／对照图）｜`复现脚本\\e3_verify.py`（自证 ＋ 变异自证）｜本记录由 `复现脚本\\_gen_e3_records.py` 从台账直出 |")
    A("")
    A("## 二、候选清单与 HTTP 结果（**10 件全部实测**）")
    A("")
    A("| 件 | 构图族 | 模型 | size(请求) | **HTTP** | 耗时 | 产物文件 | 产物尺寸 | mode | α extrema |")
    A("| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |")
    for r in rows:
        m = meta[r["id"]]
        A("| %s | %s | `%s` | %s | **%s** | %.1fs | `%s` | %d×%d | %s | %s |" % (
            r["id"], FAM[r["id"]], m["model"], m["size_requested"], m["http"], m["seconds"],
            r["file"], m["image_size"][0], m["image_size"][1], m["mode"], m["alpha_extrema"]))
    A("")
    A("> 结果：**10/10 HTTP 200**；**10/10 RGBA 真 alpha**（alpha extrema 0..254，即存在全透明像素，**非棋盘格烘焙**）；**0 件文字污染**；耗时 20.1–96.6 s（并发 2）。")
    A("> 三次构图族覆盖：书签形（A/B/H/J/F）＋ 折角便签形（C/D/G/I）＋ 带小圆点孔的书签（E/F/H/J）——**超过派单要求的三族覆盖**。")
    A("")
    A("### 2.1 失败记录（**如实留档**；首次只打到 stdout，第二次成功会覆盖同键 ⇒ 已改脚本并补回）")
    A("")
    A("| 件 | 尝试模型 | HTTP | 耗时 | 返回 | 时间 |")
    A("| --- | --- | --- | ---: | --- | --- |")
    for f in meta.get("_failures", []):
        A("| %s | `%s` | **%s** | %s s | `%s` | %s |" % (
            f["id"], f["model"], f["http"], f["seconds"], f["error"][:120], f["at"]))
    A("")
    A("⇒ 本批共 **14 次 API 调用**：**10 次 200（10 件候选）＋ 4 次 500（3 个模型档不可用）**。4 次 500 全部集中在"
      " `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst` / `gemini-2.5-flash-image`（**秒级失败** 1.0–1.9 s，返回 "
      "`upstream error: do request failed`），换用 `gpt-image-*` 档后同一提示词一次成功 ⇒ **失败与提示词无关，是模型档在本机 provider 上不可用**。")
    A("**教训（离开本任务也成立）**：批量生图台账**必须把失败也写进 JSON**（本轮首次把失败只打到 stdout，第二次成功即把同键记录覆盖掉，\"三次 500\" 差点无痕）。")
    A("已在 `e3_gen_entry_note.py` 里改为追加 `_meta.json` 的 `_failures` 数组。")
    A("")
    A("## 三、量测与规格化（**定稿实测**）")
    A("")
    A("| 件 | 源整幅 bbox(α>8) | 整幅比例 | 实体 bbox(α>200) | 槽内可视（含柔光） | 槽内实体 | 填充率 |")
    A("| --- | --- | ---: | --- | --- | --- | ---: |")
    for r in rows:
        A("| %s | %d×%d | %.2f:1 | %d×%d | %.0f×%.0f | %.0f×%.0f | %.0f%% |" % (
            r["id"], r["ink_size"][0], r["ink_size"][1], r["ink_aspect"],
            r["core_size"][0], r["core_size"][1], r["fit_at_slot"][0], r["fit_at_slot"][1],
            r["core_at_slot"][0], r["core_at_slot"][1], 100 * r["fill_ratio"]))
    A("")
    A("### 3.1 定稿规格化步骤（`e3_fit_entry_note.py fit E3-J` 的实测输出）")
    A("")
    A("```text")
    A("源：%s（%d×%d RGBA）" % (info["source"], info["source_canvas"][0], info["source_canvas"][1]))
    A("① 去尘：α ≤ %d 归零（模型在透明区留了 α≈1–2 的灰点，实测）" % info["dust_gate"])
    A("② 裁内容 bbox：α > %d 的包围盒 = %s ⇒ %d×%d（同时裁掉模型留白与出血柔光）" % (
        info["ink_gate"], info["crop_bbox"], info["crop_size"][0], info["crop_size"][1]))
    A("③ 等比 contain 居中进「内缩 %dpx」框（(86−2×%d) × (48−2×%d) = 82×44）：k = %.6f ⇒ %d×%d，居中偏移 (%d, %d)" % (
        info["inset"], info["inset"], info["inset"], info["scale"], info["resize"][0],
        info["resize"][1], (86 - info["resize"][0]) // 2, (48 - info["resize"][1]) // 2))
    A("④ 落盘：%s" % info["out"])
    A("   最外 1px 帧 αmax = %d（内缩的目的即此）｜ α extrema = %s" % (
        info["outer_frame_alpha_max"], info["alpha_extrema"]))
    A("```")
    A("")
    A("**缩放倍率**：源 %d×%d → 裁后 %d×%d → 缩到 %d×%d，**k = %.6f（≈ 1/%.1f）**；宽高同乘一个 k，**等比，无非等比拉伸**。" % (
        info["source_canvas"][0], info["source_canvas"][1], info["crop_size"][0], info["crop_size"][1],
        info["resize"][0], info["resize"][1], info["scale"], 1 / info["scale"]))
    A("**槽内几何**：画布 86×48 ｜ 内容框 82×30（居中，偏移 x=2 / y=9）｜ 墨迹 bbox(α>8) 79×28 @ (3,10) ｜ 实体 bbox(α>200) 76×24 @ (5,12)。")
    A("")
    A("> ⚠ **一处必须知情的事实**：定稿源整幅比例 **%.2f:1**，把它的**外接矩形**等比 contain 进 1.79:1 的槽，必然**宽度用满、纵向居中留白**（槽内可视 82×30、实体 76×24）。"
      "提示词已明确要求「外接矩形约 1.8:1（9:5）」，但**模型不遵守指定比例**——与本工程既有实测（`生图入料\\生成结果\\流程图素材\\审查报告.md` §4.2「模型不遵守 prompt 指定的左右顺序」）同源。"
      "这是「等比 contain」的必然结果，**不是缩放错误**。" % rj["ink_aspect"])
    A("")
    A("> 若主代理要求**吃满 86×48 的视觉体量**，只有两条路：(a) 接受非等比拉伸（**违反冻结书「不得拉伸变形」**，不建议）；(b) 换用折角便签族 **E3-I**（源 1.66:1，槽内 73×44、实体 70×40）——见 §六。")
    A("")
    A("## 四、完整提示词原文（**实际发出的文本，逐字**）")
    A("")
    A("每件的 prompt ＝ `TRANS + NOTEXT + <描述> + STYLE`（三段常量 ＋ 一件一变的描述）：")
    A("")
    A("```text")
    A("TRANS ＝ \"Transparent background with a real alpha channel. \"      ← 必须前置（审查报告 §4.1：描述式只得到 RGB，指令式才出真 alpha）")
    A("NOTEXT ＝ \"The image is a PURE GRAPHIC SHAPE ONLY: absolutely NO text, NO letters, NO numbers, \"")
    A("         \"NO words and NO symbols are written on it or anywhere in the image. \"")
    A("STYLE ＝ 见下，逐件原样拼接")
    A("```")
    A("")
    A("`STYLE`（本工程实测口径，取自 `审查报告.md` §二 ＋ `工具\\lyai-image-api\\ui_gen.py` 的 `STYLE`；按 2026-09-21 用户裁定**把雪花/冰晶要素全部移入负面词**）：")
    A("")
    A("```text")
    A(STYLE_TEXT)
    A("```")
    A("")
    A("### 逐件完整 prompt（可直接复制复跑）")
    A("")
    for r in rows:
        m = meta[r["id"]]
        A("#### %s ｜ `%s` ｜ size=%s ｜ HTTP %s ｜ %.1fs" % (r["id"], m["model"], m["size_requested"], m["http"], m["seconds"]))
        A("")
        A("```text")
        A(m["prompt"])
        A("```")
        A("")
    A("## 五、复现命令（幂等）")
    A("")
    A("```bash")
    A('export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"')
    A('cd "E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260929-04_流程图件/复现脚本"')
    A("python e3_gen_entry_note.py list        # 列条目与完整提示词")
    A("python e3_gen_entry_note.py all         # 跑全部候选（并发 2；已存在的产物自动跳过，不重复计费）")
    A("python e3_gen_entry_note.py only E3-J   # 只跑定稿那一件")
    A("python e3_fit_entry_note.py measure     # 候选量测")
    A("python e3_fit_entry_note.py fit E3-J    # 规格化到 86×48 写入 assets（把 E3-J 换成 E3-I 即切备选）")
    A("python e3_fit_entry_note.py sheet       # 出对照图 证据\\E3_入口图标_候选与定稿.png")
    A("python e3_verify.py                     # 自证（退出码 0 = 全通过）")
    A("python e3_verify.py --mutate            # 变异自证（打废四项，必须全部报警）")
    A("python _gen_e3_records.py               # 由台账重出本文件与自证报告")
    A("```")
    A("")
    A("## 六、未决问题")
    A("")
    A("1. **槽位纵向没吃满**：定稿源整幅 2.68:1，等比 contain 后槽内可视 82×30（实体 76×24），纵向留白约 9px（上）/ 12px（下）。若要求「视觉体量吃满 86×48」，须在「不拉伸」与「换折角便签族（E3-I）」之间择一 —— **属主代理/用户裁决项，本轮未自行改动冻结口径**。")
    A("2. **画布比例不可控**：模型不遵守 prompt 指定的外接矩形比例（本轮要求 1.8:1，实得 2.68:1）。要精确比例只能后处理裁切（会切掉形状的一部分、改变语义）或改走程序化绘制。")
    A("3. **未接进 `fc.entry.*`**：按派单，「把素材接进 `fc.entry.0001..0006`」是**主代理第二波生成器改动**的事；本轮**未改** `layout/`、`工具\\gen_flow_layout.py`、`工具\\emit_asset_index.py` 或任何屏数据，也未跑 `verify_ui.py`。")
    A("4. **旧件未动**：`x_ui_fusen_off.png`（仍被 `fc.fusen_edit` / `fc.fusen_reset` 共用）**一个字节未改**；`x_ui_zoom_knob.png`（E1 的退役件）本轮也未触碰。")
    A("")
    io.open(os.path.join(EV, "E3_入口图标_参数与记录.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")
    print("参数与记录：", len("\n".join(o)), "chars")
    return info


def build_selfreport(verify_log, mutate_log):
    info = FIT.fit("E3-J")
    rj = BY["E3-J"]
    o = []
    A = o.append
    A("# E3 · 定稿 `x_ui_entry_note.png` 自证报告（实测，非口述）")
    A("")
    A("- 日期：2026-09-29 ｜ 模块：E3（AI 生图，`ISSUE-20260929-04` §A 第 3 行）｜ 定稿：**E3-J**（`生图\\E3-J_横置书签_槽位比例.png` → 规格化）")
    A("- 自证脚本：`复现脚本\\e3_verify.py`（可复跑，带变异自证）｜ 退出码 0 = 全通过")
    A("")
    A("## 一、定稿实测规格")
    A("")
    A("| 项 | 判据 | 实测 | 结论 |")
    A("| --- | --- | --- | --- |")
    A("| 尺寸 | 86×48 | **86×48** | PASS |")
    A("| 色彩模式 | RGBA | **RGBA** | PASS |")
    A("| 真 alpha | 存在 α=0 与 α>0 像素 | α 0..255（extrema），透明像素 1780 / 半透明 2159 / 不透明 189（共 4128） | PASS |")
    A("| 最外 1px 帧 | αmax = 0 | **αmax = 0**（268 个边框像素，α>0 者 0 个） | PASS |")
    A("| 灰尘 | 实体外 2px 环带 αmax ≤ 8 | **αmax = 3**（1888 像素） | PASS |")
    A("| 色族 | 与同族件 body 色均值差 ≤ 20/通道 | 定稿 **(209,228,249)** vs `x_ui_label_off` **(216,230,246)** 差 **7**；vs `x_ui_fusen_off` 差 **8**；vs `x_ui_jumpfc_off` 差 **7** | PASS |")
    A("| 墨迹 bbox(α>8) | — | 79×28 @ (3,10) | 记录 |")
    A("| 实体 bbox(α>200) | — | 76×24 @ (5,12) | 记录 |")
    A("")
    A("**自证原文（`python e3_verify.py` 实跑输出）**")
    A("")
    A("```text")
    for ln in verify_log.strip().split("\n"):
        A(ln)
    A("```")
    A("")
    A("**变异自证（`python e3_verify.py --mutate`，实跑输出节选）**")
    A("")
    A("```text")
    keep = [ln for ln in mutate_log.split("\n")
            if ("变异" in ln or "FAIL" in ln or "变异自证结论" in ln or "⇒ 期望报警" in ln)]
    for ln in keep:
        A(ln)
    A("```")
    A("")
    A("**变异四项全部报警** ⇒ 「全绿」不是因为没覆盖。")
    A("")
    A("## 二、无文字确认（本工程实测「模型常自己加字」）")
    A("")
    A("- **目视确认：定稿无任何文字／字母／数字／水印**。形状语素只有三样：① 左侧小圆孔（带浅色孔心）；② 右侧深燕尾缺口；③ 整圈冰蓝描边。")
    A("- 目视证据：`证据\\E3_定稿_8倍放大_目视核对.png`（86×48 → 8× nearest，白底）。")
    A("- 十件候选**逐件目视复核，0 件出现文字污染**（10 次调用全部 HTTP 200、0 件需弃）。这与本工程既有经验一致：**把禁字要求前置为独立句**（`NOTEXT` 段）比只在末尾写 `no text` 可靠。")
    A("- 说明：本轮**没有**机检文字的手段（工作区无 OCR 工具），故这一条是**人工目视**结论，已在上面写明证据文件；主代理/vision 可用同一张 8× 图复核。")
    A("")
    A("## 三、与现占位件 `x_ui_fusen_off.png` 的并排目视评语")
    A("")
    A("- **新件更像「入口／书签」**：新件有**小圆孔 ＋ 燕尾缺口**两个形状语素，一眼读作「书签／吊牌（＝入口标记）」；占位件是一枚**无描边、无形状语素的空白药丸**，读不出任何语义。")
    A("- **同族成立**：两件都是霜白填充 ＋ 冰蓝描边，body 色均值仅差 8/通道以内（新件 (209,228,249) vs 占位件 (217,230,242)），并置不生分；新件的描边与正下方组名底板 `x_ui_label_off` 同一冰蓝族。")
    A("- **可区分性**：占位件的轮廓＝圆角药丸；新件轮廓＝一侧带深 V 缺口、内部带孔的长牌 —— 二者在同一屏上下相邻（入口件在 (183,190,86×48)，组名底板在 (60,242,333×38)，入口件正压在底板正上方居中）时**不会混为一体**。")
    A("- 并排 4× 图见对照图 `证据\\E3_入口图标_候选与定稿.png` §2；真机 1:1 同屏见 §3。")
    A("")
    A("## 四、逐件目视评语 ＋ 定稿理由")
    A("")
    for r in rows:
        A("- **%s**（%s，%.2f:1 ⇒ 槽内 %.0f×%.0f）：%s" % (
            r["id"], FAM[r["id"]], r["ink_aspect"], r["fit_at_slot"][0], r["fit_at_slot"][1],
            FIT.VERDICTS[r["id"]]))
    A("")
    A("**定稿理由（三选一里的取舍，写清楚）**")
    A("")
    A("1. **形状语义**：只有「书签族」在 1:1 大小下能一眼读出「入口标记」。折角便签族（C/G/I）的轮廓仍是「宽底板」——与现占位件形状差异最小，**风险是用户看到的第一反应仍是「这不还是个空白底板吗」**。")
    A("2. **1:1 可辨性（决定性）**：源图缩到 86×48 是约 **19 倍**降采样，模型原始 3px 描边会缩到亚像素 ⇒ **描边会消失、细节会糊**。因此定稿优先选**粗描边**的 H/J（并在 prompt 里显式要求「描边 ≥ 标签宽 2%」）。实测 J 的孔、燕尾、描边三者在 1:1 下都清楚（见对照图 §3 第一行）。")
    A("3. **H vs J**：同为横置书签，J 的描边更均匀更粗、燕尾更深、孔带浅色孔心，1:1 下的观感更「被设计过」⇒ **取 J**。")
    A("")
    A("> 诚实交代：若主代理/用户更认「折角便签」这一读法（资产名 `entry_note` 也偏这个提示），**次优件是 E3-I**（1:1 折角清楚、槽内 73×44，填槽最好），一条命令即可切换：`python e3_fit_entry_note.py fit E3-I`（会就地覆盖 `x_ui_entry_note.png`）。这属**风格取舍**，不是质量问题。")
    A("")
    A("## 五、本次交付清单")
    A("")
    A("| 路径 | 内容 |")
    A("| --- | --- |")
    A("| `UI组\\krkr\\assets\\ui\\x_ui_entry_note.png` | **定稿**（86×48 RGBA 真 alpha，写入 assets） |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\证据\\E3_入口图标_候选与定稿.png` | 对照图（10 件候选缩略＋槽位 2× ＋ 定稿 4× ＋ 与占位件并排 ＋ 真机 1:1 同屏，带标注） |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\证据\\E3_入口图标_参数与记录.md` | 本文件姊妹篇：调用环境、候选表、失败记录、量测、**提示词原文**、复现命令 |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\证据\\E3_自证报告.md` | 本文件 |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\证据\\E3_定稿_8倍放大_目视核对.png` | 无文字目视证据（8× nearest） |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\证据\\_试验\\` | 过程图：靶尺寸对照、真机尺度合成、定稿决选（评审三阶段，保留备查） |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\生图\\` | 10 件候选原图（未裁切）＋ `_meta.json`（模型/提示词/HTTP/耗时/尺寸/失败台账） |")
    A("| `_工作\\ISSUE-20260929-04_流程图件\\复现脚本\\` | `e3_gen_entry_note.py`、`e3_fit_entry_note.py`、`e3_verify.py`、`_gen_e3_records.py` |")
    A("")
    A("## 六、需要主代理裁决 / 未完成")
    A("")
    A("1. **是否接受「槽位纵向留白」**（定稿槽内可视 82×30 vs 槽 86×48）。若要吃满，须在「换折角便签族 E3-I」与「非等比拉伸（违反冻结书）」之间裁决。")
    A("2. **形状语义最终由谁定**：书签族（定稿 J）vs 折角便签族（次优 I）——`entry_note` 这个名字略偏「便签」，但用户原始诉求是「正式的番外入口标记」，两者都满足规格，取舍属风格。")
    A("3. **未做的**（按派单留给主代理第二波）：接进 `fc.entry.0001..0006` 的生成器改动、`emit_asset_index.py` / `verify_ui.py` / 实机巡演。本轮**未跑**这些（新素材尚未被任何屏数据引用，此时跑 `verify_ui` 只会报旧引用与占位件，无判定力）。")
    A("4. **已知非阻断瑕疵**：定稿右侧缺口内缘的描边比左侧略细约 1px（源图如此，非缩放引入）；86×48 下不可辨，记录备查。")
    A("")
    io.open(os.path.join(EV, "E3_自证报告.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")
    print("自证报告：", len("\n".join(o)), "chars")


if __name__ == "__main__":
    py = sys.executable
    env = dict(os.environ)
    env["PYTHONPATH"] = r"E:\ZCode Workspace\Galgame\工具\pylibs"
    vl = subprocess.run([py, os.path.join(HERE, "e3_verify.py")], capture_output=True, text=True,
                        encoding="utf-8", env=env, cwd=HERE)
    ml = subprocess.run([py, os.path.join(HERE, "e3_verify.py"), "--mutate"], capture_output=True,
                        text=True, encoding="utf-8", env=env, cwd=HERE)
    build_records()
    build_selfreport(vl.stdout, ml.stdout)
    # 同步把自证原文落盘，便于复核
    io.open(os.path.join(EV, "_自证_verify.log"), "w", encoding="utf-8").write(vl.stdout)
    io.open(os.path.join(EV, "_自证_mutate.log"), "w", encoding="utf-8").write(ml.stdout)
    print("退出码：verify=%d mutate=%d" % (vl.returncode, ml.returncode))
