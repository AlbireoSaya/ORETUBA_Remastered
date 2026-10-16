---
name: psvita-unpack
description: PlayStation Vita 游戏（NoNpDrm dump）的 PFS 解密与 CRIWARE（CPK/AWB/USM/ADX/HCA）资源提取通用管线。适用于任何用 CRIWARE 中间件的 PS Vita/PS3 galgame 的解包与素材提取。覆盖 NoNpDrm 假授权结构（klicensee 在 work.bin 偏移 0x50）、psvpfsparser 纯 PC 解密、PFS 算法（AES-CBC/逐扇区 tweak / 离线 F00D 等价）、熵扫描判定 dump 是否加密、CPK 内嵌 AWB 的识别、ADX 与 HCA 的 magic 判型与 ffmpeg 转码、USM 解复用，以及"cricodecs 不支持非 ASCII 路径"等实测坑。配套通用翻译规范 galgame-translation 使用；具体作品的专名、脚本格式与裁决见各作品专属 skill。
---

# PS Vita（NoNpDrm）解包与 CRIWARE 资源提取管线（psvita-unpack）

> 读者：执行 PS Vita 游戏解包 / 素材提取 / 汉化前置工作的代理。
> 本 skill 沉淀自《我们没有翅膀》PS Vita 版（PCSG00299，2026-09-17 全流程实测通过）。
> 与 AGENTS.md 冲突时以 AGENTS.md 为准。作品专属坐标与裁决一律在各作品 `作品skill\`，本文件只写跨作品成立的方法。
> 参考实现：`工程\我们没有翅膀PSV\工具\`（`resolve_asset_ids.py` / `collect_misaki_assets.py` / `extract_misaki_assets.py`）、`工具\美咲线过程脚本\`（音频探测与提取）。

---

## 一、识别特征：这是不是一份 PS Vita app？

```
<anything>\app\<TITLEID>\
├─ eboot.bin               可执行（零售为加密 SELF）
├─ icon.png / icon_empty.png
├─ sce_module\             libc/libfios2/libult/libface/libsmart .suprx
├─ sce_sys\                param.sfo、icon0.png、pic0.png、livearea\、manual\、package\、trophy\
├─ sce_pfs\                files.db、unicv.db（或 icv.db 目录）、pflist   ← **PFS 元数据**
└─ media\ 或 data\         游戏资源
```

要点：
- **`sce_pfs\` 的存在**说明该 app 本身就是一个 PFS 容器；`files.db`（magic `SCENGPFS`）与 `unicv.db`（magic `SCEIRODB`）是它的索引。
- `sce_sys\param.sfo` 给出 `TITLE` / `TITLE_ID` / `CONTENT_ID` / `APP_VER` / SDK 版本，**它是明文的**（SFO 结构：magic `\0PSF`，key 表 + data 表）。日文标题是 **UTF-16LE**（fmt `0x0204`）。
- 资源若为 CRIWARE 系，会出现 `*.cpk`、`*.awb`、`*.usm`，以及启动 logo 里的 `criware*.png`。

## 二、第一步永远是「判定 dump 是否已解密」——熵扫描

**不要假设 NoNpDrm 就是明文。** NoNpDrm 只伪造 license，**不解密任何文件**（其 README 原文："Allows sharing PFS encrypted content (unmodified non decrypted games)"、"This software WILL NOT Work with PFS decrypted content"）。

判定方法（30 行 Python 足够）：

```
对每个文件取前 64 KB 算香农熵：
  7.9 ~ 8.0  → 密文（或本来就是高压缩数据）
  < 7.5      → 明文
再做两个"幻数检验"破除误判：
  · PNG 必须含 89 50 4E 47 0D 0A 1A 0A
  · CPK 必须含 43 50 4B 20（"CPK "）于偏移 0
  · AWB 若为 AFS2 则含 41 46 53 32
