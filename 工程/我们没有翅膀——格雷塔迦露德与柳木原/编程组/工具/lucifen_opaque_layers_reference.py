def opaque_layers32_reference(dest, width, height, pitch, row0, color, layers,
                              mode=0, target_id=0, clear=True):
    """Fixture-only opaque 32bpp compositor over a caller-supplied byte buffer."""
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        raise ValueError("width must be a positive int")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        raise ValueError("height must be a positive int")
    if not isinstance(pitch, int) or isinstance(pitch, bool) or pitch == 0:
        raise ValueError("pitch must be a non-zero signed int")
    if not isinstance(row0, int) or isinstance(row0, bool):
        raise ValueError("row0 must be an integer index")
    buf = bytearray(dest)
    if clear:
        fill = (color & 0xFFFFFFFF).to_bytes(4, "little")
        for y in range(height):
            for x in range(width):
                i = row0 + y * pitch + x * 4
                if i < 0 or i + 4 > len(buf):
                    raise ValueError("clear write out of bounds")
                buf[i:i + 4] = fill
    m = mode & 0xFF
    if m not in (0, 1, 2):
        return bytes(buf)
    tid = target_id & 0xFFFFFFFF
    for layer in layers:
        if not layer["visible"] or not layer["enabled"]:
            continue
        lid = layer["id"] & 0xFFFFFFFF
        if m == 1 and lid != tid:
            continue
        if m == 2 and lid == tid:
            continue
        src = layer["data"]
        lw, lh = layer["width"], layer["height"]
        lp, lr = layer["pitch"], layer["row0"]
        lx, ly = layer["x"], layer["y"]
        for row in range(lh):
            for col in range(lw):
                tx, ty = lx + col, ly + row
                if not (0 <= tx < width and 0 <= ty < height):
                    continue
                si = lr + row * lp + col * 4
                if si < 0 or si + 4 > len(src):
                    raise ValueError("layer source out of bounds")
                di = row0 + ty * pitch + tx * 4
                if di < 0 or di + 4 > len(buf):
                    raise ValueError("target write out of bounds")
                buf[di:di + 4] = src[si:si + 4]
    return bytes(buf)
