# -*- coding: utf-8 -*-
r"""
build_picjp_disposition.py — 「图片化日文」629 件的**处置裁决**表生成器（ISSUE-20260930-07）

用户 2026-09-30 裁决（提问控件）：
  > 「只保留**片头/片尾的演出素材**，剩下的比如『按钮图片/时间图片』都弃用。」
  > 边界取**选项 A**：片头字幕条 `op_*` 40 件 ＋ 片尾（CG背景）92 件 = **132 件保留**，其余 **497 件弃用**。

⚠ 「弃用」= **不采用为工程素材、不重绘、不在中文界面出现**；**不是删除**。
   素材本身仍留在 `krkr素材库\`（原始账）与 `美术统一\`（统一集，逐字节不动）——
   原因：① 曲名位图是 `交接编程组\BGM曲名表.tsv` 的证据链；② 原始素材账必须可回溯。
   「是否从交付层（`美术统一_交付\`）移除」是另一件事，本次不做。

输入（只读）：
  - `资源组\审计\图片化日文_审查清单.tsv`（629 数据行 / 9 列；ISSUE-20260930-05 交付）
  - `资源组\krkr素材库\资源总账.json`（用于「片头字幕条 = ot 的 op_* 全集」这一硬闸门；
     该文件 gitignore，仅在**主工作区**存在 → 用 _product() 解析）

输出（入库）：
  - `资源组\审计\图片化日文_处置清单.tsv`（629 数据行 / 12 列：本表为处置的**唯一真值**）
  - `资源组\审计\图片化日文_保留清单.tsv`（132 数据行 / 8 列：给 UI 组 / 编程组的保留集）

硬闸门（都能真失败）：
  G1 输入行数 == 629（与 `美术统一\交付清单.tsv` 的 `图片化日文 == 是` 计数一致）
  G2 保留总数 == 132（片头 40 ＋ 片尾 92）
  G3 弃用总数 == 497；G2+G3 == G1（守恒）
  G4 片头保留集 == ot 的 `op_*.elg` **全集**（从 `资源总账.json` 取，若 != 保留数 → 失败）
  G5 片尾保留集 == 输入里 `类别 == CG背景` 的全部行
  G6 写盘后回读：行数 / 处置计数 / `统一名` 集合与内存逐项一致
  G7 `--check` 幂等：连跑两轮第二轮 0 改动

用法：
  python -X utf8 build_picjp_disposition.py            # 生成（写盘）
  python -X utf8 build_picjp_disposition.py --check     # 只校验，不写
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                      # ...\资源组
PROJ = os.path.dirname(RES)                      # ...\我们没有翅膀——格雷塔迦露德与柳木原

IN_REVIEW = os.path.join(RES, "审计", "图片化日文_审查清单.tsv")
OUT_TRIAGE = os.path.join(RES, "审计", "图片化日文_处置清单.tsv")
OUT_KEEP = os.path.join(RES, "审计", "图片化日文_保留清单.tsv")
LEDGER = os.path.join(RES, "krkr素材库", "资源总账.json")
DELIVERY_LIST = os.path.join(RES, "美术统一", "交付清单.tsv")

# 用户裁决原文（写进产物，便于溯源）
RULING = "用户 2026-09-30 裁决（提问控件）：只保留片头/片尾演出素材，其余弃用（选项 A）"

KEEP_HEAD = "保留·片头字幕条"
KEEP_TAIL = "保留·片尾"
DROP = "弃用"

# 片尾子族判定（只用于备注列，不影响处置）
TAIL_SUBFAM = OrderedDict([
    ("end_staff", "片尾STAFF（超长竖条）"),
    ("sr2_t", "片尾歌词字幕条"),
    ("sr0", "片尾STAFF 分页"),
    ("sr1", "片尾STAFF 分页"),
    ("sr2", "片尾STAFF 分页"),
    ("sr3", "片尾STAFF 分页"),
    ("sr4", "片尾STAFF 分页"),
    ("sl_", "片尾（前奏诗侧 sl_*）"),
])

# 弃用件的「族 / 是什么」——按前缀**最长优先**匹配（长的写在前面）
WHY = [
    ("mc_bgm", "曲名位图", "音乐鉴赏曲名（日文为主）——本作改引擎绘字；本族另作 BGM 曲名表证据链"),
    ("gl_bgm", "曲名位图", "音乐鉴赏曲名（英文为主）——同上"),
    ("op.png", "画廊按钮", "画廊「OPENING」按钮卡面（按钮图片）"),
    ("sr.png", "画廊按钮", "画廊「SKIP/SLOW ROLL」按钮卡面（按钮图片）"),
    ("dlg_bg", "对话窗底图", "含烘焙文字的对话窗底图——本作对话框自建、文字引擎绘制"),
    ("bg_config", "配置屏整页", "PSV 配置画面整页（本作配置屏自建）"),
    ("quick_load_bg", "存读档屏整页", "PSV 快速读档整页"),
    ("quick-save", "存读档屏整页", "PSV 快速存档整页"),
    ("sys_menu", "系统菜单整页", "PSV 系统菜单整页（本作改用快捷条）"),
    ("title_bg", "标题屏整页", "PSV 标题画面整页（本作标题屏自建）"),
    ("save_bg", "存读档屏整页", "PSV 存档画面整页"),
    ("load_bg", "存读档屏整页", "PSV 读档画面整页"),
    ("sl_data", "存读档屏整页", "PSV 存读档整页文字"),
    ("saving", "加载提示", "「セーブ中…」提示"),
    ("loading", "加载提示", "「ロード中…」提示"),
    ("config.png", "配置屏整页", "PSV 配置画面整页"),
    ("notice2", "版权声明页", "版权 / 使用条款页"),
    ("mc_galry", "画廊", "画廊入口按钮"),
    ("mc_page", "画廊", "画廊页码 / 翻页"),
    ("mc_bg", "画廊", "画廊底板"),
    ("gm_bg", "画廊整页", "画廊整页"),
    ("mv_bg", "影片鉴赏整页", "影片鉴赏整页"),
    ("mu_bg", "音乐鉴赏整页", "音乐鉴赏整页"),
    ("gl_chr", "画廊", "立绘鉴赏按钮 / 换装"),
    ("gl_page", "画廊", "画廊翻页"),
    ("gl_exit", "画廊", "画廊退出"),
    ("gl_scene", "画廊", "场景鉴赏"),
    ("gl_music", "画廊", "音乐鉴赏按钮"),
    ("gl_movie", "画廊", "影片鉴赏按钮"),
    ("gl_num", "画廊", "画廊序号"),
    ("gl_", "画廊", "画廊按钮 / 标签"),
    ("ga_", "相册/影片鉴赏按钮", "相册 / 影片鉴赏按钮与标签"),
    ("ex_", "鉴物卡面", "EXTRA 鉴赏卡面标题"),
    ("sc_", "场景选择卡面", "原作场景选择卡面标题（本作不复刻该屏）"),
    ("ec", "章节题卡/日期条", "章节题字卡与日期条——章名走 spine.json、日期走 game_date，均引擎绘字；日期条即用户所指「时间图片」"),
    ("tl", "标题菜单", "标题画面菜单 / 按钮"),
    ("sm", "系统菜单", "系统菜单条"),
    ("cf", "配置屏", "配置屏标签 / 按钮"),
    ("cfg", "配置屏", "配置屏底图"),
    ("sv", "存档屏", "存档屏标签 / 按钮"),
    ("ld", "读档屏", "读档屏标签 / 按钮"),
    ("ss", "存读档屏", "PSV 存读档屏按钮与日期条"),
    ("dm", "加载提示", "「ロード中…」提示（dm00–dm11）"),
    ("skp1_icon", "状态图集", "AUTO/SKIP/STOP 状态字图集"),
    ("if_", "确认框", "确认框按钮（はい/いいえ/…）"),
    ("cm_", "确认框", "确认框"),
    ("buru", "剧场题字", "ぶるぶる劇場题字（前奏诗框架剧）——本作自行制作该屏题字"),
    ("no_data", "占位图", "无存档占位"),
    ("no_img", "占位图", "无图占位"),
]
WHY_BY_PREFIX = sorted(WHY, key=lambda x: -len(x[0]))


def _product(*rel: str) -> str:
    """把「相对本工作树」的路径解析到**主工作区**（本工程既有的 fail-loud 口径）。

    gitignore 的产物（资源总账.json）在检出树里不存在 → 先找检出、再找主工作区；都没有就 SystemExit。
    """
    tried = []
    for relpath in rel:
        for root in (PROJ, r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原"):
            cand = os.path.join(root, relpath)
            tried.append(cand)
            if os.path.isfile(cand):
                return cand
    raise SystemExit("找不到产物（已试）：\n  " + "\n  ".join(tried))


def _lf(text: str) -> str:
    """按 LF 规范化后再比较（盘面可能是 CRLF，见 C12 与既有「闸门盘面 md5」教训）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_tsv(path: str):
    with io.open(path, encoding="utf-8", newline="") as f:
        rows = [ln.rstrip("\n").rstrip("\r").split("\t") for ln in f]
    head, data = rows[0], [r for r in rows[1:] if r and r[0] != ""]
    return head, data


