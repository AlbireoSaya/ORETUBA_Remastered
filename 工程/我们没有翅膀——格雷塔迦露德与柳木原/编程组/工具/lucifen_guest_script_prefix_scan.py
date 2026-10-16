_MAGICS = (b"TOB0", b"SOB0", b"SOB1", b"SOB2")
_U32 = 1 << 32
_MAX_SIZE = 64 * 1024 * 1024


def _int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(name)
    return value


def scan_script_prefixes(read, regions, max_regions=16384):
    max_regions = _int(max_regions, "max_regions")
    if not 1 <= max_regions <= 32768:
        raise ValueError("max_regions")
    if not isinstance(regions, (list, tuple)):
        raise TypeError("regions")
    if len(regions) > max_regions:
        raise ValueError("regions")
    total_regions = len(regions)
    scanned_regions = 0
    skipped_small = 0
    matches = []
    for region in regions:
        if not isinstance(region, (list, tuple)) or len(region) != 2:
            raise TypeError("region")
        base = _int(region[0], "base")
        size = _int(region[1], "size")
        if not 1 <= base <= 0xFFFFFFFF:
            raise ValueError("base")
        if not 1 <= size <= _MAX_SIZE:
            raise ValueError("size")
        if base + size > _U32:
            raise ValueError("base+size")
        if size < 4:
            skipped_small += 1
            continue
        data = read(base, 4)
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("read")
        data = bytes(data)
        if len(data) != 4:
            raise ValueError("read length")
        scanned_regions += 1
        for magic in _MAGICS:
            if data == magic:
                matches.append({
                    "base": base,
                    "registered_size": size,
                    "magic": magic.decode("ascii"),
                })
                break
    return {
        "total_regions": total_regions,
        "scanned_regions": scanned_regions,
        "skipped_small": skipped_small,
        "matches": matches,
    }
