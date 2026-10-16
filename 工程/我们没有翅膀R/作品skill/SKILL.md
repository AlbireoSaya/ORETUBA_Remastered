---
name: oretsuba-r-work
description: 《我们没有翅膀R》（俺たちに翼はないＲ，Navel 2011）专属工程索引，配合通用翻译规范 skill（galgame-translation）使用。含该作引擎事实、解包管线、编码与排版技术约束、文本规模、专名与 UI 词、以及存档/路径硬约束。开工前必须与通用层一同读取。
---

# 我们没有翅膀R · 作品专属 skill

> **本文件仅适用于『俺たちに翼はないＲ』**；跨作品成立的通则一律归 `.zcode\skills\galgame-translation\`。
> 引擎技术细节见 **`.zcode\skills\lucifen-unpack\`**（本作是该 skill 的首个沉淀作品）。
> 过程性技术记录见 `工程\我们没有翅膀R\技术报告.md`；两者冲突时以本文件（最新实测）为准并回写。

## 〇、作品身份

| 项目 | 值 |
| --- | --- |
| 原名 | 『俺たちに翼はないＲ』（Oretachi ni Tsubasa wa Nai R） |
| 中文译名 | **我们没有翅膀R** |
| 会社 / 发售 | Navel / 2011-06-24（Limited Edition） |
| 分级 | **一般向（15 歳以上推奨）**，非 R18；是 2009 年 R18 原版的全年龄化重制 |
| 引擎 | **Lucifen「Easy Game System DX」DX**（非 KiriKiri） |
| 原作沿革 | 2009『俺たちに翼はない』（R18）→ 2011 R 版（一般向，**新增香田亜衣路线**、改写 18 禁场景、追加 CG）→ 2014 PS3/PSV |
| 介质 | DVD-ROM；安装介质备份在 `备份\我们没有翅膀R-安装介质\` |

## 一、路径与目录（**硬约束，改前必读**）

| 用途 | 路径 |
| --- | --- |
| **游戏本体** | `_game_ascii\ORETSUBA_R\`（**纯 ASCII 路径，不可改成中文名**；成品目录 `成品\我们没有翅膀R\ORETSUBA_R` 经 junction 指向此处） |
| **存档目录** | `_game_ascii\ORETSUBA_R SaveData\` |
| 工程目录 | `工程\我们没有翅膀R\` |
| 原始解包脚本 | 工程\我们没有翅膀R\语料\R版SCRIPT\：418 TOB+23 SOB+3 DAT+INF/SYS各一 |
| 提取台词 | `工程\我们没有翅膀R\语料\R版台词.json`（58,855 槽） |
| 参照汉化 | `工程\我们没有翅膀R\参照\`（原版 2009 的汉化成品 + 提取对照） |
| 存档候选 | `工程\我们没有翅膀R\存档候选\`（含 R 版全解锁档） |

**为什么必须纯 ASCII**：引擎把存档目录绝对路径以 **Shift-JIS** 写入 `USER.CFG`；
「我们没有翅膀R」里的简体字（们/没/翅/膀）**在 Shift-JIS 中不存在**，含此类字符的路径引擎无法表示。
→ 移动游戏目录后，必须同步改写 `USER.CFG` 的路径段（存档目录内 + `%APPDATA%\壌偨偪偵梼偼側偄俼 SaveData\` 两份），
  格式为 `u16 路径长度 + SJIS 路径 + NUL`，路径长度前缀须同步。

## 二、文本承载与编码

| 项目 | 值 |
| --- | --- |
| 剧情脚本 | 418 个 `.tob`（**TOB0** 字节码），台词以 SJIS 字节内嵌，判据见 lucifen-unpack §三 |
| 系统脚本 | 23 SOB：21 SOB0+func_lib.sob(SOB2)+user_var.sob(SOB1声明)；前22容器结构通过，声明未解码 |
| 源编码 | **Shift-JIS（CP932）** |
| 目标编码 | **GBK**（中文 Windows ACP=936）——与参照汉化（新米汉化组）一致 |
| **声明串结构** | `01 01 <u16 L>` + 内容（**末字节必须 NUL**）：说话人名 / 组合名 / 编号名 / 选项标签 / 场景描述均属此类。**改动必须等长且保住 NUL 结尾**——末字节非 NUL 会让名字框越读显示 2–3 个方块（ISSUE-20260915-06 根因之一） |
| **译文 GBK 可编码性** | 译文必须可 GBK 编码；`・≪≫♪` 等不可编码字符由构建器 `build_padded.gbk_norm()` 回退为 `·《》☆`（**静默跳过=原日文残留=乱码**，ISSUE-20260915-06 根因之二） |
| 行宽 / 折行 | ⚠️ **待实测确认**（TOB0 正文无长度字段、无 NUL，长度由消息表推导；需在灰度阶段确认引擎是否自动折行） |
| 文本槽总数 | **58,855**（台词 35,462 / 旁白 22,963 / 章节标题 430） |

**写回工具**：`工程\我们没有翅膀R\工具\tob_rewrite.py`
- `equal`（定长 + `--pad` 空格补齐）：零风险模式，推荐优先
- `rebuild`（变长）：自动重定位标签值 / T 表 / 跳转 / 尾形地址四类字段，含结构自检
- 编码参数：`--enc gbk`

**重打包**：`工程\我们没有翅膀R\工具\lpk_patch.py`（二进制补丁；**只重压改动过的条目**，
未改动条目原样保留字节——全量重压会被引擎拒绝）。

## 三、UI 与系统词（来源：`语料\R版SCRIPT\` 的 `.sob` 与 `ll_app.inf`）

⚠️ 以下为**系统脚本内**的日文原文，译文待裁决后填入；**说话人标签（含 `q`/`r` 等简写）不得译**。

| 日文原词 | 出现位置 | 备注 |
| --- | --- | --- |
| 俺たちに翼はないＲ | `ll_app.inf` / 窗口标题 | 窗口标题（署名追加点） |
| セーブデータ作成フォルダが見つかりません | EXE | 非脚本，属引擎消息（不在翻译范围，需另议） |
| このシーンをスキップしますか？ | 实测截图 | 系统确认框 |
| Yes / No | 同上 | 英文原文 |
| セーブ / ロード / 戻る / ログ / 設定 等 | 系统栏 | 见 `config1.sob` / `config2.sob` |

> UI 词定译写入 `术语表.md` 的 UI 小节；本表仅登记来源位置。

## 四、专名（证据来源：`语料\R版台词.json` 的说话人标签，共 **331 种**）

**高频主要角色**（括号内为该标签在 58,855 槽中的出现次数，即证据）：

| 日文标签 | 次数 | 拟译 | 说明 |
| --- | --- | --- | --- |
| 隼人 | 5,835 | 隼人 | 主角之一（羽田隼人） |
| 鷹志 | 5,066 | 鹰志 | 主角之一（渡来鹰志） |
| 鷲介 | 3,497 | 鹫介 | 主角之一（成田鹫介） |
| 日和子 | 1,681 | 日和子 | |
| 明日香 | 1,638 | 明日香 | |
| 鳴 | 1,504 | 鸣 | |
| 亜衣 | 1,471 | 亚衣 | **R 版新增路线**（香田亜衣） |
| 京 | 1,313 | 京 | |
| 小鳩 | 1,223 | 小鸠 | |
| 狩男 | 722 | 狩男 | |
| 翔 | 711 | 翔 | |
| 英里子 | 689 | 英里子 | |
| 和馬 | 686 | 和马 | |
| 紀奈子 | 624 | 纪奈子 | |
| パル | 592 | 帕露 | 片假名名 |
| ガルーダ | 535 | 迦楼罗 | ⚠️ 与下方同音的「伽楼羅」(188) 并存，**需确认是否同一角色两种写法** |
| 蔵人 | 479 | 藏人 | |
| 咲夜 | 475 | 咲夜 | |
| 優 | 413 | 优 | |
| カケル | 292 | 翔 | ⚠️ 片假名形，与「翔」(711) 疑为同一角色的不同写形，**待确认** |

**其他标签**（片假名阵营与配角，均待逐条裁决后入表）：
`バニィＤ`(268)、`プラチナ`(262)、`ＬＲ２００１`(256)、`高内`(251)、`チケドン`(211)、`聖騎士ホーク`(209)、
`アリス`(186)、`ハリュー`(173)、`フェニックス`(166)、`ファルコン`(134)、`マルチネス`(118)、`狂夜`(108)、
`可菜`(105)、`メンマ`(103)、`声`(98)、`小娘`(90)、`イーグル`(82)、`牧師`(81)、`ダヴ`(77)…

> **说话人标签规则**：标签是引擎用来取人名与语音的**原字符串**，**原样保留不译**（含其中的 `q`/`r`/空格等简写）。
> 全部 331 个标签的完整清单可由 `R版台词.json` 重新导出：
> `python -c "import json,collections;print(collections.Counter(r['speaker'] for r in json.load(open('语料/R版台词.json',encoding='utf-8')) if r['speaker']).most_common())"`

**地名 / 组织 / 特定名词**：⚠️ **尚未提取**（需从 `.tob` 正文做 NER 级筛选，或参照 `参照\原版汉化SCRIPT_CHS\` 的既有译法）。
**在提取完成前，任何专名不得凭猜测写入译文**。

## 四之二、线路资源提取（2026-09-17 新增，ISSUE-20260917-11）

**亜衣线（`s03c_*`）全部资源**已提取并交付：`工程\我们没有翅膀R\亜衣线资源\`
（**3,055 个文件 / 478.4 MB**：剧本 55＋5 个数据文件、图像 509（立绘 353 + CG/背景 141 + 背景分片 15，16 片中 1 片与线路引用同名）、
语音 2,226、音效 135、BGM 125，另附 `说明文档.md`、`剧本\台词对照.{json,csv}`、`剧本\剧本全文.md`、`清单\素材清单.json`）。
用途＝**供用户重构新游戏**（详见该目录 `说明文档.md`：格式、映射、缺口、重构建议）。

| 工具 | 作用 |
| --- | --- |
| `工具\extract_ai_route_assets.py` | 主提取器：扫脚本引用 → 选择性提取 → ELG 转 PNG → 出清单。参数 `--out/--media/--no-png/--skip-bgm/--limit`（**默认输出即上面那个目录，复跑会覆盖**） |
| `工具\lpk_media.py` | CHR/PIC/SYS/BGM/SE/VOICE/DATA 的**选择性提取**（大小写不敏感）。这些归档的索引变体与 SCRIPT.LPK 不同，`lpk_patch.py` 会 IndexError → 借道社区 `工具\lucifen\Lucifen-Tools`（**只 import 不复制**）+ 其 `LPK-Keys.json` 里本作 R 版密钥 |
| `工具\台词对照\build_comparison.py`、`verify.py` | 台词对照表生成与自校验（55 场景 / 6,911 行；中日对照 + 配音 ID + 截断标注） |

**关键事实（线路素材引用规律）**：
- 脚本以 **ASCII 路径字符串**引用素材：`CHR\*.ELG`（立绘/差分）、`PIC\*.ELG`（CG/背景）、`SE\*.OGG`（音效）
- **BGM 不按文件名引用**（脚本里没有 `BGM\*` 路径）→ 需整包提供或另做编号映射
- 配音 ID 形如 `\<2 字节长度>\x00<ID>\x00`，**含单字母前缀者**（`X055014`、`Y051001`）易被正则漏掉；
  准入判据应以「`VOICE.LPK` 中存在小写 `<id>.ogg`」为准
- 背景存在**分片形态**（如 `BG06B.ELG` 实为 `bg06b_0..7.elg` 八片）
- 立绘为差分图层（`AI_01` + `AI_01A/B/C…`），重构时按图层叠加

## 四之三、汉化补丁包与可复现构建（2026-10-07 新增，ISSUE-20261007-04）

**背景**：汉化成品曾**只存在于游戏实体目录** `_game_ascii\ORETSUBA_R\`；2026-10-07 实测该目录
已不在工作区 ⇒ **部署过的汉化文件已消失，无副本可直接拷贝**。故改为「重建 + 固化构建脚本」。

**补丁包**（用户要的「可覆盖原版游戏目录直接生效」那一份，**不入库**）：

```
成品\我们没有翅膀R_汉化补丁\
    安装说明.md                    ← 目录说明、装载步骤、ASCII 路径警告、已知问题、md5
    覆盖到游戏目录\ORETUBAR.EXE     ← 原版 + GBK 补丁（覆盖到游戏目录，与 ORETUBAR.EXE 同级）
    覆盖到游戏目录\SCRIPT.LPK       ← 原版 + 全量汉化（同上）
    可选_全解锁存档\GAMEDATA.DAT    ← 放到 **同级** 的「<游戏目录名> SaveData\」（非游戏目录内）
