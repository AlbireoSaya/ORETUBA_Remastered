#!/usr/bin/env bash
# 立绘尺寸/摆位改造（ISSUE-20261007-05）· 巡演导出 PNG 批量
# 由 编程组/other语义接入/_shot_pairs.py 逐场跑（带目标场景素材 ⇒ 立绘层真的画出来）。
# 用法：bash _run_png.sh <before|after>
set -u
PROJ="E:/ZCode Workspace/Galgame/临时/wt-prog/工程/我们没有翅膀——格雷塔迦露德与柳木原"
TAG="${1:-after}"
cd "$PROJ" || exit 9
# 场 → 收尾行（＝ seq）；取「该场同屏非整屏族最多」的 seq
run() {
  local s=$1 l=$2
  local out="编程组/staging改造/验收/PNG/$TAG/$s"
  echo "=== $TAG $s L$l ==="
  python -X utf8 编程组/other语义接入/_shot_pairs.py --scene "$s" --mode off \
      --line "$l" --out "$out" --timeout 240 \
      > "编程组/staging改造/_png_${TAG}_${s}.log" 2>&1
  echo "  exit=$? png=$(ls "$out"/shot_*.png 2>/dev/null | wc -l)"
}
run ot_s01_04l 27
run ot_s01_02a 290
run ot_s03_07b 245
run ot_s02_03g 144
run ot_s04_20a 363
echo BATCH_DONE
