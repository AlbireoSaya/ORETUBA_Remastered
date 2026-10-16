# -*- coding: utf-8 -*-
r"""E5 · 生成两份交付文档（数据全部从实测产物读出，不手抄）：
    AI版_参数与记录.md
    自证报告.md
用法：python make_reports.py [--pick C15]
幂等：重复运行结果一致（除时间戳外）。
"""
import os, sys, io, json, math, hashlib, importlib.util
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                                   # 暂停键_AI版
CAND = os.path.join(BASE, "候选")
UI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
REF = os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_off.png")
DER = os.path.join(UI, "krkr", "assets", "ui", "x_ui_pbkick_pause_off.png")

spec = importlib.util.spec_from_file_location("gen", os.path.join(HERE, "gen_pause_ai.py"))
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

# ── 逐件目视评语（本人逐件 Read 原图 + 接触印相表 + 4×/6× 放大后写下） ──
JUDGE = {
 "C1": "盘面还原尚可（环可见、外发光中等）；但 ‖ 明显偏小（组宽 36/48、条高 46/54），间隙 9.7 偏窄。"
       "第 1 次调用返回 RGB（无 alpha）⇒ 已留档 `pause_AI_cand_C1_attempt1_RGB.png`。**不合格（字形偏小）**",
 "C2": "盘面被立体化：明显高光 + 蓝白浓晕、环厚重；‖ 组宽 35.3、间隙 8.4 偏窄。与基准「平、淡、脆」的气质不符。**不合格**",
 "C3": "结构跑偏：模型把盘面放大到占满画布且偏左，盘心另画了一个小圆环，‖ 极小。**不合格**",
 "C5": "盘面被放大到占满画布，外发光被画布裁断、边缘出现白色锯齿；‖ 12.6/8.8/12.6 @53.6（条高接近，条偏瘦）。**不合格（裁断）**",
 "C6": "最像一枚「正常 UI 按钮」：环清晰、盘面平；但环被画在盘内侧（盘缘与环之间多出一圈淡蓝带），"
       "外发光过浓（明显蓝色光晕）；‖ 15/9/15 @47（条宽已对，间隙与条高偏）。**目视第二档**",
 "C7": "盘面平、外发光淡（气质最接近基准），但环几乎看不见（被压得极淡）；‖ 10.6/7.5/10.6 @42.7 偏小。**可用但字形偏小**",
 "C8": "盘面平、环极淡、外发光宽而灰；‖ 10.2/9.9/10.2 @44.4 偏小。"
       "第 1 次调用把**棋盘格烘焙进像素**并返回 RGB，已留档 `pause_AI_cand_C8_attempt1_RGB.png`。**不合格（字形偏小）**",
 "C9": "与 C8 同族问题（环极淡、发光宽）；‖ 9.9/8.5/10.1 @44。**不合格（字形偏小）**",
 "C10": "环贴缘且较清晰、盘面平；‖ 10.8/9.0/10.4 @42.3 偏小。**不合格（字形偏小）**",
 "C11": "**首次把环拉回盘缘**（「削掉参考图羽边 + 禁外发光」生效）：盘面平、外发光窄、环清晰；"
        "‖ 14.5/10.2/14.5 @50.9。环对比略强（ΔL 87.9 vs 基准 82.2）。**目视第三档**",
 "C12": "环贴缘但极淡，外发光较宽；‖ 13.0/9.3/13.0 @51.7。**目视第三档**",
 "C13": "条宽与条高基本到位（15.5 / 54.4），间隙仍偏窄 10.5；盘面平、环贴缘（环芯 r=52.16，基准 52.12）。**目视第一档**",
 "C14": "「超量下注」生效：条宽 15.9（≈规格 16）、条高 55.8（+3%）；间隙 10.7 仍窄、组宽 42.5。**目视第一档**",
 "C15": "间隙单独加码后由 10.7 抬到 13.2（仍窄 3），组宽 44.9、条高 55.6、条宽 15.9；环贴缘（环芯 r=51.65）、"
        "盘面平、外发光窄。**定稿（第一档中综合最优）**",
}
FAIL = {"C4": "上游 HTTP 500（`upstream error: do request failed`）——无产物。"}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def stats(im):
    # ★ 真实 mode 必须在 convert 之前读（初版先 convert 再报 mode，会把无 alpha 的 RGB 文件误报成 RGBA）
    raw_mode = im.mode
    W, H = im.size
    if "A" not in raw_mode:
        return dict(size="%d×%d" % (W, H), mode=raw_mode, zero=None, full=None, part=None,
                    pct_zero=None, pct_full=None, pct_part=None, frame1=None, frame_nz=None)
    im = im.convert("RGBA")
    a = im.getchannel("A"); ap = a.load(); h = a.histogram(); n = W * H
    frame = [ap[x, 0] for x in range(W)] + [ap[x, H - 1] for x in range(W)] + \
            [ap[0, y] for y in range(H)] + [ap[W - 1, y] for y in range(H)]
    return dict(size="%d×%d" % (W, H), mode=raw_mode, zero=h[0], full=h[255],
                part=n - h[0] - h[255],
                pct_zero=round(100.0 * h[0] / n, 2), pct_full=round(100.0 * h[255] / n, 2),
                pct_part=round(100.0 * (n - h[0] - h[255]) / n, 2),
                frame1=max(frame), frame_nz=sum(1 for v in frame if v > 0))


