"""组装美咲线汉化交付物。

产出（均在 工程\\我们没有翅膀PSV\\汉化\\）：
  台词对照.json / 台词对照.csv   逐行对照（脚本/行序/类别/Task/说话人ID/说话人日/说话人中/Voice/日文/中文）
  剧本全文.md                    按场景分节的可通读中文稿
  场景标题_中文化.tsv             31 个 [StartUp] :SceneName + 4 个 SetSceneName（游戏内显示标题）
  名字表_中文化.tsv               adv.txt [Name] 表中美咲线实际用到的 37 条显示名
"""
import os
import re
import csv
import json

BASE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\汉化'
SRC = os.path.join(BASE, '原文')
DST = os.path.join(BASE, '译文')
SD = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\脚本解包'

# ---- 说话人显示名中文化（作品术语表 §一 定稿）----
SPEAKER_CN = {
    0: '明日香', 1: '日和子', 3: '小鸠', 4: '京', 5: '纪奈子', 10: '高内', 12: '鹰志',
    15: '藏人', 17: '鹫介', 19: '狩男', 21: '咲夜', 30: '翔', 32: '迦楼罗', 42: '声音',
    110: '女学生', 114: '昌子的朋友A', 115: '昌子的朋友B', 137: '男生Ａ', 138: '男生Ｂ',
    142: '翔', 147: '女性顾客', 330: '可怕的声音', 332: '林同学', 334: '高内同学？',
    335: '楼下传来的声音', 336: '二年级男生', 337: '悬疑剧女', 338: '晨间剧女',
    339: '玉袋揉子', 340: '优美的声音', 341: '神秘的声音', 342: '美咲', 343: '死神腔',
    344: '玉袋', 352: '车内广播', 353: '高年级生Ａ', 355: '图书馆职员',
}

# ---- 场景 / 章节标题中文化（主代理定译）----
SCENE_TITLE_CN = {
    'M01_01': '承前 ～此前皆为序章～', 'M01_02': '鹫介与美咲', 'M01_03': '守望着亚历山大的鹫介',
    'M01_04': '鹫介与明日香', 'M02_01': '鹰志与小鸠', 'M02_02': '鹰志与明日香',
    'M02_03': '鹰志与京', 'M02_04': '放学后的邀约', 'M02_05': '昌子的原点',
    'M02_06': '鹰志与美咲', 'M02_07': '鹫介再临', 'M02_08': '小丑的失败',
    'M03_01': '明日香缺席', 'M03_02': '额外的遗留事务处理', 'M04_01': '藏人也缺席',
    'M04_02': '天台午餐', 'M04_03': '促成林同学的恋情', 'M05_01': '周日出游',
    'M05_02': '初次约会', 'M06_01': '再见了高内同学', 'M06_02': '鹰志与咲夜',
    'M06_03': '冬之风暴', 'M07_01': '濒死的伊库鲁尔', 'M07_02': '苏醒的贤者王',
    'M08_01': '失恋的伊库鲁尔', 'M09_01': '终章 ～林田同学与我～',
    'M09_02': '解缆 ～对决羽田鹰志～',
    'P03_01A': '幸福的小美咲', 'P03_01B': '别认输，小美咲',
    'P03_01C': '烦恼的小美咲', 'P03_01D': '苏醒的小美咲',
}
SETSCENE_TITLE_CN = {
    'P03_01A': '幸福的小美咲', 'P03_01B': '别认输，小美咲',
    'P03_01C': '烦恼的小美咲', 'P03_01D': '苏醒的小美咲',
}

SRC_FILES = ['M01_01', 'M01_02', 'M01_03', 'M01_04', 'M02_01', 'M02_02', 'M02_03', 'M02_04',
             'M02_05', 'M02_06', 'M02_07', 'M02_08', 'M03_01', 'M03_02', 'M04_01', 'M04_02',
             'M04_03', 'M05_01', 'M05_02', 'M06_01', 'M06_02', 'M06_03', 'M07_01', 'M07_02',
             'M08_01', 'M09_01', 'M09_02', 'P03_01A', 'P03_01B', 'P03_01C', 'P03_01D']


def read_tsv(p):
    with open(p, encoding='utf-8-sig') as fh:
        rows = [l.rstrip('\n').split('\t') for l in fh]
    return rows[1:]


