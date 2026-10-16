#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
build_story.py —— 剧本组装器（编程组）
============================================================
把资源组交付的 `资源组\剧本\scene_<源>.jsonl` 组装成 krkrz 引擎可直接加载的
剧本数据，并把被引用的素材（背景/立绘差分/语音）复制进游戏工程，使工程自洽可跑。

设计（依据 `资源组\交接编程组\交接说明.md` §二 消费顺序与 C1–C18）：
  * 正文译文**直接取** `lines[].cn` —— 交付 jsonl 已是「定取文源(D14) → 套修正表(按
    source 门控) → 套译名替换」三步之后的**最终成品**（`layers` 字段留痕，
    `fix_refs` 只是命中凭据）。故本器不重放消费链，只做「读取 + 组装 + 取件」。
  * 素材引用两步链（C16）：`assets[].out_relpath` →(`素材引用映射.tsv`)→ `交付路径`
    → 实文件在 `资源组\美术统一_交付\<交付路径>`。禁止按 basename 跨源解析（C3）。
  * 立绘按 `场景id` 查 `挂接_立绘.tsv`（C17），**不用 `cast` 反推**。
  * 语音逐行（`lines[].audio[]`，素材库相对路径）。

输出（默认落 `<checkout>\编程组\krkr\game\`，可 `--out` 覆盖）：
  story\_index.tjs          场景顺序表 + story_assets 下的资源根
  story\scene_<id>.tjs      每场景一份（懒加载，`Scripts.execStorage`）
  story_assets\<扁平名>      被引用的实文件（背景/差分/语音）

用法：
  python build_story.py --data-root "E:/ZCode Workspace/Galgame" --out <game目录> \
      --scenes ot_s01_01a,ot_s01_02a,...        # 指定场景
  python build_story.py ... --walk ot_s01_01a --walk-depth 8   # 从起点沿 next 走
  python build_story.py ... --all                 # 全量（712 场景，体积大）
"""
import argparse, csv, json, os, re, sys, shutil

SRC_ORDER = ["ot", "otr", "ota", "otp", "otv", "np"]

# ============================================================
# ★ op=other 控制串语义接入（层 2 · tier1；ISSUE-20261007-02）
# ------------------------------------------------------------
# 现状：`build_stage()` 只消费 chr_add/chr_expr/chr_move/chr_remove/se/bg，
#       **`op=other`（控制串）整类丢弃**（三源合计 2,484/663/318 行）。
# 本接入把**已达证据阈值**的控制串翻成真实事件：
#   · `!l` / `!r` ⇒ chr_remove（退场）——E5 §4.2（`!l`→x<0 113/114、`!r`→x≥1500）
#     ＋ R2 复核 §二.6 三路独立证据（PSV 注释 `//chr_anime 3,"!l",300` 邻 CharacterMove 110/110）。
#   · 纯方向 token（`c`/`l`/`r`/`<d`/`>d`）⇒ chr_place（瞬时落位，**不用 chr_move**：
#     P0-D 已证 chr_move 在运行期走 0.3s 滑动 ⇒ 实机「乱飘」）——E5 §4.2 方向 token→x。
#   · 其余控制串（坐标串 / EyeCatch / 复合串 / 语义未定修饰符）**一律不映射，保持丢弃**。
#
# ★★ 层 2（ISSUE-20261007-02）变更——**目标族不再靠启发式推，改为消费族身份表**：
#   层 1 的 `target_rule=concurrent`（同 seq 的 chr 事件族）已被 PSV 金标反证（`ot_s01_06d`
#   `!l` 的目标是 cut-in `cin`，同 seq 的 `asu` 不是目标）⇒ **`其他语义映射.tsv` 整表已废止、
#   本器不再读取它**（含 `target_rule`；`op`/`x` 方向语义改为本文件内联常量 `OTHER_TOKEN_*`，
#   证据见该常量注释）。旧表可保留留档，但代码不依赖。
#   目标族改由**离线族身份表** `资源组\演出\其他语义_族身份.tsv` 提供：
#     按 `(src, scene_id, seq, ctrl)` 查 `fam`（同场同 slot、code 更小的最近分配节点族，
#     按事件时刻重建；键级 99.0% 与 PSV 金标一致，无歧义抽样 60/60）。
#
# ★★ 本次接入范围（一审 RV-D1 M1 分层后）＝**严格梯 194 条**（第一梯队，最保守）：
#   一审指出旧「562 最小安全集」只排除 `psv_conflict=1`，把 `psv_conflict=''`（未校验）也当安全，
#   要求分层：严格 194（`[Chara<slot>]` 精确 ∧ `psv_conflict=0`）／兜底 258（块内唯一 Chara 兜底）／
#   未校验 110（无唯一金标）。**本器只接严格梯 194，其余梯次一律不接（保持现状丢弃）。**
#   严格梯白名单由离线器 `编程组\SOB0解码\_emit_other_strict.py` 从族身份表 + PSV 精确 Chara
#   抽出，落 `资源组\演出\其他语义_族身份_严格梯.tsv`（只读消费；**未改被审的族身份表本身**）。
#   接入四条件（同时成立）：`src ∈ {ot, otp}` ∧ 命中 7 token ∧ 该键在严格梯白名单内 ∧ 族身份表有 fam。
#     · `otr` 结构性不可用（joined 仅 7.2%）⇒ **显式排除，不接**；
#     · `psv_conflict = 1`（与 PSV 金标不一致＝移植端行为）与 `psv_conflict=''`（未校验）
#       以及「唯一 Chara 兜底」⇒ **显式排除，不按多数抹平**；
#     · 表外/复合串/坐标串 **一律不接**，保持丢弃（**不猜**）。
# 默认 **off**（`--other-semantics off`）：行为与接入前**逐字节一致**，便于对照与回退。
# 口径、条数、开关、回退、与已废止的 `其他语义映射.tsv` 的关系见 `编程组\other语义接入\说明.md`。
HERE = os.path.dirname(os.path.abspath(__file__))
# 只读消费的两张离线表（相对 <proj>）；旧 `其他语义映射.tsv` **本器不再读取**。
OTHER_FAM_FILE = os.path.join("资源组", "演出", "其他语义_族身份.tsv")          # 目标族来源
OTHER_STRICT_FILE = os.path.join("资源组", "演出", "其他语义_族身份_严格梯.tsv")  # tier1 白名单
OTHER_SAFE_SRCS = ("ot", "otp")     # 接入源作用域：仅 ot/otp（otr 显式排除）

# 「控制串 → 令」方向语义（内联；证据 E5 §4.2 / R2 §二.6 金标）。
# x 单位＝1280×720 逻辑画布（与 otv `:Position` 同系），运行时按内容区换算。
# ★ 不再读 `其他语义映射.tsv`（该表连同 `target_rule` 已被 PSV 金标反证、整表废止）。
OTHER_TOKEN_EXACT = {
    "!l": ("chr_remove", None), "!r": ("chr_remove", None),
    "c": ("chr_place", 640), "l": ("chr_place", 336), "r": ("chr_place", 944),
}
OTHER_TOKEN_RE = (
    (re.compile(r"^<[0-9]$"), ("chr_place", 236)),    # `<d` 左外侧
    (re.compile(r"^>[0-9]$"), ("chr_place", 1044)),   # `>d` 右外侧
)


def other_token(ctrl):
    """控制串 → (op, x)；非 7 token（复合串/坐标串/EyeCatch 等）⇒ None（保持丢弃）。"""
    if ctrl in OTHER_TOKEN_EXACT:
        return OTHER_TOKEN_EXACT[ctrl]
    for rx, spec in OTHER_TOKEN_RE:
        if rx.match(ctrl):
            return spec
    return None


def die(msg):
    print("[FATAL] " + msg, file=sys.stderr)
    sys.exit(2)


def tjs_str(s):
    """把 Python 字符串转成 TJS2 双引号字符串字面量（含转义）。"""
    if s is None:
        s = ""
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def load_scenes(script_dir):
    idx = {}
    for src in SRC_ORDER:
        p = os.path.join(script_dir, "scene_%s.jsonl" % src)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                o = json.loads(ln)
                idx[o["scene_id"]] = o
    return idx


def load_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


# ============================================================
# 逐行演出表（C21 · 资源组 `资源组\演出\演出_<源>.tsv`）
# ------------------------------------------------------------
# ★ 口径（资源组 C21 / 演出表说明 §一，**照此实现，不自行解释列义**）：
#   * 9 列 `scene_id seq op target arg1 arg2 arg3 evidence confidence`；TAB / UTF-8。
#   * `seq` =「在该行显示之前生效」，1-based，与 `lines[].seq` 同坐标系；同 seq 多 op
#     按**文件物理先后**为触发序；`skip` 行恒 `seq=0`。
#     ⚠️ 与 C17 `BGM切换点.tsv` 的「在 seq 之后」**差 +1**，两套口径不得混用（本器分开读）。
#   * `target` = 素材账 `out_relpath` 全路径 ⇒ **必须经 C16 两步链**换成交付层实件：
#       ① 主链 `素材引用映射.tsv`（引用→交付路径）；② 反向链 `素材库到统一名.tsv`
#          （源,kind,文件→交付路径）。两条链都取不到即记 miss，**不得按 basename 猜路径**。
#   * `op` 闭集 12 值；消费 `chr_add/chr_expr/chr_move/chr_remove/se` **＋ `bg` 背景层**
#     （P0-A，ISSUE-20261006-02）+ `other`（层 2 · tier1，须 `--other-semantics tier1` 且命中
#     严格梯白名单 194 条；默认 off 即丢弃）；`bgm/movie/wait/effect` 仍不在范围。
#     ★ **B1 换源（ISSUE-20261006-04）**：背景层事件**只在未覆盖场**回落本表 `op=bg`
#       （且**剔除题卡族 `ec##`**）；**有 PSV 覆盖的场改吃 `编程组\PSV演出\时间线.tsv` 的
#       `SpriteBG`**（金标，带 seq/交付路径）。依据：《背景编排分析》§一/§二——本表
#       `op=bg` 分不清「弹卡/换背景」且整段漏切换。叠加层仍只登记不实现（P2）。
#
# ★★ 摆位规则是「**我方自定的规则、不是源侧事实**」（用户 2026-10-01 裁定）：
#   · `otv`：**用它的真位置/层序/退场**（`:Position` → arg1、`:Priority` → arg2、remove 行）
#     —— 坐标空间实测为 **1280×720**（`:Position 640,0` = 正中心；336/944、236/1044 成对
#     关于 640 对称），故映射到内容区：`cx = cb.x + px*cb.w/1280`、`top = cb.y + py*cb.h/720`。
#   · 其余五源（`ot`/`ota`/`otp`/`otr`/`np`）：**无位置、无退场** ⇒ 用**我方自定的固定摆位**。
#     ★ **2026-10-02 用户修订**（旧规则「1 人 0.40／2 人 0.25,0.75／3 人 0.18,0.50,0.82／≥4 人 10%..90% 均分」
#       是**在旧 4:3 框里标定**的：框宽 1200→1920 后首槽中心由 480 掉到 192、立绘宽约 666 ⇒ **x=−141 出画 21%**，
#       且 0.10 与 0.30 的中心只差 384px < 立绘宽 ⇒ **必然重叠**。实测 `scene_ota_23_1b` 负 x 条目 48 条）：
#       **1 号靠左、2 号靠右（不再紧贴 1 号）；3 号及以后放在 1 号与 2 号之间，从左到右排列；
#         一律保证互不重叠、且不出画**。按各族的**实际宽度**反解，见 `stage_slot_layout`。
#   · **立绘尺寸**：高度 ＝ 内容区高 × `STAGE_CHR_SCALE`（用户 2026-10-02「立绘太大」），
#     **底边贴内容区下沿**（缩放以底边为基准；`otv` 的源侧 y 偏移按同比例叠加）。
#     ⚠️ **这是"我们发明的规则"**，源侧并无该数据（见工程记录与代码注释）。
#   · **整屏件**（图像宽高比 ≈ 内容区宽高比 且 宽 ≥ 内容区半宽，实测 `np` 全部 1280×720、
#     `otv` 的 2560×1440 cut-in）：位置已烘焙在图内 ⇒ **落内容区整框、不做槽位偏移**。
# ============================================================
NONROLE_FAMILIES = ("cin", "f_mis", "cit", "pon", "unparsed")   # C21⑤ 非角色族（不得当立绘注入）
# ★ 立绘摆位/尺寸参数（★ 我方自定规则，2026-10-02 按用户要求重写；见文件头说明）
STAGE_CHR_SCALE = 0.875      # 立绘高度 ＝ 内容区高 × 此值
# ★ P0-C（ISSUE-20261006-02，**用户 2026-10-06 裁定**）：0.80 → **0.875**。
#   依据：PSV 立绘件实测 **630px 高 / 720 逻辑画布 = 87.5%**（`工程\我们没有翅膀PSV\素材\美咲线\
#   images\chr\ST_ASU01.png` = 473×630）；PSV 与我方同为 16:9 ⇒ 同一比例可直接搬用。
#   我方内容区高＝1080 ⇒ 立绘高＝1080×0.875＝**945px**。
#   （旧值 0.80 是用户 2026-10-02「立绘太大」的临时口径；本次按 PSV 金标对齐。据此 0.80→0.875 是**放大**。）
STAGE_CHR_SCALE_FLOOR = 0.35 # 同屏人多时按场景**自适应降缩放**的保底值（低于此值宁可让自检报重叠）
STAGE_CHR_EDGE  = 40         # 1 号/2 号距内容区左右沿的边距（画布像素）
STAGE_CHR_GAP   = 16         # 立绘之间的最小间距（保证不重叠）
STAGE_MAX_SLOTS = 6          # 运行期追加的立绘槽位数（ui_staging.tjs 同值）
# ★ 可见集上限（ISSUE-20261003-05）：同屏族数过多时**宁可少画几个**，也要保证立绘不小于此缩放。
#   为什么需要：五源**无退场信号**，源侧有时把整场十几个族**一次性上场**（实测 `ot_s04_08a` 19 族同 seq、
#   `otp_staff` 20 族）⇒ 自适应缩放一路降到保底 0.35（高 1080×0.35＝378px）⇒ 用户看到的「立绘极小」。
STAGE_CHR_MIN_VIS = 0.55
# ★ 立绘 z 取值（现状参数来自 `UI组\layout\screens\10_dialog.json` 的既有元素）：
#     dlg.content=1(背景) < dlg.canvas_white=2(已关) < **本槽=10** < dlg.mask_bottom=15(底部可读性遮罩)
#     < dlg.face=20(说话人头像) < dlg.name/dlg.text=22(文字) < dlg.choices=30(选择肢)
#   ⇒ 立绘夹在「背景(1)」与「文字(22)」之间，且**压在可读性遮罩之下**（遮罩本就是为压暗游戏画面
#     保文字可读而设，立绘属游戏画面的一部分），文字/头像/选择肢恒在其上。
STAGE_Z = 10


def load_staging(staging_dir):
    """`演出_<源>.tsv` × 6 → {scene_id: [row, ...]}，**保持文件物理先后**（C21 触发序）。"""
    out = {}
    for src in SRC_ORDER:
        p = os.path.join(staging_dir, "演出_%s.tsv" % src)
        if not os.path.isfile(p):
            continue
        for r in load_tsv(p):
            sid = (r.get("scene_id") or "").strip()
            if not sid:
                continue
            out.setdefault(sid, []).append(r)
    return out


