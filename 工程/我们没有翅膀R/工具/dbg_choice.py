# -*- coding: utf-8 -*-
"""调试：对比选择支文件的分支跳转（ISSUE-ORETUBAR-R）。"""
import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as LP
import tob_extract as EX

name = sys.argv[1] if len(sys.argv) > 1 else 's01_12b.tob'
orig = open(os.path.join(r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\R版SCRIPT', name), 'rb').read()
lp = LP.load(r'E:\ZCode Workspace\Galgame\ORETSUBA_R\ORETSUBA_R\SCRIPT.LPK')
cur = LP.read_entry(lp, name)['plain']

io_ = EX.parse_header(orig)
ic_ = EX.parse_header(cur)
cs_o, cs_c = io_['code_start'], ic_['code_start']
lbl_o = {l[0]: l[1] for l in io_['labels']}
lbl_c = {l[0]: l[1] for l in ic_['labels']}
print('原始 code_start=%d 标签=%s' % (cs_o, lbl_o))
print('产物 code_start=%d 标签=%s' % (cs_c, lbl_c))
print()

JUMP = re.compile(rb'\x02\xff\x00(....)', re.S)

for tag, raw, cs, lbl in (('原始', orig, cs_o, lbl_o), ('产物', cur, cs_c, lbl_c)):
    print('=== %s ===' % tag)
    # 选项块附近的分支跳转（@600..1400）
    for m in JUMP.finditer(raw):
        if 600 <= m.start() <= 1400:
            addr = int.from_bytes(m.group(1), 'little')
            tgt = cs + addr
            ok = tgt < len(raw)
            print('  @%d -> addr=%d 文件偏移=%d %s' % (m.start(), addr, tgt, '' if ok else '(越界!)'))
            if ok:
                print('     目标:', raw[tgt:tgt + 32])
    # 引用标签的指令
    for k in ('_分岐', '_選択肢', '_SC_SKIP', '_START'):
        v = lbl[k]
        for vm in re.finditer(re.escape(v.to_bytes(4, 'little')), raw):
            loc = vm.start()
            print('  引用 %s(%d) 于 @%d' % (k, v, loc))
    print()
