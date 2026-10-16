# R SOB控制与资源装载入口阶段证据

**原native受控链路** 原EXE仅作Unicorn客体，PC/SP取自先前已证yield记录；受控执行原native 0→430280（第二arg=1跳过再次VM）→41BD90→4A7000→资源构造/打开/空关闭→虚provider调用前，666初次请求、9不同ID，全source 418 hash不变。

**host64格式API核验** host64下真实lstrcpyA 666与wsprintfA 684；18例provider指针为空（9名字×显式/queued），原loader返回1且SEH头恢复，无fake unknown返回。

**第二链路与原provider路径** 第二链路原provider vtable 51A3A0+8=492450，原path 493F40至494029调用lstrlenA前显式停止，666例、lstrcpyA 1332与wsprintfA 684；baseprefix为合成fixture、provider对象受控预分配，仅实际vtable路径，未证真实初始化/读取成功。

**静态构造与bridge限制** 静态原4821B0 ctor把5357CC设self+168并写provider vtable 51A3A0（48223E），不称实际构造。bridge helper lucifen_host_format_bridge.py由editor实现，经两%s/nooverlap/容量/actual API guards验证；x86proxy仅C3 cdecl，由原caller弹16字节；当前host64非原x86 kernel。

**未完成与候选** 原source字符串不发提供者，任何未知不能noop；未完成：lstrlenA/lstrcatA→CreateFileA只读原码请求→LPK fallback→真实heap/loader发布与SOB执行→场景帧音、四版忠实TJS。已有历史VM/sourceIR不覆盖；候选r-sob-control-loader-01，formal r-sob-control-loader-replay-01与r-sob-real-provider-replay-02；四版本goal保持active。

root复核范围：16宿主成功、9宿主拒绝、1 guest真实API成功、8 guest拒绝；10原函数1048指令。两批各自计数，不合称全游戏演出通过。输入manifest仅保存受控请求与暂停状态字段，不重放完整VM现场；重新调用native0后以skip-VM入口保存PC进入控制器。wsprintfA cdecl/NULL和返回数依据[微软官方文档](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-wsprintfa)。helper实际采用128字节A5前后guard。候选before含NUL初次误拒绝由editor精确修复，正式结果对应修复后源码。
