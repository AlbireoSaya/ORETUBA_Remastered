#!/usr/bin/env bash
# M13 实机巡演脚本（UTF-8 保存，避免命令行中文被二次编码）
set -u
UIROOT="E:/ZCode Workspace/Galgame/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组"
RUN="E:/ZCode Workspace/Galgame/临时/ui_run"

echo "UIROOT=$UIROOT"
echo "RUN=$RUN"
ls -d "$UIROOT" || echo "!! UIROOT 不存在"

rm -rf "$RUN"
mkdir -p "$RUN" || echo "!! mkdir 失败"
ls -d "$RUN" || echo "!! RUN 不存在"

cp -r "$UIROOT/krkr/game" "$RUN/game" || echo "!! cp game 失败"
cp -r "$UIROOT/krkr/assets" "$RUN/game/assets" || echo "!! cp assets 失败"
cp -r "$UIROOT/krkr/runtime" "$RUN/runtime" || echo "!! cp runtime 失败"
printf 'autotour' > "$RUN/game/autotour.txt"

echo "--- RUN 内容 ---"
ls "$RUN"
echo "--- runtime 内容 ---"
ls "$RUN/runtime"

cd "$RUN/runtime" || { echo "!! cd 失败"; exit 1; }
./tvpwin32.exe "$RUN/game" > /dev/null 2>&1 &
echo "engine pid=$!"
sleep 62
taskkill //IM tvpwin32.exe //F 2>/dev/null || true
sleep 1
echo "--- savedata ---"
ls "$RUN/runtime/savedata" 2>&1 | head -30