# -*- coding: utf-8 -*-
r"""psv_build_d_screens.py —— D 鉴赏四页（27/28/37/38）＋ 外壳（39）PSV 深度换皮：**布局数据重排**。

Issue：`ISSUE-20260926-06`（PSV 系统 UI 换皮 · D 组）｜ 一次性脚手架（照 `A基础组三屏换皮` 先例，
落在 `_工作\...\复现脚本\`，不入 `工具\`，因为屏数据此后手工维护、本脚本不再重跑）。

**做什么**（派单：深度换皮 —— 底图换 PSV 件，我方内容按 PSV 实测版式常量重排）：
1. 27/28/37/38 各加一件**全屏 PSV 底图元素**（`x_ui_psv_{gal_shell,music_bg,dress_bg,replay_bg}.png`，
   **1920×1080 ⇒ 1:1 无 nine**；素材已在库，**零新增体积**）；同时**删除 `xx.dim`**
   （原「透明浮层 + 薄压暗」的前提消失：PSV 底图逐像素 alpha=255，压暗已无意义）。
2. 39 外壳 `gs.strip` → 新拆件 `x_ui_psv_shell_strip.png`（横幅带 1580×100，(340,0)，见
   `工具\psv_make_shell_strip.py`）；四个页签的文字/热区/选中指示与返回键**机制与 action 一字未改**，
   仅几何随条带重排。
3. 逐屏几何依据、未决点与缺口见交付报告（本脚本只落盘数据）。

**幂等**：目标值全部由本文件常量 ＋ `备份_改前\` 的**原始坐标**推出（**不做「当前值 + 偏移」**，
那种写法每跑一次都会再平移一次）；`add_bg` / `drop_dim` / 页码文本增删与屏 `note` 追加都带存在性判定
⇒ **重复运行结果逐字节相同**（实跑两次 md5 一致）。前提：`备份_改前\` 五份改前屏数据在案
（缺文件即报错退出，不会静默按当前值猜）。
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)                      # _工作\ISSUE-..._D鉴赏四页换皮
UI = os.path.dirname(os.path.dirname(WORK))       # <UI组>
SCR = os.path.join(UI, "layout", "screens")

# ---------------- 27: CG 网格新常量 ----------------
GAL_CELL_W, GAL_CELL_H, GAL_GAP = 240, 137, 21
GAL_COLS, GAL_ROWS = 7, 4
GAL_X, GAL_Y = 57, 230          # 187 + (697 − 611)/2（在 PSV CG 滚动区内垂直居中）
GAL_PER_PAGE = GAL_COLS * GAL_ROWS
GAL_THUMB = (2, 2, 236, 133)    # 栏位内缩 2px；236/287 = 0.822 等比（全零 nine 缩放）
GAL_PREV = (5, 51, 26, 34)
GAL_NEXT = (GAL_CELL_W - 5 - 26, 51, 26, 34)
GAL_VTEXT = (GAL_CELL_W - 2 - 56, GAL_CELL_H - 2 - 22, 56, 22)

# ---------------- 28: PSV 列表框 / 信息框（bg 实测） ----------------
MUS_BOX = (156, 477, 1607, 473)
MUS_INFO_Y0 = 223
MUS_ITEM_W, MUS_ITEM_H, MUS_GAP = 526, 59, 1
MUS_COLS, MUS_ROWS = 3, 7
MUS_LIST_X = MUS_BOX[0] + (MUS_BOX[2] - (MUS_COLS * MUS_ITEM_W + (MUS_COLS - 1) * MUS_GAP)) // 2
MUS_LIST_Y = MUS_BOX[1] + (MUS_BOX[3] - (MUS_ROWS * MUS_ITEM_H + (MUS_ROWS - 1) * MUS_GAP)) // 2
MUS_KEYS_Y = MUS_INFO_Y0 + 30
MUS_SLIDER_Y = 385

# ---------------- 37: PSV 缩略网格单元宽 + 隙 ----------------
DRE_NAME_UNIT_W, DRE_GAP = 182, 21
DRE_PANEL_X = DRE_NAME_UNIT_W + DRE_GAP          # 203

# ---------------- 38: PSV 影像槽 ----------------
REP_PREVIEW = (88, 215, 542, 702)   # PSV 左栏「上排槽 1 ＋ 下排槽」合并区（1×：542×(309+84+309)）
REP_CELL_W, REP_CELL_H, REP_GAP = 271, 152, 21
REP_COLS, REP_ROWS = 4, 4
REP_X, REP_Y = 680, 208
REP_PER_PAGE = REP_COLS * REP_ROWS
REP_THUMB = (2, 2, 265, 121)
REP_PREV = (5, 45, 26, 34)
REP_NEXT = (REP_CELL_W - 5 - 26, 45, 26, 34)

# ---------------- 39: 外壳条带与页签 ----------------
SHELL_STRIP = (340, 0, 1580, 100)
SHELL_TAB_Y, SHELL_TAB_H = 12, 76
SHELL_TAB_W = [171, 220, 258, 229]
SHELL_TAB_GAP = 10
SHELL_TAB_X0 = 360
SHELL_TITLE = (1290, 22, 300, 56)
SHELL_BACK = (1660, 22, 230, 56)

PAGE_TX = (858, 939, 204, 56)
OUTLINE = {"outline": True, "outline_color": "@palette.shadow", "outline_width": 2}
PAGE_TX_DARK = {"color": "@palette.node_locked", "bold": True}

PSV_BG = {
    "gal": ("gal.bg", "x_ui_psv_gal_shell.png",
            "27 CG 鉴赏页底（PSV gm_bg1 屏区：霜页 + 英文题 ALBUM + 页脚）"),
    "mu":  ("mu.bg", "x_ui_psv_music_bg.png",
            "28 BGM 鉴赏页底（PSV mu_bg 屏区：MUSIC + 播放条 + 信息框 + 列表框 + 滚动条）"),
    "dr":  ("dr.bg", "x_ui_psv_dress_bg.png",
            "37 立绘鉴赏页底（PSV gm_bg 屏区：霜页 + 英文题 ALBUM）"),
    "rp":  ("rp.bg", "x_ui_psv_replay_bg.png",
            "38 情景回想页底（PSV mv_bg 屏区：MOVIE + 4 个带框空槽 542×309）"),
}
DIM_ID = {"gal": "gal.dim", "mu": "mu.dim", "dr": "dr.dim", "rp": "rp.dim"}

NOTE_MARK = "\n★ **PSV 深度换皮（2026-09-26 · ISSUE-20260926-06 · D 组）**"
NOTES = {
    "27_gallery.json": (
        "：① 底图换 `ui/x_ui_psv_gal_shell.png`（PSV ALBUM 屏区，1:1，1920×1080）；"
        "删 `gal.dim`（PSV 底图逐像素不透明 ⇒ 压暗无意义）。"
        "② 网格按 PSV 结构常量重算：单元 **240×137**（宽高比 1.752 ≈ PSV 影像槽 271:152 = 1.783）、"
        "隙 **21**（PSV 缩略网格实测）、**7 列 × 4 行 = 28 栏/页** ⇒ 286 栏 = **11 页**"
        "（原 6×4 = 24 栏/页 · 12 页）。列数由「隙 21 + PSV CG 滚动区实宽 1806」反解："
        "**7×240 + 6×21 = 1806 精确**；网格外框 1806×611 @ (57,230)（滚动区 187..884 内垂直居中）。"
        "③ `item_variants` 全套保持（`frames` 286 行 / `thumb` (2,2,236,133) + 全零 nine / "
        "`prev`·`next` 26×34 / `n/N` 文本 (182,113,56,22) / `edge:\"clamp\"`）；"
        "栏位底板 `x_ui_gal_cell_*.png`（291×166）随格体改 240×137（全零 nine 等比 0.82×，件不变形）；"
        "**703 张 `x_gal_c*.png` 原样复用**（287×162 经全零 nine 在渲染期等比缩到 236×133 = 0.822×，"
        "**不改素材、不改名**）。④ 页码互斥文本随页数改为 `gal.page_tx_01..11`；"
        "页码文字改深墨 `@palette.node_locked`（底图由深色剧情画面变为浅色霜页 ⇒ 原浅色白字不可读）。"),
    "28_music.json": (
        "：① 底图换 `ui/x_ui_psv_music_bg.png`（PSV MUSIC 屏区，1:1）；删 `mu.dim`。"
        "② `mu.list` 落入 PSV **列表框**（bg 实测 156..1762 × 477..950）内 ⇒ (169,504,1580,419)；"
        "单元/行距**不变**（526×59 · 隙 1 · 行距 60 = PSV 实测行距 30@1×⇔60@2×），列数 3、"
        "行数 10 → **7**（473 高的框内 7×60 = 420 ≤ 473；8 行 = 480 > 473）⇒ **21 首/页 ⇒ 3 页**"
        "（原 30 首/页 · 2 页）。③ 8 个播放控制键整体移入 PSV **信息框**（bg 实测 156..1762 × 223..440）内"
        "（y831 → 253），音量滑块随之下移（y907 → 385）——**刻意避开 PSV 播放条（y102..184）的"
        "烘焙走带图标**，不与其叠画（播放条保留为 PSV chrome）。`bgm_*` 八个动作名、`page_flag`、"
        "逐项三态 `item_frame`、行内播放键 `item_buttons`（`bgm_play:%row%`）**一字未改**。"
        "④ 页码互斥文本 2 → 3 件（`mu.pg_tx_1..3`）；页码文字改深墨（PSV 霜页为浅底）。"
        "⑤ 已知缺口（如实登记）：页面上会同时出现「PSV 播放条烘焙图标」与「我方 8 控制键」"
        "两处走带控件观感；若需消除，可把控制键直接压在播放条上（几何已备，见交付报告未决点）。"),
    "37_dress.json": (
        "：① 底图换 `ui/x_ui_psv_dress_bg.png`（PSV 立绘页屏区霜页，1:1，含英文题 ALBUM）；删 `dr.dim`。"
        "② 整页让出外壳条带（y0..100）后重排：控制条 `dr.ctrl` y114→**160**（其 11 个热区同步 +46）、"
        "初始化键 `dr.reset`/`dr.reset_tx`/`dr.hit_reset` y33→**160**（右侧与控制条同行）。"
        "③ 左栏按 PSV 缩略网格**单元宽 182 ＋ 隙 21** 重设：`dr.namelist` **(0,212,182,420)**"
        "（= 7 行 × 60，行步进仍取参考作 `名前/#rect` step 60），7 行文字/热区随之下移 +28、"
        "文字框宽 192→148（落在单元内）；**面板左沿 = 182+21 = 203**（与 PSV 网格模块对齐）。"
        "④ 主面板 `dr.big` (204,164) → **(203,212)**（尺寸 782×386 不变；面板内 56 件按钮/标签"
        "整体 (dx,dy) = (-1,+48)，**相对关系零改动**）。⑤ **36 个 hit 与 31 个 text 一件不少**"
        "（脚本内断言），action 仍为空串；`dr.face_tx` 文字色改深墨（PSV 霜页/浅板为浅底，"
        "原浅色白字不可读）。⑥ 如实登记：PSV 立绘页的 **8 列缩略网格不在本件屏区内**"
        "（实测其位于源件 y≥1088 的长卷段，本工程 1:1 入库件只取屏区 0..1080）⇒ 本轮只把网格的"
        "**单元宽 182 / 隙 21** 用作左栏模块常量，「立绘缩略列」观感参照来自该网格的实测几何，"
        "而非本件像素。"),
    "38_replay.json": (
        "：① 底图换 `ui/x_ui_psv_replay_bg.png`（PSV MOVIE 屏区，1:1，含 4 个带框空槽 542×309 与页脚）；"
        "删 `rp.dim`。② `rp.preview` → **PSV 影像槽原址 (88,215,542,309)**（与底图左上槽框同位 ⇒ "
        "不留双框）。③ `rp.list` 单元取 PSV 影像槽 1× 口径 **271×152**（= 542×304 @2× ÷ 2）、"
        "隙 **21**（PSV 缩略网格实测）、**4 列 × 4 行 = 16 栏/页 ⇒ 4 页**（原 5×5 = 25 栏/页 · 2 页），"
        "网格外框 1147×671 @ (680,208)。④ `item_variants` 保持：`frames` 35 行（第 0..24 行显式空数组、"
        "25..34 行 10 件动画 `replay_play:25..34`、35..49 行索引越界留空）、`thumb` (2,2,265,121) + 全零 nine、"
        "`prev`/`next` 26×34、`edge:\"clamp\"`；`item_text` 占位标签槽随格体放大到 (5,125,261,25)；"
        "栏位底板 `x_ui_rp_cell_*.png`（234×133）随格体改 271×152（全零 nine 1.16×/1.14×）。"
        "⑤ 页码互斥文本 2 → 4 件（`rp.pg_tx_1..4`）。⑥ 如实登记：`list` 的 `gap` 是**单一值**"
        "（横纵同隙），而 PSV 槽框横隙 58 / 纵隙 84 不等 ⇒ **我方网格与底图槽框无法逐格对齐**"
        "（本屏取「1× 槽尺寸 + 网格隙 21」的观感口径），底图槽框线与「?」占位会在格间露出，"
        "属已知观感差异。"),
    "39_gal_shell.json": (
        "：`gs.strip` 换为从 `ui/x_ui_psv_gal_shell.png`（PSV ALBUM 屏区）裁出的**横幅带** "
        "`ui/x_ui_psv_shell_strip.png`（1580×100 @ (340,0)，1:1 无 nine；拆件脚本 "
        "`工具\\psv_make_shell_strip.py`，5.3 KB）。**四个页签的文字 / 热区 / 选中指示与返回键："
        "机制、`vis_*`、action（`gallery_tab_1..4` / `close`）一律未改**，仅几何随条带重排"
        "（页签自 x360 起、条带中心线 y50 居中、宽度照参考作实测 171/220/258/229 保持）；"
        "标题与返回键移入条带右段。文字统加 2px 深色描边：PSV 横幅带是**浅底**（实测行均亮度 197..213）"
        "而原设计是深底浅字 ⇒ 描边让同一件文字在两个底色上都可读（描边是渲染层机件、不参与布局、"
        "不改行数与断行）。★ 元素总数仍 17（条带 1 ＋ 页签 12 ＋ 标题 1 ＋ 返回 3）、热区仍 5 ⇒ "
        "巡演 `galattach` 的「每个热区在自身中心被真实命中」口径不变。"),
}


def load(name):
    with open(os.path.join(SCR, name), encoding="utf-8") as f:
        return json.load(f)


def save(d, name):
    p = os.path.join(SCR, name)
    raw = open(p, "rb").read()
    crlf = b"\r\n" in raw
    s = json.dumps(d, ensure_ascii=False, indent=2)
    if crlf:
        s = s.replace("\n", "\r\n")
    s += "\r\n" if crlf else "\n"
    with open(p, "wb") as f:
        f.write(s.encode("utf-8"))
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def by_id(d):
    return {e["id"]: e for e in d["elements"]}


BACKUP = os.path.join(WORK, "备份_改前")     # 改前原始屏数据（git 亦可还原，见交付报告「回滚方式」）


def pristine(name):
    """读**改前原始**屏数据（只用于取原始坐标 ⇒ 本脚本的平移量一律以原始值为基准，
    而非「当前值 + 偏移」——后者每跑一次都会再平移一次，不是幂等）。"""
    p = os.path.join(BACKUP, name)
    with open(p, encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)["elements"]}


def add_note_once(d, name):
    head = NOTE_MARK + NOTES[name]
    i = d["note"].find(NOTE_MARK)
    d["note"] = (d["note"][:i] if i >= 0 else d["note"]) + head


def add_bg(d, key):
    eid, asset, note = PSV_BG[key]
    dim_id = DIM_ID[key]
    el = {
        "id": eid, "kind": "image", "z": 0, "visible_default": True,
        "asset": "ui/" + asset, "x": 0, "y": 0, "w": 1920, "h": 1080, "opacity": 255,
        "source": "PSV系统UI参考\\超分2x\\%s（经 工具\\m53_psv_ui_assets.py 屏区裁切入库，1:1）" % asset,
        "note": (note + "。★ **PSV 换皮（2026-09-26 · ISSUE-20260926-06 · D 组）**：本屏原为"
                 "「透明浮层 + `" + dim_id + "` 薄压暗」，本轮按用户裁决「深度换皮：底图换 PSV 件」"
                 "改为**不透明全屏 PSV 底图**（逐像素 alpha=255，实测）⇒ 原压暗遮罩随本轮删除。"
                 "底图与元素同为 1920×1080 ⇒ **1:1 无 nine**（`verify_ui [2]` 直接成立）。"
                 "英文题字（ALBUM/MUSIC/MOVIE）与页脚按用户裁决**保留原样**（页脚属待定区，本轮不处理）。"),
    }
    old = by_id(d).get(eid)
    if old is not None:                      # 幂等：已在盘面 ⇒ 原地更新
        old.update(el)
        return old
    d["elements"].insert(0, el)
    return el


def drop_dim(d, dim_id):
    if dim_id in by_id(d):                   # 幂等：删过即无操作
        d["elements"] = [e for e in d["elements"] if e["id"] != dim_id]
    assert dim_id not in by_id(d), "dim 未删除：" + dim_id


def upsert_pg_tx(d, tpl, eid, after_id, **fields):
    """页码互斥文本的幂等增改：不存在则插到 after_id 之后，存在则原地更新。"""
    el = by_id(d)
    if eid in el:
        el[eid].update(fields)
        return el[eid]
    t = json.loads(json.dumps(tpl))
    t["id"] = eid
    t.update(fields)
    d["elements"].insert(d["elements"].index(el[after_id]) + 1, t)
    return t


def page_tx_note(v, n):
    return ("页码指示（引擎绘制，几何 858,939,204×56 与四页统一）。"
            "★ PSV 换皮（2026-09-26 · D 组）：本屏共 **%d 页**，本件 = 第 %s 页"
            "（`vis_flag` 与屏级 `page_flag` 不变）；文字色改深墨 `@palette.node_locked`"
            "（PSV 霜页为浅底）。" % (n, v))


# ============================================================
def build_gallery():
    d = load("27_gallery.json")
    drop_dim(d, "gal.dim")
    add_bg(d, "gal")
    el = by_id(d)
    lst = el["gal.list"]
    lst["x"], lst["y"] = GAL_X, GAL_Y
    lst["w"] = GAL_COLS * GAL_CELL_W + (GAL_COLS - 1) * GAL_GAP
    lst["h"] = GAL_ROWS * GAL_CELL_H + (GAL_ROWS - 1) * GAL_GAP
    lst["item_w"], lst["item_h"], lst["gap"] = GAL_CELL_W, GAL_CELL_H, GAL_GAP
    lst["max_cols"], lst["max_rows"] = GAL_COLS, GAL_ROWS
    lst["scroll"]["page_size"] = GAL_PER_PAGE
    lst["item_frame"]["nine"] = {"l": 0, "t": 0, "r": 0, "b": 0}
    assert len(lst["labels"]) == 286 and len(lst["actions"]) == 286
    vv = lst["item_variants"]
    assert len(vv["frames"]) == 286 and all(len(r) >= 1 for r in vv["frames"])
    vv["thumb"] = {"x": GAL_THUMB[0], "y": GAL_THUMB[1], "w": GAL_THUMB[2], "h": GAL_THUMB[3],
                   "nine": {"l": 0, "t": 0, "r": 0, "b": 0}}
    vv["prev"].update(dict(zip(("x", "y", "w", "h"), GAL_PREV)))
    vv["next"].update(dict(zip(("x", "y", "w", "h"), GAL_NEXT)))
    vv["text"].update(dict(zip(("x", "y", "w", "h"), GAL_VTEXT)))
    pages = (286 + GAL_PER_PAGE - 1) // GAL_PER_PAGE          # = 11
    t1 = el["gal.page_tx_01"]
    for n in range(1, pages + 1):
        eid = "gal.page_tx_%02d" % n
        assert eid in el, eid
        el[eid].update(dict(zip(("x", "y", "w", "h"), PAGE_TX)))
        el[eid]["font"].update(PAGE_TX_DARK)
        el[eid]["vis_when"] = str(n)
        el[eid]["sample"] = "%d / %d" % (n, pages)
        el[eid]["note"] = page_tx_note(str(n), pages)
    del t1
    d["elements"] = [e for e in d["elements"] if e["id"] != "gal.page_tx_12"]
    d["page_flag"] = "gal_page"
    d["flags_default"] = {"gal_page": "1"}
    add_note_once(d, "27_gallery.json")
    return save(d, "27_gallery.json")


def build_music():
    d = load("28_music.json")
    drop_dim(d, "mu.dim")
    add_bg(d, "mu")
    el = by_id(d)
    lst = el["mu.list"]
    lst["x"], lst["y"] = MUS_LIST_X, MUS_LIST_Y
    lst["w"] = MUS_COLS * MUS_ITEM_W + (MUS_COLS - 1) * MUS_GAP
    lst["h"] = MUS_ROWS * MUS_ITEM_H + (MUS_ROWS - 1) * MUS_GAP
    lst["max_cols"], lst["max_rows"] = MUS_COLS, MUS_ROWS
    lst["scroll"]["page_size"] = MUS_COLS * MUS_ROWS
    assert len(lst["labels"]) == 59
    P = pristine("28_music.json")
    for e in d["elements"]:
        eid = e["id"]
        if eid.startswith("mu.pb_") and e["kind"] in ("image", "hit"):
            assert P[eid]["y"] == 831, eid              # 原始 8 键同一行 ⇒ 目标同为 MUS_KEYS_Y
            e["y"] = MUS_KEYS_Y
        elif eid == "mu.vol":
            assert P[eid]["y"] == 907, eid
            e["y"] = MUS_SLIDER_Y
        elif eid == "mu.vol_hit":
            assert P[eid]["y"] == 898, eid
            e["y"] = MUS_SLIDER_Y - 9
    n = 3                                              # 59 首 / 21 首每页 = 2.81 ⇒ 3 页
    el["mu.pg_tx_1"].update(dict(zip(("x", "y", "w", "h"), PAGE_TX)))
    el["mu.pg_tx_1"]["font"].update(PAGE_TX_DARK)
    for v in ("1", "2"):
        e = el["mu.pg_tx_%s" % v]
        e["vis_when"] = v
        e["sample"] = "%s / %d" % (v, n)
        e["note"] = page_tx_note(v, n)
    upsert_pg_tx(d, el["mu.pg_tx_2"], "mu.pg_tx_3", "mu.pg_tx_2",
                 x=PAGE_TX[0], y=PAGE_TX[1], w=PAGE_TX[2], h=PAGE_TX[3],
                 font=dict(el["mu.pg_tx_2"]["font"]), vis_flag="music_page", vis_when="3",
                 sample="3 / %d" % n, note=page_tx_note("3", n),
                 **{"kind": "text", "z": 31, "visible_default": True, "align": "center",
                    "valign": "middle", "wrap": False, "max_lines": 1})
    assert by_id(d)["mu.pg_tx_1"]["vis_flag"] == "music_page"
    d["page_flag"] = "music_page"
    d["flags_default"] = {"music_page": "1"}
    add_note_once(d, "28_music.json")
    return save(d, "28_music.json")


def build_dress():
    d = load("37_dress.json")
    drop_dim(d, "dr.dim")
    add_bg(d, "dr")
    P = pristine("37_dress.json")
    for e in d["elements"]:
        i = e["id"]
        if i == "dr.bg":
            continue
        pe = P[i]                                  # 目标一律由**原始坐标**推出（幂等）
        if i == "dr.namelist":
            t = (0, 212, DRE_NAME_UNIT_W, 420)
        elif i.startswith("dr.name_tx_"):
            t = (34, 209 + 60 * (int(i.rsplit("_", 1)[1]) - 1), 148, pe["h"])
        elif i.startswith("dr.hit_name_"):
            t = (0, 209 + 60 * (int(i.rsplit("_", 1)[1]) - 1), DRE_NAME_UNIT_W, pe["h"])
        elif i == "dr.sel_mark":
            t = (pe["x"], 221, pe["w"], pe["h"])
        elif i in ("dr.reset", "dr.reset_tx", "dr.hit_reset"):
            t = (pe["x"], 160, pe["w"], pe["h"])
        elif i == "dr.ctrl" or i.startswith("dr.hit_ctrl_") or i.startswith("dr.time_"):
            t = (pe["x"], pe["y"] + 46, pe["w"], pe["h"])
        elif i == "dr.big":
            t = (DRE_PANEL_X, 212, pe["w"], pe["h"])
        elif (i.startswith("dr.btn_") or i.startswith("dr.hit_") or i.startswith("dr.row_tx_")
              or i == "dr.face_tx"):
            t = (pe["x"] - 1, pe["y"] + 48, pe["w"], pe["h"])
        else:
            raise AssertionError("37 未覆盖的元素：" + i)
        e["x"], e["y"], e["w"], e["h"] = t
    hits = [e for e in d["elements"] if e["kind"] == "hit"]
    txts = [e for e in d["elements"] if e["kind"] == "text"]
    assert len(hits) == 36, len(hits)
    assert len(txts) == 31, len(txts)
    assert all(e["action"] == "" for e in hits), "37 的 hit action 应为空串（语义留编程组）"
    by_id(d)["dr.face_tx"]["font"]["color"] = "@palette.node_locked"
    add_note_once(d, "37_dress.json")
    return save(d, "37_dress.json")


def build_replay():
    d = load("38_replay.json")
    drop_dim(d, "rp.dim")
    add_bg(d, "rp")
    el = by_id(d)
    el["rp.preview"].update(dict(zip(("x", "y", "w", "h"), REP_PREVIEW)))
    el["rp.preview"]["nine"] = {"l": 0, "t": 0, "r": 0, "b": 0}   # 全零 nine＝允许整图缩放（0.943×/0.982×）
    lst = el["rp.list"]
    lst["x"], lst["y"] = REP_X, REP_Y
    lst["w"] = REP_COLS * REP_CELL_W + (REP_COLS - 1) * REP_GAP
    lst["h"] = REP_ROWS * REP_CELL_H + (REP_ROWS - 1) * REP_GAP
    lst["item_w"], lst["item_h"], lst["gap"] = REP_CELL_W, REP_CELL_H, REP_GAP
    lst["max_cols"], lst["max_rows"] = REP_COLS, REP_ROWS
    lst["scroll"]["page_size"] = REP_PER_PAGE
    lst["item_frame"]["nine"] = {"l": 0, "t": 0, "r": 0, "b": 0}
    vv = lst["item_variants"]
    assert len(lst["labels"]) == 50 and len(vv["frames"]) == 35
    assert sum(1 for r in vv["frames"] if len(r) == 1) == 10
    vv["thumb"] = {"x": REP_THUMB[0], "y": REP_THUMB[1], "w": REP_THUMB[2], "h": REP_THUMB[3],
                   "nine": {"l": 0, "t": 0, "r": 0, "b": 0}}
    vv["prev"].update(dict(zip(("x", "y", "w", "h"), REP_PREV)))
    vv["next"].update(dict(zip(("x", "y", "w", "h"), REP_NEXT)))
    lst["item_text"].update({"x": 5, "y": 125, "w": 261, "h": 25})
    lst["item_text"]["font"]["color"] = "@palette.node_locked"
    n = 4                                              # 50 栏 / 16 栏每页 = 3.125 ⇒ 4 页
    for v in ("1", "2"):
        e = el["rp.pg_tx_%s" % v]
        e.update(dict(zip(("x", "y", "w", "h"), PAGE_TX)))
        e["font"].update(PAGE_TX_DARK)
        e["vis_when"] = v
        e["sample"] = "%s / %d" % (v, n)
        e["note"] = page_tx_note(v, n)
    for v in ("3", "4"):
        upsert_pg_tx(d, el["rp.pg_tx_2"], "rp.pg_tx_%s" % v, "rp.pg_tx_2",
                     x=PAGE_TX[0], y=PAGE_TX[1], w=PAGE_TX[2], h=PAGE_TX[3],
                     font=dict(el["rp.pg_tx_2"]["font"]), vis_flag="replay_page", vis_when=v,
                     sample="%s / %d" % (v, n), note=page_tx_note(v, n),
                     **{"kind": "text", "z": 31, "visible_default": True, "align": "center",
                        "valign": "middle", "wrap": False, "max_lines": 1})
    d["page_flag"] = "replay_page"
    d["flags_default"] = {"replay_page": "1"}
    add_note_once(d, "38_replay.json")
    return save(d, "38_replay.json")


def build_shell():
    d = load("39_gal_shell.json")
    el = by_id(d)
    st = el["gs.strip"]
    st.update({"asset": "ui/x_ui_psv_shell_strip.png", "x": SHELL_STRIP[0], "y": SHELL_STRIP[1],
               "w": SHELL_STRIP[2], "h": SHELL_STRIP[3]})
    st.pop("nine", None)
    st["source"] = ("裁自 ui/x_ui_psv_gal_shell.png 的横幅带（源 y455..554 · x340..1919，"
                    "左缘 80px alpha 线性淡入）；拆件脚本 工具\\psv_make_shell_strip.py")
    st["note"] = ("页签条底板 = **PSV 横幅带**（1580×100，1:1 无 nine）。"
                  "★ PSV 深度换皮（2026-09-26 · ISSUE-20260926-06 · D 组）：原 M47 冰蓝磨砂条 "
                  "`x_ui_cfg_page_strip.png`（920×52 九宫格）退场，改用从 PSV ALBUM 屏区裁出的横幅带。"
                  "**横向自 x340 起是刻意的**：x0..340 是 PSV 英文题字区（ALBUM/MUSIC/MOVIE 实测 x64..~300），"
                  "用户裁决「英文题字保留原样」⇒ 条带不得压住题字；左缘 80px 淡入与霜页底自然接续。"
                  "条带底沿 y100 亦为刻意：28 页 PSV 播放条顶沿在 y102 ⇒ 条带不得越界压住它。")
    for i in range(4):
        x = SHELL_TAB_X0 + sum(SHELL_TAB_W[:i]) + SHELL_TAB_GAP * i
        r = (x, SHELL_TAB_Y, SHELL_TAB_W[i], SHELL_TAB_H)
        host = ["gallery", "music", "dress", "replay"][i]
        tx = el["gs.tab%d_tx" % (i + 1)]
        tx.update(dict(zip(("x", "y", "w", "h"), r)))
        tx["font"].update(OUTLINE)
        tx["note"] = ("页签 %d 文字（**引擎绘制**，不烘焙）。★ PSV 换皮（D 组）：几何随条带重排"
                      "（条带 (340,0,1580,100)、页签自 x360 起、条带中心线 y50 居中：y12 h76）；"
                      "文字加 2px 深色描边（`font.outline`，M38 既有机件、纯渲染不参与布局）⇒ "
                      "同一件文字即可覆盖「条带浅底」与「`@palette.highlight` 选中块」两态，"
                      "不必拆 `_tx` / `_tx_sel`。" % (i + 1))
        on = el["gs.tab%d_on" % (i + 1)]
        on.update(dict(zip(("x", "y", "w", "h"), r)))
        on["note"] = ("页签 %d 的**选中指示**（承载屏 = %s 时显示，`vis_flag:gal_tab`）。"
                      "几何随条带重排为 (x%d,y%d,w%d,h%d)，与同页签文字/热区**逐像素同矩形**。"
                      % (i + 1, host, r[0], r[1], r[2], r[3]))
        hit = el["gs.tab%d_hit" % (i + 1)]
        hit.update(dict(zip(("x", "y", "w", "h"), r)))
        assert hit["action"] == "gallery_tab_%d" % (i + 1)
        hit["note"] = ("页签 %d 热区（**切到 %s 屏**，动作 `gallery_tab_%d` 冻结不变）。"
                       "几何随条带重排为 (x%d,y%d,w%d,h%d)。命中优先级高于承载屏（附加层先扫）。"
                       % (i + 1, host, i + 1, r[0], r[1], r[2], r[3]))
    for key, rect in (("gs.title", SHELL_TITLE), ("gs.back_panel", SHELL_BACK),
                      ("gs.back_tx", SHELL_BACK), ("gs.back_hit", SHELL_BACK)):
        el[key].update(dict(zip(("x", "y", "w", "h"), rect)))
        if key in ("gs.title", "gs.back_tx"):
            el[key]["font"].update(OUTLINE)
    assert el["gs.back_hit"]["action"] == "close"
    assert len([e for e in d["elements"] if e["kind"] == "hit"]) == 5      # 4 页签 + 返回
    assert len(d["elements"]) == 17
    add_note_once(d, "39_gal_shell.json")
    return save(d, "39_gal_shell.json")


def main():
    res = [("27_gallery.json", build_gallery()), ("28_music.json", build_music()),
           ("37_dress.json", build_dress()), ("38_replay.json", build_replay()),
           ("39_gal_shell.json", build_shell())]
    for k, v in res:
        print("%-20s md5=%s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
