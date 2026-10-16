# -*- coding: utf-8 -*-
import os, sys, json
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\pylibs")
os.chdir(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\解密\PCSG00299\media")
import cricodecs as C
out = {}
for name in ["CG.cpk", "SystemData.cpk", "ETC.cpk", "CHR.cpk"]:
    c = C.load(name)
    ents = [e.full_path for e in c.file_infos()]
    out[name] = ents
    os.makedirs(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\_cpklist", exist_ok=True)
    with open(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\_cpklist" + "\\" + name + ".txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(ents))
    print(name, "entries:", len(ents))
