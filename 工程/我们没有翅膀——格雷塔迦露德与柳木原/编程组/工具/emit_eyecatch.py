#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
emit_eyecatch.py —— 章节过场卡（弹卡）插点表与卡件生成 ｜ B3（ISSUE-20261006-04）
================================================================================
政策（用户 2026-10-06 裁定 **C3**：逐条弹、同场去重）：
  · 数据源＝PSV 金标 `编程组\PSV演出\时间线.tsv` 里 `:Tasktype "EyeCatch"` 的行（847 条 / 414 场）；
  · **同一场只取首个「可实现」卡**（Major-2，ISSUE-20261006-04 一审回执）：按 (seq, 文件序) 排序，
    跳过 leading 的 mode1 与 `N=-1`、越界、缺件，取**首个能取件的 mode0**；
    整场无可实现卡则计数登记、不插点（旧实现「取首个」若首卡是 mode1 就整场 continue，
    实测压掉 111 场同场更晚处的可实现静态卡）；
  · **场景别名**（Major-1）：构建集里的可玩对应场（`otp_p03_01a..d`）PSV 无 `EyeCatch`，
    而 PSV 的卡挂在被去重裁掉的同内容场（`otv_P03_01A..D`）上 ⇒ 用 `SCENE_ALIAS` 把 PSV 场挂回
    构建集场（依据 `剧情审计_重复场景.tsv` G43–G46：完全重复 / 相似度 1.0 / otv 不入构建）；
  · **旧表兜底**（用户 2026-10-06 裁定）：PSV **无** `EyeCatch` 覆盖的 np/ota 5 场
    （`FALLBACK_SCENES`）保留旧表插点，卡号取自 `资源组\交接编程组\素材引用映射.tsv` 的
    `CG背景/ec*` 引用、`seq=1`（场景首行 sq）；**仅此 5 场**，PSV 有卡的场一律以 PSV 为准；
  · `:Image 0,N` → 卡号由**归档序 1-based 索引**解出（见 `ec_from_n`）；`N = -1` 跳过并计数；
  · `EC28`（＝标题 logo 卡）用 `eyecatch_compose.py` **分件合成**整卡（沿用既有产物路径/命名
    `eyecatch/ec__card_<场景>.png`）；其余卡号**直接用交付层对应件**（`美术统一_交付\CG背景\ec<NN>.*`），
    交付层无对应件则**登记缺件、不编造**；
  · `mode 1`（`:Image 1,s,b[,f]`，动画卡）**合成依据未判读 ⇒ 只登记不实现**。

插点键＝**(场景, seq)**（B3 要求按 seq 在弹出位置弹，不再只靠「章节标记行」触发）；
产物：`krkr\game\eyecatch\ec__*.png` ＋ `krkr\game\story\_eyecatch.tjs`
      （只定义 `uiEyecatchFill(o)`；TJS2 跨存储赋全局会抛错）
      ＋ `编程组\章节过场卡插点.tsv`（逐行可查：场景/seq/模式/EC号/产物/依据）。
