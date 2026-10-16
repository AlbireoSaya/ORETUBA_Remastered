# R版原生分配器与归档工厂阶段交付说明

- 目标：ISSUE-20261011-02，R版原生分配器与归档工厂阶段，2026-10-12。
- 行政边界：全部写入工作区、原始只读；editor 不操作 Git、不假报测试、不回退他人改动。root 批次复核后在 issue 提交并合并 main。
- 本文件只作技术说明，不改旧文，不声明超出证据范围。

## 目录与工具
- 工具正式目录：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/
- 新增：lucifen_host_memory.py、lucifen_guest_memory_bridge.py、lucifen_host_version.py
- 复用：lucifen_readonly_io_bridge.py、lucifen_readonly_io_guest.py、lucifen_host_string_bridge.py、lucifen_host_path_bridge.py、lucifen_vm_micro.py、lucifen_thiscall_probe.py、lucifen_cdecl_probe.py
- 证据正式目录：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生分配器与归档工厂证据_20261012/
- 证据内容：与初验 JSON 逐项一致的复验数据、verify-host-memory.txt、verify-complete-reader.txt、verify-native-factory.txt、verify-guest-memory.txt、README.md、本批复核覆盖清单。
- 原始备份只读：备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE
- EXE SHA256：b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33
- SCRIPT 备份只读；解包源：工程/我们没有翅膀R/语料/R版SCRIPT/
- 原作 EXE/DLL 仅作为 CPU 仿真输入，未作为 Windows 进程/DLL 装载。

## 复验用法
- recipe 文本不能直接当 py 插件执行；从 E:/ZCode Workspace/Galgame 运行。
- 示例：Get-Content -Raw -Encoding utf8 -LiteralPath '证据完整路径/verify-native-factory.txt' | python -X utf8 -B -
- 命令使用 Path.cwd，所以必须从 E:/ZCode Workspace/Galgame 运行。
- 前置：原始安装介质存在；成熟工具和 Unicorn 已安装。
- 完整 recipe 仅引用正式工具，并新建各自临时 formal-01 目录。
- 同名目录已存在时会失败；保留历史，root 选择新后缀再复验，不覆盖。

## HostMemory 事实
- 实际 ctypes host64 调用 HeapCreate/HeapAlloc/HeapFree/HeapDestroy/GlobalAlloc/GlobalFree。
- 所有宿主指针完整 64 位；仅登记成功分配和对应 owner。
- 政策：单块 1..1MiB；固定 GlobalAlloc flags 0；Heap options 0/1；alloc flags 0/8。
- close_all 真实 free 再 destroy；失败保留登记并报告。
- HeapAlloc 不保证 SetLastError；不把随机 last error 写成结果。
- 官方接口：微软 HeapAlloc、HeapCreate、GetVersionExA、GlobalAlloc 文档。

## GuestMemoryBlocks 事实
- 为注册真 host 块建立独立 guest u32 页镜像。
- 每块前后 128 字节 A5 保护。
- sync 时真实 host memmove 和读回校验。
- 不是共享虚拟地址，也不是每条指令实时同步。
- 不截断 host 指针。
- 单调 arena 默认 07000000..17000000，不复用已释放 guest 地址。
- unmap 不自动宿主 free，由明确 API 调用释放。

## 版本与字符串桥
- host_version_ex_a 实际 GetVersionExA 与 148 字节 OSVERSIONINFOA guards。
- 现宿主返回 10.0.22621 平台 2。
- 该返回仅来自 CPython 宿主 manifest 下的系统 API。
- 未证明原作 manifest/Win7/legacy SBH。
- host_upper_ascii_z 实际 CharUpperA。
- 输入 0..4095 字节的非 NUL ASCII，实际指针 >=0x10000。
- 验证返回值/保护/NUL/实际输出。
- 不支持通用 CP932。

