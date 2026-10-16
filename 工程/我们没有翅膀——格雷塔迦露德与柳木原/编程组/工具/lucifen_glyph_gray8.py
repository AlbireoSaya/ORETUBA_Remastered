from lucifen_glyph_gray8_input import validate_gray8_input

def unpack_gray8_bitmap(data, width, height):
    stride, raw = validate_gray8_input(data, width, height)
    coverage = b"" if width == 0 or height == 0 else b"".join(
        raw[y * stride:y * stride + width] for y in range(height)
    )
    if any(b > 64 for b in coverage):
        raise ValueError("coverage byte exceeds 64")
    return {"width": width, "height": height, "stride": stride, "coverage_0_64": coverage}
