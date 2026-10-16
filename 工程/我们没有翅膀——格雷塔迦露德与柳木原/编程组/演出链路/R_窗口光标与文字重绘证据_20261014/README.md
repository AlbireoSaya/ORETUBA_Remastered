# R_窗口光标与文字重绘证据_20261014

## 阶段增量（自建作品 skill）

- 本阶段自有 SDK 11 项；自检在 32/64 位均通过。
- 目标 TJS 须保留原句柄映射、PAINT64、字形 0..64 灰度及 DWORD 行对齐，不按 255 猜缩放。
- 147 为八次原文字测量；150/151 八字形查询与八灰度请求，原 BeginPaint 成功。
- 父 WM_PAINT 跨线程持锁保护后停止；源 EndPaint 未执行，fixture 成对清理，非完整重绘。
- 光标消息源调用仍未证实。
- 完整 OT/OTA/OTV/OTR 逻辑、剧本、忠实 TJS、全路线状态与画音 100% 保留未完成。
- 不猜源像素一致，不写 8000 行类断言。

## 2026-10-15 阶段增量
更正：150/151均已运行，非“运行中/151未运行”。

- 150：6轮；原字形API 16次=查询8+取灰度8；文字测量16。
- 151：10轮；同worker TID 13980；字形16、测量16；8灰度缓冲解析0..64，无猜缩放；首块14×13、stride16、182像素。
- 原BeginPaint 40D6C3：真实nonnull HDC、guestPAINT64、rcPaint[0,0,800,600]；父WM_PAINT在EnterCriticalSection 200E3C0因他线程持锁受控停止，源EndPaint未执行；仅worker parked时fixture EndPaint1严格成对。
- 未证：完整重绘；151完整RGB仍差370068颜色字节；cursor20/SetCursor未源调用；SDK双架构通过不冒充原证；150/151 exit0、errors空、cleanup通过均非原退出；149代理地址重叠失败已修，不算游戏错误。
- 下一步：实现持锁工作线程安全让出、父原绘制接续；禁止同Unicorn并行与锁假返回。
- 四版本100% goal active、忠实TJS/音频/全路线未完成。