```

| 工具 | 作用 |
| --- | --- |
| `工具\build_patch_package.py` | **补丁包生成器（唯一入口）**：`build_padded.py` 重建 LPK → `exe_gbk_patch.py` 在原版 EXE 上重打补丁 → 取全解锁存档 → 写安装说明；**内置指纹自检**，与已实机验证成品 md5 不符即中止不出包 |

**成品指纹（实机验证过的版本，重建必须命中）**：

- `SCRIPT.LPK` = `22dda536f8bc51b7cd6274df18eeb76a`（5,039,575 B，原版 4,604,893 B）
- `ORETUBAR.EXE` = `3fb2f9b410e23deb930d3cad82d11cd0`（原版 `bcdfed12…`；165 处改动）

**构建可复现性已实测**：LPK 重建输出「等长 44409 / 补齐 44230 / 截断 5368；不可编码 0」，
418 条目等长替换零重定位；EXE 165 处改动与 `exe_patch_report.json` **逐条完全相同**。

**实机冒烟（原版副本）**：8 个大归档用 NTFS 硬链接指向备份介质 + 补丁包两个文件 →
双击启动不崩、窗口标题为中文「我们没有翅膀R」、正常到标题画面；放入 `GAMEDATA.DAT` 后
菜单出现 `GALLERY`/`MUSIC`（原版无存档时仅 4 项）。对照组（原版未打补丁）窗口标题为
`壌偨偪偵梼偼側偄俼`（SJIS 当 GBK 的乱码）——即本补丁存在的理由。

**★ 实测订正：系统界面文字是「乱码」而非「日文」**。补丁把字体字符集改成 GB2312，而
`title`/`title2`/`saveload`/`config.dat`/`config1`/`config2`/`gameinit`/`main`/`gallery`/`bgmmode`
等**系统 SOB 未纳入汉化**、仍是 SJIS 字节 ⇒ 显示为乱码汉字（实测：标题画面菜单说明气泡
原文「最初から始めます」→ 乱码）。此类文字共约 **249 条**（另含 EXE 内嵌串）。
**已做单点试验**：把该气泡按**同样的等长 GBK 写法**写入 `title.sob`/`title2.sob`
（16 B → 「从头开始游戏」+2 全角空格 = 16 B），重建后实机**正常显示中文** ⇒
**可用既有方法补齐，无需改 EXE、无需新工具链**；本轮按用户要求未纳入。

## 四之四、系统界面汉化（2026-10-07 补齐，ISSUE-20261007-06）

**用户裁决「补做」后实施**：把系统界面里仍是乱码的日文文案按**等长 GBK**写入 `SCRIPT.LPK`。

| 项 | 值 |
| --- | --- |
| 覆盖范围 | `title.sob` / `title2.sob` / `saveload.sob` / `config.dat` / `config1.sob` / `config2.sob` / `gameinit.sob` / `main.sob` / `gallery.sob` / `bgmmode.sob` / `voiceinf.dat` |
| 条数 | 工作单 **289 行** = 第一版 247 + 加宽 2 条 ｢｣ 串 + 补入 42 条；**写回 286 条 + 豁免 3 条**（字体名） |
| 等长化 | `equal 77 / padded 209 / truncated 0 / keep 3 / none 0` |
| 字节验证 | **286 / 286 逐条命中**；11 个条目长度全未变（**零重定位**） |
| 成品指纹 | `SCRIPT.LPK` = **`5c94a3fe2a068ca815b99fd0cd9a7ff5`**（5,048,329 B；上一版「仅正文汉化」为 `22dda536…`） |
| 残留 | ① 字体名 `ＭＳ ゴシック` 3 处（**有意保留**：引擎据该名创建字体，改动有失效风险）；② 23 处数值表误判单字符（`gallery.sob` 11 / `config2.sob` 11 / `title.sob` 1，非显示串） |
| 未验证 | 设置屏 / 存读档对话框 / 报错框**未逐屏目视**（本机前台被占、抓不到游戏焦点画面；菜单气泡只在有焦点时显示） |

**工具（入库）**

| 工具 | 作用 |
| --- | --- |
| `工具\scan_sysui_v2.py` | **第二版抽取器**：单元＝SJIS 双字节 + **SJIS 单字节(0xA1–0xDF)** + 半角空格；合格＝≥2 日文字符，或单字符且为 CJK 标点。可对任意 LPK 列候选并标注「与上一版重合/新增」 |
| `工具\build_sysui.py` | 等长回写器：`build_padded.fit()` 等长化 → `lpk_patch` 原地重压 11 条目；含边界/重叠静态校验 |
| `工具\fix_sysui_round2.py` | 译文汇总与裁决表（`FIX` / `ADD`），产出 `runs_v2.json` 与 `master.tsv` |
| `工具\build_patch_package.py` | 第 2 步调用 `build_sysui`，补丁包一键重建（含指纹自检） |

**★ 两条新增硬约束（踩过的坑，务必遵守）**

1. **SJIS 单字节字符必须一并替换**（`｢`0xA2 / `｣`0xA3 等，范围 0xA1–0xDF）：EXE 已把前导字节判定
   放宽到 `0x81–0xFE`，残留的单字节会被当 **GBK 前导字节**吞掉下一个字节 ⇒ **两字节错位、整屏乱码**。
   修法＝把 span **加宽**到包含该字节（本次两条：config1 @58150/24、config2 @52990/24）。
2. **含 `%s` 的串不能有补齐空隙**：`スロット%` 若译成 5 字节再补齐到 9 字节，`%` 与字面 `s` 被撑开 →
   引擎 printf 找不到 `%s`、槽号不显示。修法＝**译文恰好占满 `nbytes` 且以 `%` 结尾**（`存档栏位%`）。

**分诊经验**：第二版扫描的「新增候选」里，`04 00 <2B> 00 00` 形式、**偏移递增**的段基本是**数值表**
（本次 136 段新增里 94 段属此类）；真显示串的邻居通常是 `\x00`、ASCII 词或另一条日文串。

## 五、文本规模与归档清单

| 归档 | 体积 | 内容 |
| --- | --- | --- |
| SCRIPT.LPK | 4.6 MB | 446条目418 TOB+23 SOB+3 DAT+INF/SYS各一，与原版归档446/446哈希一致 |
| DATA.LPK | 352 MB | 数据（含 OP 影片？待确认） |
| PIC.LPK | 654 MB | 图像（`.ELG`） |
| CHR.LPK | 306 MB | 立绘 |
| SYS.LPK | 116 MB | 系统素材（含 `GL_*`/`CF_*`/`SV_*` 等 `.ELG`） |
| VOICE.LPK | 1.09 GB | 语音（Ogg，每条流头两页需另寻来源） |
| BGM.LPK / SE.LPK | 171 MB / 34 MB | 音乐 / 音效 |

**场景差异（实测）**：与 2009 原版共有 **384** 个场景；**R 版新增 34 个**（全部形如 `s03c_*`，
即新增的**香田亜衣路线**）；仅原版有 4 个（`s01_14k`、`s03_15g`、`s03_21b`、`s04_05e`）。

**译文复用价值**：R 版原日文台词与参照汉化（原版 2009）**逐字命中 92.20%**（30,636 / 33,327）——
即**约九成可经「同文匹配」直接迁移**，其余（含新增 34 文件）需新译。说话人一致率 97.31%、语音一致率 96.27%。

## 六、存档与成品

- **全解锁存档**：`存档候选\R版全解锁_GAMEDATA.DAT`（484 B，3910 项状态数组中 793 项置位）；
  与公开 R 版全 CG 存档展开数据逐字节相同。上线/回滚脚本：`工具\apply_unlock_save.py` / `rollback_save.py`。
- **成品署名**（`AGENTS.md §六`）：窗口标题须追加
  `来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode`；
  落点为 `ll_app.inf` / 标题字段（本作标题取自 `ll_app.inf` 的「俺たちに翼はないＲ」段 + 引擎侧拼接）。
- **成品目录**：`成品\我们没有翅膀R\`（已部署；`ORETSUBA_R` 为 junction → `_game_ascii\ORETSUBA_R\`）。
  ⚠️ **2026-10-07 实测 `_game_ascii\` 已不在工作区，junction 断链**；要出可玩成品请按 §四之三
  的补丁包覆盖到原版安装，或重建整份游戏（约 2.5 GB）。

## 七、与引擎 skill 的对应关系

- 对应 skill：**`.zcode\skills\lucifen-unpack\`**（本作为其首个沉淀作品）
- 复用的步骤：LPK1 解包（社区 `lucifen_extract`）、索引/trie 解析、TOB0 消息表判据、
  变长回写的四类地址重定位、LZSS 压缩器、二进制补丁法
- **不适用/需覆盖的步骤**：
  - 社区 `lpk_repack.py` / `lpk-script-repacker.py` **不支持 LZSS**，且缺少 `SCRIPT` 的 key → 本作用自研 `lpk_patch.py`
  - 全量重压会被引擎拒绝 → 本作**只重压改动条目**
  - `ll_app.inf` / `ll_app.sys` 是 `uncompr_len=0` 的**未压缩**条目（只加密不压缩）

## 八、开工必读（每次任务都重读）

1. `.zcode\skills\galgame-translation\SKILL.md` + 同目录 `术语表.md`（通用层）
2. 本文件 + 同目录 `术语表.md`（作品层）
3. 需要改脚本时另读 `.zcode\skills\lucifen-unpack\SKILL.md`

## 九、未决项（开工前须补齐）

1. ~~GBK 显示的引擎侧处理~~ → **已解决（2026-09-15）**：`ORETUBAR.EXE` **165 字节常量补丁**
   （字体字符集 3 处 `SHIFTJIS→GB2312` + 前导字节判定 83 处 `0x81-0xFC→0x81-0xFE`），无需 DLL；
   脚本 `工具\exe_gbk_patch.py`，明细 `成品\我们没有翅膀R\exe_patch_report.json`。
2. **地名/特定名词提取未完成**（见 §四）。
3. **行宽与折行规则未实测**（见 §二）。
4. **`カケル` 与 `翔`、`ガルーダ` 与 `伽楼羅` 是否同一角色**，待剧情核对。
5. 系统 UI 词的最终定译待裁决。


## 2026-10-11 原作结构核查增量

据主代理提供实测事实：418 TOB 840标签/58425消息表；label区长度/地址与尾前缀+顺序索引零错；历史58855槽含430标题，不混用；SOB分布如上，不能复用OT语义；SOB容器核查复用尚未入库B0 source_ir.py的parse_container，证据基于当前工作树依赖，不宣称全新clone独立运行；证明结构，未解演出。证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/结构证据_20261011/R_TOB结构核查.json、R_SOB容器核查.json。


## 2026-10-11 R原生接口与自修改字码增量

R与OT的SOB执行器同为1284字节且仅分派表地址不同、47个入口相对偏移一致，故允许仅复用SOB指令结构，不能复用R原生函数编号、TOB或演出效果；R构造链为3+806=809个静态原生槽（803个独立地址），22个SOB容器共49974条指令、2273次原生调用使用240个索引0..799；全部2273个参数字初值零但各有一处op40写入VM_SP快照，需按可变字码内存处理，不可当NULL、不据连续PUSH猜参数数；此为静态证据不等于运行真值，依赖未入库B0探针，不声称动态测试已过；证据目录为工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R接口证据_20261011/，本增量应追加至工程/我们没有翅膀R/作品skill/SKILL.md。


## R 装载证据增量（追加，不覆盖既有结论）

- **容器规模**：R 本机原 22 个 SOB 容器，共 42690 处重定位；map0..5 数量分别为 1237/2273/18/246/38916/0。其中 84 处为数据区未对齐四字节写入，代码区仍保持 4 对齐。
- **装载器现状**：lucifen_sob_loader 严格 parse_container，复用 source_ir.py 仅 4 个 defs（InvalidSource、NonContainer、sha、parse_container），其余 B0 逻辑未并入。重定位按 5 表处理：变量 record 第一字段、native 向量、named record 第一字段、func_lib base+offset、module base+offset；六表中 table5 非空即拒绝，保留可变字码。
- **原码对照**：22 原机器码 0x4A6E7B..0x4A6F39 逐字节对照全 PASS；其中 0/2 向量值是合成，1 是 809 静态原生候选地址，不是原进程注册表，也不等于全部装载器完成。
- **user_var.sob（SOB1）**：8 字节头 + 3724 初始数据 + u32 count 768 + 每 record <BBII> 10 字节 + u32 local_count 2 +（3104->3112，3108->3120）+ u32 reserved 0，精确 EOF；type0=764/type1=3/type2=1，flags 2=715/1=24/0=29。type1 使变量 record 地址指向数组向量槽，槽内容指向 database+decloffset，其余 record 地址是 database+offset；768 地址与原代码 0x4A6BB8..0x4A6C1A 一致，3724 初始数据修正与原 0x4A6C1A..0x4A6C67 一致。未执行分配器及额外 save/undo 副本维护，未知 flags/extra 保留，不声称全语义完成。parse_sob1 返回的 tail_fileoffset 指 reserved_count 字段位置，不是 local 表首。
- **启动构造器**：对 original main.sob + func_lib.sob + user_var 数据，构造器两 named 符号 ScriptBootFlg=this+10c、retAppProc=this+110。retAppProc 输入受控 raw word0 → main 偏移 0,8,16,28,908,920,928，首 native 0(0x41B3A0)，参数 ASCII GameInit；输入 word1 → 偏移 0,8,16,28,40,52,64，首 native 35(0x412670)。两轨迹均停止于 native 体前，实际执行 native 数 0，无 stub，不能当原启动流程、Callback 有效值或 BOOL 类型。原 0x4A79D0/4A79F0/4A7A10 仅合成 context 验证 push0/suspend pushPC/restore popPC，不是实际调度器。
- **路径**：证据统一工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R装载证据_20261011/；工具同工程编程组/工具/lucifen_sob_loader.py。
- **未完成**：100% 原画音、四版剧本尚未达成。


## 增量：R调度与DLL只读证据（20261011）

### 已核实（受控夹具，非原启动观测）
- 原版R main+func_lib+user_var，retAppProc word0；原VM9指令执行 native0，真实native写state2，唯一模拟API lstrcpyA 走成功路径。
- 原调度器41BEE0保存main续行offset956于VM栈后请求GameInit，停止于原装载体前；main有12字节局部空间。
- 11合成状态/VM返回夹具走原VM/调度器，仅到load/cleanup/第二次VM入口，未填未知返回；state3真实表项直接return0。
- 仅重放原4A717A..4A718F发布块：已核实重定位的GameInit置4000000，设置PC且push NULL保留父PC；未执行文件读取/分配器/模块列表生命周期。
- GameInit 5指令后 native6 selector21 读 global5357E4；受控0/1分别到 native796(414530) 与 7(411650)，均停体前。非零1不是有效对象或原启动真值。
- 静态调用40C219→4A0CD0：caller suffix tvpgl.dll；LoadLibraryA IAT5181A4 于4A0D2A，HMODULE存this+4(4A0D32)；GetProcAddress IAT5181A8，可见符号tvpglConfig。40C23C→48A3F0 setter：NULL或+4为0→global0；非空且+4非0→global对象指针（3CPU受控夹具通过）。完整DLL加载工厂/接口ABI尚未执行。
- R安装介质4个PE32DLL只读元数据47 exports：DS_SPRITE(GetDShowGdiSpriteCtrl/GetDllVersion)、DS_MOVIE(GetMovieObject/GetDllVersion)、tvpgl(GetLibrary/tvpglConfig/tvpglConfig2)、wuvorbis 40 exports。

### 工具边界
- lucifen_guest_api.py 仅覆盖有效非重叠NUL字符串成功模型；260上限是夹具保护而非引擎容量，不得声称SEH或整个WinAPI等价。
- lucifen_pe_inventory.py 只读元数据。pefile 2024.8.26 官方portable wheel ZIPimport，未全局安装。

### 未验证
非原版端到端；无画音对照/100%剧本。上述受控分支与global取值不得当作原启动真值或有效对象。

### 下一步
核实tvpgl接口ABI与实际依赖环境；严禁绕过失败分支填假返回。

证据索引：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R调度与DLL证据_20261011/README.md。


## R作品 skill 增量候选
- 指纹/入口：tvpgl.dll SHA63e9308c2e89445daa1d427c5b5e1ed1ce863111ca722a5f3b6dd966d065a985；GetLibrary@10001C10 静态 alloc 940 字节，field0 vtable10048108 含析构入口，cdecl 初始化10001000(object,CPUsettings)。受控执行完整 initializer：cfg非NULL全零0x98、FS:[0]映射客体，返回0；未执行 factory allocation/DllMain/Windows loader/异常处理/实机启动。
- 客体：field+4 数据指针1004D1F0，+8..3A8 有233函数，不是233个虚方法；原EXE4A0D91..4A1ABE 把后234字段逐值发布到全局，原块CPU对照全部一致；GetProcAddress查GetLibrary。
- 设置档：11受控设置档=10个单byte（8C/8F/95/91/8E/96/94/90/92/8D）+全开；8F变128字段、全开130字段；真实原启动配置/CPU选择仍未知。
- CPU核验：scalar ordinary1000F4E0、scalar HDA1000F6B0；单8F ordinary1003BAE0/HDA1003BDC8；全开 ordinary1003C260/HDA1003C550。去重6入口112缓冲（按entry/signed_len/alignment去重），559576像素字比较；填充1001DA10 9长度；覆盖256alpha、规则色值、4096随机像素、负/零长、循环边界、两优化普通入口两目的对齐、源不变/目的canary。
- 像素规则：标量ordinary仅RGB d+floor((s-d)*a/256)，输出alpha0；3个HDA保留目的alpha，RGB同式。优化ordinary：n>4，目的地址&4先单像素；bulk while i<n-4每对若两alpha都255全拷贝，否则四通道均/256差值插值；尾像素alpha255直接拷贝。同src首像素FFFFFFFF：len1结果FFFFFFFF；len5目的8对齐且第二src80FFFFFF结果FEFEFEFE；len5目的低位4首像素FFFFFFFF；两优化ordinary皆如此。
- 公式边界：单像素通用公式假说被257长度原码反例否决，未并入；buffer参考经两优化入口56缓冲279788像素对照通过。函数入口与扫描线长度/对齐必须保留，不能用单一混合公式简化。
- 静态/上游：66条引擎间接call静态候选、21不同字段（线性Capstone潜在引用，非可达/执行全覆盖）。github krkrz/krkrz 上游visual/tvpgl.h/c 已按commit fd5c4baa6a2ef5978db1bd043634351f48667daf下载工具目录、保留LICENSE与哈希；header有相关TVP混合签名，仅研究线索，不证明R二进制来自同一版本或全部可直接替代，不外发源码。
- 证据/工具：证据目录 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R绘制接口证据_20261011/；lucifen_cdecl_probe.py受限cdecl客体助手；lucifen_pixel_reference.py独立数学RGB与成对buffer参考，仅验证/移植依据，尚未连TJS生产链路。无全部配色/233ABI/特效/原画音全对照完成宣称。下一步：真实表面对象ABI、原启动CPU配置、TOB/演出实际调用链。

证据索引：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R绘制接口证据_20261011/README.md。

## 2026-10-11 R版表面对象与填色证据

按同一非翻译长任务哈希规范复用。EXE SHA `b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`。原表面构造 `4D46D0`，field0 vtable `51B7EC`；字段 +4 width、+8 height、+C signed pitch bytes、+14 四 int 裁剪、+3C 缓冲、+40 depth byte。虚方法仅限该原类：vslot+10→`458230` 读 pitch，+18→`500150` 读 buffer，+34→`48A310` SetClip，+38→`431B30` 复制 clip，+3C→`431B20` 返回 clip 地址；不推广到其他继承类或四版。

受控双 PE guest 完整原 DLL 初始化/发布原调用槽后，原 `4D4BD0` thiscall 五参(R,G,B,requestedRect*,dirtyOut*) 连续调用原 DLL `10001D20` fill32、原 Getter、原 Pixel 核 `1001DA10`；无未知函数返回 stub。使用预映射像素、几何、深度和原 setter；DLL 模式由控制模块 handle marker1 发布，非真实 Win32 装载观测。

32/8 位各 28 组合：DLL/原软件回退、正负 pitch（32±32，8±12）、7 种 None/显式/空/出界 rect，bytes/行 padding/canary 比对通过。32 位像素写完整 `00RRGGBB`，不能据高字节直接断定显示 alpha，R/G/B 均截低 8；8 位仅第一分量低 8 写字节，调色板与颜色空间未验。12 边界组合：NULLpixel 拒绝、16/24 拒绝、8/32 接受、NULLdirty 允许。

空显式 rect：DLL 库本体无绘制且保持 lastDLLrect；外层 member 仍 AL1，dirtyOut 非 NULL 复制旧 lastDLLrect；fallback 外层 AL0、caller dirty 保持。独立 caller marker(1,2,3,4) 与 global marker(9,8,7,6) 区分验证。3 步状态链 DLL 有效 A→fallback 有效 B→DLL 空请求，最后 dirty 返回 A 非 B；backend 切换不等于真实卸载重载。

9 原 SetClip 夹具：先判请求 positive extent，无效 AL0 旧 clip 不改；有效才 left=max(0,left)、top=max(0,top)、right=min(width,right)、bottom=min(height,bottom)；clamp 后不再判空。例 (10,2,11,3) 在 6x4 接受 AL1 存 (10,2,6,3)，NULLrect DLL fill 不改 bytes 但 AL1 复制该倒置 dirty。只运行正高度倒置宽度见证，不提交倒置高度给像素循环；不要自动修正原行为。`fill32_span_reference` 只对有效 clip 域作独立几何/完整 word 填充对照，不等于全部原 member 返回/脏矩形状态机；`set_clip_reference` 保留 clamp 后倒置；`invoke_thiscall_args` 校验 callee 清参和真实 EIP/ESP，不是 OS sandbox。27 fill caller/12 constructor 静态 direct call 候选，非原 native 注册映射、完整可达/实机轨迹证明。

证据目录 `工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R表面操作证据_20261011/`。新工具 `lucifen_thiscall_probe.py`、`lucifen_surface_reference.py` 仅验证/移植依据，未接 TJS 生产。仍缺 Win32 DIB 分配/生命周期、真实启动环境、上层原生/剧情/特效映射/画音对照/全部忠实剧本。

## 2026-10-11 原生处理函数到表面填色的证据

R作品知识：本批 direct CFG 工具从 809 个静态候选 slot、803 个 unique handler 与三个 target（4D46D0 构造、4D4BD0 填色、48A310 SetClip）出发，追踪真实指令边界，而非线性扫描数据；原 R EXE 指纹为 b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33。walk 覆盖 2095 个入口、131038 条指令、4315 条 direct call/tail edges，并保留 2634 个间接控制流缺口；无读、解码、预算 diagnostic 不等于完整覆盖。构造候选 46 个 handler，填色 13 个，SetClip 未找到 direct 路径，虚调用等仍未知；它们均为静态潜在路径，存在条件不可行风险，walk 入口可含跨函数直接跳转，并非准确函数边界或运行 ownership。严格 SOB 链接元数据与 13 个填色候选 slot 交叉，得到 6 个 slot、38 个 refs：429 有 22、238 有 3、239 有 6、791 有 2、793 有 4、43 有 1。候选 322 无本批 22 个 SOB 代码容器直接引用，不能推断整个 TOB 或动态无使用。单个原处理函数 420B50（候选 slot322）已做受控连续 CPU 验证：原派生构造 4540B0→原基类 4D46D0，vt 5197F4；cast 41D860 执行原类型 getter 454960 AL4；native cdecl 一个 argsFramePtr，frame 八个 u32=obj,left,top,right,bottom,R,G,B，coord 保持 signed32 位形，RGB 只取低 8。它通过 IAT 5183A8 调用 USER32.SetRect；为不填假返回，手动映射本机 C:/Windows/SysWOW64/user32.dll（原 PE32 本机版本，preferred base 69E00000，SetRect 69E31E30，非 forwarder）并绑定该 IAT，执行其完整原码；host API 原码不是 R 自带 DLL 或历史系统证明，未走 Windows loader/DllMain。下连原 derived 455460→base 4D4BD0→tvpgl 10001D20→原 kernel 1001DA10，未知返回 stub0。32/8 depth × DLL/原回退 × 正负 stride × 7 显式 rect 共 56 通过，保留输入 frame、padding/canary；10 NULL 对象/NULL pixels/16/24 拒绝/32 接受边界通过。derived+58 通知 sink=NULL（原 ctor 状态）；仅观察 +51 成功分支写 1，不宣称全部 dirty 回调或屏幕刷新。空 rect DLL 原 native EAX1 且 +51=1/旧 global dirty 不变；回退 native0/+51 不变。本阶段生产工具拟 lucifen_direct_cfg.py，仅作验证/移植依据，未做 TJS 生产。20 个独立合成 control-flow 验收含条件两臂、LOOP 三种+JECXZ、局部自循环、已知入口 tail、间接 call 继续与 jmp 停止、非法字节、范围、预算、读错、terminators、collector 去环预算。Capstone 5.0.7 的 LOOP 不在 jump group，曾漏路径，已由 editorJSON 修正显式助记符；补丁前缀缩进不匹配，root 仅机械保留唯一匹配原行缩进，不改变 editor 表达式。证据拟存 编程组/演出链路/R原生表面调用证据_20261011/。仍缺真实运行注册向量、VM 到此 native 实际参数、所有 cast 类型、nonnull 通知 sink、原 Win32 DIB 和生命周期、所有图层、全部演出脚本与画音对照。下一阶段优先有 SOB 引用的 238/239/429 操作及原 DIB/资源绑定，并准备可验证原作只读宿主；Windows 受限 token/private desktop 方案仅规划，无实现/验证，不写已可用。goal 已由用户清除误建 resume 后正式重新创建 active，无预算，四版原始全部目标不缩小。

### R 只读宿主前置（线程 PASS，primary 未通过）

- 线程 PASS：C#5/.NET4 x86 fixture，CreateRestrictedToken flags=9（WRITE_RESTRICTED+DISABLE_MAX_PRIVILEGE）+ custom restricting SID + ImpersonateLoggedOnUser。普通token前两类WRITE可以打开(仅权限查询未写)，win.ini普通已拒；受限后三类READ均成功、WRITE均拒error5。
- 正控：仅对已 grant 该 SID 的工作区临时目录 CREATE_NEW 16 字节 canary，原 3 文件 SHA256 不变。
- 负控：无 ACL 目录、已有 canary、工区外输出均失败且不生成/覆盖；SID 以 SecurityIdentifier 授 ACL，icacls 未知 SID 映射失败、未改原 ACL。
- primary 未通过：restricted token + CreateProcessAsUserW 固定自生成 child，无 inherit handles，child 仅 CheckFiles/IsTokenRestricted，未运行原作、未加载原作DLL，fixture源码无GUI/后代创建，系统DLL/OS对话框不是本批证明的零活动。。CREATE_NO_WINDOW 退出 0xC0000142 无 canary；改 DETACHED_PROCESS 后 wait 非 0，清理后子进程消失、无 canary。
- 未记录 DLL 初始化根因和 wait 值，不归咎特定 DLL/权限，不报 primary guard 通过。probe 非 OS sandbox，缺 private desktop/windowstation、default token DACL、job/树清理、原作动态。下一阶段补 startup 与 private 宿主，此前不加载原 DLL/游戏。证据拟放 编程组/演出链路/R只读宿主前置证据_20261011/。

补充实测：4 个正式源码 csc x86 全部编译成功；正式目录 RestrictedThreadProbe.exe 启动被拒 AccessDenied，随后文件不存在，正式线程重跑无 PASS、无 canary。旧候选 RestrictedWriteProbe.exe 仍在，其先前线程 PASS 收据有效，但不能套用到失败的正式路径。原因未查明，不据此下结论。

## 2026-10-11 R对象接口与空合成原码证据

# R对象接口与合成证据（20261011）

## 一、证据口径
结论出自受控 Unicorn x86-32 原 CPU 执行，guest 存储预分配；原分配器、Windows 加载器、DIB 与真实场景均未执行。工具为 lucifen_instruction_evidence.py 与 lucifen_cdecl_observer.py，产物见证据目录“R对象接口与合成证据_20261011”。所有测试处于预分配受控状态、无 child、非生产接入；0 diagnostics 与候选槽映射不构成完整性证明。

## 二、238/239 输出槽与边界
238：入口 0x41E850、工厂 0x4BA6A0、type 9；239：入口 0x41E880、工厂 0x4BA7C0、type 10。公共帧四 u32：width、height、format_low8、extra_low8。隐藏输出槽为原调用者栈 SP0+4，其 framePtr 复用为输出槽。工厂栈为 return_pc、SP0+4、width32、height32、caller_EDX_upper24|format_low8、caller_ECX_upper24|extra_low8。序言清零输出槽后，以 0xD8 调用原 operator-new 0x50577F 并在分配器 body 前停止，故属未分配边界。wrapper_return 对输出槽的最终读取仅静态观察，工厂成功/失败未动态证明。

## 三、429 转换、真值与绘制
429 入口 0x4249E0，帧 u32：object、bitmap_argument、mode_word、id_word、truth_word。object cast 静态接受 type7..10；动态 type9/10 经 embedded+0x30 得 outer+0xBC 的 auxiliary。bitmap cast 实为两条各自独立、均已验证的选择：其一，type4 对象自身即作为 bitmap；其二，outer type9/10 经 cast 返回 owned bitmap+0x34。二者不得写成需要两种类型同时存在才能成立。aux 被调方 0x45AFF0，栈为 return_pc、bitmap_argument_ptr、(truth_word&0xFFFFFF00)|mode_low8、id32、(truth_word&0xFFFFFF00)|bool(truth_word!=0)。真值用整个 DWORD：非零即真，高 24 位保留，不只看低 8 位。返回：源 cast 失败 -1；目标 cast 或 aux 缺失 -2；成功 0；argument 无像素 1；绑定缺失/尺寸不匹配 2。绘制上，空列表原 renderer 写 bitmap argument；aux 绑定 bitmap 仅在 disjoint 时不变；same-object alias 也写 bound 像素。

## 四、清屏与全局
aux+0x50 clear32 写整个 u32 含高字节；aux+0x52 clear8 取 (colour32>>16)&255，调色板语义未知；aux+0x55 非零则空列表保留像素。全局 0x529E6D 受控 0/1，真实启动值未知。

## 五、验证数量、notify 失败与未验证
计数：direct_cfg_entries 18、instruction_rows 1336、direct_edges 59、indirect_gaps 47、diagnostics 0、instruction_helper_groups 9、observer_helper_groups 6、238_239_call_cases 16、factory_allocator_boundary_cases 8、429_cast_call_cases 14、empty_compositor_pilot_cases 4、empty_compositor_matrix_cases 48、alias_and_clear_boundary_cases 11、aux_attach_cases 4。

notify1 失败：两类型 aux_bitmap 在无效 fetch 前已赋值；trace 末次调用 0x50762A 经 IAT 0x51814C 指向 KERNEL32.HeapAlloc，客体 IAT 未绑定，实际跳到未映射的 0x1277C8，该异常既非 API 失败返回，也非分配成功，本身未执行 Windows loader。

未验证：原堆与 Win32 DIB 分配、原 manager/全局启动、notify=1 完成、非空 child/list 绘制、type7/8 动态状态、真实原生向量/VM 参数、四版本全场景/脚本/音频/帧对比、TJS 生产接入。

## 六、下一阶段
解析 IAT 与真实分配器边界，恢复 notify=1 与非空 child/list 路径，补 type7/8 动态状态与真实 VM 参数，再做四版本对比和 TJS 生产接入；在此之前，候选槽映射与 0 diagnostics 不得视为完整覆盖。

证据：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R对象接口与合成证据_20261011/README.md`。原码指令详情仅本地存储，API只接收主代理生成的契约元数据。

