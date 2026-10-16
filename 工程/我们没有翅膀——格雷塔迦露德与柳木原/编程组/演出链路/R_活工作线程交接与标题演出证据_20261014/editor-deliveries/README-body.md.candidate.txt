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