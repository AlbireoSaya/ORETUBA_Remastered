# R_TJS 真实源完整记录证据（阶段 README）

日期：2026-10-16 ｜ Issue：ISSUE-20261011-02 ｜ 分支：`issue/ISSUE-20261011-02-original-fidelity` ｜ 基线：`3496d0b3…`
阶段目录：`编程组/演出链路/R_TJS真实源完整记录证据_20261016`

## 一、真实语料范围
本批直接以原完整字节为输入，覆盖 **418 个源文件 / 3794 条动态记录**，每记录 **6 个受控状态**、每状态冷暖各 1 次，分 **16 片**执行。目标端 **32/64 位每架构 45,528 条记录、22,764 个用例**，全部通过；exact 覆盖无遗漏、无重复，源哈希未变。原 `42FB50` 仅在 Unicorn 中执行，不 OS 加载原 EXE/DLL；原 EXE SHA 仍为 `b26795b1…`。

## 二、backing 策略
新增 `RSourceByte` / `RSourceRegions` 两验证夹具：以**原始完整字节 Array 作只读 backing**，另设**脏写缓存**，替代旧逐字节预填。克隆 state / execute / final 三夹具：state 保留稀疏 `initial_words` 种子；execute 从 `spec.start` 进入，内存基址仍指向 source；final 检查**全部原 source 写地址的最终字节**。源字节、完整原码事件与生成 TJS 数据只落 `临时/` 或 ignored，不入 Git、不外发。

## 三、真实验证计数
每架构：caller 读写事件 1,891,834，VM 写 562,452，VM 步 151,500，VM 运行 40,188，native 调用 7,512。实际原文矩阵用到 14 个 opcode（摘要字典），目标仍只 **17/47**，不因本批申报 47 全实现。原 native 仅三种只读查询：`411c40` 5040 次、`414160` 1236 次、`418650` 1236 次，**不等于所有 native 生命周期覆盖**。

## 四、局限
未独立计算全 source 图像哈希；VM 读取与 native 内部栈不比；native 临时 cell 仅特定准备，不代表任意机器帧别名；heap/PE 快照只作写覆盖核查，非独立语义 oracle。6 态为**受控矩阵**，不等于全路线、全画音或四版 100%；OTV 为 MAGES Task DSL + CRI，非 Lucifen。

## 五、依赖与复现入口
依赖既有本地**解包原语料**与 **dynamic-record-index**，并非无游戏原件也可复现的独立包。入口：**本地 generator + runner + full-matrix-summary**；Git 仅存自有 fixture、recipe、摘要/哈希、全部 32 目标回执与六条故障回执。LF 校验 recipe 允许原 SHA 或明确登记的 canonical LF SHA；git CRLF 入库后的 1390/1391 在 32 位实跑通过，非无条件跳哈希。

## 六、故障、失败与下一步
三类新故障各自 32/64 共 6 次全部检出：① 丢 record start 偏移；② backing 全读零；③ 篡改源写最终字节预期。三者为私有副本，无生产改动。首次 pilot 三分片 frame 列 4 失配，原因是稀疏初值未收齐 native frame 额外两个 DWORD；root 补采 16 字节后重新生成目录并全量通过，**未放宽比较**。下一步：验证新 9 个 VM 候选的边界、别名与原 CPU 微步，再接演出链路；仍缺真实银行增长、剩余 30 VM、ctx434 发布 / 129 dispatch、native 生命周期、inline live、全路线画音与四版 100%。goal 保持 active。