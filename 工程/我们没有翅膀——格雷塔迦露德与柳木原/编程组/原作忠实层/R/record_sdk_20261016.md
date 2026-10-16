# R记录SDK与实时参数（2026-10-16）

本批交付 26 个生产模块：13 个 metadata-input SDK（覆盖内存、顺序绑定、VM 参数、记录），8 个严格结构解析及 livePrefix/Gate，5 个实时参数。另有 4 个 Python reference。fixtures 仅用于验证，不是游戏产品。

严格结构诊断与 live 执行两种用途分开。只有旧 eager 测试会把解析 metadata 交给旧 runner；原 live 接受分支跳过 length、仅读 count，拒绝分支读 length、不读 count；opcode0 反转条件。先写 flags，再读取 payload，inlineOR2 在读 len 前，后续 item 从实际内存重读。

双架构结果：每架构 3794 records × 6 states × 冷暖 = 22764 pairs / 45528 records，792374 ordered writes 一致；strict 30 结构 / 22 精确拒绝与 24 records；gate 3；live 11 小样 91 scoped 事件，宽、值、顺序、cursor、64 source final 及 16 params final bytes 一致。原 whole-image 证明与 target 有序事件/最终观测不能混同，native 只是 fixture。3 类 6 故障被检出，旧 cache2 / pause4 / atomic6 各架构通过。

原码只走 Unicorn，原 PE / scriptOctets 不外发、不入 Git；本批核验 16 个 source manifest/native resultSHA 和对应 SDK 源码，不宣称 8LPK 等全量重查。

部署：`工程/我们没有翅膀——格雷塔迦露德与柳木原/编程组/原作忠实层/R`。证据：编程组/演出链路/R_TJS记录SDK与实时参数读写证据_20261016。summary 名：full-target-matrix-summary-20261016.json。root recipe 归档 recipes 目录；原大 case 输入仍临时本地，需要这些输入才能重放全矩阵。

本批不改游戏 startup/成品；VM17/47、live 表达式、银行增长、ctx434 发布、129 dispatch、正文画音、全路线/四版 100% 待验；OTV 非 Lucifen。新增 guards 另见最终 root-review.json，不预报新 guard 通过。