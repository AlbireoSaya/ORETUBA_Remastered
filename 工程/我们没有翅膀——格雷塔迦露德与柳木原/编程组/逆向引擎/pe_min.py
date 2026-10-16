#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小 PE (x86) 解析器：文件偏移 <-> RVA 映射 + 节表 + 导入表 + 字符串扫描。

只依赖标准库。反汇编部分见 disasm.py（capstone）。
目标：D:\\Gal\\[Navel]我们没有翅膀\\ORE_TUBA.EXE（只读）。

用法：
  python -X utf8 pe_min.py            # 打印概览
  python -X utf8 pe_min.py --imports  # 打印导入表
"""
import struct
import sys

DUMP_PATH = r"D:\Gal\[Navel]我们没有翅膀\ORE_TUBA.EXE"


class PE:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        assert d[:2] == b"MZ", "not MZ"
        e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not PE"
        coff = e_lfanew + 4
        (self.machine, self.nsections, self.timestamp, self.ptr_symtab,
         self.nsyms, self.size_opt, self.characteristics) = struct.unpack_from(
            "<HHIIIHH", d, coff)
        opt = coff + 20
        self.opt = opt
        self.magic = struct.unpack_from("<H", d, opt)[0]  # 0x10b = PE32
        self.entry_rva = struct.unpack_from("<I", d, opt + 16)[0]
        self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
        self.section_align = struct.unpack_from("<I", d, opt + 32)[0]
        self.file_align = struct.unpack_from("<I", d, opt + 36)[0]
        self.size_image = struct.unpack_from("<I", d, opt + 56)[0]
        self.size_headers = struct.unpack_from("<I", d, opt + 60)[0]
        self.subsystem = struct.unpack_from("<H", d, opt + 68)[0]
        self.ddir_off = opt + 96
        n_ddir = struct.unpack_from("<I", d, opt + 92)[0]
        # 交叉验证修复（ISSUE-20261007-11）：OT_PREDE.EXE 的 NumberOfRvaAndSizes 字段为垃圾值
        # （opt+92 = 3758087646）⇒ 按 PE32 上限 16 与实际文件大小夹紧，避免 struct 越界。
        # 对 ORE 无影响（其 n_ddir 本就 =16）。
        n_ddir = min(n_ddir, 16)
        while n_ddir > 0 and self.ddir_off + 8 * n_ddir > len(d):
            n_ddir -= 1
        self.ddirs = []
        for i in range(n_ddir):
            rva, sz = struct.unpack_from("<II", d, self.ddir_off + 8 * i)
            self.ddirs.append((rva, sz))
        # sections
        sec_off = opt + self.size_opt
        self.sections = []
        for i in range(self.nsections):
            o = sec_off + 40 * i
            name = d[o:o + 8].rstrip(b"\0").decode("latin1")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
            chars = struct.unpack_from("<I", d, o + 36)[0]
            self.sections.append(dict(name=name, vsize=vsize, vaddr=vaddr,
                                      rawsize=rawsize, rawptr=rawptr, chars=chars))

    # ---- 映射 ----
    def rva_to_off(self, rva):
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"]):
                delta = rva - s["vaddr"]
                if delta < s["rawsize"]:
                    return s["rawptr"] + delta
                return None  # 落在未初始化尾部
        if rva < self.size_headers:
            return rva
        return None

    def off_to_rva(self, off):
        for s in self.sections:
            if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
                return s["vaddr"] + (off - s["rawptr"])
        if off < self.size_headers:
            return off
        return None

    def read_rva(self, rva, n):
        off = self.rva_to_off(rva)
        if off is None:
            return None
        return self.data[off:off + n]

    def section_of_off(self, off):
        for s in self.sections:
            if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
                return s
        return None

    def imports(self):
        """返回 [(dllname, [(funcname_or_ord, hint_rva), ...]), ...]"""
        if not self.ddirs or len(self.ddirs) < 2:
            return []
        imp_rva, imp_sz = self.ddirs[1]
        if imp_rva == 0:
            return []
        out = []
        off = self.rva_to_off(imp_rva)
        while off is not None:
            ilt, ts, fc, name_rva, iat = struct.unpack_from("<IIIII", self.data, off)
            if ilt == 0 and ts == 0 and name_rva == 0:
                break
            dll = self.read_rva(name_rva, 64)
            dll = dll.split(b"\0")[0].decode("latin1") if dll else "?"
            funcs = []
            tho = self.rva_to_off(ilt or iat)
            if tho is not None:
                while True:
                    ent = struct.unpack_from("<I", self.data, tho)[0]
                    if ent == 0:
                        break
                    if ent & 0x80000000:
                        funcs.append(("#%d" % (ent & 0xFFFF), 0))
                    else:
                        hn = self.read_rva(ent + 2, 64)
                        hn = hn.split(b"\0")[0].decode("latin1") if hn else "?"
                        funcs.append((hn, ent))
                    tho += 4
            out.append((dll, funcs))
            off += 20
        return out


def main():
    pe = PE(DUMP_PATH)
    print("file bytes   :", len(pe.data))
    print("image base   : 0x%08X" % pe.image_base)
    print("entry RVA    : 0x%08X  (VA 0x%08X)" % (pe.entry_rva, pe.image_base + pe.entry_rva))
    print("sections     :", pe.nsections)
    for s in pe.sections:
        print("  %-8s vaddr=0x%08X vsz=0x%08X rawptr=0x%06X rawsz=0x%08X chars=0x%08X"
              % (s["name"], s["vaddr"], s["vsize"], s["rawptr"], s["rawsize"], s["chars"]))
    print("ddirs:")
    names = ["EXPORT", "IMPORT", "RESOURCE", "EXCEPTION", "SECURITY", "BASERELOC",
             "DEBUG", "ARCH", "GLOBALPTR", "TLS", "LOADCFG", "BOUNDIMP", "IAT",
             "DELAYIMP", "CLR", "RESV"]
    for i, (rva, sz) in enumerate(pe.ddirs):
        nm = names[i] if i < len(names) else str(i)
        if rva or sz:
            print("  %-10s rva=0x%08X sz=0x%06X" % (nm, rva, sz))
    if "--imports" in sys.argv:
        print("imports:")
        for dll, funcs in pe.imports():
            print("  %s : %d" % (dll, len(funcs)))
            for fn, hr in funcs:
                print("      %s" % fn)


if __name__ == "__main__":
    main()
