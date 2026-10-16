# SDK接口说明

新增 7 模块：PE 指令元数据（64 位 capstone 已验，映射由 caller 负责）；snapshot bounds、u32snapshot、u32diff（caller 提供合法 snapshot，单次 read）；rawGetFocus、SetFocus、GetForegroundWindow。

两个 selftest：verify_lucifen_guest_snapshot.py、verify_lucifen_guest_diff.py，实际 import 32/64 位均通过。focus 属 OS 验证，由 root 独立 recipe 执行，不含于上述 selftest；窗口 focus 与 foreground 须区分，有写 global 状态的 OS 病例串行。

既有 GetCurrentThread、SetThreadPriority 复用。
