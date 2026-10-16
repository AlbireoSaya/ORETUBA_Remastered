import sys
import json
sys.path.append("工具/pylibs")
from cricodecs import cpk
from pathlib import Path
import hashlib

p = Path("工程/我们没有翅膀PSV/解密/PCSG00299/media/SCRIPT.cpk")
raw = p.read_bytes()
a = cpk.Cpk.load_bytes(raw)
archive_sha256 = hashlib.sha256(raw).hexdigest()

d = Path("工程/我们没有翅膀PSV/脚本解包")
files = list(a.files)
entries = enumerate(files)
mp = {p.name.lower(): p for p in d.iterdir() if p.is_file()}
names = {f.filename.lower() for f in files}

def sha(x):
    return hashlib.sha256(x.encode() if isinstance(x, str) else x).hexdigest()

rows = []
missing = []
for i, f in entries:
    name = f.filename
    data = a.file_bytes(i)
    h = sha(data)
    lp = mp.get(name.lower())
    lh = sha(lp.read_bytes()) if lp else None
    rows.append({
        'name': name,
        'sha256': h,
        'local_sha256': lh,
        'match': h == lh,
        'bytes': len(data),
        'full_path': f.full_path,
    })
    if lp is None:
        missing.append(name)

extra = sorted(p.name for p in mp.values() if p.name.lower() not in names)

print(json.dumps({
    'rows': rows,
    'missing': missing,
    'extra': extra,
    'count': a.file_count,
    'archive_sha256': archive_sha256,
}, ensure_ascii=False))