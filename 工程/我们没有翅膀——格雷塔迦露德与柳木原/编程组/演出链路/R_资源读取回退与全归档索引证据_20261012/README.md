# R资源读取回退与全归档索引阶段证据

本阶段范围：helper `lucifen_host_path_bridge.py` 提供实际 host64 `lstrlenA`、`lstrcatA`、仅自然缺路径的只读 `CreateFileA`、ASCII `CharLowerA`；原 x86proxy 的 ret4/ret8/ret28 为真实弹栈。所有实际 API 均无 fake 成功，因此不能称为原 x86 kernel。未完成项集中在 LPK 读取链路与后续 loader。

路径666请求已自证 first-yield PC/SP 字段重调用 native0，并进入原 430280 skip-VM 入口；原 provider 492450/493F40 到达归档 lookup。实际 lstrlen666/lstrcat666/CreateFile666 返回自然错误3，CharLower666 亦为自然结果；复制1998、format684 含18缺 provider 自然失败。

下一链路采用受控预分配 archive list 加原 490B70 ctor 的 LPKreader；flag/table metadata 人工受控，表来自成熟 community 工具的原 SCRIPT 索引解密。原 492370 按 prefix 裁相对名，vtable 51A92C+18=491360，原 4F9A20 匹配 entry，666 到原 491430 读取前。该批 lower1332、复制2664，其余同上。

R原 SET_UP 八 LPK 全部 24607 entry，与社区工具 traverse 及真实 record 位置对照：mode0=4189、mode1=20418、24 真实 missing 查找均 FFFFFFFF；使用原 4F9A20，不称原解密/实际读取/解压，源 index 与 PE 不改。LPKheader 原 490850 比较 LPK1，factory static 5188D8+4 指向 490850，constructor 490B70 写 51A92C；静态和预分配 ctor 不能称完整工厂。

source418TOB 及历史 IR 不改，原游戏不 OS 运行、不载原 DLL，不外发源内容。正式依据 root 回执，不报全演出/四版本100%，goal 完整 active。后续：原 index 解密→491430/492D60 实际 LPK 读/allocator/解压→原 SOB loader 发布执行→画音及四版忠实 TJS。候选 r-resource-open-path-01，临时 r-resource-open-path-native-02、r-resource-open-path-lpk-entry-01、r-archive-native-trie-01。

root复核：13实际宿主字符串用例、3 guest用例、15拒绝；实际缺路径错误3，以及已有文件仅只读打开后立即CloseHandle并拒绝。正式四recipe产生九份完整JSON与初次完全一致；全部在本机、未加载原游戏EXE/DLL。两个666请求批次独立计数，受控元数据和已证PC/SP字段不等同实际全VM现场、实际LPK工厂或SOB执行。静态8函数964指令；LPK signature xref仅候选，51A92C由原constructor写入核实。host CharLowerA仅ASCII（严格排除packed character）；lstrlenA/lstrcatA包括CP932字节夹具。

复验：工作区PowerShell逐份 Get-Content -Raw -Encoding UTF8 -LiteralPath '<本目录>/verify-*.txt' | python -X utf8 -B -；需把副本输出改为新的临时子目录。三链路依赖既有工具、R原EXE/八LPK/418 TOB及上一阶段numeric request manifest；成熟community工具只import，不复制源码。缺文件fixture在_game_ascii/ISSUE-20261011-02-resource-empty-01，只用于真实READ/OPEN_EXISTING失败，完成后清空目录可安全重建。

接口依据：[lstrlenA](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrlena)、[lstrcatA](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrcata)、[CreateFileA](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilea)、[CharLowerA](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-charlowera)。原index解密、真实heap、491430读取/解压、SOB发布和四版全画音仍未完成；完整goal不缩小、不报100%。
