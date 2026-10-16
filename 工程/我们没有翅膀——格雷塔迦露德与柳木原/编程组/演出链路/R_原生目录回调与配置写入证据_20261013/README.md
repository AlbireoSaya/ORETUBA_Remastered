# R 原生目录回调与配置写入证据

目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013`

状态：待 root 最终复核的候选阶段证据。当前 reviewed facts 仅对应本目录；不表示完整 OT/OTA/OTV/OTR，也不表示忠实 TJS 100% 完成。

## 事实

### 原始 Shell 边界
- WinMain：`0x452cf0`
- BROWSEINFO_callback：`0x47e250`
- original_SHGetMalloc_return：`0x47e291`
- original_GetPath_return：`0x47e362`
- original_IMalloc_Free_return：`0x47e372`
- original_Release_return：`0x47e37c`
- IMalloc 槽位更正：`DidAlloc` slot 7，`Free` slot 5，`Release` slot 2。root 初始候选写 `DidAlloc` slot 8 是错误的；经自身进程测试后已拒绝该候选，改用实际 SDK 槽位。误调可能执行自身进程 `HeapMinimize`；错误候选未入库，未用于原作执行。

### 目录回调与窗口消息
- original_callback_cases：5
- only_message_1_SendMessageA：1126
- wParam：1
- native_callback_return_all：0
- host_receiver_result_is_fixture：79225
- parent_HWND：0
- WinMain_not_returned：true

### 原生写入与配置
- native_second_CreateDirectory_return：`0x40b79a`
- actual_native_write_calls：10
- original_CreateFile_write_return：`0x47ea5f`
- original_WriteFile_return：`0x47eb87`
- original_Close_return：`0x47e46f`
- USER_CFG_first_three_field_lengths_unchanged：`[72, 14, 17]`
- USER_CFG_fourth_field：original selected SaveData path plus NUL，变长；u16 length-prefixed
- APP_CFG_bytes：196
- APP_CFG_prefix_u32：192
- APP_CFG_body_bytes：192
- actual_original_missing_config_handlers：`0x515c60`、`0x515c56`
- original_files_modified：0

### EXCEPTION_RECORD / CONTEXT / unwind
- controlled_EXCEPTION_RECORD：80
- controlled_CONTEXT：716
- RtlUnwind_guest_OS_current_head_only_count：2

### 驱动边界
- native_get_drive_boundary：`0x127614`
- original_GetDriveType_return：`0x48299c`
- 在未知 `GetDriveTypeA` 处停止。该停止不等于窗口、游戏、PCM、完整关机或 Win7-10 证明。

### 正式 Shell/IO
- formal_Shell_IO_cases：7

### 源对比
- new_source_all_34_files_equal_existing_backup：true
- source_total_bytes：2768305083
- no_additional_files_vs_backup：true
- original_Source_cfg_111_unchanged：true
- source_SCRIPT446_IR418_unchanged：true
- 引用 `new-source-media-comparison.json` 已有 `source_root` 完整路径即可；本目录不重复冗长路径。

## 运行

从 workspace 根运行；每次传入的 fresh 目录必须不同且不存在，示例使用 `临时/ISSUE-20261011-02/fresh-nonexisting`。

```bash
python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013/verify-WinMain.txt" "临时/ISSUE-20261011-02/fresh-WinMain-02"
python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013/verify-Shell-and-IO.txt" "临时/ISSUE-20261011-02/fresh-Shell-IO-02"
python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生目录回调与配置写入证据_20261013/verify-source-integrity.txt" "临时/ISSUE-20261011-02/fresh-source-02"
```

源对比：

```bash
python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/lucifen_readonly_source_compare.py" --source "D:/360安全浏览器下载/[110624][Navel] 俺たちに翼はない R -Limited Edition- (nrg)/ORETUBAR" --reference "备份/我们没有翅膀R-安装介质" --output "临时/ISSUE-20261011-02/fresh-media-02/manifest.json"
```

## helper

- `lucifen_host_shell_allocator_binding.py`
- `lucifen_host_shell_pidl_bindings.py`
- `lucifen_host_message_window_bindings.py`
- `lucifen_host_file_write_binding.py`
- `lucifen_readonly_source_compare.py`

## 证据边界

- original EXE/DLL 仍仅为 Unicorn readonly x86；系统 raw API 为真实调用。
- selected PIDLIST 输入为 own workspace 显式 replay；没有实际 `SHBrowseForFolder` 对话框。
- host 为 invisible message-only fixture receiver；guest WNDPROC/callback 从未由 OS 注册。
- CP936 不是 original JP OS。
- `GetSpecialFolder` host `fCreate0` 对只读已存在目录查询忽略 original guest1。
- 未知 `GetDriveTypeA` 处停止，不证明窗口/游戏/PCM/完整关机/Win7-10。
- 曾拒绝 native probe10 的 stale postchecker，它预期两次 folder calls，但原始实际为三次；正式修复证明 `[26, 5, 26]`。

## 停点与后续

停点：本目录只覆盖上述 R 原生目录回调与配置写入候选证据。
后续未完成：完整 OT、OTA、OTV、OTR；忠实 TJS 100% 未完成。待 root 最终复核时，以最终审查状态 record 这些待评审历史措辞；不追加假完成。