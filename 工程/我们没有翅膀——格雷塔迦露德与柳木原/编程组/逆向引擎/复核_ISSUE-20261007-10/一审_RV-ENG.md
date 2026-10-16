# 一审（RV-ENG）· 逆向引擎「V=func_lib 偏移 + 装载期重定位」复核

**结论：打回。**

> 打回**不是**因为核心论断错——被审四条核心论断（V 是 func_lib 缓冲偏移 / 装载器 `sub_424D30` 对 `maps[3]` 做 `code[key]=V+[this+0xD4]` / `[this+0xD4]` 在 func_lib 装载（`push 1`）时被赋值 / 「无 switch、无命令名表，身份由指针重定位承载」）**我逐条独立复算，全部成立**（A 节给出自己写的脚本与真实输出）。
> 打回的是**两处可复现的事实/方法缺陷**（B-1 的全 `.text` 扫描实际只覆盖 8.9%、C-2 的命令节点计数与其自述判据不符）——都在 deliverables 里会被后续工序当事实引用，必须修正后再入库。修正量很小（改 `skipdata` + 改一个数字/口径），不需要重做机制论证。

- 日期：2026-10-07 ｜ 审查者：reviewer（RV-ENG，独立于 editor）
- 被审：`工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\逆向引擎\`（`说明.md`＋7 脚本）、`编程组\SOB0解码\软表解出_说明.md` §13.2
- 我的脚本（全在本目录，只读、不 import `disasm.py`/`pe_min.py`）：`rv_disasm.py`、`rv_push.py`、`rv_data.py`、`rv_variants.py`、`rv_xref.py`、`rv_scan_full.py`、`rv_scan0xd4.py`、`rv_consumer.py`、`rv_strings.py`、`rv_otherd4.py`、`rv_ret.py`
- 写入范围：仅本目录（`子代理工作区\ISSUE-20261007-10\RV-ENG\`）。未改被审文件、未 git、未写 D 盘（D 盘 exe 只读）。
- 目标 exe：`D:\Gal\[Navel]我们没有翅膀\ORE_TUBA.EXE`（1,101,824 B，只读）

---

## A. 独立复核（自己写脚本，真实输出）

### A.0 我自己解析的 PE（`rv_disasm.py`，不 import pe_min）

```
file bytes : 1101824
imagebase  : 0x00400000
entry RVA  : 0x000DC5E5   entry VA 0x004DC5E5
nsec       : 4  optsize 0xE0
  [0] .text    va=0x00001000 vsz=0x000EBA62 rp=0x001000 rsz=0x000EC000
  [1] .rdata   va=0x000ED000 vsz=0x0000DFAA rp=0x0ED000 rsz=0x0000E000
  [2] .data    va=0x000FB000 vsz=0x0003B738 rp=0x0FB000 rsz=0x00009000
  [3] .rsrc    va=0x00137000 vsz=0x000080F8 rp=0x104000 rsz=0x00009000
ddirs: [1]IMPORT 0xF96D0/0xDC  [2]RESOURCE 0x137000/0x80F8  [12]IAT 0xED000/0x48C
```
与被审 `pe_min.py` 实测输出（我另跑了 `python -X utf8 pe_min.py`）**逐字段一致**（imagebase/entry/4 节/3 个数据目录）。`.text` 内 `vaddr==rawptr==0x1000`，故 **`.text` 内 RVA==文件偏移成立**（★但 `.rsrc` 是 `va=0x137000/rp=0x104000`，二者不等——见提示 P3）。

### A.1 论断 1 复算：V 值域 / 4 对齐 / max<se

自写容器解析（`rv_data.py`，不 import `decode_sob0`），遍历 `SCRIPT` 下 411 个可解析 `.sob`（`user_var.sob` 因表条数 `0xFFFFFFFF` 越界，脚本按异常跳过——与被审脚本同现象）：

```
func_lib: magic=SOB2 table_end=102112 ss=175052 se=177978 header_end=102120 filesize=280098
六表条数 = [1343, 805, 0, 0, 10612, 0]
SCRIPT 下 *.sob = 413，排除 func_lib = 412，可解析 = 411（user_var.sob 跳过）