def load_other_families(path):
    """`资源组\\演出\\其他语义_族身份.tsv` → {(src, scene_id, seq:int, ctrl): fam}。

    ★ 层 2（ISSUE-20261007-02）：目标族的**唯一权威来源**。键与 `演出_<源>.tsv` 的
      `op=other` 行一一对应（该表 `scene_id/seq/ctrl` ＝旧表原行键；`ctrl` ＝ `arg1`）。
      本函数只做「族身份表侧」的粗筛（**不含精确 Chara 分层**——那由白名单 `load_strict_keys`
      叠加；两者取交 ＝ 严格梯 194）。粗筛条件：
      · `src ∈ {ot, otp}` —— `otr` 结构性不可用（318 行仅 23 行有族）⇒ 显式排除；
      · `fam` 非空 —— 未 join / 未解出者留空，排除；
      · `psv_conflict == '0'` —— **只收与 PSV 金标一致的**；`1`（不一致＝移植端行为）与
        `''`（无唯一金标＝未校验）**均排除**（一审 M1：`''` 不等于安全）；
      · 命中 7 token（`other_token` 非空）。
    粗筛结果 = 452 条（194 严格 + 258 兜底）；再与严格梯白名单取交 ⇒ 194。
    列义见同目录 `其他语义_族身份_说明.md`。
    """
    m = {}
    if not os.path.isfile(path):
        return m
    for r in load_tsv(path):
        src = (r.get("src") or "").strip()
        if src not in OTHER_SAFE_SRCS:
            continue
        fam = (r.get("fam") or "").strip()
        if not fam:
            continue
        if (r.get("psv_conflict") or "").strip() != "0":
            continue
        sid = (r.get("scene_id") or "").strip()
        ctrl = (r.get("ctrl") or "").strip()
        if not sid or not ctrl or other_token(ctrl) is None:
            continue
        try:
            seq = int((r.get("seq") or "0").strip() or "0")
        except ValueError:
            seq = 0
        m[(src, sid, seq, ctrl)] = fam
    return m


def load_strict_keys(path):
    """`资源组\\演出\\其他语义_族身份_严格梯.tsv` → {(src, scene_id, seq:int, ctrl)}。

    ★ tier1 白名单：一审 RV-D1 M1 定义的第一梯队（`[Chara<slot>]` 精确 ∧ `psv_conflict=0`），
      由离线器 `编程组\\SOB0解码\\_emit_other_strict.py` 从族身份表 + PSV 精确 Chara 抽出，
      实测 **194 条**。本器只**读键**做闸门；`fam` 仍从族身份表取（两张表同源一致）。
      白名单缺失 ⇒ 空集 ⇒ 全部控制串保持丢弃（＝不退化为「宽口径安全集」）。
    """
    keys = set()
    if not os.path.isfile(path):
        return keys
    for r in load_tsv(path):
        src = (r.get("src") or "").strip()
        sid = (r.get("scene_id") or "").strip()
        ctrl = (r.get("ctrl") or "").strip()
        if not src or not sid or not ctrl:
            continue
        try:
            seq = int((r.get("seq") or "0").strip() or "0")
        except ValueError:
            seq = 0
        keys.add((src, sid, seq, ctrl))
    return keys


def is_ec_card_name(s):
    """素材名/路径是否属「题卡族（`ec##`）」。

    ★ B1 排除项（ISSUE-20261006-04）：任何 `ec##` 素材**不得进入背景层**。
      归一化：剥目录 → 反复剥 `<源>_` / `<kind>__` 前缀（兼容 `take_asset` 产出的扁平名
      `bg__ec28.png`）→ 判 `^ec<数字>`。
      依据：《背景编排分析》§一.3 实测 `PIC\\EC28.ELG`（归一化 `ec28`）被源侧同时当
      「弹卡」与「背景」；`ec_bg*`（照片池）不以数字接续 ⇒ **不算题卡**，不误伤。
    """
    b = os.path.splitext(os.path.basename((s or "").replace("\\", "/")))[0]
    prev = None
    while b != prev:
        prev = b
        b = re.sub(r"^[a-z0-9]+__?", "", b, count=1)
    return bool(re.match(r"^ec\d", b, re.I))


def load_psv_timeline(psv_dir):
    """PSV 演出金标 → 背景层事件源（B1 换源）。

    返回 (bg, allbg, covered)：
      · `bg`    ＝ {scene_id: [row(op==bg 且 type==SpriteBG)]}（背景层真值，带 seq/delivery/status）
      · `allbg` ＝ {scene_id: [row(op==bg)]}（含叠加层 SpriteBS/Sprite，仅供「只计数不实现」登记）
      · `covered` ＝ `场景映射.tsv` 的 scene_id 集合（＝有 PSV 金标覆盖的场）

    ★ 为什么换源（ISSUE-20261006-04 · B1）：构建原先消费的 `演出_<源>.tsv` 的 `op=bg`
      分不清「弹卡」与「换背景」（1,047/4,063 条指向 `ec##`），且**整段漏背景切换**
      （实测 `ot_s01_02a` 剔题卡后 seq 5→269 空窗，PSV 真值在 seq 91/95/121 另有三次）。
      PSV 侧按 `:Tasktype` 已三分：`SpriteBG`(背景) / `SpriteBS`+`Sprite`(叠加) / `EyeCatch`(卡)
      ⇒ 只取 `SpriteBG` 即天然排除题卡。依据：`PSV演出\\说明.md` §三列义、§四解析规则。
    ★ `seq` 列＝我方语料 `lines[].seq`（已对齐，P1 已验），直接用于运行期挂接；
      `delivery` 列＝**交付层相对路径**（相对 `资源组\\美术统一_交付`），不再走 C16 映射链。
    """
    bg, allbg = {}, {}
    tl = os.path.join(psv_dir, "时间线.tsv")
    if os.path.isfile(tl):
        for r in load_tsv(tl):
            if (r.get("op") or "").strip() != "bg":
                continue
            sid = (r.get("scene_id") or "").strip()
            if not sid:
                continue
            allbg.setdefault(sid, []).append(r)
            if (r.get("type") or "").strip() == "SpriteBG":
                bg.setdefault(sid, []).append(r)
    covered = set()
    mp = os.path.join(psv_dir, "场景映射.tsv")
    if os.path.isfile(mp):
        for r in load_tsv(mp):
            sid = (r.get("scene_id") or "").strip()
            if sid:
                covered.add(sid)
    return bg, allbg, covered


def load_chr_family_index(proj):
    """`美术\\立绘差分索引.tsv` → out_relpath -> family（**权威族别表**，C21⑤）。"""
    m = {}
    p = os.path.join(proj, "资源组", "美术", "立绘差分索引.tsv")
    if not os.path.isfile(p):
        return m
    for r in load_tsv(p):
        orp = (r.get("out_relpath") or "").strip()
        fam = (r.get("family") or "").strip()
        if orp and fam:
            m[orp] = fam
    return m


def load_rev_asset_map(handoff):
    """`素材库到统一名.tsv` → (源,kind,文件) -> (交付路径, 替代安全性)。

    ★ C16 的**反向查询**链：权威表未登记（只在总账里）的引用靠它拿交付件路径。
      实测 chr 的 ot/ota/otp（14k+5.6k+2.9k 行）**只走这条链**，`otr/otv` 走主链。
    """
    m = {}
    p = os.path.join(handoff, "素材库到统一名.tsv")
    if not os.path.isfile(p):
        return m
    for r in load_tsv(p):
        src = (r.get("源") or "").strip()
        kd = (r.get("素材库kind") or "").strip()
        fn = (r.get("素材库文件") or "").strip()
        dp = (r.get("交付路径") or "").strip()
        sa = (r.get("替代安全性") or "").strip()
        if src and kd and fn and dp:
            m[(src, kd, fn)] = (dp, sa)
    return m


def load_16x9_override(proj):
    """`美术统一_交付_16比9\\交付清单.tsv` → {交付层相对路径: 16:9 件相对 `资源组\\` 的路径}。

    ★ **表驱动**（ISSUE-20261003-02）：不硬编码任何文件名，也**不改资源组的表**。
      · 键 ＝ `原件交付层路径` 去掉 `美术统一_交付\\` 前缀 —— 与 `素材引用映射.tsv` 的
        `交付路径` 列**同口径**（该列本就相对 `美术统一_交付\\`）；
      · 值 ＝ `新件路径`（相对 `资源组\\`）；实文件 ＝ `<proj>\\资源组\\<新件路径>`。
      ⇒ 资源组**追加交付即自动生效**，本器零改码；清单缺失/为空时返回空表（行为与改动前逐字节一致）。
    """
    m = {}
    p = os.path.join(proj, "资源组", "美术统一_交付_16比9", "交付清单.tsv")
    if not os.path.isfile(p):
        return m
    for r in load_tsv(p):
        old = (r.get("原件交付层路径") or "").strip().replace("\\", "/")
        new = (r.get("新件路径") or "").strip().replace("\\", "/")
        if not old or not new:
            continue
        k = re.sub(r"^美术统一_交付/", "", old)
        m[k] = new
    return m


def family_of(target, chr_index):
    """target(`<源>/<kind>/<源>_<名>.<ext>`) → 立绘族代号。

    ① 权威表命中即用；② 否则按文件名推（去 `<源>_` 前缀、去 PSV `st_` 前缀后取首段字母）。
    """
    fam = chr_index.get(target)
    if fam:
        return fam
    base = os.path.splitext(os.path.basename(target))[0]
    b = re.sub(r"^[a-z0-9]+_", "", base, count=1)     # 去 <源代号>_ 前缀
    b = re.sub(r"^st_", "", b)                        # PSV 侧 st_ 前缀
    m = re.match(r"^([a-z]+)", b)
    return m.group(1) if m else ""


def load_content_boxes(proj):
    """UI 组 `layout\\_root.json`：content_boxes[源] + canvas（D1 的画布与各源内容区）。"""
    p = os.path.join(proj, "UI组", "layout", "_root.json")
    if not os.path.isfile(p):
        return {}, (1920, 1080)
    o = json.load(open(p, encoding="utf-8"))
    cv = o.get("canvas") or {}
    return (o.get("content_boxes") or {}), (int(cv.get("width", 1920)), int(cv.get("height", 1080)))


def stage_slot_layout(n, widths, cb, edge=STAGE_CHR_EDGE, gap=STAGE_CHR_GAP):
    """五源的立绘**横向摆位**（★ 我方自定规则；2026-10-02 按用户要求重写）。

    用户要求：**1 号靠左、2 号靠右（不再紧贴 1 号）；3 号及以后放在 1 号与 2 号之间，
    从左到右排列，不得重叠**。返回 n 个槽位的**中心 x**（与既有「按中心锚定、换表情不移位」一致）。

    `widths`：各槽位的**代表宽度**——取该族在本场景的**最大**宽度，保证任何表情都不重叠。
    理想排法＝「两端 + 中间均分」；若总宽放不下，退化为**等距铺开**；
    最后按视觉序**左右各扫一遍**，保证互不重叠且夹在内容区内（不出画优先于间距）。
    """
    if n <= 0:
        return []
    bx, bw = cb["x"], cb["w"]
    if n == 1:
        half = widths[0] / 2.0
        return [max(bx + half, min(bx + bw - half, bx + bw * 0.40))]   # 单人：沿用旧口径（中偏左）

    avail = bw - 2 * edge
    need = sum(widths) + gap * (n - 1)
    vis = [0] + list(range(2, n)) + [1]          # 视觉从左到右：1 号 →（中间）→ 2 号
    left = [0.0] * n
    if need <= avail:
        left[0] = bx + edge                          # 1 号靠左
        left[1] = bx + bw - edge - widths[1]         # 2 号靠右
        k = n - 2
        if k > 0:
            l = left[0] + widths[0]                  # 1 号右沿
            r = left[1]                              # 2 号左沿
            for j in range(k):
                idx = 2 + j
                mid = l + (r - l) * (j + 1) / (k + 1)
                left[idx] = mid - widths[idx] / 2.0
    else:
        g = max(0.0, (avail - sum(widths)) / float(n - 1))
        x = bx + edge
        for idx in vis:
            left[idx] = x
            x += widths[idx] + g
    # 不重叠 + 不出画：按视觉序左→右、再右→左各扫一遍
    x = bx + edge
    for idx in vis:
        if left[idx] < x:
            left[idx] = x
        x = left[idx] + widths[idx] + gap
    x = bx + bw - edge
    for idx in reversed(vis):
        if left[idx] + widths[idx] > x:
            left[idx] = x - widths[idx]
        x = left[idx] - gap
    if left[vis[0]] < bx:
        left[vis[0]] = bx
    return [left[i] + widths[i] / 2.0 for i in range(n)]


def is_fullscreen(w, h, cb):
    """图像是否「整屏件」：宽高比≈内容区 且 宽 ≥ 内容区半宽（位置已烘焙在图内）。"""
    if w <= 0 or h <= 0:
        return False
    ar = w / h
    cbar = cb["w"] / cb["h"]
    return abs(ar - cbar) < 0.02 and w >= 0.5 * cb["w"]



def build_ref_map(handoff):
    """素材引用映射.tsv: 引用(out_relpath) -> (交付路径, 结论)。

    ★ C16：`结论 == 有差异替代` 的行**经裁决后才可用**。本器不再静默采用——
      返回值带上 `结论`，由调用方决定采用/跳过并**逐条留痕**。
    """
    m = {}
    p = os.path.join(handoff, "素材引用映射.tsv")
    for r in load_tsv(p):
        k = (r.get("引用") or "").strip()
        v = (r.get("交付路径") or "").strip()
        concl = (r.get("结论") or "").strip()
        if k and v:
            # 同引用多行时：代表件优先
            if k not in m or concl == "代表件":
                m[k] = (v, concl)
    return m


def build_bgm_map(proj):
    """C18：BGM 一律走 `资源组\\BGM统一\\` + 统一名。清单 `原文件`（如 otv_bgm013.ogg）
    -> 统一名（如 bgm013.ogg）。**禁止**再从 `krkr素材库\\<源>\\bgm\\` 直接取件。"""
    m = {}
    p = os.path.join(proj, "资源组", "BGM统一清单.tsv")
    if not os.path.isfile(p):
        return m
    for r in load_tsv(p):
        uni = (r.get("统一名") or "").strip()
        orig = (r.get("原文件") or "").strip()
        if uni and orig:
            m[os.path.basename(orig).lower()] = uni
    return m


def build_bgm_hookup(handoff):
    """`挂接_BGM.tsv`（C17）：场景 id -> (推荐统一名, 依据等级)。**统一名**直接对应 `BGM统一\\`。

    ⚠️ 依据等级四级：`源侧実引用`(57) 才是**源侧数据**；`人格段规则`(426)/`AfterStory专属曲`(172)/
    `共通段`(57) 是资源组按规则**重建**的——可用但须在日志/说明中标注，**不得当源侧数据**（C17）。
    """
    m = {}
    p = os.path.join(handoff, "挂接_BGM.tsv")
    if not os.path.isfile(p):
        return m
    for r in load_tsv(p):
        sid = (r.get("场景id") or "").strip()
        uni = (r.get("推荐统一名") or "").strip()
        lev = (r.get("依据等级") or "").strip()
        if sid and uni:
            m[sid] = (uni, lev)
    return m


