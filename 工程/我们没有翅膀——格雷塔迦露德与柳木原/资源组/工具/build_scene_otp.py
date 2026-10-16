# -*- coding: utf-8 -*-
r"""
W6d · 结构化剧本 `scene_otp.jsonl` 构建器（S4 前奏诗 Prelude · 59 场景 / 9,059 槽）

契约：
  - `资源组\剧本\schema.md`（W6a 定稿 schema，**本模块不另创 schema**）
  - `资源组\修正\_README.md` §三（fix_type 枚举）/ §四.2（消费顺序）/ **§四.5（修正表来源门控）**/ §八（D14 取文）
  - `资源组\剧本\亚衣线_产出报告.md`（W6a/W6a2 参考实现）

只读：
  `工程\我们没有翅膀 前奏诗\`（汉化\剧情汉化\*.jsonl、汉化\SCRIPT_CN\*.sob、汉化\交付说明.md）、
  `工程\我们没有翅膀\汉化\剧情汉化\*.jsonl`（仅用于 source_kind 的 jp 对照率实测）、
  `资源组\修正\*`、`资源组\krkr素材库\资源总账.json`
只写：
  `资源组\剧本\scene_otp.jsonl`、`子代理工作区\ISSUE-20260918-06\W6d\_build_stats.json`

与 W6a（亚衣线 s03c / TOB0）的差异（逐条，均已在报告中说明）：
  1. 取文来源 = `otp`（前奏诗独立翻译，D14 合规），故 `cn_base = "otp"`、`text_source = "otp"`；
     `_README.md` §四.5 的门控映射表**已预置** `otp→otp`，本模块直接复用。
  2. `source_kind` 按 §三.1 的定义实测判定：与 2009 本篇**同名脚本**且 jp 重合率 ≥50% → `shared`；
     否则 `new`。实测 otp `02_*`↔本篇 `s02_*`、`03_*`↔本篇 `s03_*`（16+16），另 gameinit/history/title/title2
     共 **36 shared / 23 new**。
     **注意**：本模块 `shared` 只表示「结构上有 2009 同名对照」，**不改变取文**——
     因 D14 只排除 R 版正文，前奏诗译文本身即独立翻译、可直接取用（与 W6a 的 R 版情形不同）。
  3. 本作**无 `kind=title` 槽**（结构上不存在）；篇章标题以各脚本**首条 `kind=other` 槽**表达。
  4. `index` 记源 SOB0 槽序号 `seq`（与修正表 `locator=seq=<n>` 同口径，便于逐条回溯）；
     `lineno` 记源 jsonl 行号（1-based，可直接 `sed -n 'Np'` 定位）。
  5. `assets` 取自**脚本字节码 maps[4] 实际引用的资源串**（`PIC\*.ELG`/`SE\*.OGG`/`SYS\*.ELG`），
     而非外部素材清单（前奏诗素材清单为扁平文件表，无逐脚本关联）。
  6. 说话人：源 jsonl 只有**引擎键标签**（日文，未译名字框，见作品层 SKILL §二 / 交付说明 §六.2）。
     `speaker_jp` = 标签原样；`speaker` = 依作品层/工程层术语表与泛称通则落的中文名（逐条依据见报告 §5）。
  7. `phase` / `route` 按本作自身篇章结构取值（schema 的 序/个人线/结局 三值为 s03c 专属）；
     **不用于断言全系列时序**（前奏诗在系列中的位置语料内无声明）。

复跑：
  python -X utf8 "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_scene_otp.py"
"""
import os, re, json, csv, glob, struct, collections, sys, importlib.util

sys.dont_write_bytecode = True   # 严禁在只读源目录留下 __pycache__
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
STG  = os.path.join(WS_LOCAL, r"子代理工作区\ISSUE-20260918-06\W6d")   # 写本 checkout

OTP_PROJ = os.path.join(DATA_ROOT, r"工程\我们没有翅膀 前奏诗")
CN_DIR   = os.path.join(OTP_PROJ, r"汉化\剧情汉化")
SOB_DIR  = os.path.join(OTP_PROJ, r"汉化\SCRIPT_CN")
OT_CN    = os.path.join(DATA_ROOT, r"工程\我们没有翅膀\汉化\剧情汉化")
LEDGER   = os.path.join(RES, r"krkr素材库\资源总账.json")
OTP_TOOLS = os.path.join(OTP_PROJ, r"工具")
GAME_DIR  = r"D:/Gal/壌偨偪偵梼偼側偄乣Prelude乣"


def _assert_in_checkout(path, what="产物"):
    """边界断言：产物路径必须落在本 checkout 内，否则报错中止（防止误写主工作区）。"""
    p = os.path.abspath(path); c = os.path.abspath(WS_LOCAL)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

# 无文本 .sob 的兜底名单（证据：只读读取原版 `SCRIPT.LPK` 索引实测 69 个 .sob − 59 个有文本者；
# 见 `子代理工作区\ISSUE-20260918-06\W6d\recon_otp.py` 输出）。LPK 可读时以 LPK 为准。
TEXTLESS_FALLBACK = ["advinit", "eyecatch2", "eyecatch3", "func_lib", "gallery",
                     "gamereset", "logo", "main", "movieplay", "user_var"]

TABLES = [
    ("修正表_B1B3.tsv",             os.path.join(FIX, "修正表_B1B3.tsv")),
    ("修正表_B1B3_扩展.tsv",        os.path.join(FIX, "修正表_B1B3_扩展.tsv")),
    ("修正表_新增场景mig重译.tsv",  os.path.join(FIX, "修正表_新增场景mig重译.tsv")),
    # ISSUE-20260930-10：用户 2026-09-30 术语裁决（source 按行门控；field=cn，fix_type=term_unify）
    ("修正表_裁决20260930.tsv",    os.path.join(FIX, "修正表_裁决20260930.tsv")),
]
TERM_TABLE = os.path.join(FIX, "译名替换表.tsv")

SOURCE = "otp"

