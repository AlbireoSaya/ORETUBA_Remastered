def scan_lines(data: bytes):
    import re, base64
    out, n = [], 0
    for m in re.finditer(rb'[^\r\n]*(?:\r\n|\r|\n|$)', data):
        if m.start() == m.end(): continue
        n += 1
        raw = m.group(0)
        item = {'line': n, 'start': m.start(), 'end': m.end(), 'raw_b64': base64.b64encode(raw).decode('ascii')}
        try:
            s = raw.decode('cp932')
        except UnicodeDecodeError as e:
            item['kind'], item['error'] = 'decode_error', str(e)
            out.append(item); continue
        if s.endswith('\r\n'): text = s[:-2]
        elif s.endswith('\r') or s.endswith('\n'): text = s[:-1]
        else: text = s
        item['text'] = text
        t = text.strip()
        if not t: item['kind'] = 'blank'
        elif t.startswith('//'): item['kind'] = 'comment'
        else:
            mh = re.fullmatch(r'\[([^\]\r\n]*)\]\s*(?://.*)?', t)
            if mh:
                item['kind'], item['name'] = 'header', mh.group(1)
            elif re.fullmatch(r'\{\s*(?://.*)?', t):
                item['kind'] = 'open'
            elif re.fullmatch(r'\}\s*(?://.*)?', t):
                item['kind'] = 'close'
            else:
                mp = re.fullmatch(r':([^\s]+)(?:\s+(.*))?', text.lstrip())
                if mp:
                    item['kind'], item['key'], item['value_raw'] = 'property', mp.group(1), mp.group(2) or ''
                else:
                    item['kind'] = 'opaque'
        out.append(item)
    return out