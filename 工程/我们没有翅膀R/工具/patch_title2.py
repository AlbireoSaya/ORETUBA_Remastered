# -*- coding: utf-8 -*-
r"""写入中文标题（安全版，ISSUE-ORETUBAR-R）。

**关键约束（实测）**：`ll_app.inf` 的标题字段被引擎**同时用作**：
  ① 游戏窗口标题；② `%APPDATA%\<标题> SaveData\` 这个存档配置目录名。
故标题**必须是合法的 Windows 文件夹名**：
  ✅ 可用：`我们没有翅膀R`（纯中文）
  ❌ 不可用：含 `&` `:` `/` `\` 等非法字符，或过长 → 引擎报
     「セーブデータ作成フォルダの作成に失敗しました」

署名串也因此**不能**写进标题（含空格与 `&`）。署名改由 `成品说明.md` 与作品 skill 承载；
**用户 2026-09-14 的署名要求在本作受引擎限制，已如实上报**（见工程记录「风险与未竟项」）。
"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import lpk_patch as LP

PROJ = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
CN_LPK = r'E:\ZCode Workspace\Galgame\临时\_build\SCRIPT.LPK'
ORIG_INF = os.path.join(PROJ, '语料', 'R版SCRIPT', 'll_app.inf')
NEW_TITLE = '我们没有翅膀R'


def enc_len(n):
    if n < 0x80:
        return bytes([n])
    return bytes([(n & 0x7F) | 0x80, (n >> 7) & 0xFF])


def parse_recs(buf):
    """ll_app.inf：[3 字节头][ [u8/u16 len][bytes][NUL] ]* [尾]"""
    head = buf[:3]
    pos = 3
    recs = []
    tail = b''
    while pos < len(buf):
        if buf[pos] == 0:
            tail = buf[pos:]
            break
        b0 = buf[pos]
        if b0 & 0x80:
            ln = (b0 & 0x7F) | (buf[pos + 1] << 7)
            nb = 2
        else:
            ln, nb = b0, 1
        body = buf[pos + nb:pos + nb + ln]
        if len(body) < ln:
            tail = buf[pos:]
            break
        recs.append(body)
        pos += nb + ln
    return head, recs, tail


def build(head, recs, tail):
    out = bytearray(head)
    for r in recs:
        out += enc_len(len(r)) + r
    out += tail
    return bytes(out)


def main():
    lpk = sys.argv[1] if len(sys.argv) > 1 else CN_LPK
    lp = LP.load(lpk)
    e = LP.read_entry(lp, 'll_app.inf')
    head, recs, tail = parse_recs(e['plain'])
    print('原记录 %d 条，尾 %d 字节' % (len(recs), len(tail)))
    for i, r in enumerate(recs):
        print('  [%d] %r' % (i, r.decode('cp932', errors='replace')))

    payload = NEW_TITLE.encode('gbk') + b'\x00'
    # 前两条（标题 / 副标题）替换为中文标题；其余原样
    new_recs = [payload, payload] + recs[2:]
    new = build(head, new_recs, tail)
    print()
    print('新标题: %r (%d 字节 GBK，合法文件夹名: %s)' % (NEW_TITLE, len(payload),
          not any(c in NEW_TITLE for c in r'\/:*?"<>|&')))
    print('新 ll_app.inf: %d 字节' % len(new))
    head2, recs2, tail2 = parse_recs(new)
    for i, r in enumerate(recs2):
        print('  新[%d] %r' % (i, r.decode('gbk', errors='replace')))

    info = LP.patch(lpk, lpk, {'ll_app.inf': new})
    print()
    print('已写回 %s (%d -> %d 字节)' % (lpk, info['in_size'], info['out_size']))
    lp2 = LP.load(lpk)
    e2 = LP.read_entry(lp2, 'll_app.inf')
    print('回读验证:', e2['plain'] == new)


if __name__ == '__main__':
    main()