## 2026-10-11 R原脚本实参与VM到工厂连续证据

# 剧本实参还原：source writer-to-native 片段知识稿

## 来源范围（source scope）

本稿只覆盖 31 条 original source writer-to-native 片段，分布在 8 个 SOB 模块，每条仅受控 2 个 variable/stack/module 状态。合计 62 个 case：候选 429 占 44、238 占 6、239 占 12。31 条引用由 9 条构造引用与 22 条合成引用组成，二者相加即 31。前述62例仅到native入口，未执行native函数体；另18例连续执行native wrapper与factory前段，停在allocator入口而未执行分配器，二者不可混同——18例并非「同样入口实参样本」，其已执行的工厂原码不得抹去。整批均未验证完整模块CFG、真实全局/场景、完整native生命周期或100%还原。证据为「R 剧本实参证据_20261011」，工具为 lucifen_native_frame_probe.py 与既有 lucifen_cdecl_observer.py。op5 初始参数看似 word0，但经 op40 运行期改写为 VM_SP，故非恒定 NULL；可变 code 必须保留。

## 参数实测

模式分布共 5 组，计数 7、9、9、3、3，合 31。original CPU 片段动态事实有三条：op40 把 opcode5 参数字 word 由 0 改为当前 VM_SP，op8 按源序 push；native 帧指针等于 prepush SP，SP 增加 argc*4；进入 native 时 ctxPC 已是 call+12。它们是实测动态结果，不是静态推断。

静态 literal 来自构造引用：238 在 config1.sob 偏移 10572、config2.sob 偏移 10232、saveload.sob 偏移 19320，字面为 800/600/32/2；239 在 config1.sob 偏移 11052 与 31976、config2.sob 偏移 10712 与 28580、saveload.sob 偏移 19492，字面为 800/600/32/0；gameinit.sob 偏移 2160，字面为 800/600/32/1。构造帧共 3 类，与上述 literal 对应。

## 独立对照

editor 侧实现独立 shadow helper，实际对照由 root 实跑完成，editor 未自行运行该对照。覆盖 ops 5/8/13/31/32/35/40。frame、VM_SP、call location、handler、step count、整源模块字节与受控栈跨度均与 original CPU 相等；不支持项、预算与错误原样保留。helper 分组为 12。

渲染侧候选 429 的 5 个 word 为 object/bitmap/mode/id/truth，属受控数据传播，只能说明受控输入可传递，不可据此推断真实对象指针或运行状态；受支持操作包括 address literal 与 dereference 的区分，以及 stack-relative 输入；wholeDWORDtruth 与 low8 mode 分属不同判断。controlled 429 各数值仅代表受控 case，勿视为原剧情参数常量。

## 依赖与未知

首次静态定位虽借用 B0，但 31 个固定 metadata 已与原 SOB 的 opcode/operands/offset/relocation 独立对账；正式回放使用随附 metadata 与 mature loader，不导入 B0。并非完整 B0 审查，也非全量独立 decoder，结论仍有边界。native 映射依据 809 条静态构造候选向量，真实运行时向量尚未观测。受控 2 状态不能外推为真实场景行为。

## 下一步

恢复原始 allocator 与 objects，补齐 actual caller 可达性与状态；再产出保真目标脚本，保留 source/raw/source-offset/unresolved 元数据；随后做 TJS 集成、真实帧与音频，覆盖全部四个版本。

## 原VM到工厂分配入口的连续证据

9构造源片段×2状态共18；原VM→原238/239→原factory前段连停原operator new 50577F；out原caller参数槽先清0，0xD8分配请求，未执行allocator；guest FS:[0]零页预映射为受控SEH存储，非真实Windows环境；起初未映射零页的真unmapped read停4BA6A7，不填fake返回，补客体区域后通过。


证据索引：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R剧本实参证据_20261011/README.md`。


## 2026-10-11 R非空图层受控原码增量

# R非空图层合成与未归属对象析构（20261011）

本稿由 editor-easy 提供，可作为证据目录 `README.md`，并追加到 R 作品 skill。root 执行原码核验与 Git；editor 提供独立 reference 代码与知识稿，不宣称整引擎实现完成。产物只暂存后由主代理应用。来源仅为主代理生成的契约元数据，无原游戏脚本、字节或素材。目标四版本 100% 还原尚未完成。

---

## 1. 范围与方法

- 受控环境：在 Unicorn x86-32 中执行原 R EXE + 原 `tvpgl.dll`，原件只读。
- EXE sha256：`b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`。
- 证据路径：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R非空图层证据_20261011/`。
- 新工具：`lucifen_opaque_layers_reference.py`。它是本批交付的独立纯 Python 32bpp opaque fixture oracle，不是 TJS 生产代码。
- 装载事实：10001000 是客体入口地址，不是 GetLibrary 参数；cfg 为 0x98 字节零；手工 map base 10000000，调用实际参数 libobj, cfg。
- 原发布路径：EXE 原 publish block `4A0D91..4A1ABE`，再由原 `48A3F0` 以 `wrapper+4=1` 发布 `5357E4`。未经过 OS 加载 DLL / DllMain，因此不证明原启动 CPU flags。
- 真实全局 `5357E4` 是 TVPGL library wrapper，不是 manager。

---

## 2. ABI 与结构偏移表

| 对象 / 入口 | 偏移 / 地址 | 语义 | 备注 |
|---|---|---|---|
| child 真实构造 | `456800 → base459590 → reset4568D0` | 构造链 | vtable `519854` |
| child visible | byte `+8`，经 `4581E0` | visible 标志 | 受控读取 |
| child enabled | byte `+15`，经 `458260` | enabled 标志 | 受控读取 |
| child id | u32 `+4` | 图层 ID | selector 使用，含高位用例 |
| child sourcebitmap | ptr `+1C` | 源位图指针 | 本批 `alphaFlag=0` |
| child ctor | `+18` | owner 指针 | 观察为 NULL |
| child ctor | `+20` | owned transform 指针 | 观察为 NULL |
| bind | `456910(bitmap, sourceRectPtr=0, x signed32, y signed32)` | 绑定源与坐标 | sourceRectPtr 为 0 |
| 全图 native | `4249E0 → 45AFF0 → child vt+60 = 457900` | 整图合成路径 | 传 NULL clip |
| 分块 native | child vt+64 = `457BD0` | 分块合成路径 | 传 rect clip |
| primary list | aux `+14` | 节点入口 | 受控手工预分配 |
| node | `+0` child，`+1C` next | 链接节点 | 非原插入/排序/归属生命周期 |
| aux+55 | 非零 | 保留既有底图 | 受控分支 |
| aux+56 | 非零 | 跳过 primary | 受控分支 |
| mode | low8 | 0 所有；1 ID 相同；2 ID 不同；其他跳过 | 只取低 8 位 |
| chunkglobal | `529E6D` | 受控 0/1 | 控制整图/分块 |
| 全局 | `5357E4` | TVPGL library wrapper | 不是 manager |

---

## 3. 合成与分块行为

- 整图路径传 NULL clip；分块路径传 rect。
- 宽 320 高 17 实测 clip：`[0,0,320,8]`、`[0,8,320,16]`、`[0,16,320,17]`。
- 每 band 按 node 顺序，两 child 各一 call。
- mode 只取 low8：`0` 所有，`1` ID 相同，`2` ID 不同，其他跳过。
- visible / enabled 非零时进入；`aux+56` 非零跳过 primary；`aux+55` 非零保留既有底图。
- 次列表和 truth gate 未在本批验证。
- 其它宽度阈值只做静态观察，本批不宣称动态覆盖全阈值。

---

## 4. 未归属对象析构

- 析构 6 组 flag：
  - `0`、`2`、`80000000`：正常 `ret`，`eax=child`。
  - `1`、`3`、`80000001`：到原 operator-delete `44B6B0` 入口，stack arg 为 child。
- 仅低 bit 决定 delete 路径。
- 原 vtable 均降为 base `519980`；source 未改。
- free body 不执行。
- owner / owned transform 均为 NULL。
- 因此不证明原 unlink、owner 非空、owned transform 释放或堆 free 成功。

---

## 5. 测试数量与通过口径

- 成功一次单 child 原 DLL pilot，完整 6 个 u32 像素（含高 byte）copy。
- 主 matrix 46 例 = 32 + 9 + 4 + 1：
  - 32：type9/10 × chunk0/1 × order 正常/反向 × dststride 正负 × srcstride 正负。
  - 9：selector（mode / ID 含高位）。
  - 4：flags（hidden / disabled / disableprimary / noclear）。
  - 1：宽 320 高 17。
- 原 child 构造返回 child 指针，bind 返回 0，原 native429 连 compositor/draw 最终返回 0；与独立 oracle 比较 whole buffer 的 source/frame/padding/canary。
- 析构核验 6 组通过。
- `sourcebitmap alphaFlag=0`，opaque blend byte0；不外推 alpha、色键、变换、8bpp、影片/特效、真实场景。

---

## 6. 失败试验与修正

- dummy 空 wrapper 首次导致 `UC_ERR_FETCH_UNMAPPED`，EIP `3866`，无 child draw，未报成功。
- matrix 初次参数 `x=-1` 被 u32 工具 guard 拒；root 将 signed 坐标转 32 位位形后重跑通过。
- destructor 核验初次误用快照字段名导致 `KeyError`；改用已有 `stop_reached` / `stack_words` 后 6 组通过。
- 以上均为 fixture 核验错误，未修改原指令，未填 fake 成功。

---

## 7. 已知边界

- 受控 primary list `aux+14` 节点与 `node+0 child`、`node+1C next` 是手工预分配的链接节点，不是原插入/排序/归属生命周期。
- 次列表和 truth gate 未验证本批。
- 其它宽度阈值只静态观察，本批不宣称动态覆盖全阈值。
- `5357E4` 为 TVPGL library wrapper，不是 manager。
- 未 OS 加载 DLL / DllMain，不证明原启动 CPU flags。
- `alphaFlag=0`、opaque blend byte0；不外推 alpha、色键、变换、8bpp、影片/特效、真实场景。
- 析构仅覆盖低 bit 分支；不证明原 unlink、owner 非空、owned transform 释放或堆 free 成功。
- 目标四版本 100% 还原尚未完成。