== maps[3] 全体（未过滤）==
总项 = 112621   其中 <0x100000 = 112621（即全部 <0x100000）
不同 V = 93   值域 = [0x2C3C, 0x2A4B4] = [11324, 173236]
全 4 对齐 = True
max(V)=173236 < func_lib.se=177978 ? True
max(V)=173236 < func_lib.ss=175052 ? True   （★更强：V 全落**代码区** [0,ss)，非串区）
V//4 上界 43309 < cells 数 43763 ? True      （V 是合法 cell 下标）
```
**论断 1 全部数字逐位复现**：值域 `[0x2C3C,0x2A4B4]`、93 值、全 4 对齐、max `173236` < `177978`。且我加验了一条被审文档未写、但更强的结论：`max(V) < ss`，故 V 落在**代码区**而非串区。

### A.2 论断 2 复算：装载器 VA 0x424D30–0x424EC0 逐条反汇编

`rv_disasm.py` 从 **0x424D30 函数入口**线性反汇编到 0x424EC0，逐条核对被审文档引用的 4 个地址：

| 被审引用 | 我的反汇编（真实输出） | 判定 |
| --- | --- | --- |
| `0x424EA1 mov edi,[esi+0xD4]` | `0x00424EA1  8B BE D4 00 00 00   mov edi, dword ptr [esi + 0xd4]` | ✅ |
| `0x424EB0 mov [ebx+ecx],eax` | `0x00424EB0  89 04 0B   mov dword ptr [ebx + ecx], eax` | ✅ |
| `0x424E9B mov ecx,[ebp]`（off） | `0x00424E9B  8B 4D 00   mov ecx, dword ptr [ebp]` | ✅ |
| `0x424EAD add eax,edi` | `0x00424EAD  03 C7   add eax, edi` | ✅ |

循环 D（maps[3]）完整结构（我的输出）：
```
0x424E91  mov edx,[ebp]        ; 表条数
0x424E9B  mov ecx,[ebp]        ; off = 键（代码区字偏移）
0x424E9E  mov eax,[ebp+4]      ; value = V
0x424EA1  mov edi,[esi+0xD4]   ; 库基址
0x424EAD  add eax,edi          ; V + 库基址
0x424EB0  mov [ebx+ecx],eax    ; code[off] = V + [this+0xD4]
0x424EB3  jne 0x424E9B
```
**完全成立**：`maps[3]` 的键 = 写入位置，值 = V，写入内容 = `V + [this+0xD4]`。顺带核对循环 A/B/C/E 与 §3.2 表一致：
- A(`0x424E25`) `mov edx,[esi+0x58]` + `lea eax,[eax+eax*2]` + `[edx+eax*4]` → 12 B/条（键写入 `code[off]`）；
- B(`0x424E4A`) `mov edx,[esi+0x38]` + `[edx+ecx*4]` → 4 B/条；
- C(`0x424E6C`) `mov edx,[esi+0x48]` + 12 B/条；
- E(`0x424EB5`) `add ecx,ebx` → `value + 模块缓冲基址`；
- `0x424ED3 cmp dword [ebp],0 / je`，否则 `mov eax,3`（0x424ED9）→ maps[5] 计数须为 0，否则返回 3。
- 函数尾 `0x00424F97  C2 10 00  ret 0x10` → **__thiscall、4 个栈参数**，与被审签名 `load(this,data,name,idx,is_lib)`（ECX=this ＋ 4 栈参数）一致。

另：`0x424DD4 call malloc → ebx` → `0x424DEB rep movsd`（`ecx=se`），故 `ebx` 确为「代码区+串区」合并缓冲基址（`se` 字节），`[ebx+ecx]` 即缓冲内偏移寻址。**成立。**

### A.3 论断 3 复算：`push 1` / `push 0` 与调用关系

我的原始字节与反汇编（`rv_push.py`）：
```
VA 0x004248D8 : 6a 01 83 c0 04 57 68 0c ...
0x4248D8  6A 01              push 1
0x4248DA  83 C0 04           add eax,4
0x4248DD  57                 push edi
0x4248DE  68 0C C3 4F 00     push 0x4FC30C      ; "FUNC_LIB"
0x4248E3  50                 push eax           ; data(去 magic)
0x4248E4  8B CD              mov ecx,ebp        ; this
0x4248E6  E8 45 04 00 00     call 0x424D30
前置：0x4248B2  cmp dword ptr [eax],0x32424F53   ; 'SOB2'
      0x4248B8  je 0x4248D8                        ; magic==SOB2 ⇒ 走 push 1 支路

