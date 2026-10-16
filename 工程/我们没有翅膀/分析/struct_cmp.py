# -*- coding: utf-8 -*-
"""struct_cmp.py —— 判定 SCRIPT_CHS 外挂文件与 LPK 内原版脚本的结构关系（只读）

核心问题：外挂 .sob 里为什么同时出现大量日文段？
假说 A：CHS = 原版 SJIS 字节原样保留 + 中文译文追加（双语并存，DLL 取其一）
假说 B：CHS = 原版改造（部分串仍是未翻译的 SJIS 残留）
判据：把 LPK 解出的原版条目字节，与 CHS 同名文件做「子串包含 / 顺序覆盖」比对。
"""
import os
import re
import sys

TOOLS = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具'
sys.path.insert(0, TOOLS)
import lpk_patch as LP  # noqa: E402

GAME = r'D:\Gal\[Navel]我们没有翅膀'
RUN = re.compile(rb'(?:[\x80-\xff][\x20-\xff]){3,}')


def runs(b, minlen=8):
    return [m.group(0) for m in RUN.finditer(b) if len(m.group(0)) >= minlen]


def cmp_one(entry_name, chs_name):
    lp = LP.load(os.path.join(GAME, 'SCRIPT.LPK'))
    orig = LP.read_entry(lp, entry_name)['plain']
    chs = open(os.path.join(GAME, 'SCRIPT_CHS', chs_name), 'rb').read()
    rs = runs(orig)
    in_chs = sum(1 for r in rs if r in chs)
    chs_runs = runs(chs)
    in_orig = sum(1 for r in chs_runs if r in orig)
    print('  %-18s 原版 %6d 字节 / 外挂 %6d 字节（+%d）' % (entry_name, len(orig), len(chs), len(chs) - len(orig)))
    print('     原版非 ASCII 段 %d，其中 %d (%.1f%%) 在外挂文件中逐字节原样存在'
          % (len(rs), in_chs, 100.0 * in_chs / max(1, len(rs))))
    print('     外挂非 ASCII 段 %d，其中 %d (%.1f%%) 在原版文件中逐字节存在'
          % (len(chs_runs), in_orig, 100.0 * in_orig / max(1, len(chs_runs))))
    # 首个原版段在外挂中的位置
    for r in rs[:1]:
        i = chs.find(r)
        print('     首段原版文本出现在外挂偏移 %d；外挂该处前后 96 字节：' % i)
        seg = chs[max(0, i - 48):i + 48]
        print('       cp932: %s' % seg.decode('cp932', 'replace').replace('\r', ' ').replace('\n', ' '))
        print('       gbk  : %s' % seg.decode('gbk', 'replace').replace('\r', ' ').replace('\n', ' '))
    return len(orig), len(chs), len(rs), in_chs, len(chs_runs), in_orig


def main():
    for n in ('s01_01a.sob', 's01_02a.sob', 's00_00.sob', 'gameinit.sob'):
        cmp_one(n, n)


if __name__ == '__main__':
    main()
