# R_原生资源图标与窗口类证据 2026-10-13
路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生资源图标与窗口类证据_20261013/README.md

仅原代码 Unicorn；原 PE 从不 OS 加载。pefile 2024.8.26 解析 32 资源；JP group103/lang1041 有 16/32/48/256 8bpp 图标。TrueLookup 选 32px RT_ICON2(2216B)，真 CreateIconFromResourceEx/GetIconInfo/DestroyIcon 与 2 bitmap-copy DeleteObject。原 3 个 LoadIconA 调用 40BE9F/49F6E2/49F6F0 保留同一 HICON 自缓存；资源替身非字面 LoadIcon 等证。

GetKeyState17 返 SHORT0，父字节 0E3D 前2后2，非 Ctrl 证明。MonitorFromRect[-1,-1,799,599] flags2 同借用 monitor；stock5/arrow32512 借用不删。RegisterClassExA 用原 48B EX/style3/proc49F860 字段，自有 host instance 与 Python guard proxy；proxy 从不调用，原 WNDPROC 未执行。UnregisterClass 于 DestroyIcon 前通过。

GETWORKAREA 0x30/ui0/flags0 返 [0,0,1920,1032]，无设置写入。Final CreateWindowExA 边界 RA49F840/ex200/styleCB0000/位置550,195/外820x643/lpParam parent+14C/HWND0；class 与初标题18B同哈希。实际 CreateWindow 未调，无假 HWND/回调成功。下一步须在 outer emu_start 外 relay 原窗口回调，正确 CREATESTRUCTA 与指针/句柄映射；OT/OTA/OTV/OTR fourversions/allroutes/states/keyframes/audio timing100% incomplete。

32/64 standalone fixture 均过真图标+自有 class reg/unreg，WNDCLASS40/72、EX48/80、ICONINFO20/32；非 64 原 WinMain。证据：verify-host32-WinMain.txt、verify-resource-ABI.txt、original-icon-resource.json、original-window-class-registration.json、original-window-creation-parameters.json、original-work-area-query.json、root-source-integrity.json。原源码哈希未变(1EXE/8LPK/3 originalDLL/2 referenceDLL/446SCRIPT/418IR/USER.CFG)。Guarded buffers/全 host 指针/资源清理过，fixture 清理非原 shutdown；ACP936/当前 host DPI 非 JP OS 证明。Root 批审待，绝不 full-engine/100%。拒绝：早前 firstLoadIcon RA only guard 与 window_scope 冲突已修；勿述为原 Cpp 失败。文档只列事实+边界，不叙年表；无未验证命令。本产物仅派生元数据，root 应用候选，workspace-only/noGit、未独做、未调暂停角色、非翻译规范缓存未变。
