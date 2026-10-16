### 2026-10-14 原启动窗口绘制与真实事件等待证据

用途：R作品skill增量；区分原程序执行与仅root OS取证，并标出未完成项。证据归档目录：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_原启动绘制与窗口回读证据_20261014；完整运行收据：临时/ISSUE-20261011-02。

**原程序执行（root OS/Unicorn验证，含源EIP）**
- canonical112：real GetDC(owned window)，source 45B4A4；ReleaseDC 同一OS获取线程。
- canonical113：real BitBlt source 45B762；owned window DC + 原guest 800x600 topdown 32bpp DIB，每次调用host-synchronized；79次BOOL1源blits，前75次全扫800x8@y0..592，后4次dirty rect；237个实际GetPixel样本匹配。
- canonical116：对owned event guest 69000002 的 exact actual HostSharedEvents.wait，来自已注册 real OS worker：61次timed waits，actual WAIT_TIMEOUT 258，源timeout 10..14ms变化；源blits 141；被1M指令slice在源EIP停止；无unknown opcode结论。
- canonical117：已实际退出0；63次真实有时限等待，timeout预算766ms；127次源blit；等待后原生指令切片续执行，停在旧formatter不支持新单整数格式的ValueError（适配器边界，不是原作失败），不是未知opcode；结束画面全白，整幅800x600 RGB仍匹配源bitmap，差异0，SHA-256 680a1c22a8e114ea0c637847e8cc506794073a55f4350364c8a0421e7dbcc8f0。
- 115/116/117时间不同，blit次数与图像hash不可直接当作固定回归值。

**仅root OS取证/验证（非完整原程序运行结论）**
- canonical115：同一worker重新获取同一owned window DC做capture；完整800x600 RGB（alpha未用忽略）匹配原guest bitmap，differing color bytes 0，SHA-256 5216df39f5de25f2600743aaf667201c99a9708d1e29a2afc9f46dff4055503b；live objects已清理；图像为启动白背景+小橙色loading icon，不构成完整Logo/BGM播放证明。
- canonical114：验证失败KeyError，因source已ReleaseDC；不声称源游戏报错。
- 未加载原始PE/DLL到OS；无目标引擎/日文OS黄金参考；无全路由/音频/四版本100%。

**边界与真实状态**
- 新14个SDK和两小验证模块为自有实现候选；root32/64 synthetic tests全部通过（字体ABC实际312非白像素、8bpp palette双guard roundtrip、BITMAP24/32bytes）。
- HostLargeMemory/GuestLargeBlocks仅实例级1..64MiB可配（默认32MiB），旧全局1MiB guard不变；32/64实际1920016 alloc/realloc guard清理通过；rect OffsetRect/IntersectRect通过；原帧1920016分配含16字节overhead。
