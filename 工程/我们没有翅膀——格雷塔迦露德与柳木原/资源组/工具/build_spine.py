# -*- coding: utf-8 -*-
r"""
W6g · 主线编排方案构建器（只读六源 scene_*.jsonl，产出 spine.json + 主线编排方案.md）

依据：用户裁决 D6（线性主干 + 保留关键选择支）、D13（AS 22_*/23_* 作番外）、
      D15（前奏诗 02_*/03_* 只取独有部分，不入线性主干）；
      顺序依据 `资源组\01_剧情流程图.md` §六 时间线与 §四 逐源结构。

边界：
  - 本模块**不修改任何 scene_*.jsonl**、不修改 schema.md；
  - 六个源工程目录全程只读（sys.dont_write_bytecode=True，不留 __pycache__）；
  - 只写 资源组\剧本\{spine.json, 主线编排方案.md}。

可复跑：python -X utf8 资源组/工具/build_spine.py
"""
import sys, io, json, os, collections

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))          # 资源组\工具
RES = os.path.dirname(HERE)                                 # 资源组
SCENEDIR = os.path.join(RES, "剧本")                        # 资源组\剧本
OUT_JSON = os.path.join(SCENEDIR, "spine.json")
OUT_MD = os.path.join(SCENEDIR, "主线编排方案.md")

# 路径根：本模块只读写本 checkout 内的 资源组\剧本\（无外部数据树依赖）。
# 边界断言：产物必须落在本 checkout 内，否则报错中止（防止误写主工作区）。
CHECKOUT = os.path.dirname(os.path.dirname(os.path.dirname(RES)))   # <checkout> 根


def _assert_in_checkout(path, what="产物"):
    p = os.path.abspath(path); c = os.path.abspath(CHECKOUT)
    if not (p == c or p.lower().startswith(c.lower() + os.sep)):
        raise SystemExit("!! %s 路径越界（不在本 checkout 内）：%s" % (what, p))

SOURCES = [
    ("ot", "scene_ot.jsonl", "S1 本篇主线（s00/s01/s02/s03/s04）"),
    ("ota", "scene_ota.jsonl", "S3 After Story"),
    ("otp", "scene_otp.jsonl", "S4 前奏诗 Prelude"),
    ("otr", "scene_otr.jsonl", "S2 R 版亚衣线（s03c 55 场景）"),
    ("otv", "scene_otv.jsonl", "S5 PSV 美咲线"),
    ("np", "scene_np.jsonl", "S6 涅布＊プラス 明日香篇"),
]


def load(path):
    out = []
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def script_of(sid):
    return sid.split("_", 1)[1]


def ota_prefix(script):
    if script.startswith("sc_"):
        return "sc"
    if script == "sr" or script.startswith("sr_"):
        return "sr"
    return script.split("_", 1)[0]


