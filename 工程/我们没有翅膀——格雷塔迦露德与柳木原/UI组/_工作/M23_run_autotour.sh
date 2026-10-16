#!/bin/bash
# M23 实机巡演（独立目录 临时/ui_run_m23，避免与并行模块冲突）
#   用法：bash _工作/M23_run_autotour.sh <tag>
set -u
TAG="${1:-run}"
RUN="E:/ZCode Workspace/Galgame/临时/ui_run_m23"
UI="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EVID="$UI/_工作/M23_证据"
mkdir -p "$EVID"

rm -rf "$RUN"; mkdir -p "$RUN"
cp -r "$UI/krkr/game" "$RUN/game"
cp -r "$UI/krkr/assets" "$RUN/game/assets"
cp -r "$UI/krkr/runtime" "$RUN/runtime" 2>/dev/null || \
  cp -r "E:/ZCode Workspace/Galgame/工具/krkrz/krkrz_20171225" "$RUN/runtime"
rm -f "$RUN/runtime/savedata/"*.log "$RUN/runtime/savedata/"*.txt "$RUN/runtime/savedata/"*.png 2>/dev/null
printf 'autotour' > "$RUN/game/autotour.txt"
ls -la "$RUN/runtime/tvpwin32.exe" >/dev/null || { echo "!! tvpwin32.exe 缺失"; exit 2; }

cd "$RUN/runtime"
START=$(date +%s)
./tvpwin32.exe "$RUN/game" > "$EVID/stdout_$TAG.txt" 2>&1 &
APP_PID=$!
echo "APP_PID=$APP_PID"
for i in $(seq 1 240); do
  kill -0 "$APP_PID" 2>/dev/null || break
  sleep 1
done
if kill -0 "$APP_PID" 2>/dev/null; then
  echo "!! 引擎未自行退出，按 PID 强杀 $APP_PID"
  taskkill //PID "$APP_PID" //F >/dev/null 2>&1
fi
wait "$APP_PID" 2>/dev/null
CODE=$?
END=$(date +%s)
echo "EXIT=$CODE  ELAPSED=$((END-START))s"

if [ -f "$RUN/runtime/savedata/krkr.console.log" ]; then
  cp "$RUN/runtime/savedata/krkr.console.log" "$EVID/console_$TAG.raw.log"
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$EVID/console_$TAG.raw.log" "$EVID/console_$TAG.utf8.log" <<'PY'
import io, sys
raw = open(sys.argv[1], 'rb').read()
txt = None
for enc in ("utf-16-le", "utf-16", "utf-8", "gbk"):
    try:
        c = raw.decode(enc)
        if c.count("\ufffd") == 0 and ("[UI]" in c or "info" in c):
            txt = c; break
    except Exception:
        pass
if txt is None:
    txt = raw.decode("utf-16-le", "replace")
io.open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(txt)
print("decoded console log ->", sys.argv[2], "chars =", len(txt))
PY
fi
rm -rf "$EVID/png_$TAG"; mkdir -p "$EVID/png_$TAG"
cp "$RUN"/runtime/savedata/shot_*.png "$EVID/png_$TAG/" 2>/dev/null
cp "$RUN"/runtime/savedata/ui_flow_state.txt "$EVID/flow_state_$TAG.txt" 2>/dev/null
echo "DONE tag=$TAG png=$(ls "$EVID/png_$TAG" 2>/dev/null | wc -l)"
ls "$EVID/png_$TAG" 2>/dev/null
# 只杀本目录起的引擎实例（按命令行匹配 ui_run_m23，避免误杀并行模块）
for pid in $(powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='tvpwin32.exe'\" | Where-Object { \$_.CommandLine -like '*ui_run_m23*' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r'); do
  taskkill //PID "$pid" //F >/dev/null 2>&1 && echo "killed $pid"
done
echo "KEPT RUN DIR (evidence collected): $RUN"