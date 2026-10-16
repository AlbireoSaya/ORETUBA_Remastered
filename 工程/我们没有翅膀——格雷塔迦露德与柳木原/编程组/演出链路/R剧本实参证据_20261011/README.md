# 剧本实参还原：source writer-to-native 片段知识稿

## 来源范围（source scope）

本稿只覆盖 31 条 original source writer-to-native 片段，分布在 8 个 SOB 模块，每条仅受控 2 个 variable/stack/module 状态。合计 62 个 case：候选 429 占 44、238 占 6、239 占 12。31 条引用由 9 条构造引用与 22 条合成引用组成，二者相加即 31。前述62例仅到native入口，未执行native函数体；另18例连续执行native wrapper与factory前段，停在allocator入口而未执行分配器，二者不可混同——18例并非「同样入口实参样本」，其已执行的工厂原码不得抹去。整批均未验证完整模块CFG、真实全局/场景、完整native生命周期或100%还原。证据为「R 剧本实参证据_20261011」，工具为 lucifen_native_frame_probe.py 与既有 lucifen_cdecl_observer.py。op5 初始参数看似 word0，但经 op40 运行期改写为 VM_SP，故非恒定 NULL；可变 code 必须保留。

## 参数实测

模式分布共 5 组，计数 7、9、9、3、3，合 31。original CPU 片段动态事实有三条：op40 把 opcode5 参数字 word 由 0 改为当前 VM_SP，op8 按源序 push；native 帧指针等于 prepush SP，SP 增加 argc*4；进入 native 时 ctxPC 已是 call+12。它们是实测动态结果，不是静态推断。

静态 literal 来自构造引用：238 在 config1.sob 偏移 10572、config2.sob 偏移 10232、saveload.sob 偏移 19320，字面为 800/600/32/2；239 在 config1.sob 偏移 11052 与 31976、config2.sob 偏移 10712 与 28580、saveload.sob 偏移 19492，字面为 800/600/32/0；gameinit.sob 偏移 2160，字面为 800/600/32/1。构造帧共 3 类，与上述 literal 对应。

## 独立对照

editor 侧实现独立 shadow helper，实际对照由 root 实跑完成，editor 未自行运行该对照。覆盖 ops 5/8/13/31/32/35/40。frame、VM_SP、call location、handler、step count、整源模块字节与受控栈跨度均与 original CPU 相等；不支持项、预算与错误原样保留。helper 分组为 12。

渲染侧候选 429 的 5 个 word 为 object/bitmap/mode/id/truth，属受控数据传播，只能说明受控输入可传递，不可据此推断真实对象指针或运行状态；受支持操作包括 address literal 与 dereference 的区分，以及 stack-relative 输入；wholeDWORDtruth 与 low8 mode 分属不同判断。controlled 429 各数值仅代表受控 case，勿视为原剧情参数常量。

## 依赖与未知

首次静态定位虽借用 B0，但 31 个固定 metadata 已与原 SOB 的 opcode/operands/offset/relocation 独立对账；正式回放使用随附 metadata 与 mature loader，不导入 B0。并非完整 B0 审查，也非全量独立 decoder，结论仍有边界。native 映射依据 809 条静态构造候选向量，真实运行时向量尚未观测。受控 2 状态不能外推为真实场景行为。

## 下一步

恢复原始 allocator 与 objects，补齐 actual caller 可达性与状态；再产出保真目标脚本，保留 source/raw/source-offset/unresolved 元数据；随后做 TJS 集成、真实帧与音频，覆盖全部四个版本。

## 原VM到工厂分配入口的连续证据

9构造源片段×2状态共18；原VM→原238/239→原factory前段连停原operator new 50577F；out原caller参数槽先清0，0xD8分配请求，未执行allocator；guest FS:[0]零页预映射为受控SEH存储，非真实Windows环境；起初未映射零页的真unmapped read停4BA6A7，不填fake返回，补客体区域后通过。