```

**控制实验（区分"加密"与"数据本来就压缩"）**：找两个内容相同的文件（PS Vita 包里 `icon.png` 与 `icon_empty.png` 常常逐字节相同）——若同明文得同密文，说明密钥与文件内容无关；再比较两个**不同** PNG 的**密文头 16 字节**（它们的明文头必然相同）：若各不相同，则是**逐文件/逐扇区密钥**，排除"全局流密钥"。本作实测即此形态（51/60 文件熵 7.9–8.0、全部 PNG 无幻数、23 个 PNG 密文头互不相同）。

**明文与密文的分界**（本作实测）：`param.sfo`、`clearsign`、`keystone`、`sce_sys\package\*.bin`、`sce_pfs\{files.db,unicv.db,pflist}` 明文；其余全部密文。**PFS 元数据是明文**，所以即使内容加密，文件清单仍可读。

## 三、拿密钥：NoNpDrm 假授权里的 klicensee

若 `sce_sys\package\work.bin` 存在且其**偏移 0x08（小端 u64）== `0x0123456789ABCDEF`**（NoNpDrm 的 `FAKE_AID`），则这是 NoNpDrm 假授权，结构为：

| 偏移 | 内容 |
| --- | --- |
| 0x00 | `00 01 00 01 00 01 00 02`（版本/类型字段） |
| 0x08 | **FAKE_AID `EF CD AB 89 67 45 23 01`** |
| 0x0C | Content ID（ASCII，如 `JP0745-PCSG00299_00-ORETSUBA0000VITA`） |
| **0x50** | **klicensee：16 字节明文密钥** ← 就是它 |

提取：`work.bin` 偏移 0x50 起 16 字节，转成 32 位 hex 字符串。

> 若 `work.bin` 的 aid **不是** FAKE_AID（即原生 PSN license），则 klicensee 需结合该账号的 `act.dat` / ConsoleId 派生，**纯 PC 离线基本不可行**，需真机侧 NoNpDrm 重新导出。

## 四、解密：psvpfsparser（纯 PC，无需真机）

**工具**（用官方预编译，别自己编译——上游需要 libtomcrypt + libcurl + boost + VS）：

```
https://github.com/motoharu-gosuto/psvpfstools/releases/download/v2.0/release_win64_7.zip
（426,259 B，内含 psvpfsparser.exe 629,760 B + libcurl.dll，须同目录）
```

**命令**：

```bash
psvpfsparser.exe -i "<app目录，如 …\app\PCSG00299>" -o "<输出目录>" \
  -k <klicensee 的 32 位 hex> -f http://cma.henkaku.xyz
```

- `-i` 是**含 `sce_pfs\` 的 app 目录**（不是 .pkg），`-o` 是输出目录，目录结构按 `files.db` 重建。
- `-k` 与 `-z`（zRIF）二选一；都不给则回落读 `sce_sys\sealedkey`。
- **`-f` 与 `-c` 必须且只能给一个**：`-f` 是 F00D 密钥变换服务（需联网，`http://cma.henkaku.xyz` 实测 2026-09 存活），`-c` 是缓存文件（首次成功后把控制台打印的 cache 存下来，以后完全离线）。
- 输出目录**不要指向游戏原始目录**（工作区铁律：原始文件只读）。

**验证通过标志（关键）**：末行打印 **`keystone: matched retail hmac`**。这是引擎对 dump 内 `sce_sys\keystone` 做的 HMAC 校验，**通过即为密码学级别的正确性证明**，远强于"看起来像明文"。

**补充校验**：解密后逐文件比对幻数（PNG `89504e47` / CPK `43504b20` / AFS2 `41465332` / SELF `53434500`），并复测熵——本作实测 CG.cpk 8.00→4.77、SCRIPT.cpk 8.00→5.41。

### 若要自己用 Python 重实现（无预编译可用时）

规格（照 `motoharu-gosuto/psvpfstools` 与 `Vita3K/psvpfsparser` fork 源码，两者 `PfsKeyGenerator.cpp`/`PfsKeys.cpp`/`LocalKeys.cpp`/`PfsCryptEngine*.cpp` 逐字节相同）：

