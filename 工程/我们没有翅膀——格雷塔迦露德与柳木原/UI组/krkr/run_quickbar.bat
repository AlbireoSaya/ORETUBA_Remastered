@echo off
chcp 936 >nul
rem ============================================================
rem  run_quickbar.bat  --  UI demo, auto-tour with the right-edge
rem  quick bar FORCED EXPANDED (M2 / ISSUE-20260922-28; reshaped in
rem  M37 into a column of round icon badges -- ISSUE-20260923-01)
rem
rem  FILE FORMAT MATTERS (verified the hard way in M35, same rules):
rem    * keep this file in  GBK + CRLF  (same as run_autotour.bat /
rem      run_pressprobe.bat).  cmd.exe reads .bat in the OEM codepage
rem      (936 here): UTF-8 Chinese bytes in a comment break parsing,
rem      and LF-only line endings break it too.
rem    * the flag values go into a GENERATED .tjs flag file, NOT a
rem      command-line argument: on this krkrz 1.4.0.8 build the
rem      script cannot read command-line args at all (measured in M35:
rem      -autotour=1 is echoed as a declared setting but
rem      System.getArgument() returns void).  Flag files are the only
rem      working external switch here (autotour.txt uses the same
rem      mechanism).
rem
rem  What it does:
rem    mirrors game/ + assets/ + runtime/ into %RUN% (its own run dir,
rem      so it never collides with run_autotour.bat), writes
rem        %RUN%\game\quick_flags.tjs
rem      containing the UIScrFlagForce overrides below, plus
rem      autotour.txt, then launches the engine.  startup.tjs
rem      (uiInitQuickFlags) sees quick_flags.tjs and execs it, so the
rem      tour screenshots show the quick bar EXPANDED.  Measured drawn
rem      element counts (the [UI][TOUR] log prints the same number;
rem      the recompute script is named in README_运行方式.md, section 8):
rem        collapsed (default)                  =  0   nothing is drawn
rem        expanded, pin ON  (qbar_pin = 1)     = 27   12 round icon
rem                                                     badges + 12 item
rem                                                     hotspots + 1 name
rem                                                     pill + 1 white
rem                                                     label + 1 pin
rem                                                     overlay
rem        expanded, pin OFF (qbar_pin empty)   = 26   drop the pin overlay
rem    The auto-collapse countdown is suppressed while the flag is
rem      forced (see uiScreenRevealTick), so the expanded state is
rem      stable for the whole tour even without mouse movement.
rem
rem  Usage:
rem    run_quickbar.bat
rem
rem  Output: %RUN%\runtime\savedata\
rem     krkr.console.log        grep for [UI][QBAR] / [UI][ATTACH]
rem     shot_NN_<screen>.png    shot_*_quickbar.png = the expanded column
rem ============================================================

set "UIROOT=%~dp0"
set "WTROOT=%UIROOT%..\..\..\.."
set "RUN=%WTROOT%\临时\ui_run_quickbar"
set "SRC=%UIROOT%"

echo [1/7] run dir = %RUN%

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
    rem NOTE: no "pause" here on purpose -- this script is meant for
    rem UNATTENDED runs; a pause would hang forever with nobody there.
    exit /b 1
  )
)

echo [5/7] writing the forced-flag file (quick_flags.tjs) ...
> "%RUN%\game\quick_flags.tjs" echo UIScrFlagForce["quickbar"] = "expanded"; UIScrFlagForce["qbar_tip"] = "lock"; UIScrFlagForce["qbar_pin"] = "1";

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
