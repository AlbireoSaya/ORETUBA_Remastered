# A 路 · 指令编码结构（ISSUE-20261006-05）

> **校准**：2026-10-09 · `ISSUE-20261009-01` ｜ 定位：历史快照（逆向过程件，只作背景） ｜ 权威入口：`工程\我们没有翅膀——格雷塔迦露德与柳木原\00_项目索引.md`

- 侧面：**只解「怎么切分」**——文件头 / 索引表 / 单元粒度 / 参数内联规则；不涉语义。
- 对象：`工程\我们没有翅膀\解包\SCRIPT\*.sob`（本篇 2009，411 个 SOB0 + `func_lib.sob` SOB2 + `user_var.sob` 等）、
  `工程\我们没有翅膀 前奏诗\解包\SCRIPT\*.sob`（67 个 SOB0）；另扫 `我们没有翅膀R\语料\R版SCRIPT\`、
  `我们没有翅膀 After Story\语料\原文\`（TOB0）作对照。
- 全部结论**只读复算**得出；**未改动任何文件**；本报告是 A 路唯一产物。
- 纪律：只写「有证据」与「未定」。凡未定者写明**需要什么实验**。与 PSV 金标冲突的结构推断一律降级为未定（本报告不含语义主张，故无此冲突项）。

**一句话结论**：容器、索引、单元粒度、指针编码已**全部解出且可复算**；**「高 12 位 = opcode」这个前提被证否**——高 12 位是**共享剧本地址空间的页号**；**项流文法（marker→元数表）未解出**，且我做了 4 组判否实验，都是负结果（见 §7、§8）。

---

## 一 · 容器结构（SOB0 / SOB1 / SOB2 同构，实测 482 文件）

> 订正（2026-10-06 独立复核）：本报告全篇「480 文件」的口径**实为 482 文件**（ot 413 ＋ 前奏诗 69，含前奏诗 SOB1/SOB2 各 1）—— R1 实测：唯一使 766,062 / 74,118 / 537,363 / 253 成立的口径即 **482**；若按字面 480 复算会得 maps[1]=73,494、maps[4]=528,864，从而误判本报告有错。全文已按 482 订正（各表空/非空分布同步改为 482 口径）。复核员 R1；报告 `复核\复核_R1_结构层与项文法.md`。

```
[0x00]  magic  'SOB0' | 'SOB1' | 'SOB2'      ← 三者容器完全同构（见 §1.3）
[0x04]  u32 table_size ; table_end = table_size + 8
[0x08 .. table_end)  连续 6 张表，每张 = u32 条数 + 条数×(u32 k, u32 v)   ※ 张数恒为 6，见 §2
[table_end + 0]  u32 strings_start        (相对 header_end)
[table_end + 4]  u32 strings_end
header_end = table_end + 8
代码区 = [header_end, header_end + strings_start)              ← 长度 = strings_start
串区   = [header_end + strings_start, header_end + strings_end)
文件尾 = header_end + strings_end                              ← 与文件长度逐字节吻合
```

复算样例（`工程\我们没有翅膀\解包\SCRIPT\s01_02a.sob`，文件长 110139）：

| 量 | 值 |
| --- | --- |
| magic | `SOB0` |
| table_size | `0x6e48` → table_end `0x6e50` |
| 六表条数 | `[69, 370, 0, 674, 2413, 0]` |
| strings_start / strings_end | `0xcc64` / `0x13fe3` |
| header_end | `0x6e58` |
| 代码区 | `[0x6e58, 0x13abc)`，长 `0xcc64` = 52324 字节 = 13081 个 4 字节字 |
| 串区 | `[0x13abc, 0x1ae3b)`，长 `0x737f` = 29567 字节 |

其余四个基准文件的同项值：

| 文件 | 体积 | table_end | 六表条数 | strings_start(字节) | header_end | 代码字数 |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `s00_00.sob` | 1,752 | 0x2d0 | 21,6,**0**,4,55,0 | 964 | 0x2d8 | 241 |
| `s01_01a.sob` | 15,694 | 0xec0 | 23,56,**0**,67,322,0 | 6,176 | 0xec8 | 1,544 |
| `s01_02a.sob` | 110,139 | 0x6e50 | 69,370,**0**,674,2413,0 | 52,324 | 0x6e58 | 13,081 |
| `op.sob` | 28,275 | 0x2408 | 29,84,**0**,18,1018,0 | 17,044 | 0x2410 | 4,261 |
| `main.sob` | 3,702 | 0x5f0 | 25,19,2,8,132,0 | 2,084 | 0x5f8 | 521 |

### 1.3 三种魔数同构（实测）

`工程\我们没有翅膀\解包\SCRIPT\func_lib.sob` 魔数为 **`SOB2`**（280,098 字节），按上表同一套偏移解析**完全自洽**：
table_size `0x18ed8`、六表 `[1343, 805, 0, 0, 10612, 0]`、strings_start `0x2abcc`、strings_end `0x2b73a`、header_end `0x18ee8`、代码末 `0x43ab4`。
⇒ **`SOB0/1/2` 只是版本号，容器一致；不要按魔数分支写两套解析器。**
（唯一例外：`user_var.sob` 的头部不符合本布局，第 1 张表条数读出 `0xFFFFFFFF`，解析溢出——**未定**，需要单独一页处理。）

---

## 二 · 六张表的语义（全库 482 文件复算）

**形态事实（482/482 成立）**：
1. **张数恒为 6**（482/482）。各张是否为空（482 文件统计）：
   `maps[5]` **恒空（482/482）**；`maps[2]` 空 478/482（非空 4，如 `main.sob` 2 条）；
   `maps[3]` 空 6/482；**`maps[0]` / `maps[1]` / `maps[4]` 在 480/482 非空**（各空 2 ＝ 前奏诗 SOB1/SOB2 空表文件）。
2. **表键 = 代码区字节偏移**，4 字节对齐：全部 766,062 个键中 **765,809（99.97%）≡0 (mod 4)**。
   非对齐键 253 个，**只出现在第 5 张（maps[4]）且只在 14 个系统脚本里**
   （`history.sob` 76、`saveload.sob` 42、`scskip.sob` 42、`logo.sob` 12、`ssskip.sob` 12、`func_lib.sob` 10、`gallery.sob` 10、`title.sob` 10、`eyecatch.sob` 3、`movieplay.sob` 2、`config1.sob` 1、`config2.sob` 1 …）——**未定**，见 §10-U3。
   另有 317 个键指向代码区之外（同样全是 maps[4]、全在上述系统脚本），**未定**，见 §10-U3。
3. **六张表两两互不相交**：482/482 文件，任意两表键交集计数 = 0。⇒ 一张表 = 一种「引用种类」。

**各表的值规则（逐条复算，非抽样）**：

| 表 | 条目总数 | 规则 | 命中 | 反例 |
| --- | ---: | --- | ---: | ---: |
| `maps[1]` | 74,118 | `单元值 == maps[1][键] + 1`（1 基索引） | **74,118 / 74,118** | 0 |
| `maps[3]` | 131,701 | `单元值 == maps[3][键]`（恒等，已是绝对地址） | **131,701 / 131,701** | 0 |
| `maps[4]` | 537,363 | `(单元值 & 0xFFFFF) − maps[4][键] = 该文件的常数 B` | **537,363 / 537,363** | 0 |

`maps[4]` 的 B 在 482 个文件里只有 **55 个互异取值**（例：`main.sob` B=`0x9008`、`s00_00.sob` B=`0x6d858`、
`s01_01a.sob` B=`0x9fa0`、`s01_02a.sob` B=`0x49f40`、`op.sob` B=`0xdf58`、`s01_03c1.sob` B=`0xfece0`）。
**B 相同的文件最多 166 个**（166 个剧情脚本共用同一个槽位）⇒ 剧本是**按需加载、槽位复用**的。

⇒ **结论：`maps[4]` 是「站址 → 目标在本文件体内的字节偏移」的还原表；`maps[1]` 是「站址 → 1 基索引减一」；
`maps[3]` 是「站址 → 绝对地址」；`maps[0]`/`maps[2]` 未定（§10-U2）。**

### 2.1 `maps[0]` 未定（**必须写清，防下游误用**）

`maps[0]` 的单元**全是页号 0x018 的引用**（本篇 21,607 条）+ 页号 0x017 的引用（947 条；合计 **22,554**〔R1 按 482 口径复算 **22,557**，**差 3**，口径细节未复现，不影响结论〕），
即它存的**也是指针**，但它的**值列不是文件内偏移**（`(单元值&0xFFFFF) − 值` 在全库有 1,063 个互异取值，不恒定）。
⇒ `maps[0]` 的「值列」语义**未定**；只能确定「键 = 站点、且这些站点持有指向**别的区段**的指针」。
**不要**把 `maps[0]` 当 `maps[4]` 用。

> 订正（2026-10-06 独立复核）：`maps[0]` 条目数「21,607 + 947 = **22,554**」—— R1 按 482 口径复算为 **22,557（差 3）**，口径细节未复现，不影响结论；已在正文就地标注。复核员 R1；报告 `复核\复核_R1_结构层与项文法.md`。

---

## 三 · 单元（cell）模型 —— 代码区是 **4 字节字数组**（已证）

- 表键 4 字节对齐（§2 事实 2）⇒ **代码区的可寻址单位是 4 字节**，代码字数 = `strings_start / 4`。
- 单元的**取值分布（本篇 411 文件，行首 12 位）**：

| 高 12 位 | 出现次数 | 含义（本报告结论） |
| --- | ---: | --- |
| `0x000` | 1,848,375 | 裸 32 位值：小整数 / 全局地址 / 索引 |
| `0x018` | 464,499 | **指向地址空间第 0x018 页的引用**（不是「opcode 0x18」） |
| `0xfff` | 30,352 | `0xFFFFFFFF` = **-1**（二补码的自然结果） |
| `0x00f` | 920 | 未定（值 `0x00Fxxxxx`，见 §10-U4） |
| `0x017` | 126 | 指向第 0x017 页的引用 |
| 其它 | 67 | `0x006×50`、`0x00d×5`、`0x002×3`、`0x009×3`、`0x008×2`、`0x900×2`、`0x00e×2` —— 未定 |

**关键**：`0xFFFFFFFF` 的高 12 位必然是 `0xfff`；没有哪个编译器会给「-1」这个操作数配一个 opcode `0xfff`。
⇒ **这 12 位不是一个独立的 opcode 字段，而是 32 位值自身的最高位**（见 §4）。

---

## 四 · 指针编码与基址推导（★ 本路最重要的结论）

### 4.1 事实

同一个文件内，一个「引用单元」的值 `w` 与它的**目标**之间是：

```
目标 = (w >> 20) << 20  |  ( (w & 0xFFFFF) )
     = 目标所在页 × 0x100000  +  页内偏移
