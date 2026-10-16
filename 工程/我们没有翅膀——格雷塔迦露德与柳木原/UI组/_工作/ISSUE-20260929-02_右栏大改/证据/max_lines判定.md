# max_lines 判定 · ISSUE-20260929-02 · 模块 E2（`工具/gen_flow_layout.py`）· **第 2 轮**

> 主代理 2026-09-29 第 2 轮裁决：**`fc.p_text_tx` / `fc.p_message_tx` 的 `max_lines` 由 5 改 4**；
> **不加**元素级 `line_spacing`（保持全局基线，少一个活动件）。
> 本文件给出**三条行高依据（文件:行 ＋ 实测数字）**与**改动前后**。以下每条均由本模块在本机实读/实算核过。

---

## 一、三条行高依据（一手）

| # | 依据 | 文件:行 | 实测原文 / 数值 |
| --- | --- | --- | --- |
| ① | 行距系数取「元素级优先，否则全局 `body`」 | `krkr/game/ui_theme.tjs:145-148` | `function uiThemeElementSpacing(el)` → `if(el !== void && el.line_spacing !== void) return el.line_spacing;` / `return uiThemeLineSpacing("body");` |
| ② | 行盒高度 = `floor(字号 × 该系数)`，且不小于字号 | `krkr/game/ui_theme.tjs:237-238` | `:237  var lineH = Math.floor(size * uiThemeElementSpacing(el));` / `:238  if(lineH < size) lineH = size;` |
| ③ | 全局 `line_spacing.body` = **1.4** | `layout/_root.json:66` | `"line_spacing": { "body": 1.4, "menu": 1.2 }`（json 实读确认 `fonts.line_spacing.body == 1.4`） |

**推得**：本批两件 `_tx` 的字号 **24**、**未写** `line_spacing` ⇒ 走全局 1.4
⇒ 行盒 `lineH = floor(24 × 1.4) = floor(33.6) = **33px**`（33 ≥ 24，第 ② 条的钳制不触发）。

## 二、容量实算（槽净高 159）

| 行数 | 需要高度 | 与槽净高 159 比 | 结论 |
| --- | ---: | --- | --- |
| 4 | `4 × 33 = **132**` | 132 ≤ 159（余量 **27px**） | ✓ 放得下 |
| 5 | `5 × 33 = **165**` | 165 > 159，**越槽底 6px** | ✗ 溢出 |

`159 ÷ 33 = 4.818… ⇒ max_lines = **4**`（向下取整，不越槽底）。

> ⚠ **作废**：第 11 批首版 note / SCREEN_NOTE / PRESET_TABLE 里写的
> 「槽内净高 159 ÷（24px × **1.3** 行距 = 31.2）≈ 5.09 ⇒ **5**」**是错的** ——
> 1.3 不是本工程的全局 `body` 系数（全局是 **1.4**），且该式把「行盒」当成了「字号 × 1.3」。
> 本批（第 2 轮）已在**三处**（元素 `note` ×2、`SCREEN_NOTE`、`PRESET_TABLE`）订正为 `33px / 4 行`。

## 三、改动前后（逐件）

| 元素 | 字段 | 改前 | **改后** | 说明 |
| --- | --- | --- | --- | --- |
| `fc.p_text_tx` | `max_lines` | `5` | **`4`** | 槽净高 159 ÷ 行盒 33 ＝ 4.82 ⇒ 4 |
| `fc.p_text_tx` | `line_spacing` | （无） | **（仍无）** | 裁决：**不加**，保持全局 1.4 |
| `fc.p_text_tx` | `x/y/w/h` | `1437,637,398,159` | **不变** | |
| `fc.p_text_tx` | `valign` / `wrap` | `top` / `true` | **不变** | |
| `fc.p_message_tx` | `max_lines` | `5` | **4** | 同 `fc.p_text_tx` |
| `fc.p_message_tx` | `line_spacing` | （无） | **（仍无）** | 同上 |
| `fc.p_message_tx` | `x/y/w/h` | `1437,830,398,159` | **不变** | |
| `fc.p_title_tx` | 全部 | `h40` / `valign:middle` / `wrap:false` / `max_lines:1` | **一字未动** | 标题一行，不扩槽 |
| 字号 / `bold` | — | `24` / `true` | **不变** | 用户只要求改颜色与描边 |