# ---------------------------------------------------------------- 来源门控（_README §四.5，通用规则）
CORR_SOURCE_TO_BASE = {
    "otr": "otr_new",
    "otp": "otp",
    "ota": "ota",
    "ot":  "ot",
    # 六源全覆盖（ISSUE-20260930-11 补齐 otv/np —— 缺项会让装载该表的本次运行直接 fail loud）
    "otv": "otv",
    "np":  "np",
}
GATED = []          # 被来源门控排除的条目（逐条留痕，不得静默丢弃）
TERM_NOOP = []      # `term_unify` 的幂等 no-op 留痕（ISSUE-20260930-12；构建期应为 0 条）
CORR_HIT = set()    # (source,file,locator)

# ---------------------------------------------------------------- 篇章结构（证据：各脚本首条 kind=other 槽 + 交付说明 §二）
# 前奏诗结构：框架剧 buru01–04（前説/幕間/アンコール/閉幕）+ 角色短篇 p01–p04 + 邂逅线 02/03
PHASE_ROUTE = {
    "buru01": ("序",   "前奏诗 框架剧 buru"),
    "buru02": ("框架", "前奏诗 框架剧 buru"),
    "buru03": ("框架", "前奏诗 框架剧 buru"),
    "buru04": ("结局", "前奏诗 框架剧 buru"),
    "staff":  ("结局", "前奏诗 制作人员"),
    "gameinit": ("系统", "前奏诗 系统脚本"),
    "history":  ("系统", "前奏诗 系统脚本"),
    "title":    ("系统", "前奏诗 系统脚本"),
    "title2":   ("系统", "前奏诗 系统脚本"),
}
PREFIX_ROUTE = {
    "p01_": ("个人线", "前奏诗 p01 明日香篇"),
    "p02_": ("个人线", "前奏诗 p02 山科京篇"),
    "p03_": ("个人线", "前奏诗 p03 美咲篇"),
    "p04_": ("个人线", "前奏诗 p04 轻部狩男篇"),
    "02_":  ("主线",   "前奏诗 02 邂逅·鹫介"),
    "03_":  ("主线",   "前奏诗 03 邂逅·隼人"),
}
STORY_PREFIX = ("p01_", "p02_", "p03_", "p04_", "02_", "03_", "buru")

