---
name: oretsuba-psvita-work
description: 《我们没有翅膀》PS Vita 版（俺たちに翼はない，PCSG00299）专属工程索引——配合通用解包 skill（psvita-unpack）与通用翻译规范 skill（galgame-translation）使用。含该作引擎事实、PFS 解密与 CRIWARE 解包管线、Tasktype 脚本格式与资源寻址规则、文本规模、说话人表与专名待裁决清单。开工前必须与通用层一同读取。
---

# 我们没有翅膀（PS Vita 版）· 作品专属 skill

> **本文件仅适用于『俺たちに翼はない』PS Vita 版（PCSG00299）**；跨作品成立的通则一律归 `.zcode\skills\psvita-unpack\` 与 `.zcode\skills\galgame-translation\`。
> 资源与重构细则见 `工程\我们没有翅膀PSV\美咲线资源与重构说明.md`；过程记录见 `工程记录\2026-09-17_对于我们没有翅膀PSV版解密与重做可行性的分析-02.md`。

## 〇、作品身份

| 项目 | 值 |
| --- | --- |
| 原名 | 『俺たちに翼はない』（PS Vita / PS3 移植版） |
| 中文译名 | **我们没有翅膀**（PS Vita 版） |
| 平台 / 编号 | PlayStation Vita，`PCSG00299`（另有 PS3 版，同日期） |
| Content ID | `JP0745-PCSG00299_00-ORETSUBA0000VITA` |
| 发售 / 发行 | 2014-04-10 ／ Navel 开发、5pb.（MAGES.）发行 |
| 分级 | CERO C（15 岁以上） |
| 与 PC 版关系 | **以 PC『我们没有翅膀R』为基础**，新增 **林田美咲攻略路线** + 新 CG + 新 OP「PRECIOUS」，并收录《～Prelude～》的若干短篇 |
| dump 形态 | **NoNpDrm**（假授权 + PFS 加密内容），3.1 GB / 60 文件 |
| 工程目录 | `工程\我们没有翅膀PSV\` |
| 原始 dump 路径 | `工程\我们没有翅膀PSV\我们没有翅膀[PCSG00299][日版][日文][NONPDRM]\`（**只读**，未改写；**文件** mtime 仍 2018-09-28） |

## 一、引擎（含版本与识别特征）

| 项目 | 值 |
| --- | --- |
| 引擎 | **5pb./MAGES. 自研文本 ADV 引擎**（公开世界无命名、无解包先例） |
| **不是** | 不是 Lucifen（那是 PC 原版/R 版）、不是 KiriKiri/KAG。脚本里出现的 `[iscript]`/`[include file=]`/`[define]` 等 KAG 风格标签**全部位于 `//` 注释内**，是历史遗留写法，不参与运行 |
| 识别特征 | ① 归档为 CRIWARE：`CG/CHR/SCRIPT/SystemData/ETC.cpk` + `VOICE/BGM/SE.AWB` + `media\data\*.usm`；② 脚本为 **Shift-JIS 纯文本**，`[Section]{ :Key value }` 嵌套结构；③ 指令集为 `:Tasktype "…"` 形式，实测非注释Tasktype字段52种；注释另含3种；运行时能力未完全核实；④ 全局表 `adv.txt`/`scn.txt`/`chrNNN.txt`/`chract`/`CGMODE` |
| 开发者痕迹 | 脚本注释含 MAGES. 内部署名，如 `//MAGES.松山--シーンジャンプ処理ここから。--` |
| 字体 | **所有 CPK 内无任何字体文件** → 引擎用 PS Vita 系统字体，或字体编在 `eboot.bin` 内 |
| `eboot.bin` | 877,280 B，**仍是加密 SELF**（头 `53 43 45 00`），未解密；文字渲染路径在其中 |
| 引擎识别结论的证据 | VNDB 的 PS3/Vita release 页 Engine 字段**全为空**（PC 原版与 R 版写 `Lucifen`）；GARbro 支持格式表只覆盖 PC 版 LPK1；GitHub 检索 `PCSG00299`/`oretsuba` 均 0 条 |

## 二、解包管线（与通用 skill 的对应关系）