- `files_salt` 在 **`files.db` 偏移 0x1C**（LE u32；version ≥ 4 才非 0）。
- `icv_salt`：unicv 模式 = 该文件 SCEIFTBL 记录所在**页号**；icv.db 模式 = icv 文件名按 hex 解析。
- gamedata/unicv 走 KEYGEN 分支时 **`dec_key = klicensee` 原样**；`tweak_enc_key = HMAC-SHA1(hmac_key0, LE32(files_salt)‖LE32(icv_salt))[0:16]`（`files_salt==0` 时只放 icv_salt）。
- unicv 用 **AES-128-CBC**，**逐扇区**换 IV：`tweak = LE64(扇区字节偏移)`（高 8 字节清零）**XOR tweak_mask**；尾部不足 16 字节用 `AES-ECB-Encrypt(最后一个密文块)` XOR 处理（CBC-CTS）。**扇区大小**读 SCEIFTBL 头偏移 **0x18**（期望 `0x8000`）。完整签名页 = `binTreeNumMaxAvail`（=0x32）个扇区，`sector_base` 每页 +0x32。
- icv 模式用 **AES-XTS**（key1=dec_key, key2=tweak_enc_key，**不 XOR tweak_mask**）。
- **离线 F00D 等价**（省掉联网）：`drv_key = AES-128-ECB-Decrypt(klicensee, key = contract_key0 = E12213B48016B0E99AB81F8EC02AD4A2)`，`key_id` 必须为 0。`drv_key` 只用于 secret 派生与 `*WithKeygen*` 调用；**文件数据解密用的仍是 klicensee**。
- 公开常量：`hmac_key0 = E462258B1F3121560745DB62B1436723D2BF80FE`、`hmac_key1 = AFE656BB3C17256A3C809F6E9BF19FDD5A388543`、`iv0 = 74D20CC39881C213EE770B1010E4E4BEA7`、`PFS_EncKey = 00298CDF4428E72C8785DAE0923C60BD`。
- 跳解密条件：`fs_attr`（来自 files.db 每页偏移 `0x298 + i*16 + 4` 的 u16）含 `ATTR_NENC 0x4000`（不解密，直接复制）或 `ATTR_DIR 0x8000`（目录）；`ATTR_NICV 0x2000` 表示不校验 ICV。
- 页号 ↔ 偏移的怪异约定（照抄）：`page2off(p) = p*pageSize + pageSize`，`off2page(o) = (o - pageSize)/pageSize`。

## 五、CRIWARE 资源提取

### 5.1 CPK 归档 —— `cricodecs`（Python，首选）

```bash
python -m pip install --target "<工作区>/工具/pylibs" cricodecs   # 有 cp314 win_amd64 wheel
```

```python
import sys; sys.path.insert(0, r'<工作区>\工具\pylibs')
from cricodecs import cpk as C
os.chdir(media_dir)                 # ← 见坑 1
c = C.load('SCRIPT.cpk')            # 注意：没有 len()，用 c.file_count
for i, f in enumerate(c.files):
    print(f.filename, f.file_size, f.is_compressed)
    data = c.file_bytes(i)          # ⚠️ 必须传「列表下标 i」，不能传 f.id —— 见坑 4
    assert len(data) == f.file_size  # 长度不符即说明取错了条目，务必断言
```
也支持命令行：`cricodecs <in.cpk> [--list] [--json] [-o OUT] [--raw]`，以及 `--build/--add/--replace/--compress`（**回封 CPK 的可行性在本作未实测**）。

**典型 CPK 内部布局**：条目多为**未压缩明文**（`is_compressed=False`），且**文件名保留**。内部文件若是 CRILAYLA 压缩会由库自动解压；若 CPK 启用了 CPK 级 AES FileCrypto，则现有工具都解不开（需 16 字节 `FileCryptoKey`，通常硬编码在 exe 里）——**先 `--list` 试，能列名基本就是没启用**。

### 5.2 ⚠️ `*.AWB` 可能不是 AWB

**本作实测**：`VOICE.AWB` 是真正的 **AFS2/AWB** 容器（`41 46 53 32`），而 `BGM.AWB` / `SE.AWB` / `SystemSE.AWB` **其实是 CPK 容器**（头就是 `CPK `）——扩展名骗人。