# ---------------------------------------------------------------- 说话人标签 → 名字框中文
# 依据（逐条，报告 §5 有完整表）：
#   §一  = 前奏诗 作品层术语表 §一「说话人标签」（备注列的「正文」写法）
#   §二/§三 = 前奏诗 作品层术语表 §二 人名 / §三 地名组织特定名词
#   §7-10 = 前奏诗 作品层术语表 §七–§十 跨批裁决
#   G§2.1/2.2/2.5 = 工程层术语表《格雷塔迦露德与柳木原》§2.1 人名 / §2.2 称谓 / §2.5 特定名词
#   泛称  = 前奏诗 作品层术语表 §一 明示「泛称标签按泛称通则落译」+ 通用层 SKILL §四/§五 泛称通则
SPEAKER_CN = {
    # —— 专名（作品层有据）
    "鷲介": ("鹫介", "前奏诗术语表 §一 备注「正文『鹫介』」；G§2.1 千歳 鷲介→千岁 鹫介"),
    "隼人": ("隼人", "G§2.1 成田 隼人→成田 隼人"),
    "狩男": ("狩男", "前奏诗术语表 §一（同形汉字）；G§2.1 軽部→轻部"),
    "日和子": ("日和子", "前奏诗术语表 §一 备注「正文『日和子』」；G§2.1 玉泉 日和子"),
    "紀奈子": ("纪奈子", "前奏诗术语表 §一 备注「正文『纪奈子』」"),
    "鳴": ("鸣", "前奏诗术语表 §一 备注「正文『鸣』」"),
    "英里子": ("英里子", "前奏诗术语表 §一 备注「正文『英里子』」"),
    "優": ("优", "前奏诗术语表 §一 备注「正文『优』」"),
    "春恵": ("春惠", "前奏诗术语表 §一 备注「正文『春惠』」"),
    "明日香": ("明日香", "前奏诗术语表 §一 备注「正文『明日香』」"),
    "カケル": ("翔", "前奏诗术语表 §一「同一角色两种写形；正文『翔』」"),
    "翔": ("翔", "前奏诗术语表 §一"),
    "美咲": ("美咲", "前奏诗术语表 §一 备注「正文『美咲』」"),
    "シトラス": ("西特拉斯", "前奏诗术语表 §一/§三之二（主代理裁定）"),
    "ミネオラ": ("米内奥拉", "前奏诗术语表 §一/§三之二（主代理裁定）"),
    "亜衣": ("亚衣", "前奏诗术语表 §一 备注「正文『亚衣』」"),
    "バニィＤ": ("巴尼Ｄ", "前奏诗术语表 §一；G§2.1 巴尼Ｄ（全角Ｄ）"),
    "京": ("京", "前奏诗术语表 §一 备注「正文『京』」"),
    "ＬＲ２００１": ("ＬＲ２００１", "前奏诗术语表 §一（全角英文数字，不译）"),
    "小娘": ("小丫头", "前奏诗术语表 §一（标签）；证据：03_03b 选项译文「配合小丫头的节奏」、03_03b 标题「欢迎光临，小丫头大人」"),
    "チケドン": ("奇肯多", "前奏诗术语表 §一 备注「正文『奇肯多』」；G§2.1 奇肯多"),
    "和馬": ("和马", "前奏诗术语表 §一 备注「正文『和马』」"),
    "いづみ": ("多摩泉", "前奏诗术语表 §一 备注「正文『多摩泉』」；G§2.1 多摩 いづみ→多摩 泉"),
    "ポンカン": ("椪柑", "前奏诗术语表 §一/§三之二（原词即水果名）"),
    "高内": ("高内", "前奏诗术语表 §一"),
    "プラチナ": ("普纳奇纳", "前奏诗术语表 §一；G§2.1 普纳奇纳"),
    "アリス": ("爱丽丝", "前奏诗术语表 §一"),
    "コーダイン": ("科达因", "前奏诗术语表 §一/§三之二"),
    "針生": ("针生", "前奏诗术语表 §一 备注「正文『针生』」"),
    "山科": ("山科", "前奏诗术语表 §一"),
    "マルチネス": ("马汀内斯", "前奏诗术语表 §一"),
    "エージ": ("艾吉", "前奏诗术语表 §一/§三之二"),
    "玉泉": ("玉泉", "前奏诗术语表 §一"),
    "小鳩": ("小鸠", "前奏诗术语表 §一 备注「正文『小鸠』」"),
    "ヨーゼフ": ("约瑟夫", "前奏诗术语表 §一/§三之二"),
    "狂夜": ("狂夜", "前奏诗术语表 §二"),
    "ペガサス": ("佩格萨斯", "G§2.5 ペガサス→佩格萨斯（D3 新米仲裁；旧写法「佩加索斯」见 otp/body 替换规则）"),
    "満夜": ("满夜", "前奏诗术语表 §二"),
    "ブルオラ": ("布鲁奥拉", "前奏诗术语表 §三之二"),
    "羽田": ("羽田", "前奏诗术语表 §二"),
    "バニィ君": ("巴尼君", "バニィＤ→巴尼Ｄ（前奏诗术语表 §一）＋ 君（通用层 §五.3）"),
    "ＬＲ君": ("ＬＲ君", "前奏诗术语表 §一 ＬＲ２００１（不译）＋ 君"),
    "いづみ？": ("多摩泉？", "いづみ→多摩泉（前奏诗术语表 §一）＋ 疑问标记"),
    # —— 泛称（前奏诗术语表 §一 明示「按泛称通则落译」；通用层 SKILL §四/§五）
    "太ったハゲ": ("胖秃头", "泛称（前奏诗术语表 §一 明示泛称标签按泛称通则落译）"),
    "母親": ("母亲", "前奏诗术语表 §七 お母さん→母亲（覆盖通用层「妈妈」）"),
    "牧師": ("牧师", "泛称"),
    "監督": ("导演", "泛称（02_03b 选项「監督に従う→听从导演」同源）"),
    "祖母": ("祖母", "泛称"),
    "子供": ("小孩", "泛称"),
    "男子Ａ": ("男学生Ａ", "G§2.1 男子Ａ→男学生Ａ（非替换项）"),
    "男子Ｂ": ("男学生Ｂ", "同 男子Ａ"),
    "声": ("声音", "泛称"),
    "男": ("男人", "泛称"),
    "不良Ａ": ("不良Ａ", "泛称（保留字母标记）"),
    "不良Ｂ": ("不良Ｂ", "泛称"),
    "不良Ｃ": ("不良Ｃ", "泛称"),
    "上級生Ａ": ("高年级学生Ａ", "泛称（上級生→高年级学生）"),
    "野良犬": ("野狗", "泛称"),
    "図書館職員": ("图书馆职员", "泛称"),
    "ウェイトレス": ("女服务员", "泛称"),
    "作業員Ａ": ("作业员Ａ", "泛称"),
    "作業員Ｂ": ("作业员Ｂ", "泛称"),
    "友人": ("朋友", "泛称"),
    "女性客": ("女客", "泛称"),
    "男性客": ("男客", "泛称"),
    "男性編集者": ("男编辑", "泛称"),
    "鷲介＆日和子": ("鹫介＆日和子", "合成标签（鷲介＋日和子）"),
    "鷲介＆英里子": ("鹫介＆英里子", "合成标签（鷲介＋英里子）"),
    "ＹＦＢ一同": ("ＹＦＢ众人", "G§2.1 一同→众人（非替换项）"),
    "精霊": ("精灵", "泛称"),
    "車内アナウンス": ("车内广播", "泛称"),
    "長い髪の女": ("长发女子", "泛称"),
    "女の声": ("女声", "泛称"),
    "男の声": ("男声", "泛称"),
    "待ちぶせていた男": ("埋伏的男人", "泛称"),
    "奥にいたロン毛": ("里面的长发男", "泛称"),
    "ロン毛のツレ": ("长发男的同伴", "泛称"),
    "女装の男": ("女装男", "泛称"),
    "ＡＤさん": ("ＡＤ先生", "泛称（ＡＤ＝アシスタントディレクター；保留 ＡＤ 缩写）"),
    "医師": ("医生", "泛称"),
    "水": ("水", "泛称"),
    "水がめ": ("水缸", "泛称"),
    "ハゲの仲間たち": ("秃头同伙们", "泛称"),
    "左にいたレゲエ風": ("左边那个雷鬼风", "泛称"),
    "右にいたギャル男": ("右边那个辣妹男", "泛称"),
    "馬鹿全員": ("全体笨蛋", "泛称"),
    "金髪の少女": ("金发少女", "泛称"),
    "不健康そうな男": ("看着不健康的男人", "泛称"),
    "黒人の客": ("黑人客人", "泛称"),
}

# 已确证的选择支语义（选项↔目标场景的**推定**配对；配对未逆向，pairing_verified 一律 false）
# 依据：目标场景自身首条 kind=other 槽（标题）的语义
CHOICE_TARGET = {
    "02_03g": {"はい": ("02_03g1", "目标场景标题「胸が好きかと問われて肯定」（肯定）与选项「はい」同义"),
               "いいえ": ("02_03g2", "目标场景标题「胸が好きかと問われて否定」（否定）与选项「いいえ」同义"),
               "どちらとも言えない": ("02_03g3", "目标场景标题「胸が好きかと問われて沈黙」（沉默）与选项「どちらとも言えない」同义")},
    "03_03b": {"小娘のノリに合わせる": ("03_03c1", "目标场景标题「相性チェック成功」（契合度检查成功）与选项「合わせる」同向"),
               "小娘のノリを断ちきる": ("03_03c2", "目标场景标题「相性チェック失敗」（契合度检查失败）与选项「断ちきる」同向")},
    "03_03i": {"それはあるかも": ("03_03j1", "目标场景标题「また会うんじゃね？」（还会再见吧）与选项「あるかも」同向"),
               "それはないだろ": ("03_03j2", "目标场景标题「もう会わないんじゃね？」（不会再见面了吧）与选项「ないだろ」同向")},
}

