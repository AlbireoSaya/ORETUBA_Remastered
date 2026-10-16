import re

from otv_lossless_lines import scan_lines

_INLINE_HEADER = re.compile(r'\[([^\]\r\n]*)\]\s*\{\s*(?://.*)?')


def build_blocks(data):
    records = scan_lines(data)
    nodes = []
    root_properties = []
    root_unknowns = []
    diagnostics = []
    stack = []
    pending = None

    def orphan_header():
        nonlocal pending
        if pending is not None:
            diagnostics.append({'code': 'orphan_header', 'line': pending['line']})
            pending = None

    def open_node(name, header_line, start, rec):
        node = {
            'id': len(nodes),
            'parent': stack[-1] if stack else None,
            'name': name,
            'header_line': header_line,
            'open_line': rec['line'],
            'close_line': None,
            'start': start,
            'end': None,
            'properties': [],
            'unknowns': [],
        }
        nodes.append(node)
        stack.append(node['id'])

    for rec in records:
        kind = rec['kind']
        if kind == 'blank' or kind == 'comment':
            continue
        if kind == 'header':
            orphan_header()
            pending = rec
            continue
        if kind == 'open':
            if pending is not None:
                head, pending = pending, None
                open_node(head['name'], head['line'], head['start'], rec)
            else:
                diagnostics.append({'code': 'anonymous_open', 'line': rec['line']})
                open_node(None, None, rec['start'], rec)
            continue
        if kind == 'close':
            orphan_header()
            if stack:
                node = nodes[stack.pop()]
                node['close_line'] = rec['line']
                node['end'] = rec['end']
            else:
                diagnostics.append({'code': 'unexpected_close', 'line': rec['line']})
            continue
        if kind == 'property':
            orphan_header()
            if stack:
                nodes[stack[-1]]['properties'].append(rec['line'])
            else:
                root_properties.append(rec['line'])
            continue
        match = _INLINE_HEADER.fullmatch(rec['text'].strip()) if kind == 'opaque' else None
        if match:
            orphan_header()
            open_node(match.group(1), rec['line'], rec['start'], rec)
            continue
        orphan_header()
        if stack:
            nodes[stack[-1]]['unknowns'].append(rec['line'])
        else:
            root_unknowns.append(rec['line'])
        diagnostics.append({'code': 'unknown_line', 'line': rec['line']})

    if pending is not None:
        diagnostics.append({'code': 'orphan_header', 'line': pending['line']})
        pending = None
    eof = len(data)
    for node_id in stack:
        node = nodes[node_id]
        node['end'] = eof
        diagnostics.append({'code': 'unclosed_block', 'line': node['open_line']})
    stack = []

    return {
        'records': records,
        'nodes': nodes,
        'root_properties': root_properties,
        'root_unknowns': root_unknowns,
        'diagnostics': diagnostics,
        'semantic_status': 'unresolved',
    }