---

## 8. 证据文件与复现

- `nonempty-original-compositor-matrix.json`
- `unowned-child-destruction-boundaries.json`
- 单 child pilot 三份：child-ctor-bind-pilot.json、one-child-original-compositor-pilot.json（失败）、one-child-original-DLL-compositor-pilot.json（通过）；其中一次失败。
- opaque-reference-verification.json 含 11 组独立硬编码核验（含错误顺序负控）。
- root 执行收据不是 editor 自验。
- 包内 verify-original-matrix.txt、verify-destruction.txt、verify-reference.txt 可作为 python stdin 命令回放；输出仅工作区临时新目录，且不得覆盖历史。

---

## 9. 下一步

1. 原 primary list 插入/移除与归属。
2. allocator 及原装载路径。
3. alpha / 变换 / 真实脚本状态联动。
4. TJS 接入 + 四版全画音对照。


## 2026-10-11 R对象归属列表受控原码增量

# R归属列表候选实现知识（editor-easy）

## 范围
证据新目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R归属列表证据_20261011/`；工具`lucifen_owner_list_reference.py`纯fixture oracle非生产。root执行原码核验与批次审查，editor仅交候选实现知识。scope原EXE sha：`b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`。

## 结构
原ctor 459620，owner vt 5199E8；head+4、tail+8、bound+0xC；node 0x24：child+0、dirtyRect+4（受控-1）、key+14、extra+18、prev+1C、next+20；child+18指向owner。旧判断已由原ctor与64条连续原码纠正：aux ctor在0x459DC0调用0x459620(aux+0xC)构造嵌入owner；aux+0x10是owner.head，aux+0x14是owner.tail，node+0x1C是prev、node+0x20是next；renderer自同一列表tail沿prev逆向遍历，并非另一种node结构；原aux+0x18=self是嵌入owner+0xC所关联的aux通知对象，不是位图bound；原分配/插入/真实剧情仍未验证。

## 重排459890/4599A0
before_equal/after_equal：thiscall ECX=owner，args child,key32,skip_word；ret 0xC，仅AL是布尔，EAX高位保留原中间值。NULL child或非成员→AL0且不变；skip low8非零且旧key==新key→AL1不动，child mark+9保持0。其它走原unlink/relink，同key分别before `>=`、after `>`，unsigned32比较；原child vfunc+10=458220置byte+9=1，无假回调。

## 矩阵与数量
240原方法完整返回；editor独立reference比较：224=2入口×4选择位置×7新key(0,10,20,25,30,80000000,FFFFFFFF)×4 skipword(0,1,100,10001)，另4 NULL/非成员、12 single。初始key 10,20,20,30；node预分配，child ctor原456800，手工关联owner，原插入未执行。检查全链head/tail/prev/next、key、extra+18、node其它guard、child owner及marks；keys/order输入只读。非成员缺key guard由editor修订并纳入正式复验。

## 插入
4596B0/4597A0共6：NULL child原DWORD1；already-owned原DWORD2；有效owner且child的owner字段+18为NULL时到50577F入口，size0x24；不是ECX owner NULL，不执行allocator，无owner变化。不宣称成功插入或allocator失败3动态验证。

## 移除/清空/析构
459AB0/459670/456850共14：remove NULL/missing真实AL0 return不变；head/middle/tail/single停44B6B0 node free前owner/list/child owner尚未变；clear空list完整return，4节点先清第一个child+18再停node free，其余owner尚不变；owned child析构3位置×flag0/1均先到node free入口、vt已降519980、owner尚未清，未到object free。dirtyRect=-1且bound=0避免原dirty allocator，不外推bound非NULL。

## 交付与命令
固定JSON：owner-original-reorder-matrix.json、owner-insert-allocator-boundaries.json、owner-remove-clear-destructor-boundaries.json。命令verify-reorder.txt/verify-insertion.txt/verify-removal.txt，outputs在workspace临时新目录不得覆盖旧；owner-reference-verification.json 记录10组独立手定期望核验（同键前后、unsigned high key、skip low8、NULL/非成员、缺key拒绝与只读）。

## 局限与下一步
预分配手工owner/node，非原堆、非实际源剧情/notify非NULL/生成渲染列表；无fake HeapAlloc/free或跳过函数填成功。宿主primary启动前置未过，原码仅Unicornguest，不运行OS原EXE/DLL。四版全部剧本/IR/TJS/全画音未完成，goal active。下一步原allocator及owner→render-list派生/更新，再接原VM/TOB资源与TJS忠实剧本。偏移/地址均十六进制。

补充：first综合知识+补丁请求finish length8192，仅405可见tokens，无候选，不作交付。


## 2026-10-11 R嵌入列表与反向绘制增量补正

# R 嵌入归属列表与反向绘制原码证据

> editor-easy 增量补正稿，供 README 与 skill 复用。root 仅提供契约元数据，不含原字码/脚本/素材外发。本阶段不覆盖原历史记录，skill 增量更正，旧证据目录另建补正文件。

## 一、契约元数据

- 工具：`lucifen_owner_render_reference.py`（fixture-only；有效 primary native wrapper 与 tail_order，仅 math 辅助，无 productionTJS/cast/secondary）。
- 目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R归属与反向绘制证据_20261011/`。
- 原 EXE hash `b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`；TVPGL hash `63e9308c2e89445daa1d427c5b5e1ed1ce863111ca722a5f3b6dd966d065a985`。

## 二、归属列表（owner 嵌入）

原 aux ctor `459DC0` 调用 `459620(this+0xC)`，owner vt `5199E8` 位于 aux+C。相对偏移固定：

- owner head +4 → aux+10
- owner tail +8 → aux+14
- associated_aux +C → aux+18 = self
- node size 0x24；child +0、key +14、extra +18、prev +1C、next +20

原 renderer `45AFF0` 从 `aux+14`（tail）沿 `node+1C`（prev）倒序。初始节点/链接由夹具预分配手工关联；随后原重排修改链/marks，原 renderer 遍历同一节点，全链 head/tail/prev/next 与像素经独立对照；不冒充原堆生成初始节点。

**重要补正**：旧判"不同 node 结构"错误。历史 raw 测试仍是真实受控结果，但不能沿用旧结构解释；原真实受控 raw 像素结果保留，但“不同节点结构”解释作废，由本阶段补正替代；不改写历史记录。

## 三、64 组合矩阵

维度 `64 = type9/10 × chunk0/1 × native424450/4244E0 × 8case`。三 child 的 key 为 10、20、20，三者重叠 1 像素但 u32 source 不同，手工关联出完整 nodes。原 aux ctor、child ctor/bind、wrapper cast+reorder、native429+compositor、原 TVPGL 全部实际执行；排序与逆序对照独立 editor helper，整个 dest 和 padding 对照 opaque oracle 相等，source/frame 保持不变。

source 绑定后原 mark 已为 1；夹具再调用原 setter `458220(0)` 受控清 mark 后核对 reorder，属受控核验，**非剧情真实帧**。

## 四、native 布尔与分层

native frame 为 4u32 `(outer, child, key, truth)`；候选 411/412 注册 809 列表按 callVA 给出，真实运行 vector 未观测。whole truth 以 DWORD!=0 转 bool；callee `skipword` 高 24 位实际取自 caller frameptr，写为 `高24 | bool`。native 输出 0/1 并覆写 caller argsframePtr 栈 slot 低 byte，frame 内容不变；helper 只保留判定，不模拟 stack 高位。

**不要混层**：native `0x100` truth 为 true，而直接 owner（`skipword 0x100`）lowbyte0 为 false，二者语义层不同。

## 五、反向绘制排序规则

同键 before/after 反向绘制：**更小 key 后画（覆盖），大 key 先画；相同 key 时，前插者后画、后插者先画**。本 batch 仅 opaque32，不推广到 blend/alpha。

## 六、静态与 SOB 扫描

静态 5 入口共 592 行、14 条 direct edge、20 处间接缺口、0 diag，非完整；复用 direct CFG，存在潜在 native 411/412/790 到 sort 方法（790 为多层）。21 个 SOB0 加 1 个 SOB2，合计 22 个代码容器，扫描原 reloc 表，slot 411/412/790 均 0 refs；1 个 SOB1 为声明非容器。未覆盖 TOB、indirect 与真实场景，不能据此断言游戏未使用。

## 七、产物文件（暂存，待 root 生成收据）

- `native-owner-reorder-to-compositor-matrix-02.json`（64）
- `embedded-owner-render-instruction-evidence.json`
- `owner-reorder-registration-candidates.json`
- `reorder-SOB-references.json`
- `reorder-upstream-SOB-references.json`
- `reorder-native-direct-candidates.json`
- `helper-verification.json`（8 组 root 独立手定期望核验，含错误遍历像素负控）
- `verify-native-to-render.txt`、`verify-source-references.txt`、`verify-helper.txt`

只写工作区临时新目录，不覆盖既有证据。

## 八、过程如实记录

首次 reference 4096 全 reason finishlength，非交付；窄 prompt 后 stop。源码与行为均 editor，root 侧原码验证。SOB scan 首次 mature loader 正确拒 SOB1，改仅接受"类型异常区分声明"后得 22 完整代码容器，未忽略其它 error。mark 核验初次误以 bind 后 marks 0，实际为 `[1,1,1]`，经原 setter 受控清后复验，未伪造成功。

## 九、缺口与下一步

仍缺原 allocator / 插入 / free / 真实源 CFG 及场景、secondary、notify、alpha、全部四版剧本/IR/TJS/全画音；宿主 primary 未通过，不 OS 启动原 EXE/DLL；goal active 范围不变。下一步：原 secondary/notify + 源 TOB 调度，并在有依据前提下验证对象/层序的 TJS 接入。


## 2026-10-11 增量：TOB 原码控制流与静态参数，不改旧知识。

- 工具参考 lucifen_tob_control_reference.py、lucifen_tob_literal_reference.py（均 editor-easy）；验证调用原方法、root 手定期望及批次复核，无 OS 加载原 EXE，预置 ctx 不是完整生命周期。
- 源备份 备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE SHA b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33；418 TOB 源 hash 逐文件全篇 guest 与磁盘前后不变。
- header label 4AC190（case 敏感 rawbytes 首个匹配，NULL 0，absent FFFFFFFF）；table 4AC200 unsigned index；same-module jump 4AD0A0 / call 4AD010 / return 4AD120；返回 PC 不主动写 ctx+42C。
- module=0 call 压 [-2, origin_relative] 即使 missing；return 先弹帧即使 missing。return override 0 保存 offset，FFFFFFFF 表示 codebegin，其他采用 override。
- 全部 840 labels + 58425 Tentries；lookup 1676 / table 59679 / jump 840 / call 2512 / return 2930 真实调用检查。完整 ctx/desc/guards 不变或精确允许变动。文件 corpus-control-results.json、corpus-control-summary.json。
- R 字节调度入口 42F880，看到 '[' 后消费再处理 ' ' 分支到 42FB50；原记录参数入口 42FB50 到精确“未派发前”42FDC2 断点：只 condition1 / static literal selectors 0/1；tag0=>[0,0]，tag2=>[0,u32]，其他非 zero tag + selector0=>[tag,u32]，selector1=>[tag|2,source_ptr]，长度0=>[tag|2,0]。
- 字符串长度计字节，不自行解码/复制/NUL 约束。验证 214821 records / 342881 items / 86094 source pointer items；其他 2287 unsupported selector records / 1507 nonliteral condition locator candidates 保持未验证。locator candidates 218615，signature locator 不证明完整分区。结果 corpus-literal-results.json、corpus-literal-summary.json。
- 手定 8 原记录夹具 + 6 helper groups 共 14（含错 flag / 错 pointer 负控），helper-and-synthetic-native-verification.json；12 入口静态 1069 行 58 direct edges 6 indirect gaps 0 diagnostics，tob-function-instruction-evidence.json，不说全 parser CFG 闭合。4AC640 是附属元数据加载非 main update。
- 复跑：Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB原码控制与参数证据_20261011/verify-native-control.txt' | python -X utf8 -B -；literal 用 verify-native-literals.txt，helper 用 verify-helper.txt，static 用 verify-instructions.txt。脚本创建新证据目录 临时/ISSUE-20261011-02/r-tob-control-replay-01，只新建不覆盖；顺序 control 创建目录然后其他；paths 用 PowerShell 相对 root。
- 批量短函数在 timeout=1000000 时迟迟无进度，终止已确认属于本批的进程，改 timeout 0 并保留指令 count 100000 后 control 3.5 秒通过；内部原因尚未定位。
- 本轮最初大派单 14000 / 独立 reference 7000 / probe 8500 均 reasoning finishlength 无候选；拆短后两个 helper stop；不是已有工程实现绕过 editor。
- 范围缺口：变量/表达式 selector、条件、跨模块加载/分配、真实 handler 全语义、帧音频、四版无损 IR 目标剧本及 100% 完整还原未验证。goalactive。

## 2026-10-11 增量：TOB 动态绑定与无损 IR
R418 TOB 扫描 218615 条记录，59367 条未分类孤岛，3349 条表达式，结构错误 0。
430090 原始绑定函数处理 5 组 variable/native/temp/string/local，6698 例受控 bank 绑定；890 数组条件验证至 42FC44 前，1725 数组参数执行 42FCEC→42FD42 有界块。
42FB50→4A7A30 首表达式入口 2904 条记录，cold/warm 11616 例；原版标志 0→1 时运行时绑定一次、预热跳过；全 VM 未执行。
IR 子代理工作区/ISSUE-20261011-02/r-tob-lossless-ir-02/：418 项字节精确重建 9538168 字节，raw+typed 部分语义未定。
证据位于 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB动态绑定与无损IR证据_20261011/，已完成 root batch review。
工具 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/lucifen_tob_dynamic_structure.py、lucifen_tob_binding_reference.py，editor 作者。
缺失 native callbacks、表达式 VM、完整 handlers、跨模块、全部 4 IR、忠实 TJS、全路线帧与音频；目标仍 active。
实际 bank 分配与全局默认值均未证明。


## R_表达式VM与动态记录证据 20261012

VM 4A7A30/4A7A50。3349 个原表达式乘 6 个受控状态，共 20094 条，对照 editor 独立 lucifen_expression_reference.py；轨迹、真实回调帧、全部 1 MiB live 内存、source 自修改、PE 不变、stack 平衡全部一致。只观察 14 种 VM 操作，不宣称 47 种通用语义。

真实 callback 9/58/571 分别位于 411C40/418650/414160，控制配置 byte、module 两个 flag OR、modifier 键；真实 getter 为 47A230，active XOR1 另一 bank，key 低 8、state 高 bit、AL 与 EAX 上位存在区别。边界组包括：256 设置、50 flag/null、7680 getter、576 modifier 短路、4 未证拒绝、ctor 只到 47A390 前。

418 TOB 内 3794 条动态记录，乘 6 再乘 cold/warm，共 45528；accepted 35094、declined 10434，表达式 40188，首次 bind 20094，实际 native 7512。原 42FB50 真条件/参数执行到 42FDC2 未派发前；false 时实际原函数返回记录末端，opcode 0 反转，false 不读参数；warm 不再绑定但表达式副作用重复。全内存、source、PE、trace 一致。

129 TOB 命令表：原构造片段 42ED56 至 42F374 前，helper 4304C0，ctx+653C 指针；129/256 两种预分配容量均 129 次原 push 一致。与 809 SOB/native 编号不同，尚未证明全部 handler 语义或真实 allocator。

限制：本证据基于受控预分配、静态 native vector；不是完整 allocator、OS 输入生命周期、全部演出 handler、真实场景、忠实 TJS、四版全部画音。宿主 primary 前置仍失败，禁无约束 OS 启动原件。未知情况明确报错，不 noop；完整四版目标不缩小。审查与合并状态以root批次审查和Git记录为准，不永久写“审查尚未写”。

增量证据位置：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_表达式VM与动态记录证据_20261012`。上述新阶段证据补足前文历史阶段的“VM未执行”缺口；旧阶段记录保留。


## R TOB命令表、全源使用与字符串参数边界（2026-10-12）

本README记录当前已验证事实。129个原TOB槽对应102个不同handler；418 TOB的218615条记录全部编号可对账，无未知编号，但4118728字节孤岛语义未定。静态handler为2576行、146条直接边、11个间接缺口；向下direct graph覆盖684函数、54842行、1004个间接缺口。0解码诊断不代表完成。

工具lucifen_tob_command_census.py由editor提供，root依据原码验证。命令25原址43FDA0，两个字符串位于ctx+64D1、+64E2，长度17、16且含终止；IAT518188由原PE描述符确认为lstrcpynA。35472条原record全部经42FB50真实解析、真实调度、真实handler，在首次import call前于43FDC0或43FDDC停止；涉及409个源文件。形状为inline/inline 21118、inline/empty 14054、empty/inline 300。已检查全部参数word、真实首次复制调用参数、empty首项清零及边界、source、PE不变。未执行或伪造lstrcpynA，因此不证明完整handler、truncation或OS调用。43F7F0消费双字段并交444740写目标+3B8、+3C9，且清空原字段；此为静态推断，不称其为语音名或说话人名，须查真实消费链。

受控预分配，不证明全生命周期、真实allocator、未知handler、完整画音、忠实TJS或四版全还原。宿主primary仍失败，禁止无约束OS启动原件。审查与正式回放状态以root凭据为准，完整目标不变。

增量证据路径：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TOB命令与字符串参数证据_20261012`；复跑参见该目录README。


## R 姓名标签与语音条目关联（2026-10-12）

命令25有两个字段：ctx+64D1 长度17（最多16原 bytes）、ctx+64E2 长度16（最多15）。第一字段交给显示对象，vtable 偏移124/128；第二字段与原 VOICE.LPK 文件名匹配。原 labels 只保留 CP932 bytes，不裁决译名，不展开 q/r/运行时变量。静态路径 43F7F0→444740 将目标转写至 +3B8/+3C9 并清空原字段；画面效果尚未验证。

