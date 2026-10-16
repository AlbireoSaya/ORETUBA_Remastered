实际装载 VM 与 SOB 调度证据（20261012）

一、装载 VM 实测：main.sob 由 4A7000 装载，4A7A50（this controller+4）执行 9 个 op，依序 6,11,32,30,40,8,5,12,0，偏移 0,8,16,28,908,920,928,944,952；retAppProc 是构造器初始字 0，不是回调返回；处于实际构造函数状态。native 0/41B3A0 真实体将全局 5355C0 写为 2、5354BC GameInit 经实际 Windows lstrcpyA 写入；return yield 1，SP delta 16。

二、编辑器辅助：lucifen_sob_control_step.py 在既有 inline VM 引用上扩展，仅实现 op6 jump 与 op11 reserve；内存与 native 回调均显式；未知 op 抛 NotImplementedError。

三、参考克隆：23 个自有区域共 237836 字节，含 control globals；为 9 ops 加 trace/native frame/return 之后的逐项内存/trace/frame/return 相等，并非整个应用保真；原始 payload 未存于外部。

四、原版调度器 41BEE0：非旧 TOB outer 430280，直接来自已装载 main——yield→原版 4A79F0 保存 PC→实际 vt+4 方法 41BD90→实际 host wsprintfA→4A7000 实际 GameInit SOB 装载/解密/重定位/发布→递增 5354B8、清除 5355C0→子 VM。共 22 次调度（9 main 加 13 child），子首指令缓冲为精确独立重定位参考。原版 slot6/4114D0 arg21 在实际 PE 全局 5357E4==0 时返回 0（DLL 可用性访问器）；原版全局 530C94==0 仍未初始化的父级，非真实父应用状态。随后在 slot796/414530 应用窗口消费者前停止（路由 452BD0 解引用 this+150），未伪造父级/GUI/noop/native 返回。native 体实际执行 2 个（slot0 与 slot6 arg21），末尾 native 796 未执行；模块深度 3（func/main/child），保存 PC 与 child 零标记。

五、释放与统计：释放全部经实际 4A7230/controller/archive/freeptd，计 162 HeapAlloc、162 HeapFree、24 GlobalAlloc、24 GlobalFree、26 ReadFile、25 CreateFileA、24 SetFilePointer、1 CloseHandle、1 wsprintf。

六、校验与文件：源基线是 1 EXE/8 LPK/446 SCRIPT/418 IR，当前将重验尚未新结果。artifact 列表为 main-VM-reference-summary.json、scheduler-boundary.json、scheduler-release-summary.json、verify-main-vm.txt、verify-scheduler.txt、source-provenance.json，为拟归档范围，不声明已全保存；sourceguard 采用前一阶段权威哈希。

七、待定与下一步：只 Unicorn 运行原 x86，不 OS 启动。本批未达全脚本/SOB 调度完成/父应用/CRT/OS 启动/渲染/音频/四版本 100%。本批 root 待集中审查未合并。受控条件（provider/cache 0/prefix/preopened archive/records/context/zero above frame RtlUnwind emu/TLS 索引输入）不变。父对象 ctor 尚未完成，下一步验证：检查实际父应用构造函数与窗口生命周期及 tvpglpublisher，经原版 ctor 在只读保护内获得真实类型化父对象；不支持的 API/消费者即停，不造假值；后续分支/模块帧/native 效果/音乐/脚本忠实 TJS/全路线帧音频。