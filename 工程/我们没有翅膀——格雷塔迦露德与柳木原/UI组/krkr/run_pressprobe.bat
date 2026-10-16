@echo off
chcp 936 >nul
rem ============================================================
rem  run_pressprobe.bat  --  UI demo, auto-tour WITH the
rem  "pressed state" acceptance probe (M35 / ISSUE-20260921-26)
rem
rem  FILE FORMAT MATTERS (both verified the hard way in M35):
rem    * keep this file in  GBK + CRLF  (same as run_autotour.bat).
rem      cmd.exe reads .bat in the OEM codepage (936 here): a UTF-8
rem      Chinese comment breaks parsing (spams "'p' is not recognized"),
rem      and LF-only line endings break it too.
rem    * the probe value goes into a GENERATED .tjs flag file, NOT a
rem      command-line argument: on this krkrz 1.4.0.8 build the script
rem      cannot read command-line args at all (measured: -autotour=1 is
rem      echoed as a declared setting but System.getArgument() returns
rem      void -> "autotour = OFF").  Flag files are the only working
rem      external switch here (autotour.txt uses the same mechanism).
rem
rem  What it does:
rem    mirrors game/ + assets/ + runtime/ into %RUN%, writes
rem      %RUN%\game\press_probe.tjs  containing  UIScrPressProbe = "<id>";
rem    plus autotour.txt, then launches the engine.  startup.tjs
rem    (uiInitPressProbe) sees press_probe.tjs and execs it, so the tour
rem    screenshots show that element in its pressed state.
rem
rem  Usage:
rem    run_pressprobe.bat                        default probe = title.menu_hit_1
rem    set PROBE=title.menu_txt_start  then run_pressprobe.bat
rem    (prior examples "ch.hit_1" / "sysbar.hit_snap" retired 2026-09-23:
rem     ch.hit_1 vanished with the M45f list change, and screen id "sysbar"
rem     was deleted -- its art is kept, see the UI group _work archive.
rem     Per-item list states are covered by the tour "ptr" steps instead:
rem     this probe only takes an element id, not an item index.)
rem
rem  Output: %RUN%\runtime\savedata\
rem     krkr.console.log        grep for [UI][PRESS]
rem     shot_NN_<screen>.png    probed element drawn pressed
rem ============================================================

set "UIROOT=%~dp0"
set "WTROOT=%UIROOT%..\..\..\.."
set "RUN=%WTROOT%\ÁÙÊ±\ui_run_press"
set "SRC=%UIROOT%"

rem   M46: the old default was "ch.hit_1" -- that element was folded into the
rem   "ch.choices" list back in M45f and no longer exists, so the probe drew
rem   nothing.  Per-item list states are covered by the tour "ptr" steps
rem   instead (this probe only takes an element id, not an item index).
if "%PROBE%"=="" set "PROBE=title.menu_hit_1"

echo [1/7] run dir = %RUN%
echo [1/7] probe   = %PROBE%

if not exist "%RUN%" mkdir "%RUN%"

echo [2/7] wiping old copy ...
if exist "%RUN%\game" rd /s /q "%RUN%\game"
if exist "%RUN%\runtime\savedata" del /q "%RUN%\runtime\savedata\*.*" >nul 2>nul

echo [3/7] mirroring game\ ...
xcopy "%SRC%game" "%RUN%\game" /E /I /Y /Q >nul
echo [3/7] mirroring assets\ ...
xcopy "%SRC%assets" "%RUN%\game\assets" /E /I /Y /Q >nul

if not exist "%RUN%\runtime" (
  if exist "%SRC%runtime" (
    echo [4/7] copying runtime ...
    xcopy "%SRC%runtime" "%RUN%\runtime" /E /I /Y /Q >nul
  ) else (
    echo [4/7] ERROR: %SRC%runtime not found.  ABORT.
    rem NOTE: no "pause" here on purpose -- this script is meant for UNATTENDED
    rem runs; a pause would hang forever with nobody at the keyboard.
    exit /b 1
  )
)

echo [5/7] writing the press-probe flag ...
> "%RUN%\game\press_probe.tjs" echo UIScrPressProbe = "%PROBE%";

echo [5/7] enabling auto-tour (project root autotour.txt) ...
echo autotour>"%RUN%\game\autotour.txt"

echo [6/7] starting engine (unattended) ...
pushd "%RUN%\runtime"
start "" tvpwin32.exe "%RUN%\game"
popd

echo [7/7] done. Tour runs about 45 s and exits by itself.
echo When it is gone, inspect:
echo   %RUN%\runtime\savedata\krkr.console.log
echo   %RUN%\runtime\savedata\shot_*.png
exit /b 0