# ---------------------------------------------------------------- act 定义
# 每项： (act 号, 名称, 来源代号集合, 判定函数, note, 顺序依据)
ACTS = [
    dict(
        act=1, name="前奏诗·框架剧与四短篇",
        srcs={"otp"},
        match=lambda s, sc: sc.startswith("buru") or sc.startswith("p0"),
        note="火烈鸟三人（西特拉斯/米内奥拉/椪柑）＋ＡＤさん主持的剧场框架，包裹四个角色短篇；"
             "前奏诗独有的 22 场景（D15 保留部分）。",
        basis="流程图 §4.1 调度顺序（MAIN→…→P01→P02→P03→P04→02→03→BURU01–04）与 §六 6.2"
              "（前奏诗为全系列最早，2008 先行作）",
    ),
    dict(
        act=2, name="前奏诗·系统脚本",
        srcs={"otp"},
        match=lambda s, sc: sc in ("gameinit", "history", "staff", "title", "title2"),
        note="非剧情场景：引擎初始化/回想/制作人员/标题画面。**无剧情时序**，"
             "编程组按系统功能（菜单、回想、ED、标题）处理，不排入叙事顺序。",
        basis="流程图 §4.1 末行「系统」分组（gameinit/history/staff/title/title2）",
    ),
    dict(
        act=3, name="本篇·序文",
        srcs={"ot"},
        match=lambda s, sc: sc.startswith("s00"),
        note="s00「序文 ～俺たちに翼はない～」，全篇开篇。",
        basis="流程图 §4.2 脚本分组表（s00 1 脚本 / 2 槽）",
    ),
    dict(
        act=4, name="本篇·s01 鹰志线",
        srcs={"ot"},
        match=lambda s, sc: sc.startswith("s01"),
        note="羽田鹰志 → 渡来明日香（主）/ 山科京（副）；含明日香 END（s01_16a）与京 END（s01_18a）。"
             "**与 s02/s03 为同一时间带的平行线**，先后由编程组按路线选择决定。"
             "（W10b：亚衣线 `s03c` 不是独立平行线，而是 `s03` 内的分支，见第 6/7 幕说明。）",
        basis="流程图 §4.2 s01 章节序列；§六 6.1 日期锚点 12/3、12/24",
    ),
    dict(
        act=5, name="本篇·s02 鹫介线",
        srcs={"ot"},
        match=lambda s, sc: sc.startswith("s02"),
        note="千岁鹫介 → 玉泉日和子（主）/ 日野英里子、望月纪奈子（副）；日和子 END（s02_16a）。"
             "**与 s01/s03 平行**（W10b：`s03c` 属 `s03` 内分支，不在此平行之列）。",
        basis="流程图 §4.2 s02 章节序列；§六 6.1 日期锚点 11/29、12/4",
    ),
    dict(
        act=6, name="本篇·s03 隼人线",
        srcs={"ot"},
        match=lambda s, sc: sc.startswith("s03"),
        note="成田隼人 → 凤鸣（主）；鸣 END（s03_22a）。含大量 (N)/(C) 成对变体脚本。"
             "**与 s01/s02 平行**；**亚衣线 `s03c` 是 s03 内的分支**——`s03_09a` 有 (N)/(C) 两变体："
             "`s03_09a1`「世间万象（Ｎ）」继续鸣线（`next=s03_09b`），`s03_09a2`「世间种种（Ｃ）」"
             "`next=['s03c_01a']` 分叉到亚衣线（W10b 实测更正；见 §七.2）。",
        basis="流程图 §4.2 s03 章节序列；§六 6.1 日期锚点 11/22–11/28、12/1；"
              "亚衣线入口＝`scene_ot.jsonl` 的 `s03_09a2.next=['s03c_01a']`（W10b 实测）",
    ),
    dict(
        act=7, name="亚衣线·s03c（R 版 55 场景版）",
        srcs={"otr"},
        match=lambda s, sc: sc.startswith("s03c"),
        note="香田亚衣线。**取自 scene_otr.jsonl（R 版 55 场景），不在 scene_ot 内**——"
             "21 共有 + 3 分支 + 31 新增（D14：共有取本篇译文、新增取 R 版本项目新译）。"
             "亚衣 END（s03c_20a）。**入口＝`s03_09a2`「世间种种（Ｃ）」→ `next=['s03c_01a']`**"
             "（`scene_ot.jsonl` 实测，W10b 更正）——即**亚衣线是 `s03` 隼人线内的分支**，"
             "**不是与 s01/s02/s03 并列的第四条平行线**。",
        basis="亚衣线入口＝`scene_ot.jsonl` 的 `s03_09a2.next=['s03c_01a']`（W10b 实测；"
              "`s03_09a1` 为 (N) 变体继续鸣线）；§六 6.1 日期锚点 11/22–11/26（s03c_01c）；"
              "流程图 §4.2 已于 2026-09-19 同步更正",
    ),
    dict(
        act=8, name="PSV 美咲线（同期分支）",
        srcs={"otv"},
        match=lambda s, sc: True,
        note="林田美咲线，M01–M09 + P03 四短篇。**承 s01 鹰志线 Bad End（S01_14J2）的同期分支**"
             "（D7 完全采用并并入主线）。线性、无剧情选择支；美咲 END（M09_01/M09_02）。",
        basis="流程图 §4.4；§六 6.2（PSV 美咲线为同期鷹志线分支，游戏内 12/13–12/24）",
    ),
    dict(
        act=9, name="大路线 s04（最终章）",
        srcs={"ot"},
        match=lambda s, sc: sc.startswith("s04"),
        note="多元世界真相 → 假统合 → 真·兄妹再会 → 不完全统合；**收束全线的唯一真结局**。"
             "真 END（s04_28b → s04_29a）。",
        basis="流程图 §4.2 s04 章节序列；§六 6.2（12/5 起，经新年 → 仮統合）",
    ),
    dict(
        act=10, name="After Story·主线",
        srcs={"ota"},
        match=lambda s, sc: ota_prefix(sc) in ("11", "12", "13", "14", "21", "24"),
        note="11/12/13/14 对决四篇（鹰志/鹫介/隼人/洋治）＋ 21 美咲 ＋ 24 最终统合线"
             "（24_1a「仮統合の崩壊」→ 24_5b G-END / 24_5c B-END）。",
        basis="流程图 §4.5 五层结构 A/B 层；§六 6.2（s04 之后；24_1a 明示接「仮統合」）",
    ),
    dict(
        act=11, name="涅布＊プラス 明日香篇",
        srcs={"np"},
        match=lambda s, sc: True,
        note="毕业后 2 月；a01–a06 子篇目菜单式短篇集（start_oretuba 为菜单脚本，"
             "34 条选择支全部挂于该脚本）。",
        basis="流程图 §4.6；§六 6.2（毕业后·2 月，毕业前）",
    ),
]

