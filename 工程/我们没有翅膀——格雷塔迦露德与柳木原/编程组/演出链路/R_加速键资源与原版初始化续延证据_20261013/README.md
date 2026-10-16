# R 加速键资源与原版初始化续延 · 批次交付索引

Issue ISSUE-20261011-02；本目录自2026-10-13建立，2026-10-14完成收件。知识正文由editor-easy交付及精确短语patch；下列收件/来源/审查索引由root行政整理。

依据《演出链路/R_加速键资源与原版初始化续延证据_20261013/README.md》,加速键资源7条已32/64位真实验证,原WinMain续延至imm32查询前停止;资源替身与原件非完全等价,画音100%还原仍待验。产物仅workspace暂存由root应用,不Git、不回退他人改动、不调暂停角色。

## 收件清单

- original-accelerator-resource-and-native-table.json：原资源元数据与真实宿主表回执。
- original-WinMain-after-accelerator.json：本批原码最新停止点；original-WinMain-after-window.json是前一步停止点。
- original-window-creation-callbacks.json：本轮原窗口创建复验。
- host-32-accelerator-ABI.json / host-64-accelerator-ABI.json：双架构组件与非法输入回执。
- import-call-candidates.json / import-index-component-cases.json：2096候选/279导入API及组件回执；线性扫描候选不证明CFG可达性。
- 各cleanup.json：宿主夹具清理；不代表原版shutdown。
- root-source-integrity.json：原来源、446脚本、418IR完整性回执。
- verify-original-accelerator.txt / verify-accelerator-ABI.txt / verify-source-integrity.txt：root原码/平台验证配方；必须使用新鲜未存在的输出目录。
- helper-delivery.json / root-batch-review.json：工程候选来源和最终批次审查覆盖。

## 原始判据链接

资源布局与结束标志依据[Microsoft ACCELTABLEENTRY](https://learn.microsoft.com/en-us/windows/win32/menurc/acceltableentry)；运行布局依据[ACCEL](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-accel)。真实创建、复制、销毁依据[CreateAcceleratorTableA](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createacceleratortablea)、[CopyAcceleratorTableA](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-copyacceleratortablea)、[DestroyAcceleratorTable](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-destroyacceleratortable)。[LoadAcceleratorsA](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-loadacceleratorsa)资源自动释放与本owned surrogate生命周期不同。
