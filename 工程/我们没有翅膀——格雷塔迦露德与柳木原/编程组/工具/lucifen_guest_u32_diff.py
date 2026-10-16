"""Diff two caller-supplied guest u32 snapshots.

Snapshots are mappings with keys base (int), byte_count (int),
words (sequence of u32 ints), and sha256 (str).  Only the invariants
below are checked; callers must guarantee the rest of the structure.

Returns a dict with base, byte_count, before_sha256, after_sha256,
total_changed_words, truncated, and changes.  Each change contains
offset (byte offset), va (base + offset), before, after, and xor.
changes holds only the first max_changes entries; truncated is True
when additional changed words were found.
"""

def diff_u32(before, after, max_changes=256):
    base = before["base"]
    byte_count = before["byte_count"]
    if base != after["base"] or byte_count != after["byte_count"]:
        raise ValueError("snapshot base/byte_count mismatch")
    if len(before["words"]) != byte_count // 4 or len(after["words"]) != byte_count // 4:
        raise ValueError("snapshot words length does not match byte_count")
    if type(max_changes) is not int or not 1 <= max_changes <= 16384:
        raise ValueError("max_changes must be an int in 1..16384")

    changes = []
    total = 0
    bw = before["words"]
    aw = after["words"]
    for i in range(byte_count // 4):
        b = bw[i]
        a = aw[i]
        if b != a:
            total += 1
            if len(changes) < max_changes:
                off = i * 4
                changes.append({
                    "offset": off,
                    "va": base + off,
                    "before": b,
                    "after": a,
                    "xor": b ^ a,
                })

    return {
        "base": base,
        "byte_count": byte_count,
        "before_sha256": before["sha256"],
        "after_sha256": after["sha256"],
        "total_changed_words": total,
        "truncated": total > max_changes,
        "changes": changes,
    }