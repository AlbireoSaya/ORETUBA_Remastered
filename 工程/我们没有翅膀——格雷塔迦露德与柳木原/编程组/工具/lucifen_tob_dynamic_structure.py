import struct

def _need(data, off, size):
    if off < 0 or size < 0 or off + size > len(data):
        raise ValueError("truncated")

def _u16(data, off):
    _need(data, off, 2)
    return struct.unpack_from("<H", data, off)[0]

def _u32(data, off):
    _need(data, off, 4)
    return struct.unpack_from("<I", data, off)[0]

def parse_expression(data, p):
    if isinstance(p, bool) or not isinstance(p, int) or p < 0:
        raise ValueError("bad p")
    _need(data, p, 2)
    n = _u16(data, p)
    code_start = p + 2
    _need(data, code_start, n)
    flag_offset = code_start + n
    _need(data, flag_offset, 1)
    flag = data[flag_offset]
    table_word = flag_offset + 1
    size = _u16(data, table_word)
    if size < 7:
        raise ValueError("table too small")
    end = table_word + size
    if end > len(data):
        raise ValueError("table truncated")
    cur = table_word + 2
    relocations = []
    for group in range(5):
        _need(data, cur, 1)
        count = data[cur]
        cur += 1
        for index in range(count):
            _need(data, cur, 8)
            slot_offset = _u32(data, cur)
            bank_index = _u32(data, cur + 4)
            cur += 8
            if slot_offset + 4 > n:
                raise ValueError("slot out of range")
            relocations.append({
                "group": group,
                "slot_offset": slot_offset,
                "index": bank_index,
            })
    if cur != end:
        raise ValueError("table end mismatch")
    return {
        "code_start": code_start,
        "code_size": n,
        "flag_offset": flag_offset,
        "compiled_flag": flag,
        "reloc_start": table_word,
        "reloc_size": size,
        "relocations": relocations,
    }, end

def parse_items(data, p, end):
    items = []
    if p + 1 > end:
        raise ValueError("count out of bounds")
    _need(data, p, 1)
    count = data[p]
    p += 1
    for _ in range(count):
        if p + 1 > end:
            raise ValueError("tag out of bounds")
        _need(data, p, 1)
        tag = data[p]
        p += 1
        if tag == 0:
            items.append(dict(tag=0, kind="empty", flags=0, value=0))
            continue
        if tag == 2:
            if p + 4 > end:
                raise ValueError("value out of bounds")
            _need(data, p, 4)
            items.append(dict(tag=2, kind="literal", flags=0, value=_u32(data, p)))
            p += 4
            continue
        if p + 1 > end:
            raise ValueError("selector out of bounds")
        _need(data, p, 1)
        sel = data[p]
        p += 1
        if sel == 0:
            if p + 4 > end:
                raise ValueError("value out of bounds")
            _need(data, p, 4)
            items.append(dict(tag=tag, kind="literal", flags=tag,
                              value=_u32(data, p), selector=sel))
            p += 4
        elif sel == 1:
            if p + 2 > end:
                raise ValueError("inline length out of bounds")
            _need(data, p, 2)
            n = _u16(data, p)
            p += 2
            if p + n > end:
                raise ValueError("inline data out of bounds")
            items.append(dict(tag=tag, kind="inline", flags=tag | 2,
                              data_offset=p, data_size=n, selector=sel))
            p += n
        elif sel == 2:
            if p + 8 > end:
                raise ValueError("array out of bounds")
            _need(data, p, 8)
            bank = _u32(data, p)
            elem = _u32(data, p + 4)
            p += 8
            items.append(dict(tag=tag, kind="array", flags=tag,
                              bank_index=bank, element_index=elem, selector=sel))
        elif sel == 3:
            expr, p = parse_expression(data, p)
            if p > end:
                raise ValueError("expression out of bounds")
            items.append(dict(tag=tag, kind="expression", flags=tag,
                              expression=expr, selector=sel))
        else:
            raise NotImplementedError("selector %d" % sel)
    if p != end:
        raise ValueError("parse_items cursor mismatch")
    return items, p

