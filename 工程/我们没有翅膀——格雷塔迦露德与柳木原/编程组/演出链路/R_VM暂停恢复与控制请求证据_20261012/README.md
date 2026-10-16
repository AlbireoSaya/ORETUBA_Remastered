# R VM暂停恢复与控制请求（2026-10-12）

本阶段新增 lucifen_host_string_bridge.py 与 lucifen_inline_vm_reference.py（最新 candidate03），用于核验 native0 字符串桥与内联 VM reference。native0 位于 41B3A0，先写 global 5355C0=2，取 frame 首 word 字符串，经真实 IAT 5181DC（KERNEL32.lstrcpyA）写入 global 5354BC，随后返回 native0；原 PE import descriptor 已核验。初探 666 输入全部来自原代码、最长 9 字节、9 个不同控制 ID，对应 9 个 SOB 文件均存在；文件名关联不等同原控制器或 loader 已执行，因此不对未提供的原标签名与作用作任何推断。

字符串桥以 host64 WinDLL API 实现，guest x86 proxy 仅以 ret8 接收实际结果；capacity 260 为受控核验范围，原 kernel 故障与重叠情形不构成证明，未知输入一律拒绝。当前 18 宿主、guest 拒绝 6、host 拒绝 4，控制 VM 41 fixtures 通过。返回、终止与非重叠契约以微软 lstrcpyA 文档为依据，本工具只验证桥本身，不代表目标引擎实现。

内联 reference 侧，990 独立表达式×6 受控状态共 5940 首次执行；empty、full ascending、full reversed、duplicate、even-subset 的地址列表分支 10 与零 channel 数量分支 676 均实际执行并比对。独立 reference 与原 VM 在 trace、native frame、整个 1MiB live、原 source 自改及 PE 控制字段上逐字节一致。首次运行 5274 次返回 0、666 次 yield1；原 opcode0 暂停不 pop 栈、PC 保留，绝不可当作结束或 noop。

672 恢复段中，666 结束 0、6 再次 yield1，最终全部结束且栈回 baseline；共 672 次真实系统复制，保持 PC/SP 后再进入原 4A7A50。该过程不执行外部 scene/input 控制器；人工保留原状态续行只证明 VM 状态语义，不证明演出或 SOB 控制生命周期，也不证明有效 channel 清理。原参数 3349 expr×6=20094 回归通过。

candidate 子代理工作区为 ISSUE-20261011-02/r-inline-vm-complete-01/，链路在 r-inline-vm-chain-01，正式临时目录 r-inline-vm-chain-replay-01，回归为 r-inline-vm-regression-replay-01。正式回放以 root receipt 为准，recipe 使用新输出目录，历史成果不覆盖。

下一步聚焦 ctx7560 虚接口到真实 SOB 控制器/loader（不虚构成功）、有效 voice channel lifecycle、原 heap 与文本演出、四版本忠实 TJS 以及全部路线帧音频。primary 失败时不通过 OS 启动原件；完整 goal 保持，不报 100%。

root行政凭据：八个完整JSON正式回放一致，参考03为最终精确源码。chain summary的actual_host_copy_calls为首次激活666次，恢复另6次，总672次，以完整行结果对账。先chain建立新目录，之后host/control可独立；legacy regression自建另外新目录，不能覆盖历史。工具仅核验用途，系统接口契约链接：[Microsoft lstrcpyA](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-lstrcpya)。
