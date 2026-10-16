# -*- coding: utf-8 -*-
r"""ref_extract_bytes.py —— 参照汉化（新米汉化组 v3.1，原版 2009）SOB 的**字节级零损失**提取器
（ISSUE-ORETUBAR-R · 译文迁移模块 · v2）

为什么必须字节级
================
`参照\汉化文本.json`（旧产物）用 SJIS 解码抓取，而参照汉化里的**中文正文是 GBK 字节**，
SJIS 解不出的字节被 `errors='replace'` 换成了 U+FFFD —— **信息不可逆丢失**，不可用于迁移。
`参照\原版汉化SCRIPT_CHS\*.sob` 原始文件字节完好，本脚本只碰它。

SOB 文本区结构（实测，v2 版核心发现）
====================================
v1 只按 `#<meta>$&<body>$` 抓「有说话人的台词」，**漏掉了全部旁白** —— 旁白记录没有 `#` 前缀。
实测真实结构：

    <正文原始字节> $ \x00 <\x00> <u16 序号>   ← 日文原稿区（文件序 = 显示序倒序）
    <正文原始字节> $ \x00*8                   ← 中文译文区（文件序 = 显示序正序）
    （台词记录另有 `#<说话人>[\<语音ID>]$&` 前缀，日文/中文两侧同形）

* 正文内**不可能出现 0x00 与 0x24(`$`)**（SJIS/GBK 的双字节 trail 都不含这两值），
  因此以 `$\x00` 为记录终止符、向前回溯到最近的 0x00/0x24 即得正文起点；
* 记录表整体分**两半**：前 `N//2` 条 = 2009 原版**日文**（含旁白），后 `N//2` 条 = **中文译文**；
* 两半等长且镜像：**显示序上 `前半[i]` ↔ `后半[N-1-i]` 是同一句**（实测 s01_01a：52+52，
  语音 ID 逐条对齐；全库校验见 build_migration_map.py 报告）。

本脚本做什么
============
1. 提取**全部**文本记录（旁白 + 台词），meta 与 body 均保留原始字节；
2. JSON 用 `latin-1` **逐字节无损打包**（byte↔char 一一对应），`s.encode('latin-1')` 即可还原；
3. 另给两个人读视图（不参与匹配）：`jp_view`（body 按 CP932 解）、`cn_view`（body 按 GBK 解）；
   不可解字节渲染成 `\xNN` 字面量（自定义错误处理器 `lu_hex`），**不产生 U+FFFD**；
4. 逐记录自检 `file[start:body_start] == head_b`、`file[body_start:end] == body_b`、
   `file[end:end+2] == b'$\x00'`，并记录每个源文件的 MD5。

用法
====
    python -X utf8 ref_extract_bytes.py            # 提取并写 参照\原版汉化_逐槽字节.json
    python -X utf8 ref_extract_bytes.py --quiet
"""
import codecs
import collections
import hashlib
import json
import os
import re
import sys

PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC = os.path.join(PROJ, '参照', '原版汉化SCRIPT_CHS')
DST = os.path.join(PROJ, '参照', '原版汉化_逐槽字节.json')

TERM = re.compile(rb'\x24\x00')          # 记录终止符：'$' + NUL
RUN = re.compile(rb'[\x20-\x7e\x80-\xfc]{2,160}')
KANA_FW = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
MAX_BODY = 1200                          # 单条正文长度上限（回溯保护）
MAX_META = 64                            # 说话人/语音 ID 字段长度上限


# ---------------------------------------------------------------- 无损视图
def _lu_hex_handler(exc):
    """解码错误处理器：把不可解字节写成 \\xNN 字面量（每步前进 1 字节）。"""
    if isinstance(exc, UnicodeDecodeError):
        return ('\\x%02x' % exc.object[exc.start], exc.start + 1)
    raise exc


codecs.register_error('lu_hex', _lu_hex_handler)


def view(b: bytes, enc: str) -> str:
    return b.decode(enc, 'lu_hex')


def dec(b: bytes, enc: str):
    """严格解码；失败返回 None（绝不用 errors='replace'）。"""
    try:
        return b.decode(enc)
    except Exception:
        return None


def pack(b: bytes) -> str:
    """逐字节无损打包：任意 bytes → 全部落在 U+0000–U+00FF 的 str。"""
    return b.decode('latin-1')


def unpack(s: str) -> bytes:
    return s.encode('latin-1')


# ---------------------------------------------------------------- 提取
def split_meta(meta: bytes):
    """meta = <说话人>[\\<语音ID>]；旁白记录 meta 为空。"""
    if b'\\' in meta:
        sp, vo = meta.split(b'\\', 1)
        return sp, vo
    return meta, b''


