# R表面对象与填色链路证据

2026-10-11，ISSUE-20261011-02。本目录归档 root 独立受控 CPU 取证与 editor-easy high 交付工具/知识的阶段复核依据；不是原作画面截图或全剧本复现报告。

原表面构造→原引擎填色→原 DLL→原虚方法→原像素核连续执行，未知函数返回 stub 为零。两个原模块手动映射，几何、像素缓冲和设置为受控夹具；marker1 不是已加载的 Windows 模块句柄。原始文件来源和 SHA256 见 provenance.json。

- surface-interface-contract.json：已验证原类的局部 ABI、字段和虚槽，不推广所有继承类。
- surface-first-fill-chain.json：真实原码连续调用轨迹、像素结果和 canary。
- surface32-backend-dirty-distinguished.json / surface8-backend-matrix.json：每格式28组合，两后端、正负行距、7种请求。
- surface-member-negative-boundaries.json：12个缓冲/深度/更新矩形指针边界。
- surface-clip-state-contract.json：9个原裁剪设置、clamp 后倒置宽度的 NULL请求见证。倒置高度没有送入像素循环。
- surface-stateful-dirty-chain.json：DLL有效A→回退有效B→DLL空请求，最后更新矩形仍A。
- surface-callers-static.json：27填色和12构造直接调用候选；不是完整可达或原生指令映射。
- surface-production-recheck.json / surface-production-boundaries.json：应用 editor 原文的工具重跑28组原码填色，11项调用/输入边界核验。
- 验证命令.json：7条当时实际运行命令；历史候选路径依赖忽略区，重放必须使用新输出路径；生产重跑使用正式工具。桥接 receipt 在忽略的子代理工作区，未以模型退出当工程验收。
- 批次审查覆盖清单.json：本批 root 通过范围；分别保存 worktree 原字节和 Git canonical blob 指纹，本清单本身不递归列自己。

32位写完整物理00RRGGBB，显示alpha未验；8位写第一分量低8，调色板未验。仅AL有已核实布尔语义。有效clip数学参考不覆盖全部脏矩形状态机。原Win32 DIB生命周期、真实启动环境、全部图层/特效/语音/剧本、四版本画音全对照和TJS生产接入仍未完成。