**一律按 magic 判型，不要按扩展名**：
```
41 46 53 32            → AFS2/AWB
43 50 4B 20  ("CPK ")  → CPK（用 §5.1 打开，内部才是音频）
48 43 41 00  ("HCA\0") → 裸 HCA
80 00 / 80 xx          → CRI ADX
```
**CPK 型"音频归档"里的条目往往没有文件名**（本作 BGM/SE 全为空名），只能**按索引**取——索引与脚本里的 `:BGM N` / `:SE N` 直接对应（本作 BGM 0..87↔96 条目、SE 0..700↔701 条目完全吻合）。

**混合容器**：同一个 SE 归档里会混有 ADX 与 HCA（本作 701 条 = **698 ADX + 3 HCA**），**必须逐条读 magic 判型**，不要假定统一。

### 5.3 音频转码 —— ffmpeg（本机自带 ADX 与 HCA 解码器）

```bash
ffmpeg -hide_banner -v error -y -i raw.hca -map_metadata -1 -vn -c:a libvorbis -q:a 2 out.ogg
```
- **先确认本机 ffmpeg 是否支持**：`ffmpeg -decoders | grep -E 'hca|adx'`、`ffmpeg -demuxers | grep hca`。本机（`N-123888`，2026-04）**两个都有**；若你的构建没有，则 HCA 需改用 `cricodecs` 解码。
- 语音用 `-q:a 2`、BGM/SE 用 `-q:a 3` 即可；**Opus 也可**（Ren'Py 支持 Opus/Ogg/MP3/FLAC/WAV，但**不支持 ADX/HCA**）。
- 采样率参考：本作语音 **HCA 22050 Hz 单声道**、BGM/SE **ADX 48000 Hz 立体声**。
- 验证：`ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -show_entries format=duration -of json out.ogg`，并对**全部**产物跑一遍统计失败数（本作 1,837/1,837 通过、零零字节）。

### 5.4 USM 影片

`.usm`（CRI Sofdec2）本质是 MPEG-PS 式容器，**ffmpeg 一般能直读**：
```bash
ffmpeg -y -i ED_misaki.usm -c:v libopenh264 -b:v 1600k -c:a aac -b:a 192k ED_misaki.mp4
```
- 本机 ffmpeg 是 **lgpl 构建（`--disable-libx264`）**，`-c:v libx264` 会报 unknown encoder → 用 `libopenh264` 或 `mpeg4`。
- 目标若是 Ren'Py：它**不支持 H.264 与 AAC**，需再转 **WebM/VP9(或VP8)+Vorbis/Opus**。

## 六、已知坑清单（全部为实测）

1. **`cricodecs` 的 C++ 读取器不支持非 ASCII 路径** —— 传含中文的路径会报 `I/O reader failed: could not open file`。**必须先 `os.chdir()` 到目录，再传纯文件名**（`C.load('CG.cpk')`）。Python 侧自己的 `open()` 不受影响。
2. **Python 库别装进系统 Python**（工作区铁律 3）：用 `pip install --target 工具/pylibs`，再 `sys.path.insert` 或 `PYTHONPATH`。
3. **NoNpDrm ≠ 已解密**（见 §二）。
4. **`cricodecs.Cpk.file_bytes()` 要传「列表下标」，不能传 `CpkEntry.id`** —— 这两个值在很多 CPK 里**不相等**（`id` 是 TOC 序号）。传 `id` 会**静默取到别的条目**（本作实测：CG.cpk 946/946 全错、CHR.cpk 1040/1333 错、SystemData.cpk 165/182 错、ETC.cpk 122/124 错；SCRIPT.cpk 恰好全对，所以不易发现）。**正确写法**：
   ```python
   c = C.load('CG.cpk')
   for i, f in enumerate(c.files):
       data = c.file_bytes(i)          # ← 下标，不是 f.id
       assert len(data) == f.file_size
   ```
   另：`CpkEntry.file_offset` 是**绝对偏移**，切原始字节直接用 `open(cpk,'rb').read()[f.file_offset : f.file_offset+f.file_size]` 即可，**不要再加 `content_offset`**（加了会错位）。**这个坑会让"按文件名提取"静默串位**，务必断言 `len(data) == f.file_size`。
