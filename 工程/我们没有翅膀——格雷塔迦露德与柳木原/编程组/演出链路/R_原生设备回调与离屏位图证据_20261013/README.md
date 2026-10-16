# R_原生设备回调与离屏位图证据_20261013

本批次为 host32 原始代码设备枚举与离屏 DIB 初始化的有界证据，根批次审查待定；完整 OT/OTA/OTV/OTR100% 仍不完整。完整仓库相对路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原生设备回调与离屏位图证据_20261013/README.md。

## 真实验证事实
原始 EXE 仅 Unicorn；系统 ddraw/gdi/user32 由自有全指针替身实际调用；guest 函数从未向 OS 注册。Host32 原始 DirectDrawEnumerateExA flags7 触发两个原始回调 4ABB30 返回1；两个实际 IDirect3D7 slot3 EnumDevices 调用各枚举三个原始 guest 设备回调 4ABE50，所有原始返回1，共六次回调；两者 host enum HRESULT0。D3DDEVICEDESC7 SDK236，GUID 偏移196。设备原始记录268字节：GUID+0、self+0x10、name+0x14、fullcaps+0x18、hardware flag+0x104（dwDevCaps>>19)&1、next+0x108。两个原生链表长度1、2、3，所有 GUID/name/236caps/flag 字节独立验证。设备1 RGB GUID605c66a47326cf11a31a00aa00b93356、dwDevCaps1361、flag0；设备2 GUID e03de684aa46cf11816f0000c020156e、dwDevCaps102416113、flag1；设备3 GUID789e04f56148d211a40700a0c90629a8、dwDevCaps102481649、flag1。无伪硬件设备或成功，无实际渲染证明；不声称 host 差异原因或物理硬件渲染成功。

原始 EnumDisplaySettingsExA 两个原生 caller 451595 与4515D5；各自索引0..194 返回非零成功，195 返回0 结束枚举；总计392 次只读调用，其中390 次成功、2 次枚举结束零，并非392 次 true；DEVMODEA156、dmDriverExtra0、flags0 守卫保留。模式计数仅当前 host 证据，未更改显示模式。CreateCompatibleDC caller4D490C 使用实际借用 screenDC；自有 memoryDC DeleteDC。CreateDIBSection caller4D4921 实际 header(40,800,-600,1,32,0,0,0,0,0,0)，stride3200，1920000字节，topdown32bit BI_RGB，sectionNULL。实际 bitmap/bits 映射到不同 guest 不透明 bitmap/像素跨度，初始精确字节 SHA。SelectObject caller4D4954 实际选择自有 bitmap，返回真实前一默认 bitmap 并保留借用。清理实际 SelectObject 恢复旧并返回自有 bitmap；DeleteObject 自有后 DeleteDC，借用旧从未删除。初始、结束 guest、结束 host 像素 SHA 均124617c1f65e92d3bc895fbd869e4bb16a30754b198f59e6e973949b9aaa1b01。无像素变化，无帧/渲染证明，且未建立任意 guest/host GDI 像素同步。

## 产物与配方
配方 verify-host32-WinMain.txt；产物 WinMain-boundary.json、Direct3D7-device-callbacks.json、actual-display-mode-enumeration.json、GDI-selection-cleanup.json、GDI-owned-bitmap-cleanup.json、GDI-owned-DC-cleanup.json、host-fixture-cleanup.json。实际原始 config10writes2Closes 加原始音频 DLL attach 继续通过；清理夹具不是原始 shutdown。OS 未加载任何原始 guest EXE/DLL；未创建原始窗口。上述产物记录真实原始代码执行与 Win32 调用证据，未外发原作内容，仅暂存待根应用；根审查待定，根未应用候选前不得声称已验证通过。原始备份/哈希检查独立进行，并非所有产物均为离线技术文档。

## 未决与拒绝
最后未解决导入 LoadIconA 原始 caller40BE9F，instance400000/resource103；原始 parentHWND0。仍需资源/图标/窗口/回调，然后渲染器与全部原始脚本 VM/音频/忠实 TJS 对比；完整 OT/OTA/OTV/OTR100% 仍不完整。证据缺口仍以真实调用计数与 SHA 为准，拒绝任何伪成功。拒绝历史：首次根 cap 守卫读268而非300，已在 recipe02 纠正；首次 modes 守卫只允许第一 caller，在真实第二 caller4515D5 后扩展；gdi01 围栏候选捏造不存在 import/fallback 被拒，采用02；display01 API 长度截断被拒；根 select recipe09 初始缩进错误在任何本机执行前修复。exit0 不伪造成工程成功。

## 依据与下一步
官方来源为 SDK Microsoft win32metadata d3d.h/d3dcaps.h/d3dtypes.h，以及 Microsoft Learn EnumDisplaySettingsExA/DEVMODEA/CreateCompatibleDC/CreateDIBSection/SelectObject。不得添加未验证命令或捏造输出。下一步保持证据导向，继续资源、窗口、回调、渲染器与脚本 VM/音频/忠实 TJS 对比，直到补齐全部证据。不执行原作，不调用暂停角色，不虚构日志或测试结果。
