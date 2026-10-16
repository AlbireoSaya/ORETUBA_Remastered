#!/bin/bash
# M3（ISSUE-20260922-28）无头 Edge 截图（**仅指向本 worktree**，不用工程根目录的旧脚本）
# 用法: bash shot.sh "<query 如 screen=dialog&flags=quickbar:expanded>" <out.png> [W H]
set -u
UI="E:/ZCode Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
EDGE="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
Q="${1:-}"
OUT="${2:?out png}"
W="${3:-2000}"
H="${4:-1400}"
UD="$UI/_工作/ISSUE-20260922-28_M3_证据/.edge_ud_$$"
mkdir -p "$(dirname "$OUT")" "$UD"
URL="file:///E:/ZCode%20Workspace/Galgame/临时/wt-ui26/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/复刻/index.html"
if [ -n "$Q" ]; then URL="$URL?$Q"; fi
"$EDGE" --headless=new --disable-gpu --no-sandbox \
  --user-data-dir="$UD" --window-size="$W,$H" --hide-scrollbars \
  --virtual-time-budget=9000 --screenshot="$OUT" "$URL"
rm -rf "$UD"
echo "-> $OUT"
