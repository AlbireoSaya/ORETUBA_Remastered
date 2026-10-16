---
name: kirikiri-unpack
description: KiriKiri（吉里吉里 / KiriKiri Z / krkrz）引擎的识别、XP3 归档解析与重打包、HIKARI FIELD·Applique 系「压缩型 XP3」自定义变体、.sig 外部签名与 Cxdec 系保护、KAG/KAGEX 与 PSB 脚本层判定，以及「用这套引擎自建游戏」的可行性结论（含自研标准 XP3 打包器与实机验证证据）。适用于日本 galgame 的解包/汉化/移植与自制评估。具体作品的专名、译名与字串坐标见各作品专属 skill。
---

# KiriKiri / KiriKiri Z 引擎作业 skill（kirikiri-unpack）

> ★ **原理参考**：引擎的工作逻辑、TJS2 真实语义、图层/事件/存储/存档机制、调试手段与常见误传纠正，见同目录 **`引擎工作原理.md`**（2026-09-17 依据 krkrz 1.4.0r2 源码写成，长期指导文件）。本文件是**作业手册**（识别 → 解包 → 判定 → 复刻）。

> **定位**：跨作品成立的通则 —— 引擎识别、归档格式、签名/保护机制、脚本层判定、以及"能否用它做游戏"的结论。
> **不含**：具体作品的专名译名（见 `工程\<中文译名>\作品skill\`）、翻译规范（见 `.zcode\skills\galgame-translation\`）。
> **本次来源**：2026-09-17 ISSUE-20260917-05，对 Applique（あっぷりけ）两款 Steam 游戏 `CrossConcerto`（《交汇协奏曲》，AppID 2109640）与 `tsukikage`（《月影魅像-解放之羽-》，AppID 1069230）的实测。
> **证据分级**：下文每条尽量标「实测」/「未确认」。**未确认项不得当作定案**。

---

## 1. 引擎识别特征（判断一个游戏是不是 KiriKiri / krkrz）

| 判据 | 实测值（Applique 两作） |
| --- | --- |
| 归档 | 目录下有 `*.xp3`（11 字节魔数 `58 50 33 0D 0A 20 0A 1A 8B 67 01`） |
| 插件目录 | `plugin\*.dll`，含 `wuvorbis`/`wuopus`/`krmovie`/`layerExDraw`/`windowEx`/`k2compat`/`KAGParserEx` 等 KiriKiri 系插件 |
| 主程序 | `*<作品名>.exe`，PE 版本资源 `OriginalFilename = tvpwin32.exe`、`InternalName = tvp2/win32`、`LegalCopyright = (KIRIKIRI core) (C) W.Dee and contributors` |
| exe 内串 | UTF-16：`Kirikiri Z Executable core`、`TJS2 version 2.4.1`（**注：这是生成解析器的 Bison 版本号，不是 TJS2 版本**；实际 TJS2 = **2.4.28**，见《引擎工作原理》§1）、`http://krkrz.github.io/`、`kirikiriz`、`TVP(KIRIKIRI) Z core / Scripting Platform for Win32`、`startup.tjs` |
| 版本资源 | `FileVersion` / `ProductVersion` = **1.2.0.3**（wamsoft 定制构建；官方发行版 `krkrz 1.4.0r2` 的 `tvpwin32.exe` 是 **1.4.0.8**） |
| 配置文件 | 同级 `*.cf`（明文，键 `datapath` / `vomstyle` / `wheel`，值以字面 `\xNN` 转义存储），如 `datapath="$(appdatapath)/あっぷりけ/CrossConcerto"` |
| 存档路径 | `$(appdatapath)\<品牌>\<项目名>\`（`appdatapath` = `%APPDATA%` 系），**不在游戏目录** |
| 安全选项 | exe 内明文 `-- TVPSystemSecurityOptions … --`；两作取值不同：《交汇协奏曲》=`disablemsgmap(1):forcedataxp3(2):acceptfilenameargument(0)`，《月影魅像-解放之羽-》=`forcedataxp3(1)`（见 §6） |
| 旁证 | 文件旁成对的 `.sig`（见 §5） |

**KAG 系变体判据**：`plugin\KAGParserEx.dll` 存在 ⇒ 使用 **KAGEX 方言**（TJS 类 `KAGParser`，方法 `loadScenario/callLabel/curLabel/curLine/paramMacros/onScript/onScenarioLoad` 等）；`plugin\kagexopt.dll` 存在 ⇒ 构建期把选项描述注入 exe（只导出 `GetOptionDesc`，**不是运行时插件**）；`textrender.dll`（作者 wamsoft）+ `multiimage.dll` 亦是 KAGEX 系组件。

---

## 2. 工具链与获取

| 工具 | 用途 | 获取 | 许可 | 本机落盘 |
| --- | --- | --- | --- | --- |
| **krkrz 官方发行包** `krkrz_20171225r2.7z`（1.4.0r2） | 引擎本体（含 `tvpwin32.exe` / `tvpwin64.exe` / `plugin` / 示例 `imageviewer`、`movieplayer` / 调试器 `krkrdebg.exe`） | `https://github.com/krkrz/krkrz/releases` | 源码 BSD 三条款式**自定义许可**：可再颁布/使用/修改，**无商用限制**、无强制署名，条件为保留版权与免责声明（见包内 `license.txt`） | `工具\krkrz\krkrz_20171225\`（已解出）+ `工具\krkrz\krkrz-1.4.0r2-src.tar.gz`（源码） |
| KAG3 / KAGEX | KAG 剧本系统与扩展方言 | `https://github.com/krkrz/kag3`；KAGParserEx 源 `https://github.com/wamsoft/KAGParserEx` | KAG3「改変・配布は自由」；KAGParserEx「吉里吉里本体に準拠」 | 未下载（自制时再取） |
| **`xp3pack.py`**（本工作区自研，纯标准库） | **标准 XP3 打包 / 列表 / 解包 / 自检** | 本 skill 同目录 | 本工作区自产 | `.zcode\skills\kirikiri-unpack\xp3pack.py` |
| **`xp3_variant_hikarifield.py`**（本工作区自研，纯标准库） | 解析 HIKARI FIELD/Applique 系**自定义 XP3 变体**（`info` / `list` / `sniff` / `dump`） | 本 skill 同目录 | 本工作区自产 | `.zcode\skills\kirikiri-unpack\xp3_variant_hikarifield.py` |
| **`fe_crypt.py`**（本工作区自研，纯标准库） | **解密/加密 KiriKiri 原生 `FE FE` 密文/压缩文本流容器**（mode 0/1/2；`info` / `decrypt` / `encrypt` / `xp3`） | 本 skill 同目录 | 本工作区自产 | `.zcode\skills\kirikiri-unpack\fe_crypt.py` |
| GARbro（MIT） / KirikiriTools（MIT） / KrkrzExtract（GPL-3.0） / XP3PackGUI（Apache-2.0） | 通用 XP3 工具、exe 重签名 | `github.com/morkt/GARbro`、`github.com/arcusmaximus/KirikiriTools`、`github.com/xmoezzz/KrkrzExtract`、`github.com/srt19/XP3PackGUI` | 见左 | 未下载（只登记 URL） |
| THE NVL Maker | 中文圈基于吉里吉里/KAG 的自制工具 | `nvlmaker.net` | 见其站点 | 未下载 |

