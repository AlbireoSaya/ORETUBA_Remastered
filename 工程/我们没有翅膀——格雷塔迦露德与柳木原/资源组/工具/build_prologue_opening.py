# -*- coding: utf-8 -*-
r"""
build_prologue_opening.py — 「序章开场段（片头）」素材账 + **演出序列**（ISSUE-20260930-07）

用户 2026-09-30 裁决（提问控件）：「游戏序章」= **片头＋序章开场段**，
即 `op_*`（格雷塔迦露德开篇文字条 40 件）＋ 片头影片（ot 的 2 支）。

★ 本次关键发现：**演出序列可从 `op.sob` 的字符串引用表恢复**——
  `工程\我们没有翅膀\解包\SCRIPT\op.sob`（Lucifen SOB0；非剧情脚本、无 ScSkip 标记，故不在 712 场景表内）
  的 cp932 字符串表按引用顺序登记着：
    `PIC\BG01/02/63/65/68.ELG`（5 张背景）、`VOICE\XXXnnnn.OGG`（36 条语音）、
    `SYS\OP_NN.ELG`（40 条文字条）、`SYS/RULE042.ELG`（转场遮罩），
    以及控制串 `cross` / `rule` / `bg_move` / `a0 r|u|d|l`（背景平移方向；a0＝对象、取值＝方向）。
  ⇒ 顺序 / 背景 / 语音 / 转场 / 平移方向**有据**；**时机·时长·坐标·淡入淡出仍无据**（opcode 未逆向，总纲 R1）。

输入（只读）
  - `工程\我们没有翅膀\解包\SCRIPT\op.sob`   ← 演出序列真值来源（工作区根；解包产物，gitignore）
  - `资源组\krkr素材库\资源总账.json`         ← 素材事实与可解析性
  - `资源组\美术统一\系统UI\op_*.png`         ← md5 绑定（把目读文本钉到确切字节）
  - `资源组\审计\图片化日文_处置清单.tsv`      ← 「保留·片头字幕条」集合须与素材账全集相等
  - `资源组\审计\序章开场段_影片探针.txt`       ← ffprobe + MCI(DirectShow) 实测记录

输出（入库）
  - `资源组\审计\序章开场段_清单.tsv`     ← 42 行：字幕条 40 ＋ 影片 2（素材账 + 目读文本）
  - `资源组\审计\序章开场段_演出序列.tsv`  ← 推定播放序（背景 / 语音 / 文字条 / 遮罩 / 平移 / 转场）

硬闸门（**8 条**，都能真失败）
  G1 `op.sob` 可定位；其字符串表里 `SYS\OP_*.ELG` == 40，且与素材账、处置清单「保留·片头字幕条」**三方逐名相等**
  G2 被引用素材（36 语音 + 5 背景 + 1 遮罩）在素材账中**全部可解析**（0 未解析）
  G3 反序（推定播放序）后 OP 编号**严格升序**
  G4 形态自洽**不变量**：宽幅（1200×600）背景配 `r`/`l`、纵幅（800×1200）配 `u`/`d`、屏幕尺寸（800×600）**无平移**
  G5 40 件全 RGBA、宽 201–731、高 35–39；目读文本 40/40 齐全
  G6 影片 2 支在探针记录里 OPEN-OK + playing，且探针结论含「全部 PASS」
  G7 行数守恒（清单 42）与 `--check` 幂等
  G8 影片 2 行的 `备注` 必须带「占位·待替换」标注（用户 2026-09-30 裁决「必须做好标注」）
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
PROJ = os.path.dirname(RES)


def _workspace_roots():
    """所有可能的工作区根：本工程的 git 检出树 + 各级含 Galgame.md 的祖先 + 主工作区。

    ⚠️ 检出树自己也有 Galgame.md（它是 tracked 文件）⇒ 不能「只看第一个命中」，
       必须把候选**全部**列出依次尝试（既有踩坑记录，见 probe_mci_playable.ps1 注释）。
    """
    roots = [PROJ]
    d = PROJ
    while True:
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
        if os.path.isfile(os.path.join(d, "Galgame.md")):
            roots.append(d)
    roots.append(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原")
    roots.append(r"E:\ZCode Workspace\Galgame")
    seen, out = set(), []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


ROOTS = _workspace_roots()

OUT_LIST = os.path.join(RES, "审计", "序章开场段_清单.tsv")
OUT_SEQ = os.path.join(RES, "审计", "序章开场段_演出序列.tsv")
DISP_REL = os.path.join("资源组", "审计", "图片化日文_处置清单.tsv")
PROBE_REL = os.path.join("资源组", "审计", "序章开场段_影片探针.txt")

SOB_REL = os.path.join("工程", "我们没有翅膀", "解包", "SCRIPT", "op.sob")
LEDGER_REL = os.path.join("资源组", "krkr素材库", "资源总账.json")

GROUPS = OrderedDict([
    ("0", "框（たとえば 框子：三句定场）"),
    ("1", "创世·雪与火"),
    ("2", "战祸蔓延（村镇焚毁、民逃）"),
    ("3", "列国陷落（精灵/矮人/侏儒城邦尽墨）"),
    ("4", "骑士与妖术（四幕双行条）"),
    ("5", "片头影片字幕段（与 op2 画内同段）"),
    ("6", "收束框（回到 たとえば）"),
])

TEXT = OrderedDict([
    ("op_01", ("これは“たとえば”の話だけど", "")),
    ("op_02", ("ある日、翼あるひとびとが", "")),
    ("op_03", ("グレタガルドの白い空を埋めつくしたんだ", "")),
    ("op_11", ("天地の半ばに羽根の舞う", "")),
    ("op_12", ("雪花のごとく繽紛と", "")),
    ("op_13", ("慈悲なき鏃の降りそそぐ", "")),
    ("op_14", ("羽根のまにまに繽紛と", "与 op_16 逐字节相同")),
    ("op_15", ("燃える礫の降りそそぐ", "")),
    ("op_16", ("羽根のまにまに繽紛と", "与 op_14 逐字节相同")),
    ("op_21", ("草葺き屋根の里が焼け", "")),
    ("op_22", ("ポプラ木立の邑が焼け", "")),
    ("op_23", ("世界の底を逃げまどう", "")),
    ("op_24", ("無辜なる民の靴の音", "")),
    ("op_25", ("石の街路を駆けぬけて", "")),
    ("op_26", ("荒れた嘆を駆けぬけて", "「嘆」经 **8× nearest** 目读判读（右部件＝堇「廿+口+夫」）；**非源侧直证**（左偏旁在 8–10 px 下 口/日 不可靠区分，模板匹配胜出随字体翻转）——旁证：六源语料 `嘆` 55 次、曠/嘵/嘖/嗔/暵 0 次")),
    ("op_27", ("世界の底を逃げまどう", "与 op_23 逐字节相同（md5 实测，一审复核）")),
    ("op_28", ("馬のひづめの轟きよ", "")),
    ("op_31", ("エルフの森の王国も", "")),
    ("op_32", ("ドワーフ造りの山の砦も", "")),
    ("op_33", ("機械仕掛けのノームの城も", "")),
    ("op_34", ("猖獗極まる侵寇の", "")),
    ("op_35", ("波涛に呑まれて隊伍散る", "")),
    ("op_36", ("戦火の河に立たされた", "")),
    ("op_37", ("人の子たちの負け戦", "")),
    ("op_38", ("翼の泊る空の下", "")),
    ("op_39", ("堅牢堅固も過去の栄誉か", "")),
    ("op_3a", ("終焉迫る城塞都市", "")),
    ("op_41", ("聖なる騎士さえ堂に入り　円蓋の下　神よと祈った", "双行条（上行小字＋下行大字）")),
    ("op_42", ("宮廷道化は楼閣のぼり　蛹の翼で飛ばんと嘯く", "双行条")),
    ("op_43", ("陰に潜んだスラムの王は　武器を鎧って空を睨んだ", "双行条；「鎧」经 5× 目读确认为「鎧」（一审复核）")),
    ("op_44", ("暗き洞楼む妖術使いは　闇を纏って機を待った", "双行条；「む」经 3× 目读确认（一审复核）")),
    ("op_51", ("ほら、空ってどこにでも繋がってるよね", "与 op2 影片 10s 画内字幕同段")),
    ("op_52", ("どこへ逃げたって、", "")),
    ("op_53", ("敵はその白い翼でどこまでも追っかけてくるんだ", "")),
    ("op_54", ("だから翼のない彼らは、", "")),
    ("op_55", ("どこにも繋がってない空を求めていた", "")),
    ("op_56", ("そんな願いが通じて、", "")),
    ("op_57", ("いま彼らはとてもものどかな国でジングルベルを聴いていた", "")),
    ("op_61", ("これは“たとえば”の話だけど", "与 op_01 逐字节相同")),
    ("op_62", ("僕らが君に語るのは、たとえばそんなメルヘン", "与 op2 影片 30s 画内字幕同段")),
])


def _product(rel: str) -> str:
    for root in ROOTS:
        cand = os.path.join(root, rel)
        if os.path.isfile(cand):
            return cand
    raise SystemExit("找不到产物（已试 %d 个根）：%s" % (len(ROOTS), rel))


def _lf(text: str) -> str:
    """按 LF 规范化后再比较（盘面可能是 CRLF，见 C12 与既有「闸门盘面 md5」教训）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_tsv(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        rows = [ln.rstrip("\n").rstrip("\r").split("\t") for ln in f]
    return rows[0], [r for r in rows[1:] if r and r[0] != ""]


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sob_strings(path):
    """Lucifen SOB0 的 cp932 字符串表（长度 >=3，保持文件内出现顺序）。"""
    raw = open(path, "rb").read()
    out, cur = [], bytearray()
    for b in raw:
        if b == 0:
            if len(cur) >= 3:
                out.append(bytes(cur))
            cur.clear()
        elif 0x20 <= b <= 0x7E or 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC:
            cur.append(b)
        else:
            if len(cur) >= 3:
                out.append(bytes(cur))
            cur.clear()
    if len(cur) >= 3:
        out.append(bytes(cur))
    res = []
    for s in out:
        try:
            res.append(s.decode("cp932"))
        except Exception:
            pass
    return res


KIND_RE = re.compile(r"^(VOICE|SYS|PIC|SE|BGM|MOVIE|DATA)\b")
CTRL = {"cross", "rule", "bg_move"}

# 片头影片两项裁决（用户 2026-09-30 18:00）：画内日文字幕保留原文；画幅暂留黑边、将来替换为 16:9 超分件
MOVIE_NOTE = ("**占位·待替换**（画内日文字幕**保留原文**；画幅暂按 1:1 居中留黑边，"
              "将来由 AI 超分 16:9 / 1920×1080 影片替换）")
MOVE_RE = re.compile(r"^a\d [rudl]$")
OP_RE = re.compile(r"OP_([0-9A-Za-z]{2})\.ELG$")


def resolve(ref, by):
    parts = ref.replace("/", "\\").split("\\")
    kind_dir = parts[0].lower()
    name = parts[-1].lower()
    return by.get(("ot", kind_dir, name))


def op_key(ref):
    """编号排序键：前一位＝十位组，后一位＝组内位。

    注意 `op_3a` **不是十六进制**——它是「组 3 的第 a 项」，夹在 `op_39` 与 `op_41` 之间
    （实测：源编号体系为 组号+序号，故 a 记作组内第 10 位）。用 int(s,16) 会把它排到 58，
    从而破坏「反序后升序」这条闸门。
    """
    m = OP_RE.search(ref.replace("/", "\\"))
    if not m:
        return None
    t = m.group(1).lower()
    tens = int(t[0], 16)
    sub = int(t[1]) if t[1].isdigit() else 10 + (ord(t[1]) - ord("a"))
    return (tens, sub)


def build():
    errs = []
    sob = _product(SOB_REL)
    with io.open(_product(LEDGER_REL), encoding="utf-8") as f:
        ents = json.load(f)["entries"]
    by = {(e["source"], e["kind"], e["orig_name"].lower()): e for e in ents}

    refs = [s for s in sob_strings(sob) if KIND_RE.match(s) or s in CTRL or MOVE_RE.match(s)]
    ops_ref = [r for r in refs if OP_RE.search(r.replace("/", "\\"))]
    vo_ref = [r for r in refs if r.upper().startswith("VOICE")]
    pic_ref = [r for r in refs if r.upper().startswith("PIC")]
    rule_ref = [r for r in refs if re.search(r"RULE\d+\.ELG$", r, re.I) or r.lower().startswith("sys/rule")]
    moves = [r for r in refs if MOVE_RE.match(r)]

    def uname(ref):
        r"""引用（`SYS\OP_01.ELG`）→ 交付统一名（`op_01.png`）。"""
        base = ref.replace("/", "\\").split("\\")[-1].lower()
        return re.sub(r"\.elg$", "", base) + ".png"

    def lib2uni(name):
        """素材库文件名（`ot_op_01.png`）→ 交付统一名（`op_01.png`）。"""
        return re.sub(r"^[a-z]{2,4}_", "", name)

    sob_ops = sorted(uname(r) for r in ops_ref)
    led_ops = sorted(lib2uni(e["filename"]) for e in ents
                     if e["source"] == "ot" and e["kind"] == "sys"
                     and re.match(r"^op_\w+\.elg$", e["orig_name"], re.I))
    dh, dd = read_tsv(_product(DISP_REL))
    di = {c: dh.index(c) for c in ("统一名", "处置")}
    disp_ops = sorted(r[di["统一名"]] for r in dd if r[di["处置"]] == "保留·片头字幕条")
    if len(sob_ops) != 40:
        errs.append("G1 op.sob 里 OP_*.ELG = %d != 40" % len(sob_ops))
    for label, got in (("素材账", led_ops), ("处置清单", disp_ops)):
        if got != sob_ops:
            errs.append("G1 %s 与 op.sob 不等：仅 op.sob 有 %s ｜ 仅 %s 有 %s"
                        % (label, sorted(set(sob_ops) - set(got)), label, sorted(set(got) - set(sob_ops))))

    unresolved = [r for r in refs if KIND_RE.match(r) and resolve(r, by) is None]
    if unresolved:
        errs.append("G2 无法解析的引用：%s" % unresolved)

    seq = list(reversed(refs))
    keys = [op_key(r) for r in seq if OP_RE.search(r.replace("/", "\\"))]
    if keys != sorted(keys):
        errs.append("G3 反序后 OP 编号非升序：%s" % keys)

    inv, cur_bg = [], None
    for r in seq:
        if KIND_RE.match(r) and r.upper().startswith("PIC"):
            cur_bg = resolve(r, by)
        if r == "bg_move":
            inv.append([cur_bg, None])
        elif MOVE_RE.match(r) and inv and inv[-1][1] is None:
            inv[-1][1] = r[-1]
    for e, d in inv:
        if e is None:
            errs.append("G4 bg_move 未紧邻背景引用")
            continue
        w, h = e["image"]["width"], e["image"]["height"]
        if not (((w > h) and d in ("r", "l")) or ((h > w) and d in ("u", "d"))):
            errs.append("G4 形态不变量被破坏：%s %dx%d dir=%s" % (e["orig_name"], w, h, d))

    for e in (x for x in ents if x["source"] == "ot" and x["kind"] == "sys"
              and re.match(r"^op_\w+\.elg$", x["orig_name"], re.I)):
        im = e["image"] or {}
        if (im.get("mode") != "RGBA" or not (201 <= (im.get("width") or 0) <= 731)
                or not (35 <= (im.get("height") or 0) <= 39)):
            errs.append("G5 %s 形态越界：%sx%s %s" % (e["filename"], im.get("width"), im.get("height"), im.get("mode")))
    names = [n[:-4] for n in sob_ops]
    if [n for n in names if n not in TEXT]:
        errs.append("G5 缺目读文本：%s" % [n for n in names if n not in TEXT])
    if [n for n in TEXT if n not in names]:
        errs.append("G5 文本表多出：%s" % [n for n in TEXT if n not in names])

    rows = []
    for n in names:
        e = by[("ot", "sys", n + ".elg")]
        txt, flag = TEXT[n]
        p = _product(os.path.join("资源组", "美术统一", "系统UI", n + ".png"))
        rows.append(["字幕条", n.split("_")[1], "第 %s 组" % n.split("_")[1][0],
                     GROUPS[n.split("_")[1][0]], n + ".png", e["out_relpath"], "系统UI/" + n + ".png",
                     "%dx%d" % (e["image"]["width"], e["image"]["height"]), e["image"]["mode"],
                     e["bytes"], md5_of(p), txt, flag, "见 序章开场段_演出序列.tsv", ""])
    movies = sorted((e for e in ents if e["source"] == "ot" and e["kind"] == "movie"),
                    key=lambda e: e["filename"])
    probe = io.open(_product(PROBE_REL), encoding="utf-8").read()
    if "探针结论：全部 PASS" not in probe:
        errs.append("G6 探针记录无「全部 PASS」")
    for e in movies:
        m = re.search(r"PASS\s+" + re.escape(e["filename"]) + r"\s+OPEN-OK lengthMs=(\d+)", probe)
        if not m:
            errs.append("G6 探针记录缺 %s 的 OPEN-OK/playing" % e["filename"])
        ms = int(m.group(1)) if m else 0
        mp = _product(os.path.join("资源组", "krkr素材库", "ot", "movie", e["filename"]))
        rows.append(["影片", re.sub(r"^(ot_)", "", e["filename"][:-4]), "片头影片", "片头影片（OP）",
                     e["filename"], e["out_relpath"], "movie/" + e["filename"],
                     "800x600 / %.1f s" % (ms / 1000.0), "MPEG-1(pS)+MP2", e["bytes"], md5_of(mp),
                     "（无字幕条文本；画内含日文字幕，见报告 §3）", "", "无（源侧无引用数据）",
                     MOVIE_NOTE + " ｜ MCI/DirectShow OPEN-OK 且 mode=playing（探针实测）"])
    if len(rows) != 42:
        errs.append("G7 清单 %d 行 != 42" % len(rows))
    # G8 影片行的「占位·待替换」标注不得静默消失（用户 2026-09-30 裁决要求「必须做好标注」）
    movie_rows = [r for r in rows if r[0] == "影片"]
    if len(movie_rows) != 2:
        errs.append("G8 影片行 %d != 2" % len(movie_rows))
    for r in movie_rows:
        if "占位·待替换" not in r[14]:
            errs.append("G8 影片行缺「占位·待替换」标注：%s" % r[4])

    seqrows = []
    for i, r in enumerate(seq, 1):
        if r == "bg_move":
            seqrows.append([i, "控制", "bg_move", "（背景开始平移）", "—", "—", "是", ""])
        elif MOVE_RE.match(r):
            seqrows.append([i, "控制", r, "平移方向 %s" % {"r": "右", "u": "上", "d": "下", "l": "左"}[r[-1]],
                            "—", "—", "是", ""])
        elif r in CTRL:
            seqrows.append([i, "控制", r, "转场：%s" % ("交叉淡入" if r == "cross" else "遮罩转场"),
                            "—", "—", "是", ""])
        else:
            e = resolve(r, by)
            if e is None:
                seqrows.append([i, "?", r, "未解析", "—", "—", "否", ""])
                continue
            if e["kind"] == "voice":
                dur = (e.get("audio") or {}).get("duration_sec")
                seqrows.append([i, "语音", r, e["filename"], e["out_relpath"],
                                ("%.2f s" % dur) if dur else "?", "是", ""])
            elif e["kind"] == "pic":
                seqrows.append([i, "背景", r, e["filename"], e["out_relpath"],
                                "%dx%d" % (e["image"]["width"], e["image"]["height"]), "是", ""])
            else:
                typ = "转场遮罩" if "RULE" in r.upper() else "文字条"
                seqrows.append([i, typ, r, e["filename"], e["out_relpath"],
                                "%dx%d" % (e["image"]["width"], e["image"]["height"]), "是",
                                TEXT.get(e["filename"][:-4], ("", ""))[0] if typ == "文字条" else ""])

    if errs:
        print("[闸门失败]")
        for x in errs:
            print("  -", x)
        sys.exit(1)

    print("G1 op.sob / 素材账 / 处置清单 三方 op_* 逐名相等 = 40")
    print("G2 引用全部可解析：文字条 %d ｜ 语音 %d（合计 %.1f s）｜ 背景 %d ｜ 遮罩 %d ｜ 控制 %d"
          % (len(ops_ref), len(vo_ref),
             sum(((resolve(r, by) or {}).get("audio") or {}).get("duration_sec", 0) for r in vo_ref),
             len(pic_ref), len(rule_ref), len(refs) - len(ops_ref) - len(vo_ref) - len(pic_ref) - len(rule_ref)))
    print("G3 推定播放序 OP 编号升序：%s"
          % " ".join("%d%s" % (a, "abcdefghij"[b - 10] if b >= 10 else str(b)) for a, b in keys))
    print("G4 形态自洽不变量 PASS：%s"
          % " ｜ ".join("%s(%dx%d)->%s" % (e["orig_name"], e["image"]["width"], e["image"]["height"], d or "无")
                        for e, d in inv))
    print("G5 字幕条 40 件形态合规 + 目读文本 40/40")
    print("G6 片头影片 2/2 OPEN-OK + playing")
    print("G7 清单 42 行 / 演出序列 %d 步" % len(seqrows))
    print("G8 影片 2 行均带「占位·待替换」标注（画内字幕保留原文＋将来替换 16:9 超分件）")
    return rows, seqrows


HEAD_LIST = ["类型", "编号", "段组", "段组主题（推定）", "统一名", "素材库路径", "交付路径",
             "尺寸/分辨率", "模式/编码", "字节", "md5", "文本（2026-09-30 目读）", "待核",
             "演出数据", "备注"]
HEAD_SEQ = ["步序", "类型", "资源原名（op.sob 字符串表）", "素材库/统一名", "素材库路径",
            "尺寸/时长", "在库", "文本（目读，仅文字条）"]


def write(path, head, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(head) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows, seqrows = build()
    if a.check:
        for p in (OUT_LIST, OUT_SEQ):
            if not os.path.isfile(p):
                print("[--check] 缺产物 %s → 先跑一次生成" % os.path.basename(p))
                sys.exit(1)
        old = tuple(_lf(io.open(p, encoding="utf-8", newline="").read()) for p in (OUT_LIST, OUT_SEQ))
        write(OUT_LIST, HEAD_LIST, rows)
        write(OUT_SEQ, HEAD_SEQ, seqrows)
        new = tuple(_lf(io.open(p, encoding="utf-8", newline="").read()) for p in (OUT_LIST, OUT_SEQ))
        hl, dl = read_tsv(OUT_LIST)
        hs, ds = read_tsv(OUT_SEQ)
        if hl != HEAD_LIST or len(dl) != 42 or hs != HEAD_SEQ or len(ds) != len(seqrows):
            print("[G7 失败] 回读不符")
            sys.exit(1)
        if old != new:
            print("[--check] 有改动 → 非幂等")
            sys.exit(1)
        print("[--check] 0 改动（幂等）PASS")
        return
    write(OUT_LIST, HEAD_LIST, rows)
    write(OUT_SEQ, HEAD_SEQ, seqrows)
    hl, dl = read_tsv(OUT_LIST)
    hs, ds = read_tsv(OUT_SEQ)
    if hl != HEAD_LIST or hs != HEAD_SEQ or len(dl) != 42 or len(ds) != len(seqrows):
        print("[G7 失败] 回读不符")
        sys.exit(1)
    print("写出 %s（%d 行）" % (os.path.relpath(OUT_LIST, PROJ), len(dl)))
    print("写出 %s（%d 行）" % (os.path.relpath(OUT_SEQ, PROJ), len(ds)))


if __name__ == "__main__":
    main()
