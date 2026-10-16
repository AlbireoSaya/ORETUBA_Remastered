#!/bin/bash
# M14 实机巡演：跑 krkr 自动巡演 → 收集日志与 PNG → 清理临时目录
#   用法：bash M14_run_autotour.sh [full|focus]
#     full  —— 完整巡演（保留原步骤表，仅去掉 M13 的 sysicons 合成鼠标两步）
#     focus —— 只跑 M14 三屏（gallery → fragment → flowchart + 滚动），并禁用「未列屏自动追加」
#   两种模式都**只在 临时\ui_run 的副本**里改 ui_screens.tjs，仓库内文件一字不动。
set -u
MODE="${1:-full}"
RUN="E:/ZCode Workspace/Galgame/临时/ui_run"
UI="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EVID="$UI/_工作/M14_证据"

taskkill //IM tvpwin32.exe //F >/dev/null 2>&1
sleep 1
rm -rf "$RUN"; mkdir -p "$RUN"
cp -r "$UI/krkr/game" "$RUN/game"
cp -r "$UI/krkr/assets" "$RUN/game/assets"
cp -r "$UI/krkr/runtime" "$RUN/runtime" 2>/dev/null || \
  cp -r "E:/ZCode Workspace/Galgame/工具/krkrz/krkrz_20171225" "$RUN/runtime"
rm -f "$RUN/runtime/savedata/"*.log "$RUN/runtime/savedata/"*.txt "$RUN/runtime/savedata/"*.png 2>/dev/null
printf 'autotour' > "$RUN/game/autotour.txt"
ls -la "$RUN/runtime/tvpwin32.exe" >/dev/null || { echo "!! tvpwin32.exe 缺失"; exit 2; }

# ── 只在临时副本上裁剪巡演步骤表 ───────────────────────────────────
PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/ui_screens.tjs" "$MODE" <<'PY'
import io, sys
p, mode = sys.argv[1], sys.argv[2]
t = io.open(p, encoding="utf-8").read()
# ① 去掉 M13 的 sysicons 合成鼠标两步（该屏收起浮层时会让引擎静默退出，见 M14 报告）
t = t.replace('\t%[ kind: "mouse",  v: "right",     label: "合成右键：呼出 9 图标浮层" ],\n', "")
t = t.replace('\t%[ kind: "mouse",  v: "right",     label: "合成右键：收起 9 图标浮层" ],\n', "")
# ② 在 M14 相关步骤后插入验证动作
t = t.replace('\t%[ kind: "action", v: "open_fragment",  label: "番外 Fragment 占位" ],\n',
              '\t%[ kind: "action", v: "open_fragment",  label: "番外 Fragment 占位" ],\n'
              '\t%[ kind: "action", v: "fragment_enter", label: "M14：进入番外第 1 格（进度+持久化验证）" ],\n')
t = t.replace('\t%[ kind: "action", v: "open_flowchart", label: "剧情流程图占位" ],\n',
              '\t%[ kind: "action", v: "open_flowchart", label: "剧情流程图占位" ],\n'
              '\t%[ kind: "action", v: "page_next", label: "M14：流程图下翻一屏（纵向滚动验证）" ],\n')
if mode == "focus":
    # ③ 把步骤表整体换成 M14 三屏（减少 PNG 导出次数 → 规避 M2 exportPng 的偶发静默退出）
    a = t.index("var UIScrTourSteps = [")
    b = t.index("];", a) + 2
    t = t[:a] + (
        'var UIScrTourSteps = [\n'
        '\t%[ kind: "screen", v: "gallery",   label: "CG 画廊（M14）" ],\n'
        '\t%[ kind: "screen", v: "fragment",  label: "番外 Fragment（M14）" ],\n'
        '\t%[ kind: "action", v: "fragment_enter", label: "M14：进入番外第 1 格" ],\n'
        '\t%[ kind: "screen", v: "flowchart", label: "剧情流程图（M14）" ],\n'
        '\t%[ kind: "action", v: "page_next", label: "M14：流程图下翻一屏" ],\n'
        '\t%[ kind: "screen", v: "title",     label: "回到标题" ]\n'
        '];'
    ) + t[b:]
    # ④ 禁用「未列屏自动追加」
    t = t.replace("\tfor(var n = 0; n < extra.count; n++) plan.push(extra[n]);\n",
                  "\t// M14 focus 模式：不追加未列屏\n")
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("PATCHED ui_screens.tjs (temp copy only), mode =", mode)
PY

if [ "$MODE" = "focus" ]; then
  # 临时把「演示占位播种格」从 c0 改到 c5（**只在临时副本里**）：
  #   这样巡演的 fragment_enter(index=0) 对 c0 是**首次进入** → 会走
  #   uiFlowSaveState() 持久化，状态文件里能看到 collected=c0 的落盘证据；
  #   同时 c5 仍带「已收集」环，收集态在截图里可见。
  PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs" python - "$RUN/game/ui_fragment.tjs" <<'PY'
import io, sys
p = sys.argv[1]
t = io.open(p, encoding="utf-8").read()
t2 = t.replace('var UIFragDemoSeedCell  = "c0";', 'var UIFragDemoSeedCell  = "c5";')
io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
print("PATCHED ui_fragment.tjs (temp copy only) seed c0 -> c5 :", t != t2)
PY
fi

cd "$RUN/runtime"
./tvpwin32.exe "$RUN/game" > "$EVID/krkr_stdout_$MODE.txt" 2>&1
echo "EXIT=$?"

if [ -f "$RUN/runtime/savedata/krkr.console.log" ]; then
  iconv -f UTF-16LE -t UTF-8 "$RUN/runtime/savedata/krkr.console.log" > "$EVID/krkr_console_$MODE.utf8.log"
fi
rm -rf "$EVID/png_$MODE"; mkdir -p "$EVID/png_$MODE"
cp "$RUN"/runtime/savedata/shot_*.png "$EVID/png_$MODE/" 2>/dev/null
cp "$RUN"/runtime/savedata/ui_flow_state.txt "$EVID/ui_flow_state_$MODE.txt" 2>/dev/null

taskkill //IM tvpwin32.exe //F >/dev/null 2>&1
echo "DONE mode=$MODE"
ls "$EVID/png_$MODE" | wc -l
rm -rf "$RUN"
echo "CLEANED"