def family_of(uname: str) -> str:
    """处置票用的族名（保留件按演出归属，弃用件按被判定的族；见 classify()）。"""
    if uname.startswith("op_"):
        return "片头字幕条"
    if re.match(r"^\d", uname):
        return "数字开头菜单条"
    bucket, _why = classify(uname)
    return bucket


def classify(uname: str):
    """返回 (族, 是什么)。最长前缀优先；都不中则落「其它源版 UI 图」。"""
    if re.match(r"^\d", uname):
        return "数字开头菜单条", "系统条 / 菜单条（00_qsave 等数字开头族）"
    for pref, bucket, why in WHY_BY_PREFIX:
        if uname.startswith(pref):
            return bucket, why
    return "其它源版 UI 图", "源版系统 UI 图（本作界面自建、文字一律引擎绘制）"


def tail_subfam(src_name: str) -> str:
    """来源形如 `ot:ot_sr0_01` → 先去掉源前缀与扩展名，再按族前缀归类。"""
    base = src_name.split(":")[-1].lower()
    base = re.sub(r"^[a-z]{2,4}_", "", base)
    base = re.sub(r"\.(png|jpg|jpeg)$", "", base)
    for pref, name in TAIL_SUBFAM.items():
        if base.startswith(pref):
            return name
    return "片尾"


