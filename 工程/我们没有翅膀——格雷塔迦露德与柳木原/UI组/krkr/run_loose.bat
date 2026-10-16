@echo off
chcp 936 >nul
rem ============================================================
rem  run_loose.bat  --  UI demo, normal (non-tour) mode
rem  M8 / ISSUE-20260919-11  (UI group)
rem
rem  WHY THIS SCRIPT EXISTS
rem    krkr resolves images only from two candidate names inside the project
rem    folder: "ui/..." and "assets/ui/...".  In the repository layout the
rem    assets live in krkr\assets, which is a SIBLING of the game folder,
rem    so neither candidate can reach them.  This script mirrors the game folder
rem    plus its assets into one run folder (RUN\game\assets) so that
rem    candidate 2 hits, then launches the engine in one double-click.
rem    No bash / no WSL required.
rem
rem    NOTE (measured, 2026-09-19): a non-ASCII project path is NOT the cause of
rem    failure.  Booting straight from the Chinese-named project folder works
rem    (all .tjs load, window opens); only the ASSET lookup fails, for the
rem    sibling-directory reason above.  -assetdir=<abs> did not work.
rem  WHAT IT DOES
rem    1) RUN = <worktree>\<tmp>\ui_run        (ASCII leaf names only)
rem    2) wipe RUN\game and RUN\runtime\savedata
rem    3) copy  krkr\game            -> RUN\game
rem       copy  krkr\assets          -> RUN\game\assets   (asset candidate #2)
rem    4) copy  krkr\runtime         -> RUN\runtime       (if not present yet)
rem    5) delete RUN\game\autotour.txt so the tour does NOT trigger
rem    6) start tvpwin32.exe with RUN\game as the project folder
rem
rem  Close the game window (or press Q) to quit.
rem  Log + screenshots land in  RUN\runtime\savedata\
rem ============================================================

set "UIROOT=%~dp0"
set "WTROOT=%UIROOT%..\..\..\.."
set "RUN=%WTROOT%\ÁÙÊ±\ui_run"
set "SRC=%UIROOT%"

echo [1/6] UI root = %UIROOT%
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
    echo        Copy tvpwin32.exe + license.txt + plugin\ from
    echo        the workspace toolchain into krkr\runtime\ first.
    pause
    exit /b 1
  )
)

rem ------------------------------------------------------------
rem  [4b/6] FORCE-REFRESH runtime\plugin   (ISSUE-20260927-05 / E2)
rem    The runtime copy just above only happens when %RUN%\runtime does NOT exist.
rem    A newly added or updated plugin [layerExDraw.dll = the flowchart link
rem    renderer, shipped in krkr\plugin\] would therefore never reach an
rem    already-existing run dir -> links silently missing.
rem    So copy krkr\plugin\ [layerExDraw.dll + license_layerExDraw.txt] into
rem    RUN\runtime\plugin\ on EVERY run; the engine finds plugins in the exe
rem    dir and its plugin\ subdir.
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

echo [5/6] normal mode: no autotour trigger
if exist "%RUN%\game\autotour.txt" del /q "%RUN%\game\autotour.txt"

echo [6/6] starting engine ...
pushd "%RUN%\runtime"
start "" tvpwin32.exe "%RUN%\game"
popd
echo done. Log: %RUN%\runtime\savedata\krkr.console.log
exit /b 0