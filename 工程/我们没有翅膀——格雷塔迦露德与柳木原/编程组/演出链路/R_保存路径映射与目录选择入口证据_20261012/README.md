# R_保存路径映射与目录选择入口证据（20261012）

## 范围与运行
- 正式证据目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_保存路径映射与目录选择入口证据_20261012/`
- 工具目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/`
- 工具 5 件：`lucifen_host_shell_folder_binding.py`、`lucifen_guest_storage_exact.py`、`lucifen_host_storage_bindings.py`、`lucifen_host_format_one_binding.py`、`lucifen_host_desktop_window_binding.py`
- 运行入口：脚本代码从正式 `verify-WinMain.txt` 读取后由 stdin 传给 Python；fresh 临时相对目录经 argv 传入，不是把目录作为 stdin。runtime 产物落 `临时/ISSUE-20261011-02/fresh`，root 阶段归档到正式证据目录；fresh 目录不得预先存在。
- PowerShell 命令示例：`Get-Content -Raw -LiteralPath '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_保存路径映射与目录选择入口证据_20261012/verify-WinMain.txt' | python -X utf8 -B - '临时/ISSUE-20261011-02/<fresh-name>'`

## 已验事实
- 原 EXE/DLL 仅只读 Unicorn，未 OS 执行装载；沿用已验 original wuvorbis DLL attach=1、15 export 查询、query704、ll_app.sys25 与 inf101 逐字节还原。
- 当前受控原 WinMain 452CF0 继续执行：SHGetSpecialFolderPathA 原返回地址 47E3A4，HWND=0，依次 CSIDL 26 AppData 和 5 Personal，guest fCreate=1；host 实际仅 fCreate=0，两现有目录只读查询 BOOL=1 且 buf260 守卫通过。不能声称缺失目录创建分支或原生完整 API 等价。
- guest 可见路径保留实际只读查询到的原字节；精确允许清单仅 root 已有的 AppData 根、原作品 SaveData 目录、USER.CFG 三个请求，host 目标只在新临时验证 stage/guest-storage/AppData。
- 路径清单：未知/大小写变体/NUL/非 bytes/工区外目标/junction 拒绝；不做泛化解析；不是 OS sandbox；存在串行 TOCTOU 限制。
- 真实 symlink 现场测试缺 WinError 1314 权限；仅真实 junction 拒绝得到验证，不能称 symlink 现场通过。
- 原 WinMain CreateDirectoryA RA40B36E→映射 host CreateDirectoryW 成功 1；CopyFileA RA40B3DD→CopyFileW 成功 1；SetFileAttributesA RA40B3EF→W 成功 1。源仅只读安装介质 SET_UP/USER.CFG 111 字节，sha256 `ef33b1866f5e83a99b70dee58d386898d11eabed0391d254d99879073b40090d`；复制副本逐字节相同，源未变。
- 原 CreateFileA 通道实际 ReadOnlyFiles CreateFileW：read 80000000 share1 sec0 OPEN_EXISTING3 flags80 template0；storage 独立真实 host 句柄 + 明确 guest token 空间 69600000，不碰 source IO；实际 GetFileSize RA4924EC 读到 111，实际 ReadFile RA49253D 得到原 USER.CFG 111 完全相同（这是配置字节，不是台词覆盖或保存系统完成）。
- 原 wsprintfA 1%s 格式 37 字节 + 原参数 18 字节→实际 53 字节；host cdecl3 指针、完整 64 位指针、各 buf+32 守卫、原始 ANSI literal 逐字节保留；仅限定一 %s 格式，非一般 formatter。
- 原 GetDesktopWindow 真实 host HWND + IsWindow=1；借用映射 guest 69800000，无关闭 desktop，无游戏 window 创建证明。
- 精确停止在 SHGetMalloc 未绑定 EIP 127E2A，原返回地址 47E291，未获取 IMalloc，尚未进入 SHBrowseForFolderA，未注入选目录/取消，parent+150 HWND 仍 0，原 WinMain 未返回；不得说 BROWSEINFO 已运行交付或已创建窗口。
- host fixture 清理 passed：全 owned heap/blocks/TLS/CS/file/events/COM0，storage files 也关了；非 originalWinMain 或 DLL shutdown，borrowed desktop 未关闭。
- 叶测：8 个 passed——6 个真实 CreateDir/Copy/Attrs（重复目录 183/重复复制 80/缺失目标 2）、GetFileSize 守卫高 DWORD 0 且不改变文件位置、无效 handle FFFFFFFF/error6；7 个精确 pathmapper 用例 passed；formatter/desktop 当前原生链路有意义验证通过。
- 环境/范围：当前 ACP936 环境，而非原作日文 OS/全 manifest 真实 OS 启动；没有改 originalsource/备份/历史记录/游戏成品；Win7/Win10 未验，当前 Win11 环境受控验证。

## 边界与限制
- 上述只覆盖指定保存路径/目录选择入口片段；目标全 scope OT/OTA/OTV/OTR 忠实 TJS 全部路线/画面/声音 100% 还原仍未完成。
- 目录名/接口/字节覆盖不可冒充还原率。
- 未做 OS 执行 guest 指针与越界写；未知即明确 stop，不 fake。
- symlink 仅缺权限记录，junction 拒绝已验证；不能声称原生完整 API 等价或缺失目录创建分支。

## 后继
- 真实 Shell IMalloc 接口与 Folder PIDL、guest 原 callback。
- nativewindow/plugin/PCM 链路。
- 保持只读 Unicorn/受控 host 绑定，禁止 OS 执行 guest 指针与越界写；未知明确 stop，不 fake。
