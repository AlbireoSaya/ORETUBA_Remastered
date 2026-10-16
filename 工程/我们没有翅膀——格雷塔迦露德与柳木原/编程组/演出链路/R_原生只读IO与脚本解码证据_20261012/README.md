# R 原生只读 IO 与脚本解码证据（ISSUE-20261011-02）

## 范围与产物

本稿为阶段技术依据说明，供 root 进行行政审查与应用；产物暂存 `ISSUE-20261011-02/r-resource-payload-01/README.md`，由 root 精确应用到编程组/演出链路及 R 作品 skill 增量。行政审查状态由 root 回执记录，避免本 README 长期停留在“未复核、未入库”的错误状态。

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