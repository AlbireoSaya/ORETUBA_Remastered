#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
场景级「演出挂接表」生成器   (ISSUE-20260930-04 / greta-staging)
================================================================================
**只读** 结构化剧本 + 美术映射表 + 素材账；产出三张表（交编程组）：

  1. `BGM曲名表.tsv`         —— BGM 编号 → 曲名（**来源＝库内曲名位图**
     `ot/sys/ot_mc_bgmNN.png` / `ota/sys/ota_gl_bgmNN.png`，逐张目读；
     并与官方 OST（MusicBrainz）逐条交叉，分歧处标注）。
  2. `挂接_立绘.tsv`         —— 712 场景 × 出场角色 → 立绘族 + 可用件数 + 源侧是否已有引用。
     粒度上限＝**角色级**（基名/表情/切换时机的证据在数据里不存在，见说明文档 §边界）。
  3. `挂接_BGM.tsv`          —— 712 场景 → 推荐主曲 + 候选池 + 依据等级
     （`源侧実引用` / `人格段规则` / `共通段`）。

**关键判据（都有证据，不是猜）**
  - **BGM 编号分段＝人格分区**：`01–11`=鹰志(HAWK)、`21–32`=鹫介(EAGLE)、`41–54`=隼人(FALCON)、
    `61–65`=伽鲁炟(GARUDA)、`71–74`=ヨージ(CONDOR)、`81–96`=共通/其他。
    依据：① 五首 `Main Theme "HAWK/EAGLE/FALCON/GARUDA/CONDOR"` 各起一段（曲名位图 + 官方 OST）；
    ② `otv` 源侧锚点印证——「鹫介」场景引 `02X`、「鹰志」场景引 `00X`（见 `挂接_BGM.tsv` 的 `源侧実引用` 行）。
  - **立绘族 ↔ 角色**：取 `资源组\美术\立绘差分图谱.md` §1.3「代号→角色」推定表（每条有语音前缀共现证据）。
  - **主角五人格无立绘族**：`立绘差分索引.tsv` 40 个 family 中无 tak/hay/was/yoj/gal 前缀（源侧确认）。

