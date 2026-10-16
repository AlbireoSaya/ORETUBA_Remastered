@echo off
chcp 936 >nul
rem ============================================================
rem  run_reach_assert.bat  --  M2 reachability assertion (B4), rerunnable
rem  ISSUE-20260922-28
rem
rem  What it does (mirrors run_quickbar.bat, but installs the assertion
rem  harness instead of the forced-flag file, and does NOT write
rem  autotour.txt, so the auto-tour never starts):
rem      mirror krkr\game + krkr\assets  ->  %RUN%\game
rem      copy  reach_assert_quickbar.tjs ->  %RUN%\game\quick_flags.tjs
rem            (startup.tjs's uiInitQuickFlags() execs it, same mechanism
rem             as press_probe.tjs)
rem      launch tvpwin32.exe
rem
rem  FILE FORMAT MATTERS: keep this file GBK + CRLF (cmd.exe reads .bat in
rem  the OEM codepage 936; a UTF-8 Chinese byte or an LF-only line ending
rem  breaks parsing).  The only non-ASCII bytes here are the 2 chars of
rem  the 临时 path segment, same as the other project bats.
rem
rem  Read results in:
rem    %RUN%\runtime\savedata\krkr.console.log   (UTF-16LE)  grep [REACH]
rem    expect the last line: ===== 断言结束：PASS n / FAIL 0 =====
rem
rem  Usage:  cd <UI组>\_工作\ISSUE-20260922-28_M2_证据  &&  run_reach_assert.bat
rem ============================================================

set "EV=%~dp0"
set "UIROOT=%~dp0..\..\krkr\"
set "WTROOT=%UIROOT%..\..\..\.."
set "RUN=%WTROOT%\临时\ui_run_quickbar"
set "SRC=%UIROOT%"

echo [1/5] run dir = %RUN%

if not exist "%RUN%\runtime" (
  echo [1/5] ERROR: %RUN%\runtime 不存在，先跑一次 krkr\run_quickbar.bat 建立运行副本。ABORT.
  exit /b 1
)

echo [2/5] wiping old copy ...
if exist "%RUN%\game" rd /s /q "%RUN%\game"
if exist "%RUN%\runtime\savedata" del /q "%RUN%\runtime\savedata\*.*" >nul 2>nul

echo [3/5] mirroring game\ + assets\ ...
xcopy "%SRC%game" "%RUN%\game" /E /I /Y /Q >nul
xcopy "%SRC%assets" "%RUN%\game\assets" /E /I /Y /Q >nul

echo [4/5] installing the assertion harness as game\quick_flags.tjs ...
copy /Y "%EV%reach_assert_quickbar.tjs" "%RUN%\game\quick_flags.tjs" >nul
if errorlevel 1 (
  echo [4/5] ERROR: harness copy failed. ABORT.
  exit /b 1
)

echo [5/5] starting engine (unattended, no autotour.txt) ...
pushd "%RUN%\runtime"
start "" tvpwin32.exe "%RUN%\game"
popd
echo done.  The assertion runs ~6 s and the engine quits itself.
echo log: %RUN%\runtime\savedata\krkr.console.log   (grep [REACH])
exit /b 0
