# -*- coding: utf-8 -*-
"""M47 收尾文档：Galgame.md 行原地更新 + 作品skill SKILL.md 变更行 + 交接文档 M47 段"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # …/UI组
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))            # …/wt-qbicons
GAME = os.path.dirname(UI)                                            # 工程/<game>

# ── ① Galgame.md：状态列追加 M47 子句 + 相关记录追加本次记录名 ──────────
p = os.path.join(WT, "Galgame.md")
s = io.open(p, encoding="utf-8").read()
anchor = "`layout\\_schema.md` 新增逐项三态契约小节） | 2026-09-18 |"
assert s.count(anchor) == 1, s.count(anchor)
clause = ("`layout\\_schema.md` 新增逐项三态契约小节）；"
          "**M47（2026-09-24，用户指令 9 条）**：**设置（config）屏整体重设** —— "
          "两页（**系统／声音**，默认系统页）、透明背景 + **一个巨型方框** + 选项文字全部引擎绘制、"
          "**我们的冰蓝霜白配色**（20 件程序化新素材，非参考作位图）；两页布局按《交汇协奏曲》PSB idx 80 "
          "复刻**结构**（行步进 60 / 音量行 120、页签与右上三键、预览区几何照搬）；"
          "**新机制 `kind:\"slider\"` + 设置仓（25 键，`ui_settings.tjs`）**，"
          "其中「文本窗口的不透明度」滑块**实时改变对话框遮罩浓度**（`dlg_winopac` → `ctx.opacityOverride`）"
          "并在右侧预览（与实机同算法、样例画面为程序化生成）；"
          "分页/选中态用既有 `vis_flag` 机制（**切页值标志派生 + 值记忆层**，挡跨页泄漏）；"
          "声音页 33 项角色列表（3 列 × 11 行，**常规态/选中态**两形态）+ 横幅头像**随选中角色切换**"
          "（直接用对话框同批 M44 头像 `face/<族>.png`）；**`build_config()` 生成器退休**（该屏转手工维护）；"
          "`verify_ui` 放开 asset 命名空间（`ui/` 与 `face/`）并覆盖 slider 子素材；"
          "巡演新增 `drag`/`flag`/`click` 三种步骤与 4 条判词（`★M47DRAG★`/`★M47CLICK★`/`★M47FLAG★`/`-REJECT★`）；"
          "**一审 ×2 均打回、逐项修复并复验**（含「按 MUTE 静默改音量」与「第 3 列越框」两处实质缺陷）；"
          "引擎巡演 43 屏全绿、设置读档链路私有目录实机验证 PASS） | 2026-09-18 |")
s = s.replace(anchor, clause)
tail = "`2026-09-23_对于我们没有翅膀格雷塔迦露德与柳木原UI组删除系统条屏与选择支逐项三态的修改.md` |"
assert s.count(tail) == 1, s.count(tail)
s = s.replace(tail, tail[:-2] +
              "、`2026-09-24_对于我们没有翅膀格雷塔迦露德与柳木原UI组设置屏重设的修改.md` |")
io.open(p, "w", encoding="utf-8", newline="\r\n").write(s)
print("Galgame.md 行已原地更新")

# ── ② 作品skill/SKILL.md 变更记录追加一行 ──────────────────────────────
p2 = os.path.join(GAME, "作品skill", "SKILL.md")
t = io.open(p2, encoding="utf-8").read()
assert "M47" not in t
row = ("| 2026-09-24 | 增量更新（UI 组 M47）：**设置（config）屏整体重设**（用户 9 条指令）——两页"
       "（系统/声音，默认系统页）、透明背景 + 巨型外框 + 选项文字全部引擎绘制 + **我方冰蓝霜白配色**"
       "（20 件程序化新素材）；两页布局按《交汇协奏曲》PSB idx 80 复刻**结构**。"
       "**通用口径（离开本作也成立）**：① **新控件落地要三处同改** —— 数据 schema（`layout\\_schema.md`）、"
       "引擎渲染/命中（`ui_widget.tjs` + `ui_screens.tjs`）、HTML 与编辑器（`replica.js` + `editor_ui.js`），"
       "**任一处漏掉都是静默分叉**（本轮 `slider` 首次落地即按此清单推进）；② **重叠热区的命中必须按全局最高 z 裁决**"
       "——拖动类控件的「只看自己候选集」的实现会让**块内小控件（如 MUTE 勾选框）的点击顺带拖动滑块并写设置**，"
       "两端表现分叉且会落盘；③ **『一个元素只能带一对 `vis_flag`』是硬约束**：值/选中态与页归属两个维度冲突时，"
       "用「切页时按数据派生值标志（非本页置空、本页从设置仓/记忆/默认三级链恢复）」解决，**不要给元素加第二对旗标**；"
       "④ 记忆层的捕获**不能发生在进屏那一刻**（那一刻 flag 刚被 `flags_default` 重置 ⇒ 用默认值冲掉用户选择）；"
       "⑤ **asset 命名空间可按首段放开**（`ui/`、`face/`），但守门、索引、HTML 解析三处必须同改（否则两侧误报缺件）。"
       "契约落点：`layout\\_schema.md` 的「`slider` 元素字段」「设置仓」「分页与选中态」三节；"
       "证据与复现脚本在 `UI组\\_工作\\M47_设置屏重设\\` 与 `UI组\\_工作\\ISSUE-20260924-01_W4_证据\\` "
       "| UI 组（ISSUE-20260924-01） |\n")
io.open(p2, "w", encoding="utf-8", newline="\r\n").write(t.rstrip("\n") + "\n" + row)
print("作品skill SKILL.md 变更记录已追加 M47 行")

# ── ③ 交接文档追加 M47 段 ──────────────────────────────────────────────
p3 = os.path.join(UI, "会话交接_20260923-04_高难度绘图任务前状态.md")
t3 = io.open(p3, encoding="utf-8").read()
assert "M47" not in t3
add = """