**对应通用 skill：`.zcode\skills\psvita-unpack\`**（本作是该 skill 的首个沉淀作品；PFS 解密、CRIWARE 提取、Tasktype 脚本解析三部分均已在其中成文）。

本作实际用到的步骤：

| 步骤 | 做法 | 备注 |
| --- | --- | --- |
| 1. PFS 解密 | 上游官方预编译 `psvpfstools v2.0` 的 `psvpfsparser.exe -i <app> -o <out> -k <klicensee> -f http://cma.henkaku.xyz` | 密钥取自 `sce_sys\package\work.bin` **偏移 0x50**（NoNpDrm 假授权）。本作密钥 = `238dbe01ab89893c81431287a1dee15d`。**26.5 秒**完成，末行 `keystone: matched retail hmac` 为通过标志 |
| 2. 解 CPK | `cricodecs`（Python，`pip install --target 工具/pylibs cricodecs`）`Cpk.load()` + `file_bytes(index)` | **该库的 C++ 读取器不支持非 ASCII 路径**，必须先 `os.chdir()` 到 media 目录再传纯文件名 |
| 3. 解音频 | 本机 ffmpeg 自带 **ADX 与 HCA** 解码器，逐条 `ffmpeg -i raw -c:a libvorbis -q:a 3 out.ogg` | `VOICE.AWB` 是 AFS2 容器内 HCA；`BGM.AWB`/`SE.AWB`/`SystemSE.AWB` **其实是 CPK 容器**，条目无文件名（只可按索引取），其中 SE 混有 ADX 与 HCA，用 magic 逐条判型 |
| 4. 解影片 | `ffmpeg -i x.usm …` 可直接读 USM | 本机 ffmpeg 是 lgpl 构建（无 libx264），用 `libopenh264` |
| 5. 脚本解析 | `工程\我们没有翅膀PSV\工具\parse_adv.py`、`collect_misaki_assets.py`、`extract_misaki_assets.py`、`resolve_asset_ids.py` | 均为本作沉淀 |

**本作不适用的步骤**：`.zcode\skills\lucifen-unpack\` 对本作**完全不适用**（PC 版 LPK/SOB/TOB 与 Vita 版 CPK/文本 DSL 是两套体系）。

## 三、文本承载方式 / 编码 / 技术约束

| 项目 | 值 |
| --- | --- |
| 剧情脚本 | `SCRIPT.cpk` 内 **499 个未压缩文件**（`M##_##` 美咲编、`S##_##` 本篇、`P##_##` Prelude、`CGMODE`、`chract`、`adv.txt`、`scn.txt`、`chrNNN.txt`） |
| 源编码 | **Shift-JIS（CP932）**，`\r\n` 换行 |
| **长度约束** | **无**——文本是运行期解析的自由文本字段，译文长度可变。这与 PC 版 Lucifen 的"字节长度硬依赖"形成鲜明对比 |
| 台词字段 | `Message` 任务用 **`:Message "…"`**；`SceneJumpDialog`(447) / `MessageSwitch_Tag`(25) 用 `:Text "…"`（**是场景跳过梗概文，不是台词**） |
| 换行 | 文本内用转义 **`\n`**（468 个 Task 使用，含 14 个 Message） |
| 引号 | **无转义机制**；文本内引号是全角 `”`，实测含裸 `"` 的消息为 0 |
| 说话人 | `:Name N` 为**数字 ID**，显示名在 `adv.txt` 的 **`[Name]` 表（362 条，`:NameN "显示名",0`）** — 可直接翻译 |
| 排版 | 消息窗/名字窗几何在 `adv.txt` 的 `[Window]`→`[Window0..5]`/`[MainWindowN]`/`[NameWindowN]`（`:Shape`/`:UV`/`:Texture`/`:FontScale`/`:NameFontScale 0.8125`） |
| 音乐音效 | `:BGM N` / `:SE N` 为**归档内索引**（BGM 0..87↔96 条目、SE 0..700↔701 条目完全吻合） |

### 资源寻址规则（**重构/回写时必须照抄**，否则必然取错资源）

