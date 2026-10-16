"""x86 受控 guest CPU 复位桩：FNINIT; RET。

本模块仅提供一个不可执行的字节序列构造器，用于在受控 guest CPU 语境下
表示 x86 指令 `FNINIT` 紧接 `RET` 的机器码编码：

    0xDB 0xE3    FNINIT   ; 初始化 x87 FPU：控制字复位为 0x037F，状态字清零
    0xC3         RET      ; 近返回

用途：把 guest 的 x87 控制字连同状态字等 x87 环境一并重置回硬件默认值
0x037F。随后由 root 在 guest 内执行实际原程序 CRT 的精度设置函数，以验证
控制字由原CRT精度函数设置；本guest实测为0x023F（PC=10，53位双精度）。这仅验证精度设置子路径，非完整CRT初始化。

边界声明：
- 不涉及任何 Windows API（不调用 kernel32/ntdll 等）。
- 不启动整机 OS、不启动 CRT、不加载任何镜像。
- 不声称原作已经执行过本 stub；本 stub 只是字节编码，是否投放由 root 决定。
- 本模块无 I/O、无副作用、无外部依赖，不读取任何外来二进制。
- 本文件不执行任何 CPU 指令，仅返回编码字节。
"""


def guest_x87_reset_stub() -> bytes:
    """返回 `FNINIT; RET` 的 x86 机器码字节串。

    Returns:
        bytes: ``b"\\xdb\\xe3\\xc3"``，即 x86 ``FNINIT``（0xDB 0xE3）
        后接 ``RET``（0xC3）。

    说明:
        - 该序列用于受控 guest CPU 的 x87 复位，使控制字回到 0x037F。
        - 调用方（root）随后需自行执行原程序 CRT 的精度设置函数，
          验证PC=10及异常掩码；本guest精度设置实测为0x023F。
        - 本函数不做任何执行、注入或 I/O；重复调用始终返回相同常量。
    """
    return bytes((0xDB, 0xE3, 0xC3))