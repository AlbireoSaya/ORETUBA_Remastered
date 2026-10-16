# -*- coding: utf-8 -*-
r"""写入中文标题 + 署名（AGENTS.md §六）。

本作窗口标题取自 `SCRIPT.LPK` 内 `ll_app.inf`。实测结构（101 字节）：
```
[0x00..0x04)  头部 4 字节（含作品 ID：01 00 00 13）
[0x04..)      记录序列：[u8 len][bytes][0x00]，len = 字节数 + 1（含结尾 NUL）
              记录 0：标题          记录 1：标题（副）
              记录 2：Copyright (C) 2011 Navel
              记录 3：官方网址
              记录 4：00 00（尾）
```
本脚本把记录 0/1 替换为「中文标题 + 署名串」，其余记录原样保留。
署名串（用户 2026-09-14 定规，GBK 可编码）不省略、不改写。
"""
import os, sys, re

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
CN_LPK = r'E:\ZCode Workspace\Galgame\临时\_build\SCRIPT.LPK'
SIGN = '来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode'
TITLE = '我们没有翅膀R'


def enc_len(n: int) -> bytes:
    """长度前缀编码：< 0x80 用 1 字节；>= 0x80 用 2 字节（次字节最高位置 1 作标志）。"""
    if n < 0x80:
        return bytes([n])
    return bytes([(n & 0x7F) | 0x80, (n >> 7) & 0xFF])


def dec_len(buf: bytes, pos: int):
    """返回 (长度值, 前缀字节数)。首字节 >= 0x80 表示两字节形式。"""
    b0 = buf[pos]
    if b0 & 0x80:
        return ((b0 & 0x7F) | (buf[pos + 1] << 7)), 2
    return b0, 1


def build_inf(orig: bytes, new_title: str) -> bytes:
    # 解析记录
    head = orig[:3]   # 实测头部为 3 字节（01 00 00），第 4 字节起就是首条记录的长度字节
    pos = 3
    recs = []
    while pos < len(orig):
        if orig[pos] == 0:
            recs.append(('raw', orig[pos:]))
            break
        ln, nb = dec_len(orig, pos)
        body = orig[pos + nb:pos + nb + ln]
        if len(body) < ln:
            recs.append(('raw', orig[pos:]))
            break
        recs.append(('s', body))          # body 含结尾 NUL
        pos += nb + ln
    # 替换前两条（标题）
    payload = new_title.encode('gbk') + b'\x00'
    out = bytearray(head)
    replaced = 0
    for kind, val in recs:
        if kind == 's' and replaced < 2:
            out += enc_len(len(payload)) + payload
            replaced += 1
        elif kind == 's':
            out += enc_len(len(val)) + val
        else:
            out += val
    return bytes(out)


def main():
    lpk = sys.argv[1] if len(sys.argv) > 1 else CN_LPK
    out = sys.argv[2] if len(sys.argv) > 2 else lpk
    lp = LP.load(lpk)
    e = LP.read_entry(lp, 'll_app.inf')
    orig = e['plain']
    print('原 ll_app.inf: %d 字节' % len(orig))
    new_title = TITLE + ' ' + SIGN
    print('新标题串 (%d 字节 GBK): %s' % (len(new_title.encode('gbk')), new_title))
    new = build_inf(orig, new_title)
    print('新 ll_app.inf: %d 字节' % len(new))
    # 校验
    recs = re.findall(rb'[\x20-\x7e]{4,}', new)
    for r in recs:
        print('  保留记录:', r.decode('ascii'))
    if new == orig:
        print('[警告] 未发生改动')
    info = LP.patch(lpk, out, {'ll_app.inf': new})
    print('已写回: %s (%d -> %d 字节)' % (out, info['in_size'], info['out_size']))
    # 回读验证
    lp2 = LP.load(out)
    e2 = LP.read_entry(lp2, 'll_app.inf')
    print('回读验证:', e2['plain'] == new)


if __name__ == '__main__':
    main()