RES_RE = re.compile(r"^(?:CHR|PIC|SYS|SE|BGM|VOICE|DATA)\\[A-Za-z0-9_.\-]+\.(?:ELG|OGG|MPG|GMP|LAG)$", re.I)
DIR2KIND = {"CHR": "chr", "PIC": "pic", "SYS": "sys", "SE": "se", "BGM": "bgm", "VOICE": "voice", "DATA": "movie"}
LAB_RE = re.compile(rb"[0-9A-Za-z_]{4,12}")


def w(s):
    sys.stdout.write(s + "\n"); sys.stdout.flush()


def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def parse_sob0(d):
    """返回 (maps, strings_start, strings_end, header_end)；maps[4] = 字符串指针表"""
    table_size = u32(d, 4)
    table_end = table_size + 8
    off = 8
    maps = []
    while off < table_end:
        n = u32(d, off); off += 4
        m = {}
        for _ in range(n):
            m[u32(d, off)] = u32(d, off + 4); off += 8
        maps.append(m)
    ss, se = u32(d, off), u32(d, off + 4)
    return maps, ss, se, off + 8


def read_ref_string(d, p):
    c = d[p]
    p = p + 3 if c == 0 else p
    f = d[p] if p < len(d) else 0
    if f in (2, 3):
        p += 4
    e = d.find(b"\x00", p)
    return d[p:e]


# ================================================================ [1] 输入
w("[1/7] 读取输入 ...")
scenes_raw = []
for p in sorted(glob.glob(os.path.join(CN_DIR, "*.jsonl"))):
    sc = os.path.basename(p)[:-len(".sob.jsonl")]
    rows = [json.loads(l) for l in open(p, encoding="utf-8")]
    scenes_raw.append({"script": sc, "file": os.path.basename(p), "lines": rows})
w("      场景 %d ｜ 槽 %d" % (len(scenes_raw), sum(len(s["lines"]) for s in scenes_raw)))
BASELINE_SLOTS = sum(len(s["lines"]) for s in scenes_raw)
assert BASELINE_SLOTS == 9059, BASELINE_SLOTS

# 2009 本篇 jp 集合（仅用于 source_kind 实测，不改取文）
ot_jp = collections.defaultdict(set)
for p in glob.glob(os.path.join(OT_CN, "*.jsonl")):
    osc = os.path.basename(p)[:-len(".sob.jsonl")]
    for ln in open(p, encoding="utf-8"):
        o = json.loads(ln)
        if (o.get("jp") or "").strip():
            ot_jp[o["jp"]].add(osc)
w("      本篇 jp 集合 %d" % len(ot_jp))

# ================================================================ [2] 修正表
w("[2/7] 装载修正表 ...")
corrections = {}
corr_rows = []
for tname, tpath in TABLES:
    for r in read_tsv(tpath):
        r["_table"] = tname
        corr_rows.append(r)
        key = (r["source"], r["file"], r["locator"])
        if key in corrections:
            raise SystemExit("!! 修正表定位冲突: %s" % (key,))
        corrections[key] = r
w("      修正表合计 %d 条（B1B3=%d / 扩展=%d / 新增mig重译=%d）" % (
    len(corr_rows),
    sum(1 for r in corr_rows if r["_table"] == "修正表_B1B3.tsv"),
    sum(1 for r in corr_rows if r["_table"] == "修正表_B1B3_扩展.tsv"),
    sum(1 for r in corr_rows if r["_table"] == "修正表_新增场景mig重译.tsv")))

# ================================================================ [3] 译名替换表
w("[3/7] 装载译名替换表 ...")
# 消费侧规则①：`新写法` 列尾部误带置信度批注（如「苍穹女子学院（低置信）」）——
# 批注是表格元信息，**不得写进游戏文本**，故在消费侧剥离；表本体未改（待主代理裁决是否回改表）。
ANNOT_RE = re.compile(r"（(?:低置信|中置信|高置信|待确认|待裁决|待定)）\s*$")
ANNOT_STRIPPED = []


def clean_new(s):
    t = ANNOT_RE.sub("", s).strip()
    return t


TERM_RULES = []
for r in read_tsv(TERM_TABLE):
    new, old = r["新写法"].strip(), r["旧写法"].strip()
    scope = r["适用范围(源代号)"].strip()
    if new.startswith("（") or old.startswith("（") or scope == "—":
        continue                      # 待裁决 / 非替换项 / 无旧写法残留
    if "/" in scope:
        src, stream = scope.split("/", 1)
    else:
        src, stream = scope, "body"
    if src == "全部":
        continue
    new_c = clean_new(new)
    if new_c != new:
        ANNOT_STRIPPED.append({"原词日文": r["原词日文"].strip(), "旧写法": old,
                               "表新写法": new, "实写": new_c, "scope": scope})
    TERM_RULES.append({"jp": r["原词日文"].strip(), "old": old, "new": new_c,
                       "src": src, "stream": "name" if stream == "name" else "body"})
OTP_RULES = [r for r in TERM_RULES if r["src"] == SOURCE]
w("      可用规则 %d 条（其中 otp %d 条：%s）"
  % (len(TERM_RULES), len(OTP_RULES), ", ".join("%s→%s" % (r["jp"], r["new"]) for r in OTP_RULES)))
w("      消费侧剥离置信度批注 %d 条：%s" % (len(ANNOT_STRIPPED),
      "; ".join("%s：%s → %s" % (a["原词日文"], a["表新写法"], a["实写"]) for a in ANNOT_STRIPPED) or "无"))

# §六 排除规则（正则），键 = (原词日文, 旧写法)；与 W6a 同口径
EXCL = {
    ("渡来さん", "渡来（裸名）"): re.compile(r"渡来(?!同学|明日香|家|屋|前辈|学姐|Ｓ香)"),
    ("委員長", "委员长"):        re.compile(r"(?<!执行)委员长"),
    ("ハヤブサ", "隼"):          re.compile(r"(?<!游)隼(?!人)"),
    ("ソラ学", "空学"):          re.compile(r"(?<!美)空学(?!院|府)"),
    ("針生", "针生"):            re.compile(r"针生(?!同学|前辈|君|先生|小姐|老师|哥|姐)"),
    ("ガルーダ", "伽楼罗"):      re.compile(r"(?<!伊丹)伽楼罗"),
}
JP_SKIP = {"ガルーダ": ["伽楼羅"]}
CONTEXT_FLAGGED = {"ペガサス", "ドラさん"}
# 消费侧规则②：`針生`→`针生同学` 的语义是「补回被漏掉的 `さん` 敬称」（工程层 §2.2 針生さん→针生同学），
# 故须与「渡来さん」同口径——**仅当原文确含 `針生さん`** 才替换。
# 实测（本模块）：otp 12 个 jp 含 `針生` 的槽**全部**是 `針生先輩`(8) / `針生蔵人`(4，全名)，
# 无 `針生さん`；裸替换会把全名改成「针生同学藏人」（错），故本门槛使该规则在 otp 命中 0 处。
JP_CONTEXT = {("針生", "针生"): "針生さん"}