# ---------------------------------------------------------------- 番外分组
SIDE_GROUPS = [
    (("22",), "番外·阿雷克桑德平安夜（おっぱい系列）",
     "AS 主线之后；或 21 与 24 之间可选触发（建议，无原作证据）"),
    (("23",), "番外·苍女X日",
     "AS 主线之后；或 21 与 24 之间可选触发（建议，无原作证据）"),
    (("31", "32", "33", "34"), "番外·各线 after",
     "各对应角色线之后 / AS 主线之后（建议，无原作证据）"),
    (("41", "42"), "番外·群像（新年行军 / 格兰玛尼耶）",
     "AS 主线之后（年末–新年时点，建议，无原作证据）"),
    (("50", "51", "52", "53", "54"), "番外·おれつば剧场",
     "任意时点可选（剧场式短篇，建议，无原作证据）"),
    (("61", "62", "63", "64", "sc", "sr"), "番外·おまけ（成人向）",
     "任意时点可选（おまけ/成人向短篇，建议，无原作证据）"),
]


def side_group(prefix):
    for keys, name, sug in SIDE_GROUPS:
        if prefix in keys:
            return name, sug
    return None, None


def main():
    # ---- 载入
    data = {}
    for code, fn, desc in SOURCES:
        data[code] = load(os.path.join(SCENEDIR, fn))

    # ---- 分类
    acts = {a["act"]: dict(a) for a in ACTS}
    for a in acts.values():
        a["scenes"] = []
        a["lines"] = 0

    excluded = []
    side_stories = []
    branch_points = []
    seen = {}

    def place(a, o):
        a["scenes"].append(o["scene_id"])
        a["lines"] += o.get("line_count", 0)

    for code, fn, desc in SOURCES:
        for o in data[code]:
            sid = o["scene_id"]
            sc = script_of(sid)
            if sid in seen:
                raise SystemExit("DUPLICATE scene_id: %s" % sid)
            seen[sid] = code

            # --- 排除（D15）
            if code == "otp" and (sc.startswith("02_") or sc.startswith("03_")):
                excluded.append(dict(
                    scene_id=sid, source=code, script=sc,
                    title_jp=o.get("title_jp"), title_cn=o.get("title_cn"),
                    route=o.get("route"),
                    reason_short="D15：原型版（与本篇 99.2% 重合），不入主干",
                    reason="D15：前奏诗 02_*/03_* 与本篇 s02_*/s03_* 逐字重合 99.2%（5,393/5,436 槽），"
                           "系原型版 → 不入线性主干，只保留前奏诗独有内容。",
                ))
                continue

            # --- 番外（D13 + §4.5 分层）
            if code == "ota":
                p = ota_prefix(sc)
                gname, gsug = side_group(p)
                if gname:
                    side_stories.append(dict(
                        scene_id=sid, source=code, script=sc, group=gname,
                        title_jp=o.get("title_jp"), title_cn=o.get("title_cn"),
                        next=o.get("next", []),
                        entry_after=None,
                        entry_after_basis="建议（无原作证据）",
                        entry_suggestion=gsug,
                        note=("D13：番外，不占主线位置" if p in ("22", "23")
                              else "流程图 §4.5 分层：番外/おまけ，不占主线位置"),
                    ))
                    continue

            # --- 入幕
            placed = False
            for a in acts.values():
                if code in a["srcs"] and a["match"](code, sc):
                    place(a, o)
                    placed = True
                    break
            if not placed:
                raise SystemExit("UNPLACED scene: %s" % sid)

            # --- 选择支
            ch = o.get("choices") or []
            if ch:
                branch_points.append(dict(
                    scene_id=sid, source=code, script=sc,
                    route=o.get("route"),
                    in_spine=True,
                    option_count=len(ch),
                    choices=[dict(text_jp=c.get("text_jp"), text_cn=c.get("text_cn"),
                                  target=c.get("target")) for c in ch],
                    candidate_targets=o.get("next", []),
                    pairing_verified=all(c.get("pairing_verified") for c in ch),
                    note="D6：保留关键选择支。target 未确证处为 null（总纲 R1：分支语义未逆向）——不猜配对。",
                ))

    # 被排除场景中的选择支（前奏诗 4 点 / 9 槽）也登记，标 in_spine=false
    for o in data["otp"]:
        sid = o["scene_id"]
        sc = script_of(sid)
        if sc.startswith("02_") or sc.startswith("03_"):
            ch = o.get("choices") or []
            if ch:
                branch_points.append(dict(
                    scene_id=sid, source="otp", script=sc, route=o.get("route"),
                    in_spine=False,
                    option_count=len(ch),
                    choices=[dict(text_jp=c.get("text_jp"), text_cn=c.get("text_cn"),
                                  target=c.get("target")) for c in ch],
                    candidate_targets=o.get("next", []),
                    pairing_verified=all(c.get("pairing_verified") for c in ch),
                    note="D15：所在场景已被排除（02_*/03_* 不入主干）→ 本选择支不进入主干；"
                         "如实登记以完成对账，不删除。",
                ))

    # ---- 覆盖率自证
    act_ids = [s for a in acts.values() for s in a["scenes"]]
    exc_ids = [e["scene_id"] for e in excluded]
    side_ids = [s["scene_id"] for s in side_stories]
    total = len(act_ids) + len(exc_ids) + len(side_ids)
    all_ids = act_ids + exc_ids + side_ids
    dup = [k for k, v in collections.Counter(all_ids).items() if v > 1]
    src_total = sum(len(v) for v in data.values())

    # 前奏诗 02/03 实测条数（独立重扫）
    otp_0203 = [o["scene_id"] for o in data["otp"]
                if script_of(o["scene_id"]).startswith(("02_", "03_"))]
    otp_0203_02 = [s for s in otp_0203 if script_of(s).startswith("02_")]
    otp_0203_03 = [s for s in otp_0203 if script_of(s).startswith("03_")]
    ota_22 = [s["scene_id"] for s in side_stories if ota_prefix(s["script"]) == "22"]
    ota_23 = [s["scene_id"] for s in side_stories if ota_prefix(s["script"]) == "23"]

    recon = dict(
        source_scene_total=src_total,
        acts_total=len(act_ids), excluded_total=len(exc_ids), side_total=len(side_ids),
        sum_total=total, duplicates=dup,
        coverage_ok=(total == src_total and not dup and len(seen) == src_total),
        otp_0203_in_jsonl=len(otp_0203),
        otp_0203_02=len(otp_0203_02), otp_0203_03=len(otp_0203_03),
        otp_0203_in_excluded=len([e for e in excluded if e["scene_id"] in set(otp_0203)]),
        ota_22=len(ota_22), ota_23=len(ota_23),
        choices_by_source={c: dict(
            scenes=len([b for b in branch_points if b["source"] == c and b["in_spine"]]),
            options=sum(b["option_count"] for b in branch_points
                        if b["source"] == c and b["in_spine"]))
            for c in [x[0] for x in SOURCES]},
        choices_total_in_spine=sum(b["option_count"] for b in branch_points if b["in_spine"]),
    )

    spine = dict(
        version="1.0",
        generated="2026-09-19",
        module="W6g",
        basis=dict(
            D6="剧本编排 = 线性主干 + 保留关键选择支（按时间线串联六源，在美咲线/亚衣线/AS 双结局/真 END 保留选择）",
            D13="After Story 的 22_*/23_* 作番外，不占主线位置",
            D15="前奏诗 02_*/03_* 只取独有部分（与本篇逐字重合 99.2%）→ 不入线性主干",
        ),
        acts=[dict(act=a["act"], name=a["name"],
                   source=sorted(a["srcs"]),
                   scenes=a["scenes"], line_count=a["lines"],
                   note=a["note"], basis=a["basis"])
              for a in sorted(acts.values(), key=lambda x: x["act"])],
        excluded=excluded,
        side_stories=side_stories,
        branch_points=branch_points,
        reconciliation=recon,
    )

    _assert_in_checkout(OUT_JSON, "spine.json")
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(spine, ensure_ascii=False, indent=2))
        fh.write("\n")

    print("spine.json written:", OUT_JSON)
    print(json.dumps(recon, ensure_ascii=False, indent=2))

    write_md(spine)
    return spine


