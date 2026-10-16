# R 嵌入归属列表与反向绘制原码证据

> editor-easy 增量补正稿，供 README 与 skill 复用。root 仅提供契约元数据，不含原字码/脚本/素材外发。本阶段不覆盖原历史记录，skill 增量更正，旧证据目录另建补正文件。

## 一、契约元数据

- 工具：`lucifen_owner_render_reference.py`（fixture-only；有效 primary native wrapper 与 tail_order，仅 math 辅助，无 productionTJS/cast/secondary）。
- 目录：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R归属与反向绘制证据_20261011/`。
- 原 EXE hash `b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`；TVPGL hash `63e9308c2e89445daa1d427c5b5e1ed1ce863111ca722a5f3b6dd966d065a985`。

## 二、归属列表（owner 嵌入）

原 aux ctor `459DC0` 调用 `459620(this+0xC)`，owner vt `5199E8` 位于 aux+C。相对偏移固定：

- owner head +4 → aux+10
- owner tail +8 → aux+14
- associated_aux +C → aux+18 = self
- node size 0x24；child +0、key +14、extra +18、prev +1C、next +20

原 renderer `45AFF0` 从 `aux+14`（tail）沿 `node+1C`（prev）倒序。初始节点/链接由夹具预分配手工关联；随后原重排修改链/marks，原 renderer 遍历同一节点，全链 head/tail/prev/next 与像素经独立对照；不冒充原堆生成初始节点。

**重要补正**：旧判"不同 node 结构"错误。历史 raw 测试仍是真实受控结果，但不能沿用旧结构解释；原真实受控 raw 像素结果保留，但“不同节点结构”解释作废，由本阶段补正替代；不改写历史记录。

## 三、64 组合矩阵

维度 `64 = type9/10 × chunk0/1 × native424450/4244E0 × 8case`。三 child 的 key 为 10、20、20，三者重叠 1 像素但 u32 source 不同，手工关联出完整 nodes。原 aux ctor、child ctor/bind、wrapper cast+reorder、native429+compositor、原 TVPGL 全部实际执行；排序与逆序对照独立 editor helper，整个 dest 和 padding 对照 opaque oracle 相等，source/frame 保持不变。

source 绑定后原 mark 已为 1；夹具再调用原 setter `458220(0)` 受控清 mark 后核对 reorder，属受控核验，**非剧情真实帧**。

## 四、native 布尔与分层

native frame 为 4u32 `(outer, child, key, truth)`；候选 411/412 注册 809 列表按 callVA 给出，真实运行 vector 未观测。whole truth 以 DWORD!=0 转 bool；callee `skipword` 高 24 位实际取自 caller frameptr，写为 `高24 | bool`。native 输出 0/1 并覆写 caller argsframePtr 栈 slot 低 byte，frame 内容不变；helper 只保留判定，不模拟 stack 高位。

**不要混层**：native `0x100` truth 为 true，而直接 owner（`skipword 0x100`）lowbyte0 为 false，二者语义层不同。

## 五、反向绘制排序规则

同键 before/after 反向绘制：**更小 key 后画（覆盖），大 key 先画；相同 key 时，前插者后画、后插者先画**。本 batch 仅 opaque32，不推广到 blend/alpha。

## 六、静态与 SOB 扫描

静态 5 入口共 592 行、14 条 direct edge、20 处间接缺口、0 diag，非完整；复用 direct CFG，存在潜在 native 411/412/790 到 sort 方法（790 为多层）。21 个 SOB0 加 1 个 SOB2，合计 22 个代码容器，扫描原 reloc 表，slot 411/412/790 均 0 refs；1 个 SOB1 为声明非容器。未覆盖 TOB、indirect 与真实场景，不能据此断言游戏未使用。

## 七、产物文件（暂存，待 root 生成收据）

- `native-owner-reorder-to-compositor-matrix-02.json`（64）
- `embedded-owner-render-instruction-evidence.json`
- `owner-reorder-registration-candidates.json`
- `reorder-SOB-references.json`
- `reorder-upstream-SOB-references.json`
- `reorder-native-direct-candidates.json`
- `helper-verification.json`（8 组 root 独立手定期望核验，含错误遍历像素负控）
- `verify-native-to-render.txt`、`verify-source-references.txt`、`verify-helper.txt`

只写工作区临时新目录，不覆盖既有证据。

## 八、过程如实记录

首次 reference 4096 全 reason finishlength，非交付；窄 prompt 后 stop。源码与行为均 editor，root 侧原码验证。SOB scan 首次 mature loader 正确拒 SOB1，改仅接受"类型异常区分声明"后得 22 完整代码容器，未忽略其它 error。mark 核验初次误以 bind 后 marks 0，实际为 `[1,1,1]`，经原 setter 受控清后复验，未伪造成功。

## 九、缺口与下一步

仍缺原 allocator / 插入 / free / 真实源 CFG 及场景、secondary、notify、alpha、全部四版剧本/IR/TJS/全画音；宿主 primary 未通过，不 OS 启动原 EXE/DLL；goal active 范围不变。下一步：原 secondary/notify + 源 TOB 调度，并在有依据前提下验证对象/层序的 TJS 接入。