#!/usr/bin/env bash
# 巡演导出 PNG 批量（ISSUE-20261007-02 · tier1 接入验收）
# 每场 off/tier1 各跑一次 run_storytest；PNG 收进 验收/PNG/<场>/<模式>/。
set -u
PROJ="E:/ZCode Workspace/Galgame/临时/wt-prog/工程/我们没有翅膀——格雷塔迦露德与柳木原"
WT="E:/ZCode Workspace/Galgame/临时/wt-prog"
cd "$PROJ" || exit 9
declare -A ML=( [ot_s01_06d]=345 [ot_s04_20a]=465 [ot_s03_07b]=372 [ot_s02_03g]=392 )

run() {
  local s=$1 m=$2 n=${ML[$1]}
  echo "=== run $s $m (maxlines=$n) ==="
  python -X utf8 编程组/工具/run_storytest.py --data-root "E:/ZCode Workspace/Galgame" \
    --all --entry "$s" --maxlines "$n" --issue ISSUE-20261007-02 --tag "$m-$s" \
    --no-story-assets --interval 20 --other-semantics "$m" --timeout 200 \
    > "编程组/other语义接入/_png_$m-$s.log" 2>&1
  echo "  exit=$?"
  local D OUT
  D=$(ls -d "$WT/子代理工作区/ISSUE-20261007-02/storytest_"*"_$m-$s" 2>/dev/null | head -1)
  OUT="编程组/other语义接入/验收/PNG/$s/$m"
  mkdir -p "$OUT"
  if [ -n "$D" ]; then
    cp "$D"/shot_*.png "$OUT"/ 2>/dev/null
    cp "$D"/krkr.console.storytest.txt "$OUT/_console.txt" 2>/dev/null
  fi
  echo "  -> $OUT : $(ls "$OUT"/shot_*.png 2>/dev/null | wc -l) png"
}

run ot_s01_06d tier1
run ot_s04_20a off
run ot_s04_20a tier1
run ot_s03_07b off
run ot_s03_07b tier1
run ot_s02_03g off
run ot_s02_03g tier1
echo BATCH_DONE