def records_of_bytes(data: bytes, fname: str = ''):
    """按 `$\x00` 终止符提取全部文本记录。返回 (records, stats)。

    记录框架（实测）：
      * 日文原稿区：`<body>$` `\x00\x00<u16 序号>` ↔ 下一记录
      * 中文译文区：`<body>$` `\x00*8`              ↔ 下一记录
      * 台词记录另有 `#<说话人>[\\<语音ID>]$&` 前缀
    正文内不可能出现 0x00 / 0x24，故以 `$\x00` 为锚向前回溯；回溯停止点若是单枚 0x00，
    即命中 u16 序号的高字节；若是 `\x00\x00`（两枚）则序号在其后 2 字节，需跳过。
    """
    scene = os.path.splitext(os.path.basename(fname))[0] if fname else ''
    out = []
    st = {'skipped': 0, 'u16_skip': 0, 'sep_skip': 0, 'ctl_trim': 0}
    for m in TERM.finditer(data):
        t = m.start()                       # 终止符 '$' 位置
        if t + 1 >= len(data) or data[t + 1] != 0x00:
            st['skipped'] += 1
            continue
        # 1) 向前回溯到最近的 0x00 / 0x24（正文内不可能出现这两值）
        s = t
        while s > 0 and data[s - 1] not in (0x00, 0x24) and (t - s) < MAX_BODY + 8:
            s -= 1
        if t - s > MAX_BODY:
            st['skipped'] += 1
            continue
        p = s - 1
        if p >= 0 and data[p] == 0x24:
            # 2a) 台词记录：跳过 `($&)+` 分隔符
            while s < t and data[s] == 0x26 and s >= 1 and data[s - 1] == 0x24:
                s += 1
                st['sep_skip'] += 1
        elif p >= 0 and data[p] == 0x00:
            # 2b) 数终止点前的 NUL 连写长度：恰为 2 ⇒ 其后 2 字节是 u16 序号，跳过
            r = 0
            q = p
            while q >= 0 and data[q] == 0x00:
                r += 1
                q -= 1
            if r == 2:
                s += 2
                st['u16_skip'] += 1
        # 3) 兜底：正文不会以控制字节开头
        while s < t and data[s] < 0x20:
            s += 1
            st['ctl_trim'] += 1
        body = data[s:t]
        if not body:
            st['skipped'] += 1
            continue
        if any(b < 0x20 for b in body):
            st['skipped'] += 1
            continue
        # 4) 说话人 / 语音 ID（仅台词记录）
        meta = b''
        rec_start = s
        e = s
        while e >= 2 and data[e - 2] == 0x24 and data[e - 1] == 0x26:
            e -= 2
        if e < s:
            k = e - 1
            while k > 0 and data[k] not in (0x00, 0x24, 0x23) and (e - k) <= MAX_META:
                k -= 1
            if data[k:k + 1] == b'#' and (e - k) <= MAX_META:
                rec_start = k
                meta = data[k + 1:e]
        sp, vo = split_meta(meta)
        tail = data[t + 1:t + 9]
        seq = int.from_bytes(tail[2:4], 'little') if tail[0:2] == b'\x00\x00' else None
        out.append({
            'file': os.path.basename(fname) if fname else '',
            'scene': scene,
            'index': len(out),
            'offset': rec_start,            # 记录起点（含 `#meta$&` 前缀 / u16 序号）
            'body_offset': s,
            'end': t,
            'len': t - rec_start,           # 不含终止符 `$`
            'head_b': pack(data[rec_start:s]),
            'meta_b': pack(meta),
            'speaker_b': pack(sp),
            'voice_b': pack(vo),
            'body_b': pack(body),
            'body_len': len(body),
            'tail_b': pack(tail),
            'seq': seq,
            'jp_view': view(body, 'cp932'),
            'cn_view': view(body, 'gbk'),
            'has_meta': bool(meta),
            'rec_md5': hashlib.md5(data[rec_start:t + 2]).hexdigest(),
        })
    return out, st


def records_of_file(path: str):
    with open(path, 'rb') as fp:
        data = fp.read()
    return records_of_bytes(data, path)


