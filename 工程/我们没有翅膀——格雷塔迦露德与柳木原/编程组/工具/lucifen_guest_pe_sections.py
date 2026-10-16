from unicorn import UC_PROT_ALL

def map_sections(uc, pe):
    mapped_size = (pe.size_image + 0xFFF) & ~0xFFF
    base = pe.image_base
    uc.mem_map(base, mapped_size, UC_PROT_ALL)
    try:
        uc.mem_write(base, pe.data[:pe.size_headers])
        for s in pe.sections:
            rawsize = s["rawsize"]
            if rawsize:
                rawptr = s["rawptr"]
                uc.mem_write(base + s["vaddr"], pe.data[rawptr:rawptr + rawsize])
    except Exception:
        try:
            uc.mem_unmap(base, mapped_size)
        except Exception:
            pass
        raise
    return mapped_size