def op_numbers_expected() -> int:
    """从素材总账取 ot 的 op_*.elg 件数（片头字幕条全集）。"""
    path = _product(r"资源组\krkr素材库\资源总账.json")
    with io.open(path, encoding="utf-8") as f:
        d = json.load(f)
    names = [e["orig_name"] for e in d["entries"]
             if e["source"] == "ot" and e["kind"] == "sys"
             and re.match(r"^op_\w+\.elg$", e["orig_name"], re.I)]
    return len(sorted(set(names)))


def delivery_flag_count() -> int:
    """从交付清单读 `图片化日文 == 是` 计数（用于 G1 交叉核对）。"""
    path = _product(r"资源组\美术统一\交付清单.tsv")
    head, data = read_tsv(path)
    i = head.index("图片化日文")
    return sum(1 for r in data if len(r) > i and r[i].strip() == "是")


def _ledger_by():
    """(source, 素材库文件名小写) -> ledger entry（用于把字节数并入处置表）。"""
    with io.open(_product(r"资源组\krkr素材库\资源总账.json"), encoding="utf-8") as f:
        d = json.load(f)
    def stem(fn):
        return re.sub(r"\.(png|jpg|jpeg|ogg|mpg|mp4|txt)$", "", fn.lower())

    return {(e["source"], stem(e["filename"])): e for e in d["entries"]}


