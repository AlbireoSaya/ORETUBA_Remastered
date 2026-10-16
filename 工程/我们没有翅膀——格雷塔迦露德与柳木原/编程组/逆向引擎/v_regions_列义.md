# `v_regions.tsv` 列义（2026-10-08 改口径说明，ISSUE-20261008-04 E）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：现行说明（列义口径）｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`
> 校准核对（2026-10-09）：`v_regions.tsv` = 92 数据行、新口径表头（`置信度/core起/…`）在位；§四 残留仍成立——`xvlink.py:255` 仍写旧窗口格式（未改）。

- **Issue**：`ISSUE-20261008-04-lucifen-semantics` ｜ **性质**：**只改口径、不改数据语义**（B1 建议回写）。
- **本文件是 `v_regions.tsv` 的伴随说明**。`v_regions.tsv` 本身只保留**一行表头**（不另加注释行），
  以免破坏既有读取方（`xvseg.py:847` 读该表：跳过第 1 行后取 `p[0]`=src、`p[1]`=V、`p[2]`=v_name，
  见 `xvseg.py` 的 `do_emit()`）——**前三列的名字与语义保持不变**。

## 一 为什么改

旧表把「某 V 的窗口 `[V, V+0x1000)` 内的 native 个数/调用数」当作 V 的结构度量（列 `W`/`n_native`/
`n_calls`/`n_bad`/`stop`/`native_top`）。**该口径已被证否**（ISSUE-20261008-04 B1）：

- `func_lib` 的命令实现体**边界已可判**——用**引擎真值 opcode 宽度表 + 控制流目标对齐**（`xvseg.py`）
  把整个代码区唯一切成**基本块**，再沿**过程内**控制流做可达闭包得**过程（命令实现体）**；
- 窗口法会**串到邻节点**（`n_native` 会把邻居的 native「借」来），且 `W` 是人为常数；
- 实测：`[V, nextV)` 区间归属**不可用**（`V=0x1C43C` 的过程恰为 `[V, nextV)` ⇒ 「V 体可跨过下一个 V」是窗口读数假象）。

⇒ 改用 `funclib_切分.tsv`（`xvseg.py --emit` 产出，120 行）的**core / exp 分列**（过程口径，非窗口）。

## 二 列义对照

| 旧列 | 新列 | 变化 |
| --- | --- | --- |
| `src` `V` `v_name` `corpus_nodes` `corpus_files` | 同名同序 | **不变**（前三列供 `xvseg.py` 读取，勿改） |
| `W` | —— | **删除**（人为窗口常数，无结构意义） |
| `n_native` | `native数` + `native下标` | 由「窗口内 native 计数」改为「**过程内** native 数 + 下标清单」 |
| `n_calls` | `库内CALL数` + `库内调用者站` | 由「窗口内调用数」改为「**过程内**库内 CALL 数 + 调用者站清单」 |
| `n_bad` | —— | **删除**（窗口法专有：窗口内非法 op 位；切分口径下非法 op = 0） |
| `stop` | —— | **删除**（窗口法专有：窗口内首个终止 op） |
| `native_top` | —— | **删除**（窗口内 native 频次 top） |
| （新） | `置信度` `core起` `core止` `过程起` `过程止` `连续段数` `块数` `core指令数` `过程指令数` `语料调用站数` `core串` `过程串` `被CALL目标` `既有定名` `来源` | 直接取自 `funclib_切分.tsv`；**core/exp 分列**由 `core起止`/`过程起止`/`core指令数`/`过程指令数`/`core串`/`过程串` 承载 |

- **core** = 含入口 `V` 的那个基本块（边界确定）；**exp** = 过程内可达的**其它**块。
  `过程串` 含 core 串与 exp 串（`funclib_切分.tsv` 原口径）；`core串` 为仅 core 块内的串。
- `既有定名` 列是 **2026-10-08 之前的旧记录**（=`v_regions` 原 `v_name` 同源）；本批新采纳的 9 条定名
  登记在 `解码器`（`编程组\工具\decode_sob0.py` 的 `V_NAMING`），**不回写本表**。
- 行数：**92**（与旧表一致；`funclib_切分.tsv` 的 120 行含库内私有子程序入口，本表只保留原 92 个 V）。

## 三 复跑

```bash
cd "<G>/编程组/逆向引擎"
python -X utf8 xvseg.py --stats          # 自检：非法 op 0、终点精确 = ss、1519 块、120 过程
python -X utf8 xvseg.py --emit           # 重出 funclib_切分.tsv + funclib_反汇编/
```

## 四 ⚠️ 残留：旧生成器仍写旧格式（本批未改）

`xvlink.py --vreg <path>`（`ISSUE-20261008-02` M4 的生成器）**仍写旧窗口格式**
（表头 `src V v_name corpus_nodes corpus_files W n_native n_calls n_bad stop native_top`，见 `xvlink.py:253-261`）。
⇒ **若重新运行 `xvlink.py --vreg v_regions.tsv`，会把本表退回旧口径**。
本批（ISSUE-20261008-04 E）**只改盘面数据列**、**未改 `xvlink.py`**（不在派单范围）。
后续若要再生：应以 `xvseg.py --emit`（过程口径）为准，或将 `xvlink.py` 的 writer 同步改为 core/exp 列。
