# -*- coding: utf-8 -*-
r"""run_all.py —— `ISSUE-20260928-02` 第 2 步（E1 数据层与生成器）**一键复现 + 全闸门**

跑什么（全部幂等；**最后一步把屏文件还原成交付样例 screen1**）：

  ① 按派单顺序产三档：`screen1`（无参）→ `states` → `frag`
  ② `工具\gen_layout.py` → 三处产物（`layout/ui_layout.json`、`krkr/game/ui_layout.tjs`、`复刻/ui_layout.js`）
  ③ **六道闸门**（此时盘上＝**最后一个预设 frag 的产出**）：
     `test_flow_links` / `verify_ui` / `test_gen_sync` / `test_state_targets` / `test_click_reach` / `test_verify_asset_refs`
     ⇒ **每个预设产出都必须自身过闸门**（不是只看交付样例）
     （★ 第 3 批：`test_gen_sync` 另含两条**非屏产物**常驻闸门 —— `ui_layout.tjs` 无带引号字典键、
      `ui_flow_data.tjs` 无旧元素寻址值；均自带变异/非恒真自证）
  ④ `m02_states_frag_variants.py`（生成 states/frag 变体到 `_out/` ＋ 运行态/独立层数据自证）
  ④b `m03_shell_and_delivery_loop.py`（★ 第 3 批四条机检自证：外壳不参与层旗标 / 交付样例进出闭环 /
      独立层无运行态叠加件 / 每格文字四判据）
  ④c `m04_regen_flow_data_tjs.py`（★ 第 3 批：旧元素寻址退场 —— 只重生成 `krkr/game/ui_flow_data.tjs`，
      `复刻/flow_data.js` 不动）
  ④d `m05_entry_hit_layer_scope.py`（★ 第 4 批 · 裁决 4：**入口热区作用域闭环** —— 五预设逐一实跑复算
      「存在 `fc.entry.*_hit` ⇒ 其 `layer` 在本档确有元素」＋「每个已产层进出闭环」；含两条反向自证）
  ④e `gen_flow_layout.py --selfcheck-mode-entries`（★ 第 13 批 · E5 S1 接入：**模式入口几何**的变异自证
      —— 真数据 0 违规；重叠／越出画布／压住 `fc.titleplate`／**`_tx` 位移回退** 四条变异各须被检出）
  ⑤ `test_flow_links.py --screen <states/frag 变体>`（三档连线 / 独立层端点保护）
  ⑥ 还原 `screen1` → 重出三处产物 → 六道闸门再跑一遍（**交付样例态**）
  ⑦ `m01_screen1_appearance_diff.py`（外观不变自证：盘上必须是 screen1 ⇒ 放这里跑）
  ⑧ 另两个屏预设 `screen2` / `ref150` ＋ 全量 `full` ＋ `--frag-report`（未产格清单）；**最后再跑一次无参还原交付样例**
  ⑨ `test_delivery_index_sync.py`（★ 第 14 批 · `ISSUE-20260929-07`：**《UI组_交付总纲.md》的人读数字**
      与磁盘真值一致 —— 资源族件数/字节、逐屏元素数、三处产物 md5、头像集、预算余量；含 `--selfcheck` 变异自证）
  ⑩ `gen_flow_layout.py --selfcheck-intro-overlay`（★ 第 15 批 · `ISSUE-20260930-02`：章节详情浮层与
      加号按钮的**落盘前自检变异自证** —— 6 条变异各须被检出）
  ⑩ `test_text_ellipsis.py`（★ 第 15 批 · `ISSUE-20260930-02`：**超框省略号**的冻结期望表闸门 ——
      同一张表喂给**两端**：HTML `复刻/replica.js::wrapEllipsisLines`（经无头 Edge 探针页，不自带实现）
      ／ Python `工具/gen_flow_layout.py::apply_ellipsis`（第 15 批归并后的**唯一** Python 实现）；
      断言 行数 / 截断 / 末行 `……`（两个 U+2026）/ 逐字回退 / **两端返回的行逐字相同**；
      另含 `--selfcheck` 变异自证 —— 但**本套件只跑正常态**（自证由 `--selfcheck` 单独跑））

退出码 0 = 全部通过；任一步骤非 0 即中止并打印该步骤的完整输出。

用法：
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    cd "...\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组"
    python "_工作/ISSUE-20260928-02_第2步/复现脚本/run_all.py"
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # …\UI组
REL = "_工作/ISSUE-20260928-02_第2步/复现脚本"
OUT = os.path.join(HERE, "_out")
PY = sys.executable

STEPS = []


def step(title, args):
    STEPS.append((title, args))


GATES = ("test_flow_links", "verify_ui", "test_gen_sync", "test_state_targets",
         "test_click_reach", "test_verify_asset_refs",
         # ★ ISSUE-20260928-07 一审抓出的**闸门盲区**：删屏要重跑**两个**生成器 ——
         #   `工具\gen_layout.py`（三产物，有 verify_ui [3] 等看着）与 `工具\emit_asset_index.py`
         #   （`复刻\screen_index.js` 编辑器用屏清单）。**后者此前无任何闸门** ⇒ 删 `ending` 那轮漏跑它，
         #   编辑器屏选择器为空并抛 TypeError，而 34 步闸门与两套 HTML 自检都覆盖不到
         #   （自检宿主页不加载 screen_index.js）⇒ 补此闸门（双向一致性）。
         "test_screen_index_sync")

# ① 派单顺序的三档
step("gen · screen1（交付样例）", ["工具/gen_flow_layout.py"])
step("gen · states（运行态演示）", ["工具/gen_flow_layout.py", "--preset", "states"])
step("gen · frag（番外独立层演示）", ["工具/gen_flow_layout.py", "--preset", "frag"])
# ② 三处产物
step("gen_layout（三处产物）", ["工具/gen_layout.py"])
# ③ 闸门（盘上＝frag 产出态 ⇒ 证明「预设产出自身过闸门」）
for t in GATES:
    step("闸门 · %s（最后一个预设产出态）" % t, ["工具/%s.py" % t])
# ④⑤ 变体自证与变体闸门
step("自证 · m02 states/frag 数据", [REL + "/m02_states_frag_variants.py"])
# ④b ★ 第 3 批：四条机检自证（外壳不参与层旗标 / 交付样例进出闭环 / 独立层无运行态 / 每格文字四判据）
step("自证 · m03 层旗标/组名底托与交付样例闭环（第 3+5+9 批）", [REL + "/m03_shell_and_delivery_loop.py"])
# ④d ★ 第 9 批：标题「已读对勾」不变量（实测 + 变异自证）
step("自证 · 标题首行左缘不变量（第 9 批）", ["工具/gen_flow_layout.py", "--title-check-report"])
step("自证 · 该不变量的变异自证（第 9 批）", ["工具/gen_flow_layout.py", "--selfcheck-title-break"])
# ④e ★ 第 13 批（`ISSUE-20260929-05`）：模式入口几何（画布内 ＋ 与相邻件零重叠 ＋
#      `_glow`/`_hit` 同框、`_tx` 下移 8px 的口径）的**变异自证**。E5 建议项 S1 接进常驻套件。
step("自证 · 模式入口几何的变异自证（第 13 批）",
     ["工具/gen_flow_layout.py", "--selfcheck-mode-entries"])
# ④c ★ 第 3 批：旧元素寻址退场（只重生成 krkr/game/ui_flow_data.tjs；复刻/ 不动）
step("自证 · m04 旧寻址退场（重生成 ui_flow_data.tjs）", [REL + "/m04_regen_flow_data_tjs.py"])
# ④d ★ 第 4 批 · 裁决 4：入口热区作用域闭环（五预设逐一实跑复算；含两条反向自证）
step("自证 · m05 入口热区作用域闭环（第 4 批 · 裁决 4）",
     [REL + "/m05_entry_hit_layer_scope.py"])
step("变体闸门 · states", ["工具/test_flow_links.py", "--screen",
                          os.path.join(OUT, "32_flowchart.states.json")])
step("变体闸门 · frag", ["工具/test_flow_links.py", "--screen",
                        os.path.join(OUT, "32_flowchart.frag.json")])
# ⑥ 还原交付样例 + 闸门复跑
step("gen · 还原 screen1", ["工具/gen_flow_layout.py"])
step("gen_layout · 还原后重出三处产物", ["工具/gen_layout.py"])
for t in GATES:
    step("闸门 · %s（交付样例态）" % t, ["工具/%s.py" % t])
# ⑦ 外观不变自证（盘上必须是 screen1）
step("自证 · m01 交付样例外观不变（含 HEAD 基线健全性硬失败）", [REL + "/m01_screen1_appearance_diff.py"])
# ⑦b ★ 第 9 批：交付样例「基线总账」（对照**固定引用** `ef68dcf`，不随 HEAD 漂移）——
#     管「盘上现值有没有被偷偷改过」；与 ⑦ 的「提交进去的那份是不是交付样例」互为补角。
step("自证 · m06 交付样例基线总账（固定引用）", [REL + "/m06_delivered_sample_ledger.py"])
# ⑧ 其余预设与全量，最后还原
step("gen · screen2", ["工具/gen_flow_layout.py", "--preset", "screen2"])
step("gen · ref150", ["工具/gen_flow_layout.py", "--preset", "ref150"])
step("gen · full（全量几何数据，不产元素）", ["工具/gen_flow_layout.py", "--preset", "full"])
step("report · frag 容量与未产格清单", ["工具/gen_flow_layout.py", "--frag-report"])
step("gen · 最终还原 screen1（交付样例）", ["工具/gen_flow_layout.py"])
step("gen_layout · 最终三处产物", ["工具/gen_layout.py"])
# ⑨ ★ 第 14 批（`ISSUE-20260929-07`）：**《UI组_交付总纲.md》里给人读的数字**（资源族件数/字节、
#    逐屏元素数、三处产物 md5、头像集、预算余量）必须与磁盘真值一致。放在最后 ⇒ 校验的是**交付态**。
#    通用口径：凡人读的口径副本必须有闸门盯着，否则会静默过期（本工程既有通例：凡人读的口径副本必须有闸门盯着）。
step("闸门 · 交付总纲数字与磁盘一致（第 14 批）", ["工具/test_delivery_index_sync.py"])
# ⑩ ★ 第 15 批（`ISSUE-20260930-02`）：**超框省略号**（冻结书 §五）的冻结期望表交叉闸门 ——
#    同一张表喂给 HTML（无头 Edge 跑 `复刻/_probe_text_ellipsis.html`，同一份 replica.js、探针不自带实现）
#    与 Python（`工具/gen_flow_layout.py::apply_ellipsis` 单一实现）；断言两端返回的行**逐字相同**。
#    放在最末 ⇒ 校验的是**交付态**。仅新增本步，既有步骤一字未改。
step("闸门 · 文本超框省略号（第 15 批）", ["工具/test_text_ellipsis.py"])
# ⑩ ★ 第 15 批（`ISSUE-20260930-02`）：章节详情浮层的**落盘前自检变异自证**
#    （加号按钮压文字 / 浮层热区 z 不足 / 浮层件出画布 等 6 条变异各须被检出）。
step("自证 · 章节详情浮层的变异自证（第 15 批）", ["工具/gen_flow_layout.py", "--selfcheck-intro-overlay"])
# ⑪ ★ 第 17 批（`ISSUE-20260930-09` · UI 组交付整理）：**交付包校验收据**闸门 ——
#    `交付包校验收据.md` 是给人核对**副本完整性**的单一表（素材族件数/字节、逐屏元素数、三处产物 md5、
#    flowchart 五组金标 md5、手写关键文件 md5、插件 sha256、动作计数、套件步数），其数字**全部**由
#    `工具\emit_delivery_manifest.py` 从盘上机算（脚本里不硬编码任何件数/字节/md5）。
#    本步＝重算并与盘上该 md **逐格比对**（表被 `GATE:` 注释包住）；不一致即非 0 并指名差异。
#    ★ **排在最末（「还原交付样例」之后）** ⇒ 校验的是**交付态**，不被中间态污染。
#    （套件步数以启动行自报为准，任何文档都不得写死。）本步只新增，既有步骤一字未改。
step("闸门 · 交付包校验收据与磁盘一致（第 17 批）",
     ["工具/emit_delivery_manifest.py", "--check"])


def main():
    print("=" * 78)
    print("run_all.py · ISSUE-20260928-02 第 2 步（E1）一键复现（%d 步）" % len(STEPS))
    print("  UI组 = %s" % UI)
    print("=" * 78)
    for i, (title, args) in enumerate(STEPS, 1):
        r = subprocess.run([PY] + args, cwd=UI, capture_output=True, text=True)
        print("  [%02d/%02d] %-6s %s" % (i, len(STEPS), "OK " if r.returncode == 0 else "FAIL", title))
        if r.returncode != 0:
            print("-" * 78)
            print(r.stdout[-4000:])
            print(r.stderr[-4000:])
            print("-" * 78)
            print("结果：**不通过** —— 第 %d 步「%s」退出码 %d" % (i, title, r.returncode))
            return 1
    print("=" * 78)
    print("结果：**全部通过**（%d 步全部退出码 0）；盘上 32_flowchart.json 已还原为交付样例 screen1"
          "（md5 见 `工具/gen_flow_layout.py` 的 `GOLDEN['screen1']` 与 `PRESET_TABLE`）" % len(STEPS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