1. `:Texture N` —— **不是归档索引，是场景内局部编号**（1,330 个编号中 **602 个**在不同脚本里名字不同，这是「编号为场景局部」的直接证据）。**必须按注释里烘焙的名字解析**：`:Texture 533 // EF01` → `CG.cpk\ef01.png`；`:Texture 165 // ST_ASU01` → `CHR.cpk\ST_ASU01.png`。覆盖率：1,909 个不同注释名中 **1,897 个（99.4%）** 能在归档按名找到；12 个找不到的（`BG06*`/`BG07*` 6 个 + 5 个旧名 + `NULL`）中，`BG06*`/`BG07*` 在归档里是**拆成 8 片存储**（`BG06_0.png`…`BG06_7.png`，脚本引用基名），**这 11 个在美咲线引用数均为 0**。
2. 立绘 `:Number c,p,c,e,s // 置換しました<<st_xxx>>` → 按 `<<…>>` 里的名字解析（本线 1,323/1,323 全覆盖）。
3. `:SE`/`:BGM`/`:Voice` → 归档索引，直接按序取。
4. `:Image`（EyeCatch）：**模式 0** `:Image 0,N` → `CG.cpk` 的 `EC*.png` 按**归档 TOC 顺序 1-based** 取第 N（注意归档缺 `EC20`/`EC30` 导致整体 −1，**不能按 EC 编号数字**）；**模式 1** `:Image 1,s,b[,f]` → `SystemData.cpk` 的 `ec_bg*.png` 按 **TOC 顺序 0-based** 取第 `b`。字段 `s`/`f` 语义未确证。
5. `:Movie N` → `adv.txt` 的 `[Movie]` 表直接给出文件名（12 项；`Movie7=ED_misaki.usm`、`Movie11=OP03.usm`）。
7. **分片资源**：部分资源以「`{基名}_{序号}.png`」拆成 8 片存储（全作 6 组：`BG06`/`BG06A`/`BG06B`/`BG07`/`BG07A`/`BG07B`），脚本引用**基名**。美咲线引用为 0；扩到全量时必须按基名把 8 片一起取。
8. **`cricodecs` 取数据的坑（必读）**：`Cpk.file_bytes()` **必须传 `c.files` 的列表下标**；传 `CpkEntry.id` 会**取到别的条目**（实测 CG.cpk 946/946 全错、SystemData.cpk 165/182 错、ETC.cpk 122/124 错）。另 `CpkEntry.file_offset` 是**绝对偏移**（不要再加 `content_offset`，加了反而错位）。这是本次交付中一度导致图像规格与 UI 判读全错的根因。
6. `adv.txt` 的 `[Texture]{ :TextureList "texturelist.txt" }` 指向一个**归档内不存在的文件** `texturelist.txt`——1:1 复刻原引擎的纹理编号机制无法从资源侧复原，但按名字解析已完整覆盖。

## 四、文本规模与归档清单

**全作**：65,485 条 Message / 2,183,751 字符 / 24,873 条带 `:Voice` / 24 条 `SetSceneName` 章节标题。
（口径：**先剥离 `//` 注释、再切 `[TaskN]{…}` 块**。美咲线按此口径为 **4,904 条 / 141,956 字符**。）

**分线路（台词数 / R 版语料未收录比例）**：

| 组 | 台词数 | R 版未收录 |
| --- | --- | --- |
| `S##` 本篇 | 57,947 | **0.2%**（仅 113 条）→ 与已交付 R 版实质一致 |
| `M##` 美咲编 | 4,323 | **91.0%** |
| `P03` ある日の美咲 | 581 | **92.1%** |
| `P01/P02/P04` 其他 Prelude 短篇 | 2,634 | 94.0% |

**归档清单**：