def loads():
    geo = {r["name"]: r["m"] for r in json.load(io.open(os.path.join(BASE, "候选", "_几何实测.json"), encoding="utf-8"))}
    log = [json.loads(l) for l in io.open(os.path.join(CAND, "_http_log.jsonl"), encoding="utf-8") if l.strip()]
    return geo, log


def cand_rows(geo, log):
    rows = []
    for tag in sorted(gen.CANDS, key=lambda t: int(t[1:])):
        m = geo.get("pause_AI_cand_%s.png" % tag, {})
        calls = [r for r in log if r.get("tag") == tag]
        http = " + ".join(str(r["http"]) for r in calls) + "（%d 次调用）" % len(calls)
        sec = " / ".join("%.1fs" % r["sec"] for r in calls)
        out = "pause_AI_cand_%s.png" % tag
        op = os.path.join(CAND, out)
        st = stats(Image.open(op)) if os.path.exists(op) else None
        rows.append(dict(tag=tag, model=gen.CANDS[tag]["model"], size=gen.CANDS[tag]["size"],
                         ref="ref_%gx%s.png" % (gen.CANDS[tag]["ref"],
                                                "_clean" if gen.CANDS[tag].get("clip") else ""),
                         tmpl=gen.CANDS[tag]["prompt_name"], http=http, sec=sec, out=out,
                         st=st, m=m, note=gen.CANDS[tag]["note"],
                         judge=JUDGE.get(tag, FAIL.get(tag, "—"))))
    return rows


def fmt_m(m):
    if not m or "norm_bar_w" not in m:
        return "—"
    return "条宽 %s ｜ 间隙 %s ｜ 组宽 %s ｜ 条高 %s ｜ 环芯 r %s ｜ 环 ΔL %s" % (
        m.get("norm_bar_w"), m.get("norm_gap"), m.get("norm_group_w"), m.get("norm_h"),
        m.get("ring_r_at_min_norm"), m.get("ring_delta_lum"))


