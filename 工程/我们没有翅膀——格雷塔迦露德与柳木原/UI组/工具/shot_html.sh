#!/bin/bash
# 无头 Edge 渲染 复刻/index.html 指定屏 → PNG
# 用法: ./shot_html.sh <屏id> <输出png> [宽 高]
set -u
UI="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EDGE="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
SCREEN="${1:?screen id}"
OUT="${2:?out png}"
W="${3:-2000}"
H="${4:-1400}"
UD="E:/ZCode Workspace/Galgame/临时/edge_ud_$$"
mkdir -p "$(dirname "$OUT")"
"$EDGE" --headless=new --disable-gpu --no-sandbox \
  --user-data-dir="$UD" --window-size="$W,$H" --hide-scrollbars \
  --virtual-time-budget=9000 --screenshot="$OUT" \
  "file:///E:/ZCode%20Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/复刻/index.html?screen=$SCREEN"
echo "-> $OUT"