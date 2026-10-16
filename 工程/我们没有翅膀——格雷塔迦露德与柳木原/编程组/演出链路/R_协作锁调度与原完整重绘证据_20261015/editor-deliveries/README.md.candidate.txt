## 交付：阶段README 全文替换稿（仅动两处）

派单未给出该 README 的实际文件路径，故未写盘；以下为**逐字原文 + 仅两处替换**的完整成品稿。若主代理指定落盘路径，可直接整篇替换，无需再动其他字符。

**改动一**（§目的，唯一一处 `goal active`）：
`已 100% goal active，但 not complete` → `完整100%目标保持active，尚未完成`

**改动二**（§155，唯一一处 `可能存档回退`）：
`可能存档回退` → `可能归档回退（archive，不是save）`

---

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

---

## 交付清单与未决项

- 改动清单：仅 2 处字符串替换（如上）；其余字符逐字未动，标点、空格、省略号、SHA 前缀、大小写一律照原。
- 命令与结果：未执行任何命令——派单为纯文本改动，且未提供文件路径，无法定位落盘目标。
- 未决项（需主代理补一条信息）：该 README 的实际路径。请给出后我按上稿整篇替换，或由主代理按精确候选产物落盘。
- 未验证项：无（未做任何测试，也不声称做过）。