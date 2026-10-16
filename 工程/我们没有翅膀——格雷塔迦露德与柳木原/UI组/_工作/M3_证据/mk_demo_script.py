#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
mk_demo_script.py — M3 自检/构建辅助（**非交付物，仅存于 _工作/M3_证据/**）

用途：把 资源组\剧本\scene_ot.jsonl 中场景 ot_s01_08c0 的真实中文台词
      注入 复刻/replica.js 的 DEMO_SCRIPT 常量。

铁律遵守：
  · 资源组\ 只读；只写 复刻\replica.js（本模块允许的写入范围）
  · 台词零改写：speaker / cn / text_cn / next 一律原样搬运
  · 同时输出 demo_script.json 作为可复核的中间证据

用法：
  python mk_demo_script.py --check     只打印将注入的内容概要，不写文件
  python mk_demo_script.py --write     执行注入
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.abspath(os.path.join(HERE, '..', '..'))            # ...\UI组
REPO = os.path.abspath(os.path.join(UI_DIR, '..'))                   # ...\我们没有翅膀——...
JSONL = os.path.join(REPO, '资源组', '剧本', 'scene_ot.jsonl')
REPLICA_JS = os.path.join(UI_DIR, '复刻', 'replica.js')
OUT_JSON = os.path.join(HERE, 'demo_script.json')

SCENE_ID = 'ot_s01_08c0'
SEQ_FROM, SEQ_TO = 3, 123       # 排除 seq1=章节标题、seq2=梗概，以及 seq124-126=选择肢文本本身


def build():
    rows = []
    with io.open(JSONL, encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    by = {r['scene_id']: r for r in rows}
    if SCENE_ID not in by:
        sys.exit('scene %s not found in %s' % (SCENE_ID, JSONL))
    sc = by[SCENE_ID]
    lines = []
    for ln in sc['lines']:
        if ln['seq'] < SEQ_FROM or ln['seq'] > SEQ_TO:
            continue
        lines.append({
            'seq': ln['seq'],
            'lineno': ln['lineno'],
            'kind': ln['kind'],
            'speaker': ln.get('speaker', ''),
            'cn': ln.get('cn', ''),
        })
    return {
        'scene_id': sc['scene_id'],
        'scene_title_cn': sc['title_cn'],
        'scene_route': sc.get('route'),
        'source': sc.get('source'),
        'source_file': '资源组/剧本/scene_ot.jsonl',
        'lineno_basis': 's01_08c0.sob 行号（scene_ot.jsonl lines[].lineno）',
        'seq_scope': [SEQ_FROM, SEQ_TO],
        'line_count': len(lines),
        'lines': lines,
        'choices': [{'text_cn': c['text_cn'], 'text_jp': c['text_jp']} for c in sc.get('choices', [])],
        'branch_targets': sc.get('next', []),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    data = build()
    blob = json.dumps(data, ensure_ascii=False, indent=1)

    with io.open(OUT_JSON, 'w', encoding='utf-8') as f:
        f.write(blob)

    print('scene      :', data['scene_id'], data['scene_title_cn'])
    print('source     :', data['source_file'], 'seq', data['seq_scope'])
    print('real lines :', data['line_count'])
    print('speakers   :', sorted(set(l['speaker'] for l in data['lines'])))
    print('choices    :', [c['text_cn'] for c in data['choices']])
    print('branch tgt :', data['branch_targets'])
    print('wrote      :', OUT_JSON)

    if not a.write:
        print('\n(--check only; pass --write to inject into replica.js)')
        return

    src = io.open(REPLICA_JS, encoding='utf-8').read()
    marker = '/*__DEMO_SCRIPT_JSON__*/ null'
    if marker not in src:
        sys.exit('marker not found in %s (already injected?)' % REPLICA_JS)
    # 保持缩进对齐：常量声明在 2 空格缩进的 IIFE 内
    injected = '/*__DEMO_SCRIPT_JSON__*/\n  ' + blob.replace('\n', '\n  ')
    out = src.replace(marker, injected, 1)
    io.open(REPLICA_JS, 'w', encoding='utf-8').write(out)
    print('injected   :', REPLICA_JS)


if __name__ == '__main__':
    main()