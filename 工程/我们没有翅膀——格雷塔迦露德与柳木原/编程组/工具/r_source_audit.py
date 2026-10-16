import sys
import json
sys.path.append("工程/我们没有翅膀R/工具")
import lpk_patch
a = lpk_patch.load("备份/我们没有翅膀R-安装介质/SET_UP/SCRIPT.LPK")
from pathlib import Path
import hashlib
d = Path("工程/我们没有翅膀R/语料/R版SCRIPT")

ents=list(a['ents']); mp={p.name.lower():p for p in d.iterdir() if p.is_file()}; names={n.lower() for n,_ in ents}
def sha(x): return hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
rows=[]; missing=[]; extra=[]
for name,num in ents:
 p=mp.get(name.lower()); h=sha(lpk_patch.read_entry(a,name)['plain']); lh=sha(p.read_bytes()) if p else None
 rows.append({'name':name,'sha256':h,'local_sha256':lh,'match':h==lh}); missing += [name] if p is None else []
extra=sorted(p.name for p in mp.values() if p.name.lower() not in names)
print(json.dumps({'rows':rows,'missing':missing,'extra':extra,'count':a["cnt"]},ensure_ascii=False))