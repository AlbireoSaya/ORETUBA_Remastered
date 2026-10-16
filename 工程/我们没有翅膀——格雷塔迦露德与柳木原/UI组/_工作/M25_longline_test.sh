#!/bin/bash
# M25 · 正文区「最长真实台词」实机排版验证（**只改 临时 运行副本，不碰 krkr/game 源文件**）
#   把 113 字的最长语料行塞进运行副本的 ui_demo_script.tjs 第 1 条，跑一遍看是否 4 行内不溢出。
set -u
RUN="E:/ZCode Workspace/Galgame/临时/ui_run_m25_long"
UI="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EVID="$UI/_工作/M25_证据"
mkdir -p "$EVID"

rm -rf "$RUN"; mkdir -p "$RUN"
cp -r "$UI/krkr/game" "$RUN/game"
cp -r "$UI/krkr/assets" "$RUN/game/assets"
cp -r "$UI/krkr/runtime" "$RUN/runtime" 2>/dev/null || \
  cp -r "E:/ZCode Workspace/Galgame/工具/krkrz/krkrz_20171225" "$RUN/runtime"
rm -f "$RUN/runtime/savedata/"*.log "$RUN/runtime/savedata/"*.txt "$RUN/runtime/savedata/"*.png 2>/dev/null
printf 'autotour' > "$RUN/game/autotour.txt"

# 只改运行副本：第 1 条台词换成 113 字最长行（语料原文，未自造）
PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/ui_demo_script.tjs" "$RUN/game/ui_dialog.tjs" <<'PY'
import io, sys, re
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
long_line = "隼人被店员领着走进ＶＩＰ包房。在那里等着的人跟翔一点也不像。然而他正是率领火烈鸟的凤凰寺翔本人。他有着两张面孔。隼人把大主教的事告诉了他，翔却早已掌握。翔姑且道了声谢，隼人便离开了那里。翔最后说：“下次来聊聊我们自己的事吧。”"
m = re.search(r'var UIDemoText\s*=\s*\["(.*?)"\];', s, re.S)
assert m, "UIDemoText 未找到"
s = s[:m.start()] + 'var UIDemoText     = ["%s"];' % long_line + s[m.end():]
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched UIDemoText[0] len =", len(long_line))

# 让打字机一次显示完（UIDlgCharStep=9999），使导出帧为「整行已显示」状态，
# 才能验证**完整文本**的折行行数（否则导出的是打字中途的部分文本）
p2 = sys.argv[2]
s2 = io.open(p2, encoding="utf-8").read()
s2b = s2.replace("var UIDlgCharStep    = 1;", "var UIDlgCharStep    = 9999;")
assert s2b != s2, "UIDlgCharStep 未替换"
io.open(p2, "w", encoding="utf-8", newline="\n").write(s2b)
print("patched UIDlgCharStep -> 9999")
PY

cd "$RUN/runtime"
./tvpwin32.exe "$RUN/game" > "$EVID/stdout_long.txt" 2>&1 &
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
echo "EXIT=$?"
cp "$RUN"/runtime/savedata/shot_03_dialog.png "$EVID/M25_dialog_longline.png" 2>/dev/null
cp "$RUN"/runtime/savedata/krkr.console.log "$EVID/console_long.raw.log" 2>/dev/null
for pid in $(powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='tvpwin32.exe'\" | Where-Object { \$_.CommandLine -like '*ui_run_m25_long*' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r'); do
  taskkill //PID "$pid" //F >/dev/null 2>&1 && echo "killed $pid"
done
ls -la "$EVID/M25_dialog_longline.png" 2>/dev/null || echo "!! 未导出 dialog 图"
echo DONE