def build():
    LED_BY = _ledger_by()
    head, data = read_tsv(IN_REVIEW)
    need = ["序号", "类别", "判读类别", "统一名", "交付路径", "尺寸", "来源", "子族", "曲名位图"]
    for c in need:
        if c not in head:
            sys.exit(f"[G0 失败] 审查清单缺列：{c}（实有 {head}）")
    ix = {c: head.index(c) for c in need}

    rows, keep = [], []
    for r in data:
        uname = r[ix["统一名"]]
        cat = r[ix["类别"]]
        src = r[ix["来源"]]
        if cat == "CG背景":
            disp, basis = KEEP_TAIL, "片尾演出素材（sr STAFF 页 / sr2_t 歌词条 / sl_* / end_staff）"
            consumer = "UI组/编程组（片尾演出）"
            note = tail_subfam(src)
        elif uname.startswith("op_"):
            disp, basis = KEEP_HEAD, "片头（序幕）演出文字条——`op` 脚本的演出素材"
            consumer = "UI组（重绘为中文）"
            note = "格雷塔迦露德开篇文字条（非选项文本；见 12_序章开场段演出完备性.md）"
        else:
            disp, basis = DROP, RULING
            consumer = "—"
            note = classify(uname)[1]
        _s, _f = src.split(":", 1)
        _e = LED_BY.get((_s, re.sub(r"\.(png|jpg|jpeg|ogg|mpg|mp4|txt)$", "", _f.lower())))
        rec = [r[ix["序号"]], cat, family_of(uname), uname, r[ix["交付路径"]], r[ix["尺寸"]],
               (_e or {}).get("bytes", ""), src, "是", disp, basis, consumer, note]
        rows.append(rec)
        if disp != DROP:
            keep.append([r[ix["序号"]], disp, family_of(uname), uname, r[ix["交付路径"]],
                         r[ix["尺寸"]], src, note])

    # ---- 硬闸门 ----
    n_in = len(data)
    n_keep = sum(1 for r in rows if r[9] != DROP)
    n_head = sum(1 for r in rows if r[9] == KEEP_HEAD)
    n_tail = sum(1 for r in rows if r[9] == KEEP_TAIL)
    n_drop = n_in - n_keep
    errs = []
    dv = None
    if n_in != 629:
        errs.append(f"G1 输入行数 {n_in} != 629")
    try:
        dv = delivery_flag_count()
        if dv != n_in:
            errs.append(f"G1 交付清单「图片化日文==是」= {dv} != 审查清单 {n_in}")
    except SystemExit as e:
        errs.append(f"G1 交叉核对跳过（找不到交付清单）：{e}")
    if n_head != 40:
        errs.append(f"G2 片头保留 {n_head} != 40")
    if n_tail != 92:
        errs.append(f"G2 片尾保留 {n_tail} != 92")
    if n_keep != 132:
        errs.append(f"G2 保留合计 {n_keep} != 132")
    if n_drop != 497:
        errs.append(f"G3 弃用 {n_drop} != 497")
    if n_keep + n_drop != n_in:
        errs.append("G3 守恒失败")
    exp_op = op_numbers_expected()
    if exp_op != n_head:
        errs.append(f"G4 素材总账 ot 的 op_*.elg = {exp_op} 件 != 保留的 {n_head} 件（片头集不完整或口径不一致）")
    tail_all = [r for r in rows if r[1] == "CG背景"]
    if len(tail_all) != n_tail or any(r[9] != KEEP_TAIL for r in tail_all):
        errs.append(f"G5 CG背景 {len(tail_all)} 件未全数进片尾保留集")
    # 弃用集不得混进 op_*
    bad = [r[3] for r in rows if r[9] == DROP and r[3].startswith("op_")]
    if bad:
        errs.append(f"G5 弃用集混入片头件：{bad[:5]}")

    print(f"输入 {n_in} 行（交付清单「图片化日文==是」= {dv}）")
    print(f"  保留·片头字幕条 op_* : {n_head}")
    print(f"  保留·片尾           : {n_tail}  {dict(Counter(r[12] for r in rows if r[9]==KEEP_TAIL))}")
    print(f"  弃用                : {n_drop}")
    fam = Counter(r[2] for r in rows if r[9] == DROP)

    def _by(r):
        _s, _f = r[7].split(":", 1)
        return (LED_BY.get((_s, re.sub(r"\.(png|jpg|jpeg|ogg|mpg|mp4|txt)$", "", _f.lower()))) or {}).get("bytes", 0)

    b_keep = sum(_by(r) for r in rows if r[9] != DROP)
    b_drop = sum(_by(r) for r in rows if r[9] == DROP)
    if b_drop == 0:
        errs.append("G8 弃用集字节合计为 0 → 素材账查表失败（来源列口径变了？）")
    print("  字节：保留 %.1f MiB ｜ 弃用 %.1f MiB（弃用集若从交付层移除可省这一体积）"
          % (b_keep / 1048576.0, b_drop / 1048576.0))
    print("  弃用族分布：")
    for k, v in sorted(fam.items(), key=lambda x: -x[1]):
        print(f"    {k:16s} {v}")

    # ⚠️ 闸门总检必须在**全部** errs 追加之后（G8 曾因检查点提前而成为死闸门，一审 N1）
    if errs:
        print("[闸门失败]")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    return rows, keep, head, [c for c in need]


