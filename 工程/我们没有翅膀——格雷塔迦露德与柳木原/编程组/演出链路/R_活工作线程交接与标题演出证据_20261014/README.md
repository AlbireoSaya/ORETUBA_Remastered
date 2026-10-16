# R_活工作线程交接与标题演出证据_20261014

## 用途
限定为实际原始工作线程与父级交接、部分标题演出验证的证据记录，不覆盖完整保真度。

## 工作线程 SDK
- lucifen_host_worker_park.py
- lucifen_host_worker_step_state.py
- lucifen_host_worker_step_gate.py

## 区域校验 SDK
- lucifen_verify_rect_union.py
- lucifen_verify_span_input.py
- lucifen_verify_bgrx_spans.py

## 合成自检
- verify_lucifen_rects.py
- verify_lucifen_span_compare.py

## 边界
root 阶段审计，非保真度完成；文件名均取自实际工区，无猜测。

## 阶段证据
- 137：实际 worker 259，five HFONT 60 有效，same OS-TID context+FS0。
- 138：11 blits，33 samples 通过。
- 139：partial Rmenu/full 792977 差异。
- 140：338 blits，131 通过，207 NULLREGION 失败；六次 full captures 失败；source 57 strips RECT(0,90,800,540)，captures1/2 same，ONE run 360000 pixels zero。
- 143：four 4 handoffs same TID28476，original worker 4x8M；true zero-param registered messages 0xC125、0xC220，original WNDPROC 49F860，result0。
- canonical143 的450次：postblits all clip2/sample pass，但 full 370057 差异。
- 新 text proxies 未调用，无 text proof。Actual32/64、synthetic32 generation 已验证，含 owner/stale/wrongworker guards。

## 复现
Recipe TXT canonical 136..144；依赖 previous R_线程启动握手与消息接续证据_20261014、编程组/工具、local ignored source/cache；工具 Python32/Unicorn。144 pending。

## 限制
不声称 full scheduler/loader/TEB/Exit/TJS/audio/routes/fidelity。

# 2026-10-14阶段终点（更正前述待办）

144实际6handoff（非计划16）；337postblit全clip2/samples过，full369555差异。parent adapter断言非源码故障。145诊断：实际WM_NCHITTEST 0x84打包屏幕XY被误拒。146验证原WNDPROC 49F860加实际DefWindowProc对0x84返回HTCLIENT1同窗口；2handoff 113postblit全过，full369369差异。下一边界为系统实际发送的WM_SETCURSOR 0x20，wParam自有HWND需host→guest映射，不支持则保守停止；无源码文本API调用。进程exit0、worker errors[]、fixture cleanup true，非完整游戏成功。源完整性核对1EXE 8LPK 3DLL 2refs 446scripts 418IR 111byte USERCFG未变。四版本目标活跃全100%未完成。不虚构额外证据。
