# R 装载与受控系统入口：阶段证据

ISSUE-20261011-02，2026-10-11。editor-easy 提供实现；root 执行独立原机器码对照并集中复核。本目录是小型元数据证据，不含原 EXE、原始脚本正文、素材或凭据。

## 已验证范围

| 证据 | 实际范围 |
| --- | --- |
| R_22容器原码重定位核验.json | R 22 SOB0/SOB2 容器、42,690 处重定位；独立装载工具与原 0x4A6E7B..0x4A6F39 五个循环的输出逐字节一致。变量/named 向量字段取合成值；native 向量取 809 个静态候选地址。 |
| R_SOB1声明与原码核验.json | user_var.sob 的 3,724 字节数据、768 条十字节声明、3 个数组槽、2 处局部指针。原 0x4A6BB8..0x4A6C1A 地址后处理及 0x4A6C1A..0x4A6C67 数据修正均一致；额外 save/undo 副本开关置零。 |
| R_main受控入口轨迹.json | 原 main、func_lib 和声明数据，在 retAppProc 原始输入字 0/1 的夹具中运行到首 native 前；输入 0 传入 GameInit，输入 1 到槽 35。两者原生函数体均未执行。 |
| R_控制栈原码核验.json | 原 0x4A79D0/4A79F0/4A7A10 的初始化压零、挂起压 PC、恢复弹 PC；合成 context。 |
| 装载器_边界与负控.json | 原型阶段 14 项边界/异常检查，涵盖数据未对齐允许、代码未对齐/重叠/越界/非空 table5 拒绝、u32 加法及畸形 SOB1。 |
| 装载器_回归与有效负控.json | 独立工具 4 个回归测试通过；内存中恢复旧基址守卫错误导致两个断言失败，负控有效。新增 thiscall 助手拒绝无限跳转，次数限制停机不能冒充返回。 |
| 交付来源.json | editor-easy 候选与失败请求的收据、成熟解析器提取来源。模型停止或进程退出本身不作验收。 |

## 复用与复跑

实现位于同工程 `编程组/工具/lucifen_sob_loader.py`，仅标准库；SOB0/SOB2 结构解析从旧 B0 的四个 AST 定义逐字提取，其他 B0 实现未纳入。本工具不依赖 `原作语义/source_ir.py` 导入。SOB1 独立解析，未知 flags/extra 原样保留；`tail_fileoffset` 是末尾 reserved_count 字段偏移。bind_sob1 使用调用方提供的有效数据/数组槽分配地址，不负责分配、存档和释放。

在工作区 PowerShell 执行标准库回归：

```powershell
python -X utf8 -B "工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/test_lucifen_sob_loader.py" -v
```

原机器码核验需要只读原 `备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE`、`工程/我们没有翅膀R/语料/R版SCRIPT/`、前一批 `R接口证据_20261011/R_注册顺序.json` 与工作区便携 Unicorn 2.1.4（`工具/unicorn-2.1.4-py314/`）。原 EXE SHA256 为 `b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`。这些原作/第三方大文件不入库，不能声称裸 clone 已携带它们。

root 独立核验命令通过平台运行；本批已对最终装载工具重跑全部 22 个容器和 SOB1/控制栈。CPU 核验的输入身份、起止地址、受控值、比较哈希在 JSON 中；本批尚未提供一个封装所有 CPU 核验的独立 CLI。

重定位客体配置：mgr=0x1000000，modulebase=0x3000000，reloc表=0x4000000，三向量区=0x5000000/0x5100000/0x5200000，func_libbase=0x6000000；module 和表按实际长度向上取 4 KiB 映射。0/2 向量为 stride12 记录的第一字段，1 为 stride4 函数地址。原循环 ESI=mgr、EBX=modulebase、EBP=表；ESP=0x2008000，栈+0x20=mgr+0x20。结束必须 EIP=0x4A6F39，再比较整个 module 缓冲区。R 数据有 84 处非四对齐写入，不能套用代码区对齐规则；gallery 缓冲区 292,209 字节，不能使用微用例的固定小缓冲布局。

SOB1 后处理客体：database=0x7000000、arraybase=0x7100000、recordbase=0x7200000、local表=0x7300000；记录先按 `<IBBHI>` 填写临时指针、type、flags、0、extra，type1 临时指针为零，其他为 database+offset；mgr+0x54/0x5C/0x60/0x6C 设相应数据库、记录起止与数组槽；EBP=mgr、EBX=local表，ESP 的 +0x164/+0x168 开关置零。分两段执行原码，分别比较全部记录的指针与初始数据。数组槽内容由声明推导提供，不宣称已执行分配器。

## 边界和下一步

原安装实体仍缺失。全部 guest 执行未宿主启动原 EXE，不提供返回值 stub。原 main 轨迹停止于 native 体前；retAppProc 的 0/1 是受控输入字，不是原版启动观测，也不据此断言 BOOL/回调有效类型。早期草稿误猜 ScriptRetnFlg，正式证据依据构造器字符串改为 retAppProc；轨迹指针与字节未变。

下一阶段恢复模块请求和切换状态、分配/释放及挂起恢复的调度契约，再解原生调用参数与 TOB 装载/分派。完整目标剧本、全部 47 指令、原剧情、画面/特效/音频对照和四版本 100% 还原均未完成。OT/R SOB 主体等价不能外推 TOB、原生编号或演出效果；其他版本保留独立证据要求。

文件指纹口径：实现收据中的工具 SHA256 指受验候选的提交前字节；本机 core.autocrlf=true，检出可转 CRLF。覆盖清单另存 canonical Git blob SHA256，复核检出时可将文本 CRLF 标准化为 LF 后比较；原作二进制/脚本源哈希仍取原始字节，不作行尾转换。
