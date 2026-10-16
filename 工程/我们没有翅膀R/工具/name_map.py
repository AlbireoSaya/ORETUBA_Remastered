# -*- coding: utf-8 -*-
r"""角色名中文化表（ISSUE-ORETUBAR-R）。

约束（实测）：名字标签串有**长度硬依赖**，译文 GBK 字节数必须 == 原 SJIS 字节数。
本表给出「日文标签 → 中文名」，由构建器自动补齐到原长（补全角空格）。

证据来源：
  * 主要角色名与读法：《我们没有翅膀》系列官方资料/通行译法（羽田鷹志 / 成田隼人 / 千歳鷲介 /
    渡来明日香 / 玉泉日和子 / 鳳翔 / 小鳩 / 香田亜衣 / 望月紀奈子 / 日野英里子 …）
  * 次要角色与绰号：`工程\我们没有翅膀R\语料\R版迁移映射.json` 中按说话人统计的
    参照汉化（新米汉化组）既有译法
  * 未收录者保持日文显示（已由编码归一转成 GBK，不会再乱码）
"""
import os, re, sys, json

sys.stdout.reconfigure(encoding='utf-8')
P = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC = os.path.join(P, '语料', 'R版SCRIPT')
OUT = os.path.join(P, '语料', '名字中文化.json')

# 日文标签 → 中文名（长度不足时由构建器自动补全角空格）
MAP = {
    # —— 主要角色 ——
    '隼人': '隼人', '鷹志': '鹰志', '鷲介': '鹫介',
    '日和子': '日和子', '明日香': '明日香', '鳴': '鸣', '亜衣': '亚衣',
    '京': '京', '小鳩': '小鸠', '狩男': '狩男', '翔': '翔', '英里子': '英里子',
    '和馬': '和马', '紀奈子': '纪奈子', '蔵人': '藏人', '咲夜': '咲夜', '優': '优',
    'カケル': '翔', '高内': '高内', '可菜': '可菜', '狂夜': '狂夜',
    # —— 幻想要素/组织角色 ——
    'パル': '帕露', 'ガルーダ': '伽鲁炟', '伽楼羅': '伽楼罗', '聖騎士ホーク': '圣骑士霍克',
    'ホーク': '霍克', 'アリス': '爱丽丝', 'バニィＤ': '巴尼Ｄ', 'プラチナ': '普纳奇纳',
    'チケドン': '千夏丼', 'ハリュー': '哈里', 'フェニックス': '菲尼克斯',
    'ファルコン': '法卢空', 'イーグル': '伊格尔', 'ダヴ': '达芙',
    'ＬＲ２００１': 'ＬＲ２００１', 'メンマ': '面魔', '小娘': '丫头', '牧師': '牧师',
    '声': '声', '玉泉': '玉泉',
}

NUL = b'\x00'
FULL = '\u3000'


def fit_name(cn: str, need: int):
    """中文名 → 恰好 need 字节的 GBK，**末字节必须是 0x00（NUL 结尾）**，过长返回 None。

    ⚠️ 历史事故（ISSUE-20260915-06）：旧实现把末字节补成 0x20（半角空格），
    引擎按 NUL 结尾读名字时越读到下一条记录 → 名字框显示 2–3 个方块。
    日文原记录的末字节本就是 NUL，此处必须还原该结构。
    """
    try:
        b = cn.encode('gbk')
    except UnicodeEncodeError:
        return None
    if len(b) > need:
        return None
    pad = need - len(b)
    if pad == 0:
        # 无 NUL 容身之位 ⇒ 记录无法以 NUL 结尾，宁缺毋滥（否则名字框越读方块复发）
        print('  [跳过] %r 恰好吃满 %d 字节、无 NUL 位' % (cn, need))
        return None
    if pad % 2:                       # 奇数差：全角空格后接 NUL
        s = cn + FULL * ((pad - 1) // 2)
    else:                             # 偶数差：全角空格 + 半角空格 + NUL
        s = cn + FULL * ((pad - 2) // 2) + ' '
    b2 = s.encode('gbk') + NUL
    return b2 if len(b2) == need else None


def scan_names():
    """返回 {(file, offset, len): 日文原串}"""
    out = {}
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith('.tob'):
            continue
        raw = open(os.path.join(SRC, fn), 'rb').read()
        for m in re.finditer(rb'\x01\x01', raw):
            i = m.start()
            if i + 4 > len(raw):
                continue
            lo, hi = raw[i + 2], raw[i + 3]
            if hi != 0 or not (2 < lo < 64):
                continue
            boff = i + 4
            if boff + lo > len(raw):
                continue
            core = raw[boff:boff + lo].rstrip(NUL)
            if not (2 <= len(core) <= 62):
                continue
            try:
                s = core.decode('cp932')
            except Exception:
                continue
            if '\\' in s or '.' in s:      # 素材路径，跳过
                continue
            out[(fn, boff, lo)] = s
    return out


def main():
    names = scan_names()
    print('候选声明串: %d' % len(names))
    res = []
    hit = 0
    for (fn, boff, lo), s in names.items():
        if s not in MAP:
            continue
        b = fit_name(MAP[s], lo)
        if b is None:
            print('  [跳过] %-16s %r → %r（%d 字节放不下）' % (fn, s, MAP[s], len(MAP[s].encode('gbk'))))
            continue
        res.append({'file': fn, 'offset': boff, 'len': lo,
                    'text_bytes': list(b), 'src': 'name-cn',
                    'text': b.decode('gbk', errors='replace')})
        hit += 1
    print('命中并转换: %d 条' % hit)
    from collections import Counter
    c = Counter(r['text'].rstrip() for r in res)
    print('涉及角色 %d 种；前 20：' % len(c))
    for k, v in c.most_common(20):
        print('   %-14s %d 条' % (k, v))
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', OUT)


if __name__ == '__main__':
    main()
