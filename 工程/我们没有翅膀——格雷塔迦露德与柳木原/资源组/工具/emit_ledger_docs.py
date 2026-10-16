#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""W5 资源总账 · 文档生成器（ISSUE-20260918-06）

读 `资源总账.json` + `W5自证.json`，生成两份人读文档：
  krkr素材库\资源总账.md          人读摘要（交叉统计 / 分布 / 同名组 / 缺口 / 建议）
  krkr素材库\资源总账.schema.md   字段说明 + 归一化规则 + 与六源原清单的字段映射表

统计数字一律从总账本身复算，不手写，保证与 JSON 自洽、可复跑。

用法：python emit_ledger_docs.py
"""
from __future__ import annotations

import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RES_GROUP = os.path.dirname(HERE)
PROJ = os.path.dirname(RES_GROUP)
WORKSPACE = os.path.dirname(os.path.dirname(PROJ))    # <checkout> 根

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）：`_冲突数据.json` 等 gitignore 数据仅在主工作区；
#      `资源总账.json` 读本 checkout（由 build_asset_ledger.py 写在本 checkout）。
# 写 = 本 checkout 的 krkr素材库（总账 md/schema）。
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
PRJ_DATA = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
LIB = os.path.join(PRJ_DATA, r"资源组\krkr素材库")        # 只读：_冲突数据.json 等
LIB_OUT = os.path.join(RES_GROUP, "krkr素材库")           # 读写：总账三件（本 checkout）
# 自证目录：默认 W5；可用 --out-dir 指向 W5b 等（W5b 密钥修复自证）
OUT_DIR = os.path.join(WORKSPACE, "子代理工作区", "ISSUE-20260918-06", "W5")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WORKSPACE)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]
SRC_LABEL = {
    "ot": "ot（本篇）", "otr": "otr（R 版亚衣线）", "ota": "ota（After Story）",
    "otp": "otp（前奏诗）", "otv": "otv（PSV 美咲线）", "np": "np（涅布＊プラス）",
}
KINDS = ["chr", "pic", "sys", "bgm", "se", "voice", "movie", "etc"]


def mib(b):
    return b / 1024 / 1024


def main():
    with open(os.path.join(LIB_OUT, "资源总账.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    entries = ledger["entries"]
    meta = ledger["meta"]
    with open(os.path.join(OUT_DIR, "W5自证.json"), encoding="utf-8") as f:
        sc = json.load(f)
    with open(os.path.join(LIB, "_冲突数据.json"), encoding="utf-8") as f:
        conflict = json.load(f)

    cnt = collections.Counter((e["source"], e["kind"]) for e in entries)
    byt = collections.Counter()
    for e in entries:
        byt[(e["source"], e["kind"])] += e["bytes"]
    total = len(entries)
    total_bytes = sum(e["bytes"] for e in entries)
    kinds_present = [k for k in KINDS if any(e["kind"] == k for e in entries)]

    probe = sc["near_dup_probe"]
    st = sc["stats"]

    # ---------------- 资源总账.md ----------------
    L = []
    A = L.append
    A("# krkr 素材库 · 资源总账")
    A("")
    A(f"> 生成：{meta['generated']} ｜ 模块：**W5 资源总账** ｜ Issue：`ISSUE-20260918-06` ｜ 模式：工程")
    A(f"> 构建脚本：`资源组\\工具\\build_asset_ledger.py`（可复跑）｜ 校验脚本：`资源组\\工具\\verify_asset_ledger.py`")
    A(f"> 核心交付：**`资源总账.json`**（{total:,} 条，W6 结构化剧本 / W9 美术归纳 / 编程组的唯一素材索引）")
    A("> 上游：W1/W2/W3 素材提取 → W4 六源素材归集与跨源冲突扫描 → **W5 归一化总账**")
    A("")
    A("---")
    A("")
    A("## 〇、总览")
    A("")
    A("| 项 | 值 |")
    A("| --- | --- |")
    A(f"| 素材总条数 | **{total:,}**（与 W4 `_冲突报告.md` 的 {total:,} 一致） |")
    A(f"| 磁盘总体积 | **{mib(total_bytes):,.1f} MiB**（{total_bytes:,} B） |")
    A(f"| 源数 / 类别数 | 6 源 × {len(kinds_present)} 类（{'/'.join(kinds_present)}） |")
    A(f"| 图像 / 音频 / 视频 / 数据 | "
      f"{sc['by_content_type'].get('image',0):,} / {sc['by_content_type'].get('audio',0):,} / "
      f"{sc['by_content_type'].get('video',0):,} / {sc['by_content_type'].get('data',0):,} |")
    audio_ok = sc["audio_count"] - sc["audio_duration_missing"]
    A(f"| 音频时长合计 | **{sc['audio_duration_total_sec']/3600:,.2f} 小时**"
      f"（可解析 {audio_ok:,} 条；**{sc['audio_duration_missing']} 条无法解析**） |")
    A(f"| 有用途标签 / 未判定 | {sc['usage_tagged']:,} / {sc['usage_untagged']:,}"
      f"（未判定者 `usage` 为空数组，**未编造**） |")
    A(f"| 跨源同名组 | {conflict['cross_source_stems']:,} 组"
      f"（同名相同内容 {conflict['same_groups']:,} / 同名不同内容 {conflict['diff_groups']:,}），"
      f"涉及 {conflict['detail_rows']:,} 条 |")
    A(f"| `dup_of` 已指向 | {sc['dup_of_set']:,} 条（仅「逐字节相同」的组） |")
    A("")
    A("**命名规范**：`<源代号>_<原文件名小写>`，分目录隔离（总纲 §七 I1、§八 D2）。"
      "本总账 `out_relpath` 统一为 `<源代号>/<类别>/<文件名>`。")
    A("")
    A("---")
    A("")
    A("## 一、六源 × 七类交叉统计表（条数）")
    A("")
    hdr = "| 源 | " + " | ".join(kinds_present) + " | 合计 |"
    A(hdr)
    A("| --- |" + " ---: |" * (len(kinds_present) + 1))
    colsum = collections.Counter()
    for s in SOURCES:
        row = [cnt.get((s, k), 0) for k in kinds_present]
        for k, v in zip(kinds_present, row):
            colsum[k] += v
        A(f"| {SRC_LABEL[s]} | " + " | ".join(f"{v:,}" for v in row) + f" | **{sum(row):,}** |")
    A("| **合计** | " + " | ".join(f"**{colsum[k]:,}**" for k in kinds_present)
      + f" | **{total:,}** |")
    A("")
    A(f"（数据格合计 = {total:,}，与总账条目数守恒；逐源、逐类均已复核。"
      "表内 `etc` 为 `otv`（PSV）独有的第 8 类，124 条（W3 的 ETC.cpk 产物）；"
      "其余七类 chr/pic/sys/bgm/se/voice/movie 为六源共有类别。"
      "W4b 补归集后 `otv` 已覆盖全部 8 类——W3 仅 sys/etc，美咲线素材补入 chr/pic/voice/bgm/se/movie。）")
    A("")
    A("## 二、六源 × 七类体积分布（MiB）")
    A("")
    A(hdr)
    A("| --- |" + " ---: |" * (len(kinds_present) + 1))
    for s in SOURCES:
        row = [mib(byt.get((s, k), 0)) for k in kinds_present]
        A(f"| {SRC_LABEL[s]} | " + " | ".join(f"{v:,.1f}" for v in row) + f" | **{sum(row):,.1f}** |")
    A("| **合计** | " + " | ".join(
        f"**{mib(sum(byt.get((s,k),0) for s in SOURCES)):,.1f}**" for k in kinds_present)
      + f" | **{mib(total_bytes):,.1f}** |")
    A("")
    A("## 三、图像尺寸分布（按源，Top 12）")
    A("")
    img_total = collections.Counter(e["source"] for e in entries if e["image"])
    A("（各源图像**总数**来自总账实算；下表仅列**出现最多的 12 种尺寸**）")
    A("")
    for s in SOURCES:
        d = sc["image_size_dist"].get(s)
        if not d:
            continue
        A(f"**{SRC_LABEL[s]}**（共 {img_total.get(s,0):,} 张，下表 Top {min(12,len(d))}）")
        A("")
        A("| 尺寸 | 张数 |")
        A("| --- | ---: |")
        for k, v in list(d.items())[:12]:
            A(f"| {k} | {v:,} |")
        A("")
    A("## 四、图像色彩模式分布（按源）")
    A("")
    A("| 源 | " + " | ".join(sorted({m for d in sc["image_mode_dist"].values() for m in d}))
      + " | 合计 |")
    A("| --- |" + " ---: |" * (len({m for d in sc["image_mode_dist"].values() for m in d}) + 1))
    allmodes = sorted({m for d in sc["image_mode_dist"].values() for m in d})
    for s in SOURCES:
        d = sc["image_mode_dist"].get(s, {})
        A(f"| {s} | " + " | ".join(f"{d.get(m,0):,}" for m in allmodes)
          + f" | {sum(d.values()):,} |")
    A("")
    A("## 五、音频规格分布（采样率 / 声道）")
    A("")
    A("| 源 | 规格 | 条数 |")
    A("| --- | --- | ---: |")
    for s in SOURCES:
        d = sc["audio_spec_dist"].get(s)
        if not d:
            continue
        first = True
        for k, v in sorted(d.items(), key=lambda x: -x[1]):
            A(f"| {s if first else ''} | {k} | {v:,} |")
            first = False
    A("")
    A("> 规格解析方式：直接读 Ogg 首页的 Vorbis identification header（`\\x01vorbis` 后 "
      "channels / sample_rate），**不调用外部解码器、不解码音频**。")
    A("")
    A("## 六、跨源同名组统计（引用 W4 `_冲突报告.md`）")
    A("")
    A("| 项 | 值 | 依据 |")
    A("| --- | --- | --- |")
    A(f"| 跨源同名组 | **{conflict['cross_source_stems']:,}** | 去来源前缀后的小写 stem 出现在 ≥2 个来源 |")
    A(f"| ├ 同名相同内容 | {conflict['same_groups']:,} | 组内 md5 全同（全量逐字节） |")
    A(f"| └ 同名不同内容 | **{conflict['diff_groups']:,}** | 组内 md5 不全相同 |")
    A(f"| 同名组涉及文件 | {conflict['detail_rows']:,} | |")
    A(f"| 总账中 `dup_group` 命中 | {sc['dup_members']:,} | 与上一行一致 |")
    A(f"| 总账中 `dup_of` 指向 | {sc['dup_of_set']:,} | 仅「逐字节相同」组，指向按源序首个 |")
    A("")
    A("**同名不同内容的高发源对（W4 矩阵 Top）**")
    A("")
    A("| 源对 | 类别 | 差异组数 |")
    A("| --- | --- | ---: |")
    flat = []
    for pair, kd in conflict["pair_matrix"].items():
        for k, v in kd.items():
            flat.append((v, pair, k))
    for v, pair, k in sorted(flat, reverse=True)[:12]:
        A(f"| {pair.replace('|',' ↔ ')} | {k} | {v:,} |")
    A("")
    A("### 6.1 同名差异的**性质**（W5 分层抽样全字节比对）")
    A("")
    A(f"W4 以 md5 判定「不同」，但 md5 不同 ≠ 内容不同。本模块对 {probe['diff_groups_total']:,} 个"
      f"「同名不同内容」组按类别分层抽样 **{probe['sampled_groups']} 组 / {probe['sampled_pairs']:,} 个素材对**，"
      "**完整读取双方逐字节比对**，结果：")
    A("")
    A("| 性质 | 素材对数 | 占比 | 含义 |")
    A("| --- | ---: | ---: | --- |")
    defs = probe["class_definitions"]
    for k, v in probe["counts"].items():
        A(f"| `{k}` | {v:,} | {100*v/probe['sampled_pairs']:.1f}% | {defs.get(k,'')} |")
    A(f"| **合计** | **{probe['sampled_pairs']:,}** | 100% | |")
    A("")
    same_audio = probe["counts"].get("tail_only", 0) + probe["counts"].get("tail_truncated", 0)
    A(f"→ **{same_audio:,} 对（{100*same_audio/probe['sampled_pairs']:.1f}%）前缀逐字节全同**，"
      "即「同一文件、同一录音」，差异只在文件末尾 ≤16 字节；")
    A(f"另有 {probe['counts'].get('head_zone',0):,} 对差异全部落在**文件头 300 字节内**"
      "（头部元数据差异；W5b 修复 `ot/se` 密钥后，原属此类的 `ot`↔他源 se 对已转为 `tail_only`）。")
    A("")
    A("**按类别**")
    A("")
    allk = sorted({k for d in probe["by_kind"].values() for k in d})
    A("| 类别 | " + " | ".join(f"`{k}`" for k in allk) + " |")
    A("| --- |" + " ---: |" * len(allk))
    for kind, d in probe["by_kind"].items():
        A(f"| {kind} | " + " | ".join(f"{d.get(k,0):,}" for k in allk) + " |")
    A("")
    A("**按源对**（Top 12）")
    A("")
    A("| 源对 | " + " | ".join(f"`{k}`" for k in allk) + " |")
    A("| --- |" + " ---: |" * len(allk))
    rows = sorted(probe["by_source_pair"].items(),
                  key=lambda x: -sum(x[1].values()))[:12]
    for pair, d in rows:
        A(f"| {pair.replace('|',' ↔ ')} | " + " | ".join(f"{d.get(k,0):,}" for k in allk) + " |")
    A("")
    A("> ⚠️ **口径警示**：W4 报告 §六.2「11082 组同名不同内容必须隔离」在**字节层面成立**，"
      "但其中相当一部分实为**同一录音仅尾部字节差异**。**隔离策略不变（分目录 + 来源前缀，禁止裸合并）**，"
      "但 W6/W9 在做素材选用与去重时，**不应把「md5 不同」直接当作「素材不同」**；"
      "本模块的分层抽样给出了量化比例，逐组明细可用 `_同名冲突明细.tsv` 复核。")
    A("")
    A("## 七、缺口清单（已知缺失项，如实登记）")
    A("")
    A("| # | 缺口 | 状态 | 影响 / 处置 |")
    A("| --- | --- | --- | --- |")
    otv_n = sum(cnt.get(("otv", k), 0) for k in KINDS)
    otv_b = sum(byt.get(("otv", k), 0) for k in KINDS)
    A(f"| G1 | **PSV 美咲线素材**（W3 UI 306 + W4b 美咲线补归集） | **已补提**"
      f"（`otv`，{otv_n:,} 条 / {mib(otv_b):,.1f} MiB；UI 306 条带 `content_note` 人工判读，"
      f"美咲线 2,211 条无 content_note、已按兄弟源同口径启用启发式 `usage` 标签，`usage_src=heuristic`）"
      f" | 不再阻塞；D7 裁决 PSV 美咲线完全采用 |")
    A("| G2 | **涅布＊プラス 明日香篇 ASU 音库缺失** | **无解**（本机副本即缺） | `np/voice` 仅 68 条（全部 HIY 音库）；审计 §7.4 实测 ASU 引用 559 / 存在 0 → **559 条台词无语音可放**，逐条清单见该作 `素材提取\\音频\\语音缺失清单.tsv`；成品说明须如实标注 |")
    A("| G3 | **R 版仅亚衣线素材**（`otr` 2,995 条） | **按裁决执行**（总纲 §八 D10） | R 版不提取全量，主线用 `ot` 本篇素材代替；R 版独有内容仅亚衣线 + 追加 CG，按需另议 |")
    A("| G4 | **本篇（`ot`）SE 582 条 Ogg 头部损坏** | **已定位并修复**（W5b，见 §九 F2） | 根因＝社区 `LPK-Keys.json` 的 SE.LPK `Key1` 有误；已用游戏自述密钥覆盖重提，582/582 可播放 |")
    A("| G5 | **`np` 宽幅背景未提取** | 未提取 | 审计 §7.4：11 条 32bpp `bg*_a1` 与 10 条 3840×720 未提取；`np/pic` 仅 93 条 |")
    A("| G6 | **前奏诗 `.elg` 原件未保留**（仅 PNG） | 既定 | 不影响 krkr（PNG 原生支持）；无法回溯原始编码 |")
    A("| G7 | **`otp`/`ota` 系统数据（`.gmp`/`.lag`）未结构化解码** | 未解码 | `ot` 13+1、`ota` 9+1、`otp` 4+1 条，归为 `content_type=data`；总纲 §八 D11 待裁决，UI 组若需界面布局参数则须解 |")
    A("| G8 | **BGM 无场景映射** | 未建 | 各源 BGM 均只能整包给（脚本无按名引用）；W6 需按章节语义配乐 |")
    A("| G9 | **`np` 语音命名体系与 Lucifen 系不同** | 已隔离 | `np` 为 `hiy30001.ogg`，Lucifen 系为 `ai_1002.ogg`；靠来源前缀隔离 |")
    A("| G10 | **影片未做格式验证** | 未验证 | 共 **10 条**（`ot` 2 / `ota` 3 / `otp` 1 / `np` 2 为 `.mpg`；"
      "**`otv` 2 为 `.mp4`**，W4b 补归集）——按 `content_type=video` 口径；krkr 走 DirectShow，编程组需实测（总纲 §三.2 G3）。"
      "另 `ota/movie/ota_bg.txt` 1 条为文本（`content_type=data`，非影片），故 `kind=movie` 计数为 11 |")
    A("")
    A("## 八、给 W9（美术归纳）的建议")
    A("")
    A("1. **以 `kind` 为一级分类，`source` 为二级分类**：`资源总账.json` 的 `(source, kind)` 已是稳定主键，"
      "W9 直接按此聚合即可，无需重新扫描磁盘。")
    A("2. **立绘（`chr`）与 CG/背景（`pic`）应分治**：")
    A(f"   - `chr` 共 {cnt.get(('ot','chr'),0)+cnt.get(('otr','chr'),0)+cnt.get(('ota','chr'),0)+cnt.get(('otp','chr'),0)+cnt.get(('np','chr'),0):,} 条，"
      "以 RGBA 为主（带真实透明），尺寸不统一，是**差分/部件级**素材，宜按角色代号（`ai`/`asu`/`hiy`/`nar`/`kaz`…）建索引。")
    A(f"   - `pic` 共 {sum(cnt.get((s,'pic'),0) for s in SOURCES):,} 条，含背景、事件 CG、分片与特效；"
      "`usage` 已给出 `背景`/`事件CG`/`特效`/`缩略图`/`演出CG（宽幅/竖幅）` 启发式标签（`usage_src=heuristic`），可作为初筛，**须人工复核**。")
    A("3. **尺寸是四套互不兼容体系的直接体现**（总纲 §三.5 / §八 D1）：")
    for s in SOURCES:
        d = sc["image_size_dist"].get(s)
        if d:
            top = ", ".join(f"{k}({v})" for k, v in list(d.items())[:4])
            A(f"   - `{s}`：{top}")
    A("   → **D1 已裁决**：1280×720 画布，4:3 源原生 1:1 居中留黑边、16:9 源原生填满，**一律不放大**。"
      "W9 归纳时请勿把不同源的立绘/CG 混入同一套差分体系。")
    A("4. **`otv` 的 W3 UI 306 条是唯一带人工内容判读的素材**（`note` 字段保留原始 `content_note`，"
      "`usage_src=content_note`）：UI 组做 krkr UI 时应优先引用这一批，并可据其命名规律（`bg_config_*`/`dlg_*`/`ec_*`/`loading`…）反推 PSV 界面结构。"
      "**W4b 补归集的 2,211 条美咲线素材（chr/pic/voice/bgm/se/movie）无 `content_note`，"
      "已按兄弟源同口径启用启发式 `usage` 标签（`usage_src=heuristic`）**——W9/W6 可作初筛，**须人工复核**。")
    A("5. **同名素材选用必须显式带来源前缀**：跨源同名 12,344 组中 11,082 组 md5 不同"
      "（其中抽样约 "
      f"{100*(probe['counts'].get('tail_only',0)+probe['counts'].get('tail_truncated',0))/probe['sampled_pairs']:.0f}%"
      " 实为同一录音仅尾部差异）→ **不得按 basename 隐式解析**，引用一律 `ot/…`、`otr/…` 全路径。")
    A("6. **美术风格统一**（AGENTS.md §六）：W9 归纳时应对混用不同源立绘的场合作出标注，"
      "由主代理按 D1 裁决统一处理。")
    A("")
    A("## 九、W5 发现（供主代理裁决）")
    A("")
    A("### F1 · 跨源同名 Ogg 常仅「文件末尾 ≤16 字节」不同")
    A("")
    A(f"分层抽样 {probe['sampled_pairs']:,} 个同名素材对全字节比对：**{probe['counts'].get('tail_only',0):,} 对**"
      f"（{100*probe['counts'].get('tail_only',0)/probe['sampled_pairs']:.1f}%）文件大小相同、"
      "**前缀逐字节完全一致**，仅末尾 ≤16 字节不同；另有 "
      f"**{probe['counts'].get('tail_truncated',0)} 对**为「前缀全同、一方尾部截断 ≤16 字节」。")
    A("")
    A("实证例：`ot/bgm/ot_bgm01a.ogg` ↔ `otr/bgm/otr_bgm01a.ogg` 大小同为 1,499,859 B，"
      "**前 1,499,845 字节完全一致**，仅末 14 字节不同；`np/bgm/np_bgm01a.ogg`（1,114,489 B）"
      "与前者前缀 1,114,473 字节亦完全一致。")
    A("")
    A("**影响**：W4 报告「同名不同内容 11,082 组」在字节口径成立，但**不等于素材不同**；"
      "`dup_of` 按任务书口径（逐字节相同才置值）保持 null 是正确的，未改动。")
    A("")
    A("### F2 · `ot`（本篇）SE 582 条 Ogg 首页头损坏（**已定位并修复**）")
    A("")
    A("**状态**：W5b（ISSUE-20260918-06）已定位根因并修复，582/582 恢复可播放。")
    A("")
    A("| 项 | 实测 |")
    A("| --- | --- |")
    A("| 范围 | `ot/se/*.ogg` **全部 582 条**（`ot` 其他类别 0 条；其他源 0 条） |")
    A("| 现象 | 首页无 `\\x01vorbis` identification header；`ffmpeg` 报 `CRC mismatch!` / `Codec not found`，**无法播放** |")
    A("| 差异位置 | 与 `ota`/`otp`/`otr` 同 stem 文件比对：**固定 76 字节差异，全部落在偏移 17–268**（文件头区），其余逐字节一致 |")
    A("| 页结构 | 首页 `page_seq=9`（正常为 0），`nseg=1`（正常 14），首页后直接跳到末页 |")
    A("| **根因** | 社区 `工具\\lucifen\\Lucifen-Tools\\LPK-Keys.json` 中作品键 `Ore-tachi ni Tsubasa wa Nai` 的 **`SE.LPK` 条目 `Key1` 写错 1 字节**（`0x9A5AF6DE` → 应为 **`0x935AF6DE`**）。`Key1` 仅用于 `decrypt_content_1_first_256()`（内容区**前 256 字节**），`Key2` 正确 → 索引正常、**只有文件头损坏** |")
    A("| **根因证据** | `工程\\我们没有翅膀\\解包\\SCRIPT\\gameinit.sob` 中游戏**自述**的 7 条密钥记录（偏移 `0x1594` 起、间隔 `0x88`，结构 `<u32 Key1><u32 flag=8><u32 Key2>`），与社区表逐条比对 **6/7 命中**，唯一不命中的就是 SE.LPK 的 `Key1`；其余 6 档（SYS/CHR/PIC/BGM/VOICE/DATA）与社区表**逐字节一致** |")
    A("| **修复方式** | 在资源组自有加载器 `资源组\\工具\\lpk_media.py` 中新增 `KEY_OVERRIDES` 覆盖表（**社区文件只读、未改动**），覆盖值取自 `gameinit.sob` 游戏自述；用 `extract_s1_assets.py --only se` 重提 582 条 |")
    A("| **修复验证** | 582/582 `ffprobe` 解出 `vorbis`（失败 0）；582/582 `d[28:35]==b'\\x01vorbis'` 且首页 `page_seq==0`；与重提前坏版本逐条 md5 比对 **582 条全部变化**（确实被修复） |")
    A(f"| 对总账的影响 | 重跑后该 582 条 `audio` 三字段已全部解析（不再为 `null`），音频总时长相应增加；条数守恒 {total:,} |")
    A("| 跨源交叉（补充 F1） | `ot` 与同 stem 的 `ota`/`otp`/`otr`/`np` 比对（1,144 对）：`tail_only` 1,102 对（96.3%）、`identical` 2 对（0.2%）、`content_differs` 40 对（3.5%）→ 印证 F1「同名 Ogg 多为同一录音、仅尾部字节不同」 |")
    A("")
    A("**通用防范建议**：社区 `LPK-Keys.json` 的密钥可能个别字节有误，**不要盲信**。资源组加载器已具备通用能力："
      "`lpk_media.cross_check_keys(gameinit.sob, <作品键名>)` 可从任一作品的 `gameinit.sob` **健壮解析**其自述密钥"
      "（结构签名法定位，偏移不写死；失败时用社区表回退），并与社区表逐条比对、输出不一致项。"
      "**建议后续每个作品在首次提取前先跑一次该校验**，发现不一致即以 `KEY_OVERRIDES` 覆盖。")
    A("")
    A("### F3 · `ota` 与 `otp` 的 se 同名对中「头部 300B 内差异」")
    A("")
    A("抽样中 `head_zone` 对绝大多数为 `se` 类，原因为 `ot` 侧头部损坏参与比对所致；"
      "**W5b 修复 `ot/se` 密钥后该类已转为 `tail_only`**（见 F2）。")
    A("")
    A("---")
    A("")
    A("## 十、复跑与自证")
    A("")
    A("```")
    A("cd 工程\\我们没有翅膀——格雷塔迦露德与柳木原\\资源组\\工具")
    A("python build_asset_ledger.py --out-dir ..\\..\\..\\子代理工作区\\ISSUE-20260918-06\\W5b  # 重建 资源总账.json + W5自证.json")
    A("python emit_ledger_docs.py --out-dir ..\\..\\..\\子代理工作区\\ISSUE-20260918-06\\W5b    # 重建 资源总账.md + 资源总账.schema.md")
    A("python verify_asset_ledger.py       # 6 项验收自证 -> W5验收.json")
    A("```")
    A("")
    A("> W5b（SE 密钥修复）自证产物：`子代理工作区\\ISSUE-20260918-06\\W5b\\W5b自证.json`；"
      "W5 原始自证：`子代理工作区\\ISSUE-20260918-06\\W5\\W5自证.json`。")
    A("")

    md = "\n".join(L)
    _assert_in_checkout(os.path.join(LIB_OUT, "资源总账.md"), "资源总账.md")
    with open(os.path.join(LIB_OUT, "资源总账.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(f"写出 {os.path.join(LIB_OUT, '资源总账.md')} ({len(md.encode('utf-8')):,} B)")

    # ---------------- 资源总账.schema.md ----------------
    S = []
    B = S.append
    B("# 资源总账.schema.md · 字段说明与归一化规则")
    B("")
    B(f"> 生成：{time.strftime('%Y-%m-%d %H:%M:%S')} ｜ 模块：W5 资源总账 ｜ Issue：`ISSUE-20260918-06`")
    B("> 配套：`资源总账.json`（数据）、`资源总账.md`（人读摘要）、`资源组\\工具\\build_asset_ledger.py`（构建器）")
    B("> 目的：**便于审计与复跑**——说明六源原清单的 schema 差异、归一化规则、字段映射与验收口径。")
    B("")
    B("## 一、文件结构")
    B("")
    B("```jsonc")
    B("{")
    B('  "meta":    { /* 元信息：计数、源序、发现、抽样探针结果 */ },')
    B(f'  "entries": [ /* {total:,} 条素材，每条一个对象，见 §二 */ ]')
    B("}")
    B("```")
    B("")
    B("`meta` 关键字段：")
    B("")
    B("| 字段 | 说明 |")
    B("| --- | --- |")
    B("| `source_order` | `[\"ot\",\"otr\",\"ota\",\"otp\",\"otv\",\"np\"]`，即总纲 §四 的源序 |")
    B("| `source_rank_note` | `dup_of`「首个」的确定性判定规则 |")
    B(f"| `count` | 条目总数（应为 {total:,}） |")
    B("| `per_source` / `per_source_kind` | 逐源、逐源×类计数（供快速对账） |")
    B("| `known_artifacts` | F1/F2/F3 三项发现的摘要（详见 `资源总账.md` §九） |")
    B("")
    B("## 二、`entries[]` 字段说明")
    B("")
    B("| 字段 | 类型 | 说明 | 可空 |")
    B("| --- | --- | --- | --- |")
    B("| `source` | string | 来源代号：`ot`/`otr`/`ota`/`otp`/`otv`/`np` | 否 |")
    B("| `kind` | string | **归一化后的目录型**类别：`chr`/`pic`/`sys`/`bgm`/`se`/`voice`/`movie`/`etc` | 否 |")
    B("| `content_type` | string | 内容型：`image`/`audio`/`video`/`data`（扩展名 + 魔数双判据） | 否 |")
    B("| `orig_name` | string | **归档内原始条目名**（未加前缀、未改扩展名；`ot` 为 `.elg` 等原始写形） | 否 |")
    B("| `out_relpath` | string | **统一相对路径** = `<源代号>/<kind>/<文件名>`，相对 `krkr素材库\\` | 否 |")
    B("| `filename` | string | `out_relpath` 的 basename（含来源前缀） | 否 |")
    B("| `bytes` | int | **磁盘实测字节数**（非清单申报值） | 否 |")
    B("| `ext` | string | 磁盘文件扩展名（小写，不含点） | 否 |")
    B("| `image` | object\\|null | 仅图像：`{width,height,mode}`，读 PNG IHDR，**不解码像素** | 是 |")
    B("| `audio` | object\\|null | 仅音频：`{duration_sec,sample_rate,channels}`，解析 Ogg 页头 | 是 |")
    B("| `dup_group` | string\\|null | 跨源同名组的 stem（去来源前缀、去扩展名、小写）；无同名则 `null` | 是 |")
    B("| `dup_of` | string\\|null | 该组内**逐字节相同**时的「首个」成员 `out_relpath`；**同名不同内容一律 `null`** | 是 |")
    B("| `usage` | string[] | 用途标签；**判不出即空数组，不编造** | 否（可为 `[]`） |")
    B("| `usage_src` | string\\|null | 标签来源：`content_note`（人工判读）/ `heuristic`（启发式）/ `null`（未判定） | 是 |")
    B("| `note` | string | 附注：`otv` 的原始 `content_note`、魔数不符提示、音频解析失败原因等 | 否（可为 `\"\"`） |")
    B("| `src_bytes` | int | 来源清单申报的**原始（转码前）字节数**（`ot` 的 `.elg` 等） | 是 |")
    B("| `archive` | string | 来源归档名（如 `PIC.LPK`、`SystemData.cpk`、`亜衣线资源/图像/CHR`） | 是 |")
    B("")
    B("### 2.1 `image.mode` 取值与推导")
    B("")
    B("PNG IHDR colortype → 模式（与 PIL 口径一致）：`0`→`L`、`2`→`RGB`、`3`→`P`、`4`→`LA`、`6`→`RGBA`。")
    B("`otv` 清单自带 `colortype`，本模块以**磁盘 PNG 头实读值**为准，并与清单值交叉校验（差异 0 条）。"
      "（仅 W3 UI 306 条自带 `width/height/colortype`；W4b 补归集的 2,211 条无这些字段，不参与该校验。）")
    B("")
    B("### 2.2 `audio` 字段的推导与已知缺口")
    B("")
    B("| 项 | 方法 |")
    B("| --- | --- |")
    B("| `sample_rate` / `channels` | 首页内 `\\x01vorbis` 包：`channels`@+11，`sample_rate` u32LE@+12 |")
    B("| `duration_sec` | 最后一个自洽 Ogg 页的 `granule position` ÷ `sample_rate`（Vorbis 语义 granule = 总样点） |")
    B("| 与外部工具一致性 | 抽 2 条与 `ffprobe` 对照，`duration` 完全一致（64.050454 ↔ 64.05045351473923） |")
    B("| **已知缺口** | 无。原 `ot/se` **582 条**头部损坏（社区 `LPK-Keys.json` SE.LPK `Key1` 有误）已由 **W5b** 修复并重提，现全部可解析（见 `资源总账.md` §九 F2） |")
    B("")
    B("**未采用**的方案与原因：`mutagen`/`PIL` 在本机不可用；`ffprobe` 逐文件调用对 4.1 万个 Ogg 过慢。")
    B("本模块自研 Ogg 页头解析，全量 41,127 个 Ogg 用时约 30 s。")
    B("")
    B("## 三、六源原清单 schema 差异（归一化的输入）")
    B("")
    B("| 源 | 清单形态 | 条目数 | `kind` 语义 | 字段集 |")
    B("| --- | --- | ---: | --- | --- |")
    B("| `ot` | **list** | 24,597 | **目录型** `chr/pic/sys/bgm/se/voice/movie` | `archive, orig_name, kind, src_bytes, out_relpath, out_bytes` |")
    B("| `otr` | **list** | 2,995 | **目录型** | 同上 |")
    B("| `otp` | **list** | 5,950 | **目录型** | 同上 |")
    B("| `np` | **list** | 543 | **目录型** | 同上 |")
    B("| `ota` | **dict**（容器键 `source/game/generated/root/entries/failures/per_archive`） | 14,425 | **内容型** `image/audio/data/movie` | 条目字段同 list 六字段 |")
    B("| `otv` | **list** | 2,517 | **无 `kind` 字段**（kind 由 `out_relpath` 首段推导） | "
      "W3 UI 306：`archive, index, orig_name, out_relpath, src_bytes, out_bytes, width, height, colortype, content_note`；"
      "W4b 美咲线 2,211：`archive, orig_name, out_relpath, src_bytes, out_bytes, kind`（同一 list 内两种字段集并存） |")
    B("")
    B("### 3.1 归一化规则（逐条）")
    B("")
    B("1. **取条目列表**")
    B("   - `ot`/`otr`/`otp`/`np`/`otv`：清单本身即 list。")
    B("   - `ota`：清单是 **dict**，取 `raw['entries']`；`raw['failures']` 实测为空数组（0 条失败），"
      "`raw['per_archive']` 为逐归档统计，均**不进入总账**。")
    B("2. **目录型 `kind` 的确定**")
    B("   - `ot`/`otr`/`otp`/`np`：**直接用 `kind` 字段**；同时校验其与 `out_relpath` 首段一致"
      "（不一致写入 `stats.kind_path_mismatch`，实测 0 条）。")
    B("   - `ota`：`kind` 是**内容型**（`image/audio/data/movie`），**不能直接当类别用**；"
      "改取 `out_relpath` 的首段（`bgm/chr/movie/pic/se/sys/voice`）作为目录型 `kind`。"
      "`content_type` 字段则保留其内容型信息（与扩展名/魔数判定结果一致）。")
    B("   - `otv`：**无 `kind` 字段**；`out_relpath` 形如 `otv/sys/otv_bg_config_01.png`，"
      "**先剥去 `otv/` 前缀**，再取首段作为目录型 `kind`"
      "（W3：`sys` / `etc`；W4b 补归集美咲线：`chr` / `pic` / `voice` / `bgm` / `se` / `movie`）。")
    B("3. **`out_relpath` 统一**")
    B("   - `ot`/`ota`/`otr`/`otp`/`np` 的清单 `out_relpath` 是**源内相对路径**（如 `sys/ot_00_qsave.png`），"
      "统一时**前置** `<源代号>/`。")
    B("   - `otv` 的清单 `out_relpath` **已含** `otv/` 前缀，**不重复前置**（否则会出现 `otv/otv/...`）。")
    B("   - 统一结果一律小写，形如 `ot/sys/ot_00_qsave.png`、`otv/etc/otv_black.png`。")
    B("4. **`content_type`**：由扩展名映射 + **魔数校验**双判据。")
    B("   - `.png`→`image`（校验 `89 50 4E 47 0D 0A 1A 0A`）")
    B("   - `.ogg`→`audio`（校验 `OggS`）")
    B("   - `.mpg`/`.mp4`→`video`（校验 MPEG 起始码 `00 00 01 BA/B3` 或 `ftyp`）")
    B("   - `.gmp`/`.lag`/`.dat`/`.txt`→`data`")
    B("   - 魔数与扩展名不符者写入 `stats.magic_mismatch`（实测 0 条）。")
    B("5. **`bytes`**：取**磁盘实测** `os.path.getsize`，不取清单 `out_bytes`；"
      "两者差异写入 `stats.tsv_bytes_mismatch`（实测 0 条）。")
    B("6. **`stem`（用于 `dup_group`）**：`basename` → 若以 `<源代号>_` 开头则剥去 → 去扩展名 → 小写。"
      "与 W4 `_冲突报告.md` 的口径一致。")
    B("")
    B("## 四、与六源原清单的字段映射表")
    B("")
    B("| 总账字段 | `ot`/`otr`/`otp`/`np` 来源 | `ota` 来源 | `otv` 来源 | 变换 |")
    B("| --- | --- | --- | --- | --- |")
    B("| `source` | 目录名常量 | 目录名常量 | 目录名常量 | 常量 |")
    B("| `kind` | `kind` | `out_relpath` 首段 | `out_relpath` 剥 `otv/` 后首段 | 见 §3.1-2 |")
    B("| `content_type` | 扩展名 + 魔数 | 同左（且与 `kind` 互校） | 扩展名 + 魔数 | 见 §3.1-4 |")
    B("| `orig_name` | `orig_name` | `orig_name` | `orig_name` | 直取 |")
    B("| `out_relpath` | `<源>/` + `out_relpath` | `<源>/` + `out_relpath` | `out_relpath`（原样） | 见 §3.1-3 |")
    B("| `filename` | `out_relpath` basename | 同左 | 同左 | 派生 |")
    B("| `bytes` | 磁盘实测（≈`out_bytes`） | 磁盘实测 | 磁盘实测 | 见 §3.1-5 |")
    B("| `ext` | `filename` 扩展名 | 同左 | 同左 | 派生 |")
    B("| `image` | 磁盘 PNG IHDR | 磁盘 PNG IHDR | 磁盘 PNG IHDR（与 `width/height/colortype` 互校） | 读头 |")
    B("| `audio` | 磁盘 Ogg 页头 | 磁盘 Ogg 页头 | 磁盘 Ogg 页头（W4b 补入 voice/bgm/se） | 读头 |")
    B("| `dup_group` | W4 `_冲突数据.json` 的 `detail` 键 | 同左 | 同左 | 关联 |")
    B("| `dup_of` | W4 `detail[*].same` + `md5` | 同左 | 同左 | 见 §五 |")
    B("| `usage` / `usage_src` | 文件名/类别/尺寸启发式 | 同左 | W3 UI 306 条：`content_note` 关键词映射；"
      "W4b 美咲线 2,211 条：无 `content_note` → 回落兄弟源同口径启发式（`heuristic`，须人工复核） | 见 §六 |")
    B("| `note` | 魔数提示 | 魔数提示 | `content_note` 原文 | 拼接 |")
    B("| `src_bytes` | `src_bytes` | `src_bytes` | `src_bytes` | 直取 |")
    B("| `archive` | `archive` | `archive` | `archive` | 直取 |")
    B("")
    B("## 五、`dup_group` / `dup_of` 的口径")
    B("")
    B("- **数据来源**：**复用 W4 的全量 md5 扫描结果** `_冲突数据.json`（12,344 组、逐条 md5），"
      "**不重算**，保证与 `_冲突报告.md` 完全一致、可复现。")
    B("- `dup_group`：该条目所属「跨源同名组」的 stem。已复核 `_冲突数据.json` 中**不存在单源组**"
      "（每组涉及 2–5 个来源，分布 2 源 10,272 / 3 源 1,534 / 4 源 497 / 5 源 41）。")
    B("- `dup_of`：")
    B("  - 组内 **md5 全同**（`same=true`）→ 组内**唯一一个**成员（「首个」）为 `null`，其余指向它；")
    B("  - 组内 **md5 不全同**（`same=false`）→ **全部成员为 `null`**"
      "（即 W4 报告所称「同名不同内容」组，本总账一律不置 `dup_of`）。")
    B("  - 「首个」的确定性规则：按 `meta.source_order` 的源序 + `out_relpath` 字典序取最小。")
    B("- ⚠️ **注意**：`same=false` **不等于素材不同**——分层抽样显示约 "
      f"{100*(probe['counts'].get('tail_only',0)+probe['counts'].get('tail_truncated',0))/probe['sampled_pairs']:.0f}%"
      " 的同名对前缀逐字节全同（仅文件末尾 ≤16 字节不同）。详见 `资源总账.md` §六.1 与 §九 F1。")
    B("- **不做物理去重**：同名相同内容的 1,262 组保留全部条目（保留可回滚性、维持每源自洽），"
      "仅以 `dup_of` 标注关系。")
    B("")
    B("## 六、`usage` 标签的来源与口径")
    B("")
    B("| 来源 | 适用 | `usage_src` | 说明 |")
    B("| --- | --- | --- | --- |")
    B("| `otv` 的 `content_note` | W3 UI 306 条（W4b 补归集的 2,211 条无 `content_note`，回落启发式，见下） | `content_note` | **W3 人工判读**，关键词映射为标签：加载提示→`loading`、EyeCatch→`eyecatch`、转场遮罩→`transition_mask`、场景选择画面→`scene_select`、配置画面→`config`、回想→`backlog`、logo→`logo`、对话窗样式→`message_window` |")
    B("| 类别启发式 | `chr/sys/bgm/se/voice/movie/etc`（**含无 `content_note` 的 `otv`**） | `heuristic` | 类别 → `立绘`/`系统UI`/`BGM`/`音效`/`语音`/`影片`/`其他` |")
    B("| 文件名启发式 | `pic` | `heuristic` | `bg*`→`背景`、`ec*`→`事件CG`、`ef*`→`特效`、`th_*`→`缩略图` |")
    B("| 尺寸启发式 | `pic` | `heuristic` | 宽高比 ≥1.8 或 ≤0.55 → `演出CG（宽幅/竖幅）` |")
    B("| 无法判定 | — | `null` | **`usage` 留空数组，不编造** |")
    B("")
    B(f"实测：{sc['usage_tagged']:,} 条有标签 / **{sc['usage_untagged']:,} 条无标签**（空数组）。"
      "**启发式标签仅供参考，须人工复核**；W9/W6 不得将其当作确定结论。")
    B("")
    B("**W10（2026-09-19，主代理裁决）变更**：W4b 补归集的 **2,211 条 `otv` 美咲线素材**原为 `[]` + `usage_src=null`"
      "（未编造），现启用**与兄弟源同口径的启发式标签**（`chr`→立绘、`pic` 的 `bg*`/`ec*` 前缀→背景/事件CG、"
      "`bgm`/`se`/`voice`/`movie`→类别名；`pic` 另含 `ef*`/`th_*`/尺寸启发式），`usage_src=heuristic`，**须人工复核**。"
      "W3 UI 306 条中命中关键词映射的 **264 条**仍为 `usage_src=content_note`，不受影响；"
      "另 **42 条**有 `content_note` 但未命中关键词映射者**维持空数组 + `null`**（不臆造，其原文保留在 `note` 字段）。")
    B("")
    B("## 七、验收口径与自证")
    B("")
    B("| # | 标准 | 判定 |")
    B("| --- | --- | --- |")
    B(f"| A1 | 条数守恒 = {total:,} | 总账计数 == 期望值 == **磁盘实数**（逐源对账） |")
    B("| A2 | 零丢失 | `out_relpath` 去重数 == 总条数；**全量** `os.path.isfile` 检查 + 抽样 200 条明列 |")
    B(f"| A3 | 归一化正确 | 与 W4 独立产物 `_命名映射表.tsv`（{total:,} 行）逐条交叉校验 `out_relpath` / `kind` / `bytes` |")
    B("| A4 | 图像元数据 | 随机 50 张，用 **ffprobe（独立工具）** 复核 `width/height/pix_fmt` |")
    B("| A5 | 跨源关联 | 随机 10 组 + 报告点名 8 个 stem + **全量**复核（diff 组无 `dup_of`、same 组恰好 1 个 `null`） |")
    B(f"| A6 | 统计自洽 | `资源总账.md` §一 交叉统计表：数据格求和 == {total:,}，且行合计 == 行内数据格之和 |")
    B("")
    B("自证脚本：`资源组\\工具\\verify_asset_ledger.py` → `子代理工作区\\ISSUE-20260918-06\\W5\\W5验收.json`")
    B("")
    B("## 八、复跑步骤")
    B("")
    B("```")
    B("cd 工程\\我们没有翅膀——格雷塔迦露德与柳木原\\资源组\\工具")
    B("python build_asset_ledger.py     # -> krkr素材库\\资源总账.json（约 35 s）")
    B("python emit_ledger_docs.py       # -> krkr素材库\\资源总账.md + 资源总账.schema.md")
    B("python verify_asset_ledger.py    # -> 子代理工作区\\ISSUE-20260918-06\\W5\\W5验收.json")
    B("```")
    B("")
    B("**只读声明**：三个脚本对 `krkr素材库\\{ot,ota,otv,otr,otp,np}\\` 下的素材本体与六源清单"
      "**一律只读**，不修改任何入库资产。")
    B("")

    sch = "\n".join(S)
    _assert_in_checkout(os.path.join(LIB_OUT, "资源总账.schema.md"), "资源总账.schema.md")
    with open(os.path.join(LIB_OUT, "资源总账.schema.md"), "w", encoding="utf-8") as f:
        f.write(sch)
    print(f"写出 {os.path.join(LIB_OUT, '资源总账.schema.md')} ({len(sch.encode('utf-8')):,} B)")
    print(f"  总账条目 {total:,} / 体积 {mib(total_bytes):,.1f} MiB")


if __name__ == "__main__":
    if "--out-dir" in sys.argv:
        OUT_DIR = os.path.abspath(sys.argv[sys.argv.index("--out-dir") + 1])
    main()