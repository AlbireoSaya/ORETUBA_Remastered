#!/usr/bin/env bash
# v3（确定性）：uiDialogStartTyping 重定义为整行即时显示 ⇒ 截图恰为目标行、正文一致。
set -u
cd "E:/ZCode Workspace/Galgame/临时/wt-prog/工程/我们没有翅膀——格雷塔迦露德与柳木原" || exit 9
DRV="编程组/other语义接入/_shot_pairs.py"
BASE="编程组/other语义接入/验收/画面"
run() { local s=$1 L=$2; for m in off tier1; do
    local out="$BASE/${s}_L${L}/$m"
    echo "=== $s L$L $m ==="
    python -X utf8 "$DRV" --scene "$s" --mode "$m" --line "$L" --out "$out" \
      --interval 120 --timeout 240 > "编程组/other语义接入/_shot_${s}_L${L}_${m}.log" 2>&1
    echo "  exit=$?"
  done; }
run ot_s01_06d 8
run ot_s01_06d 100
run ot_s02_03g 144
run ot_s03_07b 156
run ot_s04_20a 157
run ot_s04_20a 334
run ot_s03_06e1 141
echo ALLDONE