## 初验与正式阶段边界
- root 初验：16 真实 host 内存 fixtures、37 非法边界/owner 拒绝。
- root 初验：4 真实 CharUpperA + 5 非法拒绝。
- overlay guards、重复 bind、unmap、arena 已在正式阶段实际验证并有 JSON：guest-memory-fixtures.json 记录 8 成功/18 拒绝，包含 4 项实际 CharUpperA 与 5 项非法输入拒绝，其余为镜像/guard/arena 验证。
- 正式 6 份主流程 JSON 与初验逐项相同，另新增 guest fixture 1 份；证据限定当前 host64/cache0/预打开只读句柄/aux 输入。

## 原 CRT 分配路径
- 50A11A([1]) 真实 HeapCreate+GetVersionExA 选 568408 mode1。
- heap568404 为 controlled handle token；不是 root 手填 heapmode。
- 原 malloc 50577F→507517→507543 至实际 HeapAlloc。
- 原 free 44B6B0→50658E 至 HeapFree。
- malloc 16 字节取整。
- 该路径支持实际现宿主 mode1；其他 mode 尚未验证。

## 完整读取器
- 491430→4912A0 seek→491E20 GlobalAlloc。
- 压缩项：CRT HeapAlloc 和 ReadFile，再 4B0C80 LZSS+原内容还原+free。
- 未压缩项：直接 ReadFile，返回 0。
- 491E50 实际 GlobalFree 并清空结果 pointer。
- 全部 446 SCRIPT=418 TOB+23 SOB+5 其他；444 压缩，2 decoded_len0 未压缩按 stored_size 归一。
- 10,515,356 bytes 逐文件 exact 源一致。
- 初验 preallocated ctor/table 是分阶段定位；随后 factory 复验已消除此限制。
- 社区 LZSS 不是 SCRIPT 正确参考；旧 LZSS 阶段已有识别；用真实原 4B0C80 和逐源字节对比。

## 归档工厂与析构
- 原 490850 完整工厂→490B70 ctor→实际 malloc 对象/索引/名字。
- 读 8 byte header+全 index；原指令索引解密；490C80 原字段初始化。
- 8 归档均成功 status0，且表字节/字段完全匹配成熟 index 工具。
- 八归档：BGM125 CHR1237 DATA4 PIC717 SCRIPT446 SE584 SYS1076 VOICE20418。
- 共 24607 条，解密 index 合计 1058799 bytes。
- 仅表示全索引与原生对象成功创建，不是全部 24607 资源全 payload 读取。
- 本阶段全 payload 只 SCRIPT446；actual factory SCRIPT 对象重跑 446 全 reader exact。
- 原 490BA0(1)→490BC0 全析构：index/name HeapFree、CloseHandle、object HeapFree。
- 8 对象真实 API free/close 无活块。
- 各 host 私有堆最终 HeapDestroy 为 HostMemory 上下文清理，不属于原 CRT teardown 执行。

## API 次数
- factory+allSCRIPT：HeapCreate8、GetVersionExA8、ReadFile462、lstrcpyA16、CharUpperA8、lstrlenA16、HeapAlloc468、HeapFree468、CloseHandle8、SetFilePointer446、GlobalAlloc446、GlobalFree446。
- 原 IAT 所需只桥真实 API；没有伪成功/noop/native routine 短接。

## 约束与未验证
- 提供预打开真实只读句柄。
- 提供本地成熟工具 aux registry inputs；SCRIPT aux 缺省 0。
- 原 factory cache 模式 5357F4=0 为受控输入。
- 未验证：factory 自主 CreateFileA 开档、原 key 注册、cache1、OOM/真实 OS 失败、SBH。
- 未验证：SOB 解析/装载发布/控制调度/演出/像素/音频、四版本等价性。
- 全 goal 继续；不得称全部 100%。

## 结论与下一步
- 本验证证据只支持上述范围。
- 下一步复用真实 factory reader，进入 4A7000/4A6D90 SOB loader 与控制发布。
- 不增加 user 审批要求。
- 所有写入仅限 E:/ZCode Workspace/Galgame 内。