---

## 十、M47 后注（2026-09-24）：设置（config）屏整体重设

> 主代理在合并后追加；上面各节原文**不改写**，冲突处以本条为准。

1. **屏已整体替换**：`layout/screens/25_config.json` 121 → **435 件**（旧 121 件的 id 只沿用 5 个）。
   两页（**系统 / 声音**，默认系统页）；`flags_default` 18 键；**9 根滑块**；33 项角色列表（3 列 × 11 行）
   + 33 件 flag 互斥的横幅头像与名字（**随选中角色切换**，用 `face/<族>.png` = 对话框同批头像）。
2. **生成器已退休**：`m34_build_screens.build_config()` **已删除**（同 M45 `sysmenu` / M46 `sysbar` 先例）
   ⇒ 该屏现为**手工维护**（`test_gen_sync` 判 `NO_GEN`）。首版由
   `_工作\\M47_设置屏重设\\复现脚本\\m47_build_config.py` **一次性**产出，**重跑会覆盖手改**（文件头有警示）。
3. **新机制（改这块前必读）**：`kind:"slider"`（字段与拖动契约见 `layout\\_schema.md` 的「`slider` 元素字段」）
   + **设置仓**（`krkr\\game\\ui_settings.tjs`，25 键；HTML 侧 `replica.js` 的 `SETTING_DEF` 同名同值域）
   + 「文本窗口的不透明度」实时驱动 `dlg.mask_bottom` 与 `cfg.pv_mask`（映射 `floor(255×值/100)`，90 档 = **229**）
   + 分页值标志派生与值记忆层（三段链：设置仓 → 切页记忆 → `flags_default`；**进屏不捕获记忆**）。
4. **验收机件**：巡演 `kind:"drag"` / `"flag"` / `"click"` 三种步骤 + 4 条判词
   （`★M47DRAG★` / `★M47CLICK★` / `★M47FLAG★` / `★M47DRAG-REJECT★`）；自检 ⑲a–⑲f；
   `verify_ui` 已覆盖 slider 子素材并放开 `face/` 命名空间；设置读档链路有独立私有目录验证脚本
   （`_工作\\M47_设置屏重设\\复现脚本\\_m47_state_load_private.py`，**必须落在 `runtime/savedata/` 且用引擎自己写的文件改**）。
5. **工具/工作区变化**：`Galgame.md` 该作行已更新；`emit_asset_index.py` 现**同时索引 `assets/face/`**（361 件）；
   `.gitignore` 未变（`face/` 仍不入库，由 M44 脚本再生 —— **干净检出时 `face/` 缺失属正常**，
   `verify_ui` 对该命名空间只提示不报错）。
6. **仍未实测**：真实鼠标拖动（合成路径覆盖按下/移动/抬起三个入口）；Win7 SP1；`>6 项`独立屏分页。
7. **待用户裁决**：五人格主角（鹰志/鹫介/隼人/迦楼罗/小鹰志）**无立绘与头像素材** ⇒ 现**未列入**角色列表，
   是否要做「无头像占位」项；「透明背景」的压暗浓度（现 `cfg.dim` = `backdrop` × 70）。
"""
io.open(p3, "w", encoding="utf-8", newline="\r\n").write(t3.rstrip("\n") + add)
print("交接文档已追加 M47 段")