def main():
    recs = []
    for f in SRC_FILES:
        src = read_tsv(os.path.join(SRC, f + '.tsv'))
        dst = read_tsv(os.path.join(DST, f + '.tsv'))
        assert len(src) == len(dst), (f, len(src), len(dst))
        for a, b in zip(src, dst):
            sid = a[3]
            recs.append({
                '脚本': f, '行序': int(a[0]), '类别': a[1], 'Task': a[2],
                '说话人ID': int(sid) if sid else None,
                '说话人日文': a[4],
                '说话人中文': SPEAKER_CN.get(int(sid)) if sid else None,
                'Voice': int(a[5]) if a[5] else None,
                '日文': a[6].replace('\\n', '\n'),
                '中文': b[7].replace('\\n', '\n'),
            })
    print('对照记录数:', len(recs))

    with open(os.path.join(BASE, '台词对照.json'), 'w', encoding='utf-8') as fh:
        json.dump(recs, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, '台词对照.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0]), delimiter='\t')
        w.writeheader()
        for r in recs:
            w.writerow(r)

    # 剧本全文
    with open(os.path.join(BASE, '剧本全文.md'), 'w', encoding='utf-8') as fh:
        fh.write('# 《我们没有翅膀》PS Vita 版 · 林田美咲线 剧本全文（中文）\n\n')
        fh.write('> 译文：本项目自行翻译（未使用新米汉化组的剧情译文）。人名/地名按新米汉化写法（用户指令）。\n')
        fh.write('> 分行与原文一一对应；`——` 为原文破折号，`“”` 对应原文 `「」`。\n\n')
        for f in SRC_FILES:
            fh.write('\n## %s　%s\n\n' % (f, SCENE_TITLE_CN.get(f, '')))
            for r in [x for x in recs if x['脚本'] == f]:
                sp = r['说话人中文'] or ''
                if r['类别'] == '梗概':
                    fh.write('> *[梗概]* %s\n\n' % r['中文'])
                elif sp:
                    fh.write('**%s**：%s\n\n' % (sp, r['中文']))
                else:
                    fh.write('%s\n\n' % r['中文'])

    # 场景标题
    with open(os.path.join(BASE, '场景标题_中文化.tsv'), 'w', encoding='utf-8-sig', newline='') as fh:
        fh.write('脚本\t字段\t场景名日文\t场景名中文\n')
        for f in SRC_FILES:
            t = open(os.path.join(SD, f), 'rb').read().decode('cp932', 'replace')
            m = re.search(r'\[StartUp\][^{]*\{[^}]*?:SceneName\s+"([^"]+)"', t, re.S)
            if m:
                fh.write('%s\t[StartUp] :SceneName\t%s\t%s\n' % (f, m.group(1), SCENE_TITLE_CN.get(f, '')))
            for mm in re.finditer(r':Tasktype\s+"SetSceneName"[^}]*?:SceneName\s+"([^"]+)"', t, re.S):
                fh.write('%s\tSetSceneName\t%s\t%s\n' % (f, mm.group(1), SETSCENE_TITLE_CN.get(f, '')))

    # 名字表
    used = sorted({r['说话人ID'] for r in recs if r['说话人ID'] is not None})
    adv = open(os.path.join(BASE, '..', '素材', '美咲线', 'script', 'adv.txt'), 'rb').read().decode('cp932', 'replace')
    i = adv.find('[Name]')
    names = {int(a): b for a, b in re.findall(r':Name(\d+)\s+"([^"]*)",\d+', adv[i:])}
    with open(os.path.join(BASE, '名字表_中文化.tsv'), 'w', encoding='utf-8-sig', newline='') as fh:
        fh.write('编号\t显示名日文\t显示名中文\t美咲线引用次数\n')
        cnt = {}
        for r in recs:
            if r['说话人ID'] is not None:
                cnt[r['说话人ID']] = cnt.get(r['说话人ID'], 0) + 1
        for n in used:
            fh.write('%d\t%s\t%s\t%d\n' % (n, names.get(n, ''), SPEAKER_CN.get(n, '（待译）'), cnt.get(n, 0)))
    print('名字表条目:', len(used), '/ 场景标题表已写出')
    print('台词数:', sum(1 for r in recs if r['类别'] == '台词'), '梗概数:', sum(1 for r in recs if r['类别'] == '梗概'))


if __name__ == '__main__':
    main()