VA 0x004250DA : 6a 00 57 55 50 8b ce e8 ...
0x4250DA  6A 00              push 0
0x4250DC  57                 push edi
0x4250DD  55                 push ebp
0x4250DE  50                 push eax
0x4250DF  8B CE              mov ecx,esi
0x4250E1  E8 4A FC FF FF     call 0x424D30
```
- 参数序（右至左）核对：FUNC_LIB 处最后压入的 `eax` = arg1(data)，其前 `0x4FC30C`=arg2(name)，`edi`=arg3(idx)，最先 `push 1`=arg4(is_lib)。函数内 `0x424EE3 mov al,byte [esp+0x38]` = **arg4**（我按 SEH 序言逐字节算栈偏移：`mov esi,[esp+0x28]`=arg1、`[esp+0x38]`=arg4，自洽）⇒ `push 1` 即 `is_lib=1`。

- **is_lib 分流**（我的输出）：
```
0x424EE3  mov al,byte [esp+0x38]
0x424EE7  test al,al
0x424EE9  je   0x424EF3
0x424EEB  mov  dword ptr [esi+0xd4], ebx   ; flag=1 ⇒ 0xD4 = 该模块缓冲基址
0x424EF1  jmp  0x424F0B
0x424EF3  lea  edi,[esi+4]
0x424EF9  mov  dword ptr [esi+0xd8], ebx   ; flag=0 ⇒ 0xD8 = 该模块缓冲基址
```
⇒ func_lib（`push 1`）装载时 `[this+0xD4]=func_lib 缓冲基址`；场景（`push 0`）装载**只写 0xD8，不碰 0xD4**。⇒ 场景 `maps[3]` 重定位用的仍是 func_lib 基址。**成立。**

### A.4 独立枚举 0x424D30 的全部调用者（`rv_xref.py`，我自己扫 .text 的 E8/E9 rel32）

```
== 调用 0x424D30 的位置（E8 rel32）==
  VA 0x004248E6  opcode 0xE8  (func_lib,  push 1)
  VA 0x004250E1  opcode 0xE8  (scene,     push 0)