# ---------------------------------------------------------------- 次级：NUL 终止串
def title_strings_of_bytes(data: bytes, fname: str = ''):
    """次级扫描：**NUL 终止串** —— 只取「像章节标题」的那部分文本。

    实测 `s00_00.sob`：`<SJIS 标题>\\x00…\\x00<GBK 标题>\\x00…` —— 标题以 NUL 分界、
    无 `$` 终止符，故主记录扫描（`$\\x00` 驱动）抓不到。标题都很短，故限长 ≤ 80 字节
    且要求 ≥2 个假名（JP）／≥2 个汉字（CN），把二进制区的假命中压下去。
    """
    scene = os.path.splitext(os.path.basename(fname))[0] if fname else ''
    out = []
    for m in RUN.finditer(data):
        s = m.group(0)
        if len(s) > 80:
            continue
        if m.start() and data[m.start() - 1] != 0x00:
            continue
        if m.end() < len(data) and data[m.end()] != 0x00:
            continue
        jp = dec(s, 'cp932')
        cn = dec(s, 'gbk')
        if jp and len(KANA_FW.findall(jp)) >= 2:
            kind = 'JP'
        elif cn and len(HAN.findall(cn)) >= 2 and not KANA_FW.search(cn):
            kind = 'CN'
        else:
            continue
        out.append({
            'file': os.path.basename(fname) if fname else '',
            'scene': scene,
            'offset': m.start(),
            'len': len(s),
            'kind': kind,
            'bytes_b': pack(s),
            'text': jp if kind == 'JP' else cn,
        })
    return out


# ---------------------------------------------------------------- 主流程
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    quiet = '--quiet' in sys.argv
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.sob'))
    rows = []
    strs = []
    file_md5 = {}
    selfcheck_bad = []
    n_skip = 0
    esc_jp = esc_cn = 0
    nbytes = 0
    odd_files = []
    skip_detail = collections.Counter()
    for f in files:
        p = os.path.join(SRC, f)
        with open(p, 'rb') as fp:
            data = fp.read()
        file_md5[f] = hashlib.md5(data).hexdigest()
        recs, sk = records_of_bytes(data, f)
        skip_detail.update(sk)
        n_skip += sk['skipped']
        strs.extend(title_strings_of_bytes(data, f))
        if len(recs) % 2:
            odd_files.append((f, len(recs)))
        for r in recs:
            # 零损失自检
            if (data[r['offset']:r['body_offset']] != unpack(r['head_b'])
                    or data[r['body_offset']:r['end']] != unpack(r['body_b'])
                    or data[r['end']:r['end'] + 2] != b'$\x00'):
                selfcheck_bad.append((f, r['index']))
            esc_jp += r['jp_view'].count('\\x')
            esc_cn += r['cn_view'].count('\\x')
            nbytes += r['body_len']
            rows.append(r)

    with open(DST, 'w', encoding='utf-8') as fp:
        json.dump({
            'source_dir': SRC,
            'source_file_md5': file_md5,
            'slot_count': len(rows),
            'title_string_count': len(strs),
            'body_bytes_total': nbytes,
            'layout': {
                'record': '<head_b><body_b>$\\x00<tail_b>',
                'halves': '前 N//2 条 = 日文原稿（文件序=显示序倒序）；后 N//2 条 = 中文译文（文件序=显示序正序）',
                'pairing': '显示序 前半[i] ↔ 后半[N-1-i]',
            },
            'pack': 'latin-1 (byte<->char 1:1)',
            'views': {'jp_view': 'body 按 cp932 解', 'cn_view': 'body 按 gbk 解',
                      'escape': r'不可解字节渲染为 \xNN（非 U+FFFD）'},
            'odd_record_files': odd_files,
            'skipped_terminators': n_skip,
            'skip_detail': dict(skip_detail),
            'slots': rows,
        }, fp, ensure_ascii=False)
    if not quiet:
        half_ok = sum(1 for f in files if len([r for r in rows if r['file'] == f]) % 2 == 0)
        print('源目录: %s' % SRC)
        print('文件数: %d   文本记录总数: %d   正文字节总数: %d' % (len(files), len(rows), nbytes))
        print('次级 NUL 终止串（章节标题候选，供 build_migration_map.py 按需重扫）: %d 条' % len(strs))
        print('零损失自检（head/body/终止符重构）: %s'
              % ('全部通过' if not selfcheck_bad else '%d 处失败 %s' % (len(selfcheck_bad), selfcheck_bad[:5])))
        print('两半等长（偶数记录）的文件: %d / %d ；奇数文件: %d 个' % (half_ok, len(files), len(odd_files)))
        print('记录解析计数: %s' % dict(skip_detail))
        print(r'视图转义计数: jp_view \xNN × %d ；cn_view \xNN × %d' % (esc_jp, esc_cn))
        print('输出: %s (%.1f MB)' % (DST, os.path.getsize(DST) / 1048576.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