**下载纪律**：一律落 `E:\ZCode Workspace\Galgame\工具\`，不装系统盘（`AGENTS.md` §一 铁律 3）。7z 可用 Windows 自带 `C:\Windows\System32\tar.exe`（bsdtar/libarchive 支持 7z）解，无需装 7-Zip。

---

## 3. 标准 XP3 归档格式（自制游戏用这条）

```
0x00  u8[11]  魔数 58 50 33 0D 0A 20 0A 1A 8B 67 01
0x0B  u64     index_offset（索引块起始的绝对偏移）
0x13          —— 数据区起点 ——（本工作区打包器一律从这里开始写条目数据）
index_offset  u8 flag（0=原样索引 / 1=zlib 压缩索引）
              若 flag=1：u64 csize + u64 usize + zlib 流
索引（解压后）= N × 'File' 记录，每条含三子 chunk：
              'info'  u32 flags + u64 usize + u64 csize + u16 namelen + UTF-16LE 文件名
              'segm'  u32 mode(0=原样 / 1=zlib) + u64 offset + u64 usize + u64 csize
              'adlr'  u32 adler32(明文)          ← **引擎不校验此值**（源码里根本没有 adler32）；我们用它是为了自检「解包是否无损」
```

**用法**（自研打包器，纯标准库）：

```bash
# 打包目录 → xp3（默认 zlib 索引 + zlib 条目；可选 --store / --raw-index）
python xp3pack.py pack <游戏目录> <输出.xp3>
# 列表 / 摘要 / 解包
python xp3pack.py list  <归档.xp3>
python xp3pack.py info  <归档.xp3>
python xp3pack.py extract <归档.xp3> <输出目录>
# 自检：三种变体各打一次 → 再解包 → 与原文件比对 md5
python xp3pack.py selftest <源目录> <工作目录>
```

**自检结果（实测 2026-09-17）**：三种变体（zlib 索引+zlib 数据 / zlib 索引+原样数据 / 原样索引+zlib 数据）全部 round-trip md5 一致，`adler32=OK`。
> ⚠ `selftest` 的默认工作目录是脚本同级的 `_selftest\`（即 skill 目录内）。跑测试请显式把工作目录指到 `临时\`，免得把产物写进被 git 跟踪的 skill 目录。

**★ 实机验证（本条已闭环）**：把自研脚本 `startup.tjs` + `poc_lib.tjs` 用 `xp3pack.py` 打成 `poc.xp3`，交给 krkrz 1.4.0.8 的 `tvpwin32.exe` 直接作为项目根启动 → 窗口正常弹出、脚本执行、中日文混排文字正确渲染（含系统字体探测 `face=[微软雅黑] 宽(中)=18px`）、`Scripts.execStorage("poc_lib.tjs")` 二次加载成功、60 秒定时器正常退出。
证据截图：本 skill 同目录 `poc_windows_render.png`（736×519，2026-09-17 实机抓取）。

```bash
# 复现（POC 工程见 子代理工作区\ISSUE-20260917-02\poc\）
python xp3pack.py pack game poc.xp3
runtime/tvpwin32.exe "<绝对路径>\poc.xp3"      # 以 .xp3 为项目根
runtime/tvpwin32.exe "<绝对路径>\game"          # 以目录为项目根（散装模式）
```

---

## 4. HIKARI FIELD / Applique 系「压缩型 XP3」自定义变体

> **写入侧非标准、读取侧仍标准**：头部与首个索引块之间多 4 字节残留、真实索引挂在**索引链**（`TVP_XP3_INDEX_CONTINUE`）的下一指针上、索引内含 `Hxv4` 总览记录（仅《交汇协奏曲》）、并在 0x28 埋反解包诱饵。★ **那个 `Hxv4` 记录就是 Wamsoft Hxv4 保护的特殊索引标记**（见 §11）。
> **★ 实测更正（2026-09-17 一审打回后复核）**：本 skill 早期版本称「标准读取器/打包器都不能直接处理它」——**该结论错误**。`xp3pack.py info`（标准实现）对两作 `data.xp3` 均成功读出 11,013 / 1,100 条条目：0x17 处那个字节是 flag `0x80`（= 原样索引 | CONTINUE），实现按 CONTINUE 链顺势在 0x20 读到真索引 `V`。**能否读取决于实现是否支持 CONTINUE（krkrz 规范的一部分）**；厂商加载器是否接受标准打包器产物属**写入侧，未实测**。

```
0x00  u8[11]  魔数（同上）
0x0B  u64     index_offset = 0x17     ← **标准字段**，指向一个「空索引块」
0x13  u8[4]   01 00 00 00             ← 头部与首个索引块之间的 4 字节残留，语义未确认
0x17  u8      块 #0 的 flag = 0x80    ← 0x80 = 原样索引(0) | TVP_XP3_INDEX_CONTINUE
0x18  u64     块 #0 长度 = 0（空块）
0x20  u64     下一个 index_offset = V ← 标准索引链：CONTINUE 置位后紧跟下一指针
0x28  u8[48]  伪 PNG 头诱饵（89 50 4E 47 0A 1A 0A 00 … "Warning\0"，被删掉 1 个 0x0D；不是条目）
0x58          数据区起点（= 88，即条目 idx0 的 offset；条目 offset 为**文件内绝对偏移**）
V     u8 mode=1 + u64 csize + u64 usize + zlib 流   ← 索引明文压缩，未加密
      V + 17 + csize == filesize（12/12 归档成立，可作完整性自检）
解压后 = 记录序列：
      'Hxv4'（仅《交汇协奏曲》有）payload = u64 u + u24 (V-u) + u8 ? + u16 ?
            实测 max(offset+csize) == u
      N × 'File'{ 'adlr'(u32 adler32) , 'segm'(mode/offset/usize/csize) , 'info'(flags/len/UTF-16 名称) }
      segm.mode 0=原样 1=zlib；offset 为**文件内绝对偏移**
```

**用法**：

```bash
python xp3_variant_hikarifield.py info  <归档.xp3>              # 头部字段 + 索引块摘要
python xp3_variant_hikarifield.py list  <归档.xp3>              # TSV：idx/name/mode/offset/usize/csize
python xp3_variant_hikarifield.py sniff <归档.xp3> [limit]      # 抽样探测内容层是否为明文
python xp3_variant_hikarifield.py dump  <归档.xp3> <起> <数> <outdir>
```

**实测要点（两作对照，决定后续工作量）**：

| 项 | 《月影魅像-解放之羽-》 | 《交汇协奏曲》 |
| --- | --- | --- |
| 文件名 | **完整保留** | **被剥离**：除 `startup.tjs` 外全部替换为占位名 `U+5000+n`（倀 倁 倂…） |
| adler32 命中 | 1,099/1,100、656/657、503/504 → **解包无损** | 1/11,013 → 内容层另有变换 |
| 内容层 | 图像/音频/`.scn` **明文** | **未知编码**（已排除 XOR/ChaCha/LZ4/LZMA/BZ2/明文；观测到"每文件一个常量字节 K 出现在偶数位"的 token 结构） |
| 结论 | 可解包、可读 | **归档层可解包，内容层受阻**（阻断台词提取） |

**条目保护位（实测）**：除那条诱饵声明 `.txt` 之外，**全部条目的 `info.flags` 都带 `0x80000000`（`TVP_XP3_FILE_PROTECTED`）**——《交汇协奏曲》`data.xp3` 11,012/11,013、`locale_cn.xp3` 90/91；《月影魅像-解放之羽-》`data.xp3` 1,099/1,100、`patch.xp3` 656/657。该位的语义**已由源码解决**：krkrz 1.4.0r2 中只有 `TVPAllowExtractProtectedStorage`（**默认 true**、无外部开关）会拦它 ⇒ **实际不生效、等同标记位**（`base/XP3Archive.cpp:24,452-453`）。⇒ 重打包**不必**复刻该位，我们的 `xp3pack.py` 写 `flags=0` 是安全的。

**每条归档 0x28 处都有同一张故意损坏签名的 1×1 PNG**（签名 `89 50 4E 47 0A 1A 0A 00`，缺 `0D`），tEXt 原文含 `Warning: Extracting this archive may infringe on author's rights.` 与日文警告 → 是**反解包声明，不是数据**；12 个归档里它对应的 `adlr` 恒为 `0x689792E4`（与实际不符）→ 该记录是诱饵。

