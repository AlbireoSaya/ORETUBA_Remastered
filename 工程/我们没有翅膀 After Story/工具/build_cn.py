# -*- coding: utf-8 -*-
r"""build_cn.py —— 把中文译文回填进 AfterStory 的 172 个剧本，并重打包 SCRIPT.LPK

策略（沿用《我们没有翅膀R》实测结论：**Lucifen 对脚本文本有字节长度硬依赖**）：
  * **等长回填**：逐条把正文的原始 SJIS 字节区间 [off, off+len) 换成 GBK 中文，
    不足者以全角空格（GBK A1A1）补齐，超长者按 GBK 字符边界截断并记账；
  * **人名声明串**：`01 01 <u16 L>` 的内容区间等长覆写为中文名，**末字节必须保持 0x00**（否则名字框出方块）；
  * **只重压改动过的条目**（全量重压会被引擎拒绝）；LPK 输出文件名必须仍是 `SCRIPT.LPK`。

产出：
  构建\脚本_中文\<脚本名>           回填后的 tob 明文
  重打包\SCRIPT.LPK                中文版归档（二进制补丁，未改动条目保留原字节）
  语料\构建报告.json                每脚本改动条数 / 截断清单 / 补齐条数

用法：python build_cn.py [--dry]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, '语料', '原文')
CORPUS = os.path.join(PROJ, '语料')
OUT_TXT = os.path.join(PROJ, '构建', '脚本_中文')
OUT_LPK = os.path.join(PROJ, '重打包')

FULLSP = '　'.encode('gbk')          # A1A1 全角空格
NUL = b'\x00'


def fit_gbk(s, nbytes):
    """把 s 编码成 GBK 并适配到恰好 nbytes 字节（不足补全角空格，超出按字符边界截断）"""
    b = s.encode('gbk')
    if len(b) == nbytes:
        return b, False, False
    if len(b) < nbytes:
        pad = nbytes - len(b)
        if pad % 2:
            b += b' '
            pad -= 1
        return b + FULLSP * (pad // 2), False, False
    # 截断：按 GBK 字符边界回退
    cut = nbytes
    while cut > 0:
        try:
            seg = b[:cut]
            seg.decode('gbk')
            return seg + FULLSP * ((nbytes - cut) // 2) + b' ' * ((nbytes - cut) % 2), True, False
        except UnicodeDecodeError:
            cut -= 1
    return b' ' * nbytes, True, False


def main():
    dry = '--dry' in sys.argv
    tr = json.load(io.open(os.path.join(CORPUS, '译文.json'), encoding='utf-8'))
    lock = json.load(io.open(os.path.join(CORPUS, '译名锁定表.json'), encoding='utf-8'))
    os.makedirs(OUT_TXT, exist_ok=True)
    os.makedirs(OUT_LPK, exist_ok=True)

    # 选择支选项标签（声明串，等长覆写 + 末位 NUL）
    ch = {}
    chp = os.path.join(CORPUS, '选择支补译.json')
    if os.path.exists(chp):
        for r in json.load(io.open(chp, encoding='utf-8')):
            for o in r['options']:
                if o.get('cn'):
                    ch.setdefault(r['file'], []).append(o)

    edits, rep = {}, {}
    for fn, v in tr.items():
        raw = bytearray(io.open(os.path.join(SRC, fn), 'rb').read())
        n_text = n_decl = n_trunc = n_pad = n_skip = n_decl_trunc = 0
        trunc_list = []
        for m in v['messages']:
            cn = (m.get('cn') or '').strip()
            # 1) 人名声明串：等长覆写为中文名，末字节必须保持 NUL（否则名字框出方块）
            dcl = m.get('decl')
            if dcl and m.get('speaker') and m['speaker'] in lock['speakers']:
                doff, dlen = dcl[0], dcl[1]
                cn_name = lock['speakers'][m['speaker']]
                if len(cn_name.encode('gbk')) + 1 > dlen:
                    cn_name = lock.get('speakers_short', {}).get(m['speaker'], cn_name)
                blob = cn_name.encode('gbk')
                if len(blob) + 1 > dlen:
                    blob = blob[:dlen - 1]
                    while blob:
                        try:
                            blob.decode('gbk')
                            break
                        except UnicodeDecodeError:
                            blob = blob[:-1]
                    n_decl_trunc += 1
                pad = dlen - len(blob) - 1
                if pad % 2:
                    new = blob + b' ' + FULLSP * ((pad - 1) // 2) + NUL
                else:
                    new = blob + FULLSP * (pad // 2) + NUL
                if len(new) != dlen:
                    new = blob + b' ' * max(0, dlen - len(blob) - 1) + NUL
                if raw[doff:doff + dlen] != new:
                    raw[doff:doff + dlen] = new
                    n_decl += 1
            # 2) 正文
            off, ln = m.get('off'), m.get('len')
            if not cn or off is None or not ln:
                if m.get('jp'):
                    n_skip += 1
                continue
            blob, cut, _ = fit_gbk(cn, ln)
            if raw[off:off + ln] == blob:
                continue
            raw[off:off + ln] = blob
            n_text += 1
            if cut:
                n_trunc += 1
                trunc_list.append({'file': fn, 'index': m['index'], 'jp_len': ln,
                                   'cn': cn, 'cn_bytes': len(cn.encode('gbk'))})
            elif len(cn.encode('gbk')) < ln:
                n_pad += 1
        # 选择支标签：等长覆写（不足补全角空格，末位 NUL 由 fit 保证）
        n_opt = 0
        for o in ch.get(fn, []):
            blob, cut, _ = fit_gbk(o['cn'], o['len'])
            if raw[o['off']:o['off'] + o['len']] != blob:
                raw[o['off']:o['off'] + o['len']] = blob
                n_opt += 1
        out_p = os.path.join(OUT_TXT, fn)
        if not dry:
            io.open(out_p, 'wb').write(bytes(raw))
        edits[fn] = bytes(raw)
        rep[fn] = {'正文改写': n_text, '人名改写': n_decl, '选支改写': n_opt, '截断': n_trunc,
                   '补齐': n_pad, '人名截断': n_decl_trunc, '跳过': n_skip}
        if n_trunc:
            rep[fn]['截断明细'] = trunc_list[:20]

    tot = {k: sum(v[k] for v in rep.values()) for k in ('正文改写', '人名改写', '截断', '补齐', '人名截断', '跳过')}
    print('=== 回填汇总 ===')
    for k, n in tot.items():
        print('  %-8s %d' % (k, n))
    bad = [fn for fn, r in rep.items() if r['跳过']]
    print('  有跳过条目的脚本: %d 个 %s' % (len(bad), bad[:5]))

    if not dry:
        sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R\工具')
        import lpk_patch as P
        src_lpk = os.path.join(SRC, 'SCRIPT.LPK')
        dst_lpk = os.path.join(OUT_LPK, 'SCRIPT.LPK')
        info = P.patch(src_lpk, dst_lpk, edits)
        print('=== LPK 重打包 ===')
        print('  ', info if not isinstance(info, dict) else
              {k: info[k] for k in list(info)[:8]})
        rep['_LPK'] = {'源': src_lpk, '出': dst_lpk,
                       '出_md5': __import__('hashlib').md5(io.open(dst_lpk, 'rb').read()).hexdigest()}
    io.open(os.path.join(CORPUS, '构建报告.json'), 'w', encoding='utf-8').write(
        json.dumps(rep, ensure_ascii=False, indent=1))
    print('报告：语料\\构建报告.json')


if __name__ == '__main__':
    main()
