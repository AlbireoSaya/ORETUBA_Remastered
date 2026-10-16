# R 启动绘制与窗口回读阶段

用途：新阶段 README；概述候选 SDK 与验证、失败更正、证据路径与下一步。完整运行收据在 `临时/ISSUE-20261011-02/`；本阶段证据归档在 `工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原启动绘制与窗口回读证据_20261014`。canonical117 已实际退出 0，结论按真实退出状态更新；115/116/117 时间不同，blit 次数与图像 hash 不可直接当作固定回归值。

## 候选 SDK 与验证
- 2026-10-14 root OS/Unicorn 验证：canonical112 真实 GetDC（owned window）源 `45B4A4`，ReleaseDC 为同一 OS 获取线程。
- canonical113 真实 BitBlt 源 `45B762`：owned window DC + 原始 guest 800x600 topdown 32bpp DIB，host 每次调用同步；本次运行观察 79 次 BOOL=1 源 blit，前 75 次在 y0..592 全扫 800x8，余 4 次为 dirty rect 更新；237 个 actual GetPixel 采样匹配。
- canonical115 在同 worker 重新获取同一 owned window DC 用于 capture：整幅 800x600 RGB（alpha unused，忽略）与原始 guest bitmap 匹配，differing color bytes 0，SHA-256 `5216df39f5de25f2600743aaf667201c99a9708d1e29a2afc9f46dff4055503b`；live objects 已清理。
- 图像为启动白底加小橙色 loading 图标，不构成完整 Logo 动画证明。

## 失败更正
- canonical114 验证失败为 KeyError，原因是源已 ReleaseDC；不产生 sourcegame 错误结论。

## 等待事件与阶段边界
- canonical116 在 owned event `guest69000002`（来自注册真实 OS worker）上精确 wait：本次运行 61 次 timed wait，actual WAIT_TIMEOUT=258，源超时 10..14ms 变动；源 blit 141 次；被 1M 指令切片停在源 EIP，无未知 opcode 结论。以上为运行观察，非固定回归值。
- canonical117 已实际退出 0：63 次真实有时限等待，timeout 预算 766ms；127 次源 blit；等待后原生指令切片续执行，停在旧 formatter 不支持新单整数格式的 ValueError（适配器边界，不是原作失败），不是未知 opcode。
- canonical117 结束画面全白，整幅 800x600 RGB 仍匹配源 bitmap，差异 0，SHA-256 `680a1c22a8e114ea0c637847e8cc506794073a55f4350364c8a0421e7dbcc8f0`。
- 未加载原始 PE/DLL 到 OS；无日文 OS golden；未达全路线/音频/四版本 100%；不假报完整 Logo/BGM 播放或目标引擎/日文 OS 黄金参考。

## 兼容与声明状态
- 新 14 个 SDK 和两小验证模块为自有实现候选；新 SDK 声明使用 pointer-sized HDC 与固定 32bit DWORD。
- root32/64 synthetic tests 全部通过：字体 ABC 实际 312 非白像素、8bpp palette 双 guard roundtrip、BITMAP24/32bytes。
- HostLargeMemory/GuestLargeBlocks 仅实例级 1..64MiB 可配（默认 32MiB），旧全局 1MiB guard 不变；32/64 actual 1920016 alloc/realloc guard 清理通过。
- rect OffsetRect/IntersectRect 通过；原始帧 1920016 分配含 16 字节 overhead。

## 证据路径与下一步
- 完整运行收据：`临时/ISSUE-20261011-02/`。
- 证据归档目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原启动绘制与窗口回读证据_20261014`。
- 下一步：root 精确装配并批次审查；按 canonical117 已退出 0 的真实状态更新结论，不再以“进行中/待声明”表述，不假报完整 Logo/BGM 播放或目标引擎/日文 OS 黄金参考。

## 2026-10-14 跨运行裁剪反例与阶段准入结论
- canonical120实际退出0、worker_errors空、ownedcleanup通过。
- 源窗口GetClipBox类型1(NULLREGION)、RECT全0；IsIconic0、IsWindowVisible1。
- 所有源GetPixel为CLR_INVALID；113次blit后整幅与源16543颜色字节差异。
- 故窗口未最小化但DC无可画范围：不能判原作缺图，也不计像素还原通过；原因归属还需验证遮挡/消息泵/原父线程，不能宣称因果已定。
- 115/117两次整帧RGB0差异只对应当次运行；118/119/120反例完整保留。
- 当前覆盖17 SDK=16新增+既有IsIconic复用，以及两editor验证helper。
- 32/64自有OS验证通过，含clipbox owned DIB、IsIconic owned message-window、palette独立output+无输出写入负例拒绝；所有声明不是完成目标引擎。
- 先前14候选状态为此前小批次，不混称所有17新建。
- 单整数cdecl已SDK实测，不假称BGM播放已执行。
- 下一步接原父线程HANDLE/TID消费者与消息循环，在有效DC上再取动态整帧与音频，然后忠实TJS及四版本全路线。
- 证据入口：R_原启动绘制与窗口回读证据_20261014。
