# -*- coding: utf-8 -*-
r"""gen_review_group.py —— 生成"组级"一审派单（每 3 批一组，共 8 组）

说明（须写入工程记录）：`AGENTS.md` §三.2 Step 5 要求"每个核心模块配 1 个 reviewer"。
本工程把**模块粒度定义为"剧情弧段"**（3 批 ≈ 2,400 条 ≈ 一个脚本弧段），故 23 批 = 8 组一审。
每组的 reviewer 独立于该组译者，只读不改。

用法：python gen_review_group.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')
ROOT = r'E:\ZCode Workspace\Galgame'
GROUPS = [(1, 3), (4, 6), (7, 9), (10, 12), (13, 15), (16, 18), (19, 21), (22, 23)]

TPL = '''# 一审派单 · 组 {gi}（批次{a:02d}–{b:02d}，独立审查，只读）

你是本工程的**审查子代理（reviewer）**，独立于这些批次的译者。**只读、不改**：
不得修改任何译文、不得改写 `术语表.md`；只出结论与证据。

## 一、开工必读（第一步：必须用 Read 真读，缺一不可；未读即出结论的审查视为无效）
1. `{root}\\.zcode\\skills\\galgame-translation\\SKILL.md`
2. `{root}\\.zcode\\skills\\galgame-translation\\术语表.md`
3. `{root}\\工程\\我们没有翅膀 After Story\\作品skill\\SKILL.md`
4. `{root}\\工程\\我们没有翅膀 After Story\\作品skill\\术语表.md`（**本作专名/说话人定名的唯一依据**）
5. `{root}\\工程\\我们没有翅膀 After Story\\翻译工作区\\_翻译派单简报.md`
6. `{root}\\工程\\我们没有翅膀 After Story\\语料\\译名锁定表.json`

## 二、审查对象（本组 3 批）
{files}

机器校验结论（主代理已跑，供参考、不替代你的判断）：`{root}\\工程\\我们没有翅膀 After Story\\语料\\校验报告.json`

## 三、审查面（**只审可判定项，不得因题材放水**）
1. **漏译 / 省略 / 除敏**：抓"整条略过、语义残缺、`……` 搪塞、弱化露骨程度、直白改含蓄、删改人称或情节"。
   **发现漏译与除敏一律打回**；成人向内容只要忠实完整即通过，不得要求删改（`AGENTS.md §六`）。
2. **误译**：语义方向错、否定/时态/主客关系译反、双关硬译成错义、专名张冠李戴。
3. **术语一致性**：作品层 §一/§二 命中词必须照表；同一日文词同轨内唯一；敬称按体例 A1
   （姓+くん→○○同学、名字+くん→○○君、さん→语境分层、先輩→前辈）。
4. **标点与排版**：GBK 全角；`「」→“”`、`『』→‘’`；`……`（两个）、`——` 成对；
   **日语 `、` 逐处保留（不得合并为 `，`）**；无半角标点、无全角空格 `　`、无 SJIS 码位标点（〜 ― ・ ─）。
5. **语体**：反翻译腔；角色语气与说话人吻合；无网络烂梗。
6. 允许项（**不得判为错误**）：中文句末 `。` 的增补、`！`/`？` 按中文语气单发增补、
   译者对同一语义的合理措辞选择。

## 四、产出（写到 `{root}\\工程\\我们没有翅膀 After Story\\翻译工作区\\审校_组{gi}.md`）
```
# 一审结论 · 组 {gi}（批次{a:02d}–{b:02d}）
- 结论：通过 / 打回
- 抽检规模：逐条核对了 X 条；抽样 Y 条（写明抽样方式：随机 / 按说话人 / 按场景）
- 覆盖说明：本组 {n} 条，覆盖 i = {i_from}..{i_to}
## 打回项（每条必备证据）
1. i=<全局序号>（file+idx）
   - 原文：… / 译文：… / 问题：漏译｜误译｜术语｜标点｜语体 / 期望：…
## 提示项（不影响通过，建议主代理统一）
## 术语与体例符合性（命中作品层 §一/§二 的词列表 + 是否一致）
- 判据纪律：不要把译者风格选择当错误；不需要逐条重译；但必须覆盖①条数与 `i` 对应②随机 8–10% 逐字核对③所有异常行④所有成人向与拟声段落。
'''


def main():
    for gi, (a, b) in enumerate(GROUPS, 1):
        files, n, i_from, i_to = [], 0, None, None
        for bn in range(a, b + 1):
            src = os.path.join(WD, '批次%02d_原文.json' % bn)
            dst = os.path.join(WD, '批次%02d_译文.json' % bn)
            if not os.path.exists(dst):
                files.append('- 批次%02d：（尚无译文文件）' % bn)
                continue
            lines = json.load(io.open(src, encoding='utf-8'))['lines']
            n += len(lines)
            i_from = lines[0]['i'] if i_from is None else i_from
            i_to = lines[-1]['i']
            files.append('- 批次%02d：原文 `%s` ／译文 `%s`（%d 条，i=%d..%d）'
                         % (bn, src, dst, len(lines), lines[0]['i'], lines[-1]['i']))
        p = os.path.join(WD, '_审校派单_组%d.md' % gi)
        io.open(p, 'w', encoding='utf-8').write(TPL.format(
            gi=gi, a=a, b=b, root=ROOT, files='\n'.join(files), n=n,
            i_from=i_from, i_to=i_to))
        print('已生成 _审校派单_组%d.md（批次%02d–%02d，%d 条）' % (gi, a, b, n))


if __name__ == '__main__':
    main()
