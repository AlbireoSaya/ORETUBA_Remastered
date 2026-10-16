@echo off
rem 看片尾_肉眼验证.bat —— ISSUE-20261004-07 影片格式肉眼验收（双击即可）
rem 流程：拷播发单到 game\videoplay.tjs -> 启动引擎 -> 关窗口后自动删开关。
rem 判读：黑底上出现画面 = EVR 合在我们层之上（可用于游戏内播放）；
rem       只见黑底 + 顶部一行字 = 被我们的层挡住（集成模型要另设计）。请留意**有没有声音**。
setlocal
set B=%~dp0..
if not exist "%B%\build\game" ( echo [ERR] build\game not found & pause & exit /b 2 )
if not exist "%B%\build\runtime\tvpwin32.exe" ( echo [ERR] engine not found & pause & exit /b 2 )
copy /y "%~dp0videoplay.template.tjs" "%B%\build\game\videoplay.tjs" >nul
cd /d "%B%\build\runtime"
echo 正在启动…（关闭游戏窗口即结束；三支片尾每 14 秒轮换一支）
start "" /wait tvpwin32.exe "%B%\build\game"
del "%B%\build\game\videoplay.tjs" 2>nul
endlocal
