#!/bin/bash
# M20 实机巡演（独立目录 临时/ui_run_m20，避免与并行模块冲突）
#   用法：bash M20_run_autotour.sh <tag> [patchmode]
#     tag       —— 证据文件名后缀
#     patchmode —— 留空 = 原样跑（仓库内文件一字不动）
#                  hover = 在**临时副本**的 startup.tjs 里注入悬停探针：
#                          标题屏导出 shot（常态）后，强制 uiScreenHoverUpdate(1704,232)
#                          → redraw → 另存 hover_probe_title.png（金色悬停态）→ 复原。
#                          用来证明 hover 通路（命中判定 + ctx.hoverHit + 画 hover 图）成立。
#   说明：**只在 临时/ui_run_m20 的副本里**做任何改动，仓库内文件一字不动。
set -u
TAG="${1:-run}"
PATCH="${2:-}"
RUN="E:/ZCode Workspace/Galgame/临时/ui_run_m20"
UI="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EVID="$UI/_工作/M20_证据"
mkdir -p "$EVID"

rm -rf "$RUN"; mkdir -p "$RUN"
cp -r "$UI/krkr/game" "$RUN/game"
cp -r "$UI/krkr/assets" "$RUN/game/assets"
cp -r "$UI/krkr/runtime" "$RUN/runtime" 2>/dev/null || \
  cp -r "E:/ZCode Workspace/Galgame/工具/krkrz/krkrz_20171225" "$RUN/runtime"
rm -f "$RUN/runtime/savedata/"*.log "$RUN/runtime/savedata/"*.txt "$RUN/runtime/savedata/"*.png 2>/dev/null
printf 'autotour' > "$RUN/game/autotour.txt"
ls -la "$RUN/runtime/tvpwin32.exe" >/dev/null || { echo "!! tvpwin32.exe 缺失"; exit 2; }

if [ "$PATCH" = "hover" ]; then
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/startup.tjs" <<'PY'
import io, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
anchor = '''		Debug.message(uiTourLogLine(uiTourPlanLabel(), drawn));
		if(UI_TOUR_PNG) this.exportPng(uiScreenCurrent(), tourLogged);'''
assert anchor in t, "锚点未找到"
probe = '''		Debug.message(uiTourLogLine(uiTourPlanLabel(), drawn));
		// ===== [M20 HOVER PROBE] 仅证据运行（临时副本） =====
		if(uiScreenCurrent() == "title")
		{
			try
			{
				Debug.message("[UI][HOVERPROBE] 空白点 960,540 命中 = ["
					+ uiScreenHoverAt(960, 540) + "]（期望空串）");
				Debug.message("[UI][HOVERPROBE] 菜单1中心 1704,232 命中 = ["
					+ uiScreenHoverAt(1704, 232) + "]（期望 title.menu_hit_1）");
				var hpChanged = uiScreenHoverUpdate(1704, 232);
				Debug.message("[UI][HOVERPROBE] uiScreenHoverUpdate -> changed=" + hpChanged
					+ " | hoverHit=[" + UIScrHoverHit + "] | " + UIScrHoverMsg);
				this.redraw();
				var hbmp = new Bitmap();
				stageLayer.copyToBitmapFromMainImage(hbmp);
				hbmp.save("" + Debug.logLocation + "hover_probe_title.png", "png");
				Debug.message("[UI][HOVERPROBE] 已导出 hover_probe_title.png（悬停态）");
				uiScreenHoverClear();
				this.redraw();
			}
			catch(e){ Debug.message("[UI][HOVERPROBE][ERR] " + e.message); }
		}
		// ===== [M20 HOVER PROBE END] =====
		if(UI_TOUR_PNG) this.exportPng(uiScreenCurrent(), tourLogged);'''
t = t.replace(anchor, probe, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("PATCHED startup.tjs (temp copy only) -> hover probe injected")
PY
fi

cd "$RUN/runtime"
START=$(date +%s)
./tvpwin32.exe "$RUN/game" > "$EVID/stdout_$TAG.txt" 2>&1 &
APP_PID=$!
for i in $(seq 1 220); do
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
cp "$RUN"/runtime/savedata/hover_probe_title.png "$EVID/png_$TAG/" 2>/dev/null
cp "$RUN"/runtime/savedata/ui_flow_state.txt "$EVID/flow_state_$TAG.txt" 2>/dev/null
echo "DONE tag=$TAG png=$(ls "$EVID/png_$TAG" 2>/dev/null | wc -l)"
# 只杀本目录起的引擎实例（避免误杀并行模块的引擎）
for pid in $(powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='tvpwin32.exe'\" | Where-Object { \$_.CommandLine -like '*ui_run_m20*' } | Select-Object -ExpandProperty ProcessId" 2>/dev/null | tr -d '\r'); do
  taskkill //PID "$pid" //F >/dev/null 2>&1 && echo "killed $pid"
done
rm -rf "$RUN"
echo "CLEANED"