def build_bgm_cues(handoff):
    """`BGM切换点.tsv`（C18）：场景 id -> [ (在seq之后:int, 事件, 统一名), ... ]（按 seq 升序）。

    只有 otv/np 的 57 场有；`事件=停止` 行为无曲号（C18）。**播放序以此表为准，不得按编号拼名**。
    """
    m = {}
    p = os.path.join(handoff, "BGM切换点.tsv")
    if not os.path.isfile(p):
        return m
    for r in load_tsv(p):
        sid = (r.get("场景id") or "").strip()
        if not sid:
            continue
        try:
            seq = int((r.get("在seq之后") or "0").strip() or "0")
        except ValueError:
            continue
        ev = (r.get("事件") or "").strip()
        uni = (r.get("统一名") or "").strip()
        m.setdefault(sid, []).append((seq, ev, uni))
    for k in m:
        m[k].sort(key=lambda t: t[0])
    return m


def build_intro_table(proj, script_dir, live_ids, ref_map, disabled, take_bg):
    """章节简介（C15）＋幕信息 → 供流程图右栏/详情浮层取数。

    * 简介：`资源组\剧本\章节简介.tsv`，**只取 `采用==是`**；同一 `场景id` 多行内容一致 ⇒ 按 id 去重。
    * 幕：`spine.json` 的 `acts[]`（流程图的幕级节点 `N01..N11` 由 `UIFlowData.nodes[].act` 对应）。
    * 画面窗：取该幕**首个场景**的背景（若该场景有可解析的图像引用）。
    """
    intros = {}
    p = os.path.join(script_dir, "章节简介.tsv")
    if os.path.isfile(p):
        for r in load_tsv(p):
            if (r.get("采用") or "").strip() != "是":
                continue
            sid = (r.get("场景id") or "").strip()
            if not sid or sid in intros:
                continue
            intros[sid] = ((r.get("章节标题(中文)") or "").strip(),
                           (r.get("简介cn") or "").strip())
    acts = []
    act_scene_ids, act_scene_acts = [], []     # ★ 场景→幕（供运行期把剧情进度写回流程图「已读/当前」）
    p2 = os.path.join(script_dir, "spine.json")
    if os.path.isfile(p2):
        sp = json.load(open(p2, encoding="utf-8"))
        for i, a in enumerate(sp.get("acts") or []):
            sc = a.get("scenes") or []
            for _sid in sc:
                act_scene_ids.append(_sid)
                act_scene_acts.append(i + 1)
            first = sc[0] if sc else ""
            ti, tx = intros.get(first, ("", ""))
            # 画面窗：首场景/其后若干场景的第一张可解析图像（不在切片内的场景也能取到图）
            bg = ""
            for cand in sc[:6]:
                so = live_ids.get(cand)
                if not so:
                    continue
                for aset in (so.get("assets") or []):
                    if (aset.get("kind") or "").lower() in ("se", "bgm", "sound", "voice", "chr", "movie"):
                        continue
                    deliv = ref_map_get(ref_map, aset.get("out_relpath"))
                    if deliv and deliv in disabled:
                        deliv = ""
                    if deliv:
                        deliv = take_bg(deliv)
                    if deliv:
                        bg = deliv
                        break
                if bg:
                    break
            acts.append(dict(act=i + 1, label=(a.get("name") or a.get("id") or a.get("label") or a.get("title") or ""),
                             scenes=len(sc), first=first,
                             title=ti, intro=(tx or (a.get("note") or "")), bg=bg))
    # ---- 输出 ----
    out = ["// 生成物（build_story.py）——勿手改：章节简介（C15）与幕信息"]
    out.append("UIIntroKeys  = [" + ",".join(tjs_str(k) for k in intros) + "];")
    out.append("UIIntroTitles= [" + ",".join(tjs_str(v[0]) for v in intros.values()) + "];")
    out.append("UIIntroTexts = [" + ",".join(tjs_str(v[1]) for v in intros.values()) + "];")
    out.append("UIActNums    = [" + ",".join(str(a["act"]) for a in acts) + "];")
    out.append("UIActLabels  = [" + ",".join(tjs_str(a["label"]) for a in acts) + "];")
    out.append("UIActCounts  = [" + ",".join(str(a["scenes"]) for a in acts) + "];")
    out.append("UIActTitles  = [" + ",".join(tjs_str(a["title"]) for a in acts) + "];")
    out.append("UIActIntros  = [" + ",".join(tjs_str(a["intro"]) for a in acts) + "];")
    out.append("UIActBgs     = [" + ",".join(tjs_str(a["bg"]) for a in acts) + "];")
    out.append("UIActFirsts  = [" + ",".join(tjs_str(a["first"]) for a in acts) + "];")
    # ★ 场景→幕（两个平行数组；**不在幕内的场景（番外/序文）不出现在表里**）
    out.append("UIActSceneIds = [" + ",".join(tjs_str(x) for x in act_scene_ids) + "];")
    out.append("UIActSceneActs= [" + ",".join(str(x) for x in act_scene_acts) + "];")
    return chr(10).join(out) + chr(10), len(intros), len(acts)



def ref_map_get(rm, orp):
    v = rm.get(orp or "")
    return v[0] if v else ""


def build_music_table(proj):
    """BGM 鉴赏屏曲目表：读 UI 组 `28_music.json` 的 `mu.list.labels`（形如 `01　np_bgm53a`），
    用 `BGM统一清单.tsv` 的 `原文件`→`统一名` 映射成可播放件（C18：一律统一名）。"""
    lab = []
    p = os.path.join(proj, "UI组", "layout", "screens", "28_music.json")
    if os.path.isfile(p):
        s = json.load(open(p, encoding="utf-8"))
        for e in s.get("elements") or []:
            if (e or {}).get("id") == "mu.list":
                lab = list(e.get("labels") or [])
    bm = build_bgm_map(proj)          # 原文件 basename(小写) -> 统一名
    names, unis = [], []
    for x in lab:
        s2 = "" + x
        i = s2.find("　")
        nm = s2[i + 1:] if i >= 0 else s2
        names.append(nm)
        unis.append(bm.get((nm + ".ogg").lower(), ""))
    out = ["// 生成物（build_story.py）——勿手改：BGM 鉴赏曲目表"]
    out.append("UIMusicNames = [" + ",".join(tjs_str(n) for n in names) + "];")
    out.append("UIMusicUnis  = [" + ",".join(tjs_str(u) for u in unis) + "];")
    return chr(10).join(out) + chr(10), len(names), sum(1 for u in unis if u)


def build_disabled(handoff):
    """停用件_禁入成品.tsv（C19）：497 件弃用件，**不得编入成品**。键=交付路径。"""
    p = os.path.join(handoff, "停用件_禁入成品.tsv")
    if not os.path.isfile(p):
        return set()
    return {(r.get("交付路径") or "").strip() for r in load_tsv(p) if (r.get("交付路径") or "").strip()}


def img_size(path):
    """返回 (w,h)；支持 PNG / JPEG，失败返回 (0,0)。用于运行时缩放（交付件为 2×）。"""
    try:
        with open(path, "rb") as f:
            head = f.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                import struct
                w, h = struct.unpack(">II", head[16:24])
                return int(w), int(h)
            if head[:2] == b"\xff\xd8":                      # JPEG
                f.seek(2)
                while True:
                    b = f.read(1)
                    if not b:
                        break
                    if b != b"\xff":
                        continue
                    m = f.read(1)
                    while m == b"\xff":
                        m = f.read(1)
                    if not m:
                        break
                    mk = m[0]
                    if mk in (0xD8, 0x01) or 0xD0 <= mk <= 0xD7:
                        continue
                    ln = f.read(2)
                    if len(ln) < 2:
                        break
                    seg = (ln[0] << 8) | ln[1]
                    if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                        data = f.read(5)
                        if len(data) < 5:
                            break
                        h = (data[1] << 8) | data[2]
                        w = (data[3] << 8) | data[4]
                        return int(w), int(h)
                    f.seek(seg - 2, 1)
    except Exception:
        pass
    return 0, 0


def build_chr_map(handoff):
    """挂接_立绘.tsv: 角色(中文) -> 立绘族代号（跨场景聚合，取出现最多者）。"""
    p = os.path.join(handoff, "挂接_立绘.tsv")
    counts = {}
    scene_chr = {}
    for r in load_tsv(p):
        sid = (r.get("场景id") or "").strip()
        role = (r.get("角色") or "").strip()
        fam = (r.get("立绘族") or "").strip()
        if not sid or not role or not fam:
            continue
        if fam.startswith("（"):        # （无·主角人格）等占位
            fam = ""
        scene_chr.setdefault(sid, []).append((role, fam))
        if fam:
            counts.setdefault(role, {})
            counts[role][fam] = counts[role].get(fam, 0) + 1
    role2fam = {}
    for role, d in counts.items():
        role2fam[role] = sorted(d.items(), key=lambda kv: -kv[1])[0][0]
    return role2fam, scene_chr


def face_file_for(fam, available):
    """族 -> 一个可用的 face 文件名（优先 01 号表情，否则取第一个）。"""
    if not fam:
        return ""
    want = fam + "01.png"
    if want in available:
        return want
    cands = sorted([f for f in available if f.startswith(fam) and f.endswith(".png")])
    return cands[0] if cands else ""


def resolve_asset(out_relpath, ref_map):
    """返回 (交付路径, 结论)；未映射返回 ("", "")。"""
    v = ref_map.get(out_relpath or "")
    if v is None:
        return "", ""
    return v