用法：python -X utf8 build_staging_tables.py [--data-root <主工作区>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys

GAME = "我们没有翅膀——格雷塔迦露德与柳木原"
REL_RES = os.path.join("工程", GAME, "资源组")
SOURCES = ["ot", "otr", "ota", "otp", "otv", "np"]

# ---------------------------------------------------------------- BGM 曲名（目读位图）
# 来源：`krkr素材库\{ot,ota}\sys\*_bgmNN.png`（2036×37 / 1900×37 RGBA 文字条）逐张目读；
# 与官方 OST（MusicBrainz `94cc7399-…` 俺たちに翼はない OST / `99665831-…` AfterStory OST）
# 逐条交叉。凡两者不一致者，`曲名` 取**官方写法**并在 `分歧` 列注明位图读法。
TITLES_OT = {
    1: ('Main Theme "HAWK"', ""),
    2: ("想像力の豊かな人間になりたいと思うんだ", ""),
    3: ("こんなにも静かな夜に気の狂いそうなわたし", ""),
    4: ("君がおはようと言ってくれた今日はいい日", ""),
    5: ("見上げれば１２月の白い空はどこまでも高く", ""),
    6: ("世界が平和でありますように", ""),
    7: ("彼女がいいように僕を振りまわすという幸福", ""),
    8: ("擦れちがう会話も君の笑顔を招く要素だから", ""),
    9: ("夢の扉をふんわり撫でてゆく陽だまり", ""),
    10: ("首の後ろをどんより這いのぼってくる塊", ""),
    11: ("夕暮れの校庭ではしゃぐ君を見詰める窓辺", ""),
    21: ('Main Theme "EAGLE"', ""),
    22: ("きんきんクールビューティー", ""),
    23: ("いちごの国からこんにちは", ""),
    24: ("ロッケンロールみんなのえーりん", ""),
    25: ("アーバン・ワーキン・おねえさん", ""),
    26: ("いい天気っすねえ", ""),
    27: ("楽しんでるぅ？", ""),
    28: ("やばいよやばいよ", ""),
    29: ("なんですかこの空気", ""),
    30: ("泣いてなんかないやい", ""),
    31: ("ひとはなぜ寂しさを感じるのでしょうか", ""),
    32: ("マーベラスハウス", ""),
    41: ('Main Theme "FALCON"', ""),
    42: ("ナルキッス", ""),
    43: ("あい☆とら", ""),
    44: ("Julie＆Anna＆時男", "位图作半角 `&`，官方为全角 `＆`"),
    46: ("ヘテロクロミア", ""),
    47: ("Love Letter from ABYSS", ""),
    48: ("ギバラ闊歩 in The Night", "位图 `In the night`，官方 `in The Night`"),
    49: ("420 (four-twenty)", ""),
    50: ("You can fill in the blanks", ""),
    51: ("Stupid Passion", ""),
    52: ("Affrican", "位图字形作 `African`，官方拼作 `Affrican`"),
    53: ("おまえのテーマ", ""),
    54: ("フェニックスの頌歌", ""),
    61: ('Main Theme "GARUDA"', ""),
    62: ("指針盤仕掛けのロジック", ""),
    63: ("路地裏RAVE UP!", "位图作「裏路地RAVE UP!」（首尾两字互换，3× 放大复核），官方/OST 作「路地裏」"),
    64: ("禁じられた遊び", ""),
    65: ("赤い帳", ""),
    71: ('Main Theme "CONDOR"', ""),
    72: ("ぽぽぽぽぽぽぽ", ""),
    74: ("おれわりとしょんぼりしちゃった", ""),
    81: ("勇者行進曲 ～from WING QUEST Ⅰ～", ""),
    82: ("勇者行進曲 Oretsuba MIX", ""),
    83: ("勇者戦舞曲 Oretsuba MIX", ""),
    84: ("リウマチの天使", ""),
    86: ("なんかラブホの有線とかで流れてそうな曲", ""),
    87: ("The Closed World", ""),
    88: ("水の底で見た光", ""),
    89: ("Jewelry tears ～instrumental～", ""),
    91: ("Jewelry tears", ""),
    92: ("Sky Sanctuary", ""),
    93: ("Eternal sky", ""),
    94: ("微笑みジェノサイド", ""),
    95: ("NEON Sign", ""),
    96: ("光陰の海原", ""),
}
TITLES_OTA = {
    1: ("Eternal Prelude", ""),
    2: ("Alice in Yanagiha land", ""),
    3: ("ヤマトナデシコ残念系", ""),
    4: ("CHACO GROOVY", ""),
    5: ("Through The Night", ""),
    6: ("放課後の小娘たち", ""),
    7: ("Big Cool Favorite", ""),
    8: ("Passing year, Coming year", "MusicBrainz 作「Passing year,Coming year」（无空格）；取位图写法"),
    9: ("聖なる夜は終わらない", ""),
    10: ("Cross Illusion ～instrumental～", ""),
    11: ("Cross Illusion", ""),
    12: ("migratory bird", ""),
}

# 编号分段 = 人格分区（依据：五首 Main Theme 各起一段 + otv 锚点印证，见模块头注释）
BLOCKS = [
    (1, 11, "鹰志", 'HAWK'),
    (21, 32, "鹫介", 'EAGLE'),
    (41, 54, "隼人", 'FALCON'),
    (61, 65, "伽鲁炟", 'GARUDA'),
    (71, 74, "ヨージ", 'CONDOR'),
    (81, 99, "共通", ""),
]
# 主角五人格（无立绘族）+ 其异名 → 人格名
PROTAG = {
    "鹰志": "鹰志", "鷹志": "鹰志", "タカシ": "鹰志", "汰架示": "鹰志",
    "鹫介": "鹫介", "鷲介": "鹫介", "ヨージ": "ヨージ", "小鹰志": "ヨージ",
    "隼人": "隼人", "羽田隼人": "隼人", "ハヤブサ": "隼人",
    "ガルーダ": "伽鲁炟", "伽鲁炟": "伽鲁炟", "かるら": "伽鲁炟",
    "伽楼羅": "伽鲁炟", "迦楼罗": "伽鲁炟", "伊丹迦楼罗": "伽鲁炟",
}

# 立绘族 ↔ 角色：取 `美术\立绘差分图谱.md` §1.3（每条有语音前缀共现证据）
FAMILY_ROLE = {
    "ai": "亜衣", "asu": "明日香", "hiy": "日和子", "kob": "小鳩", "miy": "京",
    "nar": "鳴", "eri": "英里子", "kin": "紀奈子", "har": "春恵", "kaz": "和馬",
    "kab": "翔", "kur": "蔵人", "mas": "高内", "yuu": "優", "sak": "咲夜",
    "ten": "狩男", "chi": "チケドン", "ban": "バニィＤ", "ari": "アリス",
    "lr": "ＬＲ２００１", "pur": "プラチナ", "mar": "マルチネス", "men": "メンマ",
    "mit": "満夜", "kyo": "狂夜", "kaa": "翔（カケル写形·低置信）", "mis": "美咲（待确证）",
}
# 角色名（中文/日文/异名） → 族
ROLE2FAM = {}
for fam, role in FAMILY_ROLE.items():
    ROLE2FAM.setdefault(role.split("（")[0], fam)
ALIAS = {
    "亚衣": "ai", "明日香": "asu", "日和子": "hiy", "小鸠": "kob", "京": "miy",
    "鸣": "nar", "凤鸣": "nar", "英里子": "eri", "纪奈子": "kin", "春惠": "har",
    "和马": "kaz", "翔": "kab", "凤凰寺翔": "kab", "藏人": "kur", "高内": "mas",
    "优": "yuu", "咲夜": "sak", "狩男": "ten", "奇肯多": "chi", "巴尼Ｄ": "ban",
    "爱丽丝": "ari", "美咲": "mis", "林同学": "mis", "林さん": "mis",
    "亜衣": "ai", "小鳩": "kob", "鳴": "nar", "鳳鳴": "nar", "紀奈子": "kin",
    "春恵": "har", "和馬": "kaz", "蔵人": "kur", "優": "yuu", "チケドン": "chi",
    "バニィＤ": "ban", "アリス": "ari", "プラチナ": "pur", "マルチネス": "mar",
    "メンマ": "men", "満夜": "mit", "狂夜": "kyo", "カケル": "kaa",
    "フェニックス": "kab", "ハリュー": "kur", "スパロウ": "miy", "レイヴン": "kur",
    "ガルーダ": None, "伽鲁炟": None, "伽楼羅": None, "迦楼罗": None,
}
NOISE = {"旁白", "声音", "声", "男人的声音", "女学生", "女子学生", "女生徒", "侍女Ａ",
         "全人類", "ゲーム内音声", "駅アナウンス", "电视声音", "上课铃声", "呼吸声",
         "温柔的声音", "梦中的声音", "制服を着た女", "女装の男", "变态"}


def find_main_workspace(cli):
    if cli:
        return os.path.abspath(cli)
    env = os.environ.get("GALGAME_MAIN")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        cur = os.path.dirname(cur)
        if os.path.isfile(os.path.join(cur, "工程", GAME, "资源组", "krkr素材库", "资源总账.json")):
            return cur
    raise SystemExit("[FATAL] 未找到主工作区，请用 --data-root 指定")


def assert_in_checkout(path):
    here = os.path.dirname(os.path.abspath(__file__))
    checkout = here
    for _ in range(4):
        if os.path.isdir(os.path.join(checkout, ".git")) or os.path.isfile(os.path.join(checkout, ".git")):
            break
        checkout = os.path.dirname(checkout)
    p = os.path.abspath(path)
    if not (p == checkout or p.startswith(checkout + os.sep)):
        raise SystemExit(f"[FATAL] 产物路径不在本 checkout 内，拒绝写入：{p}")
    return p


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        if rows:
            w.writerows(rows)


def bgm_block(num):
    for lo, hi, who, theme in BLOCKS:
        if lo <= num <= hi:
            return who, theme
    return "其他", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    a = ap.parse_args()
    data = find_main_workspace(a.data_root)
    res = os.path.join(data, REL_RES)
    here = os.path.dirname(os.path.abspath(__file__))
    out = assert_in_checkout(os.path.join(here, "..", "交接编程组"))
    os.makedirs(out, exist_ok=True)

    # ---------------- 1. BGM 曲名表 ----------------
    trows = []
    for src, titles, pat in (("ot", TITLES_OT, "ot_mc_bgm%02d.png"),
                             ("ota", TITLES_OTA, "ota_gl_bgm%02d.png")):
        for num, (title, diff) in sorted(titles.items()):
            trows.append(dict(源=src, 编号="%02d" % num, 曲名=title,
                              位图文件=os.path.join(src, "sys", pat % num).replace("\\", "/"),
                              分段=bgm_block(num)[0], 主主题=bgm_block(num)[1], 分歧=diff))
    write_tsv(os.path.join(out, "BGM曲名表.tsv"), trows,
              ["源", "编号", "曲名", "位图文件", "分段", "主主题", "分歧"])

    # **BGM 统一名映射**（`BGM统一清单.tsv`：源文件 → 统一名）；编程组取件一律用统一名
    uni = {}
    up = next((x for x in (os.path.join(here, "..", "BGM统一清单.tsv"),
                           os.path.join(res, "BGM统一清单.tsv")) if os.path.isfile(x)), "")
    if up:
        for r in read_tsv(up):
            if r["处置"].startswith("保留"):
                uni[(r["来源"], r["原文件"])] = r["统一名"]
            else:
                uni[(r["来源"], r["被替代件"])] = r["统一名"]

    # ---------------- 1b. BGM 实测文件名（**候选一律取自这里，不按公式拼**） ----------------
    # 素材库命名并不统一：成对曲为 `NN a/b`，单档曲只有 `NN`（如 `ot_bgm52.ogg`、
    # `ot_bgm91.ogg`），且各源编号有大量空洞（`ot` 无 45/85/90/97；`otp` 仅 25 个编号）。
    # 按公式 `src_bgm%02da.ogg` 拼名会指向不存在的文件（一审实测 70 行推荐 / 410 行备选）。
    bgm_files = collections.defaultdict(lambda: collections.defaultdict(list))
    all_bgm_names = set()
    for e in json.load(open(os.path.join(res, "krkr素材库", "资源总账.json"),
                            encoding="utf-8"))["entries"]:
        if e["kind"] != "bgm":
            continue
        all_bgm_names.add(e["filename"])
        m = re.search(r"bgm(\d+)", e["filename"])
        if m:
            bgm_files[e["source"]][int(m.group(1))].append(e["filename"])

    # ---------------- 2. 立绘可用件（族 → 统一名清单） ----------------
    maprows = read_tsv(os.path.join(res, "交接编程组", "素材库到统一名.tsv"))
    fam_unames = collections.defaultdict(list)
    for r in maprows:
        if r["类别"] != "立绘" or not r["统一名"]:
            continue
        m = re.match(r"^([a-z]+?)(\d+)([a-z]*)(?:_alt\w+)?\.png$", r["统一名"])
        if m:
            fam_unames[m.group(1)].append(r["统一名"])

    # ---------------- 3. 逐场景挂接 ----------------
    scenes = []
    for src in SOURCES:
        for line in open(os.path.join(res, "剧本", "scene_%s.jsonl" % src), encoding="utf-8"):
            scenes.append(json.loads(line))
    spine = json.load(open(os.path.join(res, "剧本", "spine.json"), encoding="utf-8"))
    act_of = {}
    for act in spine.get("acts", []):
        for sid in act.get("scene_ids", act.get("scenes", []) or []):
            act_of[sid] = act.get("name") or act.get("title") or ""
    chr_ref_of = collections.defaultdict(set)
    bgm_ref_of = collections.defaultdict(list)
    for o in scenes:
        for x in o["assets"]:
            if x["kind"] == "chr" and x.get("out_relpath"):
                nm = x["out_relpath"].split("/")[-1]
                nm = re.sub(r"^[a-z]+_", "", nm)      # 去源前缀
                nm = re.sub(r"^st_", "", nm)          # otv 立绘的 `st_` 前缀
                fam = nm.split("_")[0]
                if fam not in FAMILY_ROLE:
                    m = re.match(r"^([a-z]+?)\d", nm)
                    fam = m.group(1) if m else fam
                if fam in FAMILY_ROLE:
                    chr_ref_of[o["scene_id"]].add(fam)
            if x["kind"] == "bgm" and x.get("out_relpath"):
                bgm_ref_of[o["scene_id"]].append(x["out_relpath"].split("/")[-1])

    art_rows, bgm_rows = [], []
    # np 锚点频率：np 与 ot 共用编号库（np 全部 stem ⊆ ot，跨源同 stem 为同一录音），
    # 故 np 场景实际使用的曲号可作为 ot 编号库的**用法证据**（日常/紧张/收束）。
    np_freq = collections.Counter()
    for o in scenes:
        if o["source"] != "np":
            continue
        for x in o["assets"]:
            if x["kind"] == "bgm" and x.get("out_relpath"):
                m = re.search(r"bgm(\d+)", x["out_relpath"].split("/")[-1])
                if m:
                    np_freq[int(m.group(1))] += 1
    NP_DAILY = [n for n, _c in np_freq.most_common() if n in range(1, 12)][:3]
    prev_roles = {}
    for o in scenes:
        sid = o["scene_id"]
        src = o["source"]
        # 角色：cast 过滤白名单，逐名映射到族；主角人格单列
        roles, prot = [], []
        for c in o.get("cast") or []:
            c = c.strip()
            if not c or c in NOISE:
                continue
            if c in ALIAS and ALIAS[c]:
                fam = ALIAS[c]
                if fam not in [x["族"] for x in roles]:
                    roles.append(dict(角色=c, 族=fam, 可用件数=len(fam_unames.get(fam, [])),
                                      示例件=(sorted(fam_unames.get(fam, [])) or [""])[0]))
            elif c in PROTAG and PROTAG[c]:
                if PROTAG[c] not in prot:
                    prot.append(PROTAG[c])
        for r in roles:
            推定 = r["族"] in ("mis", "kaa")
            art_rows.append(dict(
                场景id=sid, 源=src, 幕=act_of.get(sid, ""), 阶段=o.get("phase") or "",
                章节标题=o.get("title_cn") or "", 角色=r["角色"], 立绘族=r["族"],
                可用件数=r["可用件数"], 示例件=r["示例件"],
                依据可靠度=("推定" if 推定 else "有据"),
                源侧已有立绘引用=("是" if r["族"] in chr_ref_of.get(sid, set()) else ""),
                证据=("**推定**：`立绘差分图谱.md` 把 `%s` 标为「待判读」（无对应语音前缀确证）；"
                      "otv 有该族引用可佐证，须 vision 目视确认" % r["族"]) if 推定 else
                     "立绘差分图谱 §1.3 代号→角色（语音前缀共现，非目视）"))
        # 主角无立绘族：仍出一行，供编程组显式知道"此处需另作处理"
        for p in prot:
            art_rows.append(dict(场景id=sid, 源=src, 幕=act_of.get(sid, ""), 阶段=o.get("phase") or "",
                                 章节标题=o.get("title_cn") or "", 角色=p, 立绘族="（无·主角人格）",
                                 可用件数=0, 示例件="", 依据可靠度="源侧确认",
                                 源侧已有立绘引用="",
                                 证据="立绘差分索引 40 family 无 tak/hay/was/yoj/gal 前缀（源侧确认）"))

        # 旁白-only 等无角色信号的场景：沿用同一脚本/同一幕的前一场角色（**建议值**，非源侧数据）
        if not roles and not prot:
            carry = prev_roles.get((src, o.get("script"))) or prev_roles.get(("_act", act_of.get(sid, "")))
            if carry:
                for r in carry:
                    art_rows.append(dict(场景id=sid, 源=src, 幕=act_of.get(sid, ""),
                                         阶段=o.get("phase") or "", 章节标题=o.get("title_cn") or "",
                                         角色=r["角色"], 立绘族=r["族"], 可用件数=r["可用件数"],
                                         示例件=r["示例件"], 依据可靠度="推定（兜底）",
                                         源侧已有立绘引用="",
                                         证据="**兜底建议**：本场 cast 无角色信号（旁白-only），沿用同脚本上一场角色"))
        if roles or prot:
            keep = [dict(角色=r["角色"], 族=r["族"], 可用件数=r["可用件数"], 示例件=r["示例件"])
                    for r in roles]
            prev_roles[(src, o.get("script"))] = keep
            prev_roles[("_act", act_of.get(sid, ""))] = keep

        # BGM：人格段 + 场景类型 → 推荐主曲 + 候选池（**文件名一律取自素材库实测清单**）
        who = next((p for p in prot), None) or "共通"
        anchored = bgm_ref_of.get(sid, [])
        avail = bgm_files.get(src, {})
        note_avail = "；该源实测 %d 个编号 / %d 件" % (len(avail), sum(len(v) for v in avail.values()))
        if anchored:
            rec, rest = anchored[0], anchored[1:]
            grade = "源侧実引用"
            rule = ("源侧脚本 BGM 指令 %d 条；推荐＝第 1 条，其余 %d 条为同场候选；"
                    "**源侧真序未恢复**（otv 按 `Tasktype \"BgmPlay\"` 的 Task 序、np 按 `.bs5` 内 `_PlayBGM` 调用序，"
                    "均尚未与文本槽对齐）" % (len(anchored), len(rest)))
        elif src == "ota":
            # AfterStory 专属曲：用其自有 01–12（有曲名位图）中**实际存在**的编号
            pool_nums = [n for n in sorted(TITLES_OTA) if n in avail]
            rec_n = 1 if 1 in pool_nums else pool_nums[0]
            rec = avail[rec_n][0]
            rest = [avail[n][0] for n in pool_nums if n != rec_n]
            grade = "AfterStory专属曲"
            rule = ("AfterStory 专属曲（01–12 均有曲名位图，实测存在 %d 个编号）；"
                    "推荐 %02d｜%s" % (len(pool_nums), rec_n, TITLES_OTA[rec_n][0])) + note_avail
        else:
            blk = next((b for b in BLOCKS if b[2] == who), BLOCKS[-1])
            lo, hi = blk[0], blk[1]
            inblk = sorted(n for n in avail if lo <= n <= hi)
            if not avail:
                raise SystemExit("[FATAL] %s 在素材库里没有任何 bgm（无法给 %s 推荐）"
                                 % (src, sid))
            if inblk:
                pool_nums, grade = inblk, ("人格段规则" if who != "共通" else "共通段")
                seg_note = "本段实测 %d 个编号" % len(inblk)
            else:
                pool_nums = sorted(avail)
                grade = "段外退让"
                seg_note = ("**该源在第 %d–%d 段无任何曲目**，退到本源可用集（%d 个编号）"
                            % (lo, hi, len(pool_nums)))
            if o.get("phase") == "结局" and 91 in pool_nums:
                rec_n, why = 91, "阶段=结局 → 91「Jewelry tears」（ED 曲）"
            elif o.get("phase") == "结局":
                rec_n = pool_nums[-1]
                why = ("阶段=结局，但本源**无 91「Jewelry tears」**（实测编号集不含 91），"
                       "退到本段末曲作收束")
            elif o.get("phase") == "序":
                rec_n, why = pool_nums[0], "阶段=序 → 本段首曲（主主题）"
            elif NP_DAILY and NP_DAILY[0] in pool_nums:
                rec_n, why = (NP_DAILY[0],
                              "日常场景 → %02d 系（np 锚点实测最高频号；与 ot 共用编号库，用法可迁移）"
                              % NP_DAILY[0])
            else:
                rec_n, why = pool_nums[0], "取本段首曲（无更强判据）"
            rec = avail[rec_n][0]
            rest = [avail[n][0] for n in pool_nums if n != rec_n]
            rule = ("人格段规则：%s 段（%d–%d，主主题 %s）；%s；%s%s"
                    % (who, lo, hi, blk[3] or "—", why, seg_note, note_avail))
        bgm_rows.append(dict(场景id=sid, 源=src, 幕=act_of.get(sid, ""), 阶段=o.get("phase") or "",
                             章节标题=o.get("title_cn") or "", 主视角人格=who,
                             依据等级=grade, 推荐主曲=rec,
                             推荐统一名=" ".join(uni.get((src, rec), "") and [uni[(src, rec)]] or []),
                             备选数=len(rest),
                             判据=rule + ("" if src != "np" else
                                         "；⚠️ **np 的候选序为字母序、非播放序**，"
                                         "播放序见 `BGM切换点.tsv`"),
                             备选=(" ".join(rest))[:400],
                             备选统一名=(" ".join(uni[(src, f)] for f in rest if (src, f) in uni))[:400]))

    write_tsv(os.path.join(out, "挂接_立绘.tsv"), art_rows,
              ["场景id", "源", "幕", "阶段", "章节标题", "角色", "立绘族", "可用件数",
               "示例件", "依据可靠度", "源侧已有立绘引用", "证据"])
    write_tsv(os.path.join(out, "挂接_BGM.tsv"), bgm_rows,
              ["场景id", "源", "幕", "阶段", "章节标题", "主视角人格", "依据等级",
               "推荐主曲", "推荐统一名", "备选数", "判据", "备选", "备选统一名"])

    # ---------------- 自证闸门（**必须能失败**）：写出的每个 BGM 文件名都要在素材库实测清单里
    bad_bgm = sorted({f for r in bgm_rows for f in ([r["推荐主曲"]] + r["备选"].split())
                      if f and f not in all_bgm_names})
    if bad_bgm:
        raise SystemExit("[FATAL] 推荐/备选里有 %d 个文件名不在素材库：%s"
                         % (len(bad_bgm), bad_bgm[:10]))
    empty_rec = [r["场景id"] for r in bgm_rows if not r["推荐主曲"]]
    if empty_rec:
        raise SystemExit("[FATAL] %d 个场景无推荐主曲：%s" % (len(empty_rec), empty_rec[:10]))
    # 立绘：族代号必须来自 FAMILY_ROLE（除主角占位行）
    bad_fam = sorted({r["立绘族"] for r in art_rows
                      if not r["立绘族"].startswith("（无") and r["立绘族"] not in FAMILY_ROLE})
    if bad_fam:
        raise SystemExit("[FATAL] 立绘族不在证据表内：%s" % bad_fam)
    # otv 的「源侧已有立绘引用」列必须非全空（曾因 `st_` 前缀误判而恒空）
    otv_yes = sum(1 for r in art_rows if r["源"] == "otv" and r["源侧已有立绘引用"] == "是")
    if otv_yes == 0:
        raise SystemExit("[FATAL] otv 的「源侧已有立绘引用」全为空 —— 前缀解析有误")

    # 实测：源侧 chr 引用（族级）与该场 cast（映射到族）的**包含关系**（两个方向都算）
    stat_sup = {}
    for s_src in ("otr", "otv", "np"):
        c_pairs = r_pairs = notin = 0
        for o in scenes:
            if o["source"] != s_src:
                continue
            cf = chr_ref_of.get(o["scene_id"], set())
            rs = {ALIAS[c.strip()] for c in (o.get("cast") or []) if ALIAS.get(c.strip())}
            c_pairs += len(cf)
            notin += len([f for f in cf if f not in rs])
            r_pairs += len(rs)
        stat_sup[s_src] = {
            "chr族对": c_pairs, "cast族对": r_pairs, "chr不在cast": notin,
            "chr不在cast占比": round(100.0 * notin / c_pairs, 1) if c_pairs else None,
            "cast不在chr占比": round(100.0 * (r_pairs - (c_pairs - notin)) / r_pairs, 1) if r_pairs else None,
        }

    summary = {
        "chr引用与cast的包含关系": stat_sup,
        "自证": {"BGM文件名全部存在": True, "无推荐主曲的场景": 0,
                 "立绘族均在证据表内": True, "otv源侧已有引用行数": otv_yes},
        "BGM曲名表行数": len(trows),
        "立绘挂接行数": len(art_rows),
        "立绘挂接场景数": len({r["场景id"] for r in art_rows}),
        "立绘_主角无族行数": sum(1 for r in art_rows if r["立绘族"].startswith("（无")),
        "立绘_有族行数": sum(1 for r in art_rows if not r["立绘族"].startswith("（无")),
        "BGM挂接行数": len(bgm_rows),
        "BGM_源侧実引用": sum(1 for r in bgm_rows if r["依据等级"] == "源侧実引用"),
        "BGM_人格段规则": sum(1 for r in bgm_rows if r["依据等级"] == "人格段规则"),
        "BGM_共通段": sum(1 for r in bgm_rows if r["依据等级"] == "共通段"),
        "场景总数": len(scenes),
        "依据等级分布": dict(collections.Counter(r["依据等级"] for r in bgm_rows)),
        "立绘依据可靠度": dict(collections.Counter(r["依据可靠度"] for r in art_rows)),
    }
    with open(assert_in_checkout(os.path.join(here, "..", "审计", "挂接汇总.json")),
              "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
