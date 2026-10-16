# -*- coding: utf-8 -*-
r"""gen_trim_batches.py —— 为「等长截断 811 条」生成专项重译批次与派单

背景：Lucifen 对脚本文本有**字节长度硬依赖**（R 版实测：变长译文→选择支失效）。
`build_cn.py` 对超出原字节长度的译文按 GBK 边界截断 → 归档内中文不完整。
本任务要求：**不超原长重译**（GBK 字节数 ≤ 原文字节数），语义与术语不得损失。

产出：
  翻译工作区\精简批次<k>_输入.json   [{file, idx, kind, spk, budget, jp, cur}]
  （子代理产出）翻译工作区\精简批次<k>_输出.json  [{file, idx, cn}]
用法：python gen_trim_batches.py [批数=5]
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WD = os.path.join(PROJ, '翻译工作区')

TPL = '''# 专项派单 · 等长截断重译（精简批次{no}/{total}，{n} 条）

你是《我们没有翅膀 After Story》剧情汉化工程的**重译（精简）子代理**。

## 一、开工必读（第一步：必须用 Read 真读，缺一不可）
1. `{root}\\.zcode\\skills\\galgame-translation\\SKILL.md`
2. `{root}\\.zcode\\skills\\galgame-translation\\术语表.md`
3. `{root}\\工程\\我们没有翅膀 After Story\\作品skill\\SKILL.md`
4. `{root}\\工程\\我们没有翅膀 After Story\\作品skill\\术语表.md`
5. `{root}\\工程\\我们没有翅膀 After Story\\翻译工作区\\_翻译派单简报.md`
6. `{root}\\工程\\我们没有翅膀 After Story\\语料\\译名锁定表.json`

## 二、任务
输入：`{root}\\工程\\我们没有翅膀 After Story\\翻译工作区\\精简批次{no}_输入.json`（{n} 条）
输出：`{root}\\工程\\我们没有翅膀 After Story\\翻译工作区\\精简批次{no}_输出.json`
格式：`[{{"file": "11_1a.tob", "idx": 3, "cn": "……"}}, ...]`（条数与顺序与输入完全一致）

**每条的目标**：把现有译文改写为 **GBK 字节数 ≤ `budget`**（= 原文 SJIS 字节数）。
字段：`budget` 允许字节数、`jp` 日文原文、`cur` 现有译文（超长）、`over` 超出字节数。

## 三、硬约束（违反即打回）
1. **不超原长**：`len(cn.encode('gbk')) <= budget`，逐条必须成立（这是引擎的结构约束，不可放宽）。
2. **不得丢信息**：不得删句、不得省略、不得把直白改含蓄、不得除敏；只允许
   **压缩措辞 / 删减可省标点 / 合并虚词**——语义必须与 `jp` 一致。
3. **优先压缩手段（按此顺序）**：
   ① 删可省的拖音与重复标点（`——`→`—`？**不行**——见下；应删整组可省的 `——`/`～`/`…`）；
   ② 去掉可省的语气词（「真是的」「那个」「那个嘛」之类）；
   ③ 用更短的等价词（「今天早上真不错」→「早上真好」）；
   ④ 合并短句、去掉可省的「、」；
   ⑤ 最后才动实词，且必须保住原意。
4. **标点仍须合规**：全角 `，。！？`、`……`、`——`、`～`、`“”`、`‘’`；**不得新增半角**；
   若为满足字节数必须牺牲标点，优先删 `、`（并列读点）与成组的 `——`/`～`，**保留句末 `。`**。
5. **术语照表**：人名/地名/称谓按作品层 `术语表.md`，不得改译名（例：鹰志/亚衣/伽鲁炟/伊库鲁尔/妲朴/奇肯多/美空学院/格雷塔迦露德/隼人先生/高内同学）。
6. `spk` 字段仅用于判断说话人，**不要写入输出**。

## 四、交付汇报
1. 输出路径 + 条数（与输入一致）；2. 逐条自检结果（**超预算条数必须为 0**，请用脚本核对 `encode('gbk')` 字节数）；
3. 你采用的主要压缩手段与典型例子（3–5 例：原译 → 精简后，字节数变化）；4. 未决问题（若有语义必须保留却压不下的，单列并说明）。

⚠️ 不得改写任何 `术语表.md`；中间脚本放 `翻译工作区\\_scratch\\`。
'''


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    rows = json.load(io.open(os.path.join(PROJ, '语料', '_截断清单.json'), encoding='utf-8'))
    rows.sort(key=lambda r: (r['file'], r['idx'] if r['idx'] is not None else -1))
    per = (len(rows) + k - 1) // k
    for i in range(k):
        part = rows[i * per:(i + 1) * per]
        if not part:
            continue
        no = i + 1
        io.open(os.path.join(WD, '精简批次%d_输入.json' % no), 'w', encoding='utf-8').write(
            json.dumps(part, ensure_ascii=False, indent=1))
        io.open(os.path.join(WD, '_精简派单_批次%d.md' % no), 'w', encoding='utf-8').write(
            TPL.format(no=no, total=k, n=len(part), root=r'E:\ZCode Workspace\Galgame'))
        print('精简批次%d：%d 条（超长 1–2 字节 %d、3–4 %d、≥5 %d）'
              % (no, len(part), sum(1 for r in part if r['over'] <= 2),
                 sum(1 for r in part if 3 <= r['over'] <= 4),
                 sum(1 for r in part if r['over'] >= 5)))


if __name__ == '__main__':
    main()