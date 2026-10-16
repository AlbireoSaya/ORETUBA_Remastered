# -*- coding: utf-8 -*-
r"""修复名字串的尾部填充（ISSUE-ORETUBAR-R）。

现象：部分角色名后渲染出 `□□□`（占位符）。
推断：名字声明串的**尾部填充字节**在名字框的快速渲染路径上被当成未知字符。

本脚本扫描构建产物里所有形如
    `01 01 <u16 len> <名字文本><填充> 00`
的声明串，把**半角空格填充**统一替换为**全角空格**（GBK 双字节、宽度确定），
并对长度求和做一致性检查（保持原字节数不变 ⇒ 零位移）。
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

LPK = r'E:\ZCode Workspace\Galgame\_game_ascii\ORETSUBA_R\SCRIPT.LPK'
OUT = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\语料\名字填充修正.json'
SP = 0x20
FW = '\u3000'.encode('gbk')


def main():
    lp = LP.load(LPK)
    files = sorted(n for n, _ in lp['ents'] if n.lower().endswith('.tob'))
    fixes = []
    stats = {'scanned': 0, 'nhalf': 0, 'nfull': 0}
    for fn in files:
        raw = LP.read_entry(lp, fn)['plain']
        for m in re.finditer(rb'\x01\x01', raw):
            j = m.start()
            if j + 4 > len(raw):
                continue
            ln = raw[j + 2] | (raw[j + 3] << 8)
            if not (2 < ln < 64):
                continue
            boff = j + 4
            body = raw[boff:boff + ln]
            if body[-1:] != b'\x00':
                continue
            core = body[:-1]
            if not core:
                continue
            stats['scanned'] += 1
            # 统计尾部空格
            nh = len(core) - len(core.rstrip(b'\x20'))
            with_fw = core.rstrip(b'\x20')
            # 只有当「去掉半角空格后」是干净的 GBK 中文名时才算名字串
            try:
                t = with_fw.decode('gbk')
            except Exception:
                continue
            if not t or not all(0x4E00 <= ord(c) <= 0x9FFF for c in t):
                continue
            if nh:
                stats['nhalf'] += 1
            # 目标：名字后补满到与原长一致，用全角空格（保证双字节对齐）
            need = ln - 1 - len(with_fw)
            if need <= 0:
                continue
            if need % 2:
                # 奇数字节：用半角空格收尾（不可避免），但只放 1 个
                pad = FW * (need // 2) + b' '
            else:
                pad = FW * (need // 2)
            nb = with_fw + pad
            if len(nb) == ln - 1:
                stats['nfull'] += 1
                newbody = nb + b'\x00'
                if newbody != body:
                    fixes.append({'file': fn, 'offset': boff, 'len': ln,
                                  'text_bytes': list(newbody),
                                  'text': nb.decode('gbk', errors='replace')})
    print('扫描声明串 %d；含半角空格填充 %d；重写 %d' % (stats['scanned'], stats['nhalf'], len(fixes)))
    from collections import Counter
    c = Counter(x['text'].rstrip('\u3000 ') for x in fixes)
    print('涉及名字 %d 种' % len(c))
    for k, v in c.most_common(15):
        print('   %-12s %d 条' % (k, v))
    json.dump(fixes, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', OUT)


if __name__ == '__main__':
    main()
