# -*- coding: utf-8 -*-
r"""
W6f · 结构化剧本 scene_np.jsonl 构建器（S6 涅布＊プラス「渡来明日香篇」· 28 场景）

契约：
  * schema 定稿 = `资源组\剧本\schema.md`（W6a 定稿，**不得另创 schema**）
  * 消费顺序 = `资源组\修正\_README.md` §四.2 / §八.4：
      ① 按场景类别确定取文源 ② 套修正表（先过 §四.5 来源门控）③ 套译名替换表 ④ 组装
  * 参考实现 = `资源组\工具\build_scene_jsonl.py`（W6a/W6a2，亚衣线 s03c）

本模块（np）与 s03c 的差异（全部如实登记，见产出报告 §二）：
  1. 取文源 = **np 语料**（涅布＊プラス 明日香篇，独立翻译，合规）→ `cn_base`/`cn_origin`/`text_source` = `np`。
     （`_README.md` §四.5 的映射表以「源代号」为层名，已预置 otp/ota/otr/ot，本源按同一设计记 `np`）
  2. `kind` = **源值原样**（dialogue / narration / label / unknown）——schema 明文「源值，未改写」；
     s03c 源只有 title/dialogue/narration，np 源另有 label/unknown，属同一字段的取值集合差异。
  3. `source_kind` 一律 `new`：np 是 2012 独立短篇集，与本篇（2009）**无共有场景**（证据见报告 §3.1）。
  4. `align_method` 增 np 专属取值（同 W6a 增 jp_exact_fallback 的先例）：
     `np_direct`（正常直取）/ `np_engine_noise`（引擎错误串）/ `np_speaker_label`（说话人标签槽）
     / `np_menu_text`（子篇目菜单标题槽）/ `np_option_string`（选择支选项串）
  5. `title_jp`/`title_cn` 来自 **start_oretuba 子篇目菜单的（标题, 脚本）配对**（字节码常量池 + 内容交叉确证），
     不是 s03c 的 `kind=title` 槽（np 无 title 槽）。
  6. `next`/`choices` 来自 **start_oretuba 的 `_CallEx` 派发表 + 选项串配对**（Tier A 字节码确证）
     与 **首尾台词直接承接**（Tier B 内容确证）；Tier C（推断）**不写入**，一律留空并登记待裁决。
  7. 修正表：早期三张表 150 条**无一条 `source=np`** → 命中 0 是正确的（非漏修），逐条按范围外留痕；
     此后新增 `修正表_np说话人译名.tsv`（ISSUE-20260919-06，3 条）与 `修正表_鹰志简繁.tsv`
     （ISSUE-20261009-10，24 条，`term_unify` 词形级；`new_text` 闸门见装载段 [2c]）。

只读：`工程\涅布＊普拉斯\**`（一个字节都不改）、`资源组\修正\*`、`资源组\krkr素材库\资源总账.json`
只写：`资源组\剧本\scene_np.jsonl`、`子代理工作区\ISSUE-20260918-06\W6f\_build_stats_np.json`

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_np.py"
"""
import json, os, re, csv, sys, collections

sys.dont_write_bytecode = True   # 严禁在工具/只读源目录留下 __pycache__（同 build_scene_otp.py）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _term_unify               # noqa: E402  同目录共享模块：`term_unify` 语义的唯一实现