页内偏移 = B + 本文件体内的目标偏移        （B = 该文件常数，§2）
```

- 本篇剧情脚本：B ∈ [0x003ba8, 0x00a008] ⇒ 目标绝对地址落在 **0x0180xxxx–0x018Axxxx**（页号 0x018）。
- `s01_03c1.sob`：B = `0xfece0` ⇒ 本文件体绝对地址 = **0x017FECE0**（页号 **0x017**），
  它的 **126 个 maps[4] 条目全部是页号 0x017**；而它引用的**共享区对象仍是 0x018 页**
  （`0x0183cb58`、`0x0183cbd8`、`0x0183cad8`、`0x0183e1b8`）。
- `func_lib.sob`（SOB2）同时持有页号 0x018（maps[4]）与页号 0x017（maps[0] 的 `0x017fdad0`）两种引用。

⇒ **同一引擎、同一编译器的产物，页号随「该文件/该对象被装载到哪一页」而变。**

### 4.2 跨作对照（同一「字符串引用」角色，页号随作品而变）

| 来源 | 文件数 | 出现的高 12 位（主） |
| --- | ---: | --- |
| 本篇 2009 `解包\SCRIPT` | 411 (SOB0) | `0x000` 1,848,375 ／ **`0x018` 464,499** ／ `0xfff` 30,352 |
| 前奏诗 `解包\SCRIPT` | 67 (SOB0) | `0x000` 303,267 ／ **`0x018` 73,009** ／ `0xfff` 3,831 ／ `0x017` 376 |
| R 版 `R版SCRIPT` | 21 (SOB0) | `0x000` 99,851 ／ **`0x01a` 21,205 ／ `0x019` 17,152** |
| AfterStory `语料\原文` | 13 (SOB0) | `0x000` 57,299 ／ **`0x01b` 21,090** |

### 4.3 ★ 更正任务书的前提

任务书写「**已知文本命令的高 12 位恒为 0x018（另一类 0x017）**」。复算结果：

- 对 **本篇 2009 + 前奏诗** 成立（且 `0x017` 只占 502/1,848,126 ≈ 0.03%）。
- 对 **R 版 / AfterStory 的 SOB 脚本不成立**：同一角色由 `0x019`/`0x01a`（R）、`0x01b`（AfterStory）承担。
- 对 **同一作品内部也不恒定**：482 个文件里 **479 个** maps[4] 全用 `0x018`，**1 个**（`s01_03c1.sob`）全用 `0x017`（其余 2 个 maps[4] 为空，见 §二）。
- 现有判据 `(w & 0xFFF00000) ∈ {0x01800000, 0x01700000}` **恰好**覆盖了本篇观测到的两个页号，所以它在
  `extract_sob0.py` / `lucifen.cpp` 里「能用」是**巧合级**的，**不是 opcode 语义**。

**正确的判据（建议写进解码器）**：不要看高 12 位，而应
① 取 `site ∈ maps[4]`，② 令 `B = (w & 0xFFFFF) − maps[4][site]`，③ 目标 = `maps[4][site]`，
④ 目标落在 `[strings_start, strings_end)` 才算「引用了本文件的一段串」。
若必须用页号：**从该文件 maps[4] 条目的众数页号取**，不要写死 `0x018`。

---

## 五 · 串区与「脚本顺序」的关系（已证，可用于对齐）

`s01_02a.sob`：1198 个 maps[4] 条目指向串区。**除去 678 次重复的空串（偏移 `0x13fdf`）后，剩余 520 个条目
按代码地址升序排列，其目标串偏移严格单调递减（520/520，无例外）**：

| 代码地址 | 目标串偏移 | 内容 |
| --- | --- | --- |
| 0x001c | 0x13fbc | `プロローグ　～美空学園のひとびと～` |
| 0x00b0 | 0x13ebd | 前情提要长句 |
| 0x01bc | 0x13eb6 | `ScSkip` |
| 0x03c0 | 0x13ead | `EyeCatch` |
| 0x0440 | 0x13e47 | `SE\SE049.OGG` |
| … | … | … |
| 0x0cbe0 | 0x0cc64 | `S01_02B` |

同样的「剔除填充串后严格递减」在 `s01_01a.sob`(57/57)、`s00_00.sob`(6/6)、`main.sob`(11/11)、
`s03_01a.sob`(65/65) 上**独立复现**。

⇒ **串池是按「首次引用倒序」登记的；因此「代码地址升序 = 脚本正序」，而「串池偏移升序 = 脚本倒序」。**
这条是 `op.sob` 96 步法（倒序读串池）能成立的结构根据，也是**把项流与 PSV 事件序列对齐时唯一可靠的锚**。

---

## 六 · 引用单元在项流里的位置：`maps[4]` 不止指向串

`maps[4]` 的目标**可以落在代码区内部**（不只是串区）。例（`main.sob`）：站址 `0x0004` 的值 `0x01809010`，
`maps[4][0x0004] = 8` ⇒ 目标 = 代码偏移 `8`。这类「指向代码单元的引用」在 482 文件里有 537,363 − 串区条目个，
即 `maps[4]` = **本文件体引用总表**，指向串的那些只是它的子集。

⇒ 现有 `extract_sob0.py` 的过滤（`strings_start <= v < strings_end`）**丢掉了这一半**，这正是「不引用字符串的那一层
在解包层面永久不可见」的结构原因（任务书 §一.3 的判断成立，此处补上量化根据）。

---

## 七 · 项（record）切分：**已证部分**与**三条判否**

### 7.1 已证：局部文法片段（有直接字节证据，可复算）

以下片段在 **三个独立文件**里同形出现，位置如下（代码区偏移，相对 header_end）：

**(a) `[0x1F][载荷A][载荷B]`——0x1F 项吃 2 个载荷字**

| 文件 | 偏移 | 三字 |
| --- | --- | --- |
| `s01_02a.sob` | `0x038` | `1F` ／ `00000001` ／ `0183CB58` |
| `s01_02a.sob` | `0x044` | `1F` ／ `00000000` ／ `0183CBD8` |
| `s01_02a.sob` | `0x05c` | `1F` ／ `0183CD68` ／ `01849FAC` ← 两个载荷**都是引用** |
| `s00_00.sob` | `0x038` | `1F` ／ `00000007` ／ `0183CB58` |
| `main.sob` | `0x200` | `1F` ／ `0183E638` ／ `01809218` ← 两个载荷都是引用 |
| `func_lib.sob` | `0x49a8` | `1F` ／ `017FDAD0` ／ `01843188`（该模式在 func_lib 重复 16+ 次） |

**(b) `[0x20][载荷A][载荷B]`——0x20 项同样吃 2 个载荷字**
`main.sob` `0x2C4`：`20` ／ `0183E438` ／ `018092DC`；
`s00_00.sob` `0x0C4`：`20` ／ `0182C5C0` ／ `0186D930`（末字是引用）。

**(c) `[0x17][载荷A][载荷B]`——0x17 项同样吃 2 个载荷字**
`s00_00.sob` `0x074`：`17` ／ `00000000` ／ `P(0x00b8)`。
（注意：这里的 `0x17` 是**项的 marker**，与 §4 的**页号 0x017** 是两个不同的东西，勿混。）

**(d) 单载荷 marker（各文件多处）**：`0x1E` `0x0D` `0x28` `0x13` `0x14` `0x0C` `0x2E` `0x08` `0x04` `0x03` `0x05` `0x06` `0x0A` 后均只跟 1 个字。
例：`s01_02a.sob` `0x068`：`0D` ／ `00000000`；`s00_00.sob` `0x124`：`1E` ／ `00000000`。

**(e) 记录头（编译器样板）**：所有剧情脚本代码区**第 0 个字恒为 `0x00000006`**，最后 1 个字恒为 `0x1`（8 个抽样文件一致）。
`s00_00.sob` / `s01_01a.sob` / `s01_02a.sob` 的**结尾 12 字同形**：
`0183AD68` ／ `P(本文件内一处)` ／ `8` ／ `0` ／ `5` ／ `2` ／ `0` ／ `P(本文件内一处)` ／ `0C` ／ `4` ／ `1` ／ `1`
（其中两个引用字随文件基址变化，其余 10 字逐字相同）。
prologue 亦同形：`s00_00.sob` 与 `s01_01a.sob` 从 `0x008` 到 `0x038` **逐字相等**，差异只出现在
① 引用字（随基址变）与 ② `0x03C` 处 `7` vs `1`。
⇒ **代码区 = 固定 prologue + 场景体 + 固定 epilogue**，是编译器统一生成的。

**(f) 文件头字与长度奇偶无关**：482 文件中代码字数**奇偶各半**（`s01_02a` 13081 奇、`config1.sob` 9272 偶），
⇒ **不存在「全文件按 2 字一对」的固定配对**。

### 7.2 判否（负结果，**请勿重做**）

| # | 假设 | 判否证据 |
| --- | --- | --- |
| **A-N1** | 「全流 = `<marker><value>` 严格 2 字项，从第 0 字开始」 | `s01_02a`：6540 个「marker 位」里 **1712（26.2%）** 落在引用单元上 ⇒ 不成立 |
| **A-N2** | 同上但从第 1 字开始（第 0 字视为文件头） | 6540 个「marker 位」里 **1814（27.7%）** 落在引用单元上 ⇒ 不成立 |
| **A-N3** | 「`maps` 里所有引用站点的目标都是**项首**」（即指针只指向项边界） | 以该约束做全流铺砌（项元数 1..8 自由取值），`s00_00` / `main.sob` 在元数上限 4/6/8 下**均无解** ⇒ 指针会指向项内部（例如 `s00_00` 站址 `0x070` 的值指向单元 `0x078`，而 `0x078` 是 `[0x17][0][…]` 项的**载荷位**） |
| **A-N4** | 「每个 marker 的元数只是 marker 的函数」，元数表 = `{0x1F:2, 0x20:2, 0x17:2, 其余:1}` | 自纠迭代 4 轮不收敛：未识别为 marker 的引用字数 **1841 → 2424 → 1359 → 1771**（s01_02a+s00_00+op.sob+s01_01a 合计 9482→7932 项） ⇒ 该形式**不足以**解释全流 |

**A-N3/N4 的合并含义（本路的核心未定项）**：**「带 marker 的项流」不是「marker + 固定元数载荷」这一种形式**——
至少在部分区段，单元序列不是线性项流（更像**指针连成的图/树**：`0x00000008` 与 `0x00000000` 的
`<值>` 型单元在四大脚本里占 marker 位的 34%–51%，而它们与引用字交替出现，周期性明显：坏 marker 常以
`0x20`(8 字) 或 `0x18`(6 字) 为周期重复出现，说明这些区段是**定长表**而非项序列——但**表长与字段含义未定**）。

---

## 八 · 与《第一波调研小结》的结构层分歧（需仲裁）

| 项 | 第一波小结（§1.2/§1.4） | A 路复算 | 处置 |
| --- | --- | --- | --- |
| 高 12 位 | 「同文件内恒定、文件间不同（0x17F–0x185），**可能才是真 opcode 字段**」 | 现象一致（0x17F/0x184/0x185 = 页号 0x017/0x018 与低 20 位最高半字节的组合），但**机制是共享地址空间的页号**，不是 opcode：同引擎跨作由 `0x018`→`0x019/0x01a`(R)→`0x01b`(AfterStory)；`0xFFFFFFFF` 的高 12 位必为 `0xfff`；`s01_03c1` 整文件页号 `0x017` | **A 路主张：页号，非 opcode**。若采用「opcode」说法，解码器会在 R/AfterStory 上全线失效 |
| 「REF 的前一个词就是它的 tag」 | 26,418/26,420 命中，反例仅 2 | 该规则在 `1F/20/17` 三项处**必然误判**：`s01_02a` 偏移 `0x05c` = `1F 0183CD68 01849FAC`，第二个引用（`0x064`）的「前一个词」是 `0183CD68`（一个引用），不可能当 tag | 建议：解码器对 `1F/20/17` **先吃 2 个载荷**；其余按「前一词 = tag」；两者并用后再做全流铺砌校验 |
| 记录成链「倒数第 2 字是 next 指针」 | 已述 | **A 路证实同形**：`s00_00` `0x164`=`P(→0x178)`，而 `0x178` 正是该记录末字 `0` 所在的**下一项首** ⇒ 指针指向「项的起点」，与该说法一致 | 采纳 |
| `maps[4]` = 串偏移还原表 | 已述 | 采纳，并补：**它同时覆盖指向代码区的引用**（537,363 条里只有一部分指向串区）；`maps[1]/maps[3]` 的规则已逐条证明（§2） | 采纳并扩充 |

---

## 九 · 切分伪代码（**只含已证部分**，未证处显式抛「未定」）

```
读文件:
  magic = u32[0..4]            # SOB0/SOB1/SOB2 同构
  table_size = u32[4..8]; table_end = table_size + 8
  maps = []
  for i in 0..5:                      # 恒 6 张
      n = u32[p]; p += 4
      maps[i] = { u32[p+8k] : u32[p+8k+4] for k in 0..n-1 }; p += 8n
  strings_start = u32[table_end]; strings_end = u32[table_end+4]
  header_end = table_end + 8
  code  = data[header_end : header_end + strings_start]
  strtab= data[header_end + strings_start : header_end + strings_end]
  cells = [ u32le(code, 4*i) for i in 0..len(code)/4-1 ]   # 4 字节字，4 对齐（已证）