def parse_record(data: bytes, start: int) -> dict:
    if start < 0 or start + 7 > len(data):
        raise ValueError("record header out of bounds")
    if data[start:start + 2] != b'\x5b\x20':
        raise ValueError("bad record header")
    opcode = int.from_bytes(data[start + 2:start + 6], "little")
    tag = data[start + 6]
    p = start + 7
    if tag == 0:
        if p + 4 > len(data):
            raise ValueError("condition literal out of bounds")
        condition = {"tag": 0, "kind": "literal",
                     "value": int.from_bytes(data[p:p + 4], "little")}
        p += 4
    elif tag == 1:
        condition = {"tag": 1, "kind": "always"}
    elif tag == 2:
        if p + 8 > len(data):
            raise ValueError("condition array out of bounds")
        condition = {"tag": 2, "kind": "array",
                     "bank_index": int.from_bytes(data[p:p + 4], "little"),
                     "element_index": int.from_bytes(data[p + 4:p + 8], "little")}
        p += 8
    elif tag == 3:
        expression, p = parse_expression(data, p)
        condition = {"tag": 3, "kind": "expression", "expression": expression}
    else:
        raise NotImplementedError("native condition table tag %d" % tag)
    length_offset = p
    if p + 4 > len(data):
        raise ValueError("record length out of bounds")
    declared_length = int.from_bytes(data[p:p + 4], "little")
    if declared_length < 5:
        raise ValueError("declared length below minimum")
    end = p + declared_length
    if end > len(data):
        raise ValueError("record end out of bounds")
    items, _next = parse_items(data, p + 4, end)
    return {"start": start, "end": end, "opcode": opcode, "condition": condition,
            "length_offset": length_offset, "declared_length": declared_length,
            "items": items}

import struct, hashlib, base64

def pack_ir(data):
    end = 4 + struct.unpack_from('<I', data, 4)[0]
    code_start = end + struct.unpack_from('<I', data, end)[0]
    parts = [{'kind': 'header', 'start': 0, 'end': code_start}]
    pos = code_start
    while pos < len(data):
        i = data.find(b'\x5b\x20', pos)
        if i < 0:
            if pos < len(data):
                parts.append({'kind': 'island', 'start': pos, 'end': len(data)})
            break
        if i > pos:
            parts.append({'kind': 'island', 'start': pos, 'end': i})
        r = parse_record(data, i)
        rec_end = r['end']
        if rec_end <= i or rec_end > len(data):
            raise ValueError('nonprogress/outofbounds')
        item = {'kind': 'record', 'start': i, 'end': rec_end}
        item.update(r)
        parts.append(item)
        pos = rec_end
    return {'raw_base64': base64.b64encode(data).decode('ascii'),
            'sha256': hashlib.sha256(data).hexdigest(),
            'size': len(data), 'parts': parts,
            'semantic_status': 'unresolved'}
from pathlib import Path
import json, gzip, hashlib

def emit(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    if not any(out.is_relative_to(root / d) for d in ('子代理工作区', '临时')):
        raise ValueError('out outside workspace')
    out.mkdir(parents=True, exist_ok=False)
    src = root / '工程' / '我们没有翅膀R' / '语料' / 'R版SCRIPT'
    entries, tr, ti, ts, tv = [], 0, 0, 0, 0
    for i, p in enumerate(sorted(q for q in src.rglob('*') if q.suffix.lower() == '.tob'), 1):
        raw = p.read_bytes()
        if raw[:4] not in (b'TOB0', b'TOB1'):
            raise ValueError(f'magic: {p}')
        obj = pack_ir(raw)
        parts, size, prev = obj['parts'], len(raw), 0
        for q in parts:
            if q['start'] != prev or q['end'] > size:
                raise ValueError(f'parts: {p}')
            prev = q['end']
        if prev != size:
            raise ValueError(f'cover: {p}')
        blob = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        name = f'{i:04d}.json.gz'
        with (out / name).open('xb') as rawout, gzip.GzipFile(filename='', mode='wb', fileobj=rawout, mtime=0) as fh:
            fh.write(blob)
        if p.read_bytes() != raw:
            raise RuntimeError(f'changed: {p}')
        r = sum(1 for q in parts if q['kind'] == 'record')
        s = sum(1 for q in parts if q['kind'] == 'island')
        entries.append({'path': str(p.relative_to(root)), 'source_sha256': hashlib.sha256(raw).hexdigest(),
                        'size': size, 'irfile': name, 'ir_sha256': hashlib.sha256((out / name).read_bytes()).hexdigest(), 'json_sha256': hashlib.sha256(blob).hexdigest(),
                        'records': r, 'islands': s, 'parts': len(parts)})
        tr, ti, ts, tv = tr + r, ti + s, ts + size, tv + (out / name).stat().st_size
    def dump(n, o):
        (out / n).write_text(json.dumps(o, ensure_ascii=False), encoding='utf-8')
    dump('manifest.json', {'structural_only': True, 'files': entries})
    summary = {'structural_only': True, 'files': len(entries), 'records': tr,
               'islands': ti, 'source_bytes': ts, 'ir_bytes': tv}
    dump('summary.json', summary)
    return summary