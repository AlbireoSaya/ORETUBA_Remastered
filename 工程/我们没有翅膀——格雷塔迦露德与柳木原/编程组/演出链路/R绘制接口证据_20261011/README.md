# R 绘制接口与像素核阶段证据

ISSUE-20261011-02。Root在主要阶段集中复核；editor-easy交付客体cdecl助手、独立数学参考与技术知识。本阶段没有宿主启动游戏或DLL，没有原画音/完整场景/全剧本验证，也没有TJS生产接入。

## 取得的契约

- 原 tvpgl.dll：SHA256 63e9308c2e89445daa1d427c5b5e1ed1ce863111ca722a5f3b6dd966d065a985，PE32优先基址10000000。静态GetLibrary(10001C10)请求940字节并安装field0虚表后调用cdecl初始化10001000(object,CPUsettings)。实际执行的是完整初始化函数，受控预分配客体、非NULL全零0x98设置与FS:[0]映射；未执行malloc工厂、DllMain、系统加载、异常派发和真实启动。
- 235字段中field+4为数据指针1004D1F0，field+8..3A8为233个函数指针；绘制指针存在实例字段中。field0的虚表含析构入口，不能将这张函数表误记成233个虚方法。
- 原EXE4A0D91..4A1ABE复制发布234字段，逐值对照全通过。设置档10个单byte和全开共11组已执行原初始化；8F档改128字段，全开改130字段。真实游戏CPU/配置选择尚未观测。

## 文件与作用边界

| 文件 | 证据范围 |
| --- | --- |
| tvpgl-init-scalar.json | 完整初始化函数返回与235字段，受控设置；不含工厂分配/宿主加载 |
| tvpgl-engine-publication.json | 原EXE发布234字段和全局槽映射 |
| tvpgl-settings-dispatch.json | 11受控设置档与差异函数入口，不是实机CPU选择 |
| tvpgl-pixel-kernel-crosscheck.json | 标量普通/HDA各14缓冲及9填充长度 |
| tvpgl-HDA-selected-crosscheck.json | 标量/8F/全开三个HDA入口42缓冲209841像素字 |
| tvpgl-pair-context-crosscheck.json | 两优化普通入口、两目的对齐、56缓冲279788像素字 |
| tvpgl-final-tools-crosscheck.json | 最终入库助手与参考重跑上述56缓冲通过 |
| 批次像素覆盖统计.json | 去重6入口112缓冲559576像素字；含负/零长度的保全检查，不是所有配色的穷尽证明 |
| tvpgl-selected-kernel-counterexamples.json | 标量与优化入口RGBA不统一的原码反例 |
| tvpgl-selected-reference-counterexample.json | 通用单像素opaque-copy假说在长度257第171像素被否决，未采用该候选作为buffer参考 |
| tvpgl-pair-alignment-witness.json | 相同源像素随长度/对齐改变的6原码见证，cdecl和参考的有效负控 |
| tvpgl-engine-call-sites.json | 原引擎66潜在间接call、21字段；线性反汇编静态候选，非完整可达/执行覆盖 |
| upstream-source-receipt.json | 成熟上游来源、固定commit、下载哈希和LICENSE，未据此宣称相同二进制 |
| 交付来源.json / 原码复核命令.md / 批次审查覆盖清单.json | 角色、候选、失败收据、root复核命令及覆盖指纹 |

## 必须保留的像素差异

标量普通核1000F4E0只输出RGB，按d+floor((s-d)*a/256)，alpha输出0。三个HDA入口保留目的alpha，RGB同式。两个优化普通核1003BAE0/1003C260的单像素或尾像素遇alpha255全复制；成对循环仅当两source alpha都255时全复制，否则两像素四通道都按/256差值插值。n>4时目的地址低位4先处理一个单像素，再按i<n-4处理成对块，最后走尾部。

原码见证：首source FFFFFFFF，单像素结果FFFFFFFF；长度5、目的8对齐、第二source80FFFFFF时首结果FEFEFEFE；相同长度、目的低位4时首结果FFFFFFFF。因此入口、扫描线长度、对齐和邻接alpha都属于还原依据。单一逐像素公式无法覆盖这些路径，不能用更方便的标准混合替换。

## 复验环境与成熟资源

像素对照仅覆盖有效、非重叠的映射输入/目的缓冲；重叠指针行为未验证。

Windows/Python3.14.7，工作区工具/unicorn-2.1.4-py314，x86-32 guest。两个新工具位于编程组/工具/lucifen_cdecl_probe.py、lucifen_pixel_reference.py；args使用可重复遍历的参数序列，调用者提供映射内存，助手校验真实cdecl返回和ESP。不是OS sandbox。原码复核命令仍需本机只读原本/便携依赖和忽略区候选，未宣称新clone无需原本即可执行。数学函数只为验证/移植依据，尚未绑定TJS生产特效。

成熟参考来自 https://github.com/krkrz/krkrz/tree/fd5c4baa6a2ef5978db1bd043634351f48667daf/visual 。tvpgl.h/c与LICENSE在工作区工具/tvpgl-reference-fd5c4baa6a2e/，来源和各文件哈希见收据。相关签名是线索，原二进制接口/实现版本需独立验证；未将下载源码整体并入生产工程，也未外发提供者。

下一阶段需补原表面对象ABI、真实启动设置、图层/剧情实际调用链；233指针地址已取得不等于233个函数行为已懂，亦不等于OT/OTA/OTV/R全部忠实剧本与画音对照完成。