**未实现 / 不要写成已验证**：该变体的**重打包**（需复刻 4 字节残留、索引链构造、`Hxv4` 记录、条目 `flags` 的 `0x80000000` 保护位、诱饵声明）、`PackinOne`/`psbfile` 内部算法、PSB(`.pimg`/`.scn`) 的完整结构解析。（注：`fe fe` 容器**已解**，见 §7 与 `引擎工作原理.md` §5.8，工具 `fe_crypt.py`。）

---

## 5. `.sig` 外部签名机制

```
212 字节：
0x00..0x1F  ASCII "-- SIGNATURE - SHA256/PSS/RSA --"
0x20..0x21  0D 0A
0x22..0xCF  3 行 base64（172 字符）→ 解码 128 字节 = RSA-1024 签名
0xD2..0xD3  0D 0A
```

- **覆盖范围（实测）**：`exe` + `plugin\*.dll` + **depot 内全部 `.xp3`**；**排除** `*.cf`、`steam_api.dll`、Steam 云文件（`*_autocloud.vdf`）、以及**非 depot 的 xp3**。
- **同一份内容签名不同**：两作插件 DLL 为 **25 / 24** 个，同名交集 **24**、其中 **21 个字节完全相同**（另 3 个不同：`PackinOne.dll`、`krmovie.dll`、`windowEx.dll`；《交汇协奏曲》另有独有 `fftgraph.dll`），而这 21 个同内容 DLL 的 `.sig` 两两不同 → **PSS 随机化**（无法据此判断签名对象是否含文件名）。
- **校验器不在任何明文里**（exe、各插件、`steam_api.dll` 全搜不到 `.sig`/`SHA256`/`PSS`/相关 OID）→ 只可能在**加密的 `.text`**（**未确认**）。生态侧对应 wamsoft 的 `sigcheck`（`Window.checkSignature()`；manual 原文：「exe や dll の場合は署名はファイルに内臓されます。**xp3 などの場合は、元のファイルに .sig をつけた外部ファイルを署名として処理されます**」——即「xp3 → 同名 `.sig` 外部文件」正是公开约定，来源 `https://github.com/wamsoft/sigcheck`）与 Cxdec 保护机理（外部资料：「Malformed exe/dll detected」弹窗来自 `startup.tjs` 的校验逻辑，见 `https://www.kungal.com/topic/2679`、`https://www.kungal.com/topic/2670`；绕过工具 `https://github.com/arcusmaximus/KirikiriTools`（MIT）、`https://github.com/sst311212/FuckBootStrap`。**均为外部资料，未在本机二进制内取证**）。
- **实战含义**：
  1. 改 `*.cf` **不会被签名挡住**（唯一确定安全的入口）；
  2. 改 `.xp3` / `plugin\*.dll` / exe **是否被拒载未实测**；
  3. **官方自己就投递了未签名的 xp3**（《交汇协奏曲》`adult.xp3`、《月影魅像-解放之羽-》`patch.xp3`，且磁盘占用差额算术证明二者不属于 Steam depot）→ **"未签名归档通道"存在既有先例**，但"运行时是否真的加载它"仍未实测。

---

## 6. 运行时保护与强制归档