def write_tsv(path, head, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(head) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")


def verify_written(rows, keep):
    h1, d1 = read_tsv(OUT_TRIAGE)
    h2, d2 = read_tsv(OUT_KEEP)
    errs = []
    if len(d1) != len(rows):
        errs.append(f"G6 回读处置清单 {len(d1)} != {len(rows)}")
    if len(d2) != len(keep):
        errs.append(f"G6 回读保留清单 {len(d2)} != {len(keep)}")
    if {r[3] for r in d1} != {r[3] for r in rows}:
        errs.append("G6 回读统一名集合不一致")
    if Counter(r[9] for r in d1) != Counter(r[9] for r in rows):
        errs.append("G6 回读处置计数不一致")
    if h1 != ["序号", "类别", "族", "统一名", "交付路径", "尺寸", "字节", "来源", "像素事实", "处置",
              "处置依据", "消费者", "备注"]:
        errs.append(f"G6 处置清单表头不符：{h1}")
    if h2 != ["序号", "处置", "族", "统一名", "交付路径", "尺寸", "来源", "备注"]:
        errs.append(f"G6 保留清单表头不符：{h2}")
    if errs:
        print("[G6 失败]")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("G6 回读校验 PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写盘")
    args = ap.parse_args()

    rows, keep, _h, _need = build()
    head1 = ["序号", "类别", "族", "统一名", "交付路径", "尺寸", "字节", "来源", "像素事实", "处置",
             "处置依据", "消费者", "备注"]
    head2 = ["序号", "处置", "族", "统一名", "交付路径", "尺寸", "来源", "备注"]

    if args.check:
        have = os.path.isfile(OUT_TRIAGE) and os.path.isfile(OUT_KEEP)
        if not have:
            print("[--check] 产物不存在 → 需要先跑一次生成")
            sys.exit(1)
        old1 = _lf(io.open(OUT_TRIAGE, encoding="utf-8", newline="").read())
        old2 = _lf(io.open(OUT_KEEP, encoding="utf-8", newline="").read())
        write_tsv(OUT_TRIAGE, head1, rows)
        write_tsv(OUT_KEEP, head2, keep)
        same = (_lf(io.open(OUT_TRIAGE, encoding="utf-8", newline="").read()) == old1
                and _lf(io.open(OUT_KEEP, encoding="utf-8", newline="").read()) == old2)
        verify_written(rows, keep)
        if not same:
            print("[--check] 有改动 → 非幂等（产物与本次生成不一致）")
            sys.exit(1)
        print("[--check] 0 改动（幂等）PASS")
        return

    write_tsv(OUT_TRIAGE, head1, rows)
    write_tsv(OUT_KEEP, head2, keep)
    print(f"写出 {os.path.relpath(OUT_TRIAGE, PROJ)}（{len(rows)} 行）")
    print(f"写出 {os.path.relpath(OUT_KEEP, PROJ)}（{len(keep)} 行）")
    verify_written(rows, keep)


if __name__ == "__main__":
    main()
