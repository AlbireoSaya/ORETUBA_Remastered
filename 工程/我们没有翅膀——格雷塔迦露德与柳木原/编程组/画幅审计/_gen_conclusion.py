#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""由审计 TSV 生成《结论_名单.md》（一次性文档生成器，保留以便复算）。

输入（同目录）：
  超分候选_背景A类.tsv   逐场景背景归属.tsv   准16比9微边_C类.tsv
  空背景场景.tsv         影片清单.tsv
输出：结论_名单.md
"""
import os
import io
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def rd(name):
    p = os.path.join(HERE, name)
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        txt = f.read().replace("\r\n", "\n").replace("\r", "\n")
    rows = [ln.split("\t") for ln in txt.split("\n") if ln.strip()]
    head = rows[0]
    return head, [dict(zip(head, r)) for r in rows[1:]]


def col(row, *alts):
    for a in alts:
        if a in row and row[a] != "":
            return row[a]
    return ""


# 交付层实件根（`美术统一_交付\<交付路径>`）。
# ⚠️ `资源组\美术统一_交付\` 被 gitignore ⇒ **任何新 worktree 里都没有这份实体件**，
#    所以本脚本**不能只按自身位置反推**：先试本地，缺则回落到主工作树（可用 `--art-root` 覆盖）。
ART_LOCAL = os.path.normpath(os.path.join(HERE, "..", "..", "资源组", "美术统一_交付"))
ART_MAIN = (r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"
            r"\资源组\美术统一_交付")
ART = ART_LOCAL


def nbytes(deliv):
    """交付层实件的字节数；取不到返回 0（报告会以"缺件"与闸门体现，不会静默变 0）。

    ⚠️ **本目录（`美术统一_交付\\`）里只有 `交付清单.tsv` / `交付说明.md` 入库，素材本体被
    gitignore** ⇒ 任何**新建 worktree 里这个目录都存在、但实体件一件都没有**（`isdir` 判不出来）。
    故**必须逐件回落**：先试本地根，再试主工作树的同一相对路径。
    """
    rel = deliv.replace("/", os.sep)
    for root in (ART, ART_MAIN):
        try:
            return os.path.getsize(os.path.normpath(os.path.join(root, rel)))
        except OSError:
            pass
    return 0


def mib(n):
    return n / 1048576.0


def main():
    global ART
    if len(sys.argv) > 1:
        ART = os.path.normpath(sys.argv[1])
    elif not os.path.isdir(ART_LOCAL):
        ART = ART_MAIN
    print("[art] 交付层实件根 = %s" % ART)
    if not os.path.isdir(ART):
        print("[FATAL] 交付层实件根不存在，体积会全为 0 —— 请用 --art-root 指定"); return

    hA, A = rd("超分候选_背景A类.tsv")
    hC, C = rd("准16比9微边_C类.tsv")
    hE, E = rd("空背景场景.tsv")
    hS, S = rd("逐场景背景归属.tsv")
    hV, V = rd("影片清单.tsv")

    out = []
    w = out.append

    w("# 画幅审计 · 背景与影片「黑边」名单")
    w("")
    w("- Issue：`ISSUE-20261001-18` ｜ 分支：`issue/ISSUE-20261001-18-bg-blackbar-audit` ｜ 日期：2026-10-01")
    w("- 数据来源：**成品**（用户实际在玩的那份）`成品\\我们没有翅膀——格雷塔迦露德与柳木原\\game\\story\\scene_*.tjs` 共 **680** 个场景"
     "，逐场景的选框/挑图判据**逐字复算**自 `编程组\\krkr\\game\\ui_story.tjs` 的 `uiStoryBgIsCard` / `uiStoryPickBg` / `uiStoryApplyScene`；"
     "`content_boxes` 取自 `UI组\\layout\\_root.json`")
    w("- 判据（与引擎一致）：`dFull < dSrc` ⇒ 落全画布 `0,0,1920,1080`，否则落源内容区"
     "（`ot/otr/ota/otp = 360,90,1200,900`；`otv = 240,132,1440,816`；`np = 0,0,1920,1080`）；"
     "落框用 contain 居中：`k=min(cb.w/aw, cb.h/ah)`，`w=floor(aw*k)`、`h=floor(ah*k)`，**素材不会超出所选框**")
    w("")

    w("## 〇 一句话结论")
    w("")
    w("**黑边是素材问题，不是我用错。** 644 个有背景场景里 **325 个（50.5%）** 显示的素材本身不是 16:9"
     "（4:3 为主，另有竖图 / 2:1 / 超宽 / 1:1），运行时必然留边；其余 **262 个**满幅正常。")
    w("**没有任何 16:9 素材被塞进 4:3 内容框**（逐字复算 + 全量比对，反例 0），"
     "**也没有任何 16:9 素材把黑边烘焙进像素**（严格扫描命中 5 件，逐张目视后全部排除）。")
    w("另有 **40 个场景 / 19 件**素材是 `1920×1088`，比画布多 8 行 ⇒ 左右各约 7–8px 微边（占屏宽 0.4%，肉眼几乎不可见）——**仍是素材尺寸问题**。")
    w("")
    w("> ⚠️ 提醒：**单纯「超分」不会改变宽高比**。要让 4:3 素材真正铺满 16:9，需要的是**补边/外扩（outpaint）**；"
     "本工作区已有现成技能 `.zcode\\skills\\asset-outpaint\\`（4:3 → 16:9 向外扩图）与 `.zcode\\skills\\asset-upscale\\`（批量超分），两者通常配合使用。")
    w("")

    w("## 一、分类计数（全 680 场景）")
    w("")
    w("| 类别 | 含义 | 场景数 | 去重素材件数 |")
    w("| --- | --- | ---: | ---: |")
    w("| **A** | 素材本身非 16:9（比例差 > 1 个百分点）⇒ 运行必留边 | **325** | **200** |")
    w("| B | 16:9 且像素内有烘焙不透明黑边 | 0 | 0 |")
    w("| **C** | 准 16:9（`1920×1088`）⇒ 左右 7–8px 微边 | 40 | 19 |")
    w("| D | 16:9 且满幅正常（无黑边） | 262 | 63 |")
    w("| S | 额外：RGBA 立绘（透明边）被当背景显示 | 3 | 3 |")
    w("| E | 额外：整幅纯黑帧被当背景显示 | 14 | 1 |")
    w("| — | 合计 | 644 | 286 |")
    w("")
    w("另有 **36 个场景 `bg:[]` 为空** ⇒ 背景层被隐藏、整屏纯黑（见 `空背景场景.tsv`）。"
     "⇒「整屏纯黑」合计 = 空背景 36 ＋ 纯黑帧 14 = **50 个场景**，与「黑边」是两码事。")
    w("")

    # ---- v2 订正（用户 2026-10-02 纠偏「不是所有图都要 16:9」）：按母版判读类别再分拣 ----
    # 处置逻辑**只此一份**：从移交包的 `_gen_清单.py` import，避免两处口径漂移。
    _packdir = os.path.normpath(os.path.join(HERE, "..", "移交资源组_画幅补边"))
    sys.path.insert(0, _packdir)
    import _gen_清单 as _pk
    _mst = _pk.first(_pk.MST_LOCAL, _pk.MST_MAIN)
    _dlv = _pk.first(os.path.join(_pk.PROJ, "资源组", "美术统一_交付", "交付清单.tsv"),
                     os.path.join(_pk.ART_MAIN, "交付清单.tsv"))
    _hD, _rD = _pk.rd(_dlv)
    _hM, _rM = _pk.rd(_mst)
    _iD = [i for i, c in enumerate(_hD) if "交付相对路径" in c][0]
    _iDN = [i for i, c in enumerate(_hD) if c == "统一名"][0]
    _d2u = {r[_iD]: r[_iDN] for r in _rD if len(r) > max(_iD, _iDN)}
    _iN = [i for i, c in enumerate(_hM) if c == "统一名"][0]
    _iC = [i for i, c in enumerate(_hM) if c == "判读类别"][0]
    _u2 = {r[_iN]: r[_iC] for r in _rM if len(r) > max(_iN, _iC)}
    _cnt = {}
    _nobymap = []
    for _r in A:
        _u = _d2u.get(_r["deliv"])
        if not _u:
            _nobymap.append(_r["deliv"]); continue
        _disp, _take = _pk.disposition(_u2.get(_u, "?"), _r["ratio_class"],
                                       os.path.basename(_r["deliv"]))
        _cnt[_disp] = _cnt.get(_disp, 0) + 1
    w("## 一.5、★ 用途再分拣（v2 订正，2026-10-02）")
    w("")
    w("**上面的 A 类＝「被显示且宽高比≠16:9」，它≠「200 件都要补成 16:9 的背景」。**"
     "经与资源组母版层 `美术统一\\交付清单.tsv` 的**判读类别**交叉比对 ＋ 代表样本目视（两张接触印相表，"
     "`临时\\_audit_contact_sheet*.png`），200 件的真相是：")
    w("")
    w("| 处置 | 件数 | 说明 |")
    w("| --- | ---: | --- |")
    for _k in sorted(_cnt, key=lambda k: -_cnt[k]):
        w("| %s | **%d** | |" % (_k, _cnt[_k]))
    w("| — | **%d** | |" % sum(_cnt.values()))
    w("")
    w("**要点**：真正的全屏 4:3 背景只有 **46 件**（已复制进 `编程组\\移交资源组_画幅补边\\输入素材\\背景4比3\\`）；"
     "114 件是**事件 CG**（补边＝在关键美术周围生成内容，是否处理待用户裁决）；"
     "**20 件滚动/全景背景**（母版原始尺寸 1200×600 / 1440×544 / 800×1200，在原版 800×600 画面里放不下 ⇒ 原版是平移显示，"
     "**补边或裁切都会毁掉用途**）；13 件 `ef*`/`bld*` **特效图**（目视：光束/血溅）；5 件 `ec*` **章节题卡**；2 件 `cin*` **插入图**。")
    w("")
    w("**编程组自我更正**：v1 说「黑边不是用法问题」**只对了框选数学那一半**——`ef/bld/ec/cin` 这些"
     "**根本不是背景的图会以「场景背景」的身份被显示**，这是挑图规则（取第一个非题卡候选）＋ 上游把所有图都塞进 `bg[]` 候选"
     "造成的**用法/数据问题**；它的正确修法是**逐行演出（`op=bg`/`op=effect`）接线**，不是补边。")
    w("")
    if _nobymap:
        w("> ⚠️ 有 %d 件在交付清单里找不到对应统一名：%s" % (len(_nobymap), _nobymap[:5]))
        w("")
    # ---- v2 订正结束 ----

    # ---- A 类分组 ----
    grp = defaultdict(list)
    for r in A:
        grp[(col(r, "primary_src"), col(r, "ratio_class"))].append(r)
    tot_pc = sum(len(v) for v in grp.values())
    tot_bytes = sum(nbytes(col(r, "deliv")) for r in A)
    # 闸门（本工程纪律）：**体积全 0 = 交付层实件不可达**，属"闸门守错了层"的典型静默失败
    # （v1 就是在新 worktree 里跑出全 0 却照样落盘）。此处硬失败，不产出假报告。
    if tot_pc > 0 and tot_bytes == 0:
        print("[FATAL] A 类 %d 件体积全为 0 ⇒ 交付层实件不可达（根=%s）；拒绝落盘" % (tot_pc, ART))
        return
    missing = [col(r, "deliv") for r in A if nbytes(col(r, "deliv")) == 0]
    if missing:
        print("[FATAL] A 类有 %d 件取不到实件：%s" % (len(missing), missing[:5])); return
    tot_px = sum((int(col(r, "aw") or 0) * int(col(r, "ah") or 0)) for r in A)
    c_bytes = sum(nbytes(col(r, "deliv")) for r in C)
    w("## 二、A 类名单：素材非 16:9 ⇒ **超分 / 补边候选**（共 %d 件）" % tot_pc)
    w("")
    w("**去重后文件总大小 = %s 字节 = %.2f MiB（%.2f MB）**；总像素 %.2f 亿 px；平均 %.0f KiB/件"
      "（最大 %.0f KiB / 最小 %.0f KiB）。C 类 %d 件另计 %s 字节 = %.2f MiB。**A+C 合计 %.2f MiB。**"
      % ("{:,}".format(tot_bytes), mib(tot_bytes), tot_bytes / 1e6, tot_px / 1e8,
         tot_bytes / tot_pc / 1024, max(nbytes(col(r, "deliv")) for r in A) / 1024,
         min(nbytes(col(r, "deliv")) for r in A) / 1024,
         len(C), "{:,}".format(c_bytes), mib(c_bytes), mib(tot_bytes + c_bytes)))
    w("")
    w("> 体积口径＝`资源组\\美术统一_交付\\<交付路径>` 下**实件**的字节数（脚本按路径直接 `getsize`，可复算）。")
    w("> 结论：这 200 件加起来只有约 100 MiB ⇒ **存储成本可忽略，代价在算力（逐件补边/超分）**。")
    w("")
    w("> 说明：`ot/otr/ota/otp` 的 4:3 素材按美术裁决 **D1**「不放大、居中留边」是有意的，"
     "但根因仍是「素材非 16:9」；竖图 / 超宽 / 1:1 的留边更大。")
    w("")
    w("| 源 | 比例类 | 件数 | 场景数 | 体积 MiB |")
    w("| --- | --- | ---: | ---: | ---: |")
    order = sorted(grp.keys(), key=lambda k: (-sum(nbytes(col(r, "deliv")) for r in grp[k]), k))
    for src, rc in order:
        items = grp[(src, rc)]
        ns = sum(int(col(r, "scenes_n") or 0) for r in items)
        nb = sum(nbytes(col(r, "deliv")) for r in items)
        w("| `%s` | %s | %d | %d | %.1f |" % (src, rc, len(items), ns, mib(nb)))
    w("| **合计** | — | **%d** | **%d** | **%.1f** |" % (
        tot_pc, sum(int(col(r, "scenes_n") or 0) for r in A), mib(tot_bytes)))
    w("")
    for src, rc in order:
        items = sorted(grp[(src, rc)], key=lambda r: (-int(col(r, "scenes_n") or 0), col(r, "asset")))
        ns = sum(int(col(r, "scenes_n") or 0) for r in items)
        w("### %s × %s —— %d 件 / %d 场景" % (src, rc, len(items), ns))
        w("")
        w("| # | 素材（story_assets 名） | 交付层路径 | 原始尺寸 | 场景数 |")
        w("| ---: | --- | --- | --- | ---: |")
        for i, r in enumerate(items, 1):
            w("| %d | `%s` | `%s` | %s×%s | %s |" % (
                i, col(r, "asset"), col(r, "deliv"), col(r, "aw"), col(r, "ah"), col(r, "scenes_n")))
        w("")

    # ---- C 类 ----
    w("## 三、C 类：准 16:9（`1920×1088`）左右微边（%d 件）" % len(C))
    w("")
    if C:
        keys = list(C[0].keys())
        w("| " + " | ".join(keys) + " |")
        w("| " + " | ".join(["---"] * len(keys)) + " |")
        for r in C:
            w("| " + " | ".join(("`%s`" % r.get(k, "")) if k in ("asset", "deliv") else r.get(k, "") for k in keys) + " |")
    w("")
    w("成因：素材高 1088（比画布多 8 行）。落框 `k=min(1920/1920,1080/1088)=0.9926` ⇒ `w=1905,h=1080,x=7`，左右各 7–8px。")
    w("")

    # ---- 影片 ----
    w("## 四、影片（视频）素材名单")
    w("")
    w("- 工程内**物理影片文件 24 个**（**逻辑影片 17 支**）；另有 12 个 PSV 源 `.usm` 未转码、本工程不消费。")
    w("- 实测（`ffprobe`，非按扩展名猜）：`.mpg` 全为 **MPEG-1 PS + MP2**；`.mp4` 全为 **H.264/AAC**。")
    w("- **无一支是 1920×1080 原生。**")
    w("- **游戏目前不播任何影片**：`build_story.py` 对 `kind==\"movie\"` 只记数不取件（全六源实算 **2 条 / 2 场景**：`otv_M09_01`、`otv_P03_01D`），"
     "`ui_story.tjs` 无 `MoviePlay` 实现；`videoprobe.txt` 探针（非成品功能）实测 **960×544 MPEG-1 可 open、`.mp4` 被拒（Unknown video format extension）**。")
    w("")
    non169 = [r for r in V if "否" in col(r, "是否16:9(1920x1080画布)")]
    w("### 非 16:9 的影片（%d 支，需 pillarbox 或重制）" % len(non169))
    w("")
    w("| 逻辑名 | 类别/用途 | 分辨率 | 宽高比 | 时长(s) | 实际文件 |")
    w("| --- | --- | --- | --- | ---: | --- |")
    for r in sorted(non169, key=lambda r: (col(r, "分辨率"), col(r, "逻辑名"))):
        w("| `%s` | %s | %s | %s | %s | `%s` |" % (
            col(r, "逻辑名"), col(r, "类别/用途"), col(r, "分辨率"), col(r, "宽高比"),
            col(r, "时长秒"), col(r, "实际文件绝对路径")))
    w("")
    w("### 全部影片一览（%d 支）" % len(V))
    w("")
    w("| 逻辑名 | 用途 | 分辨率 | 容器/编码 | 时长(s) | 现是否播放 |")
    w("| --- | --- | --- | --- | ---: | --- |")
    for r in V:
        w("| `%s` | %s | %s | %s / %s | %s | %s |" % (
            col(r, "逻辑名"), col(r, "类别/用途"), col(r, "分辨率"), col(r, "容器"), col(r, "视频编码"),
            col(r, "时长秒"), col(r, "游戏当前是否播放")))
    w("")
    w("（完整 18 列见 `影片清单.tsv`；侦察明细见 `报告_影片.md`。）")
    w("")

    # ---- 用法侧发现 ----
    w("## 五、顺带查出的「用法 / 数据」侧问题（不是黑边，但同样会被看成黑屏）")
    w("")
    w("1. **纯黑帧被当背景**：`bg__bg_black.jpg`（整幅纯黑）在 **14 个 `otv_M*` 场景**里排在 bg 候选**第 0 位**，"
     "其后还有真实背景（如 `mis71.jpg`），而挑图规则取「第一个非题卡」⇒ **整屏纯黑**。倾向是**候选顺序错误**，不是有意黑场。")
    w("2. **RGBA 立绘被当背景**：`kur01d.png` / `aki02b.png` / `mas01e.png` 各 1 个 `np` 场景，"
     "它们本是**带透明通道的立绘**，透明边在黑板底上显黑。属**上游 `assets[]` 归类问题**。")
    w("3. **36 个场景 `bg:[]` 为空** ⇒ 背景层被隐藏、整屏纯黑（多为序文/转场）。")
    w("4. **181 个场景的 bg 候选全是「章节题卡」（`ec<数字>`）** ⇒ 挑图只能兜底显示题卡而非场景背景"
     "（其中 171 个满幅、10 个 4:3 会留边）。可能是上游只抽到了题卡，也可能是这些场景本就该显示题卡——**需与资源组确认**。")
    w("")
    w("> 上述 1/2/4 都不是「黑边」，且**大部分会随着「逐行演出（`op=bg` 逐行切换）」接线而自然解决或改写**；"
     "本轮只做审计，未改动任何素材与逻辑。")
    w("")

    w("## 六、给「统一超分」的建议口径")
    w("")
    w("| 类别 | 该怎么处理 | 件数 |")
    w("| --- | --- | ---: |")
    w("| A 类 4:3（1600×1200 / 1934×1450 等） | 比 16:9 **更窄** ⇒ 二选一：**补左右**（1600×1200 → 2133×1200，+33% 宽，画面全留、左右由 AI 生成）"
      "／**裁上下**（1600×1200 → 1600×900，丢 25% 高、零生成内容） | 178 件 |")
    w("| A 类 2:1（2400×1200 等） | 比 16:9 **更宽** ⇒ **裁左右**（2400×1200 → 2133×1200，只裁 11% 宽，最省）"
      "／或**补上下**（2400×1200 → 2400×1350，+12.5% 高） | 8 件 |")
    w("| A 类超宽（2880×1088 / 2160×1088） | 同样**更宽** ⇒ 裁左右要丢 **33%／18%** 宽，补上下要 **+49%／41%** 高，**两条路都重、需逐一目视** | 2 件 |")
    w("| A 类竖图 2:3 / 1:1 | 比 16:9 **窄得多** ⇒ 补左右要 **+167%／+78%** 宽（几乎全靠 AI 画），裁上下要丢 **62%／44%** 高；"
      "**竖图本不该铺满横屏**，建议保留留边或单独评估 | 12 件 |")
    w("| C 类 1920×1088 | **裁掉多出的 8 行**（或补到 1080 的倍数）即可满幅，成本极低 | 19 件 |")
    w("| 影片 4:3（800×600） | 需 pillarbox（保留留边）或用 AI 重制 16:9 | 6 支 |")
    w("| 影片 960×544（PSV 原生） | 非精确 16:9；先 1:1 居中留边，将来 AI 超分替换 | 9 支（7 ED ＋ 2 场景影片） |")
    w("| 影片 1280×720 | 尺寸是 16:9，**只是分辨率低** ⇒ 单纯超分即可 | 2 支 |")
    w("")
    w("**优先顺序建议**：① C 类 19 件（裁 8 行，几乎零成本、立刻消掉 40 个场景的微边）→ "
     "② A 类 4:3 的 159 件（补边，收益最大）→ ③ 超宽 10 件（裁上下）→ ④ 影片。")
    w("")

    w("## 七、方法与环境（可复算）")
    w("")
    w("- **逐场景归属**：`逐场景背景归属.tsv`（644 行，含每场景的选框、渲染框、四边黑边像素数）")
    w("- **空背景**：`空背景场景.tsv`（36 行）")
    w("- **素材级全表**：`超分候选_背景A类.tsv`（200 行）、`准16比9微边_C类.tsv`（19 行）")
    w("- **证据留档**（未入库的 gitignore 目录）：`子代理工作区\\ISSUE-20261001-18\\bg_blackbar\\`"
     "（`asset_agg.tsv` 286 件、`asset_edge_scan.tsv` 逐件边缘扫描、`thumbs\\` 14 张目视缩略图）与 `...\\videos\\`")
    w("- **烘焙黑边检测**：逐行/逐列判「整行整列 `max(R,G,B)<=16`」从边缘向内连续；命中 5 件后**逐张裁边目视**，"
     "确认为「整幅纯黑帧 / 透明 alpha 边 / 深色画面内容」，**真正的不透明烘焙黑边 = 0**。")
    w("- 抽样目视 14 张（含纯黑帧、3 张透明立绘、渐变转场、夜景暗内容、准 16:9、超宽、竖图、4:3 各代表），**全量统计与目视无矛盾**。")
    w("")

    p = os.path.join(HERE, "结论_名单.md")
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("[ok] %s  (%d 行)" % (p, len(out)))
    print("[stats] A=%d 件 / C=%d 件 / 空背景=%d / 逐场景=%d / 影片=%d" % (len(A), len(C), len(E), len(S), len(V)))


if __name__ == "__main__":
    main()