每文件的基址 B（已证规则，任取一个 maps[4] 条目即可）:
  k = 任意 key ∈ maps[4]
  B = (cells[k/4] & 0xFFFFF) - maps[4][k]
  # 若 maps[4] 为空（极少数系统脚本），改用 maps[1]/maps[3] 的规则或其他文件推断 → 未定

解的引用（已证）:
  def ref_target(site):
      if site not in maps[4]: return None
      off = maps[4][site]                 # 本文件体内字节偏移（权威、可跨机复现）
      return ('file', off)
  def is_text_ref(site):
      off = maps[4].get(site)
      if off is None: return False
      if not (strings_start <= off < strings_end): return False
      p = header_end + off                # 串的取法沿用 lucifen.cpp（见 galgame 侧既有 extract_sob0.py）
      ...
  def index_ref(site):   return maps[1][site]     # == cell - 1        （已证，74118/74118）
  def abs_ref(site):     return maps[3][site]     # == cell            （已证，131701/131701）
  def xpage_ref(site):   return maps[0][site]     # 值列语义 **未定**

项切分（**部分已证、整体未定**）:
  i = 0
  while i < n:
      m = cells[i]
      if m in (0x0000001F, 0x00000020, 0x00000017):
          emit_item(m, payload=[cells[i+1], cells[i+2]]); i += 3      # 已证：三例独立复现
      elif m < 0x100 and m not in ref_kinds:                          # 「小整数 = marker」是经验规则，未证
          emit_item(m, payload=[cells[i+1]]); i += 2
      else:
          raise Undecided('该位置不是任何已证形态（占全流 5%–20%，随文件而异）')
  # 注意：此循环在 s01_02a 上会抛 Undecided 约 1244 次 ⇒ 不是可用解码器，只是已证部分的骨架