5. **`-i` 不是 .pkg**；`-o` 绝不能指向原始目录。
6. **扩展名不可信**（见 §5.2）。
7. **同一音频容器可能混编**（ADX + HCA），逐条判型。
8. **Win7 不在 Vita3K 支持范围**（官方 FAQ：`OS: Windows 8/10/11`，需 OpenGL 4.4 / 推荐 Vulkan）——涉及"跑起来验证"的任务要先确认目标机。
9. **`eboot.bin` 解 PFS 后仍是加密 SELF**（头 `53434500`，无任何可读字符串）。要拿明文 ELF 需另做 SELF 解密：Vita3K 有"用该 app 的 license key(klic) 解密 eboot.bin/.self/.suprx"的实现（PR #3499 + `vita3k/packages/src/sce_utils.cpp` 的 `decrypt_fself(fself, klic)`）；纯 PC 无"无需 klic 的通用零售 SELF 解密器"。
10. **icv.db（存档/addcont）走 XTS，gamedata 走 CBC**，两者 tweak 处理不同（前者**不** XOR mask）——混用会全解出乱码。

## 七、验证清单（交付前逐项做）

- [ ] 熵扫描确认解密生效（密文文件熵应显著下降）
- [ ] 幻数抽查（PNG / CPK / AFS2 / SELF）
- [ ] `keystone: matched retail hmac` 出现在解密日志里
- [ ] 原 dump 目录 mtime 未变（未被写入）
- [ ] 归档条目数 vs 脚本引用编号范围是否吻合（用于判断索引式寻址）
- [ ] 音频产物 100% 可被 ffprobe 识别、零字节文件为 0、抽 3 个看编解码/采样率/声道/时长
- [ ] 抽 1 张 CG 用 PIL 打开并肉眼确认画面完整（不要只看文件大小）
- [ ] 所有产物落在工作区内；中间产物收尾清理

## 八、适用 / 不适用

| 适用 | 不适用 |
| --- | --- |
| NoNpDrm 或 FAGDec 等**未加密或已解密**的 PS Vita app 目录 | Vitamin dump（NoNpDrm README 明确不兼容） |
| 用 CRIWARE（CPK/AWB/USM/ADX/HCA）的 PS Vita / PS3 / Switch 系作品（CPK 与音频部分通用） | 需要真机才能做的步骤：VitaShell 导出、FAGDec、NoNpDrm 插件本体、psvimgtools 的 backup key |
| 想要"把资源抽出来做移植/重做"的场景 | 想"汉化 PSV 原版"时——还须额外解决 `eboot.bin` 的 SELF 解密与文字渲染路径 |

## 九、附：本作遇到过的"文本型脚本引擎"（供同类作品参考）

PCSG00299 的内层脚本是 **Shift-JIS 纯文本 DSL**（`[Section]{ :Key value }`、`:Tasktype "…"` 共 55 种），**不是字节码**。这类"文本型 ADV 引擎"的通用处理原则：

- **文本字段是自由文本，通常无字节长度约束**（与 Lucifen 的硬依赖相反）——但仍需实测确认。
- **资源编号往往是"场景内局部编号"**，不能当归档索引用；而构建工具常把真实资源名**烘焙在注释里**（`// NAME`、`<<NAME>>`、`置換しました<<NAME>>`），**按注释名解析归档文件名**才是可靠路径（本作覆盖率 99.4%）。
- **全局数据表（名字表、影片表、旗标表、场景号表）通常与脚本同放在脚本归档里**——不要因为"名字出现在注释里"就断定"表在 exe 内"。**务必把归档内的每个数据文件都打开看一眼**（本作就因此在 `adv.txt` 里找到了 362 条名字表，纠正了此前"名字表在 eboot"的误判）。