立即数 30 4D 42 00 出现处：共 0 处
```
**全 `.text` 仅这两个直接调用者**，一个 `push 1` 一个 `push 0`。⇒ 不存在「第二个库也用 push 1 装载、把 0xD4 覆盖掉」的可能。这独立佐证了论断 3。

### A.5 论断 4（无 switch / 无命令名表）与「0xD4 会被别处改写吗」的反证尝试

见 B 节。

---

## B. 反证尝试（≥1 个替代解释，逐一检验）

### B-1 替代解释：「`+0xD4` 存的不是 func_lib 基址，而是别的东西」

- **反证手段**：全 `.text` 反汇编，列出所有写 `[reg+0xD4]` 的点（`rv_scan_full.py`，`skipdata=True` 全量 361,825 条），再看有没有覆盖 manager.0xD4 的写。
- **结果**：写 `[reg+0xD4]` 的有很多（不同类），但与 **script manager 同类**的只有两处：
  - `0x00422331 mov dword ptr [esi+0xd4], ebx` —— 我反汇编该处上下文（`rv_otherd4.py`），它是**manager 构造函数**：`0x422311 mov dword ptr [esi],0x4EDEF0`（写 vtable）、`0x42231C [esi+0x74]=ebx`、`0x42231F [esi+0x98]=ebx`、`0x422325 [esi+0xBC]=ebx`、`0x42232B [esi+0xC0]=ebx`、`0x422331 [esi+0xD4]=ebx`、`0x422337 [esi+0xFC]=ebx`…… 其中 `+0x74/+0x98/+0xBC` 正是被审 §3.1 认定的 USER_VAR 三缓冲 ⇒ **同一类**，此处把 `0xD4` 初值置 0（`ebx`）；
  - `0x00424EEB [esi+0xD4]=ebx` —— func_lib 装载（A.3）。
  - 其余 `+0xD4` 写点（如 `0x433F76`/`0x43432F` 等）上下文是**别的类**（写 `+0xB3/+0xB4/+0xDC/+0xEC/+0xF0=-1` 等，字段布局不同）。
- **判定**：替代解释**不成立**。manager 的 `+0xD4` = 构造时 0 → func_lib 装载时 = func_lib 缓冲基址；场景装载不写它。**论断 3 反而被加强。**

### B-2 替代解释：「V 不是 func_lib 偏移，而是共享页基址 + 偏移」

- 重定位式子 `code[key] = V + [this+0xD4]`，而 `[this+0xD4]` 被显式赋值成「以 `push 1` 装载的那个模块的 `malloc(se)` 缓冲基址」（A.3/A.4）。所以运行期指针 `= func_lib 缓冲基址 + V`，无论你怎么称呼 V，它**都是 func_lib 缓冲内的偏移**。且 `max(V)=173236 < ss=175052`，落在**代码区**内（A.1）。
- **判定**：替代解释**不成立**。

### B-3 替代解释：「那段不是装载器，是别的函数」

- 该函数（0x424D30）**唯一被调用**的两处分别是「读 FUNC_LIB.SOB 后按名装载」与「按名装载场景 `SCRIPT\%s.SOB`」（`rv_xref.py`：只有 0x4248E6 属 `sub_424460` 的 FUNC_LIB 分支；0x4250E1 属 `sub_424FA0` 场景装载，函数头 `0x424FBD mov esi,ecx`、`0x424FD5 push "…%s.SOB"` 的调用点）。它读 `magic` 后的 table_size、6 表、`ss/se`，`malloc(se)` 后整段拷贝——正是**容器装载 + 六表重定位**。函数尾 `ret 0x10`。
- **判定**：替代解释**不成立**。

### B-4（顺带）反证：「场景装载时用的 manager 与 func_lib 装载时不是同一个对象」

- 未完全证死，但强证据：两类上下文都触碰同类字段（`+0x74/+0x98/+0xBC` USER_VAR 三缓冲、`+0xF0/+0xF4` 模块记录、`+0xD4/+0xD8`）；且 `sub_424460` 与 `sub_424FA0` 都以 `ecx=this` 调 `sub_424D30`。manager 是单例（被审称存于 app `+0x19C8`）。**我未独立回溯两处 call 点的对象来源到同一实例**（见 D/核不到），故标为「高可信、未 100% 证死」。这**不构成打回**。

### B-5（★重要：我发现的**反证方向**缺陷）——「全 `.text` 扫描」其实只扫了 8.9%

这是本次审查最实质的问题，属**方法缺陷**（不是机制反证）。

`rv_scan_full.py` 实测：
```
skipdata=False: 32790 条，最后地址 0x00418EA1（.text 末应 ~0x004ED000）
  停止文件偏移 ≈ 0x018EA4   停止点字节: d9 8b 41 00 e4 8b 41 00 ...
