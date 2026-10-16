import base64, gzip, hashlib, json, re
from pathlib import Path

def load_payload(ir_root, entry):
    if not re.fullmatch(r"[0-9]{4}\.json\.gz", entry.irfile):
        raise ValueError("invalid irfile")
    data = (Path(ir_root) / entry.irfile).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry.ir_sha256:
        raise ValueError("ir sha256 mismatch")
    obj = json.loads(gzip.decompress(data))
    raw = base64.b64decode(obj["raw_base64"], validate=True)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != obj["sha256"] or digest != entry.source_sha256:
        raise ValueError("source sha256 mismatch")
    if len(raw) != obj["size"] or len(raw) != entry.size:
        raise ValueError("size mismatch")
    return raw, obj