## 2026-10-14 原启动绘制与窗口回读有限检查点

- R 原程序（Unicorn 原码 + 真实 OS owned 窗口）：115/117 各自 800x600 整幅 RGB 零差异。
- 117 观察真实 63 次 wait、127 blit，停于旧格式适配边界。
- 118/119 另两 run 整幅出现 16543 颜色字节差异；所有 GetPixel 样本 CLR_INVALID=FFFFFFFF，窗口 DC 采样不可用，不计还原通过。
- 上述差异原因待查：clip / visible / iconic / 原消息循环。
- 结论边界：不得声称所有 run 通过、目标引擎完成或日文 OS golden。
- 自有 SDK 32/64 通过：字形 312 非白像素、palette 双独立 guards、不写输出的负例拒绝、BITMAP24/32 布局；integer cdecl 有符号四组 guard 实测。
- 现有 17 个 SDK 与两个小验证 helper；两个诊断 SDK 仅待 owned 对象测试后准入。
- 主全 goal 四版保持。
- 下一步：窗口 clip 与源 parent 消息循环；其后才谈 BGM 播放、忠实 TJS、allroutes。
- 资料入口：演出链路/R_原启动绘制与窗口回读证据_20261014。
