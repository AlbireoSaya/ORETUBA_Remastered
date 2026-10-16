### R 只读宿主前置（线程 PASS，primary 未通过）

- 线程 PASS：C#5/.NET4 x86 fixture，CreateRestrictedToken flags=9（WRITE_RESTRICTED+DISABLE_MAX_PRIVILEGE）+ custom restricting SID + ImpersonateLoggedOnUser。普通token前两类WRITE可以打开(仅权限查询未写)，win.ini普通已拒；受限后三类READ均成功、WRITE均拒error5。
- 正控：仅对已 grant 该 SID 的工作区临时目录 CREATE_NEW 16 字节 canary，原 3 文件 SHA256 不变。
- 负控：无 ACL 目录、已有 canary、工区外输出均失败且不生成/覆盖；SID 以 SecurityIdentifier 授 ACL，icacls 未知 SID 映射失败、未改原 ACL。
- primary 未通过：restricted token + CreateProcessAsUserW 固定自生成 child，无 inherit handles，child 仅 CheckFiles/IsTokenRestricted，未运行原作、未加载原作DLL，fixture源码无GUI/后代创建，系统DLL/OS对话框不是本批证明的零活动。。CREATE_NO_WINDOW 退出 0xC0000142 无 canary；改 DETACHED_PROCESS 后 wait 非 0，清理后子进程消失、无 canary。
- 未记录 DLL 初始化根因和 wait 值，不归咎特定 DLL/权限，不报 primary guard 通过。probe 非 OS sandbox，缺 private desktop/windowstation、default token DACL、job/树清理、原作动态。下一阶段补 startup 与 private 宿主，此前不加载原 DLL/游戏。证据拟放 编程组/演出链路/R只读宿主前置证据_20261011/。

### Lucifen 方法：受限令牌夹具分层验证
1. 分层判定：线程 impersonation PASS 与 primary 进程创建 PASS 分开，不互相推断。
2. 正控最小化：仅对显式 grant 的专用临时目录 CREATE_NEW 16字节全零 canary(不能0字节)，比对前后原文件 SHA256。
3. 负控齐全：无 ACL 目录、已有 canary、工区外输出必须失败且不生成/不覆盖。
4. 证据先行：记录 flags、SID 授予方式、退出码；未记录的根因与 wait 值不猜、不归咎特定 DLL。
5. 结果暂存待主代理应用，不用参考 SDK 猜根因。

补充实测：4 个正式源码 csc x86 全部编译成功；正式目录 RestrictedThreadProbe.exe 启动被拒 AccessDenied，随后文件不存在，正式线程重跑无 PASS、无 canary。旧候选 RestrictedWriteProbe.exe 仍在，其先前线程 PASS 收据有效，但不能套用到失败的正式路径。原因未查明，不据此下结论。

新目录继承的 Deny 仅 DeleteSubdirectoriesAndFiles，并非 Execute；WMI 已登记 360 安全卫士与 Defender，Defender 未找到匹配检测，故不归咎 360、不宣称 AV 误报。未修改或禁用安全产品，未改名重试逃避拦截。下一步需真实 startup 与受控写入环境，Windows 具体验证原作前置仍未满足；源码仅为受控 fixture，非生产还原层。
