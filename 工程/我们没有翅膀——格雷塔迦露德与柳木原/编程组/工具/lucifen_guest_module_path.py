# -*- coding: utf-8 -*-
"""Lucifen 来宾 PE 装载器元数据辅助模块（只读、纯函数、无副作用）。

本模块实现一个**限定范围的 OS loader 元数据模拟**：对已经由来宾侧
实际映射到内存的 PE 映像，生成其"注册文件名 / 路径"的字节序列，
对应 Windows ``GetModuleFileNameA`` 的**成功分支**语义。

严格边界（务必阅读）
--------------------
* 这**不是**真实 Windows API，也不模拟 PEB / LDR / CNG 等任何
  宿主数据结构；它只是"给定已验证参数 → 返回确定字节"的纯函数。
* 本模块**不**调用宿主 ``GetModuleFileNameA(NULL)``，也不会拿宿主
  进程（例如 python.exe）的映像路径来冒充来宾 PE 身份。
* 本模块**不**证明任何形式的"全 OS 启动成功"；来宾 PE 是否真实、
  是否已映射，由调用方（root / 平台层）负责保证。
* 本模块**无**文件 IO、进程 / 线程操作、加载 / 执行、网络、Git
  行为；不做任何截断，不设置也不读取 LastError。

调用约定
--------
调用方（root 平台层）须已持有：
1. **已实际映射**的来宾 PE 基址 ``base``（非零 uint32）；
2. 与该映像身份对应的**真实只读源文件路径** ``path``；
3. 目标缓冲区的**字节容量** ``capacity``。

调用方取得返回值后，自行检测目标缓冲范围并完成复制；本模块不接触
任何指针或可变缓冲区。

限制
----
仅实现"完整路径 + NUL 能完整放入 ``capacity``"的成功分支。
若放不下（含 ``capacity == 0``），本模块**拒绝**继续并抛出
``NotImplementedError``，绝不捏造截断结果或 LastError 值。
"""

from __future__ import annotations

__all__ = ["registered_module_filename_a"]


_UINT32_MAX = 0xFFFF_FFFF


def _require_uint32(value, name):
    """校验并返回一个非 bool 的 uint32 整数。

    ``bool`` 是 ``int`` 的子类，但在这里必须被拒绝，避免 True/False
    被当成 1/0 混入 loader 元数据语义。
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "{0} 必须是非 bool 的 uint32 整数，实际类型 {1}".format(
                name, type(value).__name__
            )
        )
    if not (0 <= value <= _UINT32_MAX):
        raise ValueError(
            "{0} 超出 uint32 范围 [0, {1}]：{2!r}".format(name, _UINT32_MAX, value)
        )
    return value


def registered_module_filename_a(module, base, path, capacity):
    """模拟 ``GetModuleFileNameA`` 的**成功分支**。

    返回 ``(length, data)``，其中 ``data`` 是以 NUL 结尾的完整路径
    字节串，``length`` 为不含结尾 NUL 的路径长度（与 Windows A 版
    返回值语义一致）。

    参数
    ----
    module : int
        HMODULE 句柄值。须为 uint32，且**仅允许** ``0``（NULL，表示
        "当前来宾 PE 模块"这一注册语义）或与 ``base`` 严格相等。
        其他任何非零值在不查询宿主模块表的前提下无法解析，直接拒绝。
    base : int
        已经实际映射的来宾 PE 基址，须为非零 uint32。
    path : bytes
        与该映像身份对应的真实只读源文件路径。须为非空 ``bytes``，
        且内部不含 NUL 字节（NUL 会破坏 C 字符串边界）。
    capacity : int
        目标缓冲区字节容量（uint32）。须能容纳 ``len(path) + 1`` 字节。

    返回
    ----
    (length, data) : (int, bytes)
        ``length == len(path)``；``data == path + b"\\x00"``。

    异常
    ----
    TypeError
        参数类型不合法（bool、非 int、非 bytes 等）。
    ValueError
        取值不合法：超出 uint32、``base`` 为零、``module`` 既非 0 也
        不等于 ``base``、``path`` 为空、``path`` 含 NUL。
    NotImplementedError
        完整路径 + NUL 无法放入 ``capacity``（含 ``capacity == 0``）。
        本模块不实现截断分支，也不返回或写入任何 LastError。
    """
    module = _require_uint32(module, "module")
    base = _require_uint32(base, "base")
    capacity = _require_uint32(capacity, "capacity")

    if base == 0:
        raise ValueError("base 必须是已实际映射的来宾 PE 基址，不能为 0")

    if module != 0 and module != base:
        raise ValueError(
            "module 仅允许 0（NULL 注册语义）或等于 base；"
            "module={0!r}, base={1!r}".format(module, base)
        )

    if not isinstance(path, bytes):
        raise TypeError(
            "path 必须是 bytes，实际类型 {0}".format(type(path).__name__)
        )

    if len(path) == 0:
        raise ValueError("path 必须是非空 bytes")

    if b"\x00" in path:
        raise ValueError("path 不得包含 NUL 字节")

    required = len(path) + 1  # 完整路径 + 结尾 NUL
    if capacity < required:
        raise NotImplementedError(
            "仅实现完整路径 + NUL 能放入 capacity 的成功分支："
            "需要 {0} 字节（path={1} + NUL），capacity={2}；"
            "本模块不捏造截断结果或 LastError。".format(
                required, len(path), capacity
            )
        )

    return len(path), path + b"\x00"