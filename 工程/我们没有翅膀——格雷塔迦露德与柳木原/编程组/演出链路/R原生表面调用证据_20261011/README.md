# R原生入口到表面操作的阶段证据

2026-10-11，ISSUE-20261011-02。root分析、原码独立验证、集中复核；editor-easy DeepSeek high交付全部实现及技术知识，暂停角色未调用。

- R-native-direct-CFG.json：809静态slot/803唯一handler＋3target，2095个walk入口、131038条累加解码指令、4315个call/tail边、2634个间接缺口，无解码/读错/预算诊断。不是完整控制流；入口可能含跨函数直接跳转，不作函数所有权边界。
- R-native-surface-direct-paths.json：构造46、填色13、SetClip零条已发现direct路径；零不证明不可达。分支可不可行，静态注册向量尚未运行观测。
- R-SOB-fill-candidate-references.json：严格SOB链接对账38条引用、6个候选slot；322没有这22个代码容器的直接引用，不能推广动态/TOB未使用。
- direct-cfg-synthetic-verification.json：20项条件/loop/jecxz、自循环/tail、间接缺口、异常/预算和collector核验。旧LOOP漏跳已按editor补丁修正；精确应用收据说明仅机械恢复原行缩进。
- native322-first-continuous-chain.json：原4540B0构造、41D860 cast/原type4 getter、原420B50处理、实际当前host32 USER32.SetRect、455460/4D4BD0、tvpgl填色与像素核连续执行，未知返回stub0。
- native322-surface-matrix56.json：32/8位、两后端、正负stride、7显式rect，像素/frame/padding/canary及+51标志对照。
- native322-null-depth-boundaries.json：10个NULL对象/像素、16/24拒绝、32接受边界。
- R-native-direct-CFG-production-recheck.json：正式lucifen_direct_cfg.py再次取得相同图；只允许耗时统计不同，源码原文与候选核对。
- provenance.json / 验证命令.json / 批次审查覆盖清单.json：源指纹、实际宿主32位API版本/绑定、命令、候选来源与审查范围。重放历史命令要换新输出路径，不覆盖历史。

[Microsoft SetRect定义](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setrect)支持API签名与坐标写入契约；本批仍以原码执行作本机版本证据。手动映射系统DLL、绑定IAT不是Windows loader、DllMain或历史系统兼容性验证。+58通知sink保持原ctor的NULL状态，+51只按实际写值报告，未当作完整屏幕刷新语义。

正式四版goal经用户清除误建resume后重新创建为active，未设预算。原运行注册、VM参数恢复、全部cast/通知sink、真实DIB/资源生命周期、TJS接入、忠实剧本及四版原画音全对照仍未完成。下一阶段优先有源引用的238/239/429操作与DIB/资源绑定，并先验证只读宿主环境。