| 归档 | 条目 | 内容 | 规格 |
| --- | --- | --- | --- |
| `CG.cpk` | 946 | 事件 CG + 背景 + 效果 + `EC*.png` | PNG；CG 960×540、4:3 系 960×720 |
| `CHR.cpk` | 1,333 | 立绘（`ST_*.png`） | PNG RGBA，典型 426×630~473×630 |
| `SystemData.cpk` | 182 | UI：消息窗/选择窗/标题/存档/相册/眼catch 背景 | PNG；**部分含预渲染日文**（如 `sys_menu.png` 是系统提示文图片） |
| `ETC.cpk` | 124 | 转场/规则图（`RULE###.PNG`、`black/white.png`） | PNG |
| `SCRIPT.cpk` | 499 | 脚本与数据表 | Shift-JIS 文本；归档文件 27,998,224 B（内部条目合计 27,458,719 B） |
| `VOICE.AWB` | 26,500 | 语音 | AFS2 内 **HCA** 22050 Hz 单声道，源未加密 |
| `BGM.AWB` / `SE.AWB` / `SystemSE.AWB` | 96 / 701 / 2 | BGM / 音效 | **实为 CPK 容器**，内 **ADX** 48000 Hz 立体声（SE 全作口径混 **3 条 HCA** = id 698/699/700；美咲线取到的 72 条里有 2 条） |
| `media\data\*.usm` | 12 | OP00-03 / ED×7 / Poem | CRI Sofdec2 |

## 五、专名与说话人

**说话人（`:Name` 编号）**：全作共 **362 条**，见 `工程\我们没有翅膀PSV\美咲线清单\名字表.tsv`（含"美咲线引用次数"列）。**美咲线实际用到 37 个**，逐条译法与证据来源见本目录 `术语表.md`。

**已可复用的既有译名**：15 个说话人可由 `工程\我们没有翅膀R\工具\name_map.py`（R 版已交付成品实测）直接沿用：鹰志 / 鹫介 / 日和子 / 高内 / 明日香 / 京 / 藏人 / 小鸠 / 咲夜 / 狩男 / 翔 / 伽楼罗 / 纪奈子 / 声 / カケル→翔。

**⚠️ 待裁决（2 项关键 + 20 项次要）**：

- **`美咲`（编号 342，297 次）与 `林さん`（编号 332，225 次）** —— 林田美咲是 PS3/PSV 独占女主角，**R 版成品里没有她的译名可沿用**。中文写法建议沿用「美咲」（`咲` 为中日通用字形，不简化为"笑"）；`林さん` 是鹰志对她的敬称，建议「林小姐」或「林同学」。**属作品层术语表裁决项，须主代理确认后再定，不得自行择一。**
- 其余 20 项为 `女生徒`/`男子Ａ`/`昌子の友人Ａ`/`玉袋もみ子`/`火サスっぽい女` 等次要与泛称。注意 **R 版对这些未收录名保持日文显示**（`name_map.py` 自述"未收录者保持日文显示"），因此**没有现成译名可抄**，重构时需补译。

## 六、已交付资源（2026-09-17）

`工程\我们没有翅膀PSV\素材\美咲线\` —— **2,249 文件 / 273 MB**：31 个线路脚本 + `adv.txt` + `scn.txt`；376 张 PNG（cg 108 / chr 253 / etc 3 / eyecatch 12）；1,837 个 OGG（voice 1737 / bgm 28 / se 72）；2 个 MP4。清单与映射结论在 `工程\我们没有翅膀PSV\美咲线清单\`。

## 七、已知缺口

UI/系统素材（306 张）未提取（线路脚本不按名字引用 UI，重构时需补）；字体不在资源内；45 条含特殊字符的 Message 未被简单规则提取；`texturelist.txt` 缺失；模式 1 EyeCatch 的 `s`/`f` 语义未确证；其他 Prelude 短篇（2,471 条独占台词）未提取；`eboot.bin` 未解密（仅影响"汉化 PSV 原版"路线）。


## 2026-10-11 原作结构保全增量

据主代理提供实测事实：499 files 27458719 bytes 1337747 lines逐字节重组，无CP932错误；Tasktype 52种120325项；旧parse_adv当前跑52种120320项漏5；另有VoicePlay/VoiceStop/CharacterQuake三种类型仅在注释，共7个字段出现；旧55的原统计命令未复现，仅说明52+上述3=55的可能口径，不宣称已证明旧统计来源；12 opaque中2 inline header-open待/可结构识别，余10原样保留；运行时未解，52非引擎能力上限，完整忠实脚本未生成。证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/结构证据_20261011/OTV_逐字节保全.json、OTV_旧解析器差异.json。
