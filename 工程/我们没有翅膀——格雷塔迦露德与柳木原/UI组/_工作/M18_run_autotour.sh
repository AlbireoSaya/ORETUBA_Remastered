#!/bin/bash
# M18 实机巡演（独立目录 临时/ui_run_m18，避免与 M17 冲突）
#   用法：bash M18_run_autotour.sh <tag> [patchmode]
#     tag       —— 证据文件名后缀（如 repro / fixed）
#     patchmode —— 留空 = 原样跑（仓库内文件一字不动）
#                  nopng = 只在临时副本里关掉 PNG 导出（隔离 M2 exportPng 干扰）
# 说明：**只在 临时/ui_run_m18 的副本里**做任何改动，仓库内文件一字不动。
set -u
TAG="${1:-run}"
PATCH="${2:-}"
RUN="E:/ZCode Workspace/Galgame/临时/ui_run_m18"
UI="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EVID="$UI/_工作/M18_证据"
mkdir -p "$EVID"

rm -rf "$RUN"; mkdir -p "$RUN"
cp -r "$UI/krkr/game" "$RUN/game"
cp -r "$UI/krkr/assets" "$RUN/game/assets"
cp -r "$UI/krkr/runtime" "$RUN/runtime" 2>/dev/null || \
  cp -r "E:/ZCode Workspace/Galgame/工具/krkrz/krkrz_20171225" "$RUN/runtime"
rm -f "$RUN/runtime/savedata/"*.log "$RUN/runtime/savedata/"*.txt "$RUN/runtime/savedata/"*.png 2>/dev/null
printf 'autotour' > "$RUN/game/autotour.txt"
ls -la "$RUN/runtime/tvpwin32.exe" >/dev/null || { echo "!! tvpwin32.exe 缺失"; exit 2; }

if [ "$PATCH" = "nopng" ]; then
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/startup.tjs" <<'PY'
import io, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
t2 = t.replace("var UI_TOUR_PNG        = true;", "var UI_TOUR_PNG        = false;")
io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
print("PATCHED startup.tjs (temp copy only) UI_TOUR_PNG true->false :", t != t2)
PY
fi

# stress：把巡演步骤表换成「dialog 上反复右键呼出/收起」，专打浮层 push/pop + 转场路径
# stressfast：同上，并把巡演节拍压到 250ms（< 420ms 转场时长）→ 让相邻两次转场**重叠**，
#             模拟用户快速连按右键的真实情形
if [ "$PATCH" = "stress" ] || [ "$PATCH" = "stressfast" ]; then
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/ui_screens.tjs" <<'PY'
import io, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
a = t.index("var UIScrTourSteps = [")
b = t.index("];", a) + 2
steps = ['%[ kind: "screen", v: "dialog",    label: "对话框" ],']
for i in range(12):
    steps.append('%[ kind: "mouse",  v: "right",     label: "压力右键 呼出 #' + str(i+1) + '" ],')
    steps.append('%[ kind: "mouse",  v: "right",     label: "压力右键 收起 #' + str(i+1) + '" ],')
steps[-1] = steps[-1][:-1]   # ★ TJS2 坑：数组字面量的**尾随逗号会产生一个 void 槽**，必须去掉
t = t[:a] + 'var UIScrTourSteps = [\n\t' + '\n\t'.join(steps) + '\n];' + t[b:]
t = t.replace("\tfor(var n = 0; n < extra.count; n++) plan.push(extra[n]);\n",
              "\t// M18 stress 模式：不追加未列屏\n")
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("PATCHED ui_screens.tjs (temp copy only) -> stress: 12 x (right-push/right-pop)")
PY
fi

if [ "$PATCH" = "stressfast" ]; then
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/startup.tjs" <<'PY'
import io, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
t2 = t.replace("var UI_TOUR_STEP_MS    = 2000;", "var UI_TOUR_STEP_MS    = 250;")
io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
print("PATCHED startup.tjs (temp copy only) UI_TOUR_STEP_MS 2000->250 :", t != t2)
PY
fi

# flowfocus：只跑流程图（含「前往一个可前往节点」以验证三态着色 + 当前节点标记）
if [ "$PATCH" = "flowfocus" ]; then
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/ui_screens.tjs" <<'PY'
import io, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
a = t.index("var UIScrTourSteps = [")
b = t.index("];", a) + 2
steps = [
    '%[ kind: "screen", v: "dialog",    label: "对话框" ],',
    '%[ kind: "action", v: "open_flowchart", label: "打开流程图（单屏总览）" ],',
    '%[ kind: "action", v: "flow_node_N03", label: "前往 N03（验证三态着色 + 当前节点标记）" ],',
    '%[ kind: "action", v: "page_next", label: "PageNext（单屏下应为惰性、不吞键）" ],',
    '%[ kind: "screen", v: "title",     label: "回到标题" ],',
]
steps[-1] = steps[-1][:-1]
t = t[:a] + 'var UIScrTourSteps = [\n\t' + '\n\t'.join(steps) + '\n];' + t[b:]
t = t.replace("\tfor(var n = 0; n < extra.count; n++) plan.push(extra[n]);\n",
              "\t// M18 flowfocus 模式：不追加未列屏\n")
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("PATCHED ui_screens.tjs (temp copy only) -> flowfocus")
PY
fi