全部 35472 条源记录中：21418 条非空 voice 全部命中原 VOICE.LPK，20319 个不同 stem，14054 条无 voice，0 缺件、0 非 ASCII。VOICE 归档 20418 entries，前后 sha fb9065da961b53b8a0c9d45918349b5787dd0d2d9766d1d9260097490c6b132d；不能把 99 个未直接引用条目称没用。一个原 Ogg 经本地 ffprobe/ffmpeg 无错误，Vorbis 44100Hz 单声道，仅为样本，不是全音频。

35472 原 parser 42FB50→原 dispatcher→完整 43FDA0→42FFF0，共 56590 次真实当前 Windows 宿主 lstrcpynA 调用；目标字段全部 35 bytes，guard、调用帧、source、PE 检查通过。原 x86 ret12 返回 stub 只接宿主真实 API 结果，不做 Python 复制假返回；桥是 host64 ABI，不能称原 x86 kernel、完整 OS，异常或重叠等未证行为不可宣称。25 个 host 边界用例、6 个拒绝。工具 lucifen_host_ansi_bridge.py 由 editor 执行实现、root 验证；派单拆短及源/目标 buffer 修订由 editor 完成。

候选目录 子代理工作区/ISSUE-20261011-02/r-speaker-voice-01/，正式 临时/ISSUE-20261011-02/r-speaker-voice-replay-01/；大 results 忽略，本目录只留摘要、fixtures、消费者指令、recipe 与 root 证据；审查与正式回放以 root 凭据为准。复跑顺序：先 verify-voice-mapping.txt 创建新目录并复制 reference，再 verify-host-fixtures.txt、verify-audio-sample.txt、verify-complete-metadata.txt（后三独立）。PowerShell 在根目录执行 Get-Content -Raw -LiteralPath '<证据>/verify-*.txt' | python -X utf8 -B -；改副本新目录，不改历史。本地成熟 lpk_media 及既有社区 Lucifen-Tools 只 import；ffmpeg/ffprobe 已安装、只读调用，原件不 OS 启动。

缺口仍包括系统 x86 内核、全音频解码/原 native 播放/时序、原 heap 分配、完整字节流/其它 handler、四版本忠实 TJS 与全部帧音频。宿主 primary 前置仍失败，四版完整目标不变。

增量证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_姓名标签与语音关联证据_20261012。root正式回放五JSON一致；空ID不等于静音，完整画音验收未完成。


## R 原字节流与独立表达式（2026-10-12）