```

---

## 十 · 未定项与「需要什么实验才能定」

| # | 未定项 | 现状 | 需要的实验 |
| --- | --- | --- | --- |
| **U1** | **项流的整体文法**（哪些字是 marker、各 marker 元数、是否所有区段都是线性项流） | A-N1..N4 四组判否；仅 `1F/20/17` 的 2 载荷、以及若干单载荷 marker **已证** | **差分实验（成本最低、最可能一击定案）**：取同场景的两个分片脚本（`s01_02d1`/`d2`、`s01_02f1`/`f2`、`s01_04b1`/`b2`、`s01_04m1`/`m2`、`s01_03c1`/`c2`），做**按项对齐**的差分（不是字级 diff）。已实测这些对的差异**只发生在 4 字节边界**（`d1`/`d2` 差异 opcodes 319 段、每段都对齐 4 字节），把每段差值的字序列取出即可读出「一条命令占几个字」 |
| **U2** | `maps[0]` 的值列语义；`maps[2]` 的语义（`main.sob` 仅 2 条：站址 `0x14`/`0x2c` 的值 `0x0098DFA4`） | 键 = 站点已证；值列 1,063 个互异取值 | 与 U1 同批：在 U1 的差分实验里，若某条命令只用 `maps[0]` 引用，其值列即可被读出 |
| **U3** | `maps[4]` 在 14 个系统脚本里的**非 4 对齐键 / 越界键**（253 + 317 条） | 键 %4 ∈ {1,2,3}，或 > 代码区长度 | 单文件实验：`history.sob` 最集中（76 条）。把这 76 个键周围的字节与 `s01_0*` 的同形段对比，判断是「键不是地址」（则系统脚本的 maps[4] 语义不同）还是「我读错了表边界」 |
| **U4** | 高 12 位 `0x00F`（本篇 920 处、前奏诗 122 处）、`0x006`(50)、`0x00D`(5)、`0x009`(3) 的单元 | 值形如 `0x00Fxxxxx` | 逐条列出站点与值（全库不足 1100 条），与 §7.1 的已证 marker 位对照；若这些单元总是出现在**同一类位置**，即可判它们是指令还是数据 |
| **U5** | `user_var.sob` 头部不符本布局 | 表 1 条数读出 `0xFFFFFFFF` | 单文件分析（1 个文件，量极小） |
| **U6** | 「页号」是否**兼作** VM 的类型标签（即 VM 是否按高 12 位分派） | 页号随装载槽变化这一点已证；「是否兼作类型」**未定** | **引擎侧实验（一次性定案）**：① 找原盘 `Lucifen Library & Tools`（`pack.exe`，汉化源工程 `text/pack.py` 曾调用 `.\lucifen\build\pack.exe`，本工作区只有 `lucifen.cpp` 源码、缺 `build\`）；② 反汇编 `ORE_TUBA.EXE` 里的脚本装载/分派函数，读 `(w >> 20)` 或 `(w & 0xFFF00000)` 的用法 |

---

## 十一 · 对「还原 214 场」的可操作含义（A 路能给的）

1. **不能靠 opcode 直接解出这 214 场**——项流文法（U1）未解，任何「解码器」目前都会在 5%–20% 的位置上卡住。
   A 路不主张现在写解码器；主张**先做 U1 的差分实验**（成本最低）。
2. **有一条已证、可立即用的替代路径**：§5 的「串池偏移随代码地址严格递减」给出**代码项 ↔ 串池条目的对齐**。
   而**演出令牌本身就是串池里的串**（已实测：`(0,0,1)(400,300,2)`、`(800,600,1)(400,300,2)`、`a0 c`、`100>3 300<> c`、
   `300c_ 100$ $`、`$_ $_`、`<3+3`、`ScSkip`、`EyeCatch`、`PIC\*.ELG`、`SE\*.OGG` 全在 `s01_02a` 串池内，
   且**坐标串与立绘令牌在串池里彼此相邻**）。⇒ **不依赖 opcode 语义**，仅按「代码地址升序 = 脚本正序」即可把
   这些令牌还原成**有序序列**，并可用项流里**紧邻同一令牌的整数字**（如坐标串前后的 `0x1`、`0xC8`=200、`0x80`=128、
   `0x12C`=300、`0x1F4`=500）**作为候选参数**去和 PSV 金标对拍。
   这条路径的**边界**：给出的是「顺序 + 邻域候选参数」，**不含**「哪个参数是 cx/cpri/时长」的绑定（那属语义层）。
3. **给解码器作者的硬约束（三条）**：
   - 别用 `高12位 == 0x018` 当文本判据（R/AfterStory 会全空）；
   - 别把 `maps[4]` 当纯字符串表（它同时覆盖代码区引用）；
   - 别假定「REF 的前一个词一定是它的 tag」（`1F/20/17` 处会错位）。

---

## 附 · 复算命令（照抄可复现；`cd` 到 `E:\ZCode Workspace\Galgame`）

```bash
# 1) 容器 + 六表 + 串区（改 SOB 路径即可复算任一文件）
python -c "import struct;d=open(r'工程/我们没有翅膀/解包/SCRIPT/s01_02a.sob','rb').read();ts=struct.unpack_from('<I',d,4)[0];te=ts+8;off=8;maps=[]
while off<te:
    wp=struct.unpack_from('<I',d,off)[0];off+=4;maps.append(dict(struct.unpack_from('<II',d,off+8*i) for i in range(wp)));off+=8*wp
