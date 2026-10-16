# 对于R版音频DLL装载与WinMain预初始化的修改

- 日期：2026-10-12
- issue：ISSUE-20261011-02；分支：issue/ISSUE-20261011-02-original-fidelity
- 参与代理：root（分析、派单、验证、批次复核、Git及行政）；editor-easy（DeepSeek-v4.1-flash/high，独立API桥接，实施7个自建辅助模块与两作品知识追加片段）。research/editor-hard/reviewer未调用。

## 任务目的

继续四版本原作忠实演出长程目标；本次有限验收为原wuvorbis DLL实际CRT初始化、WinMain实际接口解析与初始化资源读取，并准确记录下一系统边界。全部路线、分支、状态、图像和音频100%以及忠实目标剧本仍未完成。

## 改动清单

- 编程组/工具新增7个editor候选：PE原始节映射、CRT叶API/编码/ANSI大小写/文件枚举/SetHandleCount类型绑定、单线程guest异常过滤器状态；root仅应用精确候选并执行验证命令，不改写其工程实现。
- 编程组/演出链路/R_原版音频DLL装载与WinMain预初始化证据_20261012：原版DLL清单、实际DLL API与WinMain证据、原初始化资源逐源比较、归零清理、叶API与失败夹具、可重跑验证recipe与root复核覆盖。
- R作品skill与自建作品skill：追加editor交付的本阶段依据与边界。
- Galgame.md两条既有作品行及四版本目标：root行政增量登记，无新重复条目；工程记录随issue提交。

## 验证方式与结果

- 从正式证据中的 verify-WinMain.txt 以 Python -X utf8 -B 执行；使用正式工具目录与正式DLL元数据，已独立重跑并核对真实入口/参数、attach/15接口/原export执行/初始化资源与停止现场。
- 原wuvorbis.dll SHA256 302b1eb97ed0f6110904e84c11bf7436e4cdddd414f4d24d105aba687f32b47f，guest基址11000000；原CRT入口11012DED以[base,1,0]实际返回1。独立原DLL CRT产生86块、1TLS、5CS；WinMain原代码请求装载后实际解析15个原export，Query_sizeof_OggVorbis_File原码返回704，wu_DetectCPU与wu_SetCPUType实际执行（默认Unicorn CPU参数31129622，不是原机CPU证明）。
- 原WinMain452CF0在真实40A0A0父构造后执行；SCRIPT.LPK只读打开、原生header/index读取以及磁盘缺失到归档回退均实际发生。ll_app.sys 25字节、ll_app.inf 101字节与446份既有只读源中的对应文件逐字节相同；原内容未写入本批证据或发送提供者。
- 停止点为SHGetSpecialFolderPathA导入，原调用返回地址VA47E3A4，CSIDL26、fCreate1、HWND0。实际host API未调用，未在AppData创建目录。
- 8项有意义的叶/失败夹具通过：真实Uc原始映射与零BSS、映射交叠原数据保留、写失败回滚、guest过滤器交换及6个拒绝输入不变、CP936/UTF16往返、带DBCS的ANSI大小写与指针宽度、系统HMODULE/proc完整64位、真实文件枚举EOF/关闭/缺目录及缓冲区守卫。
- 正式host-fixture-cleanup.json证明所拥有的堆/块、文件、TLS、CS、事件与COM归零；原WinMain/DLL shutdown未执行，清理是明确的验证夹具清理，借用的标准句柄不关闭。
- verify-source-integrity.txt重验1原EXE、8LPK、3原DLL、2参考DLL、446源脚本、418无损IR及对应源哈希不变。规范读取沿用同一长任务未变更的哈希缓存，AGENTS main与工作区无差异。

## 风险、警示与未完成项

- 原EXE/DLL只在Unicorn受控x86中执行，未由OS装载/执行。真实Windows叶API使用宿主CPython版本/ACP936/宿主进程元数据；命令行与环境内容仅进入guest内存，不落日志或外传。模块路径使用只读备份的注册元数据；宿主64位STARTUPINFO字段显式转换为guest32，保留受控输入边界。
- guest异常过滤器初始0属于单线程受控状态，不是OS过滤器；不将guest地址注册到宿主。PE映射辅助函数只接受调用方预验证的PE32首选基址布局，不执行导入/重定位/入口，不是OS加载器或系统sandbox。
- 原DLL40export与成熟krkrz/wuvorbis的39接口仅可作ABI参考，额外GetOptionDesc；PCM、seek/循环/回调、完整CPU/OS初始化与原DLL卸载尚未证。DS_SPRITE/DS_MOVIE共享首选基址60000000，未来需正确重定位。
- 桥接3次输出预算耗尽未交付；一次原生editor-easy试调用被平台400拒绝（ChatGPT账户不支持该模型），无产物，继续独立API。mapdoc04候选错误移除了位取反，root AST复核拒绝，未进入工程；原有效map-compact03保留。guestfilter01的“原子”表述拒绝，采用明确单线程的guestfilter02。未调用其他暂停角色。
- 下一有限路径：只读查询保存路径/工作区内guest存储映射 → 原WinMain窗口与后续资源/DLL初始化 → 接续SOB演出和画音消费者 → 忠实TJS与四版本全部路线/状态/帧/音频对照。当前HWND0，不以接口覆盖当还原率；完整goal保持active。
- 回滚：撤销本批issue提交及合并所带范围；历史工程记录/原备份/既有无损IR保留只读，不覆盖、不删除，不在main直接修改。

## 审查结论

root按本有限重大阶段集中复核全部7辅助模块、实际取证和重跑命令、两作品知识增量、目标、索引与记录；覆盖清单及LF摘要见同批root-batch-review.json。有限检查点通过，四版本整体目标未完成。本记录与索引在issue分支预先准备，提交前显式确认issue分支，审查通过后合并main并返回issue；具体提交由Git历史记录，合并后不补写本记录。

