# -*- coding: utf-8 -*-
import os, re, collections, json

SCRIPTS = r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包"

files = sorted(os.listdir(SCRIPTS))
files = [f for f in files if os.path.isfile(os.path.join(SCRIPTS, f))]

img_lines = []   # (file, lineno, tasktype, raw)
imgs = []

for f in files:
    p = os.path.join(SCRIPTS, f)
    data = open(p, 'rb').read()
    try:
        txt = data.decode('shift_jis', errors='replace')
    except Exception:
        txt = data.decode('latin-1')
    lines = txt.split('\n')
    for i, ln in enumerate(lines):
        m = re.match(r'^\s*:Image\b(.*)$', ln.rstrip('\r'))
        if m:
            # find nearest preceding :Tasktype
            tt = None
            for j in range(i-1, max(-1, i-30), -1):
                m2 = re.match(r'^\s*:Tasktype\s+"?([A-Za-z0-9_]+)"?', lines[j])
                if m2:
                    tt = m2.group(1); break
            # nearest preceding //eyecatch comment
            ec = None
            for j in range(i-1, max(-1, i-25), -1):
                m3 = re.search(r'//\s*eyecatch\s*([0-9,\s]+)', lines[j])
                if m3:
                    ec = m3.group(1).strip(); break
            args = m.group(1).split('//')[0].strip()
            img_lines.append((f, i+1, tt, args, ec))

print("total :Image lines:", len(img_lines))

# tasktype distribution
ttc = collections.Counter(x[2] for x in img_lines)
print("\n[Tasktype distribution]")
for k,v in ttc.most_common(20):
    print("  %-20s %d" % (k, v))

# argument shape distribution
print("\n[Argument value distribution]")
shapes = collections.Counter()
for f,ln,tt,args,ec in img_lines:
    shapes[(tt,args)] += 1
for (tt,args),v in sorted(shapes.items(), key=lambda x:-x[1])[:40]:
    print("  %-14s %-20s %d" % (tt, args, v))

# count by number of fields
print("\n[Field count]")
fc = collections.Counter(len([x for x in a.split(',')]) for f,ln,tt,a,ec in img_lines)
for k,v in sorted(fc.items()):
    print("  %d fields: %d" % (k,v))

json.dump(img_lines, open(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\素材\美咲线\_img_lines.json","w"), ensure_ascii=False, indent=0)
