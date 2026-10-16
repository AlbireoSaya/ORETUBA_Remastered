import ctypes
from lucifen_host_dib_color_table import RGBQUAD, SetDIBColorTable, GetDIBColorTable

def check_owned_dib_colors(dc):
    GUARD = 32
    DATA = 8
    GUARD_BYTE = b'\xA5'
    input_data = bytes.fromhex('0203040005060700')
    zero_data = b'\x00' * DATA

    input_buf = ctypes.create_string_buffer(GUARD * 2 + DATA)
    ctypes.memset(input_buf, 0xA5, len(input_buf))
    ctypes.memmove(ctypes.byref(input_buf, GUARD), input_data, DATA)

    input_expected = GUARD_BYTE * GUARD + input_data + GUARD_BYTE * GUARD
    assert input_buf.raw == input_expected

    input_ptr = ctypes.cast(ctypes.byref(input_buf, GUARD), ctypes.POINTER(RGBQUAD))
    assert SetDIBColorTable(dc, 3, 2, input_ptr) == 2

    assert input_buf.raw == input_expected

    output_buf = ctypes.create_string_buffer(GUARD * 2 + DATA)
    ctypes.memset(output_buf, 0xA5, len(output_buf))
    ctypes.memset(ctypes.byref(output_buf, GUARD), 0, DATA)

    assert output_buf.raw[GUARD:GUARD + DATA] == zero_data

    output_ptr = ctypes.cast(ctypes.byref(output_buf, GUARD), ctypes.POINTER(RGBQUAD))
    assert GetDIBColorTable(dc, 3, 2, output_ptr) == 2

    raw = output_buf.raw
    assert raw[GUARD:GUARD + DATA] == input_data
    assert raw[:GUARD] == GUARD_BYTE * GUARD
    assert raw[GUARD + DATA:] == GUARD_BYTE * GUARD
    assert raw == GUARD_BYTE * GUARD + input_data + GUARD_BYTE * GUARD

    return True
