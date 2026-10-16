@echo off
chcp 936 >nul
rem ============================================================
rem  play.bat -- launch the assembled game (programming group).
rem  ASCII + CRLF; fully-qualified %~dp0 so cmd.exe (OEM 936)
rem  cannot mis-read this file.
rem ============================================================
set "HERE=%~dp0"
if not exist "%HERE%build\runtime\tvpwin32.exe" (
  echo [ERR] game exe not found - assemble first, then retry.
  pause
  exit /b 1
)
start "" "%HERE%build\runtime\tvpwin32.exe" "%HERE%build\game"
exit /b 0