| 机制 | 实测证据 | 含义 |
| --- | --- | --- |
| exe 加壳 | `.text` 段熵 **7.9999**、段内无自然字符串；`.bind` 段熵 7.9726（《交汇协奏曲》）/ 7.9620（《月影魅像-解放之羽-》）且 **PE EntryPoint 落在 `.bind`**（RVA 0x4ea310 / 0x4e5310） | 先执行外壳 → **静态改 exe / 打二进制补丁基本不可行**（归为 wamsoft **Cxdec 系**保护；来源 `https://www.kungal.com/topic/2670`、`https://github.com/Kinotern/KirikiriZ-exeFixPatch`——外部资料，未在二进制内取证） |
| `forcedataxp3` | exe 明文字段 `TVPSystemSecurityOptions disablemsgmap(1):forcedataxp3(2)`（交汇协奏曲）/ `forcedataxp3(1)`（月影魅像） | **强制从 xp3 载入**：把散装文件丢进游戏目录**不生效**，一切改动必须以归档为单位。⚠ **取值 1 与 2 语义完全相同**（源码只判 `!= 0`）；它**只决定启动时「工程根」怎么选**，**不改变归档内部的查找顺序** —— 详见《引擎工作原理》§2.1 |
| `disablemsgmap` | 同上 | msgmap 关闭 |
| `readencoding` | exe 内嵌配置区明文（《交汇协奏曲》raw 偏移 **0x3785F4**，位于 **`.rsrc`** 段）`readencoding="Shift_JIS"`，另有 `locale=cn`、`steam="yes"` | 两作是**显式指定**的 Shift_JIS。注意 krkrz 的**引擎默认是 UTF-8**（Shift_JIS 是 krkr2 时代的默认）——《引擎工作原理》§5.6 |
| `krkrsteam.dll` | 导入 `steam_api.dll`；TJS 类 `Steam`（成就/云存档/截图/overlay）；注册 `steam` 存储媒体；报错 `Steam must be running to play this game (SteamAPI_Init() failed)` | Steamworks 集成插件，**不是 Steam DRM**；来源为旧 KiriKiri2 插件树 `https://github.com/jeeb/kirikiri2/tree/master/kirikiri2/src/plugins/win32/steam`（含 `SteamAchievements.cpp`/`Storages.cpp`，CMake 版 `https://github.com/cokkeijigen/krkrsteam-plugin-cmake`；集成说明 `https://horizonglow2.blogspot.com/2019/01/steam.html`）——**外部资料**；另注：本机已解出的 krkrz 1.4.0r2 源码树 `工具\krkrz\src\` 内**无任何 steam 字样** |

---

## 7. 脚本层三种形态（判定与可读性）

| 形态 | 识别 | 读取方 | 实测可读性 |
| --- | --- | --- | --- |
| **KAGEX `.ks` / TJS 源码** | 文本；或以 `TJS2100` 开头 = TJS2 **编译字节码** | `KAGParserEx.dll` / 引擎内建 | 《交汇协奏曲》`startup.tjs` = `TJS2100` 字节码；《月影魅像》`.ks` 31 个/`.tjs` 222 个落在下面的容器里 |
| **PSB v3 场景（`.scn`）** | 头 `50 53 42 00 03 00 00 00`，BGI/Ethornell 的 PSB 容器 | `plugin\psbfile.dll`（TJS 类 `PSBFile/PSBStorage/PSBReadStream`，报错 `invalid psb file.` / `unknown compression method`） | 《月影魅像》97 个 `.scn`（data 86 + 追加盘 11，≈23.8 MB）内是 **UTF-8 明文台词**（`分 b'\x00'` 可切分：326,100 个 CJK 字符 / 19,238 条含中文串；同一文件内**混有 Shift-JIS 资源名**与 ASCII 命令串如 `SetBranchFlags(...)`）；**回写需重建 PSB 偏移表 —— 未实现** |
| **`fe fe 01 ff fe` 容器** | 5 字节头 `fe fe` ＋ mode ＋ `ff fe`；**mode 1 = 相邻位交换（自逆）** | **★ 已解（2026-09-20）** | 这是 **KiriKiri 引擎原生**的「密文/压缩文本流」（`base/TextStream.cpp:92-150`），不是厂商自研。工具 `fe_crypt.py`（`info`/`decrypt`/`encrypt`/`xp3`）；算法与实测见 `引擎工作原理.md` §5.8。**《月影魅像》1,100 条里 294 条是该容器（全 mode 1，可解）→ 其 UI/脚本层现已全部可读**；《交汇协奏曲》11,013 条中 0 条是该容器（另一套未知编码） |

> ⚠ **易踩的误判**：早期只检索 Shift-JIS / UTF-16 假名，会得出"`.scn` 无明文台词"的错误结论。**判定脚本是否含可读文本时，必须同时检索 UTF-8 中文（CJK 三字节序列）**。

---

## 8. ★「能不能用这套系统做游戏」——结论与路径

### 8.1 三条路线，各自结论

| 路线 | 可行性 | 依据 |
| --- | --- | --- |
| **A. 用 KiriKiri Z 引擎自建游戏**（推荐） | **可行，已实机闭环** | 引擎 = KiriKiri Z（krkrz），许可为 BSD 三条款式**自定义许可**：可再颁布/使用/修改、**无商用限制**、无强制署名（保留版权与免责声明即可）；KAG3「改変・配布は自由」。本工作区已用 `xp3pack.py` + 自制 TJS 脚本 + krkrz 1.4.0.8 跑通并截图（§3） |
| **B. 复用这两款游戏的运行时装自己的内容** | **不可行** | ① exe 全段加密 + 入口在 `.bind` 外壳（静态改码不可行）；② `forcedataxp3` 使散装覆盖失效；③ 剧本是 PSB v3 编译/私有容器而非可编辑的 KAG `.ks`；④ 归档为**非标准写入**（须复刻 4 字节残留、`Hxv4`、诱饵声明与条目 `flags` 的 `0x80000000` 保护位）→ 写入侧**未实现、未实测**；⑤ `plugin\*.dll`/归档/exe 带 RSA-1024 PSS `.sig` 校验链 |
| **C. 照抄 Applique 的观感做自己的游戏**（引擎选型 + UI 惯例） | **可行** | 只需在路线 A 之上叠加 KAGEX 方言（`KAGParserEx` 公开可得）与同一批公开插件（`extrans`/`extNagano`/`windowEx`/`menu`/`multiimage`/`wuopus`/`wuvorbis`/`textrender`…）；注意其中 `PackinOne.dll`、`lzfs.dll`、`psbfile.dll`、`multiimage.dll`、`kztouch.dll` **未找到公开来源**，是厂商私有件（**检索范围与时间：2026-09-17 检索 pantsudev《krkrz 生态指南》＋ GitHub／搜索引擎；本机 krkrz 1.4.0r2 官方发行包 `plugin\` 仅含 7 个插件，确不含上述件**） |

### 8.2 不可复用与法律边界

- **可以**：使用 KiriKiri Z 引擎本体、KAG3/KAGEX、公开插件来开发与（商用）发行自己的游戏。
- **不可以**：复用这两款游戏的**素材、剧本、角色、图片、语音**（Applique / HIKARI FIELD 版权），或把它们的 exe/归档当作发行基底。
- 使用 krkrz 需履行 BSD 式许可的条件：**保留版权声明与免责声明**（包内 `license.txt`）。

### 8.3 自建路线的最小落地清单

1. 取 `krkrz` 发行包（`github.com/krkrz/krkrz/releases`，1.4.0r2）→ 用其中 `tvpwin32.exe` + `plugin\`（`tools\krkrz\` 已有）。
2. 写 `startup.tjs`（引擎默认启动脚本名，可用 `-startup=<名称>` 覆盖），用 TJS2 搭窗口/图层/文字；需要 KAG 剧本系统时另取 KAG3/KAGEX。
3. 资源与脚本用 `xp3pack.py pack <目录> <data.xp3>` 打包（或先用散装目录调试）。
4. 发行目录结构：`<game>.exe`（= 改名的 `tvpwin32.exe`）+ `plugin\` + `data.xp3` + `*.cf`。

---

## 9. 已知坑（以本机实测为主；个别为推断，已在行内标注）

> **★ TJS2 语义级坑另见《引擎工作原理》§5.7**（2026-09-19 UI 组实测补充 **11 条 —— 逐条见下方 §9.1**；早期摘要：无 `String.lastIndexOf`／无 `charCodeAt`／无全局 `parseInt`／`Array.load` 是实例方法／未定义标识符报「未找到 Member」／Dictionary 缺键返回 `void` 在下一处炸／异常被 catch 引擎仍打 dump／语法错误无行号／`-assetdir` 无效／非 ASCII 路径不是问题）。
> 两条方法论：**「日志无 error」≠「功能正确」（必须逐屏导出 PNG 目视）**；**包装他人函数必须全程 try/catch 并回落原路径**。

1. **子层「画了看不见」＝ 忘了设 `visible = true`（原因已由源码定论）**：【实测】`add(new Layer(this, primaryLayer))` 建的子层上 `drawText`，画面全无、日志零报错；改画到 `primaryLayer` 上即正常。**【源码】**`Layer` 构造默认 `Visible = false`（`visual/LayerIntf.cpp:322-323`），**只有 primary 被引擎自动置可见**（`LayerManager::AttachPrimary()` 里 `SetVisible(true)`，`visual/LayerManager.cpp:124-138`）；父层遍历前先算可见子层数，为 0 就**只画自己**（`LayerIntf.cpp:5641-5650`），子层 `Draw` 开头还有 `if(!IsSeen()) return;`（`:5537`）。**官方示例正是显式设置的**（`imageviewer/startup.tjs:29-33` 的 `graphlayer.visible = true;`）。
   次因：只 `setImageSize` 而不同步 `Rect`，绘制区会按构造默认的 32×32 被裁（`LayerIntf.cpp:343-345,2353-2377`）→ 请配 `setSizeToImageSize()` 或直接设 `width`/`height`。
   **与父层 `type` 无关**，也**不需要**手调 `Layer.update()`（绘图函数内部已经调过）。详见《引擎工作原理》§6.2。
2. **给自动化用的 `.bat` 必须纯 ASCII 注释**：cmd 按本地代码页（中文机 = 936）读取 `.bat`，UTF-8 中文注释会被拆行，导致命令错乱（实测报 `'褰掓。妯″紡锛歬rkrz' 不是内部或外部命令`）。解决办法：直接调 exe，或把 `.bat` 注释写成英文。
3. **无人值守跑 GUI 会被"顺手一点"关掉**：窗口若恰在鼠标指针下弹出，Windows 会把随后的一次点击送给它（实测 `onClick 260,467 -> close()`，启动 3 秒即退出）。加"启动后 N 秒忽略输入"的静默期即可。
4. **`readencoding` 与脚本编码**：引擎按 exe 内嵌配置或命令行 `-readencoding=` 解释脚本；本次两作均为 `Shift_JIS`。自制时脚本与配置必须一致，否则中文注释/文本会乱码。
5. **路径**：实测含中文与空格的绝对路径（`E:\ZCode Workspace\Galgame\子代理工作区\…`）可正常启动；发行时仍建议纯 ASCII 路径（避开 260 字符与代码页问题）。
6. **`.cf` 里的值是字面转义**：文件内容就是 `datapath="\x24\x28…"` 这种字面文本，不是已解码的字节；改它要用同样写法。
7. **读可以、写要谨慎**：Applique 系变体**读得出来**（索引链 CONTINUE 是标准机制，见 §4 更正）；但「重打包后厂商加载器是否接受」**未实测**，且重打包还需复刻 4 字节残留、条目 `flags` 的 `0x80000000` 保护位、诱饵声明等。替换归档时应优先考虑「追加一个官方同样未签名的新 xp3」（§5），而不是重建原档。

8. **TJS2 没有 `for...in`**（本机 krkrz 1.4.0.8 实测：`for(var k in d)`、`for(k in d)`，对字典与对数组**全部**报「语法有误 （syntax error）」）→ 遍历字典请改成「并行的名字数组 + 索引循环」。这是**最容易写出、又最难从日志看出**的坑：错误只在 `execStorage` 时抛出一句**不带行号**的 `语法有误`。
9. **在函数内定义的函数（嵌套函数）取不到外层函数的参数与局部变量**（本机实测：在 `flowAutoDrive(w)` 内定义 `function once(...)`，其内引用 `w` 运行时报「未找到 Member w」）→ 回调里要用的数据**必须显式传参**，或挂在回调拿得到的对象上。
   **实测补充**：给 **`Timer` 对象**动态加成员（`t.tag = tag`）可用、不报错（demo 的驱动曾据此把上下文写在 Timer 上）；但对**窗口对象**读一个不存在的成员（`if(win.vt === void)`）会直接抛「未找到 Member vt」→ "把状态挂到窗口对象上"这条在本机走不通。
   **`this` 归属（已实证）**：`Timer` 回调用**窗口类的方法**注册时，回调里的 `this` **就是窗口**——证据：把保底退出改短后实机日志 `auto exit timer armed : 20 s` → `auto exit timer fired` → `quit (timeout 20s) : frames=4`，其中 `this.flowQuit(...)`/`this.redrawFrame()` 都成功执行。**不要**把 `this` 当成 Timer。
10. **Timer 必须被引用持有**，否则会被回收、回调永不触发（现象：日志里只打出了「已武装」那一行，之后再无任何回调日志——本次驱动脚本首版即如此）。官方示例把 Timer 存成窗口成员变量正是这个原因；本工作区的 demo 同样把 `exitTimer`/`uiTimer` 存成窗口成员（`startup.tjs:95-96`、`:134`、`:147`），实测 20 秒保底退出与每 5 秒重画都在跑（`frames=4`）。
11. **顶层 `var` 无提升**：初始化发生在脚本执行到那一行时。若在脚本前半段调用会用到"脚本末尾才初始化"的全局变量的函数，会报「未找到 Member」→ 这类状态应改成"回调期才读写的全局变量"，或把初始化提到调用点之前。
12. **改状态后要主动重画**：状态改变发生在重画之后时，画面会停在上一帧（实测两例：① 按键切到流程图后若不重画，窗口仍显示剧情视图；② 周期回调里若先重画再改状态，该帧同样不更新——把驱动挪到重画之前才抓到流程图画面）。
13. **语法错误定位手法（值得复用）**：TJS2 的语法错误只给「语法有误」+ 调用处 trace、**不带出错行号**。做法：把待查文件按"顶格 `function` 行"切成一串**前缀候选**，用一个临时 startup 在**一次运行内**逐个 `execStorage` 并 try/catch 打日志（按 `e.message` 是否含 `syntax`/`语法` 区分语法错误与运行时错误），即可把出错函数夹到单个函数体内——本次 907 行的文件一次运行就定位到行。
14. **窗口化下引擎传给 `onMouseDown`/`onMouseMove`/`onClick` 的是「客户区像素」，**不做 zoom 换算**（2026-10-01 源码定案 ＋ 运行期实测）**。链路：`environ/win32/TVPWindow.cpp`（`WM_LBUTTONDOWN` → `OnMouseDown( mbLeft, …, GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam) )`）→ `TTVPWindowForm::OnMouseDown` → **`TranslateWindowToDrawArea(x, y)`** → `tTVPOnMouseDownInputEvent` → 脚本侧事件；而 `TranslateWindowToDrawArea`（`environ/win32/WindowFormUnit.cpp`）**只在 `GetFullScreenMode()` 时减去 `FullScreenDestRect` 偏移，窗口化下是空操作** ⇒ 客户区像素**原样上抛**。
   ⇒ 若你用 `setInnerSize(1280,720)` ＋ `setZoom(2,3)` 把 1920×1080 画布缩进客户区，**脚本必须自己乘「画布宽 ÷ 客户区宽」才是画布坐标**（本工程 UI 层即 `x * primLayer.width / innerWidth`，因子实测 1.5，与 `uiMouseCanvasX(100) = 150` 一致）。
   **反过来说：「引擎给的就是画布坐标」这个假设是错的** —— 据此省掉换算会让**所有点击按 zoom 偏移**（元素越靠右下偏得越多，画面看着正常却点不中）。本工程曾长期把这条列为「未实测开口项」，2026-10-01 结案。
   附带：**`setZoom` 只影响绘制、不影响输入坐标**；全屏模式下坐标才是「减去 letterbox 偏移后的绘制区坐标」。

### 9.1 TJS2 语义级坑（2026-09-30 回写 · 源 `工程\…\UI组\UI组交接编程组.md` §五.1 · 本工程 UI 组实机实测）

> 本表 13 条：前 11 条由 UI 组在自研 TJS2 UI 工程中实机踩出（`ISSUE-20260919-11` 及后续各批），2026-09-30（`ISSUE-20260930-06`，用户裁定 12）回写至本 skill；**第 12/13 条为 2026-10-01 编程组补**（`ISSUE-20261001-05`）。**只加不动既有条目。**
> **去重说明**：其中 **⑧／⑨／⑩ 与上文第 13／1／10 条同源**（语法错误定位、子层 `visible` 默认 false、`Timer` 须持引用）——**合并去重、不另立条目**，见下表「备注」列。其余 8 条为本节新增。

| # | 坑 | 后果／表现 | 备注 |
| ---: | --- | --- | --- |
| 1 | **无 `String.lastIndexOf`** | `ui_flow.tjs` 曾因此抛异常 → 流程图全黑 + 异常外溢把对话框也打黑 | 新增 |
| 2 | **无全局 `parseInt`、无 `charCodeAt`** | 静默失败或抛异常 | 新增 |
| 3 | **`Array.load` 是实例方法**（静态调用抛「无效的 object context」，被 catch 后静默失败） | 存档**看似保存了其实读不回** | 新增 |
| 4 | 标识符**大小写敏感**，未定义标识符报的是**「未找到 Member」**（不是「未定义变量」） | 误导排错方向 | 新增（与第 9 条的「未找到 Member w」同族现象、成因不同：本条是通用语义） |
| 5 | Dictionary **读缺键返回 void、不抛** | `void → Object` 转换在**下一处**才炸（UI 组曾在 `ui_dialog.tjs:267` 炸） | 新增 |
| 6 | **异常即使被 catch，引擎仍打整段 dump** | 日志噪音大；缺文件要先 `isExistentStorage` | 新增 |
| 7 | `e.trace` 首帧是「调用者 + 调用行」；**抛错点看 `==== An exception occured at` 那一行** | 定位错文件 | 新增 |
| 8 | 语法错误**没有行号**，用「前缀夹逼法」（二分注释）定位 | —— | **去重：见上文第 13 条**（已含完整手法） |
| 9 | 子层 `visible` **默认 false**，只有 primary 自动置真 | 子层不显式置真就什么都不显示 | **去重：见上文第 1 条** |
| 10 | `Timer` **必须被引用持有**（局部变量会被回收、回调静默停止） | 打字机/动画莫名停住 | **去重：见上文第 10 条** |
| 11 | `-assetdir=<绝对路径>` **实测未生效** | 素材要靠项目根内的 `ui/` 或 `assets/ui/` | 新增 |
| 12 | **引擎事件是在「目标实例」上按成员名派发的** ⇒ 在**实例**上设同名成员即可**覆盖类方法**（`Window` 事件都能这样接管）。依据：`base/EventIntf.cpp` 的 `tTVPEvent::Deliver` → `Target->FuncCall(0, 事件名, …, Target)`；`visual/WindowIntf.cpp` 的 `tTJSNI_BaseWindow::OnMouseDown` 把 Target 设为**窗口实例** | 用它可**不改上游 .tjs 就禁用/改写某个引擎事件入口**（本工程 2026-10-01 以此禁掉右键呼出的 `sysicons` 浮层）。反之要注意**作用域**：改实例成员只影响该实例，改类方法才影响全部实例 | 新增（`ISSUE-20261001-05`，**运行期实证**：日志里 `onMouseDown` 走完类方法体 → 随即命中接管函数 → 屏未变） |
| 13 | **`Function` 类未注册 `call`/`apply`**（krkrz 1.4.0r2 的 `tjs2/tjsNative.cpp` 中 `tTJSNativeFunction` 只处理 `IsInstanceOf`） | **无法以指定 `this` 转发原方法** ⇒ 「先拦截、再回落原实现」不能按 JS 习惯写 `orig.call(this, …)`；只能改造**被调用的那个方法本身**（或把原引用存到成员/全局后用别的路径调用） | 新增（`ISSUE-20261001-05`，源码取证；**未做运行期反证**——若日后实测 `.call` 可用请订正本行） |

---

## 10. 复刻 Applique 的「流程图（フローチャート）」系统

### 10.1 结论
**可行，且已做出可运行演示** —— `.zcode\skills\kirikiri-unpackflowchart-demo\`（含 `README.md`、源码、`flow.xp3`），证据截图 `poc_flowchart_view.png`（流程图视图）与 `poc_flowchart_demo.png`（跳转后的剧情视图），2026-09-17 在 krkrz 1.4.0.8 上实机通过。要区分两种"复现"：

| 说法 | 结论 |
| --- | --- |
| **等效重做**（在自己做的游戏里实现同功能） | **已验证可行**（本 skill 的 demo 即实现） |
| **照抄他们的实现** | **两部都可行了**：《月影魅像》2026-09-20（`fe fe` 容器已解 → `main/scnchart*.tjs`、`scnchartdata.tjs` 节点数据、`scnchart_ui.tjs` 布局、`flowchart.func` 全部可读；`flowchart.pimg` 是 PSB v3，需 PSB 解析器取部件图）；**《交汇协奏曲》2026-09-21**（走的是**另一套**保护链 —— Wamsoft Hxv4，见 §11；`locale_cn.xp3` **11,012/11,012 条全部解出**，含 idx 77 流程图屏的 144 图层布局规格 + `scnchart.tjs`／`scnchart_ui.tjs`／`图表加载器`／72 件部件图） |

> ★ **本行曾在 2026-09-21 前写作「《交汇协奏曲》仍不可行（0 条 `fe fe`）」——那是把「非 `fe fe`」误当成「不可解」**：它用的是厂商 Hxv4 链而非引擎原生 `fe fe`，见 §11。**此后做流程图参照，别再去猜版式**：`scnchart_ui.tjs`（实现）+ `图表加载器`（几何/连线常量覆盖）+ `UI布局规格.md`（逐件 x/y/w/h）三份齐了，实现细节见 §10.5。

### 10.2 对方是怎么实现的（《月影魅像-解放之羽-》实测为主，个别为推断）

> 本表的**作品层明细**（文件字节数、flag 名单）以 `工程\月影魅像-解放之羽\作品skill\SKILL.md` §十一 为准；两处若不一致，**按作品 skill 处理**。

| 组成 | 实测证据（文件 / 字节数） |
| --- | --- |
| 逻辑与数据 | `main/scnchart.ks`(6,675)／`scnchart.tjs`(28,871)／**`scnchartdata.tjs`(83,785，节点数据最可能在此)**／`scnchartmacro.tjs`(5,337，命令注册)／`scnchart_scroll.tjs`(7,077)／**`scnchart_ui.tjs`(151,373，UI 实现)** —— 全部在 `fe fe` 容器内 |
| 界面定义 | `uipsd/flowchart.pimg`(187,586 B，**PSB v3**；内含 `フローチャート`／`スクロールバー`／`タブ`／`ボタン` 等日文 UI 词与 32 处 `TLG5.0` 部件图) ＋ `uipsd/flowchart.func`(8,533 B，`fe fe` 容器) |
| 状态模型 | `SetBranchFlags("<场景id>*select", 1\|2)` **12 个键**；`CheckBranchFlags(".sf.<主题>")` **6 个键**（蝶/炎/解放/木漏れ日/雲/月影）；`clear_<结局id>` **13 个**（与官方"全部 13 种结局"吻合）＋`clear_kurenai_ex3` |
| 上报机制 | **96/97 个 `.scn` 的字符串表都含 `scnchart` 一次**（唯一例外 `scn/コンプリート.txt.scn`，0 次）。**推断**为「每个场景向流程图登记一次」；**另一种可能**是对 `scnchart*.tjs/ks` 的**存储名引用**——该串所在的字符串池是「文件名 + 短记号」混排（如同一池内有 `rei_03.txt`／`ren`／`scnchart`／`se`／`se_w_tm01_01a`），无法只凭存在性定性。命令注册不在 DLL 里（`psbfile.dll`／`KAGParserEx.dll` 内 `scnchart`／`BranchFlags`／`flowchart` 均 0 命中） |
| 节点粒度 | 本作 = **场景文件**（`00_*` 21 个、`kurenai_*`、`k_*`、`m_*`、`rei_*` ＋ `*_endN`）；对照《交汇协奏曲》= **章节**，id 形如 `S0420-R01`／`0410-C13`（证据为 Steam 成就原文） |
| 疑似底图 | `rule/map*.png` **85 张，全部 1280×720**；`.scn` 字符串表里出现 `map18`／`map27`／`map504a` 等裸名（**推断**为路线图/流程图画面素材，未直接证实） |
| 官方描述 | 「本作设置了较为复杂的剧情锁，首次通关进入的结局是固定的」「随着通关新的结局，将在原有剧情中解锁新的选择分支」「您可以通过使用游戏主界面的『流程图』来实现快速跳转到新的分支选项」「游戏全部13种结局完成后，还需要通过『流程图』完成后日谈才算完整通关」 |

### 10.3 我们的等效实现（已跑通，可复用）

- **数据驱动**：两张 CSV 描述节点（id／显示名／路线／层级／坐标／剧情文本／入边 flag／跳转存储名+标签）与边（from／to／编号／成立条件 flag／置位 flag）——改表即改流程图。
- **三态着色**：已到达／已解锁可跳转／未解锁；另加三种连线态（已走／成立／未成立）。
- **跳转语义**：记录到达 → 置位该路径 flag → 解锁后继；未解锁节点点击无效并给出原因。
- **持久化**：到达集合／已走分支／flag 写入**引擎 datapath** 下的 `flow_state.txt`，重启自动读回（实测 1/14 → 2/14 → 4/14 逐次累积）。
- **与对方的接口对应（同构，非照抄）**：到达时调 `flowReachNode()`（对应对方各场景出现的 `scnchart` 串，其确切语义未确认）；跳转落点为表里的 `storage` + `label`（对应对方重载 `scn/<id>.txt.scn` 并跳 `<id>*start`，见 §4 的存储名证据）。
- **打包**：`python xp3pack.py pack game flow.xp3`；**松散模式与 XP3 模式都已实机验证**（XP3 模式下脚本与 CSV 均从归档内部成功加载）。

### 10.4 复刻时的坑
见 §9 第 **8–13** 条：`for...in` 不存在、嵌套函数不捕获外层变量、原生对象不能加成员、Timer 需持引用、`var` 无提升、切视图要重画，以及"语法错误无行号"的批量定位手法。**这些坑全部由实机验证发现，静态检查（括号配平类）查不出来。**

### 10.5 连线怎么画：参照作实现口径 + `layerExDraw.dll` 集成要点（2026-09-27，已实机跑通）

> 来源：`ISSUE-20260927-05`（《我们没有翅膀——格雷塔迦露德与柳木原》UI 组把流程图从单屏样板升级为真实数据驱动时，对参照作 `工程\交汇协奏曲\解包\flowchart\` 逐条复核 + 实机跑通）。

**(a) 参照作的连线实现口径**（**四处与二手描述的常见误读不同，逐条带出处**）

| 项 | 事实 | 出处 |
| --- | --- | --- |
| 布局主轴 | `_vertical=true` ⇒ `pos→y`（向下增大）、`vert→x`；**`step` 是沿主轴的行距**（不是「同行分叉步进」），**`vert` 才是同一行内兄弟节点的横向档距**（`y = vert×(vnumer×2−(vdenom−1)) \ 2`，只在数据给 `vdenom>0` 时生效） | `scnchart_ui.tjs:2073-2147`、`:470/:498/:491`、`:478-482` |
| 为什么不重叠 | 纵向 `step 150 > 节点高 65`；横向 `vert 375`（select 450）`> 节点宽 296` —— **不需要**「中心到中心 / 同类不邻接」之类的额外假设 | `图表加载器_未定名.txt:30,43-45` |
| 线宽 | 表里的「系数」**不等于成品宽**：成品 = 系数 × `e`（`e = 0.5×1.5 = 0.75`）。`normal`＝5×0.75＝**3.75**、`nojump`＝2.25、`rline`＝4.5、`hbox`＝10.5 | `图表加载器:54,56-64` |
| 端点与圆角 | **无端点内缩**（`padding = 0` 硬编码）；「圆角」来自 `lineJoin:LineJoinRound` + `startCap:LineCapRound`，**没有折角半径常量** | `scnchart_ui.tjs:2849,2971` |
| 路由形态 | 发货形态是**正交折线**（覆写 `_pathLinkVZ`/`_pathLinkVL` 均为 `drawLines`）；贝塞尔只在 `_vertical=false` 的 HZ 分支（本作不生效）。**VZ**＝源底边出→两节点中线横移→目标列下；**VL**（select/branch 这类 `spread`）＝源节点**朝目标那一侧的边中点**横出→目标列→竖直下 | `图表加载器:104-111` |
| 箭头 | **不是多边形，而是 GdiPlus 线端帽**（`*arrow = width:3, height:1.5, filled:true`，尺寸**随笔宽相乘**） | `图表加载器:72`、`scnchart_ui.tjs:2971-2990` |
| 迷你地图 | `minimapWidth = 3072` **只是章分隔刻度线的长度**（手写常量），**不是「虚拟总宽」**；真实映射＝`scale = 层高 / 全页总长`、`minscale = 1/20` 为下限（低于则抬到 1/20 并令 `imageHeight = ceil(scale×总长)`） | `图表加载器:41`、`scnchart_ui.tjs:2189-2240` |
| 文字 | 参数只有「字号（36/30/21）+ `maxline:2` + 居中」；**折行与禁则的实现拿不到**（`drawTextKinsokuRect` / `CustomDrawLayerText` 的函数体不在解包目录内，全包 grep 只有调用点）⇒ **自家文字排版必须用自己的引擎算法，不能照搬参照作** | `SystemConfig_未定名.txt:117-121` |
| 规模 | 参照作是**低密度**图表（章少），`step 150` 对 700+ 节点会得到十万像素级的单列总长 ⇒ **常量不可照搬**，行距/列距必须参数化并有规模自适应 | `侦察_参照作布局算法.md` §八 |

**(b) `layerExDraw.dll` 集成要点**

- 发行版**不带**该插件（`plugin/`、`plugin64/` 只有 7 个 dll，源码树无其源码）；上游 `github.com/wamsoft/layerExDraw`，**许可随 KiriKiri 本体**（允许二进制再分发，须随包附许可文本）。取件实测 sha256 `fe7760906b4ffa0ede8c840b76e8e5b8798131ae7cee4d05ccb13e138a8b5c7d`（32 位、VS2008 静态 CRT、只依赖 `KERNEL32/GDI32/ole32/gdiplus`、导出 `V2Link/V2Unlink`）。
- **能力（已实测）**：直线／斜线／粗折线（圆角连接＋圆端帽）／半透明多边形填充／抗锯齿／与 `Layer.drawText` **互不擦除**／透明层叠加；1920×1080 压力场景 736 节点框 + 735 折线 + 200 箭头 + 20 文字 ＝ **56 ms**。
- **四个集成坑**：
  1. **运行期落点是 `runtime\plugin\`**；而 `run_*.bat` 的 `if not exist "%RUN%\runtime" (xcopy …)` **只在运行目录不存在时复制** ⇒ **新增 dll 永远进不去**，必须补「每次强制刷新」。**症状具有欺骗性**：代码看着没问题、其它功能都正常，唯独连线不显示。
  2. **不要塞进 XP3**。
  3. **入库件放哪儿**：仓库根 `.gitignore` 常含全局 `*.dll`（且 `工具\`、`runtime\` 往往被整体忽略）⇒ 入库件要放在**加了作用域最小反忽略规则**的目录（本项目落 `UI组\krkr\plugin\` ＋ 一条 `!layerExDraw.dll`），并用 `git check-ignore -v` ＋ `git ls-files --others --exclude-standard` **双证**「普通 git add 会收进去」，再拿 `git status --ignored` 对照确认 `runtime\` 确实被忽略。
  4. **batch 语法坑**：在 `if (...)` 块内的 `echo` 行里写**裸右括号**（如 `echo (layerExDraw.dll)`）会**提前终止 `if` 块**、脚本崩掉（实测报「此时不应有 …」）——rem 注释里也最好别写裸括号。
- **必须优雅降级**：`Plugins.link` 包 `try/catch`；失败时**不画线** ＋ 一句可读日志（参照作原文「接続線は表示されません」，`scnchart_ui.tjs:2910`）＋ **不崩、不半画**。实测：删掉运行目录的 dll 后跑完整轮巡演 **0 EXCEPTION**、照常结束、像素断言「命中连线色 0 个」。
- **要两端逐像素一致，就别用端帽/自动箭头**：GDI+ 端帽尺寸随笔宽相乘，且「线端向前伸多少」在 GDI+ 与 canvas 两侧语义不同 ⇒ 改为按点集**画显式实心三角多边形**（顶点＝末点、沿末段方向后退 `L = 2.0×线宽` 为底边中点、底边半宽 `= 1.5×线宽`），两端同一公式即可对齐。
- **层序**：连线要画在**全屏压暗层／面板之上、节点之下**。若画在压暗层之下，会被半透明 rect 系统性改色（本项目实测被 `fc.dim`（黑 opacity 60）＋ `fc.scroll`（#5A6A8A opacity 40）压到原色的 **0.74–0.80**、**原色像素 0 个**），既与「两端逐像素一致」冲突，也与「节点坐在面板之上」的深度提示自相矛盾。
- **路由应由数据侧算好**：把「正交折线的点集」写进布局数据（本项目为屏 JSON 的顶层键 `links`），**两端只负责描线＋画箭头** —— 这样两端不可能各自路由而分叉。合法性另立闸门（点在画布内／相邻点正交／首末点锚在节点边／箭头末段够长／无重复点／色值可在色板溯源）。

---

## 11. Wamsoft Hxv4（CxdecV2 家族）保护链：**已解**（2026-09-21）

> 这是**另一套**保护，与 §7 的 `fe fe` 容器无关：`fe fe` 是引擎原生文本加密；Hxv4 是**厂商的整套保护链**，特征是「文件名被替换成占位名 + 内容层二次编码 + exe 内嵌 bres/BOOTSTRAP 资源」。

**识别特征**
1. 归档条目名被替换为 **`U+5000 + (id & 0x3fff)`** 的连续占位名（`倀 倁 倂…`）；
2. XP3 索引里有一个 **`Hxv4` 记录**（本工作区早先记为"`Hxv4` 总览记录"，其实是 Hxv4 的特殊索引标记）；
3. exe 内有 **`STARTUP.TJS` / `BOOTSTRAP` / `PLUGIN` / `salt`** 等 PE 资源（`BOOTSTRAP` 解密后内含一个 DLL）；
4. 内容层不是明文（PNG/OGG/PSB 魔数全无），adler32 与索引登记值不符。

**解密链（第三方静态工具的结论 + 本工作区实测）**
- 由 `STARTUP.TJS`（用 `startup_key` 解）里的 `_bootStrap(...)` 取 `bootstrap_key`；`BOOTSTRAP` 解出内嵌 DLL；
- DLL 配置表（`PARAMS/PUBKEY/UNIQUE/WARNING`）给出 `bootstrap_prefix` 与 `archive_unique_key`；
- exe 内 **bres salt**（8192 B，可由 "V2Link-before" 锚点自动定位）＋ 上述材料派生 **`hxv4_key`（32 B）/ `nonce0` / `nonce1`（各 24 B）**；
- 再由一个 .NET 小工具跑 DLL 的 **FilterManager/DripValue** 派生逻辑，产出 `drip_program.json`；
- 用它与 `xp3_inspect.py` 逐条解密（内容过滤按 `hxv4_key` 与条目 key 派生）→ **本作 11,012/11,012 条全部解出、adler32 全部通过**。

**文件名反查**：`filename_hash = Blake2s-256( UTF-16LE(名) + UTF-16LE("xp3hnp") )`（**必须带 extra 串 `xp3hnp`**、无 key）→ 拿候选名对表即可还原真名（本工作区据此还原出 `scnchart_ui.tjs`/`scnchart.tjs`/`scnchart.ks`/`macro.ks`/`default.tjs`/`popup.tjs`/`exroll.tjs`/`diffimage2.tjs` 等）。

**工具**：`工具\cxdec-hxv4\cxdec-hxv4-static-analysis-main\`（第三方开源；Python + 需 .NET 8 x86 运行其 `FilterManagerDerive`）。
```bash
python src/static_extract/static_xp3_recover.py --exe <exe> --work-dir <dir> --debug   # 恢复
python src/static_extract/static_xp3_recover.py --exe <exe> --xp3 <xp3> --verify       # 验证
python src/common/xp3_inspect.py extract-all <out> <xp3> --filter recovered --drip-program <dir>/drip_program.json
```
**本工作区实测参数**（《交汇协奏曲》，仅存档备查）：`startup_key=sgt3924qebe8crjrvsd8x3usds`、`bootstrap_prefix=HanaNoNoNiSakuUtakataNo/CopyrightApplique/AllRightsReserved.`（**复用了同社另一作的模板**）、`archive_unique_key={Ruri*Kyouka*Mirai*Touko*Aya*Mika}`（六位女主名）、`hxv4_key=bffb7b17…`（见 `工程\交汇协奏曲\解包flowchart\README.md`）。

**未验证**：**重打包 + `.sig` 校验链路**（改回游戏前必须实测）；`locale_cn.xp3`/`adult.xp3` 的提取（同法可行，未做）。

---

## 12. 结论速查（已验证 / 未验证 / 不适用）

| 项 | 状态 |
| --- | --- |
| krkrz 引擎可跑自制 TJS 工程（散装目录、自有 `.xp3` 两种模式） | **已验证**（1.4.0.8 实机 + 截图） |
| 自研 `xp3pack.py` 标准 XP3 打包/解包 round-trip | **已验证**（3 变体 md5 全一致，adler32 校验通过） |
| Applique 系自定义 XP3 变体的**读取**（头部/索引链/条目/名称/adler） | **已验证**（12 归档；标准实现经 CONTINUE 索引链即可读出） |
| 该变体的**重打包**（含复刻条目 `flags` 的 `0x80000000` 保护位） | **未实现 / 未实测** |
| `fe fe` 密文/压缩文本流容器的**解码**（引擎原生） | **已验证**（算法见 `TextStream.cpp:92-150`；工具 `fe_crypt.py`；《月影魅像》294 条全解） |
| 《月影魅像》PSB v3 `.scn` 内台词**提取**（UTF-8 明文） | **已验证可读**；**回写未实现** |
| 《交汇协奏曲》内容层解码（Wamsoft **Hxv4** 保护链） | **已验证解开**（2026-09-21：11,012/11,012 条解出、adler 全通过；见 §11） |
| `.sig` 校验器位置/公钥/失败行为 | **未确认**（只可能在加密 `.text`） |
| 运行时是否拒载未签名/非标准 xp3 | **未实测** |
| 改 exe / 打静态补丁 | **不适用**（加壳 + 入口在外壳段） |
| 用 KiriKiri Z 自建并（商用）发行游戏 | **许可上允许**（BSD 三条款式自定义许可，无商用限制） |
| 复刻 Applique 式「流程图」系统（等效重做） | **已验证**（可运行演示 + 实机截图，见 §10 与 `flowchart-demo\`） |
| 照抄 Applique 流程图的原实现（读其 `scnchart*`/`flowchart.func`） | **《月影魅像》可行**（`fe fe` 容器已解，2026-09-20）；**《交汇协奏曲》不可行**（内容层为另一套未知编码，连文件都定位不到） |
