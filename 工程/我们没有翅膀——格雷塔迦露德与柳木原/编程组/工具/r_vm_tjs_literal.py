"""TJS2 验证数据字面量序列化。

纯函数、无 IO：仅把 Python 值转成 TJS2 验证数据字面量文本，不执行脚本、不读取游戏数据。
支持：void / bool / Integer64(int) / string / array / dictionary(%[...=>...])。
字符串按 UTF-16LE 单元输出：仅可打印 ASCII 直出，其余一律 \\xHHHH（大写四位 hex），
不使用 JSON 的 \\uXXXX 转义（TJS2 官方 tjsLex.cpp 只认 \\x，不认 \\u）。

约束：
- TJS 字符串字面量不能表示 NUL（U+0000）；字符串值或字典键含 NUL 时拒绝。
- int 按 TJS2 Integer64 处理，仅允许 signed 64 位区间 [-2**63, 2**63-1]。
"""

__all__ = ["tjs_literal"]

_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1


def _quote(value):
    if chr(0) in value:
        raise ValueError("NUL cannot be represented in TJS string literal")
    raw = value.encode("utf-16-le", "surrogatepass")
    parts = ['"']
    for index in range(0, len(raw), 2):
        unit = raw[index] | (raw[index + 1] << 8)
        if unit == 0x22:
            parts.append('\\"')
        elif unit == 0x5C:
            parts.append("\\\\")
        elif 0x20 <= unit <= 0x7E:
            parts.append(chr(unit))
        else:
            parts.append("\\x%04X" % unit)
    parts.append('"')
    return "".join(parts)


def tjs_literal(value):
    if value is None:
        return "void"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        if value < _INT64_MIN or value > _INT64_MAX:
            raise ValueError("TJS Integer64 out of range")
        return str(value)
    if isinstance(value, str):
        return _quote(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(tjs_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("TJS dict key must be str, got " + type(key).__name__)
            parts.append(_quote(key) + "=>" + tjs_literal(item))
        return "%[" + ",".join(parts) + "]"
    raise ValueError("unsupported type for TJS literal: " + type(value).__name__)