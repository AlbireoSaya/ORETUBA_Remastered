# R 原版工作线程启动与同步证据（2026-10-14）

- 原作EXE/DLL代码仅在guestCPU执行，原进程没有OS启动；真实宿主线程由自有Pythonguard调用guestCPU。
- 14个通用SDK/字节helper经root32/64独立验证，thread/events/font通过；该14仅为helper数量，非实际运行编号。
- 原CRT TID/TLS逐项与真实OS一致；原WUV entry reason2返回1，不可笼统声称完整attach链已确认。
- 两个原SetEvent实为自有事件信号。
- 静态global531188初值为0；原data table 52804C→40E180→40E190→402DF0与原atexit登记产生原5199F0虚表，未手填。
- 77越过原空目标；78源为CreateFontIndirectA RA45C697，60字节LF完整guard，GetObjectA 60字节SHA同输入，真实非空原branch至45C6CB。
- 原CRT 43指令与business 87静态CFG零诊断。
- 完整CRT/TEB/OSloader尚未完成，整体未达100%。

## 限制与下一步

- 现状锚点：CRT wrapper 506EFA、业务 4F8D50；原 CreateThread caller 未消费句柄/TID。
- host 守卫结束码 A1100000，非原 ThreadExit；退出路径与原语义不等价。
- 执行模型：单 Unicorn 按序，FS0 有限 SEH 模型，非完整 TEB / OSloader。
- 原 DLL 仅作 guestCPU 使用，绝不走 OS LoadLibrary。
- 原 font 刚到达 45C6CB，非完整 font 储存/选择/绘制/实际 glyph 对照。
- 下一步：沿 CRT 初始化表系统收齐静态对象。
- 贯通 source 线程句柄消费者，补齐业务 loop/事件等待。
- 接入字体选择与实际画音链路。
- 未完成：正常 GameInit/素材 VM 帧、忠实 TJS/fullscheduler/原 shutdown、四版 OT/OTA/OTV/OTR 100%；目标完整保留。
- 本批实际复验通过：原 1EXE/8LPK/3 原 DLL+2 参照 DLL/446 scripts/418 IR/USER.CFG 源哈希。
- 峰值 13 独立 API 仅为实际可用容量，不固定人数；截断不算完成。

## 复现与证据入口

```powershell
Set-Location 'E:\ZCode Workspace\Galgame'
$stage = 'E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\演出链路\R_原版工作线程启动与同步证据_20261014'
Get-Content -Raw "$stage/verify-original-thread-font.txt" | & './工具/python-3.13.12-embed-win32/python.exe' -X utf8 -B - '临时/ISSUE-20261011-02/必须选全新目录名'

# 动态 canonical74/76/77/78 下 original-thread-prefix.json；78 还有 original-static-531188-initializer.json 与 host-fixture-cleanup.json
# 对账六份 sdk-*.json、editor-helper-provenance.json、source-integrity.json、CFG/global xref/batch-review；root 集中批审，APIstop 不等于验收

$recipes = @('verify-shared-thread-sdk.txt','verify-shared-events-sdk.txt','verify-font-sdk.txt')
$pythons = @('E:/Tools/Python/python.exe','./工具/python-3.13.12-embed-win32/python.exe')
foreach ($recipe in $recipes) {
  foreach ($python in $pythons) {
    Get-Content -Raw "$stage/$recipe" | & $python -X utf8 -B -
  }
}
```