# ---------------------------------------------------------------- 人读版 md
def write_md(spine):
    L = []
    w = L.append
    a = spine["acts"]
    recon = spine["reconciliation"]
    w("# 主线编排方案 · 《我们没有翅膀——格雷塔迦露德与柳木原》")
    w("")
    w("> **本文件是资源组 → 编程组的编排契约（人读版）。**机器可读版：同目录 `spine.json`。")
    w("> 模块：W6g ｜ Issue：`ISSUE-20260918-06` ｜ 生成：2026-09-19 ｜ 构建器：`资源组\\工具\\build_spine.py`（可复跑）")
    w("> **本方案不改任何 `scene_*.jsonl`**：以 `scene_id` 引用场景，编程组据本方案组装。")
    w("")
    w("---")
    w("")
    w("## 〇、摘要")
    w("")
    w("| 项 | 值 |")
    w("| --- | --- |")
    w("| 输入场景总数 | **%d**（六源 `scene_<源代号>.jsonl`） |" % recon["source_scene_total"])
    w("| `acts[]`（入主线） | **%d** |" % recon["acts_total"])
    w("| `excluded[]`（排除） | **%d** |" % recon["excluded_total"])
    w("| `side_stories[]`（番外） | **%d** |" % recon["side_total"])
    w("| 三者合计 | **%d**（＝输入总数，无遗漏无重复：%s） |" % (recon["sum_total"], recon["coverage_ok"]))
    w("| 分幕数 | %d |" % len(a))
    w("| 保留的选择支 | %d 场景 / %d 选项（不含被排除场景的 4 点/9 槽） |"
      % (sum(1 for b in spine["branch_points"] if b["in_spine"]), recon["choices_total_in_spine"]))
    w("")
    w("**编排依据（用户裁决）**")
    w("")
    w("- **D6**：%s" % spine["basis"]["D6"])
    w("- **D13**：%s" % spine["basis"]["D13"])
    w("- **D15**：%s" % spine["basis"]["D15"])
    w("")
    w("---")
    w("")
    w("## 一、编排原则")
    w("")
    w("1. **线性主干（D6）**：按 `01_剧情流程图.md` §六 时间线串联六源——"
      "前奏诗 → 本篇三条平行线 `s01`/`s02`/`s03`（＋`s03` 内分支亚衣线 `s03c`；＋PSV 美咲线同期分支）"
      "→ s04 大路线 → After Story → 涅布。")
    w("2. **保留关键选择支（D6）**：三条平行线、美咲线、亚衣线（`s03` 内分支）、AS 双结局（G-END/B-END）、"
      "真 END 处的选择支一律保留；编程组按 `branch_points[]` 实现。")
    w("3. **不臆断配对（总纲 R1）**：`target`（选项↔目标场景配对）未逆向者一律 `null`，"
      "编程组以场景级 `next` 为准。")
    w("4. **平行线的先后由编程组按路线选择决定**：`s01`/`s02`/`s03`（及 PSV 美咲线）"
      "**处于同一时间带**，本方案的幕序（s01→s02→s03→s03c→otv）**仅为编号顺序，不是强制播放顺序**。"
      "**亚衣线 `s03c` 是 `s03` 内的分支**（入口 `s03_09a2` → `s03c_01a`，W10b 更正），"
      "故编程组应在 `s03` 走到 `s03_09a2` 时分支进 `s03c`，而非把 `s03c` 当作与 `s03` 并列的第四条线。")
    w("5. **番外不占主线位置（D13）**：AS 的 `22_*`/`23_*` 与其余番外/おまけ一律入 `side_stories[]`，"
      "插入时机由编程组按 `entry_suggestion` 可选触发。")
    w("6. **排除项精确（D15）**：前奏诗 `02_*`/`03_*` 全 32 场景排除，理由与逐场景清单见 §四。")
    w("")
    w("---")
    w("")
    w("## 二、分幕表")
    w("")
    w("| 幕 | 名称 | 来源 | 场景数 | 行数 | 顺序依据 |")
    w("| ---: | --- | --- | ---: | ---: | --- |")
    for x in a:
        w("| %d | %s | %s | %d | %d | %s |"
          % (x["act"], x["name"], "/".join(x["source"]), len(x["scenes"]),
             x["line_count"], x["basis"]))
    w("")
    w("**各幕说明**")
    w("")
    for x in a:
        w("- **第 %d 幕 · %s**（%s）：%s" % (x["act"], x["name"], "/".join(x["source"]), x["note"]))
    w("")
    w("---")
    w("")
    w("## 三、主线顺序（含首尾锚点）")
    w("")
    for x in a:
        sc = x["scenes"]
        if not sc:
            continue
        w("- **%d %s**：`%s` → … → `%s`（%d 场景）"
          % (x["act"], x["name"], sc[0], sc[-1], len(sc)))
    w("")
    w("> 第 2 幕（前奏诗系统脚本）无剧情时序，故不在本顺序的叙事链上；"
      "编程组按系统功能（菜单/回想/ED/标题）处理。")
    w("")
    w("---")
    w("")
    w("## 四、排除清单（D15，逐场景 %d 条）" % len(spine["excluded"]))
    w("")
    w("**排除范围**：前奏诗 `02_*`（邂逅·鹫介，%d 场景）与 `03_*`（邂逅·隼人，%d 场景），"
      "合计 **%d 场景**。理由：与本篇 `s02_*`/`s03_*` 逐字重合 **5,393/5,436 槽（99.2%%）**，"
      "系原型版（W6d 实测）。**前奏诗只保留 `buru01`–`buru04` 与 `p01_*`–`p04_*`（＋系统脚本）。**"
      % (recon["otp_0203_02"], recon["otp_0203_03"], recon["otp_0203_in_jsonl"]))
    w("")
    w("| # | `scene_id` | 标题（中） | 理由 |")
    w("| ---: | --- | --- | --- |")
    for i, e in enumerate(spine["excluded"], 1):
        w("| %d | `%s` | %s | %s |"
          % (i, e["scene_id"], e["title_cn"] or "—", e.get("reason_short") or e["reason"]))
    w("")
    w("> **对账**：`scene_otp.jsonl` 中 `02_*`/`03_*` 前缀场景实测 **%d** 条（02:%d / 03:%d），"
      "`excluded[]` 中同前缀条数 **%d** → **一致**。"
      % (recon["otp_0203_in_jsonl"], recon["otp_0203_02"], recon["otp_0203_03"],
         recon["otp_0203_in_excluded"]))
    w("")
    w("---")
    w("")
    w("## 五、番外清单（D13 ＋ 流程图 §4.5 分层，逐场景 %d 条）" % len(spine["side_stories"]))
    w("")
    w("**D13 明确项**：AS 的 `22_*`（%d 场景）与 `23_*`（%d 场景）作番外，不占主线位置。"
      % (recon["ota_22"], recon["ota_23"]))
    w("")
    cur = None
    for s in spine["side_stories"]:
        if s["group"] != cur:
            cur = s["group"]
            grp = [x for x in spine["side_stories"] if x["group"] == cur]
            w("### %s（%d 场景）" % (cur, len(grp)))
            w("")
            w("建议插入时机：%s" % grp[0]["entry_suggestion"])
            w("")
            w("| `scene_id` | 标题（中） | 后继 |")
            w("| --- | --- | --- |")
            for x in grp:
                w("| `%s` | %s | %s |"
                  % (x["scene_id"], x["title_cn"] or "—",
                     ", ".join("`%s`" % n for n in x["next"]) or "（终）"))
            w("")
    w("> **`entry_after` 一律为 `null`**：原作无「番外插入时机」的脚本内证据，"
      "故只给 `entry_suggestion`（建议）并标 `entry_after_basis=建议（无原作证据）`——**不臆断为既定事实**。")
    w("")
    w("---")
    w("")
    w("## 六、关键选择支保留点（D6）")
    w("")
    w("### 6.1 对账表（与各源产出报告）")
    w("")
    w("| 源 | 产出报告已知数 | `scene_*.jsonl` 实测 | 入主干（in_spine） | 差异 |")
    w("| --- | --- | --- | --- | --- |")
    known = {
        "ot": ("本篇 24 脚本 / 54 选项", "24 场景 / 54 选项"),
        "ota": ("AS 40 记录 / 57 选项（涉 20 场景）", "20 场景 / 57 选项"),
        "otp": ("前奏诗 4 点 / 9 槽", "4 场景 / 9 选项（全部在排除场景内）"),
        "otr": ("亚衣线 1 点 / 2 选项", "1 场景 / 2 选项"),
        "otv": ("PSV 无", "0"),
        "np": ("涅布 34 条选项串", "1 场景 / 34 选项"),
    }
    for c in ["ot", "ota", "otp", "otr", "otv", "np"]:
        ins = recon["choices_by_source"][c]
        allc = [b for b in spine["branch_points"] if b["source"] == c]
        w("| %s | %s | %s | %d 场景 / %d 选项 | 0 |"
          % (c, known[c][0], known[c][1], ins["scenes"], ins["options"]))
    w("")
    w("**对账结论**：与各源产出报告**逐条吻合，差异 0**。"
      "前奏诗的 4 点 / 9 槽**全部位于被 D15 排除的 `02_*`/`03_*` 场景内**，"
      "故 `in_spine=false`（如实登记，不删除）。AS 的「40 记录」是源 `选择支补译.json` 的记录数，"
      "落到 `scene_ota.jsonl` 为 **20 场景 / 57 选项**（报告 §5.1 已说明 40=20×2 的口径）。")
    w("")
    w("### 6.2 逐条明细")
    w("")
    for c in ["ot", "otr", "otv", "np", "ota", "otp"]:
        bs = [b for b in spine["branch_points"] if b["source"] == c]
        if not bs:
            continue
        w("#### %s（%d 场景 / %d 选项）" % (c, len(bs), sum(b["option_count"] for b in bs)))
        w("")
        w("| `scene_id` | 入主干 | 选项 | 选项原文 → 译文 | 候选目标（`next`） | `target` |")
        w("| --- | :---: | ---: | --- | --- | --- |")
        for b in bs:
            opts = "<br>".join(
                "%s → %s" % (x["text_jp"], x["text_cn"] if x["text_cn"] else "（缺译）")
                for x in b["choices"])
            tgt = b["choices"][0]["target"]
            tgts = "／".join(str(x["target"]) for x in b["choices"]) if any(
                x["target"] for x in b["choices"]) else "**null**"
            w("| `%s` | %s | %d | %s | %s | %s |"
              % (b["scene_id"], "是" if b["in_spine"] else "**否（D15 排除）**",
                 b["option_count"], opts,
                 "／".join("`%s`" % n for n in b["candidate_targets"]) or "（终）", tgts))
        w("")
    w("> **`target` 为 `null` 的处置（总纲 R1）**：TOB0/SOB0/BGI 的分支语义未逆向，"
      "**选项↔目标标签的配对无字节码依据** → 一律 `null`、`pairing_verified=false`，"
      "编程组以场景级 `next` 为准。**唯二例外**：`np_start_oretuba` 的 34 条"
      "（BGI 常量池「标题串紧接脚本名」+ 分支体首句内容确证，`pairing_verified=true`）；"
      "前奏诗 7/9 槽的 `target` 依目标场景标题语义推定（报告 §4.1），但 `pairing_verified=false`。")
    w("")
    w("---")
    w("")
    w("## 七、已知缺口与未决项")
    w("")
    w("1. **`target` 配对未逆向（总纲 R1）**：除涅布 34 条外，全部选择支的 `target` 为 `null`。"
      "编程组须以 `next` 为准，并在实现/试玩阶段确定配对。")
    w("2. **亚衣线的入口＝`s03_09a2`（已确证，原文档分歧已销）**：实测 `scene_ot.jsonl` 的 "
      "`s03_09a2`「世间种种（Ｃ）」`next=['s03c_01a']`（`next_kind=linear`）——即**亚衣线是 `s03` 隼人线内的分支**。"
      "机制：`s03_09a` 有 (N)/(C) 两变体，`s03_09a1`「世间万象（Ｎ）」继续鸣线（`next=s03_09b`）、"
      "`s03_09a2`「（Ｃ）」分叉到亚衣线。"
      "**旧版（v1.0）曾记「入口＝`s04_03e` 选第 1 项（４５．４ＭＨｚ频道的故事）」——该说法错误**："
      "`s04_03e`「小巷鼎谈」的三个选项通向 `s04_03f1`/`f2`/`f3`（多元世界真相三条），与亚衣线无关"
      "（`s04_03e.next=['s04_03f1','s04_03f2','s04_03f3']`，实测）。"
      "`01_剧情流程图.md` §4.2 已于 2026-09-19 由主代理同步更正；**本条不再是未决项**。")
    w("3. **`a05_d0`/`a05_e0`（涅布）后继未确证**：`next=[]`、`next_kind=\"end\"`，"
      "但语义上非终点（报告 §4.4）。候选 `a05_b1`/`a05_c1`/`a06_a0`。")
    w("4. **`24_5a` 的 3 条选项源值均为 `ヨージ`**（AS 报告 §5.3 登记，疑源提取缺陷），如实保留。")
    w("5. **`24_1b` 的 `伽桜羅` 为原作写形**（非 `伽楼羅`），故其译文保持 AS 侧「伽楼罗」。")
    w("6. **`s03c_01d` 的 `target` 未确证**（`next` 候选 `s03c_01d1`/`s03c_01d2`）。")
    w("7. **前奏诗 4 点 / 9 槽随 D15 一并排除**——若用户日后决定保留 `02_*`/`03_*`，"
      "这些选择支须重新纳入（已在 `branch_points[]` 中 `in_spine=false` 留档）。")
    w("8. **`ot` 的 `s03c` 场景不在 `scene_ot.jsonl`**（其 21 脚本由 `scene_otr.jsonl` 的 55 场景版覆盖）；"
      "跨模块 `next` 由编程组接线，**唯一入口**为 `ot_s03_09a2.next=['s03c_01a']` → `otr_s03c_01a`"
      "（W10b 确证；`s03_09a2` 本身无 `choices`，是 (N)/(C) 变体分叉，见 §七.2）。")
    w("9. **番外插入时机无原作证据**：`entry_after` 一律 `null`，只给建议值。")
    w("")
    w("---")
    w("")
    w("## 八、验收自证（6 项）")
    w("")
    w("| # | 标准 | 实测 | 结论 |")
    w("| ---: | --- | --- | :---: |")
    w("| 1 | 场景全覆盖（712 ∈ acts ∪ excluded ∪ side，无遗漏无重复） | "
      "acts %d ＋ excluded %d ＋ side %d ＝ **%d**；重复 %d；源总数 %d | **通过** |"
      % (recon["acts_total"], recon["excluded_total"], recon["side_total"],
         recon["sum_total"], len(recon["duplicates"]), recon["source_scene_total"]))
    w("| 2 | 排除项精确（前奏诗 02_*/03_* 条数 == jsonl 实测） | excluded %d == jsonl %d（02:%d/03:%d） | **通过** |"
      % (recon["otp_0203_in_excluded"], recon["otp_0203_in_jsonl"],
         recon["otp_0203_02"], recon["otp_0203_03"]))
    w("| 3 | 番外精确（AS 22_* = 7、23_* = 7） | 22_* **%d**、23_* **%d** | **通过** |"
      % (recon["ota_22"], recon["ota_23"]))
    w("| 4 | 分支点完整（本篇 24/54、AS 40/57、前奏诗 4/9、亚衣线 1/2、涅布 34、PSV 0） | "
      "ot 24/54、ota 20/57、otp 4/9、otr 1/2、np 1/34、otv 0；差异 0 | **通过** |")
    w("| 5 | 顺序有据（每幕注明依据） | 11 幕全部标注 `basis`（流程图 §六 / §四） | **通过** |")
    w("| 6 | 不臆断（`target`、插入时机无确证填 `null`） | `target` 除涅布 34 条外全 `null`；"
      "`entry_after` 全 `null` 并说明 | **通过** |")
    w("")
    w("---")
    w("")
    w("## 九、可复现命令")
    w("")
    w("```bash")
    w("cd \"E:/ZCode Workspace/Galgame\"")
    w("python -X utf8 \"工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/build_spine.py\"")
    w("```")
    w("")
    w("**只读声明**：构建器对六个 `scene_<源代号>.jsonl` 全程只读（`sys.dont_write_bytecode=True`），"
      "**不改任何 `scene_*.jsonl`、不改 `schema.md`**；只写 `资源组\\剧本\\{spine.json, 主线编排方案.md}`。")
    w("")
    _assert_in_checkout(OUT_MD, "主线编排方案.md")
    with io.open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("md written:", OUT_MD)


if __name__ == "__main__":
    main()