原字节流事实：42F880字节调度→42FB00字符读取；lead闭区间81..9F/E0..FC时盲消费两字节，trail可0/5B且不验证；边界0终止、5B marker，不能文本解码后查指令。434 native单元fixtures通过。59,367结构island全部首literal run与reference相等：3,904,210 bytes / 1,952,105 units；stop marker 990、nul 418、limit 57959。剩余恰为990独立[s格式expr 214100 bytes + 418终止0；原island 4118728全部字节机械对账，语义全明、各路可达、画音还原不等同已证明。

独立expr头为n u32LE、compiledflag 1 byte、table_size u32LE；表5组count u32LE，每条offset、index各u32LE；不同于参数内短计数expr。990 code 116418 bytes、8374 relocs，全表尾和slot范围精确校验，源只读。

原VM初探990×6=5940：受控空查询向量与零channel manager下5274返回、666在native0入口显式停止；不能fake返回或称通过、无独立VM对比。58的case10实际查地址列表，676实际通道清理路径，零count只证无效索引返回；0待系统字符串import和外部控制。当前新增结构/文字核验，不证明全VM或画面音频。

候选子代理工作区/ISSUE-20261011-02/r-literal-run-01；formal临时/ISSUE-20261011-02/r-literal-run-replay-01/；正式回放状态以root receipt为准。工具为lucifen_literal_run_reference.py与lucifen_inline_expression_reference.py。新输出目录复跑，历史不覆盖。

保留完整OT/OTA/OTV/OTR忠实剧本与帧目标，未知不得noop。root仅分析与运行核验，技术工具由editor-easy提供。后续需补独立VM对比、系统字符串import、外部控制与最终画面音频验证，再交批次审查。

增量证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原字节流与独立表达式证据_20261012；root正式回放十JSON一致。冷/热绑定范围与VM未完成边界见阶段凭据；既有未知不按noop处理。


## R VM暂停恢复与原控制请求（2026-10-12）

本阶段新增 lucifen_host_string_bridge.py 与 lucifen_inline_vm_reference.py（最新 candidate03），用于核验 native0 字符串桥与内联 VM reference。native0 位于 41B3A0，先写 global 5355C0=2，取 frame 首 word 字符串，经真实 IAT 5181DC（KERNEL32.lstrcpyA）写入 global 5354BC，随后返回 native0；原 PE import descriptor 已核验。初探 666 输入全部来自原代码、最长 9 字节、9 个不同控制 ID，对应 9 个 SOB 文件均存在；文件名关联不等同原控制器或 loader 已执行，因此不对未提供的原标签名与作用作任何推断。

字符串桥以 host64 WinDLL API 实现，guest x86 proxy 仅以 ret8 接收实际结果；capacity 260 为受控核验范围，原 kernel 故障与重叠情形不构成证明，未知输入一律拒绝。当前 18 宿主、guest 拒绝 6、host 拒绝 4，控制 VM 41 fixtures 通过。返回、终止与非重叠契约以微软 lstrcpyA 文档为依据，本工具只验证桥本身，不代表目标引擎实现。

内联 reference 侧，990 独立表达式×6 受控状态共 5940 首次执行；empty、full ascending、full reversed、duplicate、even-subset 的地址列表分支 10 与零 channel 数量分支 676 均实际执行并比对。独立 reference 与原 VM 在 trace、native frame、整个 1MiB live、原 source 自改及 PE 控制字段上逐字节一致。首次运行 5274 次返回 0、666 次 yield1；原 opcode0 暂停不 pop 栈、PC 保留，绝不可当作结束或 noop。

672 恢复段中，666 结束 0、6 再次 yield1，最终全部结束且栈回 baseline；共 672 次真实系统复制，保持 PC/SP 后再进入原 4A7A50。该过程不执行外部 scene/input 控制器；人工保留原状态续行只证明 VM 状态语义，不证明演出或 SOB 控制生命周期，也不证明有效 channel 清理。原参数 3349 expr×6=20094 回归通过。

candidate 子代理工作区为 ISSUE-20261011-02/r-inline-vm-complete-01/，链路在 r-inline-vm-chain-01，正式临时目录 r-inline-vm-chain-replay-01，回归为 r-inline-vm-regression-replay-01。正式回放以 root receipt 为准，recipe 使用新输出目录，历史成果不覆盖。

下一步聚焦 ctx7560 虚接口到真实 SOB 控制器/loader（不虚构成功）、有效 voice channel lifecycle、原 heap 与文本演出、四版本忠实 TJS 以及全部路线帧音频。primary 失败时不通过 OS 启动原件；完整 goal 保持，不报 100%。

增量凭据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_VM暂停恢复与控制请求证据_20261012。上一阶段666状态停于native0是历史阶段；本阶段已通过受控首次/恢复VM对照，外部SOB控制器及有效通道生命周期仍待验证。


## R SOB控制与资源装载入口（2026-10-12）

**原native受控链路** 原EXE仅作Unicorn客体，PC/SP取自先前已证yield记录；受控执行原native 0→430280（第二arg=1跳过再次VM）→41BD90→4A7000→资源构造/打开/空关闭→虚provider调用前，666初次请求、9不同ID，全source 418 hash不变。

**host64格式API核验** host64下真实lstrcpyA 666与wsprintfA 684；18例provider指针为空（9名字×显式/queued），原loader返回1且SEH头恢复，无fake unknown返回。

**第二链路与原provider路径** 第二链路原provider vtable 51A3A0+8=492450，原path 493F40至494029调用lstrlenA前显式停止，666例、lstrcpyA 1332与wsprintfA 684；baseprefix为合成fixture、provider对象受控预分配，仅实际vtable路径，未证真实初始化/读取成功。

**静态构造与bridge限制** 静态原4821B0 ctor把5357CC设self+168并写provider vtable 51A3A0（48223E），不称实际构造。bridge helper lucifen_host_format_bridge.py由editor实现，经两%s/nooverlap/容量/actual API guards验证；x86proxy仅C3 cdecl，由原caller弹16字节；当前host64非原x86 kernel。

**未完成与候选** 原source字符串不发提供者，任何未知不能noop；未完成：lstrlenA/lstrcatA→CreateFileA只读原码请求→LPK fallback→真实heap/loader发布与SOB执行→场景帧音、四版忠实TJS。已有历史VM/sourceIR不覆盖；候选r-sob-control-loader-01，formal r-sob-control-loader-replay-01与r-sob-real-provider-replay-02；四版本goal保持active。

root正式六JSON完全一致；16宿主/1guest API成功与17拒绝。阶段证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_SOB控制与资源装载入口证据_20261012。两recipe依赖本机原EXE与418 TOB、仓库内numeric request manifest，无需旧忽略目录中的探针results。未知不可noop，完整四版本goal持续。


## R资源读取回退与全归档索引（2026-10-12）

本阶段范围：helper `lucifen_host_path_bridge.py` 提供实际 host64 `lstrlenA`、`lstrcatA`、仅自然缺路径的只读 `CreateFileA`、ASCII `CharLowerA`；原 x86proxy 的 ret4/ret8/ret28 为真实弹栈。所有实际 API 均无 fake 成功，因此不能称为原 x86 kernel。未完成项集中在 LPK 读取链路与后续 loader。

路径666请求已自证 first-yield PC/SP 字段重调用 native0，并进入原 430280 skip-VM 入口；原 provider 492450/493F40 到达归档 lookup。实际 lstrlen666/lstrcat666/CreateFile666 返回自然错误3，CharLower666 亦为自然结果；复制1998、format684 含18缺 provider 自然失败。

下一链路采用受控预分配 archive list 加原 490B70 ctor 的 LPKreader；flag/table metadata 人工受控，表来自成熟 community 工具的原 SCRIPT 索引解密。原 492370 按 prefix 裁相对名，vtable 51A92C+18=491360，原 4F9A20 匹配 entry，666 到原 491430 读取前。该批 lower1332、复制2664，其余同上。

R原 SET_UP 八 LPK 全部 24607 entry，与社区工具 traverse 及真实 record 位置对照：mode0=4189、mode1=20418、24 真实 missing 查找均 FFFFFFFF；使用原 4F9A20，不称原解密/实际读取/解压，源 index 与 PE 不改。LPKheader 原 490850 比较 LPK1，factory static 5188D8+4 指向 490850，constructor 490B70 写 51A92C；静态和预分配 ctor 不能称完整工厂。

source418TOB 及历史 IR 不改，原游戏不 OS 运行、不载原 DLL，不外发源内容。正式依据 root 回执，不报全演出/四版本100%，goal 完整 active。后续：原 index 解密→491430/492D60 实际 LPK 读/allocator/解压→原 SOB loader 发布执行→画音及四版忠实 TJS。候选 r-resource-open-path-01，临时 r-resource-open-path-native-02、r-resource-open-path-lpk-entry-01、r-archive-native-trie-01。


root正式九完整JSON相同；helper最新02。实际字段/表由受控输入和已有成熟工具提供，不等同原loader全成功。证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_资源读取回退与全归档索引证据_20261012。原字节保全、术语及所有旧IR不改，完整四版本目标active。


## R原生只读IO与全量脚本解码（2026-10-12）

## 原生只读 IO 桥

editor 实现两个标准库 helper：`lucifen_readonly_io_bridge.py`、`lucifen_readonly_io_guest.py`。host 侧 `CreateFileW` 固定 `GENERIC_READ/SHARE_READ/OPEN_EXISTING/flags80`，仅显式白名单原文件；真实 host64 HANDLE 映射为 u32 token，自 `60000000` 起，不截断、不复用。`ReadFile`、`SetFilePointer`（NULL high）、`CloseHandle` 同步返回真实结果，含 128A5 guard，单次读上限 1 MiB。guest 仅接受严格同步合法映射，不支持或未知路径一律 raise，不伪造 API 成败。

## 原版执行与解码

原 EXE 不在 OS 运行、不加载原 DLL。Unicorn 运行原 490850 读取 8 个归档 header 并经 LPK1 分支，止于 490923。预分配对象由原 490B70 ctor 写入 51A92C；index/metadata 由成熟工具受控解密。原 4912A0 对全部 24607 原条目生成 entryflag/stored/decodedsize/offset 并真实 `SetFilePointer`；全部条目在完整读前仅先真实 `ReadFile` 至多 64 bytes，与原 archive slice 精确一致；这不等同于全部 24607 条完整读取。

SCRIPT 446 条目另行完整读存储 payload。第一批真实计数：guest `ReadFile` 25061 次、`SetFilePointer` 24607 次，8 档条目数 125/1237/4/717/446/584/1076/20418。第二批 SCRIPT 全 446 = 418 TOB / 23 SOB / 5 other，真实读取 stored payload 总计 4587734 bytes（总存储数据 4587734 bytes，包含 2 项共 126 bytes 未参与解压的 decoded_len 0 条目）；444 压缩项经原 4B0C80 以 allocationflag 0 进入受控预分配目标，2 项 decoded_len 0 按原 4912A0 归一 storedsize、无需解压。内容还原块对应原 49159B..491643，使用准确 archive 参数及受控寄存器/frame。结果总 10515356 bytes，与既有工作区 `lucifen_lzss`/`lpk_patch` 独立参考、所有 446 源文件逐字节一致；原 PE 不改。

## 缺陷与新发现

社区 `lpk_extractor.py` 的 generic LZSS 使用距离式，而原生使用 4096 环形窗绝对偏移，其 best-effort 短输出不能作为本 SCRIPT 语义参考。当前只复用其索引，不改动或复制 GPL 工具。既有 `lpk_patch.read_entry` 实际以 archive key 为准，不应沿用其陈旧“条目 key”注释。原码为最终依据，本稿不写实际 key 值。

## Fixture 与边界

IO fixture 覆盖 10 个真实案例与 16 项严格拒绝：0 count、EOF 尾部不改、真实负 seek error 131、合法 low FFFFFFFF 且 error 0、token 非复用、全部真实关闭；仅 AGENTS 已有文件只读，未生成稀疏或大文件。

复验 recipes：`verify-readonly.txt`、`verify-SCRIPT-decode.txt`、`verify-fixtures.txt`，依赖本机原 EXE、8 个 LPK、446 既有源与既有 workspace 工具。

## 未完成

原完整 LPK factory/index 解密/heap、491430 完整 caller 成功、resource 发布、SOB 执行、全画音、四版忠实 TJS 均未完成。预分配 decoder 与孤立还原块不能称为原完整读取链路或原 x86 kernel。后续路径：原 allocator → 整合 491430 → SOB 发布执行 → 画音/四版对照，完整 goalactive 不缩小。

root正式复验与审查凭据：编程组/演出链路/R_原生只读IO与脚本解码证据_20261012。初次/formal01六JSON完全一致；formal02全部逐项results不变，仅摘要字段由compressed澄清为stored并记未压缩126bytes。完整目标仍未完成。


## R版原生分配器与归档工厂（EDITOR-EASY 2026-10-12）
- 工具新增：lucifen_host_memory.py、lucifen_guest_memory_bridge.py、lucifen_host_version.py。
- HostMemory 只桥真实 host64 Heap/Global API，仅登记成功分配与 owner；close_all 真 free 再 destroy。
- GuestMemoryBlocks 是独立 guest u32 页镜像，前后 128B A5；sync 做真 memmove 与读回；非共享地址、非逐指令同步。
- 版本/字符串：真 GetVersionExA（现宿主 10.0.22621 平台2）与真 CharUpperA；不代表原作 manifest/Win7/SBH，不支持通用 CP932。
- 原 CRT：50A11A 真 HeapCreate+GetVersionExA 选 568408 mode1；malloc/free 达真 HeapAlloc/HeapFree；仅验证 mode1。
- 完整读取器：491430→491E20 GlobalAlloc；压缩走 4B0C80 LZSS；446 SCRIPT 全 exact，10,515,356 bytes；社区 LZSS 非参考。
- 工厂：490850/490B70 建 8 归档对象与全索引，24607 条，index 1058799 bytes；本阶段全 payload 只 SCRIPT446。
- 析构：490BA0/490BC0 真 HeapFree/CloseHandle；私有堆 HeapDestroy 属宿主清理。
- 复验：从 E:/ZCode Workspace/Galgame 运行四份 verify-*.txt；新建 formal-01，已存在则换后缀，不覆盖。正式证据登记目录：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生分配器与归档工厂证据_20261012/。
- 未验证：自主 CreateFileA、原 key、cache1、OOM/OS 失败、SBH、SOB 装载/调度/演出/像素/音频、四版本等价。
- 继续进入 4A7000/4A6D90 SOB loader 与控制发布；不新增 user 审批。
- 行政边界：原始只读；editor 不操作 Git、不假报测试、不回退他人。root 审查后完成 issue 提交、main 合并与记录。


## 20261012 R_完整SOB发布与释放证据_20261012

编辑器侧实现与技术证据：控制器ctor/dtor 809真实原生向量、803唯一处理器；具名向量3：+DC/+10C/+110；全部3个USER_VAR数据集768记录/3724字节/3数组/2局部重定位；22模块42690重定位/607129字节已释放。通用ASCII只读桥用CreateFileA/GetFileSize NULL高，复用基只读API；GlobalFree亦调原生RA4F8687，勿限旧491E62。Host64/guest镜像独立，CPU为原始x86非原OS启动，宿主10.0.22621 CPython清单，Win7未测。

证据边界：请求SCRIPT/SOB_INIT.DAT缺失时原C++ RaiseException E06D7363仅捕获STOP，未派发异常，非成功/noop，boot未证明；合成元数据仅有效输入路径，非空模块元数据与原始缺失异常未验证。provider/list/prefix/cache0/localaux/preopened受控。不缩目标。

# R技能追加 20261012（主合并待评审）

前序完整SOB阶段已建立参照与夹具体系；本阶段新增原生异常恢复与CRT线程证据，属于扩展而非替代。关键变化：在本窄加载证明中，去掉合成元数据依赖，改由受控guest异常记录/上下文驱动原始C++处理链，并以真实Windows内存合法性API在独立宿主替身上验证（各1次）。因此旧fixture证据仍有效，未被否定；新证据只限定在当前 narrow load proof 内。

证据链：original 4A67E0路径经Unicorn只读执行，缺失SCRIPT/SOB_INIT.DAT触发真实CreateFileA错误2/3→original RaiseException E06D7363（flags=1，3参19930520/throwobject/ThrowInfo 522F38）。root构造EXCEPTION_RECORD 80/CONTEXT 716，于低原栈02007000调用original handler 515C60（FuncInfo 523170）。original RtlUnwind thunk 5120A8→IAT 5181F4→wrapper 5053E1→continuation 505409；target==FS0，目标即当前链首；目标以上没有待展开帧（目标帧自身不在该RtlUnwind调用中展开），仅窄guest OS边界由strict planner模拟（flags OR2、ESP+20、EAX、IP转移）。original 505409清bit2/恢复FS，507994局部unwind→507AAD catch→typed catch 49275D→native continuation 492776。非真实宿主RtlUnwind/非完整SEH。

HostTLS：实际TLS index供original 52D970；507EF3_getptd实际calloc 50BEBE HeapAlloc flags8、0x74取整128；TLS set/GetCurrentThreadId/PTD init执行；+6C/+70 catch后恢复0。507F5A_freeptd释放实际PTD并TlsSetValue0；真实TlsFree由宿主清理，非original CRT teardown。original _mtinit 507E8C/critical sections未执行。

计数：157 HeapAlloc/157 HeapFree、23 GlobalAlloc/23 GlobalFree、25 ReadFile、24 CreateFileA、23 SetFilePointer、1 CloseHandle；native指针探针各1，Rtl guest模拟1，GetLastError 6/TlsGetValue 7/TlsSetValue 2/GetCurrentThreadId 1/SetLastError 6。Fixtures 36指针、28 TLS、1 unwind接受/53拒绝；64ptr >FFFFFFFF保留；错误线程变更前拒绝；HostTLS 包装器不释放调用者所有的内存；PTD 由原版 _freeptd 释放。无泄漏自有块/句柄/TLS。

工具与证据：lucifen_host_read_probe.py、lucifen_host_write_probe.py、lucifen_host_tls.py、lucifen_guest_unwind.py；sob-recovery-summary.json、original-Cxx-handler-probe-summary.json、missing-initialization-exception-summary.json、boot-API-results.json、fixtures.json、root-source-integrity.json、root-batch-review.json、verify-recovery.txt、verify-fixtures.txt。

边界：仍受控provider/list/prefix/cache0/预打开归档/allocator Win mode1/PTD index输入/records/context/零帧OS模拟。非原始OS引导/完整CRT/父应用/native body/完整script/render/audio/OTOTAOTVOTR 100%。原始EXE/8LPK/446SCRIPT/418IR哈希由root校验，root评审待最终。下一步：original VM指令调度/控制续延→original native bodies/resource/task/render/audio比较。不声称完成。

证据目录与模块位置：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生异常恢复与CRT线程证据_20261012/
模块路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/


【2026-10-12 追加检查点】证据目录：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_父应用构造与原生窗口入口证据_20261012。复核从 workspace 根执行 python -X utf8 -B 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_父应用构造与原生窗口入口证据_20261012/verify-parent-scheduler.txt；工具在 编程组/工具，原资料只读，Win32 子进程 temp 限 workspace 内。只追加，不改历史文本。检查点：父对象 40A0A0 size0x1C18 -> parent 0x02003000、vtable 51874C、HWND+150=0；WinMain 40A040/452CF0 未执行；FPCW 023F PC10=53bit；EnumDisplayMonitors 快照+原回调 4ECFB0；26 dispatch；dtor 后 530C94 悬空勿用。后续路径：原 WinMain 窗口生命周期，再任务/资源/画音消费者，再四版本忠实 TJS 与全路线对照。root 复核待完成。

## 追加：原版音频DLL与WinMain预初始化证据（R）
正式证据相对路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原版音频DLL装载与WinMain预初始化证据_20261012/。要点：原wuvorbis.dll仅只读映射加受控Unicorn执行，禁止OS装载/执行原EXE/DLL；WinMain 452CF0的LoadLibraryA由guest adapter返回原基址，15接口GetProcAddress成功，query机器码704不超过960。精确停止在SHGetSpecialFolderPathA调用返回地址VA 4711332（47E3A4），HWND=0、CSIDL=26、fCreate=1，WinMain未返回、原shutdown未执行。SCRIPT.LPK header 8、index 17151已读，ll_app.sys 25字节与ll_app.inf 101字节与既有只读源逐字节相同。保留全scope OT/OTA/OTV/OTR与忠实TJS/画音100%未完成，接口与文件覆盖不等于还原率；完整OS级异常过滤器与原环境仍待解决，有限纯guest注册状态已验证。

### R_保存路径映射与目录选择入口（20261012）
- 证据：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_保存路径映射与目录选择入口证据_20261012/`
- 工具：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/lucifen_host_shell_folder_binding.py`、`lucifen_guest_storage_exact.py`、`lucifen_host_storage_bindings.py`、`lucifen_host_format_one_binding.py`、`lucifen_host_desktop_window_binding.py`
- 运行：脚本代码从正式 `verify-WinMain.txt` 读取后由 stdin 传给 Python，fresh 临时相对目录经 argv 传入（不是把目录作为 stdin）；runtime 产物落 `临时/ISSUE-20261011-02/fresh`，root 阶段归档到正式证据目录；fresh 目录不得预先存在。
- 已验：原 WinMain 452CF0 受控；SHGetSpecialFolderPathA RA47E3A4，HWND=0，CSIDL26/5，guest fCreate=1、host fCreate=0，目录只读 BOOL=1/buf260 守卫通过。
- 已验：仅 AppData 根/SaveData/USER.CFG 三请求；host 目标新 stage/guest-storage/AppData；未知、大小写变体、NUL、非 bytes、工区外、junction 拒绝。
- 已验：CreateDirectoryA RA40B36E→CreateDirectoryW 1；CopyFileA RA40B3DD→CopyFileW 1；SetFileAttributesA RA40B3EF→W 1；源 SET_UP/USER.CFG 111 字节 sha256 ef33b1866f5e83a99b70dee58d386898d11eabed0391d254d99879073b40090d，副本逐字节同、源未变。
- 已验：ReadOnlyFiles CreateFileW；storage 独立 host 句柄+guest token 69600000；GetFileSize RA4924EC=111，ReadFile RA49253D=原 USER.CFG 111 相同（非台词覆盖/保存完成）。
- 已验：wsprintfA 一 %s：37+18→53 字节，cdecl3、64 位指针、buf+32 守卫、ANSI literal 保留；GetDesktopWindow host HWND+IsWindow=1，借用 guest 69800000，未关闭 desktop。
- 停止：SHGetMalloc 未绑定 EIP127E2A/RA47E291；未取 IMalloc、未进 SHBrowseForFolderA、未注入选目录/取消；parent+150 HWND=0，原 WinMain 未返回。
- 清理：fixture passed（heap/blocks/TLS/CS/file/events/COM0，storage files 关）；非 originalWinMain/DLL shutdown，borrowed desktop 未关。
- 测例：8 passed——6 CreateDir/Copy/Attrs（183/80/2）、GetFileSize 守卫高 DWORD 0 且不改变文件位置、无效 handle FFFFFFFF/error6；7 pathmapper passed；formatter/desktop 原生链路有意义验证。
- 限制：symlink 现场缺 WinError1314，仅 junction 拒绝验证；ACP936、非日文 OS/全 manifest；Win7/10 未验；Win11 受控。
- 限制：不是 OS sandbox，串行 TOCTOU；不泛化解析；未 OS 执行 guest 指针/越界写；未知 stop，不 fake。
- 后继：真实 Shell IMalloc/Folder PIDL、guest callback、nativewindow/plugin/PCM；全 scope OT/OTA/OTV/OTR 100% 还原未完成。

## R 原作参照：原生目录回调与配置写入证据（20261013）

追加方式：原样追加到两个已有作品 skill 末尾；只追加，不重写历史。

- 这是 R 原作参照证据，不是四版通过；不得写成四版通过。
- 正式阶段目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013`
- 正确 IMalloc 槽位：`DidAlloc` slot 7，`Free` slot 5，`Release` slot 2。root 初始候选 slot 8 错误，已拒绝；误调可能执行自身进程 `HeapMinimize`。
- 关键边界：WinMain `0x452cf0`；BROWSEINFO_callback `0x47e250`；original_SHGetMalloc_return `0x47e291`；original_GetPath_return `0x47e362`；original_IMalloc_Free_return `0x47e372`；original_Release_return `0x47e37c`。
- 回调事实：original_callback_cases 5；only_message_1_SendMessageA 1126；wParam 1；native_callback_return_all 0；host_receiver_result_is_fixture 79225；parent_HWND 0；WinMain_not_returned true。
- 写入/配置事实：native_second_CreateDirectory_return `0x40b79a`；actual_native_write_calls 10；original_CreateFile_write_return `0x47ea5f`；original_WriteFile_return `0x47eb87`；original_Close_return `0x47e46f`；USER_CFG 前三字段长度不变 `[72, 14, 17]`；第四字段为 original selected SaveData path plus NUL，变长 u16 length-prefixed；APP_CFG 196 字节，前缀 u32 192，body 192；缺失配置处理程序 `0x515c60`、`0x515c56`；original_files_modified 0。
- EXCEPTION_RECORD 80；CONTEXT 716；RtlUnwind guest OS current head only count 2。
- 驱动边界：native_get_drive_boundary `0x127614`；original_GetDriveType_return `0x48299c`；未知 `GetDriveTypeA` 处停止。停止不等于窗口/游戏/PCM/完整关机/Win7-10 证明。
- 正式 Shell/IO cases 7。
- 源对比：新源 34 文件全部等于已有备份；source_total_bytes 2768305083；no_additional_files_vs_backup true；Source cfg 111、SCRIPT446、IR418 不变。详细 `source_root` 引用 `new-source-media-comparison.json`。
- 运行：从 workspace 根，fresh 每次不同且不存在：
  - `python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013/verify-WinMain.txt" "临时/ISSUE-20261011-02/fresh-WinMain-02"`
  - `python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013/verify-Shell-and-IO.txt" "临时/ISSUE-20261011-02/fresh-Shell-IO-02"`
  - `python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013/verify-source-integrity.txt" "临时/ISSUE-20261011-02/fresh-source-02"`
- 源对比命令：`python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/lucifen_readonly_source_compare.py" --source "D:/360安全浏览器下载/[110624][Navel] 俺たちに翼はない R -Limited Edition- (nrg)/ORETUBAR" --reference "备份/我们没有翅膀R-安装介质" --output "临时/ISSUE-20261011-02/fresh-media-02/manifest.json"`
- 边界：original EXE/DLL 仍仅为 Unicorn readonly x86；系统 raw API 真实；selected PIDLIST 为 own workspace 显式 replay，无实际 `SHBrowseForFolder` 对话框；host 为 invisible message-only fixture receiver，guest WNDPROC/callback 未由 OS 注册；CP936 非 original JP OS；`GetSpecialFolder` host `fCreate0` 对只读已存在目录查询忽略 original guest1。拒绝 native probe10 stale postchecker 两 folder calls 预期；正式修复证明 `[26, 5, 26]`。
- 停点：完整 OT/OTA/OTV/OTR 与忠实 TJS 100% 未完成；待 root 最终复核以最终审查状态 record，不追加假完成。


## 2026-10-13 编程组/演出链路：R_DirectDraw与双架构设备枚举证据
依据 工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_DirectDraw与双架构设备枚举证据_20261013/README.md（R 与 customskills 中均可解析）。要点：严格区分32/64位；32位 GetCaps 已到 DDCAPS 复制；实际 IID_IDirect3D7 QueryInterface 已成功，随后调用实际 GetCaps 槽位11，之后在调用实际 IDirect3D7 槽位3 EnumDevices 之前停止；未调用未知回调 ABI。窗口/协作层级/表面/渲染/资产/VM/音频仍待做；全局四版本目标未完成。本段用于 R skill 与 custom engine skill 引用，不添加虚构测试命令。


## 2026-10-13 原生设备回调与离屏位图证据

完整仓库相对路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生设备回调与离屏位图证据_20261013/README.md

6 次原始 guest 设备回调，2 次 D3D7 EnumDevices 调用，每个驱动/调用 3 个回调，所有原始 return1、host HRESULT0；两个原生链表长度 1、2、3；设备1 RGB GUID605c66a47326cf11a31a00aa00b93356、dwDevCaps1361、flag0；设备2 GUID e03de684aa46cf11816f0000c020156e、dwDevCaps102416113、flag1；设备3 GUID789e04f56148d211a40700a0c90629a8、dwDevCaps102481649、flag1。EnumDisplaySettingsExA 392 次调用，390 次成功、2 次枚举结束零；CreateDIBSection 800x600 topdown 32bit DIB，精确 SelectObject/恢复/DeleteObject。stop：LoadIconA HWND0（parentHWND0）未决。无帧证明，完整 OT/OTA/OTV/OTR 100% 仍不完整，不添加未验证命令/测试，不伪完成；无实际渲染证明，不声称 host 差异原因或物理硬件渲染成功。


## 技能追加 2026-10-13
路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生资源图标与窗口类证据_20261013/README.md
仅原代码 Unicorn、原 PE 不 OS 加载；original icon+classregistration/cleanup verified, originalWNDPROC/windowcreation notexecuted, fourversion100%incomplete。下一步 relay 原窗口回调，勿假 HWND。仅派生元数据，root 应用候选，workspace-only/noGit、未独做、未调暂停角色、非翻译缓存未变。


## 2026-10-13 原版窗口创建与消息链路增量

R窗口创建阶段技术增量索引。先读工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原版窗口创建与消息链路证据_20261013/README.md与同目录两JSON，核对49F840/49F860、69F50000、parent+14C、消息24/81/83/1返回0/1/0/0。下一步RT_ACCELERATOR102映射与VM/渲染/语音，不造NULL加速键，不称100%。


## 2026-10-14 加速键资源与原版初始化续延增量

索引登记完整路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_加速键资源与原版初始化续延证据_20261013/README.md

依据《演出链路/R_加速键资源与原版初始化续延证据_20261013/README.md》,加速键资源7条已32/64位真实验证,原WinMain续延至imm32查询前停止;资源替身与原件非完全等价,画音100%还原仍待验。产物仅workspace暂存由root应用,不Git、不回退他人改动、不调暂停角色。

## 2026-10-14 IME输入与VM窗口消费者增量

- 路径：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_IME输入与VM窗口消费者证据_20261014/README.md`
- 范围：R_IME 输入链路与 VM 窗口消费者证据，仅证据与停点登记；产物仅供 root 应用。
- 已验证（真实、非推测）：IME disable；17 手柄查询；两者均已通过 fixture 清理，链路停点位于 `ShowWindow` 之前。
- 消费者映射：`GameInit` 原 native 796 失败提示参数已映射到实际 9001 注册消费者。
- WndProc 证据：原 `WndProc` 为明确直接重放，未调用 OS `SendMessage`；链路停点位于嵌套 9000，未继续向下重放。
- 待办（未验证/未完成）：正常 VM；绘制；语音；四版 100%。
- 使用方式：可追加至 R 与自建两 skill 的索引入口，术语沿用本段，不做改写。
- 约束：不 Git、不回退他人改动、不调用暂停角色；所有写入仅限 `E:/ZCode Workspace/Galgame` 内，由 root 应用。


# R_原版窗口显示与DLL初始化衔接_20261014

证据入口：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原版窗口显示与DLL初始化衔接_20261014/README.md

关联 issue：ISSUE-20261011-02-original-fidelity
性质：纯技术、非翻译；仅涉及自有 SDK 源码与自有验证元数据。本段为阶段记录，集中复核由 root 阶段执行。

## 一、窗口显示衔接

- 原 ShowWindow 触发的原 WndProc（49F860）回调通过。
- 夹具触发计数：55 夹具 23 次、63 夹具 18 次、65 夹具 19 次。
- 系统消息序列可变；SetForeground 实际取值 0 与 1 的路径均保留，不做折叠或归一化。

## 二、宿主与客体消息组件

- 32 位与 64 位 WINDOWPOS / NCC 组件验证通过；宿主 MSG 组件验证通过。
- 原 NCC wParam1 分支未触发；客体 MSG 布局未证。

## 三、DLL 初始化与入口接续

- 原 tvpgl 入口、GetLibrary 包装器与 setter 写入真实 5357E4；原 selector 21 = 1。
- 随后原 DS_SPRITE 与 DS_MOVIE 入口均在客体 CPU 自行返回 1。
- 原源导出解析与原有消费者接续至 GetCursorPos。

## 四、边界与限制

- 有限客体 loader / 线程通知模型不等于完整 OS loader；原 DLL 未走 OS 加载路径。
- 以上“通过”“未触发”“未证”均为本阶段观测口径，最终判定以 root 集中复核为准。

## 五、未完成项与哈希基线

- 正常 GameInit、VM 画音、忠实 TJS、四版本 100% 均未完成。
- 原资料 446 脚本 / 418 IR 哈希未变，基线保持。


## 2026-10-14 原工作线程启动与业务同步（ISSUE-20261011-02）

- 阶段目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原版工作线程启动与同步证据_20261014`；正式候选模块 14 个：前 11 线程/TLS/CS/Event/request/frame helper，加 `lucifen_host_logfont_a.py`、`lucifen_host_font_create.py`、`lucifen_host_gdi_object_query.py`。
- 宿主取证：`sdk-thread-32/64.json`、`sdk-events-32/64.json`、`sdk-font-32/64.json` 六份 root 独立 OS 验证全部通过；真实 `WindowsCreateThread` 只喂自有 guard，不把 guest 地址交 OS。
- canonical74 为源 CRT 原线程 prefix；canonical76 重现空目标：ECX/ESI=531188、EDX/vtable=0、原对象前 16 DWORD 全 0，`next_import` 正确为 null（canonical75 误报 `#17` 未采用为真实 import）。
- 源静态初始化表 slot `52804C=40E180`，`40E180` 调 `40E190`，后者对 global `531188` 调原 ctor `402DF0` 并做原 atexit 注册；canonical77 执行原 initializer 与原 atexit 登记成功，原对象首 DWORD=`5199F0`(5347824)，虚表 8 项为真实源函数且有效。
- 未手填对象/虚表，未声称完整 CRT 启动已执行。
- canonical77 原 business 越过 `402F1D`，停在原 `CreateFontIndirectA` `RA45C697`，LOGFONT ptr `531194`；canonical78 经 14 SDK 实际调用 `CreateFontIndirectA`，复制原 60 字节 LF，guard 保留。
- 原 height=-14、weight=400、charSet=128、quality=3，其余关键标志 0；输入 SHA `6d2c34e67c1217593b92747b4186d8120ca243ce79b769bdb60f984656825037`；真实 `GetObjectA` 返回 60 且 SHA 同原输入。
- OS 真实非空 font/fullwidth，无 guest 指针给 OS；源非空分支执行到 `45C6CB` 停；原 font 后续储存/选择/实际 glyph/pixel 尚未验证；自有 font `DeleteObject` 成功。
- native 原创建 `RA506ED6`/wrapper `506EFA`/`TlsSetValue RA506F30`/`GetCurrentThreadId RA506F42` 匹配真实 hostworker，参数 `+48/+4C` 业务 `4F8D50`；同实际 worker 的 WUV source `DLL_THREAD_ATTACH` reason 2 原返回 1；其余 3 模块有限通知禁用模型沿用。
- CRT `43` 静态/业务 `87` 指令 CFG 无 diagnostics；canonical75/76 源 business 66 条 API 与 2 处 `SetEvent`（`RA50526D`/`4F8D97`）已证为原实际自有 event。
- native 源 `CreateThread` 消费者尚未消费 HANDLE/TID；Root hostguard 有限结束码 `A1100000` 非 sourceThreadExit；parentcontext/FS0 已 restored，worker 授权/资源清理通过。
- 同一时刻只有一个 Unicorn 运行，FS0 为有限模型非完整 TEB/OS loader；SharedCS/TLS 为已授权线程+串行 guestCPU 契约，不标无条件通用并发模型；阻塞 CS 必须在 VM 锁外，SDK fixture 已证。
- SharedEvents 状态 RLock 在 Wait 之前释放，waiter 保护 close，未经授权 wait 拒绝。
- 完整 goal 100% OT/OTA/OTV/OTR 保留；正常 GameInit/原素材 VM 帧、画音、忠实可执行目标剧本、full scheduler/原 Exit/原 DLL detach/全量对照仍未完成。
- 源完整性本批真实复验通过：EXE1/LPK8/原 DLL3+既有参照 DLL2/446 脚本/418IR/原 USER.CFG 111 字节哈希一致；通过不等于完整 100%。
- 资料取证仅本地 guestCPU+system DLL，原 DLL 绝不 OS LoadLibrary；峰值实际 13 独立 API；未设固定人数，不用截断回合计完成。
- 目录内产物：`sdk-thread-32/64.json`、`sdk-events-32/64.json`、`sdk-font-32/64.json`、`canonical74/76/78/original-thread-prefix.json`、`canonical78/original-static-531188-initializer.json`、`host-fixture-cleanup.json`（每 canonical 独立子目录）、`original-thread-entry-CFG.json`、`original-business-thread-CFG.json`、`global-531188-constructor-CFG.json`、`global-531188-literal-xrefs.json`、`source-integrity.json`、`editor-helper-provenance.json`。
- 正式 root 平台装配把 verification recipe 候选 import 路径改为 `编程组/工具`，仅 recipe 路径搬运，不技术改 helper。
- 下一阶段：从 `45C6CB` 继续字体选择/显示与真实窗口调度，建立源 CreateThread 消费者/工作线程生命周期与业务任务循环；系统性沿 EXE CRT initializer table 收齐静态对象，避免零对象假失败；阶段 root 批审后合并。


## 2026-10-14 字体请求与严格停点

证据路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_完整CRT初始化与字体请求证据_20261014。

三原字体对象531188/533240/5332A4，cp932 face依次ＭＳ ゴシック(-14,400)、ＭＳ Ｐゴシック(-16,700)、ＭＳ ゴシック(-19,400)，charset128 quality3。源45C719真实metrics给第一ascent12，对象531188的+20B0/+20B4=[0,12]；第三height19/ascent16/descent3。

实际ACP936，第一A接口选MS PGothic；受控cp932→W选MS Gothic；iiii宽12对28，32/64一致。W对照不是日文原OS像素基准，不硬编码metrics。

95捕获MSVC E06D7363，EAdlErrorCode值3，ThrowInfo522F38，调用点492758/返回49275D，尚未dispatch。SOB_INIT.DAT可选探测缺失不能证明错误原因。正常GameInit和四版100%仍未完成。

## README 追加
canonical96 在实际 owned worker 执行原 SEH handler 515C60，命中原 EAdlErrorCode3 原 catch 49275D；current-head-only guest RtlUnwind 一次，stack 03700000..03720000。原码随后读取归档 USER_VAR.SOB（3171 压缩 bytes）、FUNC_LIB.SOB（17508 压缩 bytes）。仅证明异常恢复，可选 loose 缺失后有 archive 回退；未证明正常 GameInit 或完整 SOB 发布。2M 指令预算停 4915C3，failure null 亦非退出成功。保留旧 95 未 dispatch 原述，不改写为当前仍未 dispatch。


## README 追加：初始化→恢复→资源→窗口检查

原初始化异常由 catch 恢复，继续四个资源读取（canonical96–99）：canonical97 读 VOICEINF.DAT 归档 932 压缩 bytes；canonical98 确认实际源 `%s%s.SOB` 格式 `RA41BDB9`，旧 version formatter 不支持非原游戏错误；canonical99 复用自有 two-string `wsprintfA` helper，原调用实际返回 15，随后归档读 MAIN.SOB 压缩 3000 bytes。下一 stop import `IsIconic`（hintRVA `12706C`，sourceRA `44DCA8`）；真实已有窗口 guest token `69850000`，尚未调用，不假返回。canonical96/97/98/99 真实 fixture 清理通过、进程退出 0，但不等价原 worker exit/正常 GameInit/画音还原，未称完整绑定正常 VM 或 100%。


## 自有派生事实检查点
本检查点仅记录自有派生元数据，禁止原作与凭据外发。
- 新增三个独立SDK声明：IsIconic、IsWindowEnabled、GetAsyncKeyState；32/64位ABI验证通过，不替代原输入对照。
- canonical100：原IsIconic RA44DCA8在同一真实已显示owned window上查询，实际BOOL为0；global5357E4实际119394432非零，但不能定位为worker写入。
- canonical101：继续GetCursorPos RA44E00D、ClientToScreen RA4A85F1、GetClientRect RA4A85FD，真实guard8/16输出，client[0,0,800,600]；不要宣称画帧。
- 独立同环境调用原native4114D0（selector21）真实返回1，cdecl/CPU/FS0恢复，无global注入；这是独立验证，非GameInit VM调用整链。
- next：sourceOffsetRect，hintRVA127104/sourceRA4A860E，尚未调用。
- 阶段18SDK、原worker完整Exit/parent CreateThread HANDLE消费者、正常VM全画音、忠实TJS、四版100%仍未完成。
所有结论均来自独立验证，不扩范围、不Git、不回退他人。下一步需复核，避免整链误判。

### 2026-10-14 原启动窗口绘制与真实事件等待证据

用途：R作品skill增量；区分原程序执行与仅root OS取证，并标出未完成项。证据归档目录：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原启动绘制与窗口回读证据_20261014；完整运行收据：临时/ISSUE-20261011-02。

**原程序执行（root OS/Unicorn验证，含源EIP）**
- canonical112：real GetDC(owned window)，source 45B4A4；ReleaseDC 同一OS获取线程。
- canonical113：real BitBlt source 45B762；owned window DC + 原guest 800x600 topdown 32bpp DIB，每次调用host-synchronized；79次BOOL1源blits，前75次全扫800x8@y0..592，后4次dirty rect；237个实际GetPixel样本匹配。
- canonical116：对owned event guest 69000002 的 exact actual HostSharedEvents.wait，来自已注册 real OS worker：61次timed waits，actual WAIT_TIMEOUT 258，源timeout 10..14ms变化；源blits 141；被1M指令slice在源EIP停止；无unknown opcode结论。
- canonical117：已实际退出0；63次真实有时限等待，timeout预算766ms；127次源blit；等待后原生指令切片续执行，停在旧formatter不支持新单整数格式的ValueError（适配器边界，不是原作失败），不是未知opcode；结束画面全白，整幅800x600 RGB仍匹配源bitmap，差异0，SHA-256 680a1c22a8e114ea0c637847e8cc506794073a55f4350364c8a0421e7dbcc8f0。
- 115/116/117时间不同，blit次数与图像hash不可直接当作固定回归值。

**仅root OS取证/验证（非完整原程序运行结论）**
- canonical115：同一worker重新获取同一owned window DC做capture；完整800x600 RGB（alpha未用忽略）匹配原guest bitmap，differing color bytes 0，SHA-256 5216df39f5de25f2600743aaf667201c99a9708d1e29a2afc9f46dff4055503b；live objects已清理；图像为启动白背景+小橙色loading icon，不构成完整Logo/BGM播放证明。
- canonical114：验证失败KeyError，因source已ReleaseDC；不声称源游戏报错。
- 未加载原始PE/DLL到OS；无目标引擎/日文OS黄金参考；无全路由/音频/四版本100%。

**边界与真实状态**
- 新14个SDK和两小验证模块为自有实现候选；root32/64 synthetic tests全部通过（字体ABC实际312非白像素、8bpp palette双guard roundtrip、BITMAP24/32bytes）。
- HostLargeMemory/GuestLargeBlocks仅实例级1..64MiB可配（默认32MiB），旧全局1MiB guard不变；32/64实际1920016 alloc/realloc guard清理通过；rect OffsetRect/IntersectRect通过；原帧1920016分配含16字节overhead。

## 2026-10-14 跨运行裁剪反例与阶段准入结论
- canonical120实际退出0、worker_errors空、ownedcleanup通过。
- 源窗口GetClipBox类型1(NULLREGION)、RECT全0；IsIconic0、IsWindowVisible1。
- 所有源GetPixel为CLR_INVALID；113次blit后整幅与源16543颜色字节差异。
- 故窗口未最小化但DC无可画范围：不能判原作缺图，也不计像素还原通过；原因归属还需验证遮挡/消息泵/原父线程，不能宣称因果已定。
- 115/117两次整帧RGB0差异只对应当次运行；118/119/120反例完整保留。
- 当前覆盖17 SDK=16新增+既有IsIconic复用，以及两editor验证helper。
- 32/64自有OS验证通过，含clipbox owned DIB、IsIconic owned message-window、palette独立output+无输出写入负例拒绝；所有声明不是完成目标引擎。
- 先前14候选状态为此前小批次，不混称所有17新建。
- 单整数cdecl已SDK实测，不假称BGM播放已执行。
- 下一步接原父线程HANDLE/TID消费者与消息循环，在有效DC上再取动态整帧与音频，然后忠实TJS及四版本全路线。
- 证据入口：R_原启动绘制与窗口回读证据_20261014。

### 2026-10-14 线程启动握手与父线程消息接续
阶段入口 `R_线程启动握手与消息接续证据_20261014`。root 精确装配，按批审记录推进。

- editor SDK 现 10 个：原 8 个含 guest thread HANDLE 纯登记、guest MSG pack/unpack 32 字节、GetMessageA signed int、TranslateAcceleratorA、SetWindowPos NOACTIVATE、GetForegroundWindow、wvsprintfA typed fixed 3 args；本批 ReadOnlyFilesLarge 实例 max_transfer 默认 32 MiB/上限 64 MiB；bridge_ReadFile_large 单调用 max_read。保留旧全局 1 MiB/readonly 白名单/guard/错误/短读 EOF/offset wrap 及 overlap 验证。
- root32/64 owned OS/ABI 测试通过：native MSG 32/48 bytes，guest MSG 32，host 指针不截断；register dup/invalid 不修改映射；bool/overflow 拒绝；32/64 真实合成 ReadFile 1571162 bytes 守卫/短读 EOF/无效参数预检/旧 cap 不变/cleanup 通过。
- real WM_QUIT 返回 0 guarded；无 accelerator 非键返回 0；wvsprintf host va slot4/8 真实 OS 匹配 guard。SetWindowPos 仅 owned 合成对象测试，未称修复原窗口。
- source 121/122 实际 CreateThread consumer：object+4 HANDLE、+8 TID、+5C ready event；原 4F8D91 SetEvent 在业务虚调用之前，故启动握手不是 GameInit 完成。
- 122 wait_zero 成功会消费 auto-reset 信号，不能作为非侵入 peek，不回写假 SetEvent。
- 123 新重放未探测直接真实原无限等待返回 0，原 CloseHandle ready event 并清零 5C 后进入 GetMessageA。
- 124 真实队列首 0x31F，保守暂停；125 实际 GetMessageA/MSG 显式 HWND 映射、TranslateAcceleratorA 0、进入 TranslateMessage。
- 127 实际 TranslateMessage 0、DispatchMessageA 0、原 WNDPROC 49F860/真实 GetWindowLongA/DefWindowProcA，回到 GetMessageA；唯一真实系统消息 0x31F/wParam1/lParam0，未注入源消息，没有任何原消息广覆盖证明。
- 128 原码实际 4 次 one-string wvsprintfA，host va slot4bytes 重建，所有输入输出 guard/结果通过，推进至 >1MiB ReadFile 旧 cap 边界；131 原码 ReadFile 1571162 字节成功，继续原图像解码，8 个 native 1M slices 预算停，不是未知 API/原作损坏；132 继续解码进行中无结论。
- 129 会话消失且无活原流程/完整 receipt，不计成功或原游戏失败；130 root 取证 late legacy imports 覆盖 new aliases，未越过旧 cap；131 修正全局导入并运行时 assert final bindings，源码 helper 未改。
- 主代理规范源：MS DWM WM_DWMNCRENDERINGCHANGED，完整链接 https://learn.microsoft.com/en-us/windows/win32/dwm/wm-dwmncrenderingchanged。原 PE/DLL 只 Unicorn 非 OS 加载。
- worker 仍有限 guard 结束非原退出，消息分发仅此非绘制消息；并发调度、aliveworker、字体/DC 跨线程生命周期、WM_PAINT/键鼠/动画/音频、四版全路线、忠实 TJS 未完成；旧 NULLREGION 反例未宣称修复。
- root126 取证缩进编译失败未启动原流程，改 127；源 SetRect 旧 8 次取证预算停，改 512 次真实 API 有 guard 并保留有限预算。128 已按上述推进，132 未结论，不先报通过。

## 2026-10-14 原资源解码与阶段终点
- 本批10个SDK/32及64 OS或ABI自测通过。
- 131：原始ReadFile实际1,571,162字节，8片段执行预算停，非缺资源。
- 132：root 30秒观察deadline中止缺完整receipt，不判断原游戏失败；先前“进行中”文本由本补充纠正。
- 133：短10秒观察循环等待有限worker，22个1M原码片段退出0/cleanup通过，停在原tvpgl执行区0x12039486（根取证续跑仅限EXE原因，不是未知API）。
- 134：扩原EXE/4DLL已核验可执行区，26个片段退出0，停Root旧SelectObject将所有worker对象路由为font；原owned bitmap不是font。
- 135：按registered object kind区分实际字体与bitmap，44个片段真实EXE/tvpgl执行、源bitmap选择成功，退出0/worker_errors空/cleanup通过，停SetCursorPos原请求[960,540]，source return 44E009、hint 126D2E。
- 两次类型/导入/observer误判均为root验证器边界；未改原码、未伪造结果。
- 现状：尚未达完整初始化/动画/音频/生存线程/WM_PAINT/键鼠或四版TJS 100%；NULLREGION反例未宣称修复；源资料最终完整性复验前保持待审。
- 下一步：有界接Cursor API，将source parent/worker以实际OS活线程与资源生命周期的串行Unicorn协作模式接通，随后走原素材画音/忠实TJS/全四版全部路线。
- 规范引用保留正确WM_DWMNCRENDERINGCHANGED；不复制巨大trace。

## 2026-10-14 活工作线程交接与标题演出取证

承接 ISSUE-20261011-02-original-fidelity。当前仅 root/easy 活跃：root 负责规划/OS 原作核验/审计/Git/管理，easy 负责全部生产代码与知识。原作代码/资产不外发；仅自有 SDK/派生元数据。

阶段建议：R_活工作线程交接与标题演出证据_20261014。

证据：
- canonical137：实际 worker 在原父线程处理中 STILL_ACTIVE=259；收到真实系统消息 0x31F；5 个实际 HFONT GetObjectA 均 60 有效；上下文与 FS0 在同一实际 OS TID 恢复；无并发 Unicorn，无源关闭。
- canonical138：原父线程后 1M 指令、11 blits，33 样本全匹配，源 DC clip=2；不构成普适裁剪修复。
- canonical139：原父线程后 12M 在预算内执行无异常；部分原始 R 标题菜单 START/LOAD/CONFIG/EXIT 可见；白带/全帧 792977 RGB 字节不匹配，169 blits 中 146 匹配、23 NULLREGION。
- canonical140：原父线程后 24M 有限预算，338 blits：131 clip=2、207 NULLREGION、样本失败。原作 ReleaseDC 前六次实际捕获，全帧均失败；捕获 1、2 在 RECT[0,90,800,540] RGB 精确，但全帧仍差 351009，差异行 0..89 与 540..599；其余并集也失败。该并集由源 strip 调用派生，非为隐藏不匹配而选；仍仅同一 canonical140 有限运行中的两次实际捕获，非普适 100%。

标题演出：原作画 8 像素水平条 y90..538，末 2 像素；源 ret 45B762 / ReleaseDC 45B908。逐调用结果保留 CLR_INVALID/NULLREGION/SetCursorPos BOOL0，无假成功。

SDK：WorkerParkGate 一次性；WorkerStepState/WorkerStepGate 多代；实际 Win32 TID 导入 lucifen_host_tls；两门模块合成实际 OS 32/64 的 synthetic multi32 32 代，alive259、GDI 字体+DC 可用；owner/stale/skip/timeout/duplicate 负例与同 worker 清理。该多代为 synthetic multi32 代，尚未接原完整调度器。整初始 stepgate provider 任务长 10000 无产物；两个较小模块 + 微小实际 TID 导入修正被接受。光标实际签名请求与 BOOL0/1 保留；仅当仍为最后请求位置时恢复光标，保留期间用户移动。root 失败属验证适配器限制，非游戏失败。

边界：无完整原作 Exit/detach/TEB/loader；无全部消息/WM_PAINT/按键/鼠标；无忠实目标 TJS/普通 VM 全音频/全路线证明。源完整性合并前最终待定。Norm cache AGENTS 未变，LF sha ecd14ee3924532a75eb02cf7ad1b02a49cf76329ca4be6ff74c612c4d56af4bf。仅非翻译技术知识。

# 2026-10-14多轮交接增量
- 141：停在 GetTextExtentPoint32A 适配边界；适配器缺失，非游戏故障。0xC125 零参数已注册、留队。
- 142：4 次 2M 交接，实际同 TID29996；5 个活字体、worker259，未多消费消息。
- 143：4 次 8M 交接，同 TID28476；实际零参数 0xC125+0xC220，经原 WNDPROC49F860/DefWindowProc，结果 0；450 后置 blit 全 clip2、1350 样本匹配，全量 370057 有差异；新 TextExtent/TextOut 代理未调用，无源文本证据。实际 32/64 合成 32 代次，错误 worker 负通过。region3 helper+自测计数字节不匹配，非强度；忽略 alpha，保留全量负例。源完整性已验：1EXE、8LPK、3DLL、2 引用、446 脚本、418IR、111USERCFG 未变。144 待办；4 项版本目标均活跃、100% 未完成。

# 2026-10-14阶段终点（更正前述待办）

144实际6handoff（非计划16）；337postblit全clip2/samples过，full369555差异。parent adapter断言非源码故障。145诊断：实际WM_NCHITTEST 0x84打包屏幕XY被误拒。146验证原WNDPROC 49F860加实际DefWindowProc对0x84返回HTCLIENT1同窗口；2handoff 113postblit全过，full369369差异。下一边界为系统实际发送的WM_SETCURSOR 0x20，wParam自有HWND需host→guest映射，不支持则保守停止；无源码文本API调用。进程exit0、worker errors[]、fixture cleanup true，非完整游戏成功。源完整性核对1EXE 8LPK 3DLL 2refs 446scripts 418IR 111byte USERCFG未变。四版本目标活跃全100%未完成。不虚构额外证据。

2026-10-15 R作品技术增量：新增11项SDK验证与3项自检，32/64位通过。范围含光标消息坐标、自有HWND映射、借用HCURSOR；0..64灰度原样、DWORD行对齐；nativePAINT64/72映射guest64，Begin/End配对。原程序150/151八字形查询、八缓冲读取、16次文字测量及BeginPaint成功；当前字体环境非日文原OS像素golden。父WM_PAINT因worker持锁受控停，EndPaint仅fixture清理；光标20源调用未证。对应阶段R_窗口光标与文字重绘证据_20261014。四版本100%及忠实TJS/画音/全路线仍未完成。

## 2026-10-15 阶段增量
更正：150/151均已运行，非“运行中/151未运行”。

- 150：6轮；原字形API 16次=查询8+取灰度8；文字测量16。
- 151：10轮；同worker TID 13980；字形16、测量16；8灰度缓冲解析0..64，无猜缩放；首块14×13、stride16、182像素。
- 原BeginPaint 40D6C3：真实nonnull HDC、guestPAINT64、rcPaint[0,0,800,600]；父WM_PAINT在EnterCriticalSection 200E3C0因他线程持锁受控停止，源EndPaint未执行；仅worker parked时fixture EndPaint1严格成对。
- 未证：完整重绘；151完整RGB仍差370068颜色字节；cursor20/SetCursor未源调用；SDK双架构通过不冒充原证；150/151 exit0、errors空、cleanup通过均非原退出；149代理地址重叠失败已修，不算游戏错误。
- 下一步：实现持锁工作线程安全让出、父原绘制接续；禁止同Unicorn并行与锁假返回。
- 四版本100% goal active、忠实TJS/音频/全路线未完成。

## R 作品 skill 增量（153／154／155／156）

**153（实际锁释放＋原重绘整帧零差异）**：实际 key `02003B50`，worker 28996 leaves depth 0，actual native Leave `RA45214A`；parent 17084 CPU/FS 0 已恢复并 actual enter。原始 `WM_PAINT 49F860` 实测 `Begin RA40D6C3`／`End RA40D864` 返回 BOOL 1，同 worker 创建者仍存活，800×600 全帧 RGB 差异 0／`SHA07419b…`。**同时留存 153 恢复重入失败**：worker resume 旧 proxy ret 触发 repeat Leave 与 owned guard `RuntimeError`，root adapter 非 game。

**154（精确 proxy）**：Stdcall 8 字节 `[ra,key]` pop，EIP=ra 先于 yield，无 fake unlock；worker 27012／parent 22492，gen13→14 多一片；16 logical parent rounds 无失败无错误，全帧 RGB 0／`SHAc303be1f…`，actual original `EndPaint` 1。

**155（测试输入＋取证 cap 停）**：仅 owned `PostMessage` move/down/up `715385`，flags 0/1/0，非物理输入，在 actual source paint 之后；WndProc 512/513/514 返回 0，引擎／脚本字节未改。29 rounds 全帧 RGB 0／`SHAd14d…`，旧 root `SetRect` 取证 cap 2048 停；source `loosepic/bg64.elg` 查询缺失、可能 archive fallback，**不得声称完整 first story**。

**156（待验）**：仅扩 root rect cap 至 8192，real guards 不变，pending 无结论。

**100% 保留**：FullOT/OTA/OTV/OTR 100% goal active、未完成；**不得猜测 source 标题等于完整 GameInit**。Original GetFocus/SetFocus/async state 未知；source events／audio／routes／final TJS／full scheduler／Exit／loader／TEB 全部仍缺。原 PE／DLL 从未 OS 加载，写入全在 workspace，original backup 只读，source integrity 终验 pending；不称 all clipping fixed、不称 every blit sample pass，initial NULL negatives 保留。capture 3 未导入原 EXE（synthetic only）。

# 2026-10-15 最终收据（增量 · 更正 156 待验）

- 156 更正：真实完成 40 逻辑父轮。
- 明确测试 3 条：PostMessage move / down / up 由原 WndProc 处理。
- 无 worker / parent 异常。
- SetRect 真实 3281 次，观察 cap 8192。
- 完整 RGB 差 12600 仍保留，不当完全通过。
- 截图仍为 R 标题菜单；bg64 loose 探测不能证明进入正文。
- 153 / 154 / 155 三次完整 RGB 为 0，只证明对应源缓冲 / 原窗口时刻；初始 NULL 反例不抹掉。
- 全四版「全部原逻辑 / 剧本 / 忠实 TJS / 路线状态 / 画音 100%」仍未完成。
- 下一步：追根原输入对象状态与标题 START 触发链，未以未知 API 伪返回。

（仅上列给定事实，不补理由、不外推。）

## 2026-10-15 原输入回调与坐标证据
适用：R版及其自建还原基准skill。159/161 用 ownClientToScreen+SetCursorPos 对齐 (715,385)，非物理注入。真实尾转发：原 WNDPROC 49F860→49F8F0；513/514 485920→485B20/485B50；161 最终 targets 00481F70/00481F80，manager +C94→44D9C0/44D9F0。161 source_late_OS_calls 空，不得称两新 OS 接口原码已验证，仅有限 recipe；源 native≠TJS 100%。

## 2026-10-15 case162真实输入设备与线程优先级

162动态source：11父轮，AL类型=2，device=0x71ce080，manager=parent+0xC94。地址源方法 0x459020 源按下：device+4=0、+14=0→0x10、+24=0→0x80；地址源方法 0x459050 源松开：device+4=1、+14=0x10、+24=0x80→0。设备非父对象内嵌状态；父对象范围零差异不能证明按钮未被处理，真实设备字段变化已由原码证实。SetThreadPriority original RA 0x40cca5/0x40cd46，guest HANDLE 0x69D80000 map own host，actual same worker TID 23232，priority 0→-2→0，真实BOOL 1/error 0，worker owner cleanup再恢复0。PostMessageA本例未执行，不写已验证。本例下一未映射 KERNEL32 API 为 lstrcpynA，hintRVA 0x00126C16，不是未知 VM 指令；root 另记 next-source-boundary。worker_errors空/17 cleanup receipts仅fixture，不等全引擎成功。新动态输入仍不等正文开始/目标TJS 100%。源输入/device精确JSON见input-state-162-derived.json。


## 2026-10-15 原字符串与输入页阶段增量

作品知识增量 · 我们没有翅膀——格雷塔迦露德与柳木原
来源：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原字符串调用与输入页清理证据_20261015/README.md
一、9 SDK + 6 selftests = 15 工程文件；32/64 全部 6 selftest 通过。
二、仅 164 新桥读取 offset0..26（27 字节含 NUL）后停止；163 旧桥仅作输出 SHA 对照（dst0x7655528、src0x88d50c2 仅 164run）。
三、input 为维护非菜单消费：device0x071CE080+0x14 由 0x10→0，458FD9 AND / 45900A XOR byte4 由 worker25240 操作，main1836 up24=0，41 条源写。
四、165 actualForeground BOOL1/error0，四次 title fullRGB0，最终白色全帧 hash680a1c22a8e114ea0c637847e8cc506794073a55f4350364c8a0421e7dbcc8f0，非对白。
五、166 仅 magic TOB0+1347 与 registered 0x82D4080，不足以同一性；worker_errors[]，74/80 轮止于 GetWindowLongA -16 40D16D rootadapter assert。
六、167 失败无终验：getter 接续后 setter -16 value348782592 return4247943 边界 assert，无最终 threadprefix 报告，不假报 cleanup。
七、168 80 轮、worker_errors 空、root failures 0、host-fixture-cleanup passed、6 次 registered 扫描（10/20/40/60/80/81）无 magic、style getter/setter 与 lstrcpynA 原调用 0、actualSetForegroundWindow BOOL0/error0/actual_foreground_is_owned false（保留真实 OS 拒绝，不单点因果）。
八、169 已终态 exit0/80 轮/worker30324/errors[]/parentfail0/hostcleanup passed，source169-summary.json 已落 stage；两次 actualSetForegroundWindow BOOL0/error0/foregroundownedfalse，第二次 START 三个 ownedPostMessage 在 45/46/47 轮真实发出，cursor 期间用户另行移动则保留用户位置、不强行恢复；6 次 registered heap 头扫描全部无 magic，style getter/setter 原调用 0、lstrcpynA 原调用 0；未确认 S00 文件 SHA 同一性，不报完成，168/169 均属有界负例。
九、四版 100%、目标 TJS、全路线画音未完成；OTV MAGES 任务 DSL+CRI 非 Lucifen；配方依赖旧 ignored 缓存非 standalone。
下一有限路径：前台资格未满足则避免 80 轮重复空转；同时独立并行推进 TOB 已有 IR/原 VM 轨迹到目标 TJS 的覆盖与未知拒绝契约、代表性演出/音频语义；R 当前 GUI 输入路线保留未验证，禁止伪造源 foreground 或成功。


## R_TJS文字流与标量核证据_20261015 · 作品技术增量
- 入口：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_TJS文字流与标量核证据_20261015/README.md`（stage 内另含 `verify-target-runtime.txt`、`verify-source-target-vectors.txt`、`verify-target-faults.txt`、`source-runtime-summary.json`、`original-native-reconciliation.json`、`negative-controls.json` 等）。
- 两个真实目标模块：`编程组/原作忠实层/R/r_u32.tjs`、`r_literal_run.tjs`；真实校验器 `证据目录内r_byteflow_verify.tjs`；向量助手 `编程组/工具/r_tjs_numeric_vectors.py`、`r_tjs_case_lines.py`、`r_tjs_ir_payload.py`、`r_tjs_ir_parts.py`（只读）。
- `RValueOp` 仅 ops 13/19/20/23/41/44/45（**7 个标量操作**），严格 TJSInteger/u32mask/signed32comparisons，未知操作抛异常——**不是完整表达式 VM**。
- `RLiteralRun` 只按首 byte 分 1/2，lead 81..9F/E0..FC 第二 byte 可 00/5B，首 00/5B 停不消费；**无 Unicode 解码/绘制/标签语义**。
- 向量：1378 算术边界/随机 reference + 434 原码字符单元 fixtures + 7 补充 literal + 11 非法/未知拒绝 = **1830**；真实 `tvpwin32.exe` 与 `tvpwin64.exe` **各通过 1830**。
- 源对照来自 418 TOB、9,538,168 原 bytes / **59,367 个结构 island**：总 island 4,118,728 bytes、payload 3,904,210 bytes、**1,952,105 units**、marker 990 / nul 418 / limit 57959。
- 双架构并行约 8 秒全过：每架构 **59,367 checks**，逐 unit 绝对偏移与 width、逐 payload byte/end/stop 精确相等，不只 checksum；8 新鲜 nonce/日志/进程 exit0/jobcleanup 通过。
- **复用旧原 CPU 42F880/42FB00** 的 59,367 行 native 轨迹 SHA `d76de631eead4029d7af9b2cf00e7ef5fdd1f7260709ce037fc59afe73f35e06`（本轮未重跑原 PE），逐文件 sourceSHA/island 起止/consumed end/bytes/units/stop/payloadSHA 与本次全部一致。
- 负例：10 个 Python guard 通过；故意破坏加法与 81 lead 的两份临时 TJS 均被实际检出差异，engine exit0 但 **verdict=false**——不以进程 0 当通过；probe01 未加引号字典 key 错误已修，错误 fixture 保留。
- 明确未完成：不执行 218,615 条 TOB command、990 表达式 body、3349 参数 expr；不等于所有 island 语义；不负责可达/分支/全剧本/原窗口/字形/语音/音乐/完整画音/所有 4 版 100%；OTV MAGES Task DSL+CRI 非 Lucifen。
- 环境边界：仅当前 Win 环境 32/64 解释器测试，**未测 Win7/Win10/其他系统**；无新成品、术语沿用不改；原件/418 IR/446 scripts 最终完整性不变；下一有限路径＝把已原码验证的 VM memory/control/yield-PC/SP 续行移入 TJS，对未支持 native 生命周期显式拒绝而非空 stub/noop。


## R_TJS表达式VM与暂停恢复证据_20261015
- 6 生产核 `r_vm_entry/memory/control/value/step/run.tjs`（`编程组/原作忠实层/R`，复用已提交 `r_u32.tjs`）；13 个 TJS fixture 在本证据目录，5 个 Python 辅助 `r_vm_shadow_range/read/write`、`r_vm_access_log`、`r_vm_tjs_literal.py` 在 `编程组/工具`。
- 原 VM 47 opcode，目标仅 17：0,1,5,8,12,13,19,20,23,26,30,31,32,40,41,44,45；未知操作 throw；cold 写入口/压 0，warm 不重置 PC/SP，opcode 0 保留 fetch 后 PC 暂停。
- callback 读写 guest 逻辑地址而非 host 指针；maxSteps 只是验证守卫，不是游戏 limit。
- 3349 参数 expr + 990 inline 共 4339 × 6 states = 26034 cases、672 resume、26706 segments 每架构；真实 tvpwin32/64 全部通过，各 494442 有序写事件，逐 PC/op trace、native 帧、observed words、PC/SP 与返回精确比较。
- 原全内存 hash 与旧原 CPU oracle 逐条 reconcile，旧 oracle hashes anchored 于 `root-replay-comparison.json`；本批源 cases 新跑原 430090 binder，未新跑全部 source VM。
- 另 1390 合成 cases/1391 segments 本批确实在 Unicorn 运行原 4A7A30/50 VM，比全 live/source/PE 字节，两 TJS 架构同过。
- 14 guard 两架构通过；两个故意错实现（warm 重新入栈、错误 increment）均被检出，engine exit0 而 verdict false。
- 5 个 native fixture 仅 flags/固定 keyboard states/query list/invalid channel/control copy，非真实 lifecycle（valid channel 显式拒绝、无真实 audio cleanup，不执行 SOB/scene controller）；四版 100% 未完，OTV 是 MAGES Task DSL+CRI 非 Lucifen；下一步 binder/relocation 连接及其余 opcode 按独立小模块并行，再接真实 native/TOB 执行与演出画音。


## R_TJS表达式解析与重定位证据_20261015（ISSUE-20261011-02）
- 11 个新生产模块落 `编程组/原作忠实层/R`：`r_expr_read/header/relocations`、`r_parse_expression`、`r_inline_expr_header/relocations`、`r_parse_inline_expression`、`r_relocation_pair/writes`、`r_record_value/arguments.tjs`。
- 两格式必须分开：参数 3349＝长度/size u16 ＋ count u8；inline 990＝`[s` 两 byte 标记后长度/size/count u32（`+` 不属于魔数）；保留 flag、顺序、重复／未对齐 reloc。
- 银行 0/1/2 group、3 字符串 base+index、4 codebase+index；u32 地址与 value；未知 bank 不猜、明确 throw。
- 覆盖：4339 源表达式重解析对旧 metadata；每表达式 2 状态、真 Unicorn 调原 430090 全 8678；16 个真 tvpwin32/64 并行约 8s 全过，每架构 4339 parsechecks＋8678 relocationplans。
- 178 synthetic checks 每架构通过（126 拒绝／48 recordprimitivecase／4 其他 positive）＋2 合成 relocation plans；record-value 六 kind 与 record-arguments opcode0 反转对 Python reference；expression 回调仅 fixture 返回值，非整合 TJS VM，本批未重跑原 42FB50。
- 故意错基址与条件反转两份注入均已检出；原件/脚本/IR 完整性复验不变，限本期范围。
- 限制：纯 relocation-write 计划尚未实际写回、不执行 flag 0→1／lazy cache，非完整绑定运行器；未串接 129 命令派发／native 生命周期／画音／四版 100%；原 PE 仅 Unicorn 不 OS load；OTV＝MAGES Task DSL+CRI 非 Lucifen；无新成品、无其他 Windows 版本验证。
