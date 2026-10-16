# -*- coding: utf-8 -*-
r"""等长汉化构建（ISSUE-ORETUBAR-R）。

**背景（实测确诊）**：本作引擎对脚本内文本存在**长度硬依赖**——
某场景标题（`アスカと王宮騎士団`，30 字节）译成 22 字节后，
「选择任意选项 → 退回标题界面」。而**补齐到 30 字节**后一切正常。
⇒ 修复方案：**全部译文补齐到与原字节数完全一致**。

规则：
  * GBK 字节数 < 原长  → 末尾补**全角空格**（U+3000，2 字节）直至恰好等于原长；
    若差 1 字节，补一个半角空格。
  * GBK 字节数 > 原长  → 在 GBK 字符边界上截断至 ≤ 原长，再补齐（**记录到清单**）。
  * 结果与原文长度完全一致 ⇒ **无需任何地址重定位**（零风险写回）。

用法：
  python -X utf8 build_padded.py [--deploy] [--out PATH]
"""
import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

WS = r'E:\ZCode Workspace\Galgame'
P = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP', 'SCRIPT.LPK')
OUT = os.path.join(WS, '临时', '_padded', 'SCRIPT.LPK')
# 现行游戏实体目录（ISSUE-20260915-06 修正：旧路径 WS\ORETSUBA_R\ORETSUBA_R 已不存在，
# 误用会让 --deploy「假部署」到无人使用的位置；成品目录经 junction 指向此处）
DEPLOY = os.path.join(WS, '_game_ascii', 'ORETSUBA_R', 'SCRIPT.LPK')
DEPLOY_GAME = os.path.join(WS, '_game_ascii', 'ORETSUBA_R')
REPORT = os.path.join(P, '语料', '等长补齐_截断清单.json')

FULL = '\u3000'

# GBK 不可编码字符 → GB2312 等价字符（ISSUE-20260915-06 / bug B）。
# 此前构建对这类译文**静默跳过**，原始 SJIS 字节留在 LPK 里 → 游戏内显示为乱码
# （实测 39 条：・≪≫♪）。此处统一回退，与 recode_safe.py / recode_names.py 的回退表一致。
FALLBACK = {
    '\u226a': '\u300a',   # ≪ → 《
    '\u226b': '\u300b',   # ≫ → 》
    '\u30fb': '\u00b7',   # ・ → ·
    '\u266a': '\u2606',   # ♪ → ☆
    '\u301c': '\uff5e',   # 〜 → ～
    '\u2015': '\u2014',   # ― → —
}
SUBST = {}
UNKNOWN = {}


def gbk_norm(text: str) -> str:
    """把 GBK 不可编码字符替换为等价 GBK 字符；替换明细记入 SUBST（未知者记入 UNKNOWN）。"""
    for ch in text:
        try:
            ch.encode('gbk')
        except UnicodeEncodeError:
            out = []
            for c in text:
                try:
                    c.encode('gbk')
                    out.append(c)
                except UnicodeEncodeError:
                    if c in FALLBACK:
                        r = FALLBACK[c]
                        SUBST[c] = SUBST.get(c, 0) + 1
                    else:
                        r = '?'
                        UNKNOWN[c] = UNKNOWN.get(c, 0) + 1
                    out.append(r)
            return ''.join(out)
    return text


