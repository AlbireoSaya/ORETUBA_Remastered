from collections import Counter

def command_counts(parts):
    groups = {}
    for r in parts:
        if r['kind'] == 'record':
            groups.setdefault(r['opcode'], []).append(r)
    out = []
    for opcode in sorted(groups):
        rs = groups[opcode]
        out.append({
            'opcode': opcode,
            'records': len(rs),
            'conditions': Counter(r['condition']['kind'] for r in rs),
            'item_kinds': Counter(i['kind'] for r in rs for i in r['items']),
            'arity': Counter(str(len(r['items'])) for r in rs),
            'first3': [r['start'] for r in rs[:3]],
        })
    return out