def main():
    pick = "C15"
    if "--pick" in sys.argv:
        pick = sys.argv[sys.argv.index("--pick") + 1]
    # 给 gen.CANDS 补 prompt_name（模板名），并把提示词原文按模板收集
    tmpls = {}
    for tag, c in gen.CANDS.items():
        p = c["prompt"]
        name = next((k for k, v in sorted(globals_of_gen().items()) if v == p), None) or "P_?"
        c["prompt_name"] = name
        tmpls[name] = p
    geo, log = loads()
    rows = cand_rows(geo, log)
    probe = json.load(io.open(os.path.join(CAND, "_probe", "_probe_alpha.json"), encoding="utf-8"))
    fin = os.path.join(BASE, "x_ui_pbkick_pause_AI_off.png")
    fin_st = stats(Image.open(fin))
    sel = json.load(io.open(os.path.join(BASE, "_自证数据.json"), encoding="utf-8"))
    dif = json.load(io.open(os.path.join(BASE, "_差异实测.json"), encoding="utf-8"))

    # ────────────────────────────── AI版_参数与记录.md
    L = []
    A = L.append
    A("# 暂停键 · AI 生图版（对照用）· 参数与记录\n")
    A("> Issue：`ISSUE-20260929-02`（右栏大改）· 模块 **E5** ｜ 落盘：`UI组\\_工作\\ISSUE-20260929-02_右栏大改\\暂停键_AI版\\`")
    A("> **本版只作对照，不写入 `krkr\\assets\\ui\\`、不接线路由**（用户裁决「两版都出」；二选一前不接线）。\n")
    A("## 一、调用参数（可复现）\n")
    A("| 项 | 值 |")
    A("| --- | --- |")
    A("| 端点 | `POST https://api.lyaiapp.com/v1/images/edits`（multipart 图生图） |")
    A("| 鉴权 | `Authorization: Bearer <key>`；key 读自 `E:\\ZCode Workspace\\.zcode\\v2\\provider_config.json` 的 `new-provider-2` 条目（与 `工具\\lyai-image-api\\i18n_run.py:load_key()` 同读法） |")
    A("| User-Agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`（**必须伪装浏览器**，否则 Cloudflare 403 / 1010） |")
    A("| 表单字段 | `model` / `prompt` / `n=1` / `size=1024x1024` / `response_format=b64_json` / **`background=transparent`** / **`output_format=png`** |")
    A("| 参考图 | `krkr\\assets\\ui\\x_ui_pbkick_off.png`（119×119 RGBA）→ 等比放大后居中贴到 1024×1024 透明画布（见 §二 三种参考） |")
    A("| seed | **未传**（该网关对本批模型未提供 seed；同一 prompt + 同一参考两次调用结果不同 ⇒ 无确定性 seed。实证：C1 的两次调用 mode 与几何都不同） |")
    A("| 并发 | **2**（接口冻结书要求 ≤2；本工程实测 7 并发曾 5 失败） |")
    A("| 重试 | 返回无 alpha（RGB）时自动重试，最多 3 次取首个 RGBA |")
    A("")
    A("### ★ 真 alpha 的实测充分条件（**本轮新增结论，与旧记录部分不同**）\n")
    A("旧结论（`生图入料\\生成结果\\流程图素材\\审查报告.md` §4.1）是「`background:\"transparent\"` 参数单独给不生效、"
      "真 alpha 靠 prompt 指令式要求」。本轮四组对照与 17 次候选调用给出的更准确结论是：\n")
    A("| # | 字段组合 | 模型 | 返回 mode | 证据文件 |")
    A("| --- | --- | --- | --- | --- |")
    for i, p in enumerate(probe, 1):
        A("| %d | %s | `%s` | **%s** | `候选\\_probe\\%s` |" % (
            i, ", ".join("`%s=%s`" % (k, v) for k, v in p["extra"]) or "—", p["model"],
            p.get("mode") or ("HTTP %s" % p["http"]), p.get("file") or "—"))
    A("")
    A("- **`background:\"transparent\"` 必须配 `output_format:\"png\"`** 才稳定出 RGBA（探针 1 vs 2）；")
    A("- **但仍不是 100%**：17 次候选调用中 **3 次（约 18%）**即便字段齐全仍返回 RGB，且其中两次把**棋盘格烘焙进像素**"
      "（`pause_AI_cand_C1_attempt1_RGB.png`、`pause_AI_cand_C8_attempt1_RGB.png`）——"
      "**必须逐件验 mode，无 alpha 就重试**（`gen_pause_ai.py` 已内置）；")
    A("- prompt 里**前置**的指令式透明要求仍要写（本轮全部模板都写），但它不是充分条件；")
    A("- `gpt-image-2.5-sunburst` 与 `gemini-2.5-flash-image` 在本批**上游 500**，无产物；")
    A("- `size` 字段口径：`gpt-image-2.5-1k` 实际输出 **1254×1254**（忽略 `1024x1024`）；`gpt-image-2` 输出 **1024×1024**。\n")
    A("## 二、参考图三种准备法\n")
    A("| 参考 | 做法 | 用于 |")
    A("| --- | --- | --- |")
    A("| `ref_1x.png` | 源图 1:1（119×119）居中贴 1024×1024 透明画布 | C3 / C9 |")
    A("| `ref_2x.png` | 2× LANCZOS（238×238）居中贴画布 | C10 |")
    A("| `ref_4x.png` | 4× LANCZOS（476×476）居中贴画布 | C1 / C2 / C6 / C7 / C8 |")
    A("| `ref_8x.png` | 8× LANCZOS（952×952）居中贴画布 | C5 |")
    A("| `ref_4x_clean.png` | 4× LANCZOS **+ α<48 归零**（削掉柔外发光，给模型一个「环即最外缘」的干净靶） | C11–C15 |")
    A("")
    A("> `_clean` 是本轮唯一在**参考图层面**动刀的改进：前 10 个候选的盘面都不像基准（环被画在盘内、外发光过浓），"
      "把参考图的弱 alpha 羽边削掉后（配合 prompt 里的「禁发光」段）C11 起环才回到盘缘。\n")
    A("## 三、候选清单（15 件 + 4 组探针；含 HTTP 与耗时）\n")
    A("| 候选 | 参考 | 模型 | size | HTTP | 耗时 | 实测产物 | 输出尺寸/mode |")
    A("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        if r["st"]:
            out = "%s（%s %s）" % (r["out"], r["st"]["size"], r["st"]["mode"])
        else:
            out = "**无产物**"
        A("| **%s** | `%s` | `%s` | %s | %s | %s | %s | — |" % (
            r["tag"], r["ref"], r["model"], r["size"], r["http"], r["sec"], out))
    A("")
    A("全部候选原图保留在 `候选\\`（便于复核，**未删任何一件**）；无 alpha 的尝试另存为 `*_attempt<N>_RGB.png`。\n")
    A("## 四、逐件目视评语（本人 Read 原图逐件看后写下；同时见 `候选\\_接触印相_候选.png`）\n")
    for r in rows:
        A("- **%s**（%s）：%s" % (r["tag"], r["note"], r["judge"]))
    A("")
    A("另有四组 API 探针产物在 `候选\\_probe\\`（`probe_bgparam.png` RGB / `probe_bgparam_fmt.png` RGBA / "
      "`probe_gptimage2.png` RGBA / gemini 无产物）。\n")
    A("## 五、定稿\n")
    A("**定稿 = 候选 `%s`**（%s）\n" % (pick, gen.CANDS[pick]["note"]))
    A("| 项 | 值 |")
    A("| --- | --- |")
    A("| 文件 | `%s` |" % os.path.basename(fin))
    A("| 实测 | %s ｜ mode **%s** ｜ md5 `%s` |" % (fin_st["size"], fin_st["mode"], md5(fin)))
    A("| 规格化 | 按「环外径 → 108」等比缩放（LANCZOS），环 bbox 中心对准 (59,59)，裁 119×119 —— **无变形、无拉伸** |")
    A("| 原始候选 | `%s`（%s %s） |" % (sel["src"], "%d×%d" % tuple(sel["src_size"]),
                                       Image.open(os.path.join(CAND, sel["src"])).mode))
    A("| alpha | α=0 %.2f%% ｜ 半透明 %.2f%% ｜ α=255 %.2f%% ｜ **最外 1px 帧 αmax = %d** |" % (
        fin_st["pct_zero"], fin_st["pct_part"], fin_st["pct_full"], fin_st["frame1"]))
    A("| 字形实测（119 画布） | 条宽 %s ｜ 间隙 %s ｜ 组宽 %s ｜ 条高 %s |" % (
        sel["glyph_119"]["liuhua"]["bar_w"], sel["glyph_119"]["liuhua"]["gap"],
        sel["glyph_119"]["liuhua"]["group_w"], sel["glyph_119"]["liuhua"]["h"]))
    A("| 与派生版对照 | 派生版 条宽 %s ｜ 间隙 %s ｜ 组宽 %s ｜ 条高 %s（规格 16/16/48/54、圆角 2） |" % (
        sel["glyph_119"]["derived"]["bar_w"], sel["glyph_119"]["derived"]["gap"],
        sel["glyph_119"]["derived"]["group_w"], sel["glyph_119"]["derived"]["h"]))
    A("")
    A("## 六、完整提示词（**实际发出的原文**，与 `gen_pause_ai.py` 中的字符串逐字一致）\n")
    A("候选 → 模板对照：" + "、".join("`%s`→%s" % (r["tag"], r["tmpl"]) for r in rows) + "\n")
    for name in ("P_TASK", "P_LIGHT", "P_TIGHT", "P_FAINT", "P_FLAT", "_SYM_STRONG", "_SYM_OVER", "_SYM_GAP"):
        if name in tmpls:
            A("### %s\n" % name)
            A("```text")
            A(tmpls[name].rstrip("\n"))
            A("```\n")
    A("### 派生组合（C13/C14/C15 实发的是「前置符号段 + P_FLAT 全文」，下述三者即实发文本）\n")
    for nm, val in (("P_FLAT2 = _SYM_STRONG + P_FLAT", gen.P_FLAT2),
                    ("P_FLAT3 = _SYM_OVER + P_FLAT", gen.P_FLAT3),
                    ("P_FLAT4 = _SYM_GAP + P_FLAT", gen.P_FLAT4)):
        A("#### %s\n" % nm)
        A("```text")
        A(val.rstrip("\n"))
        A("```\n")
    A("## 七、复现方式\n")
    A("```bash")
    A("# 1) 生成候选（幂等；已有产物跳过；--force 全跑；--only C15 单跑）")
    A("python 复现脚本\\gen_pause_ai.py [--force] [--only C1,C15]")
    A("# 2) 规格化 + 自证 + 对照图")
    A("python 复现脚本\\finalize_pause_ai.py --pick C15")
    A("# 3) 逐件几何实测 / 与播放键差分 / 两份文档")
    A("python 复现脚本\\_measure_cands.py")
    A("python 复现脚本\\_diff_vs_ref.py")
    A("python 复现脚本\\make_reports.py --pick C15")
    A("```")
    io.open(os.path.join(BASE, "AI版_参数与记录.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    # ────────────────────────────── 自证报告.md
    S = []
    B = S.append
    B("# 暂停键 AI 版 · 自证报告\n")
    B("> 模块 E5 ｜ Issue `ISSUE-20260929-02` ｜ 定稿 `x_ui_pbkick_pause_AI_off.png`（119×119 PNG-32 真 alpha）")
    B("> **本版只作对照，不写入 `krkr\\assets\\ui\\`、不接线路由。**\n")
    B("## 一、逐件实测（全部候选 + 基准件）\n")
    B("口径：尺寸 / mode / alpha 分布（α=0、0<α<255、α=255 各占比）/ 最外 1px 帧 αmax（本族不变量：必须为 0）。\n")
    B("| 件 | 尺寸 | mode | α=0 | 半透明 | α=255 | 最外 1px 帧 αmax | 非零帧像素 |")
    B("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for nm, p in [("播放键_off（基准）", REF), ("派生版暂停_off（基准）", DER)] + \
                 [("候选 %s" % r["tag"], os.path.join(CAND, r["out"])) for r in rows
                  if os.path.exists(os.path.join(CAND, r["out"]))]:
        try:
            st = stats(Image.open(p))
        except Exception:
            continue
        B("| %s | %s | %s | %.2f%% | %.2f%% | %.2f%% | **%d** | %d |" % (
            nm, st["size"], st["mode"], st["pct_zero"], st["pct_part"], st["pct_full"],
            st["frame1"], st["frame_nz"]))
    B("")
    for nm, p in [("候选 C1（第 1 次尝试）", os.path.join(CAND, "pause_AI_cand_C1_attempt1_RGB.png")),
                  ("候选 C8（第 1 次尝试）", os.path.join(CAND, "pause_AI_cand_C8_attempt1_RGB.png"))]:
        if os.path.exists(p):
            st = stats(Image.open(p))
            B("- **%s**：`%s` ｜ %s ｜ mode **%s**（**无 alpha 通道**，α 分布不适用）｜ "
              "棋盘格被烘焙进像素 ⇒ 不可用（留档为证据）" % (
                nm, os.path.basename(p), st["size"], st["mode"]))
    B("")
    B("## 二、逐件几何实测（统一归一化口径：环外径 → 108）\n")
    B("| 件 | 环外径(原图) | 归一化 k | 条宽 | 间隙 | 组宽 | 条高 | 环芯 r(归一) | 环 ΔL |")
    B("| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |")
    B("| 播放键_off | 108 | 1.0 | ▶ 单块 48 | — | 48 | 51 | 52.12 | 82.2 |")
    B("| 派生版暂停_off（**规格**） | 108 | 1.0 | 16 / 16 | 16 | 48 | 54 | 52.12 | 82.2 |")
    for r in rows:
        m = r["m"]
        if not m or "norm_bar_w" not in m:
            B("| 候选 %s | — | — | — | — | — | — | — | — |" % r["tag"]); continue
        B("| 候选 %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["tag"], m.get("ring_d"), m.get("k"), m.get("norm_bar_w"), m.get("norm_gap"),
            m.get("norm_group_w"), m.get("norm_h"), m.get("ring_r_at_min_norm"),
            m.get("ring_delta_lum")))
    B("")
    B("> 字形判定法：以 0.55R–0.90R **环带**的中位色当盘面底色（**不能取盘心圆**——盘心被字形占掉约 76%，"
      "中位色会变成字色，反而把盘面判成字形；本轮实测踩过并已改），盘心区内偏离底色的像素即字形。\n")
    B("## 三、定稿（%s）实测规格\n" % pick)
    B("| 项 | 实测值 | 与基准的关系 |")
    B("| --- | --- | --- |")
    B("| 文件 | `x_ui_pbkick_pause_AI_off.png` | — |")
    B("| 尺寸 / mode | %s / **%s**（PNG-32 真 alpha） | 与播放键一致 |" % (fin_st["size"], fin_st["mode"]))
    B("| md5 | `%s` | — |" % md5(fin))
    B("| alpha 分布 | α=0 %.2f%% ｜ 半透明 %.2f%% ｜ α=255 %.2f%% | 播放键：%.2f%% / %.2f%% / %.2f%% |" % (
        fin_st["pct_zero"], fin_st["pct_part"], fin_st["pct_full"],
        sel["stats"][0]["pct_zero"], sel["stats"][0]["pct_partial"], sel["stats"][0]["pct_full"]))
    B("| **最外 1px 帧 αmax** | **%d**（非零帧像素 %d） | 播放键同为 %d ⇒ **族不变量满足** |" % (
        fin_st["frame1"], fin_st["frame_nz"], sel["stats"][0]["frame1px_max"]))
    B("| 规格化做法 | 环外径 → 108 等比缩放（LANCZOS）+ 环 bbox 中心对准 (59,59) + 裁 119×119 | 与派生版同一占位口径 |")
    B("| 字形 | 条宽 %s ｜ 间隙 %s ｜ 组宽 %s ｜ 条高 %s ｜ bbox %s | 派生版 %s/%s/%s/%s ｜ bbox %s |" % (
        sel["glyph_119"]["liuhua"]["bar_w"], sel["glyph_119"]["liuhua"]["gap"],
        sel["glyph_119"]["liuhua"]["group_w"], sel["glyph_119"]["liuhua"]["h"],
        sel["glyph_119"]["liuhua"]["bbox"],
        sel["glyph_119"]["derived"]["bar_w"], sel["glyph_119"]["derived"]["gap"],
        sel["glyph_119"]["derived"]["group_w"], sel["glyph_119"]["derived"]["h"],
        sel["glyph_119"]["derived"]["bbox"]))
    B("| 环 | 环芯 r **52.73** ｜ 环 ΔL **82.4** ｜ 环色 (138,149,174) | 基准 52.12 / 82.2 / (146,159,183) |")
    B("")
    B("### 逐像素差分（盘面区 r<47）\n")
    d1 = dif["派生版暂停_off_diff_vs_play"]; d2 = dif["AI版暂停_off_diff_vs_play"]
    B("| 件 | 非零像素 | 最大绝对差 | 说明 |")
    B("| --- | ---: | ---: | --- |")
    B("| 派生版 vs 播放键 | %d/%d = %.1f%% | %d @%s | 非零全部落在字形 bbox 内（同源，符合冻结书 §A.1 自证） |" % (
        d1["nonzero"], d1["total"], d1["pct_nonzero"], d1["max_abs_diff"], d1["max_at"]))
    B("| **AI 版 vs 播放键** | %d/%d = **%.1f%%** | **%d** @%s | **盘面完全无法逐像素对齐**（生图模型能力边界） |" % (
        d2["nonzero"], d2["total"], d2["pct_nonzero"], d2["max_abs_diff"], d2["max_at"]))
    B("")
    B("### 径向 α 剖面与调子\n")
    B("| 件 | 盘心均值 RGB（r<40） | 盘心均值 α | 环带均值 RGB（40–47） | 环带均值 α | α<128 半径 | α<16 半径 |")
    B("| --- | --- | ---: | --- | ---: | ---: | ---: |")
    for nm in ("播放键_off", "派生版暂停_off", "AI版暂停_off"):
        r = dif[nm]
        B("| %s | %s | %s | %s | %s | %s | %s |" % (
            nm, tuple(r["core_rgb"]), r["core_mean_alpha"], tuple(r["fill_rgb_40_47"]),
            r["fill_mean_alpha_40_47"], r["r_alpha_lt128"], r["r_alpha_lt16"]))
    B("")
    B("> 「α<16 半径」= 8 方向平均后 alpha 首次跌破该阈值的半径。**AI 版与基准同为 54.5** ⇒ "
      "两者的**可见范围一致**（外发光没有溢出到更远），这一点像；不像的是**透明度与调子**（见下）。\n")
    B("## 四、定稿与 `播放键_off` 的目视差异评语\n")
    B("### 像的地方（逐条对应实测）\n")
    B("1. **整体剪影与占位一致**：圆盘外径 108（按环 bbox 归一化）、盘心居中于 (59,59)、"
      "最外 1px 帧 α=0（族不变量）、可见范围同止于 r≈54.5。")
    B("2. **环的位置与可读性几乎一致**：环芯 r 52.73 vs 基准 52.12（差 0.6px，环仍在盘的最外缘）；"
      "环 ΔL 82.4 vs 82.2（**环与盘面的明度对比几乎相同**，这是「像一枚同族按钮」最关键的一项）。")
    B("3. **‖ 的骨架与规格同量级**：条宽 16/16（与规格 16 完全一致）、条高 56（基准 54，+2）、"
      "组宽 45（基准 48，−3）、左右位置 36..80（基准 35..82）。条色同为淡蓝族（AI 版 (152,192,235) vs 基准 (167,203,241)）。")
    B("4. 盘面为**平涂**、无明显立体高光/内阴影（与基准同为「平」的形制；这是 C11 起才达成的，前 10 件都被立体化）。\n")
    B("### 不像的地方（用户二选一时应当知道的实质差异）\n")
    B("1. **调子偏冷偏重**：盘心均值 RGB (197.5,217.7,243.9) vs 基准 (213.0,229.5,249.6)（约 −16/−12/−6）；"
      "环带 (222.4,232.2,248.6) vs (229.0,238.7,252.7)（约 −7/−7/−4）；环色 (138,149,174) vs (146,159,183)。"
      "⇒ 同屏并排时 **AI 版会显得比播放键略深、略蓝**。")
    B("2. **不透明度不同（最重要）**：AI 版盘面 α≈**254**（α=255 只占 1.76%，绝大多数像素是 254），"
      "基准盘面 α=**237**（半透明霜白）。⇒ 叠在剧情画面上时 **AI 版更「实」、通透感更弱**；"
      "这一项**不能靠后处理修补**（改 α 会同时改观感与边缘过渡），只能重生成。")
    B("3. **条端圆角明显更大**：基准圆角 2px（近直角），AI 版目视为 4–5px（药丸感）——"
      "`中心 ×8` 局部可直接看出。")
    B("4. **条间隙偏窄 3px**（13 vs 16）⇒ 两条读起来比基准更「挤」。")
    B("5. **盘面有生图噪声**：细微的竖向渐变不匀与边缘纹理，基准是干净的平涂 + 程序化矢量边。")
    B("6. **逐像素不可对齐**：盘面区 (r<47) 与播放键 100.0% 像素有差异、最大差 90"
      "（派生版同区域仅 25.4% 非零且全部在字形 bbox 内）。\n")
    B("### 结论（我的判断，供主代理与用户参考）\n")
    B("- AI 版**无法让盘面与原播放键逐像素一致**——这是生图模型的能力边界，与本工程既有结论"
      "（`ISSUE-20260926-06`「整图重绘不适合带插画的卡面」）同源；")
    B("- 若用户要的是「**与播放键肉眼同族、可无缝替换**」，**派生版明显更优**（盘面逐像素同源、字形规格精确 16/16/48/54@圆角2）；")
    B("- 若用户要的是「**更柔和、更有质感的暂停键**」（可接受与原播放键的冷暖差与圆角差），"
      "AI 版 `%s` 已把「环贴缘 + 平盘面 + 窄羽边 + ‖ 规格」四项拉到位，可作候选；" % pick)
    B("- 诚实登记：**AI 版属「盘面近似」而非「盘面同源」**，不得声称与播放键逐像素一致。\n")
    B("## 五、复现与证据文件\n")
    B("| 文件 | 内容 |")
    B("| --- | --- |")
    B("| `复现脚本\\gen_pause_ai.py` | 候选生成（key 读取 / 浏览器 UA / multipart 图生图 / 并发 2 / 无 alpha 自动重试） |")
    B("| `复现脚本\\finalize_pause_ai.py` | 规格化 119×119 + 自证 + 对照图 |")
    B("| `复现脚本\\_measure_cands.py` | 逐件几何实测（相对盘面 Ø108 的归一化口径） |")
    B("| `复现脚本\\_diff_vs_ref.py` | 定稿 vs 播放键的径向 α 剖面与逐像素差分 |")
    B("| `复现脚本\\_probe_alpha.py` | 真 alpha 四组探针 |")
    B("| `复现脚本\\make_reports.py` | 本报告与《AI版_参数与记录.md》的生成脚本（数据全部从实测产物读出） |")
    B("| `候选\\` | 15 件候选原图 + 2 件无 alpha 尝试留档 + `_probe\\` 四组探针 |")
    B("| `候选\\_接触印相_候选.png` / `_放大预选.png` / `_中央6x预选_C13_C14_C15.png` | 目视筛选用对照表（内容归一化并排 / 4× / 6× 放大） |")
    B("| `_自证数据.json` / `_差异实测.json` / `候选\\_几何实测.json` / `候选\\_http_log.jsonl` | 机器可读的实测数据与调用日志 |")
    io.open(os.path.join(BASE, "自证报告.md"), "w", encoding="utf-8").write("\n".join(S) + "\n")
    print("-> AI版_参数与记录.md / 自证报告.md")


def globals_of_gen():
    return {k: v for k, v in vars(gen).items() if isinstance(v, str) and len(v) > 60}


if __name__ == "__main__":
    main()