def fit(text: str, need: int):
    """把 text 变成 GBK 字节数恰好为 need 的字节串。返回 (bytes, 状态)。"""
    text = gbk_norm(text)
    try:
        b = text.encode('gbk')
    except UnicodeEncodeError:
        return None, 'gbk不可编码'
    if len(b) == need:
        return b, 'equal'
    if len(b) < need:
        pad = need - len(b)
        s = text + FULL * (pad // 2)
        if pad % 2:
            s += ' '
        b2 = s.encode('gbk')
        if len(b2) != need:
            return None, '补齐失败(%d)' % len(b2)
        return b2, 'padded'
    # 偏长：按字符边界截断
    out = []
    n = 0
    for ch in text:
        cb = ch.encode('gbk')
        if n + len(cb) > need:
            break
        out.append(cb)
        n += len(cb)
    b3 = b''.join(out)
    if len(b3) < need:
        pad = need - len(b3)
        b3 += (FULL * (pad // 2)).encode('gbk')
        if pad % 2:
            b3 += b' '
    return b3, 'truncated'


def main():
    deploy = '--deploy' in sys.argv
    out_lpk = OUT
    if '--out' in sys.argv:
        out_lpk = sys.argv[sys.argv.index('--out') + 1]

    mig = json.load(open(os.path.join(P, '语料', 'R版迁移映射.json'), encoding='utf-8'))
    new = json.load(open(os.path.join(P, '语料', '新增译文映射.json'), encoding='utf-8'))
    rec = json.load(open(os.path.join(P, '语料', '重编码映射.json'), encoding='utf-8'))

    by = {}
    stat = {'equal': 0, 'padded': 0, 'truncated': 0}
    trunc_list = []
    bad = 0
    for r in mig + new:
        f = r['file']
        t = r.get('cn') or r.get('text') or ''
        if not t:
            continue
        need = int(r['len'])
        b, how = fit(t, need)
        if b is None:
            bad += 1
            continue
        stat[how] = stat.get(how, 0) + 1
        if how == 'truncated':
            trunc_list.append({'file': f, 'offset': int(r['offset']), 'need': need,
                               'cn': t, 'kept': b.decode('gbk', errors='replace')})
        by.setdefault(f, []).append({'offset': int(r['offset']), 'len': need, 'text_bytes': b})
    # 重编码本身即等长
    for r in rec:
        f = r['file']
        tb = r.get('text_bytes')
        b = bytes(tb) if isinstance(tb, list) else r.get('text_bytes_latin1', '').encode('latin-1')
        by.setdefault(f, []).append({'offset': int(r['offset']), 'len': int(r['len']), 'text_bytes': b})
        stat['equal'] += 1

    print('等长 %d / 补齐 %d / 截断 %d；不可编码 %d'
          % (stat['equal'], stat['padded'], stat['truncated'], bad))
    if SUBST:
        print('GBK 回退替换:', {'\\u%04x' % ord(k): v for k, v in SUBST.items()})
    if UNKNOWN:
        print('!! 警告：以下字符不在回退表，已降级为 ?（需补入 FALLBACK 并重译检查）:',
              {'\\u%04x' % ord(k): v for k, v in UNKNOWN.items()})
    print('涉及文件 %d' % len(by))
    json.dump(trunc_list, open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('截断清单: %s (%d 条)' % (REPORT, len(trunc_list)))

    lpm = LP.load(MEDIA)
    edits = {}
    delta_nonzero = 0
    out_of_range = 0
    for f, lst in by.items():
        raw = LP.read_entry(lpm, f)['plain']
        buf = bytearray(raw)
        for e in lst:
            off, ln, nb = e['offset'], e['len'], e['text_bytes']
            if off + ln > len(buf):
                out_of_range += 1
                continue
            if len(nb) != ln:
                delta_nonzero += 1
                continue
            buf[off:off + ln] = nb
        newb = bytes(buf)
        if newb != raw:
            edits[f] = newb
    print('长度不符被跳过: %d 条；越界被跳过: %d 条' % (delta_nonzero, out_of_range))
    print('需替换条目: %d（**全部等长 ⇒ 零重定位**）' % len(edits))
    os.makedirs(os.path.dirname(out_lpk), exist_ok=True)
    info = LP.patch(MEDIA, out_lpk, edits)
    print('LPK: %d -> %d' % (info['in_size'], info['out_size']))
    import subprocess
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'patch_title2.py'), out_lpk],
                   capture_output=True)
    print('输出:', out_lpk, os.path.getsize(out_lpk))
    if deploy:
        import shutil, hashlib
        shutil.copy2(out_lpk, DEPLOY)
        h1 = hashlib.md5(open(out_lpk, 'rb').read()).hexdigest()
        h2 = hashlib.md5(open(DEPLOY, 'rb').read()).hexdigest()
        print('已部署到', DEPLOY)
        print('部署校验 md5: %s %s' % (h1, 'OK' if h1 == h2 else '!!不符!!'))


if __name__ == '__main__':
    main()
