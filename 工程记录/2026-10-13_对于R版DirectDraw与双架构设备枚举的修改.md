# 2026-10-13 对于R版DirectDraw与双架构设备枚举的修改

- Issue：ISSUE-20261011-02 ｜ 模式：工程 ｜ 分支：issue/ISSUE-20261011-02-original-fidelity → main
- 参与代理：root（分析/规划/研究/派发/验证/阶段批次复核/Git与行政）；editor-easy（DeepSeek high，独立API桥接，原始Win32/COM类型、布局与最小双架构修订、文档）｜ research/editor-hard/reviewer保持暂停。

## 任务目的

沿原版 R WinMain 图形初始化推进，验证真实 DirectDraw/Direct3D 接口与宿主位宽差异，为后续窗口、绘图表面与演出链路提供证据；四版本100%全路线/状态/画音还原仍是完整长程目标，本阶段不宣称达成。

## 改动清单

- 编程组/工具：新增9份精确editor-easy原始绑定/布局，HostMemory与HostCritical按5处精确literalpatch支持32/64位；没有代写原作引擎或TJS演出实现。
- 编程组/演出链路/R_DirectDraw与双架构设备枚举证据_20261013：技术README由editor提供并精确修订；root原码验证配方、真实API/COM/能力数据/停止点与清理证据、来源与批次覆盖清单。
- 两份作品skill追加同一editor技术增量；Galgame.md仅更新既有R与自建作品两行状态/记录，不新增游戏行；长程目标仅追加阶段检查点。
- 官方32位便携Python3.13.12与Unicorn2.1.4仅落工具，下载与运行时出处/哈希纳入证据；二进制不入Git。Python EXE及DLL签名Valid/PSF，Unicorn wheel与官方PyPI SHA256一致。
- 新用户日文DVD全部34文件与既有备份相同。用户允许外部目录例外未使用，无外部写入、无新增大体积游戏副本。

## 验证方式与结果

- root分别以工具/python-3.13.12-embed-win32/python.exe -X utf8 -B和系统python -X utf8 -B运行阶段verify-host32-WinMain.txt/verify-host64-WinMain.txt的工作区配方：两次退出0，显式检查原生配置10写2关、原DLL attach及15导出、Shell回调、mutex/drive/RECT、确定停止点与真实资源清理。
- 原GetDriveTypeA E:\=3；原OpenMutex缺失后CreateMutex初始拥有成功；另一个真实既有mutex受控分支Open成功并到FindWindowA，未完成整条多开退出路径。原800x600客户区与当前宿主外框[-10,-33,810,610]不作为原作OS/DPI/像素证明。
- 原LoadLibraryA返回点4AB8F3请求ddraw.dll；只主机系统DLL可OS装载。原GetProcAddress实际取得DirectDrawCreateEx/DirectDrawEnumerateExA。主机完整引用与guest32令牌分离。
- 宿主64两次原回调4ABB30真CoCreate/Initialize成功；真实QI IDirect3D7为E_NOINTERFACE(-2147467262)，原Release两次0、原FreeLibrary返回点4AB971成功，随后捕获第三C++图形初始化异常。未恢复此第三异常；之前两次配置缺失异常已恢复。
- 相同主机32位CoCreate与DirectDrawCreateEx独立夹具QI IDirect3D7均成功；32位虚拟System32路径对应真实SysWOW64 DLL的SHA256由64位进程读取交叉验证，不能因名称相同混淆两个系统库。
- 主32原回调真CoCreate/Initialize/QI全部HR0，GetCaps slot11返回点4ABD30真返回0；两份380字节DDCAPS实际宿主输出逐字节复制回原guest缓冲，各有独立guard及输入/输出SHA256。
- 最终严格停在IDirect3D7 slot3 EnumDevices：原返回点4ABD75，原callback4ABE50、上下文为原设备分配。未知ABI未调用；为结束主机夹具枚举返回受控中止0，但原回调未返回、原HRESULT未注入，所以不计为原版枚举成功。COM真实fixture Release1→0、系统模块真实FreeLibrary；原窗口仍0。
- 两架构实际HeapAlloc17字节零初始化/读写/释放，GlobalAlloc17字节往返，临界区24/40字节Enter两次/Leave两次/Delete均通过；动态STARTUPINFOA 68/104布局在原音频DLL CRT attach中通过，不等于原作OS进程CRT启动。
- root-source-integrity：1 EXE、8 LPK、3原DLL、2参考DLL、446 SCRIPT、418 IR源与压缩哈希及111字节USER.CFG全部未变。
- 全部命令、字节证据和有限阶段断言见阶段JSON及验证配方；完整原码仍仅由Unicorn执行，没有原作EXE/DLL的OS启动。

## 风险、警示与未完成项

- 起初把原IID f5049e77误称GammaControl，经微软SDK纠正为IDirect3D7，错误候选未使用。root旧formatter计数后验失效；Win32早期12/13配方proxy全局名冲突导致回调TypeError，尽管进程退出0仍拒收为工程证据；最终配方显式拒绝意外回调错误。
- API长度截断候选全部丢弃；一次DSML伪工具文本未执行；后续离线小模块交付成功。未外发原作剧本、游戏本体、素材、凭据或环境/命令行内容。原型本身不提供OS sandbox或路径/地址自动验证。
- 宿主64失败不代表游戏不能运行；当前宿主32成功不代表原版Windows/硬件/DPI/日文ACP下画面一致。GUI窗口、协作层级、绘图表面、演出素材VM、实音频解码/PCM/时序及四版本忠实剧本与全路线帧对照仍未完成。
- 串行原作回调只在没有活动外层emu_start时执行；guest函数/缓冲地址不注册OS。当前仅支持实测原型，不以空成功越过未知接口。
- 回滚以本issue前基线d5d80653/main ff18e067为依据，在新issue上Git revert本批提交；原始备份与历史成果未更改，不删除历史工程记录。工具为可复用便携依赖，不属于原作本体。

## 审查结论

root在本大型阶段集中覆盖全部helper、两份skill、阶段证据/配方/README、索引/长程检查点与本记录。批次结论及LF哈希以同批root-batch-review.json为准；通过后只在issue提交并合并main，合并后返回issue。实际提交/合并标识由本记录所在Git历史确定。此为有限接口阶段通过，不是四版100%还原或原作完整启动通过。