## 四、机检（实跑）

```
# 落盘后从屏文件读（layout/screens/32_flowchart.json）
fc.p_text_tx     max_lines= 4  line_spacing= (无，走全局)  h= 159  valign= top
fc.p_message_tx  max_lines= 4  line_spacing= (无，走全局)  h= 159  valign= top
fc.p_title_tx    max_lines= 1  line_spacing= (无，走全局)  h=  40  valign= middle
```

- 生成器编译：`py_compile` 在 `-W error::SyntaxWarning` 下 **clean**；
- 金标闸：改后先**按设计拒绝落盘**（旧金标），`--refresh-golden` 重钉后 `✓ 产出 md5 == 金标`；
- `--title-check-report` ⇒ **712 条 / 断行表 20 条 / 违规 0 / 最紧 +34.00（s01_02b）/ 两行 105 / 最宽 228.0px**（**与改前逐项一致**）；
- `--selfcheck-title-break` ⇒ 真表 0 违规、删 1 条必越线、清空表 20 条 ⇒ **按预期**（与改前一致）；
- 元素数**不变**：`screen1` 280 / `screen2` 124 / `ref150` 103 / `states` 117 / `frag` 136；
  但 `content-sha256`（去 note 摘要）**五档全变**（`max_lines` 属内容字段）⇒ 金标重钉。

## 五、五组新金标（第 2 轮 · 现行真值）

| 预设 | md5 | content-sha256 |
| --- | --- | --- |
| `screen1` | `6e6f2185ee1f752f3f3a8926d387c293` | `c086626bc0fec6f54e1cdf3b630daadd9b1aa868e5f271e9abe0e34eac74ab78` |
| `screen2` | `0a3f50dd122109ec161c78d0ef9084df` | `9838b6f1277b3b8490993e0699cfb5217271d1a3b1df93efc0f49eef726029ad` |
| `ref150` | `27facd6bb5426ac317e1157a1d1c0755` | `bad60c14ef7e146c2cdcb55e06661b1ce75db125a996297076b69d1d21f395c4` |
| `states` | `a1e2371a8e7bd317699d4077cc36e188` | `82d8d88e94de3f8e258bb2cdc0d48e7e1814510ad04834749c5049896dbe711a` |
| `frag` | `9c5ffde2f0d493ad3821590ee4a0112c` | `ab46773eee77efb0d23692cc5206401454bd2b94328bab7301489c1d21c4efd2` |

> 回填范围（本轮）：`gen_flow_layout.py` 的 `GOLDEN` 字面量（`--refresh-golden` 自动写）＋ `PRESET_TABLE`（手改）。
> **`layout/_schema.md` 本批一律未动**（按第 2 轮指令，金标表归主代理）—— 五组新值以本条消息回复为准。

## 六、复现命令

```bash
cd "E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
python 工具/gen_flow_layout.py --dry-run
python 工具/gen_flow_layout.py            # 旧金标 ⇒ 按设计拒绝落盘（exit=1）
python 工具/gen_flow_layout.py --refresh-golden
python 工具/gen_flow_layout.py            # ✓ md5 == 新金标 后落盘
python 工具/gen_flow_layout.py --preset states
python 工具/gen_flow_layout.py --preset frag
python 工具/gen_flow_layout.py            # ★ 还原交付样例 screen1
python 工具/gen_flow_layout.py --title-check-report
python 工具/gen_flow_layout.py --selfcheck-title-break
```
实跑输出全量：`证据/_验收日志_第二轮.txt`（本轮）与 `证据/自检报告.md` §六（第二轮段落）。
