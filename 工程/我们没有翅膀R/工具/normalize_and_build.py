# -*- coding: utf-8 -*-
r"""全量汉化最终构建（ISSUE-ORETUBAR-R）。

流程：
  1. 归一化译文里 GBK 不可编码的符号（`・♪≪≫` 等）→ GB2312 内等效符号
     （依据：通用层 `galgame-translation\SKILL.md` §七.2「只用 GB2312 范围内的 GBK 全角标点」）
  2. 合并：迁移映射（51,736）+ 三批新译（6,624）+ 重编码映射（4,000）
  3. 调 `build_cn.py --with-extra` 重建 SCRIPT.LPK 并部署

符号归一化表（保持语义与视觉等效，不改变文本内容）：
    `・`(U+30FB 中点) → `·`(U+00B7)          —— 通用层 §六.1 明文规定
    `♪`(U+266A)       → `☆`(U+2606)          —— 装饰符，GB2312 内
    `≪`→`《`、`≫`→`》`                        —— 书名号等效
    `〜`(U+301C)      → `～`(U+FF5E)          —— 通用层 §六.1 明文规定
"""
import json, os, sys, shutil, subprocess

sys.stdout.reconfigure(encoding='utf-8')
PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'

NORM = {
    '\u30fb': '\u00b7',   # ・ -> ·
    '\u266a': '\u2606',   # ♪ -> ☆
    '\u226a': '\u300a',   # ≪ -> 《
    '\u226b': '\u300b',   # ≫ -> 》
    '\u301c': '\uff5e',   # 〜 -> ～
    '\u2015': '\u2014',   # ― -> —
    '\u2014\u2014\u2014': '\u2014\u2014',  # 三连破折号 -> 双
}


def normalize(s: str):
    for a, b in NORM.items():
        s = s.replace(a, b)
    return s


def main():
    print('=== 1. 归一化新增译文 ===')
    p = os.path.join(PROJ, '语料', '新增译文映射.json')
    src = json.load(open(p, encoding='utf-8'))
    fixed = 0
    out = []
    still_bad = []
    for r in src:
        t = normalize(r['text'])
        try:
            t.encode('gbk')
        except UnicodeEncodeError as e:
            still_bad.append((r['file'], r['offset'], t[:30], str(e)[:60]))
            out.append(r)
            continue
        if t != r['text']:
            fixed += 1
        r2 = dict(r); r2['text'] = t
        out.append(r2)
    print('  译文 %d 条；归一化修正 %d 条' % (len(out), fixed))
    if still_bad:
        print('  ⚠ 仍不可编码 %d 条：' % len(still_bad))
        for x in still_bad[:10]:
            print('     ', x)
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('  已写回', p)

    print()
    print('=== 2. 归一化重编码映射 ===')
    p2 = os.path.join(PROJ, '语料', '重编码映射.json')
    if os.path.exists(p2):
        rec = json.load(open(p2, encoding='utf-8'))
        print('  重编码 %d 条（未改动，仅检查）' % len(rec))
    else:
        print('  [警告] 重编码映射不存在，将不带重编码构建')

    print()
    print('=== 3. 重建 SCRIPT.LPK 并部署 ===')
    cmd = [sys.executable, '-X', 'utf8', os.path.join(PROJ, '工具', 'build_cn.py'), '--with-extra']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '').splitlines()
    for l in tail[-25:]:
        print(' ', l)
    if r.returncode != 0:
        print('构建失败，stderr：')
        print((r.stderr or '')[-2000:])


if __name__ == '__main__':
    main()
