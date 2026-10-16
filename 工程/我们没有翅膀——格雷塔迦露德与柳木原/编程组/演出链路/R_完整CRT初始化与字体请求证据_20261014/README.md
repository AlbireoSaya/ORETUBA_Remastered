## 2026-10-14完整Cinit

证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_完整CRT初始化与字体请求证据_20261014。

原506FC8→5070CE按原表顺序执行4个C与110个C++非零入口，共114，Cinit整体返回；C[5281C0,5281D4)、C++[528000,5281BC)。89完整冷Cinit；90–95在原parent ctor前执行，撤去两手动C++入口与40E180补丁。15自有SDK精确候选，32/64位metrics、realloc移动/同址扩页/冲突拒绝、timer已实测；OS成功后不能伪造回滚。真实timeGetTime/BeginPeriod1ms，EndPeriod清理。非完整EXE CRT启动/OSloader/TEB，coreheap/TLS仍有限fixture。source-integrity.json实际复验通过EXE1/LPK8/DLL3+参考2/446脚本/418IR/111byte原USER.CFG。

## 2026-10-14 字体请求与严格停点

证据路径：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_完整CRT初始化与字体请求证据_20261014。

三原字体对象531188/533240/5332A4，cp932 face依次ＭＳ ゴシック(-14,400)、ＭＳ Ｐゴシック(-16,700)、ＭＳ ゴシック(-19,400)，charset128 quality3。源45C719真实metrics给第一ascent12，对象531188的+20B0/+20B4=[0,12]；第三height19/ascent16/descent3。

实际ACP936，第一A接口选MS PGothic；受控cp932→W选MS Gothic；iiii宽12对28，32/64一致。W对照不是日文原OS像素基准，不硬编码metrics。

95捕获MSVC E06D7363，EAdlErrorCode值3，ThrowInfo522F38，调用点492758/返回49275D，尚未dispatch。SOB_INIT.DAT可选探测缺失不能证明错误原因。正常GameInit和四版100%仍未完成。

## 2026-10-14 忠实字体与异常恢复约束

证据：工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_完整CRT初始化与字体请求证据_20261014。

- 原Cinit完整114入口已有原表顺序证据。
- 目标脚本/runtime保留原fontname、编码和metrics计算；禁止把当前ACP936字体回退当原像素golden；受控Unicode对照未等价原日文OS基准。
- 原EAdlErrorCode3调用点492758，返回49275D，尚未dispatch，正常GameInit尚未完成。
- 下一步用既有原MSVC handler/catch/current-head-only unwind，核对worker栈03700000..03720000；不能跳异常或假返回；之后资源archive/VM。
- 当前原版完整性复验已通过。四版本完整100% goal保持active；线程HANDLE消费者、退出/detach、所有路线、像素与声音时序未完成。

# README 复现片段
以下仅用于已授权自有 SDK 派生验证：在工程根目录运行，原 EXE/DLL 仅由 Unicorn 客体执行，不进行 OS 加载。命令未在本单复跑，输出目录须为 临时/ISSUE-20261011-02/ 下尚未存在的新目录。

Get-Content -Raw '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_完整CRT初始化与字体请求证据_20261014/verify-full-Cinit-ADL-caller.txt' | & '.\工具\python-3.13.12-embed-win32\python.exe' -X utf8 -B - '临时/ISSUE-20261011-02/REPLACE_NEW_verify_full_Cinit_ADL_caller'

Get-Content -Raw '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/演出链路/R_完整CRT初始化与字体请求证据_20261014/verify-original-cold-Cinit-timers.txt' | & '.\工具\python-3.13.12-embed-win32\python.exe' -X utf8 -B - '临时/ISSUE-20261011-02/REPLACE_NEW_verify_original_cold_Cinit_timers'

## README 追加
canonical96 在实际 owned worker 执行原 SEH handler 515C60，命中原 EAdlErrorCode3 原 catch 49275D；current-head-only guest RtlUnwind 一次，stack 03700000..03720000。原码随后读取归档 USER_VAR.SOB（3171 压缩 bytes）、FUNC_LIB.SOB（17508 压缩 bytes）。仅证明异常恢复，可选 loose 缺失后有 archive 回退；未证明正常 GameInit 或完整 SOB 发布。2M 指令预算停 4915C3，failure null 亦非退出成功。保留旧 95 未 dispatch 原述，不改写为当前仍未 dispatch。


## README 追加：初始化→恢复→资源→窗口检查

原初始化异常由 catch 恢复，继续四个资源读取（canonical96–99）：canonical97 读 VOICEINF.DAT 归档 932 压缩 bytes；canonical98 确认实际源 `%s%s.SOB` 格式 `RA41BDB9`，旧 version formatter 不支持非原游戏错误；canonical99 复用自有 two-string `wsprintfA` helper，原调用实际返回 15，随后归档读 MAIN.SOB 压缩 3000 bytes。下一 stop import `IsIconic`（hintRVA `12706C`，sourceRA `44DCA8`）；真实已有窗口 guest token `69850000`，尚未调用，不假返回。canonical96/97/98/99 真实 fixture 清理通过、进程退出 0，但不等价原 worker exit/正常 GameInit/画音还原，未称完整绑定正常 VM 或 100%。


## 自有派生事实检查点
本检查点仅记录自有派生元数据，禁止原作与凭据外发。
- 新增三个独立SDK声明：IsIconic、IsWindowEnabled、GetAsyncKeyState；32/64位ABI验证通过，不替代原输入对照。
- canonical100：原IsIconic RA44DCA8在同一真实已显示owned window上查询，实际BOOL为0；global5357E4实际119394432非零，但不能定位为worker写入。
- canonical101：继续GetCursorPos RA44E00D、ClientToScreen RA4A85F1、GetClientRect RA4A85FD，真实guard8/16输出，client[0,0,800,600]；不要宣称画帧。
- 独立同环境调用原native4114D0（selector21）真实返回1，cdecl/CPU/FS0恢复，无global注入；这是独立验证，非GameInit VM调用整链。
- next：sourceOffsetRect，hintRVA127104/sourceRA4A860E，尚未调用。
- 阶段18SDK、原worker完整Exit/parent CreateThread HANDLE消费者、正常VM全画音、忠实TJS、四版100%仍未完成。
所有结论均来自独立验证，不扩范围、不Git、不回退他人。下一步需复核，避免整链误判。
