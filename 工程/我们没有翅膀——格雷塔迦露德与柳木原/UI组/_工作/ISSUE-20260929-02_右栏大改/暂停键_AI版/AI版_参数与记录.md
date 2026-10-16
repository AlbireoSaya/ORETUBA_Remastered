# 暂停键 · AI 生图版（对照用）· 参数与记录

> Issue：`ISSUE-20260929-02`（右栏大改）· 模块 **E5** ｜ 落盘：`UI组\_工作\ISSUE-20260929-02_右栏大改\暂停键_AI版\`
> **本版只作对照，不写入 `krkr\assets\ui\`、不接线路由**（用户裁决「两版都出」；二选一前不接线）。

## 一、调用参数（可复现）

| 项 | 值 |
| --- | --- |
| 端点 | `POST https://api.lyaiapp.com/v1/images/edits`（multipart 图生图） |
| 鉴权 | `Authorization: Bearer <key>`；key 读自 `E:\ZCode Workspace\.zcode\v2\provider_config.json` 的 `new-provider-2` 条目（与 `工具\lyai-image-api\i18n_run.py:load_key()` 同读法） |
| User-Agent | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`（**必须伪装浏览器**，否则 Cloudflare 403 / 1010） |
| 表单字段 | `model` / `prompt` / `n=1` / `size=1024x1024` / `response_format=b64_json` / **`background=transparent`** / **`output_format=png`** |
| 参考图 | `krkr\assets\ui\x_ui_pbkick_off.png`（119×119 RGBA）→ 等比放大后居中贴到 1024×1024 透明画布（见 §二 三种参考） |
| seed | **未传**（该网关对本批模型未提供 seed；同一 prompt + 同一参考两次调用结果不同 ⇒ 无确定性 seed。实证：C1 的两次调用 mode 与几何都不同） |
| 并发 | **2**（接口冻结书要求 ≤2；本工程实测 7 并发曾 5 失败） |
| 重试 | 返回无 alpha（RGB）时自动重试，最多 3 次取首个 RGBA |

### ★ 真 alpha 的实测充分条件（**本轮新增结论，与旧记录部分不同**）

旧结论（`生图入料\生成结果\流程图素材\审查报告.md` §4.1）是「`background:"transparent"` 参数单独给不生效、真 alpha 靠 prompt 指令式要求」。本轮四组对照与 17 次候选调用给出的更准确结论是：

| # | 字段组合 | 模型 | 返回 mode | 证据文件 |
| --- | --- | --- | --- | --- |
| 1 | `background=transparent` | `gpt-image-2.5-1k` | **RGB** | `候选\_probe\probe_bgparam.png` |
| 2 | `background=transparent`, `output_format=png` | `gpt-image-2.5-1k` | **RGBA** | `候选\_probe\probe_bgparam_fmt.png` |
| 3 | `background=transparent` | `gpt-image-2` | **RGBA** | `候选\_probe\probe_gptimage2.png` |
| 4 | `background=transparent` | `gemini-2.5-flash-image` | **HTTP 500** | `候选\_probe\—` |

- **`background:"transparent"` 必须配 `output_format:"png"`** 才稳定出 RGBA（探针 1 vs 2）；
- **但仍不是 100%**：17 次候选调用中 **3 次（约 18%）**即便字段齐全仍返回 RGB，且其中两次把**棋盘格烘焙进像素**（`pause_AI_cand_C1_attempt1_RGB.png`、`pause_AI_cand_C8_attempt1_RGB.png`）——**必须逐件验 mode，无 alpha 就重试**（`gen_pause_ai.py` 已内置）；
- prompt 里**前置**的指令式透明要求仍要写（本轮全部模板都写），但它不是充分条件；
- `gpt-image-2.5-sunburst` 与 `gemini-2.5-flash-image` 在本批**上游 500**，无产物；
- `size` 字段口径：`gpt-image-2.5-1k` 实际输出 **1254×1254**（忽略 `1024x1024`）；`gpt-image-2` 输出 **1024×1024**。

## 二、参考图三种准备法

| 参考 | 做法 | 用于 |
| --- | --- | --- |
| `ref_1x.png` | 源图 1:1（119×119）居中贴 1024×1024 透明画布 | C3 / C9 |
| `ref_2x.png` | 2× LANCZOS（238×238）居中贴画布 | C10 |
| `ref_4x.png` | 4× LANCZOS（476×476）居中贴画布 | C1 / C2 / C6 / C7 / C8 |
| `ref_8x.png` | 8× LANCZOS（952×952）居中贴画布 | C5 |
| `ref_4x_clean.png` | 4× LANCZOS **+ α<48 归零**（削掉柔外发光，给模型一个「环即最外缘」的干净靶） | C11–C15 |

> `_clean` 是本轮唯一在**参考图层面**动刀的改进：前 10 个候选的盘面都不像基准（环被画在盘内、外发光过浓），把参考图的弱 alpha 羽边削掉后（配合 prompt 里的「禁发光」段）C11 起环才回到盘缘。

## 三、候选清单（15 件 + 4 组探针；含 HTTP 与耗时）

| 候选 | 参考 | 模型 | size | HTTP | 耗时 | 实测产物 | 输出尺寸/mode |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | `ref_4x.png` | `gpt-image-2.5-1k` | 1024x1024 | 200 + 200 + 200（3 次调用） | 23.0s / 23.5s / 20.1s | pause_AI_cand_C1.png（1254×1254 RGBA） | — |
| **C2** | `ref_4x.png` | `gpt-image-2.5-1k` | 1024x1024 | 200（1 次调用） | 25.0s | pause_AI_cand_C2.png（1254×1254 RGBA） | — |
| **C3** | `ref_1x.png` | `gpt-image-2.5-1k` | 1024x1024 | 200（1 次调用） | 20.9s | pause_AI_cand_C3.png（1254×1254 RGBA） | — |
| **C4** | `ref_4x.png` | `gpt-image-2.5-sunburst` | 1024x1024 | 500（1 次调用） | 1.0s | **无产物** | — |
| **C5** | `ref_8x.png` | `gpt-image-2.5-1k` | 1024x1024 | 200（1 次调用） | 29.4s | pause_AI_cand_C5.png（1254×1254 RGBA） | — |
| **C6** | `ref_4x.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 28.4s | pause_AI_cand_C6.png（1024×1024 RGBA） | — |
| **C7** | `ref_4x.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 27.2s | pause_AI_cand_C7.png（1024×1024 RGBA） | — |
| **C8** | `ref_4x.png` | `gpt-image-2.5-1k` | 1024x1024 | 200 + 200（2 次调用） | 26.2s / 26.6s | pause_AI_cand_C8.png（1254×1254 RGBA） | — |
| **C9** | `ref_1x.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 78.0s | pause_AI_cand_C9.png（1024×1024 RGBA） | — |
| **C10** | `ref_2x.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 30.0s | pause_AI_cand_C10.png（1024×1024 RGBA） | — |
| **C11** | `ref_4x_clean.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 26.2s | pause_AI_cand_C11.png（1024×1024 RGBA） | — |
| **C12** | `ref_4x_clean.png` | `gpt-image-2.5-1k` | 1024x1024 | 200（1 次调用） | 30.4s | pause_AI_cand_C12.png（1254×1254 RGBA） | — |
| **C13** | `ref_4x_clean.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 32.5s | pause_AI_cand_C13.png（1024×1024 RGBA） | — |
| **C14** | `ref_4x_clean.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 46.9s | pause_AI_cand_C14.png（1024×1024 RGBA） | — |
| **C15** | `ref_4x_clean.png` | `gpt-image-2` | 1024x1024 | 200（1 次调用） | 28.0s | pause_AI_cand_C15.png（1024×1024 RGBA） | — |