# clickstress：右键呼出后**用左键点击浮层**收起（走 handleClick 的 sysicons 分支）——
#              这是巡演原本完全没覆盖的路径（"右键→close"的真实含义）
# clickraw   ：同上，但合成左键**不加 try/catch**，让异常原样冒进引擎事件分发
#              —— 用来判定「点击路径里的未捕获 TJS 异常」会不会把引擎打死
if [ "$PATCH" = "clickstress" ] || [ "$PATCH" = "clickraw" ]; then
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/ui_screens.tjs" "$PATCH" <<'PY'
import io, sys
p, mode = sys.argv[1], sys.argv[2]
t = io.open(p, encoding="utf-8").read()
a = t.index("var UIScrTourSteps = [")
b = t.index("];", a) + 2
steps = ['%[ kind: "screen", v: "dialog",    label: "对话框" ],']
for i in range(12):
    steps.append('%[ kind: "mouse",  v: "right",  label: "右键呼出 #' + str(i+1) + '" ],')
    steps.append('%[ kind: "lclick", v: "center", label: "左键点浮层收起 #' + str(i+1) + '" ],')
steps[-1] = steps[-1][:-1]
t = t[:a] + 'var UIScrTourSteps = [\n\t' + '\n\t'.join(steps) + '\n];' + t[b:]
t = t.replace("\tfor(var n = 0; n < extra.count; n++) plan.push(extra[n]);\n",
              "\t// M18 %s 模式：不追加未列屏\n" % mode)
body = 'UIScrMouseSink.handleClick(cx, cy);'
if mode == "clickstress":
    body = 'try { UIScrMouseSink.handleClick(cx, cy); }\n\tcatch(e) { Debug.message("[UI][MOUSE] 合成左键点击 EXCEPTION：" + e.message); }'
t = t.replace('''	else if(st.kind == "mouse")     // ★ M13：合成鼠标事件（走 onMouseDown 同一入口）
	{
		note = uiScreenSyntheticMouse(st.v);
	}''',
'''	else if(st.kind == "mouse")     // ★ M13：合成鼠标事件（走 onMouseDown 同一入口）
	{
		note = uiScreenSyntheticMouse(st.v);
	}
	else if(st.kind == "lclick")    // ★ M18：合成左键点击（走 handleClick 同一入口）
	{
		note = uiScreenSyntheticClick();
	}''')
t = t.replace('''function uiScreenDraw(stage)
{''',
'''// ★ M18：合成左键点击 —— 引擎对左键在 WM_LBUTTONUP 发 onClick（environ/win32/TVPWindow.cpp:95），
//   这里直接调窗口的 handleClick，即 onClick 内部分派到的**同一个入口**。
function uiScreenSyntheticClick()
{
	var cx = Math.floor(uiThemeCanvasW() / 2);
	var cy = Math.floor(uiThemeCanvasH() / 2);
	if(UIScrMouseSink === null || UIScrMouseSink === void)
		return "窗口未登记，合成左键点击跳过";
	Debug.message("[UI][MOUSE] 合成左键点击（巡演）at " + cx + "," + cy + " —— 走 handleClick 同一入口");
	UIScrSynthMouse = true;
	''' + body + '''
	UIScrSynthMouse = false;
	return "合成左键点击 -> 当前屏 " + uiScreenCurrent();
}

function uiScreenDraw(stage)
{''')
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("PATCHED ui_screens.tjs (temp copy only) -> %s: 12 x (right-open / left-click-close)" % mode)
PY
fi

cd "$RUN/runtime"
START=$(date +%s)
./tvpwin32.exe "$RUN/game" > "$EVID/stdout_$TAG.txt" 2>&1
CODE=$?
END=$(date +%s)
echo "EXIT=$CODE  ELAPSED=$((END-START))s"

if [ -f "$RUN/runtime/savedata/krkr.console.log" ]; then
  cp "$RUN/runtime/savedata/krkr.console.log" "$EVID/console_$TAG.raw.log"
  # 引擎按 UTF-16LE 写日志；用 Python 解码（iconv 在本机 shell 下会二次编码，故不用）
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
# 只杀本目录起的引擎实例（避免误杀并行模块 M17 的进程）
for pid in $(powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='tvpwin32.exe'\" | Where-Object { \$_.CommandLine -like '*ui_run_m18*' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r'); do
  taskkill //PID "$pid" //F >/dev/null 2>&1 && echo "killed $pid"
done
rm -rf "$RUN"
echo "CLEANED"