skipdata=True : 361825 条，最后地址 0x004ECFFE，覆盖到 .text 末 ? True
```
- 被审 `disasm.py` **第 21 行 `md.skipdata = False`**。capstone 在 `0x418EA1` 撞上内嵌数据表（`8B 41 00 E4 8B 41 00…` 是 .text 内的一张 dword 表）即**停止**。
- 我实跑被审工具：`python -X utf8 disasm.py --rva 0x1000 --len 0xEC000 | wc -l` → **32790**，正是被审 `说明.md` §六自述的「全 `.text` 反汇编 **×3.4 万指令**」。
- **真值：`.text` 可反汇编 361,825 条；被审只覆盖 32,790 条 = 9.06%。** 即 §六「全 `.text` 反汇编」**是假的**，随后的「管理器字段访问 180 处」「`+0x58/+0x38/+0x48` 命中 90+ 处」都建立在 9% 采样上，**据此下的「解释器主循环未定位」负结论不成立**。
- 更糟：`[esi+0xD4]` 的**消费点其实就在被扫到的那 9% 里**，而被审文档未引用——`rv_consumer.py` 实测：
  ```
  0x00425232  mov eax,dword ptr [esi + 0xd4]   ; 若非 0 → [esi+0x24..0x28) 列表处理分支
  0x00425293  mov eax,dword ptr [esi + 0xd4]   ; 若非 0 → 压缩/搬移该列表
  ```
  这两处读 `[this+0xD4]` 并按非零分支处理（紧邻场景装载 `sub_424FA0`，属另一函数），**是本作「0xD4 被当缓冲指针消费」的正面旁证**，被截断的扫描错过/未采用。

**B 节结论：核心机制的三条反证全部失败 ⇒ 论断 1/2/3 成立；但发现审查对象的方法缺陷（全 `.text` 假象）——见 打回项 R1。**

---

## C. 过度解读检查

### C-1 V 处内嵌串（`bg_zoom` 等）标注是否足够？
- 我按自写解析（`rv_strings.py`）**逐条复现** 被审 §5.1 全表（窗口 0x120 首次非空串）：
  ```
  V=0x00FDF4  want='bg_zoom'@0x68          got='bg_zoom'@0x68          OK
  V=0x013300  want='bg_blur'@0x68          got='bg_blur'@0x68          OK
  V=0x010150  want='bg_move'@0x100         got='bg_move'@0x100         OK
  V=0x0186C8  want='sp_move'@0x100         got='sp_move'@0x100         OK
  V=0x02A150  want='cross'@0x114           got='cross'@0x114           OK
  V=0x02A4B4  want='rule'@0x114            got='rule'@0x114            OK
  V=0x01E45C  want='SYS\RULE%03d.ELG'@0x2C got=同上                    OK
  V=0x01E634  want='SYS\%s.ELG'@0x2C       got=同上                    OK
  V=0x024F1C  want='SYS/SM_BG2.GMP'@0xC0   got=同上                    OK
  ```
- 跨界声明亦**逐条复现**：窗口 0x400 时 `0x1B040` → `zoomflip@0x1B0/…`（432/608/820/1016）；`0x1A15C` → `cross@364 / cross@808 / SYS\RULE%03d.ELG@916`。
- **判定：标注基本足够**。被审已写 ⚠️「窗口可能跨界……只取 0x120 内首个串，仍标中/低，须对拍」，且 §5.3 声明「未出现者留空、不编」。这是诚实且自洽的。**唯一可加一处**（提示 P2）：无论窗口多小，只要**节点边界未知**，`+0x68`/`+0x100`/`+0x114` 处的串仍可能是**相邻节点**的；尤其 `0x2A4B4`（节点数 1）取到 `+0x114` 处的 `rule`，几乎确定是邻节点串。建议在 §5.1 明确一句「V 的节点长度未解 ⇒ 表内串**不保证属于 V 的节点**，采纳前须先解出节点边界」，并把 `0x2A4B4` 这类「节点数 1 却取到远端串」的直接降为「不足以定名」。当前已标「低（样本 1）」，方向正确，措辞可再硬。

### C-2 命令节点计数（★须修正）
- `说明.md` §1.1 写：`其中构成「命令节点」[4][V][0C][k][3][REF] 的 V | 82 个不同值，共 110,888 节点`。
- `rv_variants.py` 实算（两种判据）：
  ```
  V1 严格：+尾REF空串 +maps[3]键    :  75 值 /  52984 节点
  V2 松动：无尾REF  +maps[3]键      :  82 值 / 110888 节点
  V3/V4 遍历 maps[3] 键看形态       :  82 值 / 110888 节点
  ```
  ⇒ **82/110,888 来自「不带空串 REF」的松动判据**（正是被审 `t1_evidence_dump.py` 的实际代码，我实跑也输出 82/110888）；而被审 §1.1 的方括号**写了 `[REF]`**（同 `decode_sob0.command_nodes` 的定义），按该定义真值是 **75/52,984**。
- **判定：过度标注/数字与自述判据不符**——见 打回项 R2。（对「93 值」的结论无影响，因为 93 是 `maps[3]` 全体值集。）

### C-3 论断 4「无 switch / 无命令名表」
- 机制（重定位式分派）已实测成立；「无 switch、无命令名表」是**由机制推出的否定性结论**，被审 §4.3 已自限：「未定位解释器循环……指针由节点遍历器消费」。**属诚实边界，可接受**。但注意：B-5 表明支撑该否定性结论的「全 `.text` 搜索」并不全，故该结论的证据强度应随 R1 修正后再评。建议 §六 把「全 `.text`」改为「.text 前段（0x401000–0x418EA1）」，并补一次覆盖到 0x4ED000 的搜索。

---

## D. 可复跑性（实跑贴真实输出）

被审 7 个脚本我**全部实跑**（`PYTHONDONTWRITEBYTECODE=1` 防写 `__pycache__`；`GRETA_DATA_ROOT` 取默认 `E:\ZCode Workspace\Galgame`）。均为**只读**（`decode_sob0` 只被 import、不落盘）：

| 脚本 | 实跑结果 | 与被审自报 |
| --- | --- | --- |
| `pe_min.py` / `--imports` | imagebase 0x400000、entry VA 0x4DC5E5、4 节、IMPORT 0xF96D0；导入 **10 个 DLL**（KERNEL32/USER32/GDI32/…/ole32） | 数值一致；**但 §二「导入仅 2 个 DLL」** → 见提示 P1 |
| `t1_v_hypothesis.py` | 「ot 全库命令节点 53769 个（413 文件）」「不同 V 173 个」 | 该脚本判据=REF+maps[3] 无关，输出与 §1.1 的 82/110888 非同一口径（见 C-2） |
| `t1_v_vs_funclib.py` | 「ot 文件 411，真实 V 93 个」「code targets 8812」「命中 41/93」「≤4:55 ≤16:28 ≤64:10」「首字 0xb×51 0x20×30…」 | **逐条与 §1.2 一致** |
| `t1_evidence_dump.py` | 「真实 V 82 个 / 110888 节点；值域[0x2C3C,0x2A4B4]；max<se True；全 4 对齐 True；假阳性 0」 | **与 §1.1 一致**（惟判据见 C-2） |
| `t3_funclib.py` | 「reverse map size 340」，14 个 V 的描述符列表 | 可跑通 |
| `t4_table.py` | 全表（`0x002C3C 57859 0x0B`…`0x0186C8 sp_move@0x100`…） | 可跑通 |
| `t4_v_refs.py` | `0x01A96C … strings=['trans']`、`0x01B69C …['quake']`、`0x0186C8 …['sp_move']` … exit=0 | 可跑通 |
| `disasm.py`（`--rva/--off/--xref/--find-funcs`） | `--xref 0x4FC318` 命中 `0x424898`；`--rva 0x1000 --len 0xEC000` → **32790 行**（截断） | **截断缺陷见 R1** |

**结论**：脚本本身**可复跑、无落盘副作用**（`pe_min.py` 的 image base / entry / 节数与我自写解析**逐字段一致**）。唯一工具缺陷是 `disasm.py` 的 `skipdata=False` 截断。

**核不到（如实登记）**：
1. 我未独立回溯 `sub_424FA0`（场景装载）调用点的 `ecx` 实例是否**同一** manager 单例（B-4）——只证到同类字段与同函数调用约定。卡点：需动态调试点或静态回溯 app+0x19C8 的构造/传递链，本轮未及。
2. 被审 §3.3「`0x425080` 在 `[this+0xF0]` 的 0x28 B 记录里按名查索引」我未逐字节复算（与四条核心论断无关，未投入）。
3. `[this+0x58]` 内建符号表填充点——被审自述「未定位」，我亦未定位（一致）。

---

## 打回项（必须先修正）

### R1【方法/事实】`disasm.py` 的 `.text` 反汇编被截断，§六「全 `.text` 反汇编 ×3.4 万指令」为假
- **位置**：`逆向引擎\disasm.py:21`（`md.skipdata = False`）；`说明.md` §六 表「解释器主循环」行（第 295 行）。
- **触发条件**：任何用 `disasm.py` 对 `.text` 做「整段」反汇编的操作。
- **影响**：`.text` 实际可反汇编 **361,825** 条，被审只得到 **32,790** 条（=9.06%），在 `0x418EA1` 撞内嵌数据表即停；「180 处 / 90+ 处」及「解释器主循环未定位」的负结论建立在 9% 采样上，**证据不足**；且漏掉 `[this+0xD4]` 的消费点 `0x425232/0x425293`（就在已扫区内，属未采用）。
- **修复建议**：① `disasm.py` 第 21 行改 `md.skipdata = True`（或改分段续扫，遇坏字节跳 1 再续）；② §六 把「全 `.text` 反汇编 ×3.4 万指令」改为「.text 前段 `0x401000–0x418EA1`（32,790 条，约占 9%）」，并**补一次覆盖到 `0x4ED000` 的全量扫描**后重述「未定位」结论；③ 补登记消费点 `0x425232`/`0x425293`。

### R2【事实/口径】§1.1「命令节点 = 82 值 / 110,888 节点」与其自述判据 `[4][V][0C][k][3][REF]` 不符
- **位置**：`说明.md` §1.1 表第 37 行；对应脚本 `t1_evidence_dump.py`。
- **触发条件**：按方括号所写的 `[REF]`（空串 REF）判据重算。
- **影响**：带 `[REF]` 的真值是 **75 值 / 52,984 节点**；`82/110,888` 是**不带 REF**判据的结果。数字虽可由 `t1_evidence_dump.py` 复现，但与该行标注、与 `decode_sob0.command_nodes` 的定义（含 REF）不一致——后续工序据此会**把命令节点规模高估约 2 倍**。
- **修复建议**：二者择一改齐——(a) 若坚持 `[REF]` 定义，把 82/110,888 改为 75/52,984，并在 `t1_evidence_dump.py` 补空串 REF 判据；(b) 若保留 110,888，则把方括号改为 `[4][V][0C][k][3]`（无 REF），并说明这是「V 位形态」而非 `decode_sob0` 的命令节点定义。**推荐 (a)**（与 `decode_sob0` 口径统一）。

---

## 提示（不阻塞，建议一并改）

- **P1**：`说明.md` §二「**导入仅 2 个 DLL**」**错误**——实测导入表 **10 个 DLL**（KERNEL32 126 / USER32 93 / GDI32 24 / ADVAPI32 5 / SHELL32 8 / COMCTL32 3 / IMM32 9 / WINMM 8 / comdlg32 2 / ole32 3）。删掉「仅 2 个」或改为 10 个。
- **P2**：§5.1 建议加一句「V 的节点边界未解 ⇒ 窗口内串**不保证属 V 节点**」，并把「节点数 1 却取远端串」的 `0x2A4B4`（`rule@0x114`）显式降为「不足以定名（仅登记发现）」；当前措辞方向正确，可更硬。
- **P3**：§二「（`.text vaddr=rawptr=0x1000 size=0xEBA62`，**其余同名**）」易误读——`.rdata/.data` 的 `va==rp`，但 **`.rsrc` 是 `va=0x137000` ≠ `rp=0x104000`**。「`.text` 内 RVA==文件偏移」这句是**对的**，但「其余同名」不是全对；建议只保留「`.text` 内 RVA==off」。
- **P4**：`pe_min.py` 无功能错误；`disasm.py --rva X --len Y` 靠 `args[3]` 取长度（隐含假设 `--len` 在固定位置），建议改正规参数解析以免日后误用。
- **P5**：`说明.md` §2 复跑命令里的 `t1_v_hypothesis.py` 判据（报 173 值，含页引用字）与 §1.1 的 93 值不同口径，建议在命令旁注明，免得读者对不上数。

---

## 复核覆盖声明（我查了哪些关键路径）

- 论断 1：自写容器解析，411 文件全遍历，逐位复算值域/数量/对齐/max<se。
- 论断 2：自写 PE 解析 + 从函数入口线性反汇编 0x424D30–0x424EC0，逐条核对 4 个被引地址与循环 A–E 结构、`ret 0x10`。
- 论断 3：核对 0x4248D8/0x4250DA 原始字节与上下文、栈偏移（arg4=`[esp+0x38]`）、is_lib 分流写 0xD4/0xD8；**全 .text 枚举 0x424D30 调用者（仅 2 处）**；manager 构造函数（0x422331）核对同类。
- 论断 4：机制确认；否定性结论的证据强度受 R1 影响。
- 反证：0xD4≠func_lib 基址 / V 非偏移 / 非装载器 —— 三者均被数据否证；发现方法缺陷 R1。
- 过度解读：§5.1 串逐条复现、跨界声明复现；§1.1 计数口径问题 R2。
- 可复跑：7 脚本全跑通、贴真实输出；`pe_min.py` 数值与我自写解析逐字段一致；`disasm.py` 截断实测。

（本报告 100% 基于我自己的脚本输出与此前实跑结果，未编造；核不到项已在 D 节列出并注明卡点。）