全部候选原图保留在 `候选\`（便于复核，**未删任何一件**）；无 alpha 的尝试另存为 `*_attempt<N>_RGB.png`。

## 四、逐件目视评语（本人 Read 原图逐件看后写下；同时见 `候选\_接触印相_候选.png`）

- **C1**（4× 参考 + 几何规格详尽段；**两次尝试都返回 RGB**（含重试）——用来证明「无 alpha」与 prompt 里透明指令的位置无关，是随机事件）：盘面还原尚可（环可见、外发光中等）；但 ‖ 明显偏小（组宽 36/48、条高 46/54），间隙 9.7 偏窄。第 1 次调用返回 RGB（无 alpha）⇒ 已留档 `pause_AI_cand_C1_attempt1_RGB.png`。**不合格（字形偏小）**
- **C2**（4× 参考 + 轻措辞（前置透明指令 + 强调同风格））：盘面被立体化：明显高光 + 蓝白浓晕、环厚重；‖ 组宽 35.3、间隙 8.4 偏窄。与基准「平、淡、脆」的气质不符。**不合格**
- **C3**（1:1 参考（保盘面尺度）+ 几何规格段）：结构跑偏：模型把盘面放大到占满画布且偏左，盘心另画了一个小圆环，‖ 极小。**不合格**
- **C4**（换模型 sunburst + 极简指令式措辞（**上游 500，无产物**））：上游 HTTP 500（`upstream error: do request failed`）——无产物。
- **C5**（8× 参考（大图给模型更多像素）+ 极简措辞）：盘面被放大到占满画布，外发光被画布裁断、边缘出现白色锯齿；‖ 12.6/8.8/12.6 @53.6（条高接近，条偏瘦）。**不合格（裁断）**
- **C6**（换模型 gpt-image-2（原生 1024×1024）+ 几何规格段）：最像一枚「正常 UI 按钮」：环清晰、盘面平；但环被画在盘内侧（盘缘与环之间多出一圈淡蓝带），外发光过浓（明显蓝色光晕）；‖ 15/9/15 @47（条宽已对，间隙与条高偏）。**目视第二档**
- **C7**（盘面口径加强段（压外发光/环贴最外缘/钉盘面占画布 91%）+ gpt-image-2）：盘面平、外发光淡（气质最接近基准），但环几乎看不见（被压得极淡）；‖ 10.6/7.5/10.6 @42.7 偏小。**可用但字形偏小**
- **C8**（盘面口径加强段 + gpt-image-2.5-1k）：盘面平、环极淡、外发光宽而灰；‖ 10.2/9.9/10.2 @44.4 偏小。第 1 次调用把**棋盘格烘焙进像素**并返回 RGB，已留档 `pause_AI_cand_C8_attempt1_RGB.png`。**不合格（字形偏小）**
- **C9**（盘面口径加强段 + 1:1 参考（试把「盘面占画布 91%」这条压住））：与 C8 同族问题（环极淡、发光宽）；‖ 9.9/8.5/10.1 @44。**不合格（字形偏小）**
- **C10**（盘面口径加强段 + 2× 参考（盘面 / 图形都比 4× 更小，留出更多画布余量））：环贴缘且较清晰、盘面平；‖ 10.8/9.0/10.4 @42.3 偏小。**不合格（字形偏小）**
- **C11**（「禁外发光 + 环贴外缘」极限口径 + **参考图先削掉弱 alpha 羽边**（ref_4x_clean））：**首次把环拉回盘缘**（「削掉参考图羽边 + 禁外发光」生效）：盘面平、外发光窄、环清晰；‖ 14.5/10.2/14.5 @50.9。环对比略强（ΔL 87.9 vs 基准 82.2）。**目视第三档**
- **C12**（同上口径，换 gpt-image-2.5-1k）：环贴缘但极淡，外发光较宽；‖ 13.0/9.3/13.0 @51.7。**目视第三档**
- **C13**（P_FLAT + 符号段前置重写（钉 16/16/16 @54、明令「不得偏小」））：条宽与条高基本到位（15.5 / 54.4），间隙仍偏窄 10.5；盘面平、环贴缘（环芯 r=52.16，基准 52.12）。**目视第一档**
- **C14**（P_FLAT + 符号段前置**超量下注**（按 20/20/20 @62 下单，指望落回 16/16/16 @54））：「超量下注」生效：条宽 15.9（≈规格 16）、条高 55.8（+3%）；间隙 10.7 仍窄、组宽 42.5。**目视第一档**
- **C15**（P_FLAT + 符号段前置、**间隙单独超量下注**（20/30/20 @62，专治间隙一直偏窄））：间隙单独加码后由 10.7 抬到 13.2（仍窄 3），组宽 44.9、条高 55.6、条宽 15.9；环贴缘（环芯 r=51.65）、盘面平、外发光窄。**定稿（第一档中综合最优）**

另有四组 API 探针产物在 `候选\_probe\`（`probe_bgparam.png` RGB / `probe_bgparam_fmt.png` RGBA / `probe_gptimage2.png` RGBA / gemini 无产物）。

## 五、定稿

**定稿 = 候选 `C15`**（P_FLAT + 符号段前置、**间隙单独超量下注**（20/30/20 @62，专治间隙一直偏窄））

| 项 | 值 |
| --- | --- |
| 文件 | `x_ui_pbkick_pause_AI_off.png` |
| 实测 | 119×119 ｜ mode **RGBA** ｜ md5 `90bc78f1ac7783ae17c335e12827b7b2` |
| 规格化 | 按「环外径 → 108」等比缩放（LANCZOS），环 bbox 中心对准 (59,59)，裁 119×119 —— **无变形、无拉伸** |
| 原始候选 | `pause_AI_cand_C15.png`（1024×1024 RGBA） |
| alpha | α=0 32.25% ｜ 半透明 65.99% ｜ α=255 1.76% ｜ **最外 1px 帧 αmax = 0** |
| 字形实测（119 画布） | 条宽 [16, 16] ｜ 间隙 13 ｜ 组宽 45 ｜ 条高 56 |
| 与派生版对照 | 派生版 条宽 [16, 16] ｜ 间隙 16 ｜ 组宽 48 ｜ 条高 54（规格 16/16/48/54、圆角 2） |

## 六、完整提示词（**实际发出的原文**，与 `gen_pause_ai.py` 中的字符串逐字一致）

候选 → 模板对照：`C1`→P_TASK、`C2`→P_LIGHT、`C3`→P_TASK、`C4`→P_TIGHT、`C5`→P_TIGHT、`C6`→P_TASK、`C7`→P_FAINT、`C8`→P_FAINT、`C9`→P_FAINT、`C10`→P_FAINT、`C11`→P_FLAT、`C12`→P_FLAT、`C13`→P_FLAT2、`C14`→P_FLAT3、`C15`→P_FLAT4

### P_TASK

```text
You are given one image: a small round pause/play button sprite from a Japanese visual novel UI. It is a perfectly circular disc: a very pale ice-blue to near-white vertical gradient fill (about #E7F0FD), a 3-pixel grey-blue ring border (about #929FB7) around the rim, and a soft cyan-blue outer glow halo (about #7AB0E8) fading out past the rim. In the middle of the disc there is a single solid light-blue triangle (a PLAY arrow, about #A7CBF1).
TASK: change ONLY the symbol in the middle. Replace the PLAY triangle with a PAUSE symbol made of exactly TWO vertical rounded bars (a double vertical bar, like the pause icon ||). Do not touch anything else.
KEEP COMPLETELY UNCHANGED - redraw them exactly as in the input image, same position, same size, same radius, same thickness, same colours, same soft anti-aliased edges: the circular pale-blue disc, the grey-blue ring border, and the feathered outer glow halo. The disc must stay centred in the canvas with the same margin as the input image.
PAUSE SYMBOL GEOMETRY (proportions measured on the input image; follow them closely): the two bars are vertical, rectangular with small rounded corners (corner radius about 2 pixels at this size), parallel, identical in size, separated by a gap. Bar height is about 50% of the disc diameter (i.e. about 54 px on a 108 px disc). The two bars plus the gap together are about 44% of the disc diameter (about 48 px on a 108 px disc), so each bar is about 16 px wide and the gap between them is about 16 px - the gap is as wide as a bar. The whole two-bar group is centred in the disc (do not shift it left or right). The bars are filled with the same flat light-blue colour as the play triangle (about #A7CBF1) with clean anti-aliased edges, no outline, no shadow, no gradient, no glow on the bars themselves.
TRANSPARENT BACKGROUND: this is a game UI sprite; it MUST have a real alpha channel. Everything outside the soft feathered glow around the disc is fully transparent. Do not add any square plate, card, panel, frame, border, box, rounded rectangle, background wash, drop shadow rectangle or watermark. Do not add any text, letters, numbers smiley, logo or decorative element. Output only the single round button sprite, centred, nothing else.
```

### P_LIGHT

```text
Transparent background with a real alpha channel: the PNG must have genuine transparency - every pixel outside the soft glow of the button is fully transparent (alpha = 0). Do not place the button on any opaque backdrop.
Redraw this exact round UI button, keeping its look identical, but swap its centre symbol: the existing play triangle must become a pause symbol = two parallel vertical rounded bars. Keep the frosted pale-blue disc body, its grey-blue circular outline ring and its soft blurred outer glow exactly as they are in the reference; only the middle symbol changes. The two bars are thin vertical rounded rectangles of equal width, the same height as the old triangle (about half the disc diameter), close to each other with a narrow gap about as wide as one bar, together about 44% of the disc width, the pair perfectly centred inside the disc. Flat light-blue colour, same tint as the old triangle, smooth anti-aliased edges. Keep the icon a single round button sprite on transparent background, no panel, no box, no frame, no text, no extra decoration.
```

### P_TIGHT

```text
Transparent background, real alpha channel, alpha = 0 everywhere outside the button's soft glow.
Input: one round play-button sprite (pale blue-white frosted disc + grey-blue ring + soft blue outer glow, with a light-blue play triangle in the centre).
Output: the SAME sprite pixel for pixel, except that the light-blue play triangle is deleted and replaced by the pause symbol: exactly two vertical rounded bars, side by side, equal size, flat light-blue fill (#A7CBF1), rounded corners, no outline. Measurements relative to the disc: disc diameter 108 units; each bar 16 units wide, 54 units tall, 16 units apart; the pair occupies 48 units total, perfectly centred both horizontally and vertically inside the disc. Nothing else changes: no new glow, no new ring, no border, no panel, no shadow, no text, no background. The final image is a single round button icon floating on full transparency.
```

### P_FAINT

```text
Transparent background with a real alpha channel - alpha = 0 on every pixel outside the button's faint glow. Do NOT place the button on any opaque or coloured backdrop.
Redraw this round UI button keeping its look, but replace the middle play triangle with a pause symbol = two parallel vertical rounded bars.
CRITICAL STYLE CONSTRAINTS - the input image is pale, flat and whisper-quiet; the output must be the same, not a saturated glossy icon:
1) The outer glow is VERY FAINT: only a soft, barely-visible pale white-blue feathering a few pixels wide just outside the rim, low opacity, fading to fully transparent quickly. Do NOT draw a thick bright saturated blue halo, a glowing neon ring, a wide blue band or a coloured backdrop around the button.
2) The circular outline ring is a THIN flat grey-blue line (about 3 px on a 108 px disc) sitting exactly on the outer rim of the disc - the outermost edge of the disc body. It is NOT a band, NOT a double ring, NOT placed inside the disc with blue between the ring and the rim.
3) The disc body is nearly flat and very pale: only a very slight vertical gradient from near-white at the top (#F2F7FE) to pale ice blue at the bottom (#E4EFFC). No strong shading, no glossy highlight, no inner shadow.
4) The disc keeps the same size and the same margin inside the canvas as the input: its outer rim spans about 91% of the canvas width, leaving a narrow margin of about 5% on each side.
5) Keep the disc perfectly circular and centred.
PAUSE SYMBOL: two identical vertical bars with small rounded corners (radius about 2 px at 108 px disc size), each bar about 16 px wide and 54 px tall, separated by a gap about as wide as one bar (about 16 px), the pair about 48 px wide in total, perfectly centred in the disc. Flat pale-blue fill about #A7CBF1, no outline and no glow on the bars. The image contains only this single round button on full transparency: no panel, no card, no frame, no box, no text, no letters, no numbers, no watermark, no decoration.
```

### P_FLAT

```text
Transparent background, real alpha channel - alpha = 0 everywhere outside the 1-2 pixel anti-aliasing feather of the button's edge.
Draw a FLAT, MATTE, MINIMAL game UI icon - a plain round button, NOT a glossy 3D orb:
The plate is an almost perfectly flat circular disc in one single very pale ice-blue tint (#E7F0FD), uniform to the eye, with at most a barely perceptible vertical lightness variation of 2-3 percent; NO three-dimensional shading, NO specular highlight, NO inner shadow, NO glossy reflection, NO bevel, NO elevation, NO drop shadow.
The whole outline of the plate is ONE thin solid grey-blue circular stroke (#929FB7), about 3 units thick on a 108-unit diameter plate, drawn exactly ON the outer circumference of the plate: it IS the outermost edge of the button. There is NO margin, band, rim or second ring outside this stroke, and no pale ring between the stroke and the plate inside.
OUTER GLOW IS FORBIDDEN: do not draw any halo, glow, bloom, blur, aura, vignette or soft shadow around the button. Immediately outside that grey-blue stroke the image is fully transparent with alpha = 0 (only a 1-2 pixel anti-aliasing feather is allowed).
Centre symbol: replace the play triangle of the input image with the pause symbol = two vertical bars with only slightly rounded corners. Each bar is about 16 units wide and 54 units tall, separated by a gap about 16 units wide, the pair about 48 units wide in total, centred exactly in the plate. Fill them with one flat uniform pale blue (#A7CBF1): no gradient, no outline, no shadow, no glow.
The image contains only this one flat round button icon on full transparency: no panel, no card, no frame, no box, no background, no text, no letters, no numbers, no watermark.
```

### 派生组合（C13/C14/C15 实发的是「前置符号段 + P_FLAT 全文」，下述三者即实发文本）

#### P_FLAT2 = _SYM_STRONG + P_FLAT

```text
Centre symbol: the play triangle of the input image must be replaced by the pause symbol = EXACTLY TWO vertical bars with slightly rounded corners (corner radius at most 1/8 of the bar width).
SIZE - the symbol must be as large as the play triangle it replaces and fill the middle of the plate boldly, NOT a small or skinny glyph: the two bars plus the gap between them span about 44 percent of the plate diameter (48 of 108 units), each bar is about 54 units tall (about half the plate diameter), so each bar is about 16 units wide and the empty vertical slot between them is about 16 units wide - exactly as wide as one bar. The pair is centred exactly in the plate both horizontally and vertically. Flat uniform pale blue (#A7CBF1), no gradient, no outline, no shadow, no glow.
Transparent background, real alpha channel - alpha = 0 everywhere outside the 1-2 pixel anti-aliasing feather of the button's edge.
Draw a FLAT, MATTE, MINIMAL game UI icon - a plain round button, NOT a glossy 3D orb:
The plate is an almost perfectly flat circular disc in one single very pale ice-blue tint (#E7F0FD), uniform to the eye, with at most a barely perceptible vertical lightness variation of 2-3 percent; NO three-dimensional shading, NO specular highlight, NO inner shadow, NO glossy reflection, NO bevel, NO elevation, NO drop shadow.
The whole outline of the plate is ONE thin solid grey-blue circular stroke (#929FB7), about 3 units thick on a 108-unit diameter plate, drawn exactly ON the outer circumference of the plate: it IS the outermost edge of the button. There is NO margin, band, rim or second ring outside this stroke, and no pale ring between the stroke and the plate inside.
OUTER GLOW IS FORBIDDEN: do not draw any halo, glow, bloom, blur, aura, vignette or soft shadow around the button. Immediately outside that grey-blue stroke the image is fully transparent with alpha = 0 (only a 1-2 pixel anti-aliasing feather is allowed).
Centre symbol: replace the play triangle of the input image with the pause symbol = two vertical bars with only slightly rounded corners. Each bar is about 16 units wide and 54 units tall, separated by a gap about 16 units wide, the pair about 48 units wide in total, centred exactly in the plate. Fill them with one flat uniform pale blue (#A7CBF1): no gradient, no outline, no shadow, no glow.
The image contains only this one flat round button icon on full transparency: no panel, no card, no frame, no box, no background, no text, no letters, no numbers, no watermark.
```

#### P_FLAT3 = _SYM_OVER + P_FLAT

```text
Centre symbol: replace the play triangle with the pause symbol = EXACTLY TWO vertical bars with slightly rounded corners.
GEOMETRY - follow these numbers literally: plate diameter 108 units; EACH BAR 20 units wide and 62 units tall; the empty vertical slot between the two bars 20 units wide; so the two bars plus the slot span 60 units in total (55 percent of the plate diameter) and the whole pair is centred exactly in the middle of the plate, both horizontally and vertically. Make the symbol bold and generous: it must occupy the middle of the plate clearly, never a small, short or skinny glyph. Flat uniform pale blue (#A7CBF1), no gradient, no outline, no shadow, no glow.
Transparent background, real alpha channel - alpha = 0 everywhere outside the 1-2 pixel anti-aliasing feather of the button's edge.
Draw a FLAT, MATTE, MINIMAL game UI icon - a plain round button, NOT a glossy 3D orb:
The plate is an almost perfectly flat circular disc in one single very pale ice-blue tint (#E7F0FD), uniform to the eye, with at most a barely perceptible vertical lightness variation of 2-3 percent; NO three-dimensional shading, NO specular highlight, NO inner shadow, NO glossy reflection, NO bevel, NO elevation, NO drop shadow.
The whole outline of the plate is ONE thin solid grey-blue circular stroke (#929FB7), about 3 units thick on a 108-unit diameter plate, drawn exactly ON the outer circumference of the plate: it IS the outermost edge of the button. There is NO margin, band, rim or second ring outside this stroke, and no pale ring between the stroke and the plate inside.
OUTER GLOW IS FORBIDDEN: do not draw any halo, glow, bloom, blur, aura, vignette or soft shadow around the button. Immediately outside that grey-blue stroke the image is fully transparent with alpha = 0 (only a 1-2 pixel anti-aliasing feather is allowed).
Centre symbol: replace the play triangle of the input image with the pause symbol = two vertical bars with only slightly rounded corners. Each bar is about 16 units wide and 54 units tall, separated by a gap about 16 units wide, the pair about 48 units wide in total, centred exactly in the plate. Fill them with one flat uniform pale blue (#A7CBF1): no gradient, no outline, no shadow, no glow.
The image contains only this one flat round button icon on full transparency: no panel, no card, no frame, no box, no background, no text, no letters, no numbers, no watermark.
```

#### P_FLAT4 = _SYM_GAP + P_FLAT

```text
Centre symbol: replace the play triangle with the pause symbol = EXACTLY TWO vertical bars with slightly rounded corners.
GEOMETRY - follow these numbers literally: plate diameter 108 units; EACH BAR 20 units wide and 62 units tall; the EMPTY VERTICAL SLOT between the two bars is 30 units wide, i.e. clearly WIDER than one bar - the two bars are well separated and must never look crowded, touching or merged. The two bars plus the wide slot span 70 units in total and the whole pair is centred exactly in the middle of the plate, both horizontally and vertically. Make the symbol bold and generous. Flat uniform pale blue (#A7CBF1), no gradient, no outline, no shadow, no glow.
Transparent background, real alpha channel - alpha = 0 everywhere outside the 1-2 pixel anti-aliasing feather of the button's edge.
Draw a FLAT, MATTE, MINIMAL game UI icon - a plain round button, NOT a glossy 3D orb:
The plate is an almost perfectly flat circular disc in one single very pale ice-blue tint (#E7F0FD), uniform to the eye, with at most a barely perceptible vertical lightness variation of 2-3 percent; NO three-dimensional shading, NO specular highlight, NO inner shadow, NO glossy reflection, NO bevel, NO elevation, NO drop shadow.
The whole outline of the plate is ONE thin solid grey-blue circular stroke (#929FB7), about 3 units thick on a 108-unit diameter plate, drawn exactly ON the outer circumference of the plate: it IS the outermost edge of the button. There is NO margin, band, rim or second ring outside this stroke, and no pale ring between the stroke and the plate inside.
OUTER GLOW IS FORBIDDEN: do not draw any halo, glow, bloom, blur, aura, vignette or soft shadow around the button. Immediately outside that grey-blue stroke the image is fully transparent with alpha = 0 (only a 1-2 pixel anti-aliasing feather is allowed).
Centre symbol: replace the play triangle of the input image with the pause symbol = two vertical bars with only slightly rounded corners. Each bar is about 16 units wide and 54 units tall, separated by a gap about 16 units wide, the pair about 48 units wide in total, centred exactly in the plate. Fill them with one flat uniform pale blue (#A7CBF1): no gradient, no outline, no shadow, no glow.
The image contains only this one flat round button icon on full transparency: no panel, no card, no frame, no box, no background, no text, no letters, no numbers, no watermark.
```

## 七、复现方式

```bash
# 1) 生成候选（幂等；已有产物跳过；--force 全跑；--only C15 单跑）
python 复现脚本\gen_pause_ai.py [--force] [--only C1,C15]
# 2) 规格化 + 自证 + 对照图
python 复现脚本\finalize_pause_ai.py --pick C15
# 3) 逐件几何实测 / 与播放键差分 / 两份文档
python 复现脚本\_measure_cands.py
python 复现脚本\_diff_vs_ref.py
python 复现脚本\make_reports.py --pick C15
```
