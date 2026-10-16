@echo off
chcp 936 >nul
rem ============================================================
rem  run_autotour.bat  --  UI demo, unattended auto-tour mode
rem  M8 / ISSUE-20260919-11  (UI group)
rem
rem  Same mirroring as run_loose.bat, but it also drops autotour.txt
rem  into the mirrored project root.  startup.tjs detects the tour in
rem  three ways, in this order:
rem     1) command line  -autotour=1
rem     2) <datapath>\autotour.flag
rem     3) project root  autotour.txt        <-- used here
rem
rem  The tour walks the screen list (title -> dialog -> choices -> sysicons
rem  -> save -> load -> config -> backlog -> gallery -> music -> fragment ->
rem  flowchart -> ending -> loading -> title, then any extra
rem  screen registered in the layout), 2 s per screen, then quits by itself.
rem
rem  Output (all under RUN\runtime\savedata\):
rem     krkr.console.log   UTF-16LE log, one [UI][TOUR] line per screen
rem     shot_NN_<screen>.png   one PNG per screen (off-screen export)
rem     ui_state.txt / ui_flow_state.txt
rem
rem  Expected runtime: about 45 seconds for 19 screens.
rem
rem  ------------------------------------------------------------
rem   [NEW - ISSUE-20260928-02 第 2 步] 可选参数 1 = 强制流程图层
rem     usage:  run_autotour.bat            (无参：不强制)
rem             run_autotour.bat frag1      (强制 fc_layer=frag1 -> 番外独立层截图)
rem     做法：写 RUN\game\quick_flags.tjs，内容
rem               UIScrFlagForce["fc_layer"] = "<arg>";
rem           startup.tjs 的 uiInitQuickFlags() 用项目根 flag 文件机制执行它（本轮实测
rem           唯一可用的外部开关），在 flags_default 之后套用 => 换屏也保留；日志会打
rem           `[UI][QBAR] quickflags 已生效： fc_layer='frag1'`。
rem     为什么需要它：番外独立层的「零点击截图」要由**屏级 flag 机制**给出（不靠脚本
rem           伪造状态）；再由巡演的 flowclick 步骤点「返回主干」切回 main 取第二张。
rem     注意：文件写在**运行目录的镜像工程根**里，源码树的 game\ 不会被污染
rem           （每次运行 [2/6] 会 rd /s /q 清掉镜像，源树本来也没有该文件）。
rem  ------------------------------------------------------------
rem ============================================================

set "UIROOT=%~dp0"
set "WTROOT=%UIROOT%..\..\..\.."
set "RUN=%WTROOT%\临时\ui_run"
set "SRC=%UIROOT%"

echo [1/6] run dir = %RUN%

if not exist "%RUN%" mkdir "%RUN%"

echo [2/6] wiping old copy ...
if exist "%RUN%\game" rd /s /q "%RUN%\game"
if exist "%RUN%\runtime\savedata" del /q "%RUN%\runtime\savedata\*.*" >nul 2>nul

if not exist "%RUN%\runtime" (
  if exist "%SRC%runtime" (
    echo [4/6] copying runtime ...
    xcopy "%SRC%runtime" "%RUN%\runtime" /E /I /Y /Q >nul
  ) else (
    echo [4/6] ERROR: %SRC%runtime not found.
    pause
    exit /b 1
  )
)

rem ------------------------------------------------------------
rem  [4b/6] FORCE-REFRESH runtime\plugin   (ISSUE-20260927-05 / E2)
rem    The runtime copy just above only happens when %RUN%\runtime does NOT exist.
rem    A newly added or updated plugin [layerExDraw.dll = the flowchart link
rem    renderer, shipped in krkr\plugin\] would therefore never reach an
rem    already-existing run dir -> links silently missing in the tour.
rem    So copy krkr\plugin\ [layerExDraw.dll + license_layerExDraw.txt] into
rem    RUN\runtime\plugin\ on EVERY run. The engine finds plugins in the exe
rem    dir and its plugin\ subdir, so this is the load path that matters.
rem    NOTE: no parentheses in the echo lines below - an unescaped ")" inside
rem    an "if ( ... )" block terminates the block and breaks the script.
rem ------------------------------------------------------------
if exist "%SRC%plugin" (
  echo [4b/6] force-refreshing runtime\plugin - layerExDraw.dll ...
  xcopy "%SRC%plugin" "%RUN%\runtime\plugin" /E /I /Y /Q >nul
) else (
  echo [4b/6] WARNING: %SRC%plugin not found - flowchart links will not render.
)

echo [3/6] mirroring game\ ...
xcopy "%SRC%game" "%RUN%\game" /E /I /Y /Q >nul
echo [3/6] mirroring assets\ ...
xcopy "%SRC%assets" "%RUN%\game\assets" /E /I /Y /Q >nul

echo [5/6] enabling auto-tour (project root autotour.txt) ...
echo autotour>"%RUN%\game\autotour.txt"

rem ------------------------------------------------------------
rem  [5b/6] optional forced flowchart layer (ISSUE-20260928-02 第 2 步)
rem    arg1 非空 => 写 quick_flags.tjs（UIScrFlagForce["fc_layer"]=<arg1>）。
rem    无参 => 什么都不做（行为与改动前一致）。
rem    NOTE: no parentheses inside the echo lines (an unescaped ")" would close
rem          the if-block), and the redirect goes first so cmd does not echo it.
rem ------------------------------------------------------------
if not "%~1"=="" (
  echo [5b/6] forcing flowchart layer fc_layer=%~1 via quick_flags.tjs ...
  >"%RUN%\game\quick_flags.tjs" echo UIScrFlagForce["fc_layer"] = "%~1";
) else (
  echo [5b/6] no forced flowchart layer - quick_flags.tjs not written.
)

echo [6/6] starting engine (unattended) ...
pushd "%RUN%\runtime"
start "" tvpwin32.exe "%RUN%\game"
popd
echo.
echo Tour runs ~45 s and then exits by itself.
echo When it is gone, inspect:
echo   %RUN%\runtime\savedata\krkr.console.log
echo   %RUN%\runtime\savedata\shot_*.png
exit /b 0