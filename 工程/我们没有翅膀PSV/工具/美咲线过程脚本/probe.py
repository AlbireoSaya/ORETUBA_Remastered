# -*- coding: utf-8 -*-
"""Probe container + codec of audio entries (read-only)."""
import os, sys, json

PYPATH = r"E:\ZCode Workspace\Galgame\工具\pylibs"
sys.path.insert(0, PYPATH)

MEDIA = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\解密\PCSG00299\media"

import cricodecs as C
from cricodecs import awb as Cawb, cpk as Ccpk

os.chdir(MEDIA)


def hexdump(b, n=64, base=0):
    out = []
    for i in range(0, min(len(b), n), 16):
        chunk = b[i:i + 16]
        hx = " ".join(f"{x:02X}" for x in chunk)
        asc = "".join(chr(x) if 32 <= x < 127 else "." for x in chunk)
        out.append(f"  {base + i:08X}  {hx:<47}  {asc}")
    return "\n".join(out)


def banner(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# ---------- VOICE.AWB (AFS2) ----------
banner("VOICE.AWB  -> AFS2 via cricodecs.awb")
v = Cawb.load("VOICE.AWB")
print(f"file_count={v.file_count}  alignment={v.alignment}  version={v.version}  subkey={v.subkey}")
for idx in (0, 1, 26500 - 1):
    e = v.entry_info(idx)
    d = v.file_bytes(idx)
    print(f"entry[{idx}] offset={e.offset} size={e.size} wave_id={e.wave_id} "
          f"real_size={len(d)} magic={d[:8]!r}")
    print(hexdump(d, 64))

# ---------- BGM.AWB / SE.AWB / SystemSE.AWB (actually CPK) ----------
for fn in ("BGM.AWB", "SE.AWB", "SystemSE.AWB"):
    banner(f"{fn}  -> CPK via cricodecs.cpk")
    c = Ccpk.load(fn)
    print(f"file_count={c.file_count}  alignment={c.alignment}  tver={c.tver!r} "
          f"comment={c.comment!r} layout={c.layout_mode} preset={c.preset}")
    for idx in (0, 1, c.file_count - 1):
        try:
            e = c.file_info(idx)
            d = c.file_bytes(idx)
            print(f"entry[{idx}] id={e.id} path={e.full_path!r} fname={e.filename!r} "
                  f"off={e.file_offset} size={e.file_size} compressed={e.is_compressed} "
                  f"extract_size={e.extract_size} real_size={len(d)} magic={d[:8]!r}")
            print(hexdump(d, 64))
        except Exception as ex:
            print(f"entry[{idx}] ERROR: {type(ex).__name__}: {ex}")
