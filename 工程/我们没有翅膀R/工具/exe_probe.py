# -*- coding: utf-8 -*-
r"""ORETUBAR.EXE 路径逻辑侦察：定位「存档目录如何确定」的证据。"""
import re, sys, os

sys.stdout.reconfigure(encoding='utf-8')
EXE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\壌偨偪偵梼偼側偄俼\ORETUBAR.EXE'

d = open(EXE, 'rb').read()
print('EXE size =', len(d))
print()

print('=== 关键串命中 ===')
for k in ['SaveData', 'SAVEDATA', 'USER.CFG', 'SCRIPT', 'PATCH', 'data.ini', '.ini',
          'Install', 'INSTALL', 'DataPath', 'datapath', 'Setup', 'SETUP']:
    b = k.encode('cp932')
    hits = [m.start() for m in re.finditer(re.escape(b), d)]
    print('%-12s %3d 处 %s' % (k, len(hits), [hex(x) for x in hits[:6]]))

print()
print('=== 含路径特征的可读串（前后 30 字节窗口）===')
seen = set()
for m in re.finditer(rb'[ -~]{5,}', d):
    s = m.group(0)
    # 只关心像路径/文件名/模板的串
    if not any(c in s for c in (b'\\', b'/', b'%s', b'%d', b':')):
        continue
    try:
        t = s.decode('cp932')
    except Exception:
        continue
    if t in seen:
        continue
    seen.add(t)
    print('  @0x%06x  %r' % (m.start(), t))

print()
print('=== SJIS 含反斜杠的串（日文路径习惯）===')
cnt = 0
for m in re.finditer(rb'[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]', d):
    i = m.start()
    # 只看周围 40 字节是否含 0x5C
    w = d[i:i + 40]
    if b'\\' in w and b'%' in w:
        try:
            t = d[i:i + 40].split(b'\x00')[0].decode('cp932')
        except Exception:
            continue
        print('  @0x%06x %r' % (i, t))
        cnt += 1
        if cnt > 20:
            break

print()
print('=== 版本 / 公司资源 ===')
for pat in [rb'Navel', rb'ORETUBAR', rb'1\.2\.2']:
    for m in list(re.finditer(pat, d))[:3]:
        i = m.start()
        seg = d[max(0, i - 20):i + 60]
        try:
            t = seg.decode('cp932', errors='replace')
        except Exception:
            t = repr(seg)
        print('  @0x%06x %r' % (i, t))
