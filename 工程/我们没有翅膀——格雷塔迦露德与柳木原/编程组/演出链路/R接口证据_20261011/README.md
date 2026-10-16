# R 原生接口与 SOB VM 证据（2026-10-11）

ISSUE-20261011-02 的 L2 检查点。root 研究、核验与批次审查；editor-easy / DeepSeek V4.1 Flash high 实施候选。这里只存来源哈希、地址、索引、偏移和有限客体观察，不含原剧本、EXE 字节、素材或凭据。

## 结论与限度

- R EXE SHA256：`b26795b15a5b8a1f58102d30dcd60ae2b04cd19a6a936cd7024f55993a8ebf33`；OT：`b269980423e9c85281046e358804b0d66d86001084bae23f5ac75b30ae9d8a4b`。原版与补丁分开识别。
- SOB VM 主体 1,284 字节仅分派表 disp32 不同，47 入口相对位置一致。只允许复用该 SOB 指令结构，R 原生函数、TOB、资源与演出仍须独立恢复。
- R 子构造器先注册 3 项、父注册段 806 项：809 静态槽、803 独立地址，重复地址保留。父注册段完整反汇编，无分支/其他调用。maps[1] 装载时用索引读取 manager+0x38 向量并覆写缓冲。未观测原进程注册向量。
- 22 R SOB 容器：49,974 指令、144,950 代码字、2,273 原生调用；SOB1 声明另计。引用使用 240 索引、范围 0..799，全部位于代码区。非法索引和地址负控被拒绝。
- 全部 2,273 参数字初值零，各有一处 op40 写入 SP 快照。原始零是占位，必须保留可变字码；静态配对不证明 CFG 可达、实参数或效果。一处空跳表项继续保留未决。
- OT/R 各三项合成字码微用例共六项：原机器码执行 SP 减偏移写后续操作数、PUSH、空跳表读异常。R 原生槽号 2 的一个微用例另观察到实参为栈快照、返回 0、全局状态置 3；不能据此命名为“脚本返回”。
- 无限 JMP 用例以次数上限停止：error 为空、returned=false。CPU 停止不等于 VM 返回。客体内没有 WinAPI stub、没有宿主原游戏进程；以上不是完整 47 指令覆盖、原剧情或画音重放。

## 依赖与来源

容器统计及链接临时探针仍依赖当前树未入库 B0 `编程组/原作语义/source_ir.py` 和本 issue 临时探针。本批不并入 B0，这部分不宣称 fresh-clone 独立复验。原语料为 `工程/我们没有翅膀R/语料/R版SCRIPT/`；与安装介质 SCRIPT.LPK 的 446/446 明文哈希对账已在前一阶段保存。

新工具不依赖 B0：`编程组/工具/lucifen_registration_candidates.py` 复用已入库 PE 读取器及 Capstone，输出局部签名候选，不自动确定注册顺序；`lucifen_vm_micro.py` 提供 `map_pe(pe)`、`execute_vm(uc,entry,fetch,words)`，只在 Unicorn 客体执行调用者指定的 PE32 i386 入口。

Unicorn 2.1.4 便携库位于 `工具/unicorn-2.1.4-py314/`，wheel 位于 `工具/`，不入 Git。wheel SHA256 为 `d7107500c64ce5c168fbff6bef9485b5db1350050036f4cea568650cf8bdbdf5`；安装的 36 个包内文件与 wheel 逐字节相等。本机 Python 3.14.7 库加载通过；Win7/Win10 未验证。来源：[PyPI](https://pypi.org/project/unicorn/2.1.4/)、[官方教程](https://www.unicorn-engine.org/docs/tutorial.html)。新 clone 不自动下载依赖。

`交付来源.json` 记录候选、组装、失败回合与哈希。DSML 文字请求未执行；无完整代码的回合不算交付。未成功交付持久回归测试文件，下面是 root 独立复验命令与回执，不是假报模型已执行测试。

## 复验命令

从工作区根目录运行注册探针：

```powershell
python -X utf8 -B '工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/工具/lucifen_registration_candidates.py' '备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE'
```

复验六项结果（需要原 EXE 与上述便携依赖，不需要 B0）：

```powershell
@'
from pathlib import Path
import sys,json,hashlib
root=Path.cwd()
g=root/'工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组'
sys.path[:0]=[str(root/'工具/unicorn-2.1.4-py314'),str(g/'逆向引擎'),str(g/'工具')]
from pe_min import PE
from lucifen_vm_micro import map_pe,execute_vm
p=json.loads((g/'演出链路/R接口证据_20261011/OT_R_VM微仿真.json').read_text(encoding='utf-8'))
paths={'R':root/'备份/我们没有翅膀R-安装介质/SET_UP/ORETUBAR.EXE','OT':Path(r'D:\Gal\[Navel]我们没有翅膀\ORE_TUBA.EXE')}
for row in p['rows']:
    pe=PE(paths[row['version']])
    assert hashlib.sha256(pe.data).hexdigest()==row['exe_sha256']
    assert execute_vm(map_pe(pe),row['entry'],row['fetch'],row['fixture'])==row['result']
print('6/6 original CPU microcases reproduced')
'@ | python -X utf8 -B -
```

四版本忠实剧本、完整原生/TOB 语义、原画音和全部路线仍未完成；目标保持 active。
