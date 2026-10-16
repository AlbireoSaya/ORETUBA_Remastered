# 片尾说明（PSV 侧 · 7 支 ED 视频）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（PSV 侧 7 支 ED） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

> **范围**：PSV《我们没有翅膀～美咲线～》(PCSG00299) 的 7 支片尾 `.usm` → 本工程（krkrz 1.4.0.8）可用格式。源（只读）：`工程\我们没有翅膀PSV\解密\PCSG00299\media\data\`（**不是**同级 `…[NONPDRM]` 加密副本）。
> **机读清单**：`资源组\片尾\_raw_psv_ed.tsv`（LF／制表符／UTF-8 无 BOM）｜**生成脚本**：`资源组\工具\transcode_ending_psv.py`｜**可播性探针**：`资源组\工具\probe_mci_playable.ps1`。
> **产物**：`资源组\片尾\_src\psv_ed\`（7 `.mpg` ＋ 7 `.mp4` 预览 ＋ `_frames\` 21 张，共 529 MB，`.gitignore` 已排除、不入库）｜本次执行 2026-09-29。

## 一、7 支 ED 一览

| 源文件 | 归属 | 时长 | 帧数 | 源字节 | `mpg` 字节 | `mp4` 预览字节 |
| --- | --- | --- | --- | ---: | ---: | ---: |
| ED_ai.usm | 亚衣 | 2:11.00 | 3926 | 30,748,032 | 27,105,280 | 28,868,992 |
| ED_asuka.usm | 明日香 | 2:01.99 | 3656 | 28,771,072 | 25,374,720 | 26,630,576 |
| ED_hiyoko.usm | 日和子 | 3:45.02 | 6744 | 68,273,664 | 62,070,784 | 52,273,359 |
| ED_kobato.usm | 小鸠 | 4:25.00 | 7942 | 62,369,856 | 54,996,992 | 62,769,302 |
| ED_misaki.usm | 美咲 | 2:01.99 | 3656 | 27,313,312 | 23,916,544 | 25,017,828 |
| ED_miyako.usm | 京 | 2:01.99 | 3656 | 28,677,792 | 25,284,608 | 25,360,976 |
| ED_naru.usm | 凤鸣 | 2:11.00 | 3926 | 30,790,784 | 27,148,288 | 28,820,527 |

- **交付格式＝`<名小写>.mpg`**：视频流 `-c:v copy` **原样复制**（零画质损失）＋ 音轨 MPEG-1 Layer II **224 kbps**/48 kHz/立体声。`<名小写>.mp4`（H.264 main/AAC 160k）**仅供审阅、不作交付**；未启用 `-allow_skip_frames`（实测开它会丢 6 帧 ⇒ 预览件帧数对不上）。

## 二、`-c:v copy` 保真自证（7/7 通过）

方法：把**源**与**产物**的 MPEG-1 原始基本流（ES）各自解出，比 `md5` 与字节数；再叠加 ffprobe 的「视频编码 / 分辨率 / **解码计数**帧数」三项。

| 源 | 视频编码 | 分辨率 | 帧数（源=产物） | 视频 ES md5（源≡产物） | ES 字节 |
| --- | --- | --- | --- | --- | ---: |
| ED_ai | mpeg1video | 960x544 | 3926 = 3926 | `5d687f8123589f15f3977c42447c9a24` | 23,261,352 |
| ED_asuka | mpeg1video | 960x544 | 3656 = 3656 | `30b93ecf869b38afa6ad910eed82f247` | 21,797,909 |
| ED_hiyoko | mpeg1video | 960x544 | 6744 = 6744 | `6984513628058f1cb0f4f88d0610371c` | 55,415,529 |
| ED_kobato | mpeg1video | 960x544 | 7942 = 7942 | `db35b00676e1d598b41731118f22be63` | 47,227,448 |
| ED_misaki | mpeg1video | 960x544 | 3656 = 3656 | `3a592ccc4cc60a22df7fa7aecea6b355` | 20,344,164 |
| ED_miyako | mpeg1video | 960x544 | 3656 = 3656 | `07a70301106bd2b397849f20d1326210` | 21,705,811 |
| ED_naru | mpeg1video | 960x544 | 3926 = 3926 | `b0a563f0053ade9f43172f11a8688a18` | 23,304,175 |

**结论：7/7 视频 ES 逐字节一致 ⇒ `-c:v copy` 成立**（不是"看起来像"）；mp4 预览件帧数亦逐支与源一致。复跑确定性：`--force` 全量重跑三次，14 个视频 ＋ 21 张 PNG 的 md5 全部不变。
封装层有一处**有据改动**：ffmpeg 的 mpeg(PS) 复用器默认 `-preload 500000µs` 会让首帧 PTS≈0.51 s（播放开头空 0.5 s），故加 `-preload 0`；改后音频起点 0、视频首帧 +0.010 s（AV 差 10 ms）。**该选项只动封装时间基准，视频 ES 仍逐字节相同**（即上表）。

## 三、抽帧（21 张，供人工核对 STAFF 与画质）

落 `_src\psv_ed\_frames\`，位置＝按**帧序号**取 5% / 50% / 95%（`idx = round(pct × 帧数)`，不用按时间 seek）：

```bash
ffmpeg -i <src.usm> -vf "select=eq(n,<idx>)" -fps_mode passthrough -frames:v 1 _frames/<名小写>_f<pct>.png
```

逐支索引（@声明帧率 30 fps）：亚衣/凤鸣 `196/1963/3730`；明日香/美咲/京 `183/1828/3473`；日和子 `337/3372/6407`；小鸠 `397/3971/7545`。
7 支的 50% 帧已**逐张目视核对**：均为「角色 CG／背景 ＋ 右侧烘焙日文 STAFF」⇒ 清单 `含图片化文字=是`、`文字语言=日语` 系实证（非沿用派单结论）。

## 四、风险：krkrz 实机播放**未验证**（**待编程组实机确认**）

- 播放路径＝**系统 DirectShow**：krkrz 1.4.0r2 源码 `movie/win32/dsoverlay.cpp:106`、`dslayerd.cpp:127` 均调 `IGraphBuilder::Render`（`dsmovie.h:53` 持 `IGraphBuilder`）。
- 本机（Win10 22621）注册表实测 MPEG-1 链路齐备：`MPEG-I Stream Splitter`→`quartz.dll`、`MPEG Audio Codec`→`quartz.dll`、`Microsoft DTV-DVD Video Decoder`→`msmpeg2vdec.dll`、`MPEG-2 Splitter`→`mpg2splt.ax`；`.mpg` 关联 `video/mpeg`。
- MCI `mpegvideo` 设备实测（`mciqtz32.dll`，与 krkrz **同一个** `IGraphBuilder::RenderFile`）：**7/7 `.mpg` OPEN-OK 且 `mode=playing`**（`lengthMs` 与源时长吻合）；**7/7 源 `ED_*.usm` OPEN-FAIL（rc=277）** ⇒ 转码必要，且产物能被该链路建图并推进播放。
- **两点未验证**：① 未在 krkrz 实机里跑过；② `960×544` 超出 MPEG-1 的 *constrained parameters*（常记 ≤768×576 / ≤396 宏块）——基本流语法合法但非常规，系统解码器实测能吃，仍须实机确认。
- **退路**（若实机被拒）：转 *constrained* 尺寸的 MPEG-1（**有损**：重编码＋缩分辨率）或改 H.264（**有损**，且 Win7 需系统 H.264 解码器）；二者都不如现在的零损失 `.mpg`。

## 五、复跑命令

```bash
# 转码 + 清单（幂等；加 --force 强制重做）
python "工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\工具\transcode_ending_psv.py"
# 负向自证（4 项，必须全 PASS；退出码 0）
python "工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\工具\transcode_ending_psv.py" --self-test
# DirectShow 可播性探针（7/7 mpg OPEN-OK ＋ 源 usm OPEN-FAIL ⇒ 退出码 0）
powershell -NoProfile -ExecutionPolicy Bypass -File "工程\我们没有翅膀——格雷塔迦露德与柳木原\资源组\工具\probe_mci_playable.ps1"
```

## 六、未决项

1. **krkrz 实机播放未验证**（§四）——待编程组接入后确认；须登记进工程记录。
2. `ED_misaki` 片头约 `0–13.5 s` 近乎纯色：按「内容特征（片头淡入）」记录，不改写、不另查；同帧数（3,656）同时长（2:01.99）的 `ED_asuka`/`ED_miyako` 首帧即有内容 ⇒ **是否为源 dump 异常未经证实**。
3. mpg 音轨 MP2 **224 kbps**（源 ADX 432 kbps，有损）；主代理 2026-09-29 裁决保留，如需更高保真改脚本常量后重跑。
4. 本模块未派独立 reviewer（编辑器类模块，走主代理一审）。

## 附：一次写入违规的如实记录（供工程记录引用）

- **时间/文件**：2026-09-29 22:48，首次比对视频 ES 的测试命令把 `_t_src.es`、`_t_out.es`（各 20,344,164 B）**误写进只读源目录** `工程\我们没有翅膀PSV\解密\PCSG00299\media\data\`（输出用了相对路径，而 cwd 恰在该目录）。
- **处置**：已自行 `rm` 删除（同日 23:10）。**复核结论**：该目录恢复为原 **12 个文件**（ED×7 ＋ OP00–03 ＋ Poem），**大小与 mtime 全未变**（仍为 2026-09-17 05:06），仅目录自身 mtime 因增删而变、对内容无影响。
- **后续加固**：脚本内一切输出路径由 `guard_out()` 以 `realpath` 归一后硬校验必须落在工作树内，越界即 FATAL；负向自证 B 例专测该场景（`<worktree>/..` 必须被拦住）。
