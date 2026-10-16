# R_TJS 九项 VM 指令扩展证据（2026-10-16）· README

- **Issue**：ISSUE-20261011-02 ｜ **分支**：`issue/ISSUE-20261011-02-original-fidelity` ｜ **main 基线**：`d87b9251ff027eb5fe2f61d39197f35e831a2fbb`
- **代码目录**：`编程组\原作忠实层\R` ｜ **证据目录**：`编程组\演出链路\R_TJS九项VM指令扩展证据_20261016`
- **性质**：自有 SDK 源码与自有派生元数据；原游戏字节不入库，原 PE / 脚本 / 素材 / 凭据不外发。

## 一、范围与结论

本批在既有 17 条 VM 路径之上新增 **9 条指令**，覆盖推进至 **26/47 opcode，余 21 条**。

| op | 指令 | op | 指令 |
| --- | --- | --- | --- |
| 14 | sub | 25 | shl |
| 15 | mul | 42 | signed<= |
| 21 | xor | 43 | signed> |
| 22 | not | 46 | neq |
| 24 | sar |  |  |

## 二、生产代码与装载依赖

7 处生产改动 ＝ 6 个新函数文件（`r_value_extra_arithmetic` / `..._bits` / `..._compare` / `..._mul`、`r_vm_extra_operands` / `r_vm_extra_value`）＋ `r_vm_step` 新增路由。

**装载依赖**：6 个新文件**必须与既有原 VM 模块显式一同加载**，不会自动接入游戏 `startup`；单独加载或漏载即缺失对应指令。

## 三、数值语义与读写顺序

- 位宽统一 **u32**；移位**取 count 低 5 位**；**sar 先按 s32 解释**再算术右移。
- **mul 用四个 16 位 limb 求低 32 位**，不做可能溢出 signed64 的整字乘法。
- 操作数读序：op15（mul）＝ **b→dest→a**；op21（xor）＝ **b→a→dest**；op22（not）＝ **a→dest**；其余 ＝ **a→b→dest**。
- 写 dest 后**重读 ctx+8**，再加 8（op22）或 12（其他）；**不得提前缓存 PC**。

## 四、证据

1. **原码核对**：原 R47 分派表 `4a7f54` 中本批新增 9 项均从该 R 表定位并本地核对完成；不声称本轮全部 47 项已核。原 EXE SHA256 `b26795b1…3a8ebf33`，**仅由 Unicorn 驱动，不 OS 加载**，不动原件与备份；program 与 handler microstate 均为自构，非原剧情。
2. **目标运行**：新增 **1343** 个完整 VM 用例，在真实原 `4a7a30` 运行，比对原 CPU 的有序写 / PC·op / 返回 / 最终 words，并对 closed-form 结果校验；目标侧实际 `global.RVMRun` 两架构各 **1343/1343 段通过**，非 stub。用例含高位与符号，移位 32 / 33 / 63 / 64 / 65 / 255，乘法边界，source operand 与未对齐 dest 别名；**非法改 RET 后执行不当合法用例**，地址别名另由微步覆盖。
3. **微步**：**216** 个原 handler 微步（ESI＝ctx、EDI＝operand p、EBP＝4、EBX＝12），hook 明确停在 **4a7a75 取指前**，逐 guest operand / ctx DWORD 读写与终值比对，双架构各 216 通过，含未对齐 operand 与 dest、dest＝ctx8/operand 字、u32 回绕。
   —— 此证据**只覆盖新 9 个 handler 的微步**，不代表整个 `RVMRun` 读序（旧 entry guard / 原 native 栈）已完全匹配。

## 五、回归

旧 1390 VM / 1391 段双架构回归通过；真实源 group0 的 242 条动态记录六态冷暖，每架构 2904 次、118574 caller / 35520 VM 写 / 9552 步 / 2556 VM / 480 native 回归通过。此前每架构 45528 全矩阵属既有 17 路径的历史证据，**本轮未重跑该全矩阵，也不冒作新覆盖**。

## 六、故障与教训

三类故障（乘法 operand 读序换位、shift 取低 6 位、先缓存 PC 再写 dest）× 两架构共 **6 次全部检出**，仅用私有副本，候选与原比较器未变。过程修正：源码初稿的 `instanceof Integer/Error` 在执行前由 editor 修正（未通过原样草稿）；root native recipe 最初以 bytearray 传 `mem_write` 失败、改 bytes，第二次因 cached TB 边界造成微步继续取指，补显式 hook stop 后原输入 1343/216 一次通过；**失败未被伪称成功**。

## 七、边界与下一步

未完成：其余 21 条 VM、VM 全读序 / 回调与任意帧别名、银行增长、ctx434 发布 / 129 dispatch、native 生命周期、全部路线画音、四版 100%（OTV 为 MAGES Task DSL + CRI，**非 Lucifen**）。无新成品，goal 保持 active。

下一步：余 21 按 **control 8 / div 3 / memory 10** 分小批并行，先出原 CPU 证据，再接真实运行器，阶段批审。