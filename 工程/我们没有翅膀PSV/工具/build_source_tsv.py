"""生成《我们没有翅膀》PS Vita 版美咲线的行级原文表（供逐行翻译与对齐）。

输出：工程\\我们没有翅膀PSV\\汉化\\原文\\<脚本>.tsv
列：行序 | 类别 | Task | 说话人ID | 说话人日文 | Voice | 日文原文
  · 类别 = 台词（`:Message`）或 梗概（`:Text`，SceneJumpDialog/MessageSwitch_Tag 用）
  · 说话人日文 = 从 adv.txt 的 [Name] 表按 :Name 的 ID 反查
  · 顺序与脚本内出现顺序一致；**行序是唯一对齐键**，译文表必须逐行同序同数
用法: python build_source_tsv.py
"""
import os
import re

PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV'
SD = os.path.join(PROJ, '脚本解包')
OUT = os.path.join(PROJ, '汉化', '原文')
ADV = os.path.join(PROJ, '素材', '美咲线', 'script', 'adv.txt')


def strip_comments(text):
    out = []
    for line in text.split('\n'):
        q = False
        i = 0
        res = ''
        while i < len(line):
            ch = line[i]
            if ch == '"':
                q = not q
                res += ch
            elif not q and line[i:i + 2] == '//':
                break
            else:
                res += ch
            i += 1
        out.append(res)
    return '\n'.join(out)


TASK = re.compile(r'\[(Task\d+)\]\s*\{', re.M)


def tasks(t):
    res = []
    i = 0
    while True:
        m = TASK.search(t, i)
        if not m:
            break
        j = m.end() - 1
        d = 0
        k = j
        while k < len(t):
            if t[k] == '{':
                d += 1
            elif t[k] == '}':
                d -= 1
                if d == 0:
                    break
            k += 1
        res.append((m.group(1), t[j + 1:k]))
        i = k + 1
    return res


def main():
    adv = open(ADV, 'rb').read().decode('cp932', 'replace')
    i = adv.find('[Name]')
    names = {int(a): b for a, b in re.findall(r':Name(\d+)\s+"([^"]*)",\d+', adv[i:])}

    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(SD) if re.match(r'^(M\d\d_\d\d|P03_01[A-Z])$', f))
    total = 0
    for f in files:
        raw = open(os.path.join(SD, f), 'rb').read().decode('cp932', 'replace')
        t = strip_comments(raw)
        rows = []
        for sec, body in tasks(t):
            m = re.search(r':Tasktype\s+"([^"]+)"', body)
            if not m:
                continue
            tt = m.group(1)
            text = None
            cat = None
            if tt == 'Message':
                mm = re.search(r':Message\s+"(.*?)"', body, re.S)
                if mm:
                    text = mm.group(1)
                    cat = '台词'
            elif tt in ('SceneJumpDialog', 'MessageSwitch_Tag'):
                mm = re.search(r':Text\s+"(.*?)"', body, re.S)
                if mm:
                    text = mm.group(1)
                    cat = '梗概'
            if text is None:
                continue
            nm = re.search(r':Name\s+(\d+)', body)
            vid = re.search(r':Voice\s+(\d+)', body)
            rows.append((sec, cat, nm.group(1) if nm else '',
                         names.get(int(nm.group(1)), '') if nm else '',
                         vid.group(1) if vid else '',
                         text.replace('\r', '').replace('\n', '\\n')))
        with open(os.path.join(OUT, f + '.tsv'), 'w', encoding='utf-8-sig', newline='') as fh:
            fh.write('行序\t类别\tTask\t说话人ID\t说话人日文\tVoice\t日文原文\n')
            for n, r in enumerate(rows, 1):
                fh.write('%d\t%s\t%s\t%s\t%s\t%s\t%s\n' % (n, r[1], r[0], r[2], r[3], r[4], r[5]))
        total += len(rows)
        print('  %-10s %4d 行' % (f, len(rows)))
    print('合计 %d 个脚本 / %d 行' % (len(files), total))


if __name__ == '__main__':
    main()