ss,se=struct.unpack_from('<II',d,te);print(d[:4],hex(ts),hex(te),[len(m) for m in maps],hex(ss),hex(se),'he',hex(te+8),'cells',ss//4)"

# 2) maps[1]/maps[3]/maps[4] 的规则（全库逐条，非抽样；482 文件约 10 秒）
python -c "
import struct,glob,collections
def load(p):
    d=open(p,'rb').read(); ts=struct.unpack_from('<I',d,4)[0]; te=ts+8; off=8; maps=[]
    while off<te:
        wp=struct.unpack_from('<I',d,off)[0]; off+=4
        maps.append(dict(struct.unpack_from('<II',d,off+8*i) for i in range(wp))); off+=8*wp
    ss,se=struct.unpack_from('<II',d,te); return d,maps,te+8,ss,se
c1=collections.Counter(); c3=collections.Counter(); c4=collections.Counter(); ov=collections.Counter()
for p in glob.glob('工程/我们没有翅膀/解包/SCRIPT/*.sob')+glob.glob('工程/我们没有翅膀 前奏诗/解包/SCRIPT/*.sob'):
    if open(p,'rb').read(4) not in (b'SOB0',b'SOB1',b'SOB2'): continue
    try: d,maps,he,ss,se=load(p)
    except Exception: continue
    code=d[he:he+ss]
    for k,v in maps[1].items(): c1[struct.unpack_from('<I',code,k)[0]-v]+=1
    for k,v in maps[3].items(): c3[struct.unpack_from('<I',code,k)[0]-v]+=1
    for k,v in maps[4].items():
        if k+4<=len(code): c4[(struct.unpack_from('<I',code,k)[0]&0xFFFFF)-v]+=1
    s=[set(m) for m in maps]
    ov[sum(len(s[i]&s[j]) for i in range(6) for j in range(i+1,6))]+=1
print('map1 cell-value:',c1.most_common(2)); print('map3 cell-value:',c3.most_common(2))
print('map4 distinct per-file consts:',len(c4),'entries',sum(c4.values())); print('overlap hist:',dict(ov))"

# 3) 某文件自身的页号与基址（s01_03c1 的页号 0x017 由此得出）
python -c "import struct;d=open(r'工程/我们没有翅膀/解包/SCRIPT/s01_03c1.sob','rb').read();ts=struct.unpack_from('<I',d,4)[0];te=ts+8;off=8;maps=[]
while off<te:
    wp=struct.unpack_from('<I',d,off)[0];off+=4;maps.append(dict(struct.unpack_from('<II',d,off+8*i) for i in range(wp)));off+=8*wp
ss,se=struct.unpack_from('<II',d,te);he=te+8;code=d[he:he+ss]
print('maps4 tags',{hex(struct.unpack_from('<I',code,k)[0]>>20) for k in maps[4]})
print('B',hex(min((struct.unpack_from('<I',code,k)[0]&0xFFFFF)-maps[4][k] for k in maps[4])))"

# 4) 「串池倒序」验证（剔除填充串后严格递减）
python -c "import struct;d=open(r'工程/我们没有翅膀/解包/SCRIPT/s01_02a.sob','rb').read();ts=struct.unpack_from('<I',d,4)[0];te=ts+8;off=8;maps=[]
while off<te:
    wp=struct.unpack_from('<I',d,off)[0];off+=4;maps.append(dict(struct.unpack_from('<II',d,off+8*i) for i in range(wp)));off+=8*wp
ss,se=struct.unpack_from('<II',d,te);m4=maps[4];from collections import Counter
v=sorted((a,x) for a,x in m4.items() if ss<=x<se);fill=Counter(x for a,x in v).most_common(1)[0][0]
w=[(a,x) for a,x in v if x!=fill];print('filler',hex(fill),'entries',len(w),'strict dec',all(w[i][1]>w[i+1][1] for i in range(len(w)-1)))"

# 5) 已证项形 [1F][载荷][载荷]
python -c "import struct;d=open(r'工程/我们没有翅膀/解包/SCRIPT/s01_02a.sob','rb').read();ts=struct.unpack_from('<I',d,4)[0];he=ts+16
for a in range(0x038,0x070,4): print(hex(a),'%08x'%struct.unpack_from('<I',d,he+a)[0])"

# 6) TOB0（R 版 / AfterStory，另一种容器：无 maps[]，字节流 + 5B 20 记录头；对齐不固定）
python -c "import struct,glob;d=open(sorted(glob.glob('工程/我们没有翅膀R/语料/R版SCRIPT/*.tob'))[0],'rb').read()
B=struct.unpack_from('<I',d,8)[0];cs=0x2e+4*B;pos=[];i=0
while True:
    j=d.find(b'\x5b\x20',i)
    if j<0: break
    pos.append(j);i=j+1
import collections;print('TOB0 magic',d[:4],'code_start',hex(cs),'5B20 count',len(pos),'mod4',dict(collections.Counter(x%4 for x in pos)))"
```

### 交付边界

- 本报告**只写结构**（怎么切分、怎么定位、怎么还原指针）。**不含任何语义主张**，故不需与 PSV 金标对拍；
  与 PSV 冲突的可能性只出现在 §11.2 建议的「令牌序 + 邻域参数」路径上（那是第二波的事）。
- A 路**未产出**解码器脚本（任务书要求「不要写脚本进工作区」）；§9 的伪代码是骨架，
  它在 `s01_02a` 上会抛 `Undecided` 约 1244 次，**不足以当解码器使用**——这一点必须原样传达给第二波。
