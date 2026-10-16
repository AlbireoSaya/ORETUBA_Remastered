# -*- coding: utf-8 -*-
"""只读：按 scene 顺序打印记录流（op 十进制 + items + body_hex），供人工读演出序。"""
import io, sys

SCENE = sys.argv[1] if len(sys.argv) > 1 else "ota_11_1a"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 400

recs = []
with io.open("_records_ota.tsv", encoding="utf-8") as f:
    next(f)
    for line in f:
        p = line.rstrip("\n").split("\t")
        if p[0] == SCENE:
            recs.append(p)

print("scene=%s  records=%d" % (SCENE, len(recs)))
NAMES = {0x0c:"line_end",0x10:"line_begin",0x12:"title",0x18:"dialog",0x22:"bg_set",
         0x14:"wait",0x49:"chr_a",0x51:"chr_act",0x52:"chr_pos",0x5d:"wait",0x61:"wait",
         0x66:"chr_b",0x76:"se",0x2f:"move",0x30:"move",0x32:"keyframe",0x3b:"msvec",
         0x63:"bg_fx",0x64:"bg_fx",0x65:"bg_fx",0x77:"se_fx",0x7d:"chr_sp",0x07:"lab_sc",
         0x08:"jmp",0x0d:"choice"}
for i, r in enumerate(recs[:LIMIT]):
    op = int(r[2])
    nm = NAMES.get(op, "")
    print("%4d %-8s op=0x%02x(%3d) n=%s items=%s" % (i, r[1], op, op, r[6], r[7]))
    if r[9]:
        print("        err=%s hex=%s" % (r[9], r[8]))
