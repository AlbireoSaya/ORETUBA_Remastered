import pefile

def resource_entries(pe):
    """Return flat resource metadata using mature pefile, not a new PE parser.

    Root caller independently validates entire raw spans, groupicon and DIB
    structures against original source, avoids OS-loading the original, and
    is not an adversarial sandbox.
    """
    q = pefile.PE(data=pe.data, fast_load=True)
    try:
        q.parse_data_directories([2])
        root = getattr(q, "DIRECTORY_ENTRY_RESOURCE", None)
        if root is None or not getattr(root, "entries", None):
            return []

        def key(e):
            name = getattr(e, "name", None)
            if name is not None and hasattr(name, "string"):
                return name.string.decode("utf-8")
            return e.id

        out, seen = [], set()
        for te in root.entries:
            if not hasattr(te, "directory") or te.directory is None:
                raise ValueError("missing type directory")
            t = key(te)
            for ne in te.directory.entries:
                if not hasattr(ne, "directory") or ne.directory is None:
                    raise ValueError("missing name directory")
                n = key(ne)
                for le in ne.directory.entries:
                    if not hasattr(le, "data") or le.data is None:
                        raise ValueError("missing leaf data")
                    l = key(le)
                    triple = (t, n, l)
                    if triple in seen:
                        raise ValueError("duplicate resource triple")
                    seen.add(triple)
                    s = le.data.struct
                    rva = s.OffsetToData
                    out.append({
                        "type": t,
                        "name": n,
                        "language": l,
                        "rva": rva,
                        "file_offset": q.get_offset_from_rva(rva),
                        "size": s.Size,
                        "codepage": s.CodePage,
                    })
                    if len(out) > 16384:
                        raise ValueError("too many resource leaves")
        return out
    finally:
        q.close()
