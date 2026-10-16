# 阶段README · 协作锁调度与原完整重绘证据（20261015）

## 目的
汇总本阶段证据：FullOT/OTA/OTV/OTR 完整100%目标保持active，尚未完成；不声称 world 锁已全部支持，不推断未给出的测试执行。

## 生产 SDK 与自检
10 SDK：ownerstate/wait/control 3、cooperative CS request 1、budget 1、mousepack 1、PostMessage 1、capture Get/Set/Release 3（capture 3 未导入原 EXE，仅合成）。3 项 easy 模块自检（owner/CS/mouse）：OS32/64 递归 CS 在 worker 上 depth 2→0、parent 实际 enter、释放 CS worker 259、同 OS identity；错误 owner 拒绝、原子 budget 保留未执行；ownPostMessage/Peek/Dispatch 顺序与 capture previous/cleanup 通过；无物理键鼠注入。

## 152/153
152 仅 root CREATESTRUCT local cs None alias AttributeError，无实际 handoff，cleanup 通过。153 实际 key 02003B50，worker 28996 留 depth0，实际 native Leave RA45214A；parent 17084 CPU/FS 0 恢复并实际 enter；原 WM_PAINT 49F860 实际 Begin RA40D6C3/End RA40D864 BOOL1，同 worker creator 仍活，全 800x600 RGB 差 0/SHA 07419b…；但 worker 恢复旧 proxy ret 触发重复 Leave 与 owned guard RuntimeError，root adapter 非 game。

## 154/156
154 修复精确 proxy Stdcall 8 字节 [ra,key] pop 与 EIP ra before yield，无假解锁；worker 27012/parent 22492，gen13→14 多一切片，16 logical parent rounds 无失败/错误，全 RGB 0/SHA c303be1f…，实际原 EndPaint 1；首次捕获全 R title 无白带，来源生成后台缓冲比较，非目标 TJS/日文 OS/全路线 100%。156 仅扩 root rect cap 8192，real guards 不变，pending 无 outcome。

## 155
explicit owned PostMessage move/down/up 715385，flags 0/1/0，非物理输入，在源 paint 后；源 WndProc 512/513/514 返回 0；无引擎/脚本字节变更。29 rounds，全 RGB 0/SHA d14d…，停止旧 rootSetRect 观察 cap 2048；源 loose pic/bg64.elg 查询缺失，可能归档回退（archive，不是save），不能声称完成首故事。

## 复现与限制
复现依赖前阶段、编程组工具与 ignored original/cache。限制：原 GetFocus/SetFocus/async state、全部 source events/audio/routes/final TJS/full scheduler/Exit/loader/TEB 均 remain；原 PE/DLL 从未 OS loaded；全部写入 workspace，original backup 只读，source integrity final pending；无 native paused roles；Dispatch 全批准 AGENTS 文本已显式发出，仅用于 pure tools。不称 all clipping fixed 或 every blit samples pass，初始 NULL 负面结果保留。

# 2026-10-15 最终收据（增量 · 更正 156 待验）

- 156 更正：真实完成 40 逻辑父轮。
- 明确测试 3 条：PostMessage move / down / up 由原 WndProc 处理。
- 无 worker / parent 异常。
- SetRect 真实 3281 次，观察 cap 8192。
- 完整 RGB 差 12600 仍保留，不当完全通过。
- 截图仍为 R 标题菜单；bg64 loose 探测不能证明进入正文。
- 153 / 154 / 155 三次完整 RGB 为 0，只证明对应源缓冲 / 原窗口时刻；初始 NULL 反例不抹掉。
- 全四版「全部原逻辑 / 剧本 / 忠实 TJS / 路线状态 / 画音 100%」仍未完成。
- 下一步：追根原输入对象状态与标题 START 触发链，未以未知 API 伪返回。

（仅上列给定事实，不补理由、不外推。）