def decl_idx(choice):
    """选项的**声明源点**（`evidence` 里的 `#idxN`）；无则空串。

    ★ 用途：同一场景里若某项的声明源点与其余项不同，说明它来自**另一处声明**（实测是说话人/标签，不是选项）。
      见 `build_story` 的选择支补全规则③。
    """
    m = re.search(r"#idx(\d+)", (choice.get("evidence") or ""))
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame")
    ap.add_argument("--out", required=True, help="游戏工程根（含 game\\ 的那层）")
    ap.add_argument("--scenes", default="")
    ap.add_argument("--walk", default="")
    ap.add_argument("--walk-depth", type=int, default=8)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--act", type=int, default=0, help="取 spine 第 N 幕（1 起）的全部场景")
    ap.add_argument("--entry", default="", help="入口场景 id（默认第一个）")
    ap.add_argument("--strict-c16", action="store_true",
                    help="C16 严格模式：跳过所有「有差异替代」映射（默认采用并逐条留痕）")
    # ★【开发/对照用】内容区四源按全画布生成（模拟 D-04 落地后的状态）。
    #   为什么必须有它：**立绘/演出槽位的 x/y/w/h 是 build 时按 `content_boxes` 烘焙进场景数据**的，
    #   只做运行期覆盖（`ui_cbfull.tjs`）只能改**背景选框**，立绘仍是旧框 ⇒ 对照会失真。
    #   成品构建**不要**带此开关；它与 `ui_cbfull.tjs` 成对使用（一个管数据、一个管运行期选框）。
    ap.add_argument("--cb-full", action="store_true",
                    help="[开发] content_boxes 的 ot/otr/ota/otp 按全画布 0,0,W,H 生成（模拟 D-04）")
    # ★ op=other 控制串语义接入（层 2 · tier1，ISSUE-20261007-02）：**默认 off＝与接入前逐字节一致**。
    #   tier1 时读 `资源组\演出\其他语义_族身份.tsv`（按 (src,scene_id,seq,ctrl) 查 fam）
    #   ＋ `资源组\演出\其他语义_族身份_严格梯.tsv`（tier1 白名单，194 条）取交，
    #   把严格梯内的控制串翻成 chr_remove / chr_place。**不再读 `其他语义映射.tsv`（整表废止）。**
    ap.add_argument("--other-semantics", choices=["off", "tier1"], default="off",
                    help="[对照/回退] op=other 控制串语义接入：off(默认,行为同现状) / tier1(仅接严格梯 194 条白名单)")
    args = ap.parse_args()

    other_on = (args.other_semantics == "tier1")
    root = args.data_root
    proj = os.path.join(root, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
    script_dir = os.path.join(proj, "资源组", "剧本")
    handoff = os.path.join(proj, "资源组", "交接编程组")
    art_root = os.path.join(proj, "资源组", "美术统一_交付")
    media_root = os.path.join(proj, "资源组", "krkr素材库")
    face_root = os.path.join(proj, "UI组", "krkr", "assets", "face")
    if not os.path.isdir(script_dir):
        die("剧本目录不存在: %s" % script_dir)

    scenes = load_scenes(script_dir)
    ref_map = build_ref_map(handoff)
    disabled = build_disabled(handoff)
    bgm_map = build_bgm_map(proj)
    bgm_root = os.path.join(proj, "资源组", "BGM统一")
    bgm_hook = build_bgm_hookup(handoff)
    bgm_cues = build_bgm_cues(handoff)
    role2fam, scene_chr = build_chr_map(handoff)
    face_avail = [f for f in os.listdir(face_root)] if os.path.isdir(face_root) else []
    # ---- 逐行演出表（C21）：数据 + 两条取件链 + 内容区 ----
    staging_dir = os.path.join(proj, "资源组", "演出")
    staging = load_staging(staging_dir)
    # ---- ★ 层 2 · tier1：op=other 目标族的权威来源（族身份表 ∩ 严格梯白名单）----
    #   按 `(src, scene_id, seq, ctrl)` 从族身份表查 fam；再由严格梯白名单（194 条）闸门取交。
    #   未命中 / 白名单外 / 被粗筛排除 ⇒ 保持丢弃（不猜）。
    #   表位置：优先与 `--data-root` 同树（`<proj>\资源组\演出\`，合并后即此处）；未合并的
    #   多 worktree 场景回落到**本脚本所在工程树**（`<HERE>\..\..\资源组\演出\`）。两树 staging
    #   逐字节一致（已核 md5），故键口径相同；两处都缺 ⇒ 空表 ⇒ 全部丢弃（＝保持 off 行为）。
    other_fam = {}
    if other_on:
        def _pick(rel):
            _c = [os.path.join(proj, rel), os.path.join(HERE, "..", "..", rel)]
            return next((p for p in _c if os.path.isfile(p)), _c[0])
        _fam_p = _pick(OTHER_FAM_FILE)
        _str_p = _pick(OTHER_STRICT_FILE)
        _fams = load_other_families(_fam_p)                    # 族身份表粗筛（452 条）
        _strict = load_strict_keys(_str_p)                     # tier1 白名单（194 条）
        other_fam = {k: v for k, v in _fams.items() if k in _strict}
        print("[other] op=other 语义接入 tier1 ｜ 族身份表粗筛 %d 条 ∩ 严格梯白名单 %d 条 ⇒ **接入 %d 条**"
              % (len(_fams), len(_strict), len(other_fam)))
        print("[other]   族身份表 %s ｜ 严格梯白名单 %s" % (os.path.abspath(_fam_p), os.path.abspath(_str_p)))
        if not other_fam:
            print("[other][warn] tier1 接入集为空（表缺失或白名单为空）⇒ 全部控制串保持丢弃（＝off 行为）")
    # ---- ★ B1（ISSUE-20261006-04）：背景层事件换吃 PSV 金标 ----
    #   PSV 覆盖场用 `PSV演出\时间线.tsv` 的 SpriteBG；未覆盖场回落「演出表 op=bg 剔题卡」。
    psv_dir = os.path.join(proj, "编程组", "PSV演出")
    psv_bg, psv_bg_all, psv_covered = load_psv_timeline(psv_dir)
    chr_index = load_chr_family_index(proj)
    rev_map = load_rev_asset_map(handoff)
    ov16x9 = load_16x9_override(proj)      # ★ 16:9 覆盖层（ISSUE-20261003-02）：美术交付层的表驱动替换
    content_boxes, (CANVAS_W, CANVAS_H) = load_content_boxes(proj)
    if args.cb_full:
        # ★ 开发用：把四源内容区换成全画布（模拟 D-04）。**只改内存数据**，不写回 UI 组文件。
        for _s in ("ot", "otr", "ota", "otp"):
            _b = content_boxes.get(_s)
            if isinstance(_b, dict):
                print("[cb-full] %s %s,%s,%s,%s → 0,0,%d,%d"
                      % (_s, _b.get("x"), _b.get("y"), _b.get("w"), _b.get("h"), CANVAS_W, CANVAS_H))
                _b["x"], _b["y"], _b["w"], _b["h"] = 0, 0, CANVAS_W, CANVAS_H

    def norm(nid, src):
        nid = (nid or "").strip()
        if not nid:
            return ""
        if nid in scenes:
            return nid
        for cand in ("%s_%s" % (src, nid), nid):
            if cand in scenes:
                return cand
        # 跨源兜底（唯一实测跨源 next：ot.s03_09a2 -> s03c_01a 在 otr）
        for s2 in SRC_ORDER:
            c = "%s_%s" % (s2, nid)
            if c in scenes:
                return c
        return ""

    # ---- 选场景 ----
    order = []
    if args.act:
        sp = json.load(open(os.path.join(script_dir, "spine.json"), encoding="utf-8"))
        acts = sp.get("acts") or []
        if args.act < 1 or args.act > len(acts):
            die("--act 越界：1..%d" % len(acts))
        for sid in acts[args.act - 1].get("scenes") or []:
            if sid in scenes and sid not in order:
                order.append(sid)
    elif args.all:
        sp = json.load(open(os.path.join(script_dir, "spine.json"), encoding="utf-8"))
        seq = []
        for a in sp.get("acts") or []:
            seq += a.get("scenes") or []
        # 番外（side_stories）也纳入全量；`excluded`（32）按 D15 是前奏诗 02_/03_ 的去重件，不入
        # ⚠️ `side_stories` 的元素是**字典**（{scene_id, source, script, group, next, …}），不是字符串
        for sd2 in sp.get("side_stories") or []:
            if isinstance(sd2, dict):
                seq.append(sd2.get("scene_id") or "")
            elif isinstance(sd2, str):
                seq.append(sd2)
        for sid in seq:
            if sid in scenes and sid not in order:
                order.append(sid)
    elif args.scenes:
        for s in args.scenes.split(","):
            s = s.strip()
            if s in scenes and s not in order:
                order.append(s)
    elif args.walk:
        cur = norm(args.walk, "ot")
        if not cur:
            die("起点场景不存在: %s" % args.walk)
        while cur and cur not in order and len(order) < args.walk_depth:
            order.append(cur)
            sc = scenes[cur]
            nxt = [norm(x, sc["source"]) for x in (sc.get("next") or [])]
            nxt = [x for x in nxt if x]
            if len(nxt) == 0 or len(nxt) > 1:      # 分支/终点 => 本切片取第一支
                if nxt:
                    order.append(nxt[0])
                break
            cur = nxt[0]
    if not order:
        die("没有选中任何场景（用 --scenes/--walk/--all）")

    # ---- 输出目录 ----
    game = os.path.join(args.out, "game") if os.path.basename(args.out.rstrip("\\/")) != "game" else args.out
    story_dir = os.path.join(game, "story")
    asset_dir = os.path.join(game, "story_assets")
    os.makedirs(story_dir, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    copied = {}
    stats = dict(scenes=0, lines=0, voice=0, bg=0, chr=0, se=0, bgm=0, bgm_cue=0, scenes_with_cue=0,
                 chr_skip=0, movie_skip=0,
                 # ---- 逐行演出（C21）统计 ----
                 stage_ops=0, stage_chr=0, stage_se=0, stage_remove=0, stage_move=0,
                 stage_bg=0,                # ★ 本轮新增：背景层 bg 事件（已发进 stage[]，P0-A）
                 # ★ B1（ISSUE-20261006-04）背景换源分账：
                 bg_psv=0,                  # 来自 PSV 时间线 SpriteBG 的背景事件
                 bg_fallback=0,             # 回落自 演出表 op=bg（剔题卡）的背景事件
                 bg_fallback_scenes=0,      # 走回落路径的场数（未覆盖场）
                 bg_covered_scenes=0,       # 有 PSV 覆盖的场数
                 bg_covered_empty=0,        # 有覆盖但 PSV 无 SpriteBG 的场数（=0 事件，如实登记）
                 bg_ec_dropped=0,           # 回落路径被剔除的题卡(ec##)条数
                 bg_psv_missing=0,          # PSV 背景行 delivery 为空（status=missing）|
                 bg_psv_subdiff=0,          # PSV 背景行 status=sub-diff（按 C16 口径采用并留痕）
                 bg_psv_overlay_skipped=0,  # PSV 叠加层(SpriteBS/Sprite)只计数的条数
                 stage_place=0,             # ★ 本轮新增：自造重排改发 chr_place（瞬时落位，P0-D）
                 stage_chr_filtered=0,      # 被族过滤的 chr_* 非角色族条数
                 stage_chr_missing=0,       # chr target 取件失败
                 stage_se_missing=0,        # se target 取件失败（对不上账）
                 # 叠加层 bg（otv 且 arg3 ∉ {"", SpriteBG}）：**P0 不实现**，只计数登记（判据见 build_stage）
                 stage_bg_skipped=0,
                 stage_slot_over=0,         # 超槽位
                 # ★ op=other 控制串语义接入（层 2 · tier1，ISSUE-20261007-02）
                 stage_other_mapped=0,      # 命中 7 token 且在严格梯白名单内、**成功发出**（chr_remove/chr_place）的条数
                 stage_other_nofam=0,       # 命中 7 token 但**不在严格梯白名单内**（含族身份表无 fam/粗筛排除）⇒ 保持丢弃
                 stage_other_dropped=0,     # 有严格梯 fam 但**运行期取不到**（族不在场/槽越界）⇒ 保持丢弃
                 stage_other_nostate=0,     # 　└ 明细：发出时该族**不在场**（含非角色族 cin/cit/pon 被 build 过滤）
                 stage_other_noslot=0,      # 　└ 明细：在场但占不到可绘槽（slot ≥ STAGE_MAX_SLOTS）
                 stage_other_unmapped=0,    # 未命中 7 token（表外/复合串/坐标串）**保持丢弃**的条数
                 ov16x9_hit=0,              # 命中 16:9 覆盖层的取件次数（ISSUE-20261003-02）
                 # ---- 选择支配位（ISSUE-20261003-03）----
                 choice_missing=0,          # 仍有「未解析（留空）」选项的场景数（须为 0）
                 choice_label_dropped=0,    # 被判为「标签非选项」而移除的项数
                 choice_fallback=0,         # 走「兜底指向首个出口」的场景数（配对未确证）
                 choice_next_unused=[],     # 未被任何选项指向的出口（登记用）
                 miss_art=[], miss_media=[], disabled=[], diff_subst=[], null_ref=[])
    choice_log = []            # (场景id, 项序, 文本, 目标, 依据) —— 全量落盘供复核

    def take_asset(kind, relpath, srcdir):
        """把实文件复制进 story_assets，返回 (游戏内引用名, w, h)；失败返回 ("",0,0)。

        ★ **16:9 覆盖层**（ISSUE-20261003-02）：只对**美术交付层**（`srcdir == art_root`）生效。
          命中覆盖表时改到 `资源组\\<新件路径>` 取件；表外的件一律走原路径（零影响）。
        """
        src = os.path.join(srcdir, relpath.replace("/", os.sep))
        if srcdir == art_root:
            _ov = ov16x9.get((relpath or "").replace("\\", "/"))
            if _ov:
                src = os.path.join(proj, "资源组", _ov.replace("/", os.sep))
                stats["ov16x9_hit"] += 1
        if not os.path.isfile(src):
            stats["miss_media"].append(relpath)
            return "", 0, 0
        flat = kind + "__" + re.sub(r"[^0-9A-Za-z_.\-]", "_", os.path.basename(relpath))
        if flat not in copied:
            shutil.copyfile(src, os.path.join(asset_dir, flat))
            copied[flat] = relpath
        w, h = img_size(os.path.join(asset_dir, flat))
        return "story_assets/" + flat, w, h

    def resolve_chr(target):
        """chr target(out_relpath) → (交付路径, 结论)。主链 `素材引用映射` 优先，缺则反向链。"""
        deliv, concl = resolve_asset(target, ref_map)
        if deliv:
            return deliv, concl
        parts = target.split("/")
        if len(parts) == 3:
            v = rev_map.get((parts[0], parts[1], parts[2]))
            if v:
                return v[0], ("有差异替代" if v[1] == "有差异" else "等价替代")
        return "", ""

    def bg_rows_for(sid, src):
        """背景层事件源（B1）：返回 (rows, covered)。

        · 覆盖场（`场景映射.tsv` 有 scene_id）⇒ PSV 时间线 `SpriteBG`（**金标**）；
        · 未覆盖场 ⇒ 回落「`演出_<源>.tsv` 的 `op=bg` **剔除题卡族（`ec##`）**」，
          **无源侧卡/背景判别**，按最接近还原，须在日志/记录如实标注。
        rows 元素统一为 dict(seq, psv, deliv, target, status, name, concl)：
          · `deliv`：PSV 行＝交付层相对路径（直接用，不走 C16）；回落行＝空，走 target→C16。
          · `status`：PSV 行原样（`sub-diff` 按既有 C16 口径处理）；回落行＝空。
        """
        psv_overlay = 0
        if sid in psv_covered:
            stats["bg_covered_scenes"] += 1
            out = []
            for r in psv_bg_all.get(sid, []):
                if (r.get("type") or "").strip() != "SpriteBG":
                    psv_overlay += 1        # 叠加层（SpriteBS/Sprite）：只计数不实现（P2）
                    continue
                try:
                    seq = int((r.get("seq") or "0").strip() or "0")
                except ValueError:
                    seq = 0
                out.append(dict(seq=seq, psv=True, deliv=(r.get("delivery") or "").strip(),
                                target="", status=(r.get("status") or "").strip(),
                                name=(r.get("name") or "").strip(), concl=""))
            if psv_overlay:
                stats["bg_psv_overlay_skipped"] += psv_overlay
            if not out:
                stats["bg_covered_empty"] += 1
            return out, True
        # ---- 回落路径（未覆盖场）：演出表 op=bg 剔题卡 ----
        stats["bg_fallback_scenes"] += 1
        out = []
        for r in staging.get(sid, []):
            if (r.get("op") or "").strip() != "bg":
                continue
            a3 = (r.get("arg3") or "").strip()
            if (src == "otv") and (a3 != "") and (a3 != "SpriteBG"):
                stats["stage_bg_skipped"] += 1      # otv 叠加层：只计数（同 P0 口径）
                continue
            t = (r.get("target") or "").strip()
            if not t:
                continue
            if is_ec_card_name(t):
                stats["bg_ec_dropped"] += 1         # ★ B1 排除项：题卡不得进背景层
                continue
            try:
                seq = int((r.get("seq") or "0").strip() or "0")
            except ValueError:
                seq = 0
            out.append(dict(seq=seq, psv=False, deliv="", target=t, status="",
                            name="", concl=""))
        return out, False

    def build_stage(sid, rows, src, bgrows):
        """把一个场景的演出行组装成 `stage[]`（已解析几何/槽位/实件）+ 逐场景计数。

        ★ 消费 chr_*、se 与 bg；`bgm/movie/wait/effect` 不在本轮范围（`other` 由
          `--other-semantics tier1` 按严格梯白名单 194 条有条件消费，默认 off 即丢弃）。
          （BGM 仍走既有挂接表+切换点）。

        ★★ 背景层（P0-A 建立，B1/ISSUE-20261006-04 换源）：
          · 事件来源**不再从 `rows`（演出表）取**，改由 `bgrows`（见 `bg_rows_for`）传入：
            覆盖场＝PSV `SpriteBG`；未覆盖场＝演出表 `op=bg` 剔题卡。题卡族（`ec##`）
            **一律不进背景层**（B1 排除项）。
          · 背景层事件进 `stage[]`（运行期由 ui_staging 分发到 ui_story 的 dlg.content）；
            与 chr/se 事件**按 seq 稳定归并**（同 seq 时 chr/se 先、bg 后；bg 之间保持源顺序）。
            同时**按 stage 事件顺序去重**得到本场 `bg[]`（＝回退兜底候选）。
          · **叠加层只计数、只登记**（`stage_bg_skipped` / `bg_psv_overlay_skipped`），P2 再做。
        """

        cb = content_boxes.get(src)
        if not cb:
            cb = dict(x=0, y=0, w=CANVAS_W, h=CANVAS_H)
        # 逐场景计数 = 结束时与进入时的差值（stats 是全局累计）
        snap = dict((k, stats[k]) for k in ("stage_chr", "stage_se", "stage_remove",
                                            "stage_move", "stage_place", "stage_bg",
                                            "stage_chr_filtered", "stage_bg_skipped"))
        # ---- 第一遍：解析 chr/se，过滤，收集族出现序 ----
        ev = []            # 统一的按文件物理先后的触发序
        fam_seen = []
        for r in rows:
            op = (r.get("op") or "").strip()
            if op == "" or op == "skip":
                continue
            try:
                seq = int((r.get("seq") or "0").strip() or "0")
            except ValueError:
                seq = 0
            if op == "bg":
                # ★ B1 换源（ISSUE-20261006-04）：背景层事件**不再**从演出表 `rows` 取——
                #   改由 `bgrows`（PSV 金标 / 回落剔题卡，见 bg_rows_for）统一构建后按 seq 归并。
                #   原 P0-A 在此消费 `演出表 op=bg` 正是「题卡当背景 + 漏切换」的根因（分析 §一）。
                continue
            if op in ("chr_add", "chr_expr", "chr_move"):
                t = (r.get("target") or "").strip()
                fam = family_of(t, chr_index) if t else ""
                if (not t) or fam == "" or fam.lower() in NONROLE_FAMILIES:
                    # C21⑤：非角色族（cin/f_mis/cit/pon/unparsed）与推不出族者**不得当立绘注入**
                    stats["stage_chr_filtered"] += 1
                    continue
                deliv, concl = resolve_chr(t)
                if not deliv:
                    stats["stage_chr_missing"] += 1
                    continue
                if deliv in disabled:
                    stats["disabled"].append("%s:%s" % (sid, t))
                    continue
                if concl == "有差异替代":
                    stats["diff_subst"].append((sid, t, deliv))
                    if args.strict_c16:
                        continue
                g, w, h = take_asset("chr", deliv, art_root)
                if not g:
                    stats["stage_chr_missing"] += 1
                    continue
                arg1 = (r.get("arg1") or "").strip()
                pri = (r.get("arg2") or "").strip()
                px = py = None
                mm = re.match(r"^\s*(-?\d+)\s*,\s*(-?\d+)", arg1)
                if mm:
                    px = int(mm.group(1)); py = int(mm.group(2))
                if fam not in fam_seen:
                    fam_seen.append(fam)
                ev.append(dict(op=op, fam=fam, t=g, w=w, h=h, px=px, py=py, pri=pri, seq=seq))
                continue
            if op == "chr_remove":
                t = (r.get("target") or "").strip()
                fam = family_of(t, chr_index) if t else ""
                if t and fam and fam.lower() in NONROLE_FAMILIES:
                    stats["stage_chr_filtered"] += 1
                    continue
                # target 空 ⇒ 源侧「CharacterDelete :SpriteMax 0」无 :Number ⇒ **清空该场景全部立绘**
                ev.append(dict(op="chr_remove", fam=fam, t="", w=0, h=0, px=None, py=None, pri="", seq=seq))
                continue
            if op == "se":
                t = (r.get("target") or "").strip()
                if not t:
                    ev.append(dict(op="se", fam="", t="", w=0, h=0, px=None, py=None, pri="", seq=seq))  # 停止全部
                    continue
                g, w, h = take_asset("se", t, media_root)
                if not g:
                    stats["stage_se_missing"] += 1
                    continue
                ev.append(dict(op="se", fam="", t=g, w=0, h=0, px=None, py=None, pri="", seq=seq))
                continue
            # ★ op=other 控制串语义接入（层 2 · tier1，ISSUE-20261007-02）：默认 off ⇒ 与接入前一致（丢弃）。
            #   tier1 时：先过**内联 7 token 表**（控制串 → 令 op/x），再到 `other_fam`
            #   （＝族身份表 ∩ 严格梯白名单＝194）取目标族；两者齐备才收进 `ev`（第二遍发出）。
            #   缺一即**保持丢弃并计数**（不猜）。
            if op == "other":
                if other_fam:
                    ctrl = (r.get("arg1") or "").strip()
                    tok = other_token(ctrl)
                    if tok is not None:
                        fam = other_fam.get((src, sid, seq, ctrl), "")
                        if fam:
                            ev.append(dict(op="other_ctrl", fam=fam, t="", w=0, h=0, px=None, py=None,
                                           pri="", seq=seq, ctrl=ctrl, tok=tok))
                            continue
                        stats["stage_other_nofam"] += 1     # 7 token 但不在严格梯白名单 ⇒ 丢弃
                        continue
                    stats["stage_other_unmapped"] += 1      # 非 7 token（复合/坐标/EyeCatch）⇒ 丢弃
                continue
            # 其余 op（bgm/movie/wait/effect）：本轮不处理
        # ---- ★ B1：构建背景层事件（PSV 金标 / 回落剔题卡），并按 seq 稳定归并进 `ev` ----
        #   归并规则：chr/se（`ev`）先入、bg 后入，随后 `sort(key=seq)`（Python 稳定排序）⇒
        #   同 seq 时保持「chr/se 在 bg 之前」、bg 之间保持源顺序（满足 B1 验收②的背景序列）。
        #   seq 排序不改变 chr/se 相互顺序：演出表本身按 seq 升序（C21 触发序＝文件物理先后）。
        _bg_ev = []
        for r in bgrows:
            seq = r["seq"]
            concl = r["concl"]
            if r["psv"]:
                # PSV 行：`delivery` 已是交付层相对路径，直接用；`status=sub-diff` 按既有 C16 口径。
                deliv = r["deliv"]
                if not deliv:
                    stats["bg_psv_missing"] += 1         # status=missing（76 行）：取不到件，如实计数
                    continue
                if r["status"] == "sub-diff":
                    stats["bg_psv_subdiff"] += 1
                    stats["diff_subst"].append((sid, r["name"], deliv))
                    if args.strict_c16:
                        continue
                if deliv in disabled:
                    stats["disabled"].append("%s:%s" % (sid, deliv))
                    continue
                if is_ec_card_name(deliv) or is_ec_card_name(r["name"]):
                    stats["bg_ec_dropped"] += 1          # ★ 保险：题卡不得进背景层
                    continue
                g, w, h = take_asset("bg", deliv, art_root)
                if not g:
                    stats["bg_missing"] = stats.get("bg_missing", 0) + 1
                    continue
                _bg_ev.append(dict(op="bg", fam="", t=g, w=w, h=h, px=None, py=None, pri="", seq=seq))
                stats["bg_psv"] += 1
                continue
            # 回落行：target(out_relpath) → C16 两步链 → 交付件
            t = r["target"]
            deliv, concl = resolve_asset(t, ref_map)
            if deliv and deliv in disabled:
                stats["disabled"].append("%s:%s" % (sid, t))
                continue
            if not deliv:
                stats["miss_art"].append("%s:%s" % (sid, t))
                stats["bg_missing"] = stats.get("bg_missing", 0) + 1
                continue
            if concl == "有差异替代":
                stats["diff_subst"].append((sid, t, deliv))
                if args.strict_c16:
                    continue
            g, w, h = take_asset("bg", deliv, art_root)
            if not g:
                stats["bg_missing"] = stats.get("bg_missing", 0) + 1
                continue
            _bg_ev.append(dict(op="bg", fam="", t=g, w=w, h=h, px=None, py=None, pri="", seq=seq))
            stats["bg_fallback"] += 1
        ev = ev + _bg_ev
        ev.sort(key=lambda e: e["seq"])
        # ---- 槽位分配（族→槽；固定摆位规则见文件头）----
        N = len(fam_seen)
        slot_of = {}
        for i, f in enumerate(fam_seen):
            slot_of[f] = i
        for e in ev:
            if e["op"] == "chr_move" and e["fam"] and e["fam"] not in slot_of:
                slot_of[e["fam"]] = len(slot_of)
        # ---- 立绘横向布局（用户 2026-10-02 规则）：按各族**最大宽度**反解，保证不重叠、不出画 ----
        #   ★ 同屏人多时（实测存在 4 人同屏、宽度合计 2238px > 可用 1840px）**按场景自适应降缩放**：
        #     先把基准宽的立绘宽度算出来，若放不下就按比例缩小该场景的有效缩放（不低于保底值），
        #     否则「不重叠」这条用户硬要求无法满足。同屏少人的场景仍用基准缩放。
        _gh_lay = int(round(cb["h"] * STAGE_CHR_SCALE))
        _fam_ar = {}
        for e2 in ev:
            if e2["op"] in ("chr_add", "chr_expr") and e2["fam"] and e2["h"]:
                _ar2 = e2["w"] / float(e2["h"])
                # ★ **比高还宽（宽高比 > 1.0）的条目不参与立绘宽度反解**（2026-10-03 修「立绘极小」）：
                #   站姿立绘必然**竖构图**（本作实测宽高比 0.55–0.87）；比高还宽的是**整屏 CG**（1.33/1.78）
                #   或**横幅差分**（2.65）——源侧会把它们当某族的"表情差分"塞进 `chr_expr`
                #   （实测 `ot_s01_02a` 的 `asu08a/asu08i/kaz01h` 都是 2560×1440 整屏图）。
                #   若把它的宽高比计入该族的代表宽度，布局会以为这个族要占 1281px
                #   ⇒ 整场被压到保底缩放 ⇒ **所有立绘变极小**（用户实测截图即此）。
                #   注：`is_fullscreen()` 只认「宽高比≈内容区」，4:3 框下认不出 16:9 整屏 CG，故此判据独立存在。
                if _ar2 > 1.0 or is_fullscreen(e2["w"], e2["h"], cb):
                    continue
                if _ar2 > _fam_ar.get(e2["fam"], 0.0):
                    _fam_ar[e2["fam"]] = _ar2
        #   ⚠️ 只对**前 STAGE_MAX_SLOTS 个族**布局：五源**无退场信号** ⇒ `slot_of` 会把整场出现过的族全算上
        #   （实测最多 20 个），而运行期只有 `STAGE_MAX_SLOTS`(=6) 个槽 ⇒ 若按全部族铺开，会把位置浪费在
        #   **根本显示不出来**的族上、把真正显示的那几个挤到极小。故按「先出现的 6 个」定位置。
        # ---- ★ 可见集上限（ISSUE-20261003-05）：宁可少画几个，也要保住可读尺寸 ----
        #   根因：五源**无退场信号**（C21 边界①），且源侧有时把**整场十几个族一次性"上场"**
        #   （实测 `ot_s04_08a` **19 个族挤在同一 seq**、`otp_staff` 20 个、`ota_42_5` 14 个）。
        #   照单全画 ⇒ 自适应缩放一路降到保底 **0.35**（1080×0.35＝378px 高）。
        #   规则：按「**本场景实际说话人优先**（`lines[].speaker` → `role2fam`，按首次说话序）
        #   ＞ 其余按出场序」排优先级，取**能在 ≥ `STAGE_CHR_MIN_VIS` 缩放下放下**的最大前缀；
        #   落选族 **slot 置 99**（`uiStagingShowSlot` 对超界 slot 直接不画）。
        #   ⚠️ 说话人优先是**真信号**（不是猜）：`lines[].speaker` 与 `chr[]` 的 role→fam 都是实测字段。
        _spk = []
        for _l in (sc.get("lines") or []):
            _f = role2fam.get((_l.get("speaker") or "").strip())
            if _f and _f in slot_of and _f not in _spk:
                _spk.append(_f)
        _spkset = set(_spk)
        _order = _spk + [f for f in sorted(slot_of, key=lambda x: slot_of[x]) if f not in _spk]
        _avail = cb["w"] - 2 * STAGE_CHR_EDGE
        _n_all = len(slot_of)
        _keep = _order[:STAGE_MAX_SLOTS]
        # ★★ **只砍非说话人**：说话的人必须有立绘（砍掉＝「角色在说话、画面上却没他」，
        #   那是比"小"更严重的缺陷）。故砍人只在「队尾还有非说话人」时进行；
        #   若砍到只剩说话人仍放不下 ⇒ **停止砍人**，交给下面既有的自适应降缩放（保底 0.35）。
        while len(_keep) > 1:
            _ws = [int(round(_fam_ar.get(f, 0.6) * _gh_lay)) for f in _keep]
            if sum(_ws) + STAGE_CHR_GAP * (len(_ws) - 1) <= _avail:
                break
            _k2 = (_avail - STAGE_CHR_GAP * (len(_ws) - 1)) / float(sum(_ws))
            if STAGE_CHR_SCALE * _k2 >= STAGE_CHR_MIN_VIS:
                break
            _victim = -1
            for _i in range(len(_keep) - 1, -1, -1):
                if _keep[_i] not in _spkset:
                    _victim = _i
                    break
            if _victim < 0:
                break                        # 全是说话人 ⇒ 不砍，走自适应降缩放
            _keep.pop(_victim)
        # ★★ **必须重编号**（ISSUE-20261003-12，一审 Critical）：保留族占 0..len(_keep)-1，其余置 99。
        #   原实现只把「落选族」置 99、**从不给保留族重新编号** ⇒ 保留族沿用「出场序索引」，
        #   若该索引 ≥ STAGE_MAX_SLOTS(6)，运行期 `uiStagingShowSlot` 判定超界 ⇒ **保留却不可见**；
        #   而原本可见的「出场序前 6」又被顶掉 ⇒ **净少画**（实测 63 个场景共少 92 个绘制族次），
        #   且「说话人优先」对**晚出场**的说话人完全失效（它被保留、却仍不可见）。
        _dropped = [f for f in slot_of if f not in _keep]
        for _i2, _f2 in enumerate(_keep):
            slot_of[_f2] = _i2
        for f in _dropped:
            slot_of[f] = 99
        if _dropped:
            stats["stage_dropped"] = stats.get("stage_dropped", 0) + len(_dropped)
            stats["stage_drop_scenes"] = stats.get("stage_drop_scenes", 0) + 1
            # 写「保留 N / 实绘 M」两个数：重编号后二者相等，留作自检（一审指出原打印只有保留数）
            stats.setdefault("stage_drop_worst", []).append(
                "%s %d→保留%d/实绘%d" % (sid, _n_all, len(_keep),
                                      len([f for f in _keep if 0 <= slot_of.get(f, -1) < STAGE_MAX_SLOTS])))
        _fams_big = [f for f in _keep]
        _lay_w = [int(round(_fam_ar.get(f, 0.6) * _gh_lay)) for f in _fams_big]
        _s_eff = STAGE_CHR_SCALE
        if len(_lay_w) >= 2:
            _sum0 = sum(_lay_w)
            if _sum0 + STAGE_CHR_GAP * (len(_lay_w) - 1) > _avail:
                _k = (_avail - STAGE_CHR_GAP * (len(_lay_w) - 1)) / float(_sum0)
                _s_eff = max(STAGE_CHR_SCALE_FLOOR, STAGE_CHR_SCALE * _k)
                _gh_lay = int(round(cb["h"] * _s_eff))
                stats["stage_tight"] = stats.get("stage_tight", 0) + 1
        _smin = stats.get("stage_scale_min", STAGE_CHR_SCALE)
        if _s_eff < _smin:
            stats["stage_scale_min"] = _s_eff
        gh_used = _gh_lay                    # ← 该场景实际采用的立绘高度（第二遍几何用它）
        # ---- 第二遍：算几何、发事件 ----
        out = []
        state = {}      # fam -> dict(x,y,w,h,z,fs)（供 chr_expr 同槽换图 / chr_move 保尺寸）

        # ★ 立绘横向布局（用户 2026-10-02 规则）：**按「当前在场集合」实时重排**——
        #   1 号左 / 2 号右 / 其余居中均分、从左到右、互不重叠。
        #   为什么必须"实时"：**场景级固定槽**会把实际同屏的两人落到相邻的"中间"槽 ⇒ 重叠
        #   （全量实测：121 场景有重叠，其中 **68 个场景只有 2 人同屏却仍重叠**）。
        #   缩放仍取**场景级**（同屏人多时自适应降缩放，在任何子集下都不会更挤）。
        def _relayout(extra=None):
            # ⚠️ 只算**运行期画得出来**的族：`ui_staging.tjs` 的槽位上限是 `UIStageMaxSlots`(=STAGE_MAX_SLOTS)，
            #   slot ≥ 上限的族**永远不会显示**（`uiStagingShowSlot` 对超界 slot 直接 return false）
            #   ⇒ 若把它们也算进重排，会白白占掉位置、把真正显示的那几个挤到重叠。
            #   `extra`＝**即将入场**的族（调用方还没把它写进 state）⇒ 一并排位（排在最后＝出场序）。
            fams = [f for f in state.keys()
                    if (not state[f].get("fs")) and (0 <= slot_of.get(f, -1) < STAGE_MAX_SLOTS)]
            if extra is not None and (extra not in fams) \
               and (0 <= slot_of.get(extra, -1) < STAGE_MAX_SLOTS):
                fams = fams + [extra]
            if not fams:
                return {}
            ws = [int(round(_fam_ar.get(f, 0.6) * gh_used)) for f in fams]
            cxs = stage_slot_layout(len(fams), ws, cb)
            # 自检：相邻重叠对数必须为 0（可失败，不是空跑）
            o = sorted(range(len(cxs)), key=lambda i: cxs[i])
            ov = 0
            for i in range(1, len(o)):
                a, b = o[i - 1], o[i]
                if cxs[b] - cxs[a] < (ws[a] + ws[b]) / 2.0:
                    ov += 1
            stats["stage_overlap"] = stats.get("stage_overlap", 0) + ov
            return {f: cxs[i] for i, f in enumerate(fams)}

        def _emit_moves(newpos, seq):
            """在场集合变化后，把**变位**的老成员补发 `chr_place`（自造重排专用）。

            ★ P0-D（ISSUE-20261006-02，用户实报「人物乱飘」）：本函数产出的移位是**我方自造的
              重排**（源侧无此信号），此前发 `chr_move` 会被运行期渲染成 **0.3s 滑动动画** ⇒ 实机「乱飘」。
              改发新 op **`chr_place`**：运行期 `uiStagingPlaceSlot` **瞬时落位、不起动画**。
              ⚠️ **源侧真移位**（`otv` 的 `chr_move` 行）不走此处、保持原样走 0.3s 滑动
                （尊重用户 2026-10-03 裁定；见第二遍循环里的 `if op == "chr_move"` 分支）。
            """
            for f in list(state.keys()):
                st = state[f]
                if st.get("fs"):
                    continue
                cx = newpos.get(f)
                if cx is None or abs(st["cx"] - cx) < 1.0:
                    continue
                st["cx"] = cx
                st["x"] = int(round(cx - st["w"] / 2.0))
                out.append(dict(seq=seq, op="chr_place", slot=slot_of.get(f, -1), fam=f,
                                t="", x=st["x"], y=st["y"], w=-1, h=-1, z=st["z"]))
                stats["stage_place"] += 1
        for e in ev:
            op = e["op"]
            # ★ op=other 控制串语义接入（层 2 · tier1，ISSUE-20261007-02）：在此发出事件。
            #   目标族已在第一遍由**族身份表 ∩ 严格梯白名单**定好（`e["fam"]`，194 条），此处不再做
            #   任何归属推断（旧 `concurrent`/`edge-*` 规则已废止）。仅做**运行期可行性**守卫：
            #   目标族须**已在场且占 0..STAGE_MAX_SLOTS-1 可绘槽**，否则画不出 ⇒ 丢弃，不猜。
            if op == "other_ctrl":
                tok = e.get("tok") or ("", None)     # (op, x)
                fam = e.get("fam") or ""
                if (not fam) or (fam not in state):
                    stats["stage_other_nostate"] += 1
                    stats["stage_other_dropped"] += 1
                    continue
                if not (0 <= slot_of.get(fam, -1) < STAGE_MAX_SLOTS):
                    stats["stage_other_noslot"] += 1
                    stats["stage_other_dropped"] += 1
                    continue
                if tok[0] == "chr_remove":
                    out.append(dict(seq=e["seq"], op="chr_remove", slot=slot_of[fam], fam=fam,
                                    t="", x=0, y=0, w=0, h=0, z=0))
                    stats["stage_remove"] += 1
                    stats["stage_other_mapped"] += 1
                    state.pop(fam, None)
                    # ★ 与既有 chr_remove 同口径：**退场不重排**（其余立绘原地留位）。
                    continue
                # tok[0] == chr_place：源侧方向 token → x（1280×720 逻辑画布，与 otv :Position 同系）
                try:
                    px = float(tok[1])
                except (TypeError, ValueError):
                    stats["stage_other_dropped"] += 1
                    continue
                st = state[fam]
                st["cx"] = cb["x"] + px * cb["w"] / 1280.0
                nx = int(round(st["cx"] - st["w"] / 2.0)); ny = int(round(st["cy"]))
                st["x"] = nx; st["y"] = ny
                out.append(dict(seq=e["seq"], op="chr_place", slot=slot_of[fam], fam=fam,
                                t="", x=nx, y=ny, w=-1, h=-1, z=st["z"]))
                stats["stage_place"] += 1
                stats["stage_other_mapped"] += 1
                continue
            if op == "bg":
                # ★ P0-A 背景层事件。x/y 为占位（运行期按素材宽高比在 dlg.content 内做 contain）；
                #   w/h 落**素材实测尺寸**——运行期要复用既有 contain 适配（它按 aw/ah 挑框），
                #   若落画布尺寸则 4:3 素材会被误当满幅（依据：ui_story.tjs 的 uiStoryApplyScene 同口径）。
                #   z=1 对齐既有背景层 dlg.content 的 z（build 注释 STAGE_Z 段：背景=1 < 立绘=10 < 文字=22）。
                out.append(dict(seq=e["seq"], op="bg", slot=-1, fam="", t=e["t"],
                                x=0, y=0, w=e["w"], h=e["h"], z=1))
                stats["stage_bg"] += 1
                continue
            if op == "se":
                out.append(dict(seq=e["seq"], op="se", slot=-1, fam="",
                                t=e["t"], x=0, y=0, w=0, h=0, z=0))
                stats["stage_se"] += 1
                continue
            if op == "chr_remove":
                if e["fam"]:
                    # 指定族的退场：仅当该族**本场景已建槽**才发；否则**跳过**——
                    # 绝不落成「清空全部」（`slot=-1`），避免把未建槽的族误当整屏清屏。
                    if e["fam"] not in slot_of:
                        stats["stage_chr_missing"] += 1
                        continue
                    slot = slot_of[e["fam"]]
                    out.append(dict(seq=e["seq"], op="chr_remove", slot=slot, fam=e["fam"],
                                    t="", x=0, y=0, w=0, h=0, z=0))
                    stats["stage_remove"] += 1
                    state.pop(e["fam"], None)
                    # ★ 用户 2026-10-03 裁定：**退场不重排**——其余立绘原地留位（退场者空出的位置不补）。
                    #   （原实现在此重排并补发 chr_move；现删除 ⇒ 场景内后续**有人入场**时才会再统一排位。）
                else:
                    # target 空 ⇒ 源侧「CharacterDelete :SpriteMax 0」无 :Number ⇒ **清空该场景全部立绘**
                    out.append(dict(seq=e["seq"], op="chr_remove", slot=-1, fam="",
                                    t="", x=0, y=0, w=0, h=0, z=0))
                    stats["stage_remove"] += 1
                    state = {}
                continue
            if op == "chr_move":
                slot = slot_of.get(e["fam"], -1)
                if slot < 0 or e["fam"] not in state:
                    stats["stage_chr_missing"] += 1
                    continue
                st = state[e["fam"]]
                if e["px"] is not None:
                    st["cx"] = cb["x"] + e["px"] * cb["w"] / 1280.0
                    # 顶 y 与主路径同口径：**底边贴内容区下沿** + 源侧 y 偏移（按缩放同比例）
                    st["cy"] = (cb["y"] + cb["h"] - st["h"]
                                + int(round((e["py"] or 0) * cb["h"] / 720.0 * STAGE_CHR_SCALE)))
                nx = int(round(st["cx"] - st["w"] / 2.0)); ny = int(round(st["cy"]))
                st["x"] = nx; st["y"] = ny
                out.append(dict(seq=e["seq"], op="chr_move", slot=slot, fam=e["fam"],
                                t="", x=nx, y=ny, w=-1, h=-1, z=st["z"]))
                stats["stage_move"] += 1
                continue
            # chr_add / chr_expr
            slot = slot_of.get(e["fam"], -1)
            if slot < 0:
                stats["stage_slot_over"] += 1
                continue
            fs = is_fullscreen(e["w"], e["h"], cb)
            # ---- 立绘尺寸：高度 ＝ 内容区高 × STAGE_CHR_SCALE（用户 2026-10-02「立绘太大」）----
            #      缩放**以底边为基准**：底边恒贴内容区下沿（cb.y+cb.h），顶随缩放下移。
            if fs:
                gw, gh = cb["w"], cb["h"]
            else:
                gh = gh_used                      # 本场景实际采用（同屏人多时会自适应降缩放）
                gw = int(round(e["w"] * gh / float(e["h"])))
            # 锚点：**中心 x + 顶 y**（换表情时宽度会变，必须按中心定位，否则左沿钉住会让角色横移）
            if src == "otv" and e["px"] is not None:
                acx = cb["x"] + e["px"] * cb["w"] / 1280.0
                acy = cb["y"] + int(round((e["py"] or 0) * cb["h"] / 720.0 * STAGE_CHR_SCALE))
            else:
                # ★ 我方自定摆位（非源侧事实）：位置由 `_relayout()`（按**当前在场集合**）给出；
                #   已在场者先沿用旧中心（随后集合一变就统一重排），新入场者暂给画布中心占位。
                if (e["fam"] in state) and (not fs):
                    acx = state[e["fam"]]["cx"]
                else:
                    acx = cb["x"] + cb["w"] * 0.5
                acy = cb["y"]
            if not fs:
                acy = cb["y"] + cb["h"] - gh + (acy - cb["y"])      # 底边对齐 + 源侧 y 偏移
            # 同族换表情且无新位置：**继承该族的中心/顶**（不改位置，只换图）
            # ★ P0-B（ISSUE-20261006-02，已证实缺陷）：**当该族上一拍是整屏件时不继承 cy**。
            #   根因：整屏分支把 state[fam]["cy"] 写成 `cb["y"]`（本构建内容区 y=0 ⇒ cy=0），
            #   而紧随其后的「整屏→立绘」重排分支**只重算 acx、不重算 acy**（见下 `_relayout` 段）
            #   ⇒ 若在此继承 cy，该立绘此后**永久停在 y=0**（实测 scene_ot_s01_02c：seq44–54 y:216
            #   → seq56 整屏件 → seq59 起 y:0）。故条件加 `not state[fam].get("fs")`：
            #   整屏转立绘时保留本拍已算好的「底边对齐」acy（cb.y+cb.h-gh）。
            if (op == "chr_expr") and (e["fam"] in state) and (e["px"] is None) and (not fs) \
               and (not state[e["fam"]].get("fs")):
                acx = state[e["fam"]]["cx"]; acy = state[e["fam"]]["cy"]
            # ★ **本族首次出场** ⇒ 按当前在场集合重排（用户 2026-10-02 规则：1 左 / 2 右 / 其余居中、不重叠）。
            #   ⚠️ 触发条件是「**本族不在 state**」而**不是** `op == "chr_add"`：源侧也用 `chr_expr`
            #     引入新族（实测 `ota_23_1b`/`ot_s01_02a` 首个立绘 op 就是 `chr_expr`）——只看 chr_add 会漏排、
            #     两个族都落到画布中心而重叠。
            #   顺序：先把老成员的位移落成 `chr_move`（文件序在本次事件之前）⇒ 引擎先移位、再让新角色入场。
            #   ⚠️ 还要覆盖「**该族上一拍是整屏件、这一拍变成普通立绘**」：此时它虽已在 state 里，
            #     却带着整屏件的中心（=画布中心）⇒ 不重排就会压住别人（实测 `ot_s01_02a`/`np_a*` 即此型）。
            if (not fs) and ((e["fam"] not in state) or state[e["fam"]].get("fs")):
                _np = _relayout(extra=e["fam"])
                _emit_moves(_np, e["seq"])          # 只动**老成员**（新成员还没进 state，不会被动）
                acx = _np.get(e["fam"], cb["x"] + cb["w"] * 0.5)
            if fs:
                # 整屏件：位置已烘焙在图内 ⇒ 落内容区整框，不做槽位偏移
                gx, gy, gw, gh = cb["x"], cb["y"], cb["w"], cb["h"]
            else:
                gx = int(round(acx - gw / 2.0)); gy = int(round(acy))
            # 层序 z：默认 STAGE_Z；**继承该族已设层序**（源侧只给一次 `:Priority` 时后续沿用）；
            # otv 行带显式 Priority 时按 `STAGE_Z + Priority` **更新**（"用它的真层序"）。
            z = STAGE_Z
            if e["fam"] in state:
                z = 0 + state[e["fam"]]["z"]
            if src == "otv" and e["pri"] != "":
                try: z = STAGE_Z + int(e["pri"])
                except ValueError: pass
            state[e["fam"]] = dict(cx=acx, cy=acy, x=gx, y=gy, w=gw, h=gh, z=z, fs=fs)
            out.append(dict(seq=e["seq"], op=op, slot=slot, fam=e["fam"], t=e["t"],
                            x=gx, y=gy, w=gw, h=gh, z=z))
            stats["stage_chr"] += 1
        # ★ P0-A：本场 `bg[]` 回退候选 ＝ 背景层事件**按 stage 事件顺序去重**（保留首个实件路径）。
        #   目的仅是兜底（老存档/无事件场）；运行期主路径是逐条 op=="bg" 事件 + 跨场景延续。
        bgl = []
        _bgl_seen = set()
        for e in out:
            if e["op"] != "bg":
                continue
            if e["t"] in _bgl_seen:
                continue
            _bgl_seen.add(e["t"])
            bgl.append((e["t"], e["w"], e["h"]))
        info = dict(
            chr=stats["stage_chr"] - snap["stage_chr"],
            se=stats["stage_se"] - snap["stage_se"],
            removed=stats["stage_remove"] - snap["stage_remove"],
            moved=stats["stage_move"] - snap["stage_move"],
            placed=stats["stage_place"] - snap["stage_place"],
            bg=stats["stage_bg"] - snap["stage_bg"],
            filtered=stats["stage_chr_filtered"] - snap["stage_chr_filtered"],
            bgskip=stats["stage_bg_skipped"] - snap["stage_bg_skipped"],
            bgl=bgl)
        stats["stage_ops"] += len(out)
        return out, info

    # 逐场景累计计数（build 结束时打印全局账）
    gfiltered = [0]; gbgskip = [0]; gsemiss = [0]; gchrmiss = [0]; gchrops = [0]; gseops = [0]
    # ★ P0-A/P0-D 全局账：背景层事件 / 叠加层事件 / 自造重排(chr_place) / 源侧移位(chr_move)
    gbgev = [0]; gbgov = [0]; gplace = [0]; gmove = [0]

    for sid in order:
        sc = scenes[sid]
        src = sc["source"]

        # ---- 场景级素材：**按 kind 分流** ----
        #   se / sound / voice → 音频 → 素材库
        #   bgm        → **一律 BGM统一\ + 统一名（C18）**，禁止从 krkr素材库\<源>\bgm 取件
        #   chr / movie → 演出层（立绘差分 / 影片）：**演出语义未逆向（C6/R1）⇒ 不取件**，只记数
        #   pic / sys（图像）→ ★ P0-A（ISSUE-20261006-02）起**不再无差别塞进 bg[]**——那正是
        #       「背景乱放」的根因（`sc.assets` 里 CG/立绘/系统件混排，取首个即错）。背景层改由
        #       staging 的 `op=="bg"` 事件驱动（build_stage），`bg[]` 只回收其**去重候选**作兜底。
        bgs = []          # 由 build_stage 的 sInfo["bgl"] 回填（背景层事件按序去重）
        se = []
        bgm = []
        for a in sc.get("assets") or []:
            kind = (a.get("kind") or "").lower()
            # ★ `out_relpath` 可能是 JSON null（全语料 8 条，交接说明 §5.3-4 规定按兜底处理）
            orp = a.get("out_relpath")
            if not orp:
                stats["null_ref"].append("%s:%s(%s)" % (sid, a.get("ref") or "?", kind))
                continue
            orp = "" + orp

            if kind == "bgm":
                uni = bgm_map.get(os.path.basename(orp).lower(), "")
                if not uni:
                    stats["miss_media"].append("%s:%s(BGM统一无此件)" % (sid, orp))
                    continue
                g, w, h = take_asset("bgm", uni, bgm_root)
                if g:
                    bgm.append(g); stats["bgm"] += 1
                continue
            if kind in ("se", "sound", "voice"):
                g, w, h = take_asset("se", orp, media_root)
                if g:
                    se.append(g); stats["se"] += 1
                continue
            if kind in ("chr", "movie"):
                if kind == "chr":
                    stats["chr_skip"] += 1
                else:
                    stats["movie_skip"] += 1
                continue
            # ★ P0-A / B1：其余 kind（pic / sys 等图像）**不再当 bg 候选**。
            #   原实现此处把每张图像经 C16 链取件并压进 `bg[]`（=背景乱放根因）；
            #   现背景层只由 `bg_rows_for()` 提供（B1：PSV SpriteBG / 回落剔题卡，见 build_stage），
            #   故这里**不取件、不登记**（既不复制进 story_assets，也不进 bg[]）。
            stats["art_ignore"] = stats.get("art_ignore", 0) + 1

        # ---- 场景级 BGM（C17/C18）----
        #   优先级：① `BGM切换点.tsv`（otv/np 的源侧播放序，精确到行）→ `bgmCue[]`
        #           ② 源侧实测引用（脚本 assets[] 的 bgm）     ┐
        #           ③ `挂接_BGM.tsv` 推荐统一名（**重建**，带依据等级）┘ → `bgm[]`
        bgmLev = "源侧実引用" if bgm else ""
        hk = bgm_hook.get(sid)
        if hk and hk[0] not in bgm:
            g2, _w2, _h2 = take_asset("bgm", hk[0], bgm_root)
            if g2:
                bgm.append(g2)
                if bgmLev == "":
                    bgmLev = hk[1]
                stats["bgm"] += 1
            else:
                stats["miss_media"].append("%s:BGM统一缺件 %s" % (sid, hk[0]))
        cues = []
        for (seq, ev, uni) in bgm_cues.get(sid, []):
            if ev == "停止" or not uni:
                cues.append((seq, "stop", ""))
                continue
            g3, _w3, _h3 = take_asset("bgm", uni.split()[0], bgm_root)
            if g3:
                cues.append((seq, "play", g3)); stats["bgm_cue"] += 1
            else:
                stats["miss_media"].append("%s:BGM切换点缺件 %s" % (sid, uni))
        if cues:
            stats["scenes_with_cue"] += 1

        # ---- 场景级立绘（挂接表，C17 按场景 id）——只记「角色→族」，**脸文件走 face/ 命名空间**，
        # 不再为每场景复制 face 件（那批数据消费端不读，纯冗余）。
        chrs = []
        for role, fam in scene_chr.get(sid, []):
            if fam:
                chrs.append((role, fam)); stats["chr"] += 1

        # ---- ★ 逐行演出（C21）：立绘 + 逐行音效 + 背景层（B1 换源 PSV 金标）----
        _bgrows, _bgcov = bg_rows_for(sid, src)
        stage, sInfo = build_stage(sid, staging.get(sid, []), src, _bgrows)
        gfiltered[0] += sInfo["filtered"]; gbgskip[0] += sInfo["bgskip"]
        gchrops[0] += sInfo["chr"]; gseops[0] += sInfo["se"]
        gbgev[0] += sInfo["bg"]; gbgov[0] += sInfo["bgskip"]
        gplace[0] += sInfo["placed"]; gmove[0] += sInfo["moved"]
        stats["bg"] += sInfo["bg"]          # [ok] 总账的「背景」＝背景层事件数（P0-A）
        # ★ P0-A：bg[] ＝ 本场背景层事件按序去重（兜底候选）；主路径是逐条 op=="bg" 事件。
        bgs = sInfo["bgl"]

        # 台词
        lines = []
        for l in sc["lines"]:
            vo = ""
            aud = l.get("audio") or []
            if aud:
                vo, _vw, _vh = take_asset("vo", aud[0], media_root)
                if vo:
                    stats["voice"] += 1
            lines.append(dict(k=l.get("kind") or "", sp=l.get("speaker") or "",
                              tx=l.get("cn") or "", vo=vo, ln=l.get("lineno"),
                              # `seq` 供 BGM 切换点按行对齐（C18：切换点精确到 lines[].seq）
                              sq=(l.get("seq") if l.get("seq") is not None else 0)))
        # ---- 选择支（R1：选项↔目标配对未逆向 ⇒ 本器按**有序规则**补全，规则不适用就留空）----
        #   源侧 `choices[].target` 大多为 null（总纲 R1，只给候选目标列表）。补全次序：
        #   ① `target` 已确证 → 直接用；
        #   ② **单出口**（`next` 只有 1 个）→ 所有选项都指向它。源侧这类是「谁来发言／和谁组队」
        #      的**提示**而非分支（13 个 `ota_24_*` 场景实测 `next_kind:linear`）；
        #   ③ **首项是声明标签**：多出 1 项、且首项的声明源点 `#idxN` 与其余项**不同** ⇒ 去掉首项后按位对位。
        #      （`ota_11_3d0` 4→3 项、`ota_12_4c0` 3→2 项，实测首项 `#idx58`/`#idx124` 与其余 `#idx59`/`#idx125` 不同源）；
        #   ④ **等长** → 按位对位（原实现即此，未变）；
        #   ⑤ 其余（选项数 < 出口数）→ 前 `len(choices)` 个按位对位，**多出的出口登记为
        #      「触发条件未确证、当前不可达」**（`ot_s01_12b`/`13b`：2 选项 vs 3 出口，三个出口互为兄弟且
        #      汇流到同一 `next`，无结构线索；选项 1 文案「不邀山科同学，自己回去」与出口 2「山科京独自回去了」
        #      语义吻合 ⇒ 采按位对位，未采用的第 3 个出口另行登记）。
        #   ⚠️ **每条补全都写进 `story\选择支配对说明.tsv`**（含留空的），可逐条复核，不静默。
        raw_ch = list(sc.get("choices") or [])
        choices = []
        nxt = [norm(x, src) for x in (sc.get("next") or [])]
        nxt = [x for x in nxt if x]
        _dropped = None
        if len(raw_ch) == len(nxt) + 1 and len(raw_ch) >= 3:
            _a, _b = decl_idx(raw_ch[0]), decl_idx(raw_ch[1])
            if _a and _b and _a != _b:
                _dropped = raw_ch[0]
                raw_ch = raw_ch[1:]
        for i, c in enumerate(raw_ch):
            tgt = norm(c.get("target") or "", src)
            how = "已确证" if tgt else ""
            if not tgt:
                if len(nxt) == 1:
                    tgt, how = nxt[0], "单出口"
                elif 0 < len(nxt) and i < len(nxt):
                    tgt, how = nxt[i], ("等长对位" if len(nxt) == len(raw_ch) else "按位对位（出口多于选项）")
                elif nxt:
                    # ★ **绝不留空**：留空的选项运行期会被判「目标不在本次切片内」并**终止剧情**
                    #   （`ui_story.tjs::uiStoryChoose`：`to == ""` ⇒ `UIStoryDone = true`）。
                    #   实测 `ota_24_4e`（3 个人格选项 vs 2 个结局出口）会踩这条 ⇒ 兜底到首个出口并单独计数。
                    tgt, how = nxt[0], "兜底（指向首个出口；配对未确证）"
                else:
                    how = "未解析（该场景无出口）"
            choices.append((c.get("text_cn") or c.get("text_jp") or "", tgt))
            choice_log.append((sid, i, c.get("text_cn") or c.get("text_jp") or "", tgt, how))
        if _dropped is not None:
            choice_log.append((sid, -1, _dropped.get("text_cn") or _dropped.get("text_jp") or "",
                               "", "标签（非选项，已从菜单移除）"))
            stats["choice_label_dropped"] += 1
        if choices and any(t == "" for _x, t in choices):
            stats["choice_missing"] += 1
        if raw_ch and any(h.startswith("兜底") for _s, _i, _t, _g, h in choice_log[-len(raw_ch):]):
            stats["choice_fallback"] += 1
        # ★ 只在**本场景有选择支**时才谈「某出口没被任何选项指向」；逐行推进的场景不算（否则会把全库 next 都算进来）
        if raw_ch:
            _used = set(t for _t, t in choices if t)
            for _t in nxt:
                if _t not in _used:
                    stats["choice_next_unused"].append("%s→%s" % (sid, _t))

        # 写场景文件
        parts = []
        parts.append("// 生成物（build_story.py）——勿手改：scene " + sid)
        parts.append("UIStoryScene = %[")
        parts.append("\tid:" + tjs_str(sid) + ", src:" + tjs_str(src) + ",")
        parts.append("\ttitle:" + tjs_str(sc.get("title_cn") or sc.get("title_jp") or "") + ",")
        parts.append("\tnext:[" + ",".join(tjs_str(x) for x in nxt) + "],")
        parts.append("\tchoices:[" + ",".join("%%[ tx:%s, to:%s ]" % (tjs_str(t), tjs_str(g))
                                              for t, g in choices) + "],")
        parts.append("\tbg:[" + ",".join("%%[ a:%s, w:%d, h:%d ]" % (tjs_str(g), w, h)
                                        for g, w, h in bgs) + "],")
        parts.append("\tse:[" + ",".join(tjs_str(x) for x in se) + "],")
        parts.append("\tbgm:[" + ",".join(tjs_str(x) for x in bgm) + "],")
        parts.append("\tbgmLev:" + tjs_str(bgmLev) + ",")
        parts.append("\tbgmCue:[" + ",".join(
            "%%[ seq:%d, ev:%s, t:%s ]" % (sq, tjs_str(ev), tjs_str(tk))
            for sq, ev, tk in cues) + "],")
        parts.append("\tchr:[" + ",".join("%%[ role:%s, fam:%s ]" % (tjs_str(r), tjs_str(f))
                                          for r, f in chrs) + "],")
        # ★ 逐行演出（C21）：`stage[]` 已含**解析后的几何/槽位/实件**；`stageInfo` 是逐场景计数
        #   （供运行期日志复现「过滤了多少非角色族 / 跳过了多少叠加层 bg」）。
        #   `bg`＝背景层事件数（P0-A）；`moved`＝源侧 chr_move 条数、`placed`＝自造重排 chr_place 条数（P0-D）。
        stage_txt = ",\n".join(
            "\t\t%%[ seq:%d, op:%s, slot:%d, fam:%s, t:%s, x:%d, y:%d, w:%d, h:%d, z:%d ]" % (
                e["seq"], tjs_str(e["op"]), e["slot"], tjs_str(e["fam"]), tjs_str(e["t"]),
                e["x"], e["y"], e["w"], e["h"], e["z"])
            for e in stage)
        parts.append("\tstage:[\n" + stage_txt + "\n\t],")
        parts.append("\tstageInfo:%%[ chr:%d, se:%d, removed:%d, moved:%d, placed:%d, bg:%d, filtered:%d, bgskip:%d ],"
                     % (sInfo["chr"], sInfo["se"], sInfo["removed"], sInfo["moved"], sInfo["placed"],
                        sInfo["bg"], sInfo["filtered"], sInfo["bgskip"]))

        # ★ TJS2 铁律：数组字面量**不得有尾逗号**（尾逗号会多出一个 void 元素，
        #   使 lines.count 比实际多 1，循环到末尾即「不能将 (void) 转换为 Object」）。
        #   故 lines 一律用 join 拼接，不逐行追加尾逗号。
        lines_txt = ",\n".join(
            "\t\t%%[ k:%s, sp:%s, tx:%s, vo:%s, sq:%d ]" % (
                tjs_str(l["k"]), tjs_str(l["sp"]), tjs_str(l["tx"]), tjs_str(l["vo"]), l["sq"])
            for l in lines)
        parts.append("\tlines:[\n" + lines_txt + "\n\t]")
        parts.append("];")
        with open(os.path.join(story_dir, "scene_%s.tjs" % sid), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(parts) + "\n")
        stats["scenes"] += 1
        stats["lines"] += len(lines)

    if args.entry:
        entry = norm(args.entry, "ot")
    elif ("ot_s00_00" in order):
        entry = "ot_s00_00"          # 本篇·序文＝可链式主线的真正入口（前奏诗框架剧 next=[] 独立）
    else:
        entry = order[0]
    # 索引文件
    idx_txt = ["// 生成物（build_story.py）——勿手改：切片场景顺序索引"]
    idx_txt.append("UIStoryIndex = [" + ",".join(tjs_str(x) for x in order) + "];")
    idx_txt.append("UIStoryEntry = " + tjs_str(entry) + ";")
    idx_txt.append("UIStoryAssetRoot = %[ root: \"story_assets/\" ];")
    # 角色 → 立绘族/脸（跨场景聚合；TJS2 不用带引号键的内联字典，故用并行数组）
    rkeys, rfams, rfaces = [], [], []
    for role in sorted(role2fam.keys()):
        fam = role2fam[role]
        fn = face_file_for(fam, face_avail)
        rkeys.append(role); rfams.append(fam); rfaces.append(("face/" + fn) if fn else "")
    idx_txt.append("UIStoryRoleKeys  = [" + ",".join(tjs_str(k) for k in rkeys) + "];")
    idx_txt.append("UIStoryRoleFams  = [" + ",".join(tjs_str(k) for k in rfams) + "];")
    idx_txt.append("UIStoryRoleFaces = [" + ",".join(tjs_str(k) for k in rfaces) + "];")
    with open(os.path.join(story_dir, "_index.tjs"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(idx_txt) + "\n")

    # ★ ISSUE-20261004-12：**输出目录剪枝**——`story\scene_*.tjs` 以**本次生成集**（order）为唯一
    #   权威。只增不删会让上一轮（或去重前）的场景文件残留：实测 wt-prog 检出残留 4 个
    #   `otv_P03_*`（680≠676），并让审计脚本按磁盘存在性判"入构建"时漂移。story\ 是纯构建产物。
    _pruned = 0
    for _nm in sorted(os.listdir(story_dir)):
        _m = re.match(r"^scene_(.+)\.tjs$", _nm)
        if _m and _m.group(1) not in set(order):
            os.remove(os.path.join(story_dir, _nm))
            _pruned += 1
    if _pruned:
        print("[prune] story/ 剪掉上一轮陈旧场景文件 %d 件（以本次生成集为准）" % _pruned)

    print("[ok] 场景 %d / 台词 %d / 语音 %d / 背景 %d / 立绘 %d / 音效 %d / BGM %d" % (
        stats["scenes"], stats["lines"], stats["voice"], stats["bg"], stats["chr"],
        stats["se"], stats["bgm"]))
    print("[ok] story_assets 实文件 %d 件 ｜ 带 BGM 切换点场景 %d" % (len(copied), stats["scenes_with_cue"]))
    print("[skip] 演出层未取件（C6/R1 语义未逆向）：chr %d / movie %d" % (
        stats["chr_skip"], stats["movie_skip"]))
    if stats["diff_subst"]:
        # C16：逐条留痕（同一 引用 只记一次影响面）
        p_c16 = os.path.join(story_dir, "_c16_有差异替代.tsv")
        byref = {}
        for sid2, orp2, deliv2 in stats["diff_subst"]:
            byref.setdefault((orp2, deliv2), []).append(sid2)
        with open(p_c16, "w", encoding="utf-8", newline="\n") as f:
            f.write("引用\t交付路径\t影响场景数\t样例场景\t本次采用\n")
            for (orp2, deliv2), sids in sorted(byref.items()):
                f.write("%s\t%s\t%d\t%s\t%s\n" % (
                    orp2, deliv2, len(sids), sids[0],
                    "否(strict-c16)" if args.strict_c16 else "是(用户 2026-10-01 裁决：照现状)"))
        print("[C16] 「有差异替代」命中 %d 条引用 / %d 处场景引用 → %s"
              % (len(byref), len(stats["diff_subst"]), p_c16))
        if not args.strict_c16:
            print("[C16][warn] 已按用户裁决**采用**「有差异替代」交付件（契约要求裁决后使用；此处裁决＝照现状继续）")
    if stats["null_ref"]:
        print("[warn] out_relpath 为 null（按兜底跳过）%d 条：%s" % (len(stats["null_ref"]), stats["null_ref"][:5]))
    if stats["miss_art"]:
        print("[warn] 美术取件失败 %d 条（前 5）：%s" % (len(stats["miss_art"]), stats["miss_art"][:5]))
    if stats["disabled"]:
        print("[skip] 弃用件(C19) 跳过 %d 条：%s" % (len(stats["disabled"]), stats["disabled"][:5]))
    if stats["miss_media"]:
        print("[warn] 媒体取件失败 %d 条（前 5）：%s" % (len(stats["miss_media"]), stats["miss_media"][:5]))
    # 章节简介（C15）＋幕信息 → story/_intro.tjs（供流程图右栏/详情浮层取数）
    intro_txt, n_intro, n_acts = build_intro_table(proj, script_dir, scenes, ref_map, disabled,
                      lambda rel: take_asset("bg", rel, art_root)[0])
    with open(os.path.join(story_dir, "_intro.tjs"), "w", encoding="utf-8", newline=chr(10)) as f:
        f.write(intro_txt)
    print("[ok] 章节简介 %d 条（采用=是，按场景去重）/ 幕 %d 个 → story/_intro.tjs" % (n_intro, n_acts))
    mus_txt, n_mus, n_mus_ok = build_music_table(proj)
    with open(os.path.join(story_dir, "_music.tjs"), "w", encoding="utf-8", newline=chr(10)) as f:
        f.write(mus_txt)
    print("[ok] BGM 鉴赏曲目 %d 条（可播放 %d）→ story/_music.tjs" % (n_mus, n_mus_ok))
    # 章节过场卡插点（ISSUE-20261005-03）→ story/_eyecatch.tjs ＋ story_assets/ec__*
    # ★ 必须**在这里**生成：`run_storytest.py` 会先 `rmtree(krk/game/story)` 再重建 ⇒
    #   只手动跑一次生成器会被清掉（实测踩到）。缺源映射表时写空表，引擎侧过场退场。
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "emit_eyecatch",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_eyecatch.py"))
        _ee = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_ee)
        _ee.emit(story_dir, os.path.join(os.path.dirname(story_dir), "eyecatch"),
                 os.path.join(proj, "资源组"),
                 # ★ B3：插点表改由 PSV EyeCatch 生成（按 (场景,seq)）；只处理**本次构建集**的场。
                 #   `full=args.all`：剪枝 `ec__*` 只在**全量构建**才做（Minor-1 护栏）——
                 #   单场/子集切片若也剪，会把源树 `krkr\game\eyecatch\` 收窄到该切片。
                 psv_dir=os.path.join(proj, "编程组", "PSV演出"), scene_ids=set(order),
                 full=args.all,
                 # ⚠️ 插点表落**本脚本所在工程**（worktree），不落 `--data-root`——
                 #    重资产只从 data-root 读，产物/表一律写回本工作树（铁律 1）。
                 tsv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                       "章节过场卡插点.tsv"))
    except Exception as eEC:
        print("[warn] 章节过场卡表生成失败（不影响其余构建）：%s" % eEC)
        with open(os.path.join(story_dir, "_eyecatch.tjs"), "w", encoding="utf-8", newline=chr(10)) as f:
            f.write("function uiEyecatchFill(o)\n{\n\to.keys = []; o.seqs = []; o.imgs = []; o.ws = []; o.hs = [];\n\treturn 0;\n}\n")

    # Q 版人物池（ISSUE-20261005-06）→ game/eyecatch/chibi/（三槽预缩放件）＋ story/_eyecatch_chibi.tjs
    # ★ 与过场卡同链：run_storytest 会先 rmtree(story) 再重建 ⇒ 必须在此生成；
    #   提取约 2 分钟，emit_chibi 自带缓存（源/参数/工具未变则跳过）。失败只少 Q 版，不阻塞构建。
    try:
        import importlib.util as _ilc
        _specC = _ilc.spec_from_file_location(
            "emit_chibi",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_chibi.py"))
        _ecb = _ilc.module_from_spec(_specC)
        _specC.loader.exec_module(_ecb)
        _ecb.emit(os.path.join(os.path.dirname(story_dir), "eyecatch"), story_dir,
                  os.path.join(proj, "资源组"),
                  tsv_path=os.path.join(proj, "编程组", "Q版素材映射.tsv"))
    except Exception as eCB:
        print("[warn] Q 版素材生成失败（不影响其余构建）：%s" % eCB)
        with open(os.path.join(story_dir, "_eyecatch_chibi.tjs"), "w", encoding="utf-8", newline=chr(10)) as f:
            f.write("function uiEyecatchChibiFill(o)\n{\n\to.slots = []; o.files = []; o.rects = [];\n\treturn 0;\n}\n")

    # ---- 逐行演出（C21）总账 ----
    # ★ P0-D：自造重排改发 chr_place（瞬时落位）；chr_move 只剩源侧(otv)真移位。
    print("[stage] 注入逐行演出：立绘 op %d 条 / 逐行音效 %d 条（chr_remove %d / chr_move(源侧真移位) %d / chr_place(自造重排) %d）"
          % (gchrops[0], gseops[0], stats["stage_remove"], gmove[0], gplace[0]))
    # ★ op=other 控制串语义接入（层 2 · tier1，ISSUE-20261007-02）：off 时各项均为 0（零行为变化）。
    #   接入集（族身份表 ∩ 严格梯白名单）在启动时打印；此处为**处理计数**（仅本次构建的场景集）。
    print("[stage] op=other 语义接入(%s)：发出 %d 条 ｜ 7token 但白名单外(丢弃) %d 条 ｜ 白名单内但运行期取不到(丢弃) %d 条（不在场 %d / 无可绘槽 %d）｜ 非7token(保持丢弃) %d 条"
          % (args.other_semantics, stats["stage_other_mapped"], stats["stage_other_nofam"],
             stats["stage_other_dropped"], stats["stage_other_nostate"], stats["stage_other_noslot"],
             stats["stage_other_unmapped"]))
    # ★ B1（ISSUE-20261006-04）：背景层换源分账——覆盖场用 PSV SpriteBG，未覆盖场回落剔题卡。
    print("[stage] 背景层事件 %d 条（PSV 金标 %d / 回落 %d）｜ 覆盖场 %d（其中 PSV 无背景层 %d）/ 回落场 %d"
          % (gbgev[0], stats["bg_psv"], stats["bg_fallback"],
             stats["bg_covered_scenes"], stats["bg_covered_empty"], stats["bg_fallback_scenes"]))
    print("[stage] 背景排除/登记：题卡 ec## 剔除 %d 条 ｜ PSV 叠加层 SpriteBS/Sprite 仅登记 %d 条 ｜ "
          "PSV 缺件(status=missing) %d 条 ｜ PSV sub-diff 采用 %d 条"
          % (stats["bg_ec_dropped"], stats["bg_psv_overlay_skipped"],
             stats["bg_psv_missing"], stats["bg_psv_subdiff"]))
    print("[stage] 过滤 chr_* 非角色族(cin/f_mis/cit/pon/unparsed) %d 条 ｜ 不再当 bg 候选的图像 %d 个"
          % (gfiltered[0], stats.get("art_ignore", 0)))
    print("[stage] 取件失败：chr %d 条 / se %d 条 / bg %d 条（对不上账，已跳过不崩）"
          % (stats["stage_chr_missing"], stats["stage_se_missing"], stats.get("bg_missing", 0)))
    # ★ 立绘摆位自检（可失败）：布局后相邻**重叠对数必须为 0**；tight＝理想排法放不下的场景数（走等距铺开）
    print("[stage] 立绘布局：基准缩放×%.2f（保底 %.2f，可见集下限 %.2f）｜ 相邻重叠对 %d（须为 0）｜ 自适应降缩放的场景 %d 个 ｜ 最小有效缩放×%.3f"
          % (STAGE_CHR_SCALE, STAGE_CHR_SCALE_FLOOR, STAGE_CHR_MIN_VIS, stats.get("stage_overlap", 0),
             stats.get("stage_tight", 0), stats.get("stage_scale_min", STAGE_CHR_SCALE)))
    # ★ 可见集上限（ISSUE-20261003-05）总账：源侧「整场一次性上场」的场景，落选族不绘制
    if stats.get("stage_drop_scenes"):
        _w = stats.get("stage_drop_worst", [])
        print("[stage] 可见集上限：%d 个场景收窄（共不绘制 %d 族）｜ 收窄最多的：%s%s"
              % (stats["stage_drop_scenes"], stats.get("stage_dropped", 0),
                 "、".join(sorted(_w, key=lambda s: -int(s.split()[-1].split("→")[0]))[:5]),
                 " …" if len(_w) > 5 else ""))

    # ---- 16:9 覆盖层（ISSUE-20261003-02）总账 ----
    #   ★ 判据：`覆盖表 46 条` 且 `命中 > 0`。命中 0 说明键格式或路径口径变了（须查，不是"没影响"）。
    _ov_hit = stats.get("ov16x9_hit", 0)
    print("[ov16x9] 覆盖表 %d 条（资源组 `美术统一_交付_16比9\\交付清单.tsv`）｜ 本次命中取件 %d 次%s"
          % (len(ov16x9), _ov_hit,
             "" if (len(ov16x9) == 0 or _ov_hit > 0) else "  ← ⚠️ 表非空但零命中，键口径可能已变"))

    # ---- 选择支配位（ISSUE-20261003-03）总账 + 全量回执 ----
    #   ⚠️ 判据：**未解析（留空）项必须为 0**——非 0 意味着有场景的选择肢不会展开（源侧是分支，玩家却看不到）。
    _clp = os.path.join(story_dir, "选择支配对说明.tsv")
    with open(_clp, "w", encoding="utf-8", newline=chr(10)) as f:
        f.write("scene_id\t项序\t文本\t目标\t依据\n")
        for r in choice_log:
            f.write("\t".join("" if x is None else str(x) for x in r) + "\n")
    _nch = len(choice_log)
    print("[choice] 选择支 %d 项 → story/选择支配对说明.tsv ｜ 未解析（留空）场景 %d 个（须为 0）"
          " ｜ 判为「标签非选项」移除 %d 项 ｜ 兜底到首个出口 %d 个场景"
          % (_nch, stats.get("choice_missing", 0), stats.get("choice_label_dropped", 0),
             stats.get("choice_fallback", 0)))
    if stats.get("choice_next_unused"):
        _u = stats["choice_next_unused"]
        print("[choice] 未被任何选项指向的出口 %d 个（触发条件未确证，登记待裁决）：%s%s"
              % (len(_u), "、".join(_u[:8]), " …" if len(_u) > 8 else ""))

    print("[ok] 入口 = %s ；顺序 = %s" % (entry, order))

    # ★ 流程图「全量节点几何」（ISSUE-20261003-14）：**随构建一起产出**。
    #   为什么必须在这里做：`run_storytest.py` 会先 `rmtree(krk/game/story)` 再重建，
    #   若几何只由独立工具 `emit_flow_geometry.py` 生成，**每次自测/重建后它就没了**
    #   ——挂屏的自绘会因此画 0 个节点（本轮实测）。
    #   失败不致命：只告警，不影响剧本产出。
    #   ⚠️ 输出**必须跟 `--out` 走，不能跟 `--data-root` 走**（ISSUE-20261003-18 一审打回项）：
    #      `proj` 是用 `--data-root` 拼出来的（＝**主工作区**），而剧本写的是 `--out`（＝本 checkout）。
    #      若把几何按 `proj` 落盘，几何会写进**主工作区**、本次 checkout 的 `story\` 反而没有它
    #      ⇒ `--skip-build` 的机检会拿上一轮遗留的几何"通过"，且跨 worktree 互相污染。
    #      正解＝与剧本同目录（`game\story\`）。
    try:
        import subprocess, sys as _sys
        _eg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_flow_geometry.py")
        _geom_out = os.path.join(game, "story", "_flowgeom.tjs")
        _r = subprocess.run([_sys.executable, "-X", "utf8", _eg, "--proj", proj, "--out", _geom_out],
                            capture_output=True, text=True, encoding="utf-8")
        if _r.returncode == 0:
            for _ln in (_r.stdout or "").splitlines():
                print("[flowgeom] " + _ln)
        else:
            print("[warn] 流程图几何生成失败（不影响剧本）：" + ((_r.stderr or "").strip()[-200:]))
    except Exception as _e:
        print("[warn] 流程图几何生成异常（不影响剧本）：%s" % _e)

    # ★★ 流程图「分页几何」（ISSUE-20261004-03）：**随构建一起产出**（与上面同因：重建后不能丢）。
    #    产出的 `story/_flowpages.tjs` 才是渲染器的**首选**几何；上面那份扁平 `_flowgeom.tjs` 只作兜底
    #    （它带 UI 组 `full` 预设的 48 处同坐标叠字）。落点同样**跟 `--out` 走**，且生成器自身
    #    会跑一遍版式体检（同坐标必须为 0、跨页锚点必须 12）——非 0 退出即版式没过，此处只告警。
    try:
        import subprocess, sys as _sys2
        _ep = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emit_flow_pages.py")
        _page_out = os.path.join(game, "story", "_flowpages.tjs")
        _r2 = subprocess.run([_sys2.executable, "-X", "utf8", _ep, "--proj", proj, "--out", _page_out],
                             capture_output=True, text=True, encoding="utf-8")
        for _ln in ((_r2.stdout or "").strip().splitlines() or []):
            print("[flowpage] " + _ln)
        if _r2.returncode != 0:
            print("[warn] 分页几何生成**非 0 退出**（%d）——版式体检没过或源缺失，详见上方输出"
                  % _r2.returncode)
    except Exception as _e2:
        print("[warn] 分页几何生成异常（不影响剧本）：%s" % _e2)


if __name__ == "__main__":
    main()
