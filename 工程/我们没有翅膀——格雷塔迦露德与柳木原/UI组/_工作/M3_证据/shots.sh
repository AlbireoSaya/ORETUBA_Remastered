#!/usr/bin/env bash
# shots.sh — M3 无头截图自检（**非交付物，仅存于 _工作/M3_证据/**）
# 用本机 Edge（headless=new）对 harness.html 逐场景截图。
set -u

EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/shots"
BASE="file:///E:/ZCode%20Workspace/Galgame/%E4%B8%B4%E6%97%B6/wt-ui/%E5%B7%A5%E7%A8%8B/%E6%88%91%E4%BB%AC%E6%B2%A1%E6%9C%89%E7%BF%85%E8%86%80%E2%80%94%E2%80%94%E6%A0%BC%E9%9B%B7%E5%A1%94%E8%BF%A6%E9%9C%B2%E5%BE%B7%E4%B8%8E%E6%9F%B3%E6%9C%A8%E5%8E%9F/UI%E7%BB%84/_%E5%B7%A5%E4%BD%9C/M3_%E8%AF%81%E6%8D%AE/harness.html"

mkdir -p "$OUT"

shot() {  # name query width height
  local name="$1" q="$2" w="${3:-1300}" h="${4:-780}"
  "$EDGE" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --virtual-time-budget=12000 --window-size="$w,$h" \
    --screenshot="$(cygpath -w "$OUT/$name.png")" \
    "$BASE?$q" >/dev/null 2>&1
  if [ -f "$OUT/$name.png" ]; then echo "OK   $name.png  ($q)"; else echo "FAIL $name.png  ($q)"; fi
}

# 画布纯画面（隐藏复核面板 + 1:1）
shot 01_title            "panel=0&scale=1&screen=title"                 1290 730
shot 02_dialog_line1     "panel=0&scale=1&screen=dialog&line=0"         1290 730
shot 03_dialog_line18    "panel=0&scale=1&screen=dialog&line=17"        1290 730
shot 04_dialog_choices   "panel=0&scale=1&choices=1"                    1290 730
shot 05_dialog_choice_1  "panel=0&scale=1&choice=1"                     1290 730
shot 06_dialog_hide      "panel=0&scale=1&screen=dialog&line=5&mode=hide" 1290 730
shot 07_dialog_src_otv   "panel=0&scale=1&screen=dialog&line=5&src=otv" 1290 730
shot 08_dialog_src_np    "panel=0&scale=1&screen=dialog&line=5&src=np"  1290 730
shot 09_noscreen_save    "panel=0&scale=1&screen=save"                  1290 730
shot 10_noscreen_flow    "panel=0&scale=1&screen=flowchart"             1290 730
shot 11_noscreen_frag    "panel=0&scale=1&screen=fragment"              1290 730
# 含复核面板的整页
shot 20_shell_title      "screen=title"                                 1500 1050
shot 21_shell_dialog     "screen=dialog&line=40"                        1500 1050

echo "--- shots ---"
ls -la "$OUT"