# ================================================================ [4] 素材总账（otp）
w("[4/7] 建立素材总账 otp 索引 ...")
ledger = json.load(open(LEDGER, encoding="utf-8"))
idx = collections.defaultdict(dict)
for e in ledger["entries"]:
    if e["source"] != SOURCE:
        continue
    idx[e["kind"]][os.path.splitext(e["orig_name"])[0].lower()] = e["out_relpath"]
w("      otp 索引 %s" % {k: len(v) for k, v in idx.items()})

# ================================================================ [5] 脚本字节码：跳转标签 + 资源引用
w("[5/7] 扫描 .sob 字节码（跳转标签 / maps[4] 资源引用） ...")
script_names = set(s["script"] for s in scenes_raw)


def list_sob_from_lpk():
    """只读读取原版 SCRIPT.LPK 索引，返回 69 个 .sob 名（失败返回 None）。"""
    lp_path = os.path.join(GAME_DIR, "SCRIPT.LPK")
    mod_path = os.path.join(OTP_TOOLS, "lpk_patch.py")
    if not (os.path.isfile(lp_path) and os.path.isfile(mod_path)):
        return None
    try:
        spec = importlib.util.spec_from_file_location("_otp_lpk_patch", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        lp = mod.load(lp_path)
        return sorted(os.path.splitext(n)[0] for n, _ in lp["ents"] if n.lower().endswith(".sob"))
    except Exception as e:                                    # noqa: BLE001
        w("      [warn] LPK 索引读取失败（%s），改用兜底名单" % e)
        return None


lpk_sobs = list_sob_from_lpk()
if lpk_sobs:
    all_sob = set(lpk_sobs)
    w("      原版 SCRIPT.LPK 索引实测 .sob = %d 个" % len(all_sob))
else:
    all_sob = set(script_names) | set(TEXTLESS_FALLBACK)
    w("      [warn] 使用兜底名单：.sob = %d 个" % len(all_sob))
TEXTLESS = sorted(all_sob - script_names)

next_map, refs_map, labels_raw = {}, {}, {}
avail = sorted(os.path.splitext(os.path.basename(f))[0]
               for f in glob.glob(os.path.join(SOB_DIR, "*.sob")))
for sc in avail:
    d = open(os.path.join(SOB_DIR, sc + ".sob"), "rb").read()
    labs = []
    for m in LAB_RE.findall(d):
        t = m.decode("ascii").lower()
        # 只收「有文本场景脚本名」：无文本系统脚本名（main/logo/gallery…）短且易与正文 ASCII 字节碰撞，会误报
        if t in script_names and t != sc and t not in labs:
            labs.append(t)
    next_map[sc] = sorted(labs)
    labels_raw[sc] = labs
    maps, ss, se, he = parse_sob0(d)
    refs = set()
    for addr, v in maps[4].items():
        if not (ss <= v < se):
            continue
        s = read_ref_string(d, v + he)
        try:
            t = s.decode("ascii")
        except UnicodeDecodeError:
            continue
        if RES_RE.match(t):
            refs.add(t)
    refs_map[sc] = sorted(refs)
w("      .sob %d 个（有文本 %d / 无文本 %d）｜ 引用资源 %d 处 / %d 个不同"
  % (len(all_sob), len(script_names), len(TEXTLESS),
     sum(len(v) for v in refs_map.values()),
     len(set(r for v in refs_map.values() for r in v))))
w("      无文本脚本（10 个，如实标注）：%s" % ", ".join(TEXTLESS))

# ================================================================ [6] 组装
w("[6/7] 组装 %d 场景 ..." % len(scenes_raw))


def apply_term(cn, jp):
    hits = []
    if not cn:
        return cn, hits
    for rule in OTP_RULES:
        if rule["stream"] != "body":
            continue
        if rule["jp"] not in jp:
            continue
        ctx = JP_CONTEXT.get((rule["jp"], rule["old"]))
        if ctx and ctx not in jp:
            continue                                   # 原文语境门控（如 針生 须为 針生さん）
        skip = JP_SKIP.get(rule["jp"])
        if skip and any(s in jp for s in skip):
            continue
        rx = EXCL.get((rule["jp"], rule["old"]))
        new_cn = rx.sub(rule["new"], cn) if rx is not None else cn.replace(rule["old"], rule["new"])
        if new_cn != cn:
            hits.append({"原词日文": rule["jp"], "旧写法": rule["old"], "新写法": rule["new"],
                         "字段": "body", "before": cn, "after": new_cn,
                         "context_flag": rule["jp"] in CONTEXT_FLAGGED})
            cn = new_cn
    return cn, hits


def map_ref(ref):
    d, fn = ref.split("\\", 1) if "\\" in ref else ("", ref)
    kind = DIR2KIND.get(d.upper(), "etc")
    return kind, idx.get(kind, {}).get(os.path.splitext(fn)[0].lower())


def build_scene(s):
    sc, file_ = s["script"], s["file"]
    # ---- source_kind：按 §三.1 定义实测（同名 2009 脚本 + jp 重合率 ≥50%）
    cp = sc if sc in ("gameinit", "history", "title", "title2", "staff") else ("s" + sc if sc[0].isdigit() else None)
    jps = [l.get("jp") or "" for l in s["lines"]]
    n_jp = sum(1 for j in jps if j.strip())
    same = sum(1 for j in jps if j.strip() and cp and cp in ot_jp.get(j, ()))
    ov_rate = (100.0 * same / n_jp) if n_jp else 0.0
    source_kind = "shared" if (cp and ov_rate >= 50.0) else "new"

    # ---- 篇章
    phase, route = None, None
    if sc in PHASE_ROUTE:
        phase, route = PHASE_ROUTE[sc]
    else:
        for pre, pr in PREFIX_ROUTE.items():
            if sc.startswith(pre):
                phase, route = pr
                break
    if phase is None:
        raise SystemExit("!! 未定篇章: " + sc)

    is_story = sc.startswith(STORY_PREFIX)
    choice_seqs = set()

    lines_out = []
    cast = []
    voices = set()
    by_origin = collections.Counter()
    fix_n = name_n = empty_n = 0
    layers_used = set()
    title_line = None

    for i, l in enumerate(s["lines"], 1):
        src_seq = l["seq"]
        jp = l.get("jp") or ""
        cn = l.get("cn") or ""
        speaker_jp = l.get("speaker") or ""
        kind = l.get("kind") or ""
        is_choice = l.get("sel", 0) != 0
        if is_choice:
            choice_seqs.add(i)

        # ---- ① 取文（D14：otp 为独立翻译源，直接取用）
        fix_refs = []
        if not jp and not cn:
            base, align, empty_slot = "empty", "empty_slot", True
            empty_n += 1
        else:
            base, align, empty_slot = "otp", "otp_direct", False
        layers = [] if base == "empty" else [base]

        # ---- ② 修正表（(source,file,locator) 三元组定位 → §四.5 来源门控）
        loc = "seq=%d" % src_seq
        row = corrections.get((SOURCE, file_, loc))
        if row is not None:
            want = CORR_SOURCE_TO_BASE.get(row["source"])
            if want is None:
                raise SystemExit("!! 修正表 source 未登记门控映射: %s @ %s/%s" % (row["source"], file_, loc))
            # `term_unify` 与取文层无关 ⇒ 不受来源门控约束（见 `修正\_README.md` §四.5）
            if want == base or row["fix_type"] == "term_unify":
                cn_before = cn
                if row["fix_type"] == "term_unify":
                    # ISSUE-20260930-12：`term_unify` 是**词形级替换**——`old_text` = 词形正则、
                    # `new_text` = 替换值（**不是整句**）。命中即 re.sub；已是后态 ⇒ 幂等 no-op
                    # （不记 fix_refs、不计命中）；两者都不是 ⇒ fail loud。
                    cn, tu_state = _term_unify.apply(cn, row["old_text"], row["new_text"])
                else:
                    # old_text 逐字符断言（与其余构建器同口径）：不符即 fail loud
                    if (row.get("old_text") or "") != (cn_before or ""):
                        raise SystemExit("!! 修正表 old_text 与源译文不符: %s/%s（源=%r 表=%r）"
                                         % (file_, loc, cn_before, row.get("old_text")))
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
                    fix_n += 1
                    CORR_HIT.add((SOURCE, file_, loc))
            else:
                GATED.append({"table": row["_table"], "source": row["source"], "file": file_,
                              "locator": loc, "kind": row["kind"], "fix_type": row["fix_type"],
                              "script": sc, "line_seq": src_seq, "cn_base": base, "jp": jp,
                              "cn_kept": cn, "cn_gated": row["new_text"], "old_text": row["old_text"],
                              "reason": "source_gate: 条目 source=%s 对应取文基准 %s，而该行取文基准为 %s → 不生效"
                                        % (row["source"], want, base)})
        # 其余 source（otr/ota/ot）的条目在本模块一律无对象 → 逐条留痕（见 [7] 段）
        for k, r2 in corrections.items():
            if k[0] == SOURCE:
                continue
            if r2["file"] == file_ and r2["locator"] == loc:
                GATED.append({"table": r2["_table"], "source": r2["source"], "file": file_,
                              "locator": loc, "kind": r2["kind"], "fix_type": r2["fix_type"],
                              "script": sc, "line_seq": src_seq, "cn_base": base, "jp": jp,
                              "cn_kept": cn, "cn_gated": r2["new_text"], "old_text": r2["old_text"],
                              "reason": "source_gate: 本模块取文基准层为 %s，条目 source=%s 属他源语料 → 无对象、不生效"
                                        % (base, r2["source"])})

        # ---- ③ 译名替换（JP 门控；otp 仅有 body 流规则）
        cn, hits = apply_term(cn, jp)
        if hits:
            layers.append("name_replace")
            name_n += len(hits)
        layers_used.update(layers)

        origin = base
        for lay in layers:
            if lay == "name_replace":
                continue
            if {"empty": 0, "otp": 1, "fix_table": 3, "retranslate": 4}.get(lay, -1) > \
               {"empty": 0, "otp": 1, "fix_table": 3, "retranslate": 4}.get(origin, -1):
                origin = lay
        if not layers:
            origin = "empty"
        by_origin[origin] += 1

        vid = l.get("voice") or ""
        audio = []
        if vid:
            voices.add(vid)
            p = idx["voice"].get(vid.lower())
            if p:
                audio.append(p)

        # ---- cast
        if kind == "dialogue" and speaker_jp:
            nm = SPEAKER_CN.get(speaker_jp, (speaker_jp, ""))[0]
            if nm not in cast:
                cast.append(nm)
        elif is_story and kind == "other" and not speaker_jp and jp.strip() and i != 1 and not is_choice:
            if "旁白" not in cast:
                cast.append("旁白")

        lines_out.append({
            "seq": i, "index": src_seq, "lineno": i, "kind": kind,
            "speaker": SPEAKER_CN.get(speaker_jp, (speaker_jp, ""))[0],
            "speaker_jp": speaker_jp, "voice": vid, "jp": jp, "cn": cn,
            "cn_origin": origin, "cn_base": base, "align_method": align,
            "layers": layers, "fix_refs": fix_refs, "name_replaced": hits,
            "empty_slot": empty_slot, "d14_exception": None, "audio": audio,
        })
        if is_story and i == 1:
            title_line = lines_out[-1]

    # ---- 标题（本作无 kind=title 槽；标题 = 首条 kind=other 槽）
    if title_line is not None:
        title_jp, title_cn = title_line["jp"], title_line["cn"]
        title_variants = [{"offset": s["lines"][0].get("addr"),
                           "jp": title_jp, "cn": title_cn, "cn_origin": title_line["cn_origin"]}]
    else:
        title_jp = title_cn = None
        title_variants = []

    # ---- 后继
    nxt = next_map.get(sc, [])
    nk = "end" if not nxt else ("linear" if len(nxt) == 1 else "branch")

    # ---- 选择支
    choices = []
    if choice_seqs:
        for l in lines_out:
            if l["seq"] not in choice_seqs:
                continue
            t = CHOICE_TARGET.get(sc, {}).get(l["jp"])
            ev = ("%s.sob 字节码选择支串实测（sel/idx 标记）；候选目标 %s；"
                  "选项↔目标**配对未逆向**（SOB0 分支语义未逆向，总纲 R1）"
                  % (sc, "/".join(x.upper() for x in nxt)))
            if t:
                ev += "；按目标场景标题语义**推定** target=%s（%s），未确证" % (t[0], t[1])
            choices.append({"text_jp": l["jp"], "text_cn": l["cn"] or None,
                            "cn_origin": "otp" if l["cn"] else None,
                            "target": t[0] if t else None,
                            "pairing_verified": False, "confirmed": True,
                            "evidence": ev})

    # ---- 素材
    assets, missing = [], []
    for ref in refs_map.get(sc, []):
        k, p = map_ref(ref)
        if p:
            assets.append({"ref": ref, "kind": k, "out_relpath": p, "hit": True})
        else:
            assets.append({"ref": ref, "kind": k, "out_relpath": None, "hit": False})
            missing.append(ref)

    # ---- text_source（按取文基准层汇总）
    bases = set(l["cn_base"] for l in lines_out if l["cn_base"] != "empty")
    text_source = "otp" if not bases else ("otp" if bases == {"otp"} else "mixed")

    return {
        "scene_id": "%s_%s" % (SOURCE, sc),
        "source": SOURCE, "script": sc, "source_kind": source_kind, "text_source": text_source,
        "title_jp": title_jp, "title_cn": title_cn, "title_variants": title_variants,
        "game_date": None, "game_dates": [],
        "phase": phase, "route": route, "cast": cast,
        "next": nxt, "next_kind": nk, "choices": choices,
        "line_count": len(lines_out), "voice_count": len(voices),
        "assets": assets, "assets_missing": missing,
        "stats": {
            "lines_by_origin": dict(by_origin),
            "lines_by_source": {},           # 前奏诗 jsonl 无 src 字段（R 版专有），如实为空
            "corrections_hit": fix_n,
            "name_replace_count": name_n,
            "empty_slots": empty_n,
            "d14_exceptions": 0,
            "jp_overlap_2009": {"counterpart": cp, "same": same, "jp_lines": n_jp,
                                "rate_pct": round(ov_rate, 1)},
        },
        "lines": lines_out,
    }


scene_objs = [build_scene(s) for s in scenes_raw]

# ================================================================ [7] 自检
w("[7/7] 自检 ...")
in_scope = [r for r in corr_rows if r["source"] == SOURCE]
miss_corr = [(r["_table"], r["source"], r["file"], r["locator"], r["fix_type"]) for r in in_scope
             if (r["source"], r["file"], r["locator"]) not in CORR_HIT]
gated_full = set((g["source"], g["file"], g["locator"]) for g in GATED)
out_scope = [r for r in corr_rows if (r["source"], r["file"], r["locator"]) not in CORR_HIT
             and (r["source"], r["file"], r["locator"]) not in gated_full]
# 非 otp 源的条目逐条登记（本模块无对象）
gated_other = [{"table": r["_table"], "source": r["source"], "file": r["file"], "locator": r["locator"],
                "kind": r["kind"], "fix_type": r["fix_type"],
                "reason": "本模块取文基准层恒为 otp/empty，条目 source=%s 属他源语料 → 无对象、不生效"
                          % r["source"]}
               for r in corr_rows if r["source"] != SOURCE]

tot_lines = sum(s["line_count"] for s in scene_objs)
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
choice_total = sum(len(s["choices"]) for s in scene_objs)
choice_pts = [s["script"] for s in scene_objs if s["choices"]]

report = {
    "module": "W6d", "source": SOURCE,
    "scenes": len(scene_objs), "lines_total": tot_lines,
    "lines_baseline_jsonl": BASELINE_SLOTS,
    "lines_balanced": tot_lines == BASELINE_SLOTS,
    "scene_ids_unique": len(set(s["scene_id"] for s in scene_objs)) == len(scene_objs),
    "textless_sobs": TEXTLESS, "textless_count": len(TEXTLESS),
    "orig_dist": dict(orig_dist), "src_dist": dict(src_dist),
    "corrections_total": len(corr_rows),
    "corrections_in_scope_otp": len(in_scope),
    "corrections_hit_in_scope": len(in_scope) - len(miss_corr),
    "corrections_missing_in_scope": miss_corr,
    "corrections_gated_in_scope": sum(1 for g in GATED if g["source"] == SOURCE),
    "corrections_gated_out": GATED,
    # ISSUE-20260930-12：`term_unify` 的幂等 no-op 留痕（构建期应为 0——每个目标槽都应命中词形）
    "term_unify_noop": TERM_NOOP,
    "corrections_gated_other_source": gated_other,
    "corrections_gated_other_by_table_source": collections.Counter(
        (g["table"], g["source"]) for g in gated_other).most_common(),
    "corrections_out_of_scope": collections.Counter((r["source"] or "-", r["_table"]) for r in out_scope).most_common(),
    "choice_points": choice_pts, "choice_slots": choice_total,
    "choices": [{"script": s["script"], "text_jp": c["text_jp"], "text_cn": c["text_cn"],
                 "target": c["target"], "pairing_verified": c["pairing_verified"],
                 "evidence": c["evidence"]} for s in scene_objs for c in s["choices"]],
    "assets_total": a_total, "assets_hit": a_hit, "assets_missing": a_total - a_hit,
    "asset_missing_list": [{"script": s["script"], "ref": r} for s in scene_objs for r in s["assets_missing"]],
    "voice_refs": v_ref, "voice_hit": v_hit,
    "term_hits": sum(s["stats"]["name_replace_count"] for s in scene_objs),
    "term_rules_otp": [{"原词日文": r["jp"], "旧写法": r["old"], "新写法": r["new"]} for r in OTP_RULES],
    "term_annot_stripped": ANNOT_STRIPPED,
    "term_jp_context_rules": [{"原词日文": k[0], "旧写法": k[1], "须含原文": v} for k, v in JP_CONTEXT.items()],
    "empty_slots": sum(s["stats"]["empty_slots"] for s in scene_objs),
    "d14_exceptions": sum(s["stats"]["d14_exceptions"] for s in scene_objs),
    "text_source_dist": dict(collections.Counter(s["text_source"] for s in scene_objs)),
    "source_kind_dist": dict(collections.Counter(s["source_kind"] for s in scene_objs)),
    "phase_dist": dict(collections.Counter(s["phase"] for s in scene_objs)),
    "route_dist": dict(collections.Counter(s["route"] for s in scene_objs)),
    "next_kind_dist": dict(collections.Counter(s["next_kind"] for s in scene_objs)),
    "scenes_with_date": [s["script"] for s in scene_objs if s["game_date"]],
    "align_method_dist": dict(collections.Counter(l["align_method"] for s in scene_objs for l in s["lines"])),
    "kind_dist": dict(collections.Counter(l["kind"] for s in scene_objs for l in s["lines"])),
    "speaker_label_count": len(set(l["speaker_jp"] for s in scene_objs for l in s["lines"] if l["speaker_jp"])),
    "speaker_unmapped": sorted(set(l["speaker_jp"] for s in scene_objs for l in s["lines"]
                                   if l["speaker_jp"] and l["speaker_jp"] not in SPEAKER_CN)),
    "speaker_map_used": sorted(set(l["speaker_jp"] for s in scene_objs for l in s["lines"] if l["speaker_jp"])),
    "term_hit_examples": [{"script": s["script"], "seq": l["seq"], "jp": l["jp"], "cn": l["cn"],
                           **{k: h[k] for k in ("原词日文", "旧写法", "新写法", "before", "after", "context_flag")}}
                          for s in scene_objs for l in s["lines"] for h in l["name_replaced"]],
    "per_scene": [{
        "script": s["script"], "source_kind": s["source_kind"], "text_source": s["text_source"],
        "line_count": s["line_count"], "voice_count": s["voice_count"],
        "title_jp": s["title_jp"], "title_cn": s["title_cn"], "phase": s["phase"], "route": s["route"],
        "next": s["next"], "next_kind": s["next_kind"], "choices": len(s["choices"]),
        "cast": s["cast"], "assets_total": len(s["assets"]),
        "assets_hit": sum(1 for a in s["assets"] if a["hit"]), "assets_missing": s["assets_missing"],
        "corrections_hit": s["stats"]["corrections_hit"], "name_replace_count": s["stats"]["name_replace_count"],
        "lines_by_origin": s["stats"]["lines_by_origin"], "empty_slots": s["stats"]["empty_slots"],
        "jp_overlap_2009": s["stats"]["jp_overlap_2009"],
    } for s in scene_objs],
    "fix_hits_otp": sorted(CORR_HIT),
}
report["corrections_all_in_scope_hit"] = (len(miss_corr) == 0)

os.makedirs(STG, exist_ok=True)
json.dump(report, open(os.path.join(STG, "_build_stats.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- 写出 scene_otp.jsonl
_assert_in_checkout(OUT, "剧本产物目录")
os.makedirs(OUT, exist_ok=True)
outpath = os.path.join(OUT, "scene_otp.jsonl")
_assert_in_checkout(outpath, "scene_otp.jsonl")
with open(outpath, "w", encoding="utf-8", newline="\n") as f:
    for s in scene_objs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
with open(outpath, encoding="utf-8") as f:
    n = sum(1 for ln in f if json.loads(ln))
w("      -> %s（%d 行，逐行 json.loads OK）" % (outpath, n))

# ================================================================ 摘要
w("")
w("================ 摘要 ================")
w("场景数            : %d  (shared %d / new %d) ｜ 无文本 .sob %d" % (
    report["scenes"], report["source_kind_dist"].get("shared", 0),
    report["source_kind_dist"].get("new", 0), report["textless_count"]))
w("行数              : %d  (基线 jsonl %d，守恒=%s)" % (tot_lines, BASELINE_SLOTS, report["lines_balanced"]))
w("cn_origin 分布    : %s" % report["orig_dist"])
w("text_source 分布  : %s" % report["text_source_dist"])
w("修正表            : 合计 %d ｜ otp 范围内 %d ｜ 命中 %d ｜ 未命中 %d ｜ 非 otp 源（门控排除）%d" % (
    len(corr_rows), len(in_scope), report["corrections_hit_in_scope"],
    len(miss_corr), len(gated_other)))
w("  未命中(范围内)  : %s" % (miss_corr or "无"))
w("term_unify 幂等 no-op: %d 条（构建期应为 0）%s"
  % (len(TERM_NOOP), (" ← " + str(TERM_NOOP[:3])) if TERM_NOOP else ""))
w("  命中逐条        : %s" % report["fix_hits_otp"])
w("选择支            : %d 个选择点 / %d 个选项槽  %s" % (len(choice_pts), choice_total, choice_pts))
w("译名替换处数      : %d" % report["term_hits"])
w("素材命中          : %d/%d (缺失 %d) ｜ 语音 %d/%d" % (a_hit, a_total, a_total - a_hit, v_hit, v_ref))
w("空槽 / D14 例外   : %d / %d" % (report["empty_slots"], report["d14_exceptions"]))
w("next_kind 分布    : %s" % report["next_kind_dist"])
w("phase 分布        : %s" % report["phase_dist"])
w("有显式日期场景    : %s" % (report["scenes_with_date"] or "无（全 null）"))
w("scene_id 唯一     : %s" % report["scene_ids_unique"])
w("说话人标签        : %d 种 ｜ 未映射 %s" % (report["speaker_label_count"], report["speaker_unmapped"] or "无"))