被 `build_story.py` 在每次构建时调用（`run_storytest.py` 会先 rmtree story/ 再重建 ⇒ 必须进生成链）。
"""
import argparse
import csv
import io
import json
import os
import re
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eyecatch_compose as _ec

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(PROJ, "资源组")

# 章号规则：ot/otr 按路线；其余源**推定**（TSV 依据列写明，可逐行改）
CHAP_ROUTE = {"s01": 1, "s02": 2, "s03": 3, "s04": 4, "s03c": 3}
CHAP_SRC = {"np": 1, "ota": 1, "otv": 2}
CHAP_OTP = {"p01": 1, "p02": 1, "p03": 2, "p04": 2}

# ★ 场景别名表（Major-1，ISSUE-20261006-04 一审回执）：构建集场 → 「持有其 EyeCatch 的 PSV 场」。
#   依据：**不改写不臆造**，直接取 `编程组\剧情审计_重复场景.tsv` 现有记录 G43–G46
#   （「组」=完全重复，「相似度」=1.0，「入构建A」=是/「入构建B」=否）——
#   otp_p03_01{a..d} 入构建、otv_P03_01{A..D} 不入构建，正文行同为 112/151/176/142。
#   值为 (PSV 场 id, 证据组号)。
SCENE_ALIAS = {
    "otp_p03_01a": ("otv_P03_01A", "G43"),
    "otp_p03_01b": ("otv_P03_01B", "G44"),
    "otp_p03_01c": ("otv_P03_01C", "G45"),
    "otp_p03_01d": ("otv_P03_01D", "G46"),
}

# ★ 兜底插点白名单（**用户 2026-10-06 裁定**，主代理 2026-10-06 转达）：PSV **无** `EyeCatch`
#   覆盖、但旧表曾给过插点的 np/ota 5 场 ⇒ **保留旧表兜底插点**（与 B1「未覆盖场回落旧表」同一原则）。
#   卡号来源＝`资源组\交接编程组\素材引用映射.tsv` 里该场的 `CG背景/ec*` 引用（可复算的旧表来源）；
#   seq＝**场景首行 sq（=1）**——本作全部场 `lines[].sq` 实测为 `1..N` 连续（676/676），故 seq=1
#   必在该场 sq 集合内，且运行期 `uiStoryEcOnLine`（`cur >= due`）在入场首行即触发（＝旧「入场弹卡」行为）。
#   **这 5 场之外不得扩大兜底范围**：PSV 有 `EyeCatch` 的场一律以 PSV 为准（见循环前的 `s in cand` 判据）。
FALLBACK_SCENES = ("np_a01_b0", "np_a06_b1", "ota_11_3d1", "ota_41_5", "ota_42_5")

# ★ `:Image 0,N` 的 N ＝ CG.cpk 中 `EC*.png` 的「1-based 归档序索引」。
#   归档实存 EC01..EC19, EC21..EC29, EC31..EC37（35 个；**缺 EC20 / EC30**）——
#   依据：资源组《美咲线清单\映射结论.md》§A.1（吻合 654/658）与 §F6。
#   ⇒ 卡号 = 该序列第 N 个。例：N=27→EC28、N=20→EC21、N=29→**EC31**（不是 EC30）。
#   ⚠️ 任务书给的简化式「N+1（N≥20）否则 N」在 N≥29 处与归档枚举不符（因 EC30 亦缺，
#      偏移是 −2 而非 −1）；本实现按**归档枚举**（源文档权威），并在插点表逐条写明。
EC_ARCHIVE = list(range(1, 20)) + list(range(21, 30)) + list(range(31, 38))   # 35 个


def ec_from_n(n):
    """归档序 1-based 索引 N → EC 编号；越界返回 None。"""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return None
    if 1 <= n <= len(EC_ARCHIVE):
        return EC_ARCHIVE[n - 1]
    return None


def route_of(scene):
    if scene.startswith("otr_s03c"):
        return "s03c"
    for r in ("s01", "s02", "s03", "s04"):
        if scene.startswith("ot_" + r + "_"):
            return r
    return ""


def chapter_of(scene):
    r = route_of(scene)
    if r:
        return CHAP_ROUTE[r], "路线 " + r
    src = scene.split("_")[0]
    if src == "otp":
        for k, v in CHAP_OTP.items():
            if scene.startswith("otp_" + k):
                return v, "前奏诗 " + k + "（推定）"
        return 1, "前奏诗 其它（推定）"
    if src in CHAP_SRC:
        return CHAP_SRC[src], src + "→章（推定）"
    return 0, ""


def img_size(path):
    with open(path, "rb") as f:
        d = f.read(200000)
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", d[16:24])
    if d[:2] == b"\xff\xd8":
        i = 2
        while i < len(d) - 9:
            if d[i] != 0xFF:
                i += 1
                continue
            m = d[i + 1]
            if m in (0xC0, 0xC1, 0xC2, 0xC3):
                h, w = struct.unpack(">HH", d[i + 5:i + 9])
                return w, h
            if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    return 0, 0


def load_psv_eyecatch(psv_dir):
    """PSV `时间线.tsv` 的 EyeCatch 行 → {scene_id: [row, ...]}（保持文件先后）。"""
    out = {}
    p = os.path.join(psv_dir, "时间线.tsv")
    if not os.path.isfile(p):
        return out
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if (r.get("type") or "").strip() != "EyeCatch":
                continue
            sid = (r.get("scene_id") or "").strip()
            if sid:
                out.setdefault(sid, []).append(r)
    return out


def load_fallback_cards(res_root):
    """旧表兜底卡号：`资源组\交接编程组\素材引用映射.tsv` 中 `CG背景/ec*` 引用 → {样例场景: (card, 交付路径)}。

    仅用于白名单 `FALLBACK_SCENES`（见常量注释）；卡号＝交付路径 basename 里 `ec<NN>` 的十进制数。
    该表列：引用/统一名/**交付路径(2)**/组分类/结论/引用场景数/**样例场景(6)**/严重度。
    """
    out = {}
    p = os.path.join(res_root, "交接编程组", "素材引用映射.tsv")
    if not os.path.isfile(p):
        return out
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f, delimiter="\t")
        next(rd, None)
        for c in rd:
            if len(c) < 8 or "CG背景/ec" not in c[2]:
                continue
            scene = (c[6] or "").strip()
            m = re.match(r"ec0*(\d+)", os.path.basename(c[2].replace("\\", "/")))
            if scene and m:
                card = int(m.group(1))
                if card in EC_ARCHIVE:
                    out.setdefault(scene, (card, c[2].strip()))
    return out


def first_eyecatch(rows):
    """同场只取首个 ⇒ 按 (seq, 文件序) 取最靠前的行（已弃用：改用 emit 内的
    `pick_implementable`「首个可实现卡」判据，见 Major-2；保留仅为对照/外部引用兼容）。"""
    best = None
    for i, r in enumerate(rows):
        try:
            sq = int((r.get("seq") or "0").strip() or "0")
        except ValueError:
            sq = 0
        k = (sq, i)
        if best is None or k < best[0]:
            best = (k, r)
    return best[1] if best else None


def find_delivery_ec(deliv_dir, card):
    """交付层 `CG背景` 里找 EC 卡件：`ec<NN>.png` → `.jpg` → 同名 alt 变体；无则 None。"""
    base = "ec%02d" % card
    for ext in (".png", ".jpg"):
        p = os.path.join(deliv_dir, "CG背景", base + ext)
        if os.path.isfile(p):
            return p
    d = os.path.join(deliv_dir, "CG背景")
    if os.path.isdir(d):
        cands = sorted(f for f in os.listdir(d)
                       if f.startswith(base) and os.path.splitext(f)[1].lower() in (".png", ".jpg"))
        if cands:
            return os.path.join(d, cands[0])
    return None


def emit(story_dir, assets_dir, res_root=RES, also=(), tsv_path=None, quiet=False,
         psv_dir=None, scene_ids=None, full=None):
    deliv = os.path.join(res_root, "美术统一_交付")
    sys_dir = os.path.join(res_root, "krkr素材库", "ot", "sys")
    pic_dir = os.path.join(res_root, "krkr素材库", "ot", "pic")
    if psv_dir is None:
        psv_dir = os.path.join(os.path.dirname(res_root), "编程组", "PSV演出")
    # ★ Minor-1 护栏：剪枝 `ec__*` 只在**全量构建**才做（否则单场切片会把源树
    #   `krkr\game\eyecatch\` 收窄到该切片，而 `deploy_product.py` 对 eyecatch 无闸门）。
    #   调用方未显式给 full 时按「未限 scene_ids」推定（＝全库），切片构建须传 full=False。
    if full is None:
        full = scene_ids is None

    def log(*a):
        if not quiet:
            print(*a)

    # ---- 场景元数据（日期 + 场景 CG 引用，供 EC28 合成选照片；沿用旧口径）----
    meta = {}
    corpus = os.path.join(res_root, "剧本")
    if os.path.isdir(corpus):
        for fn in sorted(os.listdir(corpus)):
            if not (fn.startswith("scene_") and fn.endswith(".jsonl")):
                continue
            for ln in io.open(os.path.join(corpus, fn), encoding="utf-8"):
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                pics = [(a.get("out_relpath") or "") for a in (d.get("assets") or []) if a.get("kind") == "pic"]
                gd = d.get("game_date")
                if not gd:
                    gds = d.get("game_dates") or []
                    if gds and isinstance(gds[0], dict):
                        gd = gds[0].get("date")
                meta[d.get("scene_id", "")] = (gd, pics)
    pool = [n for n in sorted(os.listdir(sys_dir))
            if n.startswith("ot_ec_bg") and n.endswith(".png")] if os.path.isdir(sys_dir) else []
    if not pool:
        log("[eyecatch][warn] 缺 ot 题卡素材池：%s" % sys_dir)

    _photo_cache = {}

    def pick_photo(scene):
        """场景 CG → ot_ec_bg 池里 SAD 最接近的一张（沿用旧实现；按候选件缓存，B3 场景量大）。"""
        from PIL import Image, ImageChops
        _, pics = meta.get(scene, (None, []))
        pics = [b for b in pics if not os.path.basename(b).lower().startswith(("ot_ec", "ec", "np_ec", "otp_ec", "otr_ec"))]
        cand = ""
        for b in pics:
            stem = os.path.splitext(os.path.basename(b))[0]
            for pre in ("bg__", "pic__"):
                if stem.startswith(pre):
                    stem = stem[len(pre):]
            for nm in ("ot_" + stem + ".png", stem + ".png"):
                if os.path.isfile(os.path.join(pic_dir, nm)):
                    cand = os.path.join(pic_dir, nm)
                    break
            if cand:
                break
        if not cand or not pool:
            return (pool[0] if pool else ""), "无场景 CG ⇒ 池内补件（待核）"
        if cand in _photo_cache:
            return _photo_cache[cand]
        base = Image.open(cand).convert("RGB").resize((48, 96), Image.LANCZOS)
        best, bn = 1e9, pool[0]
        for n in pool:
            c = Image.open(os.path.join(sys_dir, n)).convert("RGB")
            s2 = max(48 / c.size[0], 96 / c.size[1])
            c2 = c.resize((max(int(c.size[0] * s2), 1), max(int(c.size[1] * s2), 1)), Image.LANCZOS)
            ox, oy = (c2.size[0] - 48) // 2, (c2.size[1] - 96) // 2
            d2 = ImageChops.difference(c2.crop((ox, oy, ox + 48, oy + 96)), base).convert("L")
            v = sum(i * nn for i, nn in enumerate(d2.histogram())) / (48 * 96)
            if v < best:
                best, bn = v, n
        _photo_cache[cand] = (bn, "场景 CG %s 择优 SAD=%.1f（待核）" % (os.path.basename(cand), best))
        return _photo_cache[cand]

    def compose_card(scene):
        """EC28 → 分件合成整卡（沿用旧产物路径/命名）。返回 (dst_name, w, h, why) 或 None。"""
        ch, ch_why = chapter_of(scene)
        gd, _ = meta.get(scene, (None, []))
        mmdd = ""
        if gd and "/" in gd:
            mm, dd = gd.split("/")[:2]
            try:
                mmdd = "%02d%02d" % (int(mm), int(dd))
            except ValueError:
                mmdd = ""
        if not (ch and os.path.isfile(os.path.join(sys_dir, "ot_ec%d_bg.png" % ch))):
            return None
        photo, ph_why = pick_photo(scene)
        dst_name = "ec__card_%s.png" % scene
        notes = []
        if not quiet:
            notes = _ec.compose(ch, mmdd, os.path.join(sys_dir, photo), sys_dir,
                                os.path.join(assets_dir, dst_name))
        why = "EC28 整卡合成：章%d（%s）｜日期%s｜照片%s（%s）%s" % (
            ch, ch_why, mmdd or "（无，语料未标）", photo, ph_why,
            ("｜备注：" + "；".join(notes)) if notes else "")
        return dst_name, 1920, 1080, why

    # ---- 逐场取**首个可实现** EyeCatch（Major-1 别名 + Major-2 判据）----
    ec_by_scene = load_psv_eyecatch(psv_dir)
    n_scenes_all = len(ec_by_scene)

    def row_parts(r):
        return [x.strip() for x in (r.get("image") or "").split(",")]

    def row_mode(r):
        p = row_parts(r)
        return p[0] if p else ""

    def row_seq(r):
        try:
            return int((r.get("seq") or "0").strip() or "0")
        except ValueError:
            return 0

    def scene_rows(scene):
        """本场的全部 EyeCatch 行（含**别名来源**；依据见 `SCENE_ALIAS`）。"""
        rows = list(ec_by_scene.get(scene, []))
        al = SCENE_ALIAS.get(scene)
        if al:
            rows += list(ec_by_scene.get(al[0], []))
        return rows

    def card_available(card, scene):
        """该卡能否落成实件：EC28 需 ot 题卡套件（`ot_ec<章>_bg.png`）；其余需交付层件。"""
        if card == 28:
            ch, _ = chapter_of(scene)
            return bool(ch and os.path.isfile(os.path.join(sys_dir, "ot_ec%d_bg.png" % ch)))
        return find_delivery_ec(deliv, card) is not None

    def pick_implementable(rows, scene):
        """Major-2：按 (seq, 文件序) 取**首个可实现**卡——
        跳过非 mode0、`N=-1`、越界、缺件；整场无可实现卡返回 None。"""
        for _i, r in sorted(enumerate(rows), key=lambda t: (row_seq(t[1]), t[0])):
            if row_mode(r) != "0":
                continue
            p = row_parts(r)
            n = p[1] if len(p) >= 2 else ""
            if str(n) == "-1":
                continue
            card = ec_from_n(n)
            if card is None:
                continue
            if not card_available(card, scene):
                continue
            return r, card
        return None

    def classify_no_card(rows):
        modes = [row_mode(r) for r in rows]
        m0 = [row_parts(r) for r, m in zip(rows, modes) if m == "0"]
        if not m0:
            return ("全 mode1（leading mode1 且无 mode0）" if modes and all(m == "1" for m in modes)
                    else "无 mode0（含未知模式）")
        ns = [(p[1] if len(p) >= 2 else "") for p in m0]
        if all(str(n) == "-1" for n in ns):
            return "全 N=-1"
        if not any(ec_from_n(n) is not None for n in ns):
            return "N 越界"
        return "件缺"

    # 候选＝(PSV 有 EyeCatch 或 别名可用) 且 在本次构建集
    cand = [s for s in sorted(set(ec_by_scene) | set(SCENE_ALIAS))
            if (scene_ids is None or s in scene_ids) and scene_rows(s)]
    n_skip_scene = len([s for s in ec_by_scene if scene_ids is not None and s not in scene_ids])
    alias_used = set(SCENE_ALIAS[s][0] for s in SCENE_ALIAS if s in cand)

    keys, vals, ws, hs, seqs, tsv = [], [], [], [], [], []
    n_compose = n_deliv = n_missing = n_alias = n_fallback = n_nocard = n_mode1_rows = 0
    nocls = {}
    for scene in cand:
        rows = scene_rows(scene)
        al = SCENE_ALIAS.get(scene)
        n_mode1_rows += sum(1 for r in rows if row_mode(r) == "1")
        got = pick_implementable(rows, scene)
        if got is None:
            n_nocard += 1
            c = classify_no_card(rows)
            nocls[c] = nocls.get(c, 0) + 1
            r0 = sorted(rows, key=row_seq)[0]
            tsv.append((scene, str(row_seq(r0)), row_mode(r0), "-", "PSV", "（无）",
                        "无**可实现**卡（%s）：同场无可取件的 mode0 ⇒ 不插点%s"
                        % (c, ("（别名来源 %s）" % al[0]) if al else "")))
            continue
        r, card = got
        sq = row_seq(r)
        p0 = row_parts(r)
        n = p0[1] if len(p0) >= 2 else ""
        note_al = ("｜别名：构建集场对应 PSV `%s`（%s·剧情审计_重复场景.tsv 完全重复/相似度1.0）"
                   % (al[0], al[1])) if al else ""
        if card == 28:
            got2 = compose_card(scene)
            if got2 is None:
                n_missing += 1
                tsv.append((scene, str(sq), "0", "EC28", "PSV", "（无）",
                            "EC28 合成所需 ot 题卡套件缺失（`ot_ec<章>_bg.png`）⇒ 登记缺件，不编造" + note_al))
                continue
            dst_name, w, h, why = got2
            n_compose += 1
        else:
            p = find_delivery_ec(deliv, card)
            if not p:
                n_missing += 1
                tsv.append((scene, str(sq), "0", "EC%02d" % card, "PSV", "（无）",
                            "交付层无 `ec%02d.*` 对应件 ⇒ 登记缺件，不编造" % card + note_al))
                continue
            base = os.path.splitext(os.path.basename(p))[0]
            dst_name = "ec__" + base + os.path.splitext(p)[1]
            if not quiet:
                os.makedirs(assets_dir, exist_ok=True)
                shutil.copyfile(p, os.path.join(assets_dir, dst_name))
            why = "EC%02d 直接取交付层件 `%s`（归档序 N=%s → EC%02d，映射结论 §A.1）" % (
                card, os.path.relpath(p, deliv), n, card)
            n_deliv += 1
            w, h = img_size(p)
            if w <= 0:
                n_missing += 1
                continue
        if al:
            n_alias += 1
        keys.append('"%s"' % scene)
        seqs.append(str(sq))
        vals.append('"eyecatch/%s"' % dst_name)
        ws.append(str(w))
        hs.append(str(h))
        tsv.append((scene, str(sq), "0", "EC%02d" % card, "PSV+别名" if al else "PSV",
                    dst_name, why + note_al))

    # ---- 兜底插点（用户 2026-10-06 裁定）：PSV 无 `EyeCatch` 覆盖的 np/ota 5 场保留旧表插点 ----
    fb_cards = load_fallback_cards(res_root)
    for scene in FALLBACK_SCENES:
        if scene_ids is not None and scene not in scene_ids:
            continue
        if scene in cand:                       # PSV 有 EyeCatch ⇒ 一律以 PSV 为准，不兜底
            continue
        sq = 1                                  # 场景首行 sq（本作全部场 sq=1..N 连续）
        fb = fb_cards.get(scene)
        if fb is None:
            n_nocard += 1
            k = "兜底源缺件（素材引用映射无 CG背景/ec 行）"
            nocls[k] = nocls.get(k, 0) + 1
            tsv.append((scene, "1", "0", "-", "旧表兜底", "（无）",
                        "旧表兜底：`素材引用映射.tsv` 无该场 `CG背景/ec*` 行 ⇒ 登记、不插点"))
            continue
        card, deliv_rel = fb
        note = ("｜兜底：用户 2026-10-06 裁定保留旧表插点（PSV 无 EyeCatch 覆盖）｜"
                "来源 资源组\\交接编程组\\素材引用映射.tsv `%s`（样例场景＝本场）｜seq=%d（场景首行 sq）"
                % (deliv_rel, sq))
        if card == 28:
            got2 = compose_card(scene)
            if got2 is None:
                n_missing += 1
                tsv.append((scene, str(sq), "0", "EC28", "旧表兜底", "（无）",
                            "EC28 合成所需 ot 题卡套件缺失 ⇒ 登记缺件，不编造" + note))
                continue
            dst_name, w, h, why = got2
            n_compose += 1
        else:
            p = find_delivery_ec(deliv, card)
            if not p:
                n_missing += 1
                tsv.append((scene, str(sq), "0", "EC%02d" % card, "旧表兜底", "（无）",
                            "交付层无 `ec%02d.*` 对应件 ⇒ 登记缺件，不编造" % card + note))
                continue
            base = os.path.splitext(os.path.basename(p))[0]
            dst_name = "ec__" + base + os.path.splitext(p)[1]
            if not quiet:
                os.makedirs(assets_dir, exist_ok=True)
                shutil.copyfile(p, os.path.join(assets_dir, dst_name))
            why = "EC%02d 兜底取交付层件 `%s`" % (card, os.path.relpath(p, deliv))
            n_deliv += 1
            w, h = img_size(p)
            if w <= 0:
                n_missing += 1
                continue
        n_fallback += 1
        keys.append('"%s"' % scene)
        seqs.append(str(sq))
        vals.append('"eyecatch/%s"' % dst_name)
        ws.append(str(w))
        hs.append(str(h))
        tsv.append((scene, str(sq), "0", "EC%02d" % card, "旧表兜底", dst_name, why + note))

    tsv.sort(key=lambda t: (t[0], int(t[1])))

    body = ["// 生成物（build_story.py → emit_eyecatch.py · B3/ISSUE-20261006-04）——勿手改：章节过场卡插点",
            "// 插点键＝(场景, seq)：seq 为**我方语料 lines[].seq**（PSV 金标），按 seq 在弹出位置弹；",
            "//   `seqs` 与 keys 同序；运行期 ui_story.tjs 的 uiStoryEcOnLine() 按当前行 seq 触发。",
            "// 形式：只定义 uiEyecatchFill(o)（TJS2 跨存储给全局赋值会抛「未找到 Member」）",
            "function uiEyecatchFill(o)",
            "{",
            "\to.keys = [" + ",".join(keys) + "];",
            "\to.seqs = [" + ",".join(seqs) + "];",
            "\to.imgs = [" + ",".join(vals) + "];",
            "\to.ws   = [" + ",".join(ws) + "];",
            "\to.hs   = [" + ",".join(hs) + "];",
            "\treturn o.keys.count;",
            "}"]
    if not quiet:
        os.makedirs(story_dir, exist_ok=True)
        with io.open(os.path.join(story_dir, "_eyecatch.tjs"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(body) + "\n")
        # ★ 以**本次生成集**为准剪枝：删除上一轮残留的 `ec__*`（如旧 PC 33 插点产物）——
        #   否则与 B3 的 PSV 去重集并存，既不显示也污染产物目录（story/ 同法已有剪枝）。
        #   ★ Minor-1 护栏：**只在全量构建才剪**——单场/子集切片（`run_storytest --scenes 单场`）
        #   会把源树 `krkr\game\eyecatch\` 收窄到该切片，而 `deploy_product.py` 对 eyecatch 无闸门。
        if not full:
            log("[eyecatch] 子集构建（非全量）⇒ **跳过** `ec__*` 剪枝"
                "（护栏：避免把 eyecatch\\ 收窄到切片；部署前须先跑一次全量构建）")
        elif os.path.isdir(assets_dir):
            _keep = set(os.path.basename(v.strip('"').replace("eyecatch/", "")) for v in vals)
            _rm = 0
            for f3 in os.listdir(assets_dir):
                if f3.startswith("ec__") and f3 not in _keep:
                    try:
                        os.remove(os.path.join(assets_dir, f3))
                        _rm += 1
                    except OSError:
                        pass
            log("[eyecatch] 全量构建 ⇒ 已按本次生成集剪枝 `ec__*`（删残留 %d 件 / 保留 %d 件）"
                % (_rm, len(_keep)))
        if tsv_path:
            with io.open(tsv_path, "w", encoding="utf-8", newline="") as f:
                f.write("场景\tseq\t模式\tEC号\t来源\t产物\t依据\n")
                for r in tsv:
                    f.write("\t".join(r) + "\n")
        for d in also:
            os.makedirs(d, exist_ok=True)
            for f2 in os.listdir(assets_dir):
                if f2.startswith("ec__"):
                    shutil.copyfile(os.path.join(assets_dir, f2), os.path.join(d, f2))

    # 汇总**始终打印**（--check 也要看各计数）；逐条 warn 仍受 quiet 控制。
    print("[eyecatch] PSV EyeCatch %d 场（构建集外跳过 %d，其中别名复用 %d）｜ 可玩候选 %d 场 ｜ 去重后插点 %d"
          % (n_scenes_all, n_skip_scene, len(alias_used), len(cand), len(keys)))
    print("  EC28 合成 %d ｜ 其他卡号交付层件 %d ｜ 缺件登记 %d ｜ 别名补入 %d ｜ 旧表兜底补入 %d"
          % (n_compose, n_deliv, n_missing, n_alias, n_fallback))
    print("  无可实现卡 %d 场：%s ｜ 跳过登记的 mode1 行 %d 条（动画卡，`s`/`f` 语义未判读）"
          % (n_nocard, "、".join("%s %d" % (k, nocls[k]) for k in sorted(nocls)) or "（无）",
             n_mode1_rows))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--res", default=RES)
    ap.add_argument("--psv", default="")
    ap.add_argument("--story", default=os.path.join(PROJ, "编程组", "krkr", "game", "story"))
    ap.add_argument("--assets", default=os.path.join(PROJ, "编程组", "krkr", "game", "eyecatch"))
    ap.add_argument("--also", action="append", default=[])
    ap.add_argument("--tsv", default=os.path.join(PROJ, "编程组", "章节过场卡插点.tsv"))
    a = ap.parse_args()
    return emit(a.story, a.assets, a.res, a.also, a.tsv, quiet=a.check,
                psv_dir=(a.psv or None), scene_ids=None)


if __name__ == "__main__":
    sys.exit(main())