# ---------------------------------------------------------------- 路径根（读写分离）
# 读 = DATA_ROOT（共享数据树，默认 `E:\ZCode Workspace\Galgame`，可用环境变量
#      `GRETA_DATA_ROOT` 覆盖）；写 = 本脚本所在 checkout（由 `__file__` 推导）。
HERE      = os.path.dirname(os.path.abspath(__file__))            # <checkout>\...\资源组\工具
PRJ_LOCAL = os.path.dirname(os.path.dirname(HERE))                # <checkout>\...\<作品>
RES_LOCAL = os.path.join(PRJ_LOCAL, r"资源组")
WS_LOCAL  = os.path.dirname(os.path.dirname(PRJ_LOCAL))           # <checkout> 根
FIX  = os.path.join(RES_LOCAL, r"修正")                            # 修正表：以本分支副本为准
OUT  = os.path.join(RES_LOCAL, r"剧本")                            # 产物：写本 checkout
DATA_ROOT = os.environ.get("GRETA_DATA_ROOT", r"E:\ZCode Workspace\Galgame")
ROOT = DATA_ROOT
PRJ  = os.path.join(DATA_ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
RES  = os.path.join(PRJ, r"资源组")
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6f")   # 写本 checkout
NP   = os.path.join(DATA_ROOT, r"工程\涅布＊普拉斯")

CORPUS   = os.path.join(NP, r"语料\明日香线_原文.json")
CORPUS_STAT = os.path.join(NP, r"语料\明日香线_统计.json")
TRANS    = [os.path.join(NP, r"翻译工作区\分块%d_译文.json" % i) for i in (1, 2, 3)]
REFS     = os.path.join(NP, r"素材提取\明日香线_引用清单.json")
VOICE_MISS = os.path.join(NP, r"素材提取\音频\语音缺失清单.tsv")
BP_DIR   = os.path.join(NP, r"解包\data01100.arc")
LEDGER   = os.path.join(RES, r"krkr素材库\资源总账.json")


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))
TABLES = [
    ("修正表_B1B3.tsv",            os.path.join(FIX, "修正表_B1B3.tsv")),
    ("修正表_B1B3_扩展.tsv",       os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    ("修正表_新增场景mig重译.tsv", os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260919-06 新增：np 说话人标签槽未译修正（3 条，source=np，field=cn，fix_type=retranslate）
    ("修正表_np说话人译名.tsv",    os.path.join(FIX, "修正表_np说话人译名.tsv")),
    # ISSUE-20261009-10 新增：`鷹志`（繁）→`鹰志`（简）词形级归一（24 条，source=np，field=cn，
    #   fix_type=term_unify；`old_text=鷹志`／`new_text=鹰志`；locator=np 形态 `offset=<n>`）。
    #   `new_text` 侧机器约束见装载段 [2c] 闸门（未登记改动 ⇒ fail loud）。
    ("修正表_鹰志简繁.tsv",        os.path.join(FIX, "修正表_鹰志简繁.tsv")),
]
TERM_TABLE = os.path.join(FIX, "译名替换表.tsv")

SOURCE = "np"
ROUTE  = "np 涅布明日香篇"
ENGINE_ERR = "指定されたラベルは見つかりませんでした。"

# ---------------------------------------------------------------- 修正表来源门控（§四.5）
# 条目 source ↔ 取文基准层 cn_base。本源（np）按同一设计登记 np→np（见模块头注 1）。
# 六源全覆盖（ISSUE-20260930-11 补齐 otv —— 缺项会让装载该表的本次运行直接 fail loud）
CORR_SOURCE_TO_BASE = {"otr": "otr_new", "otp": "otp", "ota": "ota", "ot": "ot",
                       "otv": "otv", "np": "np"}
GATED = []          # 被门控排除（source 与 cn_base 不符）
TERM_NOOP = []      # `term_unify` 的幂等 no-op 留痕（ISSUE-20260930-12；构建期应为 0 条）
NP_CORR = []        # 范围内（source=np）条目

def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def w(s):
    sys.stdout.write(s + "\n"); sys.stdout.flush()

# ---------------------------------------------------------------- 场景表（脚本 → 元数据）
# 脚本顺序 = 剧情顺序（由 start_oretuba 菜单常量池顺序 + 首尾承接确证）
STORY = ["a01_a0","a01_b0","a01_c0","a02_a0","a02_b0","a03_a0","a03_b0",
         "a04_a0","a04_a1","a04_a2","a04_a3","a04_a4","a04_b0",
         "a05_a0","a05_b0","a05_b1","a05_c0","a05_c1","a05_d0","a05_e0",
         "a06_a0","a06_b1","a06_b2","a06_b3","a06_b4","a06_c0"]
FUNC = ["start_oretuba", "end_oretuba"]
ALL_SCRIPTS = STORY + FUNC

# ---- Tier A：start_oretuba 常量池的（子篇目标题, 脚本名）配对（26 条，逐条已内容交叉确证）
# 证据：start_oretuba 常量池偏移（十六进制）+ 该脚本首句内容
MENU = [   # (script, title_jp, 常量池偏移, 内容交叉确证要点)
    ("a01_a0", "再会　～バーサス羽田タカシ～",        0x230F, "a01_a0 尾「僕らが君に語るのは、たとえばこんなロマンス。」= 全篇开场（バーサス框架）"),
    ("a01_b0", "完徹モーニング",                    0x2352, "a01_b0 首「土曜の夜は…明けていた…二月にしては暖かな日曜の朝」＝通宵后之晨"),
    ("a01_c0", "いちゃいちゃ明日香さまプラス",        0x236B, "a01_c0 全篇为床戏/黏腻互动"),
    ("a02_a0", "お昼寝デイライト",                  0x238F, "a02_a0 首「喉に刺さる刺のような痛みで目が覚めた」＝昼寝后醒来"),
    ("a02_b0", "あのころの僕らと言ったら",            0x23A7, "a02_b0 全篇为两人闲聊往事"),
    ("a03_a0", "黄昏サンセット",                    0x23C7, "a03_a0 尾「ぬるっと生きよう」＝黄昏氛围"),
    ("a03_b0", "黄金の鷹外伝　～夢見るホークじゃいられない～", 0x23E2, "a03_b0 首「そのあと僕は夢を見た」＋ホーク/アスカ姫＝格雷塔迦露德幻想剧"),
    ("a04_a0", "星空トゥインクル",                  0x2416, "a04_a0 为仮装セット选物之夜的铺垫"),
    ("a04_a1", "タカシくんで遊ぼうｗｉｔｈリボン",     0x24A9, "a04_a1 首「リボンかな」＋尾「頭のリボンを外して」"),
    ("a04_a3", "タカシくんで遊ぼうｗｉｔｈ猫ミミ",     0x24D1, "a04_a3 首「猫耳かな」＋尾「僕の耳をブチっとひっこぬいた」"),
    ("a04_a2", "タカシくんで遊ぼうｗｉｔｈヘッドドレス", 0x24F9, "a04_a2 首「ヘッドドレスかな」"),
    ("a04_a4", "タカシくんで遊ぼうｗｉｔｈ鼻メガネ",   0x2527, "a04_a4 首「鼻眼鏡かな」"),
    ("a04_b0", "王女の品格",                        0x2551, "a04_b0 首「ところで渡来さんは付けないの？」＝假装后续（王女尊严说教）"),
    ("a05_a0", "らぶらぶミッドナイト",              0x2563, "a05_a0 为夜间亲热铺垫"),
    ("a05_b0", "僕はいつだって誰かをしばき倒したいと思っているんだ", 0x25A7, "a05_b0 首「いや、どちらかと言えばＳかな」＝S 分支"),
    ("a05_b1", "逆襲のチェリーボーイ",              0x25E1, "a05_b1 为 S 分支后续（パンツ要求场景）"),
    ("a05_c0", "僕はいつだって誰かにしばかれたいと思っているんだ", 0x25FD, "a05_c0 首「まあ、どちらかと言えばそうかもしれないけど」＝承认 M"),
    ("a05_c1", "やりすぎ明日香さまプラス",          0x2635, "a05_c1 为 M 分支后续（目隠し・腹部落书场景）"),
    ("a05_d0", "僕はいつだって誰かに穴という穴をアッー！　ひぎぃ！", 0x2655, "a05_d0 首「ううん、ドＭかな」＝ドM 分支"),
    ("a05_e0", "本当はいつだって誰かに拒絶されるのが恐いだけなんだ", 0x26A9, "a05_e0 首「ただ気が弱いだけだと思う」→「正解！」＝気弱分支"),
    ("a06_a0", "エピローグ　～今年の二月は暖かい～",   0x26E3, "a06_a0 首「それから三日後。冬の終わりを感じさせる、暖かな水曜の午後」"),
    ("a06_b1", "エピローグ　～やったね！～",          0x270D, "a06_b1 尾「やったね！」（b1/b4 共有）"),
    ("a06_b2", "エピローグ　～にゃうーん～",          0x272F, "a06_b2 尾「にゃあああーッ！」"),
    ("a06_b3", "エピローグ　～今日はピンクです～",     0x2751, "a06_b3 为服装赞美结局"),
    ("a06_b4", "エピローグ　～これでこそ明日香さま～",  0x2779, "a06_b4 为小鳩反应结局"),
    ("a06_c0", "閉幕　～バーサス羽田タカシ～",        0x27A5, "a06_c0 为全篇告别旁白（与 a01_a0 的バーサス框架成对）"),
]
TITLE_BY_SCRIPT = {s: t for s, t, _o, _e in MENU}
TITLE_OFFSET    = {s: o for s, _t, o, _e in MENU}
MENU_EVIDENCE   = {s: e for s, _t, _o, e in MENU}

# ---- Tier A：选择支选项串（常量池偏移）与其分支体首句的配对
A04_OPTIONS = [   # (option_jp, 常量池偏移, target, 分支体首句)
    ("小鳩が付けたら映えそうなかわいいリボン", 0x242E, "a04_a1", "a04_a1 首「リボンかな」"),
    ("つい先日、針生さんと熱く語った猫耳",     0x2455, "a04_a3", "a04_a3 首「猫耳かな」"),
    ("玉泉さんによく似合っていたヘッドドレス", 0x2478, "a04_a2", "a04_a2 首「ヘッドドレスかな」"),
    ("鼻眼鏡",                                 0x249F, "a04_a4", "a04_a4 首「鼻眼鏡かな」"),
]
A05_OPTIONS = [
    ("Ｓだよ",             0x257F, "a05_b0", "a05_b0 首「いや、どちらかと言えばＳかな」"),
    ("Ｍだよ",             0x2586, "a05_c0", "a05_c0 首「まあ、どちらかと言えばそうかもしれないけど」"),
    ("ドＭだよ",           0x258D, "a05_d0", "a05_d0 首「ううん、ドＭかな」"),
    ("気が弱いだけだよ",   0x2596, "a05_e0", "a05_e0 首「ただ気が弱いだけだと思う」→「正解！」"),
]

# ---- next 表：Tier A（字节码/派发表确证）+ Tier B（首尾台词直接承接确证）
NEXT_TIER_B = {   # 1 后继
    "a01_a0": ("a01_b0", "a01_a0 为バーサス框架开场 → a01_b0 首「土曜の夜は…」为叙事正篇开始"),
    "a01_b0": ("a01_c0", "a01_b0 尾「そんな渡来さんの手は僕の下半身へ伸びていた」→ a01_c0 首「寝てるのにここがこうなってる」"),
    "a01_c0": ("a02_a0", "a01_c0 尾「結局寝ちゃったよ」→ a02_a0 首「喉に刺さる刺のような痛みで目が覚めた」"),
    "a02_a0": ("a02_b0", "a02_a0 尾「僕は意気地なしだ」→ a02_b0 首「ひとときの眠りから覚めた僕たちは」"),
    "a02_b0": ("a03_a0", "a02_b0 尾「いよいよ僕の感謝は言葉にならなかった」→ a03_a0 为翌日/后续对话"),
    "a03_a0": ("a03_b0", "a03_a0 尾「ぬるっと生きよう」→ a03_b0 首「そのあと僕は夢を見た」"),
    "a03_b0": ("a04_a0", "a03_b0 尾「ゲーム・オーバー。」→ a04_a0 首「遠くで声が聞こえた／ん……誰……」＝梦醒"),
    "a04_b0": ("a05_a0", "a04_b0 尾「わくわく仮装セットをそっと押し入れへ戻した」→ a05_a0 首「そんなやり取りはあったものの」"),
    "a05_b1": ("a06_a0", "a05_b1 尾「薄明るい陽が兆すまで抱きあっていた」→ a06_a0 首「それから三日後」"),
    "a05_c1": ("a06_a0", "a05_c1 尾段与 a05_b1 逐字相同 → 同一后继 a06_a0"),
}
NEXT_TIER_B_MULTI = {   # ≥2 后继（并行分支体，无脚本内选择支串）
    "a04_a1": (["a04_b0"], "a04_a1..a4 四分支体共同汇合点：a04_b0 首「ところで渡来さんは付けないの？」承接仮装セット话题"),
    "a04_a2": (["a04_b0"], "同上（四分支汇合）"),
    "a04_a3": (["a04_b0"], "同上（四分支汇合）"),
    "a04_a4": (["a04_b0"], "同上（四分支汇合）"),
    "a05_b0": (["a05_b1"], "a05_b0 尾「おい、パンツ見せてください」「敬語かよ」→ a05_b1 首（明日香反应）"),
    "a05_c0": (["a05_c1"], "a05_c0 尾「これでいい？」→ a05_c1 首「せめてもの情けとして…目隠ししてあげます」＝同一目隠し场景续"),
    "a06_b1": (["a06_c0"], "a06_b1..b4 四并行搞笑分支 → 閉幕 a06_c0"),
    "a06_b2": (["a06_c0"], "同上"),
    "a06_b3": (["a06_c0"], "同上"),
    "a06_b4": (["a06_c0"], "同上"),
}
NEXT_BRANCH = {   # Tier A/B：≥2 后继
    "a04_a0": (["a04_a1", "a04_a2", "a04_a3", "a04_a4"],
               "a04_a0 尾「彼女が並べた四つの選択肢は…その中から僕が手を伸ばしたのは――」「これかな」＝选择支；"
               "四选项串位于 start_oretuba 常量池 0x242E/0x2455/0x2478/0x249F，各分支体首句逐条确证（见 choices）"),
    "a05_a0": (["a05_b0", "a05_c0", "a05_d0", "a05_e0"],
               "a05_a0 尾「羽田君ってＭなの？」＝选择支；四选项串位于 start_oretuba 常量池 "
               "0x257F/0x2586/0x258D/0x2596，各分支体首句逐条确证（见 choices）"),
    "a06_a0": (["a06_b1", "a06_b2", "a06_b3", "a06_b4"],
               "a06_a0 尾「渡来さんは大袈裟なぐらいにドアを叩いている」→ a06_b1..b4 首两行逐字相同"
               "（「そんなに慌てなくても……」「僕は苦笑しながらドアを開けた。」）＝四条并行搞笑分支"),
}
NEXT_END = {   # 终点（有证据）
    "a06_c0": "閉幕～バーサス羽田タカシ～＝全篇终点（尾「ばいばい。」）",
    "end_oretuba": "0 文本槽，但引用 ED 素材（END_BG / END_STAFF / End_Oretuba / Endroll1 / SP_ASU_1011 / wipe_18）"
                   "→ 是「结尾/ED 脚本」，非剧情脚本（无台词，故无 lines）",
}
NEXT_UNKNOWN = {   # 无脚本级后继证据 → 留空（不猜），登记待裁决
    "a05_d0": "a05_d0 尾「でも、とりあえずＭはＭなんでしょ？」；该句在 a05_b1/a05_c1/a06_a0 中均无对应承接 → "
              "候选（未确证）：a05_b1 / a05_c1 / a06_a0",
    "a05_e0": "a05_e0 尾与 a05_d0 逐字相同（「でも、とりあえずＭはＭなんでしょ？」）→ 与 a05_d0 同处未决，候选同上",
    "start_oretuba": "菜单脚本，其后继即 26 条子篇目派发（见 choices / next）",
}

# ---- phase（本线路取值：序 / 个人线 / 结局）
PHASE = {}
PHASE["start_oretuba"] = "序"        # 子篇目菜单＝入口
PHASE["a01_a0"] = "序"               # 再会～バーサス羽田タカシ～＝全篇框架开场
PHASE["end_oretuba"] = "结局"        # 终点标记（空脚本）
for s in ("a06_a0", "a06_b1", "a06_b2", "a06_b3", "a06_b4", "a06_c0"):
    PHASE[s] = "结局"
for s in ALL_SCRIPTS:
    PHASE.setdefault(s, "个人线")

# ---------------------------------------------------------------- 读输入
w("[1/7] 读取输入 ...")
corpus = json.load(open(CORPUS, encoding="utf-8"))
stat   = json.load(open(CORPUS_STAT, encoding="utf-8"))
trans  = {}
for p in TRANS:
    for x in json.load(open(p, encoding="utf-8")):
        k = (x["file"], x["idx"])
        if k in trans:
            raise SystemExit("!! 译文重复键: %s" % (k,))
        trans[k] = x["text"]
refs   = json.load(open(REFS, encoding="utf-8"))
ledger = json.load(open(LEDGER, encoding="utf-8"))

by_file = collections.OrderedDict()
for x in corpus:
    by_file.setdefault(x["file"], []).append(x)
assert set(by_file) | {"end_oretuba"} == set(ALL_SCRIPTS), \
    "!! 语料脚本集合与预期不符: %s" % (set(by_file) ^ set(ALL_SCRIPTS),)
for f in STORY:
    assert f in by_file, "!! 缺脚本: " + f
w("      语料 %d 槽 / %d 脚本 ｜ 译文 %d 条 ｜ 引用清单 %s ｜ 总账 %d"
  % (len(corpus), len(by_file), len(trans), refs["counts"], len(ledger["entries"])))

# 译文完备性（本源 100%）
miss_tr = [(f, x["idx"]) for f, xs in by_file.items() for x in xs if (f, x["idx"]) not in trans]
assert not miss_tr, "!! 译文缺失 %d 条: %s" % (len(miss_tr), miss_tr[:5])
extra_tr = [k for k in trans if k[0] not in by_file]
assert not extra_tr, "!! 译文有多余键: %s" % (extra_tr[:5],)

# ---------------------------------------------------------------- 修正表（含来源门控）
w("[2/7] 装载修正表（%d 张）..." % len(TABLES))
corr_rows = []
corrections = {}
for tname, tpath in TABLES:
    for r in read_tsv(tpath):
        r["_table"] = tname
        corr_rows.append(r)
        key = (r["source"], r["file"], r["locator"])
        if key in corrections:
            raise SystemExit("!! 修正表定位冲突: %s" % (key,))
        corrections[key] = r
w("      修正表合计 %d 条（%s）"
  % (len(corr_rows),
     " / ".join("%s=%d" % (t, sum(1 for r in corr_rows if r["_table"] == t)) for t, _ in TABLES)))

# ---- [2c] 修正表_鹰志简繁 new_text 闸门（ISSUE-20261009-10）
# 本表全部行为 `term_unify` 的**单对词形**（`old_text=鷹志` → `new_text=鹰志`）。`_term_unify.apply`
# 的命中判据在 `old_text` 侧；`new_text` 侧若无机器约束，把替换值改成任意未登记字样仍会 EXIT=0 并
# 静默进语料（与 ISSUE-20261009-04b E3「N2 类静默篡改」同源）。故本表在装载期逐行 fail loud：
#   ① `fix_type` 必须 `term_unify`、`field` 必须 `cn`；
#   ② `old_text` 必须为登记词形 `鷹志`、`new_text` 必须为采用值 `鹰志`（唯一允许的改动＝繁→简）。
YZ_GATE_ROWS = 0
for r in corr_rows:
    if r["_table"] != "修正表_鹰志简繁.tsv":
        continue
    YZ_GATE_ROWS += 1
    if r["fix_type"] != "term_unify" or r["field"] != "cn":
        raise SystemExit("!! 修正表_鹰志简繁 行越界（只允许 term_unify/cn）: %s/%s"
                         % (r["file"], r["locator"]))
    if r["old_text"] != "鷹志" or r["new_text"] != "鹰志":
        raise SystemExit("!! 修正表_鹰志简繁 old_text/new_text 含未登记改动（只允许 鷹志→鹰志）: "
                         "%s/%s（old=%r new=%r）"
                         % (r["file"], r["locator"], r["old_text"], r["new_text"]))
w("      [2c] 修正表_鹰志简繁 闸门：%d 行通过（只允许 鷹志→鹰志）" % YZ_GATE_ROWS)

# 本源范围判定：条目 source == np，或 file 命中 np 脚本名
NP_FILES = set(ALL_SCRIPTS)
np_corr_rows = [r for r in corr_rows if r["source"] == SOURCE]
np_file_rows = [r for r in corr_rows if os.path.splitext(r["file"])[0] in NP_FILES]
w("      source=np 条目 %d 条 ｜ file 命中 np 脚本名的条目 %d 条（预期均 0）"
  % (len(np_corr_rows), len(np_file_rows)))
corr_hit = set()

# ---------------------------------------------------------------- 译名替换表
w("[3/7] 装载译名替换表 ...")
TERM_RULES = []
for r in read_tsv(TERM_TABLE):
    new, old, scope = r["新写法"].strip(), r["旧写法"].strip(), r["适用范围(源代号)"].strip()
    if new.startswith("（") or old.startswith("（") or scope == "—":
        continue                                  # 待裁决 / 非替换项 / 无旧写法残留
    if "/" in scope:
        src, stream = scope.split("/", 1)
    else:
        src, stream = scope, "body"
    if src == "全部":
        continue                                  # 全源条目实测旧写法残留 0，无替换面
    stream = "name" if stream == "name" else "body"
    TERM_RULES.append({"jp": r["原词日文"].strip(), "old": old, "new": new,
                       "src": src, "stream": stream, "table_note": r["备注"].strip()})
np_rules = [x for x in TERM_RULES if x["src"] == SOURCE]
w("      可用规则 %d 条，其中 np 专用 %d 条：%s"
  % (len(TERM_RULES), len(np_rules), [(x["jp"], x["old"], x["new"]) for x in np_rules]))
TERM_PENDING = [r for r in read_tsv(TERM_TABLE)
                if r["适用范围(源代号)"].strip().startswith(SOURCE)
                and (r["新写法"].strip().startswith("（") or r["旧写法"].strip().startswith("（"))]
w("      np 适用范围内「待裁决/非替换项」%d 条（不生效，登记）：%s"
  % (len(TERM_PENDING), [r["原词日文"] for r in TERM_PENDING]))

# §六 排除规则（正则；键 = (原词日文, 旧写法)）。与 W6a 一致（`资源组\修正\译名统一口径.md` §六）。
EXCL = {
    # np 实测补充（W6f）：表内排除用的是全角 `Ｓ香`，而译文实测出现**半角** `渡来S香`
    # （a05_c1「渡来Ｓ香と言っても過言じゃない」→ 译文「渡来S香」），旧排除不命中 →
    # 误改成「渡来同学S香」。故把 `Ｓ香` 扩为 `[ＳS]香`。建议主代理把本条登记进 §六。
    ("渡来さん", "渡来（裸名）"): re.compile(r"渡来(?!同学|明日香|家|屋|前辈|学姐|[ＳS]香)"),
    ("委員長", "委员长"):        re.compile(r"(?<!执行)委员长"),
    ("ハヤブサ", "隼"):          re.compile(r"(?<!游)隼(?!人)"),
    ("ソラ学", "空学"):          re.compile(r"(?<!美)空学(?!院|府)"),
    ("針生", "针生"):            re.compile(r"针生(?!同学|前辈|君|先生|小姐|老师|哥|姐)"),
    ("ガルーダ", "伽楼罗"):      re.compile(r"(?<!伊丹)伽楼罗"),
}
JP_SKIP = {"ガルーダ": ["伽楼羅"]}
CONTEXT_FLAGGED = {"ペガサス", "ドラさん"}

# ---- JP 门控的「敬称写形变体 / 假名写形」（W6f 新增，提请主代理确认）
# 背景：W6a 的 JP 门控是**字面包含**（`rule["jp"] not in jp`）。本源实测该口径漏 3 处：
#   a02_a0#29 jp「んん……**はねだくん**……」、a05_b0#12 jp「久しぶりに**羽田くん**が…」——
#   原文把敬称 `くん` 写成**假名**、或整个姓名写成**平假名**，字面不含 `羽田君` → 门控不通过，
#   译文 `羽田同学` 未被替换为 `羽田君`，造成同一作品内「羽田同学 / 羽田君」两种写法并存
#   （违反 AGENTS.md §六 术语全篇统一；通用 SKILL §五「先矫正、后翻译」要求含混写形先归一化）。
# 处置：门控改为「原词日文」的**写形变体正则**（君↔くん、平/片假名写形），语义不变（仍是同一原词），
#   只承认同一词的不同书写形。此为**门控放宽**，须主代理确认后登记（与 W6a「排除规则登记 §六」同一流程）。
JP_GATE_VARIANTS = {
    "羽田君": [r"羽田[君くん]", r"はねだ[君くん]", r"ハネダ[クく][ンん]", r"羽田クン"],
    "渡来さん": [r"渡来[さサ][んン]", r"わたらい[さサ][んン]", r"ワタライ[さサ][んン]"],
}
_JP_GATE_CACHE = {}

def jp_gate_ok(jp_word, jp):
    if jp_word in jp:
        return True
    rx = _JP_GATE_CACHE.get(jp_word)
    if rx is None:
        pats = JP_GATE_VARIANTS.get(jp_word)
        rx = re.compile("|".join(pats)) if pats else re.compile(re.escape(jp_word))
        _JP_GATE_CACHE[jp_word] = rx
    return bool(rx.search(jp))

def apply_term(cn, jp, src, stream):
    hits = []
    if not cn:
        return cn, hits
    for rule in TERM_RULES:
        if rule["src"] != src or rule["stream"] != stream:
            continue
        if not jp_gate_ok(rule["jp"], jp):
            continue                                     # JP 门控（含写形变体）
        skip = JP_SKIP.get(rule["jp"])
        if skip and any(s in jp for s in skip):
            continue
        rx = EXCL.get((rule["jp"], rule["old"]))
        new_cn = rx.sub(rule["new"], cn) if rx is not None else cn.replace(rule["old"], rule["new"])
        if new_cn != cn:
            hits.append({"原词日文": rule["jp"], "旧写法": rule["old"], "新写法": rule["new"],
                         "字段": stream, "before": cn, "after": new_cn,
                         "context_flag": rule["jp"] in CONTEXT_FLAGGED})
            cn = new_cn
    return cn, hits

# ---------------------------------------------------------------- 素材：逐脚本反查（复现 route_refs.py 口径）
w("[4/7] 逐脚本反查素材引用 ...")
route_re = re.compile(r"^a0[1-6]_|^start_oretuba$|^end_oretuba$")
tok_re   = re.compile(rb"[A-Za-z_][A-Za-z0-9_]{2,20}")
SKIP = ("Buriko", "DSC", "BGV", "ASC", "SGC", "ASD", "_Set", "_Play", "_Get", "_Fade", "_Wait",
        "_Exec", "_Call", "_Jump", "_If", "_Loop", "_End", "_Msg", "_Text", "_Win", "_Obj", "_Sys",
        "_BG", "_Chara", "_Se", "_Bgm", "_Voice", "_Anime", "_Save", "_Load", "_Return", "_Select",
        "_Sound", "_Movie", "_Quake", "_Shake", "_Flash", "_Def", "_Var", "_Draw", "_Quit", "_Stop",
        "_Init", "_Bustshot")

def classify_ref(s):
    l = s.lower()
    if re.fullmatch(r"(asu|hiy|skr|tub|ore|sak|y)\d{5}", l):
        return "voice_id"
    if re.match(r"(asu_|hiy_|skr_|tub_|sak_)", l):
        return "sprite"
    if l.startswith("bgm"):
        return "bgm"
    if l.startswith("se"):
        return "se"
    if l.startswith("bg"):
        return "bg"
    if re.match(r"^(ore|tub|skr|sak|aki|ec|ef|cin|wipe|end|sec|tn|ban|chi|kaz|kob|kur|mas|mis|miy|sp_)", l):
        return "cg_fx"
    return "other"

per_file_refs = collections.defaultdict(lambda: collections.defaultdict(set))
for fn in sorted(os.listdir(BP_DIR)):
    if not route_re.match(fn):
        continue
    raw = open(os.path.join(BP_DIR, fn), "rb").read()
    for m in tok_re.finditer(raw):
        s = m.group().decode("ascii")
        if not re.search(r"[0-9_]", s) or s.startswith(SKIP):
            continue
        per_file_refs[fn][classify_ref(s)].add(s)
tot_refs = collections.defaultdict(set)
for f, d in per_file_refs.items():
    for k, v in d.items():
        tot_refs[k] |= v
assert {k: len(v) for k, v in tot_refs.items()} == refs["counts"], \
    "!! 逐脚本反查与引用清单不一致: %s vs %s" % ({k: len(v) for k, v in tot_refs.items()}, refs["counts"])
for k in refs["counts"]:
    assert tot_refs[k] == set(refs["sets"][k]), "!! 引用集合不一致: " + k
w("      与 引用清单.json 逐类逐名完全一致：%s" % {k: len(v) for k, v in sorted(tot_refs.items())})

# 总账 np 索引（大小写不敏感，按 orig_name 去扩展名）
np_index = collections.defaultdict(dict)
for e in ledger["entries"]:
    if e["source"] != SOURCE:
        continue
    np_index[e["kind"]][e["orig_name"].rsplit(".", 1)[0].lower()] = e["out_relpath"]
REF2KIND = {"sprite": "chr", "cg_fx": "pic", "bg": "pic", "bgm": "bgm", "se": "se", "voice_id": "voice"}
REF_KINDS = ("sprite", "cg_fx", "bg", "bgm", "se")     # voice_id 逐行走 lines[].audio

def map_asset(ref):
    cat = classify_ref(ref)
    kind = REF2KIND.get(cat)
    if kind is None:
        return None, None
    return kind, np_index.get(kind, {}).get(ref.lower())

def map_voice(vid):
    return np_index["voice"].get(vid.lower())

# 语音缺失清单（源侧权威，逐条）
voice_missing_rows = read_tsv(VOICE_MISS)
VOICE_MISSING = {r["语音ID"]: r for r in voice_missing_rows}
w("      语音缺失清单 %d 条（源侧 TSV）" % len(voice_missing_rows))

# ---------------------------------------------------------------- 组装场景
w("[5/7] 组装 %d 场景 ..." % len(ALL_SCRIPTS))

def build_scene(script):
    xs = by_file.get(script, [])
    # 说话人标签集合：kind=label（除 start_oretuba 的 7 条菜单串）＋ 短 unknown 紧邻 dialogue（侍女Ａ）
    label_texts = set()
    for i, x in enumerate(xs):
        if x["kind"] == "label" and script != "start_oretuba":
            label_texts.add(x["text"])
        elif x["kind"] == "unknown" and len(x["text"]) <= 8 and i + 1 < len(xs) and xs[i + 1]["kind"] == "dialogue":
            label_texts.add(x["text"])

    lines_out, cast = [], []
    voices = set()
    by_origin, by_src = collections.Counter(), collections.Counter()
    name_repl_scene = 0
    cur_speaker_jp = ""
    cur_speaker_cn = ""
    dates = []
    for i, x in enumerate(xs, 1):
        jp = x["text"]
        cn = trans[(script, x["idx"])]
        kind = x["kind"]
        off = x["offset"]

        # ---- ① 取文基准层
        base = SOURCE
        if jp == ENGINE_ERR:
            align = "np_engine_noise"
        elif kind == "label" and script != "start_oretuba":
            align = "np_speaker_label"
        elif script == "start_oretuba" and x["idx"] != 34:
            align = "np_menu_text" if jp in set(TITLE_BY_SCRIPT.values()) else "np_option_string"
        elif kind == "unknown" and jp in label_texts:
            align = "np_speaker_label"
        else:
            align = "np_direct"
        layers = [base]

        # ---- ② 修正表（(source,file,locator) 三元组定位 + §四.5 来源门控）
        fix_refs = []
        loc = "offset=%d" % off
        row = corrections.get((SOURCE, script, loc))
        if row is not None:
            want = CORR_SOURCE_TO_BASE.get(row["source"])
            if want is None:
                raise SystemExit("!! 修正表 source 未登记门控映射: %s @ %s/%s" % (row["source"], script, loc))
            # `term_unify` 与取文层无关 ⇒ 不受来源门控约束（见 `修正\_README.md` §四.5）
            if want == base or row["fix_type"] == "term_unify":
                cn_before = cn
                if row["fix_type"] == "term_unify":
                    # ISSUE-20260930-12：`term_unify` 是**词形级替换**——`old_text` = 词形正则、
                    # `new_text` = 替换值（**不是整句**）。命中即 re.sub；已是后态 ⇒ 幂等 no-op
                    # （不记 fix_refs、不计命中）；两者都不是 ⇒ fail loud。
                    cn, tu_state = _term_unify.apply(cn, row["old_text"], row["new_text"])
                else:
                    # ISSUE-20260919-06：新增 old_text 逐字符断言（与其余构建器一致，防表与语料脱节）
                    if (row.get("old_text") or "") != (cn_before or ""):
                        raise SystemExit("!! 修正表 old_text 与源译文不符: %s/%s（源=%r 表=%r）"
                                         % (script, loc, cn_before, row.get("old_text")))
                    tu_state = _term_unify.APPLIED
                    cn = row["new_text"]
                if tu_state == _term_unify.NOOP:
                    TERM_NOOP.append({"table": row["_table"], "source": row["source"],
                                      "file": row["file"], "locator": loc,
                                      "old_text": row["old_text"], "new_text": row["new_text"]})
                else:
                    o = "retranslate" if row["fix_type"] == "retranslate" else "fix_table"
                    layers.append(o)
                    fix_refs.append({"table": row["_table"], "locator": loc,
                                     "fix_type": row["fix_type"], "cn_before": cn_before})
                    corr_hit.add((SOURCE, script, loc))
            else:
                GATED.append({"table": row["_table"], "source": row["source"], "file": script,
                              "locator": loc, "kind": row["kind"], "fix_type": row["fix_type"],
                              "script": script, "seq": i, "cn_base": base, "jp": jp,
                              "cn_kept": cn, "cn_gated": row["new_text"], "old_text": row["old_text"],
                              "reason": "source_gate: 条目 source=%s 对应取文基准 %s，而该行取文基准为 %s"
                                        % (row["source"], want, base)})

        # ---- ③ 译名替换（JP 门控；body 作用于 cn，name 作用于名字框）
        cn, h1 = apply_term(cn, jp, SOURCE, "body")

        # ---- 说话人
        if kind == "label" and script != "start_oretuba":
            cur_speaker_jp, cur_speaker_cn = jp, cn
        elif kind == "unknown" and jp in label_texts:
            cur_speaker_jp, cur_speaker_cn = jp, cn
        if kind == "dialogue":
            sp_jp, sp_cn = cur_speaker_jp, cur_speaker_cn
        else:
            sp_jp, sp_cn = "", ""
        sp_cn, h2 = apply_term(sp_cn, sp_jp, SOURCE, "name")
        hits = h1 + h2
        if hits:
            layers.append("name_replace")
            name_repl_scene += len(hits)

        # ---- 语音
        vid = x["voice_id"] or ""
        audio = []
        if vid:
            voices.add(vid)
            p = map_voice(vid)
            if p:
                audio.append(p)

        # ---- cast（旁白行计为 旁白；标签/菜单槽不计入）
        if kind in ("dialogue", "narration"):
            name = sp_cn if sp_cn else "旁白"
            if name not in cast:
                cast.append(name)

        # ---- 显式日期（仅 ○月○日 写形）
        for m in re.finditer(r"[０-９0-9]{1,2}月[０-９0-9]{1,2}日", jp):
            s = "".join(chr(ord(c) - 0xFEE0) if "０" <= c <= "９" else c for c in m.group(0))
            mm, dd = s.split("月")
            d = "%02d/%02d" % (int(mm), int(dd.rstrip("日")))
            if d not in [y["date"] for y in dates]:
                dates.append({"date": d, "line_index": x["idx"]})

        origin = base
        for lay in layers:
            if lay != "name_replace" and lay not in ("fix_table", "retranslate") and lay != base:
                origin = lay
        if fix_refs:
            origin = "retranslate" if fix_refs[-1]["fix_type"] == "retranslate" else "fix_table"
        by_origin[origin] += 1
        by_src[SOURCE] += 1

        lines_out.append({
            "seq": i,
            "index": x["idx"],
            "lineno": x["idx"] + 1,
            "kind": kind,
            "speaker": sp_cn,
            "speaker_jp": sp_jp,
            "voice": vid,
            "jp": jp,
            "cn": cn,
            "cn_origin": origin,
            "cn_base": base,
            "align_method": align,
            "layers": layers,
            "fix_refs": fix_refs,
            "name_replaced": hits,
            "empty_slot": (not jp and not cn),
            "d14_exception": None,
            "audio": audio,
        })

    # ---- 标题（来自 start_oretuba 子篇目菜单配对）
    if script in TITLE_BY_SCRIPT:
        tj = TITLE_BY_SCRIPT[script]
        tc = trans[("start_oretuba", next(x["idx"] for x in by_file["start_oretuba"] if x["text"] == tj))]
        title_jp, title_cn = tj, tc
        title_variants = [{"offset": TITLE_OFFSET[script], "jp": tj, "cn": tc, "cn_origin": SOURCE}]
    else:
        title_jp = title_cn = None
        title_variants = []

    # ---- next / next_kind
    if script == "start_oretuba":
        nxt = list(STORY); nk = "branch"
    elif script in NEXT_TIER_B:
        nxt = [NEXT_TIER_B[script][0]]; nk = "linear"
    elif script in NEXT_TIER_B_MULTI:
        nxt = list(NEXT_TIER_B_MULTI[script][0]); nk = "linear" if len(nxt) == 1 else "branch"
    elif script in NEXT_BRANCH:
        nxt = list(NEXT_BRANCH[script][0]); nk = "branch"
    elif script in NEXT_END:
        nxt = []; nk = "end"
    else:
        nxt = []; nk = "end"            # NEXT_UNKNOWN：无脚本级证据 → 留空，不猜

    # ---- choices
    # 口径（**本模块唯一的归属决定，提请主代理确认**）：
    #   本作所有选择支的**选项串物理上都位于 `start_oretuba` 的常量池**（a04_a0/a05_a0 自身常量池内无选项串，
    #   只含「彼女が並べた四つの選択肢は…」「羽田君ってＭなの？」这类**选择铺垫正文**）。
    #   故本模块把全部选择支（26 条子篇目菜单 + 4 条 a04 选项 + 4 条 a05 选项）一律挂在 `start_oretuba`，
    #   而把「该选择支在哪个场景弹出」记在 `evidence` 与对应场景的 `next` 里——**不重复登记**。
    choices = []
    if script == "start_oretuba":
        for s in STORY:
            tj = TITLE_BY_SCRIPT[s]
            row = next(x for x in by_file["start_oretuba"] if x["text"] == tj)
            choices.append({
                "text_jp": tj, "text_cn": trans[("start_oretuba", row["idx"])], "cn_origin": SOURCE,
                "target": s, "pairing_verified": True, "confirmed": True,
                "evidence": "子篇目菜单条目：start_oretuba 常量池 %#06x 处该标题串紧接脚本名 %s"
                            "（_SetSceneName/_CallEx 语义，首条 `_SetSceneName`+`_CallEx` 直接可见）；"
                            "内容交叉确证：%s" % (TITLE_OFFSET[s], s.upper(), MENU_EVIDENCE[s])})
        for opt, off, tgt, ev in A04_OPTIONS:
            row = next(x for x in by_file["start_oretuba"] if x["text"] == opt)
            choices.append({
                "text_jp": opt, "text_cn": trans[("start_oretuba", row["idx"])], "cn_origin": SOURCE,
                "target": tgt, "pairing_verified": True, "confirmed": True,
                "evidence": "a04 选择支选项（弹出场景＝a04_a0，其正文含「彼女が並べた四つの選択肢は…」「これかな」）："
                            "选项串位于 start_oretuba 常量池 %#06x；配对由分支体首句确证：%s" % (off, ev)})
        for opt, off, tgt, ev in A05_OPTIONS:
            row = next(x for x in by_file["start_oretuba"] if x["text"] == opt)
            choices.append({
                "text_jp": opt, "text_cn": trans[("start_oretuba", row["idx"])], "cn_origin": SOURCE,
                "target": tgt, "pairing_verified": True, "confirmed": True,
                "evidence": "a05 选择支选项（弹出场景＝a05_a0，其正文含「羽田君ってＭなの？」）："
                            "选项串位于 start_oretuba 常量池 %#06x；配对由分支体首句确证：%s" % (off, ev)})

    # ---- 素材
    assets, missing = [], []
    for cat in REF_KINDS:
        for ref in sorted(per_file_refs.get(script, {}).get(cat, [])):
            k, p = map_asset(ref)
            if p:
                assets.append({"ref": ref, "kind": k, "out_relpath": p, "hit": True})
            else:
                assets.append({"ref": ref, "kind": k, "out_relpath": None, "hit": False})
                missing.append(ref)

    # ---- text_source
    bases = set(t["layers"][0] for t in lines_out if t["layers"])
    text_source = "mixed" if len(bases) > 1 else (next(iter(bases)) if bases else SOURCE)

    return {
        "scene_id": "%s_%s" % (SOURCE, script),
        "source": SOURCE,
        "script": script,
        "source_kind": "new",
        "text_source": text_source,
        "title_jp": title_jp,
        "title_cn": title_cn,
        "title_variants": title_variants,
        "game_date": dates[0]["date"] if dates else None,
        "game_dates": dates,
        "phase": PHASE[script],
        "route": ROUTE,
        "cast": cast,
        "next": nxt,
        "next_kind": nk,
        "choices": choices,
        "line_count": len(lines_out),
        "voice_count": len(voices),
        "assets": assets,
        "assets_missing": missing,
        "stats": {
            "lines_by_origin": dict(by_origin),
            "lines_by_source": dict(by_src),
            "corrections_hit": sum(1 for l in lines_out if l["fix_refs"]),
            "name_replace_count": name_repl_scene,
            "empty_slots": sum(1 for l in lines_out if l["empty_slot"]),
            "d14_exceptions": 0,
        },
        "lines": lines_out,
    }

scene_objs = [build_scene(s) for s in ALL_SCRIPTS]

# ---------------------------------------------------------------- 自检
w("[6/7] 自检 ...")
corr_out_of_scope = [r for r in corr_rows if r["source"] != SOURCE]
corr_hit_in_scope = [r for r in np_corr_rows if (r["source"], r["file"], r["locator"]) in corr_hit]
miss_corr = [r for r in np_corr_rows if (r["source"], r["file"], r["locator"]) not in corr_hit]

tot_lines = sum(s["line_count"] for s in scene_objs)
baseline = len(corpus)
per_script_base = {f: len(v) for f, v in by_file.items()}
per_script_out = {s["script"]: s["line_count"] for s in scene_objs}
line_diff = {f: per_script_base.get(f, 0) - per_script_out.get(f, 0)
             for f in set(per_script_base) | set(per_script_out)}

orig_dist, src_dist = collections.Counter(), collections.Counter()
for s in scene_objs:
    for k, v in s["stats"]["lines_by_origin"].items():
        orig_dist[k] += v
    for k, v in s["stats"]["lines_by_source"].items():
        src_dist[k] += v

a_total = sum(len(s["assets"]) for s in scene_objs)
a_hit = sum(1 for s in scene_objs for a in s["assets"] if a["hit"])
v_ref = sum(1 for s in scene_objs for l in s["lines"] if l["voice"])
v_hit = sum(1 for s in scene_objs for l in s["lines"] if l["audio"])
v_missing_ids = sorted({l["voice"] for s in scene_objs for l in s["lines"]
                        if l["voice"] and not l["audio"]})
v_present_ids = sorted({l["voice"] for s in scene_objs for l in s["lines"] if l["audio"]})

# 逐类素材命中（按引用名去重，模块级）
class_hit, class_tot, class_missing = {}, {}, {}
for cat in REF_KINDS:
    tot = set(tot_refs[cat]); hit, miss = set(), set()
    for r in tot:
        k, p = map_asset(r)
        (hit if p else miss).add(r)
    class_tot[cat], class_hit[cat], class_missing[cat] = len(tot), len(hit), sorted(miss)
class_tot["voice_id"] = len(tot_refs["voice_id"])
class_hit["voice_id"] = len([v for v in tot_refs["voice_id"] if map_voice(v)])
class_missing["voice_id"] = sorted(v for v in tot_refs["voice_id"] if not map_voice(v))

# 缺失语音逐条（带引用处）
voice_missing_detail = []
for vid in class_missing["voice_id"]:
    r = VOICE_MISSING.get(vid)
    voice_missing_detail.append({"voice_id": vid,
                                 "cited_at": (r.get("引用处(file:offset)") or r.get("引用处")) if r else "",
                                 "judgement": r["判定"] if r else ""})
# 逐场景缺失语音 ID
voice_missing_per_scene = {s["script"]: sorted({l["voice"] for l in s["lines"]
                                                 if l["voice"] and not l["audio"]})
                           for s in scene_objs}

# 选择支/next 统计
choices_total = sum(len(s["choices"]) for s in scene_objs)
choices_verified = sum(1 for s in scene_objs for c in s["choices"] if c["pairing_verified"])
choices_null = sum(1 for s in scene_objs for c in s["choices"] if c["target"] is None)

report = {
    "scenes": len(scene_objs),
    "scripts_expected": len(ALL_SCRIPTS),
    "lines_total": tot_lines,
    "lines_baseline_corpus": baseline,
    "lines_balanced": tot_lines == baseline,
    "lines_per_script_diff": line_diff,
    "lines_per_script_diff_nonzero": {k: v for k, v in line_diff.items() if v != 0},
    "kind_dist": dict(collections.Counter(l["kind"] for s in scene_objs for l in s["lines"])),
    "orig_dist": dict(orig_dist),
    "src_dist": dict(src_dist),
    "align_method_dist": dict(collections.Counter(l["align_method"] for s in scene_objs for l in s["lines"])),
    "text_source_dist": dict(collections.Counter(s["text_source"] for s in scene_objs)),
    "source_kind_dist": dict(collections.Counter(s["source_kind"] for s in scene_objs)),
    "source_kind_note": "np 与 2009 本篇无共有场景（见 §3.1 证据）→ `shared`=0；§三.1 的 `branch` 判据"
                        "（与父场景 jp 重合率≥50%）在 np 无对象 → 亦为 0。本源的 14 个并行分支体"
                        "（a04_a1..a4 / a05_b0,c0,d0,e0 / a06_b1..b4）结构改由 `next`/`choices` 表达。"
                        "如需把该 14 个场景标为 `branch`，改 PHASE/SOURCE_KIND 一行即可（提请主代理确认）。",
    "branch_body_scripts": ["a04_a1", "a04_a2", "a04_a3", "a04_a4",
                            "a05_b0", "a05_c0", "a05_d0", "a05_e0",
                            "a06_b1", "a06_b2", "a06_b3", "a06_b4"],
    "other_refs_excluded": {f: sorted(per_file_refs.get(f, {}).get("other", [])) for f in ALL_SCRIPTS
                            if per_file_refs.get(f, {}).get("other")},
    "other_refs_note": "`other` 类引用（47 个）＝脚本名（A01_A0…A06_C0）与引擎标识符，非素材，"
                       "故不写入 assets（与 W6a 一致：assets 只收 chr/pic/se/bgm）；逐脚本清单见本键。",
    "phase_dist": dict(collections.Counter(s["phase"] for s in scene_objs)),
    "next_kind_dist": dict(collections.Counter(s["next_kind"] for s in scene_objs)),
    "corrections_total": len(corr_rows),
    "corrections_source_np": len(np_corr_rows),
    "corrections_file_matches_np_script": len(np_file_rows),
    "corrections_hit": len(corr_hit),
    "corrections_hit_in_scope": len(corr_hit_in_scope),
    "corrections_gated": len(GATED),
    # ISSUE-20260930-12：`term_unify` 的幂等 no-op 留痕（构建期应为 0——每个目标槽都应命中词形）
    "term_unify_noop": TERM_NOOP,
    "corrections_missing_in_scope": miss_corr,
    "corrections_out_of_scope_by_source": collections.Counter(r["source"] for r in corr_out_of_scope).most_common(),
    "corrections_out_of_scope_by_table": collections.Counter(r["_table"] for r in corr_out_of_scope).most_common(),
    "corrections_out_of_scope_files": sorted({r["file"] for r in corr_out_of_scope}),
    "term_rules_np": [(x["jp"], x["old"], x["new"]) for x in np_rules],
    "term_pending_np": [r["原词日文"] for r in TERM_PENDING],
    "term_hits": sum(s["stats"]["name_replace_count"] for s in scene_objs),
    "term_residual_audit": {
        "羽田同学_remaining": [{"script": s["script"], "seq": l["seq"], "jp": l["jp"], "cn": l["cn"]}
                               for s in scene_objs for l in s["lines"] if "羽田同学" in l["cn"]],
        "渡来_裸名_remaining": [{"script": s["script"], "seq": l["seq"], "jp": l["jp"], "cn": l["cn"]}
                               for s in scene_objs for l in s["lines"]
                               if re.search(r"渡来(?!同学|明日香|家|屋|前辈|学姐|[ＳS]香)", l["cn"])],
        "note": "交付前残留审计：`羽田同学` 应为 0（59 处旧写法全部替换为 `羽田君`）；"
                "`渡来` 裸名残留为 **合法**（a06_a0#30 是明日香自报姓氏「姓渡来。」，原文 jp 无 `渡来さん`，"
                "JP 门控正确地未替换）。",
    },
    "name_replace_examples": [{"script": s["script"], "seq": l["seq"], "field": h["字段"],
                               "原词日文": h["原词日文"], "旧写法": h["旧写法"], "新写法": h["新写法"],
                               "before": h["before"], "after": h["after"], "jp": l["jp"]}
                              for s in scene_objs for l in s["lines"] for h in l["name_replaced"]],
    "assets_class": {k: {"total": class_tot[k], "hit": class_hit[k],
                         "missing": class_missing[k]} for k in
                     ("sprite", "cg_fx", "bg", "bgm", "se", "voice_id")},
    "assets_total": a_total, "assets_hit": a_hit, "assets_missing_count": a_total - a_hit,
    "asset_missing_list": [{"script": s["script"], "ref": r} for s in scene_objs for r in s["assets_missing"]],
    "voice_ref_lines": v_ref, "voice_hit_lines": v_hit,
    "voice_ids_referenced": len(tot_refs["voice_id"]),
    "voice_ids_in_ledger": sorted({e["orig_name"].rsplit(".", 1)[0].lower()
                                   for e in ledger["entries"]
                                   if e["source"] == SOURCE and e["kind"] == "voice"}),
    "voice_ids_attributed_to_lines": sorted({l["voice"] for s in scene_objs for l in s["lines"] if l["voice"]}),
    "voice_attribution_note": "脚本内共扫出 %d 个语音 ID；语料的 `voice_id` 是「该槽前后 192 字节内最近的 "
                              "ID」启发式（作品 skill §8.1 明确「逐行精确绑定未实现」），故实际被归到某一行的 "
                              "ID 为 %d 个（差 %d 个：脚本内引用但启发式未归到任何槽）。"
                              "语音 ID 的文件命中一律按总账 np/voice 判定。"
                              % (len(tot_refs["voice_id"]),
                                 len({l["voice"] for s in scene_objs for l in s["lines"] if l["voice"]}),
                                 len(tot_refs["voice_id"]) - len({l["voice"] for s in scene_objs for l in s["lines"] if l["voice"]})),
    "voice_ids_present": v_present_ids,
    "voice_ids_missing_count": len(v_missing_ids),
    "voice_ids_missing": v_missing_ids,
    "voice_missing_detail": voice_missing_detail,
    "voice_missing_per_scene": voice_missing_per_scene,
    "engine_noise_lines": [{"script": s["script"], "seq": l["seq"], "index": l["index"], "jp": l["jp"]}
                           for s in scene_objs for l in s["lines"] if l["align_method"] == "np_engine_noise"],
    "menu_text_lines": [{"script": s["script"], "index": l["index"], "jp": l["jp"], "cn": l["cn"]}
                        for s in scene_objs for l in s["lines"] if l["align_method"] == "np_menu_text"],
    "option_string_lines": [{"script": s["script"], "index": l["index"], "jp": l["jp"], "cn": l["cn"]}
                            for s in scene_objs for l in s["lines"] if l["align_method"] == "np_option_string"],
    "speaker_label_lines": [{"script": s["script"], "index": l["index"], "jp": l["jp"]}
                            for s in scene_objs for l in s["lines"] if l["align_method"] == "np_speaker_label"],
    "choices_total": choices_total, "choices_pairing_verified": choices_verified,
    "choices_target_null": choices_null,
    "choices_by_scene": {s["script"]: [{"text_jp": c["text_jp"], "text_cn": c["text_cn"],
                                        "target": c["target"], "pairing_verified": c["pairing_verified"]}
                                       for c in s["choices"]] for s in scene_objs if s["choices"]},
    "next_table": {s["script"]: {"next": s["next"], "next_kind": s["next_kind"]} for s in scene_objs},
    "next_evidence": {**{k: v[1] for k, v in NEXT_TIER_B.items()},
                      **{k: v[1] for k, v in NEXT_TIER_B_MULTI.items()},
                      **{k: v[1] for k, v in NEXT_BRANCH.items()},
                      **NEXT_END},
    "next_unknown": NEXT_UNKNOWN,
    "scenes_with_date": [s["script"] for s in scene_objs if s["game_date"]],
    "empty_slots": sum(s["stats"]["empty_slots"] for s in scene_objs),
    "d14_exceptions": sum(s["stats"]["d14_exceptions"] for s in scene_objs),
    "scene_ids_unique": len(set(s["scene_id"] for s in scene_objs)) == len(scene_objs),
    "per_scene": [{
        "script": s["script"], "phase": s["phase"], "line_count": s["line_count"],
        "voice_count": s["voice_count"], "title_jp": s["title_jp"], "title_cn": s["title_cn"],
        "game_date": s["game_date"], "next": s["next"], "next_kind": s["next_kind"],
        "choices": len(s["choices"]), "cast": s["cast"],
        "assets_total": len(s["assets"]), "assets_hit": sum(1 for a in s["assets"] if a["hit"]),
        "assets_missing": s["assets_missing"],
        "voice_missing": len(voice_missing_per_scene[s["script"]]),
        "corrections_hit": s["stats"]["corrections_hit"],
        "name_replace_count": s["stats"]["name_replace_count"],
        "lines_by_origin": s["stats"]["lines_by_origin"],
    } for s in scene_objs],
}
report["corrections_np_hit_zero_ok"] = (len(np_corr_rows) == 0 and len(corr_hit) == 0)
report["all_corrections_out_of_scope"] = (len(corr_hit_in_scope) == 0 and len(GATED) == 0)
# ISSUE-20260919-06：新增 `修正表_np说话人译名.tsv`（3 条 source=np）后，np 范围内命中不再为 0。
# 新的完整性判据 = **np 范围内条目全部命中（生效 3 / 未命中 0）**，且无门控排除。
report["np_corrections_all_hit"] = (len(miss_corr) == 0 and len(GATED) == 0
                                    and len(corr_hit_in_scope) == len(np_corr_rows))

os.makedirs(STG, exist_ok=True)
json.dump(report, open(os.path.join(STG, "_build_stats_np.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 写出
w("[7/7] 写出 scene_np.jsonl ...")
_assert_in_checkout(OUT, "剧本产物目录")
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "scene_np.jsonl")
_assert_in_checkout(outpath, "scene_np.jsonl")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    for s in scene_objs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
with open(outpath, encoding="utf-8") as f:
    n = sum(1 for ln in f if json.loads(ln))
w("      -> %s （%d 行，逐行 json.loads OK）" % (outpath, n))

# ---------------------------------------------------------------- 摘要
w("")
w("================ 摘要（np 明日香篇） ================")
w("场景数            : %d  (剧情 %d + 菜单 %d + 空脚本 %d)"
  % (report["scenes"], len(STORY), 1, 1))
w("行数              : %d  (语料基线 %d，守恒=%s)" % (tot_lines, baseline, report["lines_balanced"]))
w("逐脚本差异        : %s" % (report["lines_per_script_diff_nonzero"] or "全 0"))
w("kind 分布         : %s" % report["kind_dist"])
w("cn_origin 分布    : %s" % report["orig_dist"])
w("align_method 分布 : %s" % report["align_method_dist"])
w("修正表            : 合计 %d ｜ source=np %d ｜ 命中 %d ｜ 门控排除 %d ｜ 未命中 %d"
  % (len(corr_rows), len(np_corr_rows), len(corr_hit), len(GATED), len(miss_corr)))
w("  范围外(他源)    : %s" % report["corrections_out_of_scope_by_source"])
w("term_unify 幂等 no-op: %d 条（构建期应为 0）%s"
  % (len(TERM_NOOP), (" ← " + str(TERM_NOOP[:3])) if TERM_NOOP else ""))
w("译名替换          : np 规则 %d 条 ｜ 实际发生 %d 处 ｜ 待裁决不生效 %d 条"
  % (len(np_rules), report["term_hits"], len(TERM_PENDING)))
w("素材命中(逐类)    :")
for k in ("sprite", "cg_fx", "bg", "bgm", "se", "voice_id"):
    d = report["assets_class"][k]
    w("      %-9s %d/%d  缺失 %d %s" % (k, d["hit"], d["total"], len(d["missing"]), d["missing"]))
w("语音（逐行）      : %d/%d 引用行有音频；引用 ID %d 个，可得 %d 个，缺失 %d 个"
  % (v_hit, v_ref, report["voice_ids_referenced"], len(v_present_ids), len(v_missing_ids)))
w("选择支            : %d 条（配对确证 %d，target=null %d）"
  % (choices_total, choices_verified, choices_null))
w("next_kind 分布    : %s" % report["next_kind_dist"])
w("有显式日期场景    : %s" % report["scenes_with_date"])
w("scene_id 唯一     : %s" % report["scene_ids_unique"])
w("修正表命中 0 正确 : %s" % report["corrections_np_hit_zero_ok"])
w("np 修正全命中     : %s（source=np %d 条 / 生效 %d / 未命中 %d / 门控排除 %d）"
  % (report["np_corrections_all_hit"], len(np_corr_rows), len(corr_hit_in_scope),
     len(miss_corr), len(GATED)))