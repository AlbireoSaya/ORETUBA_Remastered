import hashlib
import pefile
from pathlib import Path


def dll_inventory(paths):
    rows = []
    for path in paths:
        raw = Path(path).read_bytes()
        pe = pefile.PE(data=raw)
        imports = []
        for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
            imports.append({"dll": entry.dll.decode("latin1"), "symbols": [
                {"name": s.name.decode("latin1") if s.name else None, "ordinal": s.ordinal}
                for s in entry.imports]})
        exports = []
        for sym in getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", []) or []:
            exports.append({"ordinal": sym.ordinal, "address": sym.address,
                            "name": sym.name.decode("latin1") if sym.name else None,
                            "forwarder": sym.forwarder.decode("latin1") if sym.forwarder else None})
        rows.append({"name": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                     "machine": pe.FILE_HEADER.Machine, "optional_header_magic": pe.OPTIONAL_HEADER.Magic,
                     "image_base": pe.OPTIONAL_HEADER.ImageBase, "imports": imports, "exports": exports})
        pe.close()
    return rows