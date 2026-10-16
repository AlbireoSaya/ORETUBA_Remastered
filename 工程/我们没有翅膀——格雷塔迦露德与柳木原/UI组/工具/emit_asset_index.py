# -*- coding: utf-8 -*-
r"""emit_asset_index.py —— 扫描 `krkr\assets\ui\` 生成 `复刻\asset_index.js`（素材资料库索引）。

**为什么需要**：浏览器在 `file://` 协议下**无法列目录**，而编辑器要一个可搜索、可分类、
带尺寸的素材资料库 → 必须离线预生成清单。

产物：`复刻\asset_index.js` → `window.UI_ASSET_INDEX = { items: [...], groups: {...} }`
     每项：`{ n: 文件名, w, h, g: 分组, s: 体积 }`
"""
import os, sys, json, collections, datetime
sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
OUT = os.path.join(UI, "复刻", "asset_index.js")

# 分组规则（按文件名前缀，从长到短匹配）
GROUPS = [
    # ★ M57（2026-09-28 · ISSUE-20260928-03_素材 · 「未解锁压暗件方角修复 + 已读绿对勾」）：**2 件**
    #   产出脚本 `_工作\ISSUE-20260928-03_素材\复现脚本\m57_make_state_assets.py`（幂等、自带断言）。
    #   `x_ui_read_check.png`（主版 20×20：`@palette.node_visited` 系绿圆牌 Ø18 + 白勾）
    #   ／ `x_ui_read_check_alt.png`（备选版 20×20：绿勾 + 白 1px 描边、透明底）
    #   —— 流程图节点「已读（`visited`）」叠加件（`fc.node.<NNNN>_read`）。
    #   一条前缀覆盖两件；**必须排在通用前缀之前**（本函数首匹配即返回）。
    #   ⚠️ 与既有前缀**互不为前缀**：`x_ui_replay_`（第 7 字符 `p`）/ `x_ui_reset_`（`s`）
    #      与 `x_ui_read_...`（`d`）在第 7 字符即分叉，两侧不吞并。
    #   ⚠️ 本 issue 另产的 3 件 `x_ui_node_*_dim.png`（未解锁压暗件，随形 alpha）
    #      **落在既有前缀 `x_ui_node_`**（下方「流程图节点」行）⇒ **不另立行**。
    ("流程图已读对勾", "x_ui_read_check"),
    # ★ M56（2026-09-28 · ISSUE-20260928-02 第 7 批 · 番外组名底板换件）：**1 件**
    #   产出脚本 `_工作\ISSUE-20260928-02_素材\复现脚本\m56_make_fragtitle_bg.py`（幂等、自带断言）。
    #   `x_ui_fragtitle_bg` —— 番外独立层「组名底板」**专用硬边件** 444×52。
    #   起因：第 5 批复用主图标签件 `x_ui_label_off.png`（355×60，四边宽渐隐带）拉到 420×38 后
    #   真不透明核心只剩 rows 7..30 / cols 13..406 ⇒ 首末字压在渐隐带上（对比度 5 分位退化）。
    #   **必须排在通用前缀之前**（本函数首匹配即返回）：前缀 `x_ui_fragtitle_` 与
    #   `x_ui_frag*` 无任何既有条目（全表无 `x_ui_frag` 前缀），也不与 `x_ui_ftab_`/`x_ui_fusen_` 互为前缀。
    ("流程图组名底板", "x_ui_fragtitle_"),
    # ★ M55（2026-09-28 · ISSUE-20260928-02_流程图第2步 · C 素材缺口）：**流程图新素材 23 件**
    #   产出脚本 `_工作\ISSUE-20260928-02_素材\复现脚本\m55_make_flow_assets.py`（幂等、自带断言）。
    #   **五条新前缀（写在 4 行里）**，均加在通用前缀之前（本函数首匹配即返回）：
    #     ① `x_ui_new`         —— NEW 角标 50×17（**必须独立成行**：否则无前缀可匹配，落「其它」组）
    #     ② `x_ui_pbkick_`     —— 场景回放键三态 119×119
    #     ③ `x_ui_zoomout_`    —— 缩放 − 三态 **29×29**（2026-09-28 第 2 轮：按下态 41×41 已取消，
    #        元素矩形即 29×29；41 会被引擎 0.71× 重采样致边缘发虚）
    #     ④ `x_ui_zoomin_`     —— 缩放 ＋ 三态 **29×29**（同上）
    #     ⑤ `x_ui_replay_panel`—— 场景回放窗底板 426×241（**必须排在 `x_ui_replay_` 之前**，
    #        否则会被「回放框」（回想屏的重播小键）吞掉；两者语义不同屏）
    #   ⚠️ 前五条与既有前缀**互不为前缀**：`x_ui_new` vs `x_ui_node_`（第 6 字符 `w` vs `o`）、
    #      `x_ui_zoomout_`/`x_ui_zoomin_` vs `x_ui_zoom_`（第 10 字符 `o` vs `_`）、
    #      `x_ui_pbkick_` 无同族。两侧不吞并。
    #   ⚠️ `x_ui_shift_lf_/rg_` 归既有「平移条」、`x_ui_scroll_up_/dn_` 归既有「滚动条」，
    #      故**不另立行**（它们本来就命中 `x_ui_shift_` / `x_ui_scroll_`）。
    ("流程图回放窗底板", "x_ui_replay_panel"),
    # ★ M60（2026-09-29 · ISSUE-20260929-02_右栏大改 · E1 素材）：**4 件**
    #   产出脚本 `_工作\ISSUE-20260929-02_右栏大改\复现脚本\m60_make_playwin_and_pause.py`（幂等、自带断言）。
    #   ① `x_ui_playwin_bg.png` —— **大播放窗底板 380×300**（照 `x_ui_replay_panel` 同一配方，仅尺寸不同）
    #      **必须独立成行**：否则无前缀可匹配，会落进「其它」组。
    #      ⚠️ 与既有前缀**互不为前缀**（`x_ui_playwin` vs `x_ui_pb_` / `x_ui_pbkick_` / `x_ui_panel_`
    #         在第 7 字符分叉：`l` vs `b` / `b` / `a`），两侧不吞并。
    #   ② `x_ui_pbkick_pause_{off,over,on}.png` —— **暂停键三态 119×119**（盘面 = 同态播放键**逐像素同源**，
    #      仅替换字形掩膜）⇒ **落既有前缀 `x_ui_pbkick_`（本行，见下条注记），不另立行**。
    ("流程图播放窗底板", "x_ui_playwin"),
    # 流程图回放键 —— ★ M60 注记：`x_ui_pbkick_pause_*`（暂停键三态）**同上前缀**，实测
    #   `"x_ui_pbkick_pause_off.png".startswith("x_ui_pbkick_")` 为真 ⇒ 与播放键 `x_ui_pbkick_{off,over,on}`
    #   **同组**（语义相符：同一控件的一对互斥态），故**不另立行**。
    ("流程图回放键", "x_ui_pbkick_"),
    ("流程图缩放键", "x_ui_zoomout_"), ("流程图缩放键", "x_ui_zoomin_"),
    ("章节详情加号按钮", "x_ui_plusbtn_"),
    ("流程图 NEW 角标", "x_ui_new"),
    # ★ M53（2026-09-26 · ISSUE-20260926-06_PsvUI换皮）：PSV 系统 UI 入库件 32 件
    #   （`工具\m53_psv_ui_assets.py` 从参考区 `PSV系统UI参考\` 裁切/整流而来：
    #    存/读档/快速读档/通话记录/设置两页底图 6 ＋ 去字药丸壳 14 ＋ 滑槽 5
    #    ＋ 确认空白板 / 选择支两态 / 鉴赏外壳 / BGM / 情景回想 / 立绘网格 / 槽零件 7）。
    #   本前缀**不与任何既有前缀互为前缀**（`x_ui_psv_` vs `x_ui_pg_`/`x_ui_pill_`… 无交集），
    #   不吞并也不被吞并；不加本条目时会全部落进「其它」组。
    ("PSV系统UI(换皮)", "x_ui_psv_"),
    ("菜单图标", "x_ui_menuicon_"),
    # ↓ M35 系统页按钮文字（方框脚手架方案，精确 48×48/4px）：c=合成、无后缀=正文层、f=独立羽毛层
    ("按钮字·批次2·合成", "x_ui_btntxt2c_"),
    ("按钮字·批次3·合成", "x_ui_btntxt3c_"),
    ("按钮字·批次2·正文", "x_ui_btntxt2_"),
    ("按钮字·批次3·正文", "x_ui_btntxt3_"),
    ("按钮字·羽毛层", "x_ui_btntxtf_"),
    ("字1·AI(有柔光)", "x_ui_menutxt1_"),
    ("字2·字体直出", "x_ui_menutxt2_"),
    ("字3·扁平冰蓝", "x_ui_menutxt3_"),
    ("字4·冰蓝渐变", "x_ui_menutxt4_"),
    ("字5·字体白底描边", "x_ui_menutxt5_"),
    ("字6·AI扁平冰蓝", "x_ui_menutxt6_"),
    ("字7·AI冰蓝渐变", "x_ui_menutxt7_"),
    ("字8·AI白底描边", "x_ui_menutxt8_"),
    ("中文字1·羽毛轻", "x_ui_cnmenutxt1_"),
    ("中文字2·羽毛中", "x_ui_cnmenutxt2_"),
    ("中文字3·羽毛密", "x_ui_cnmenutxt3_"),
    ("中文字4·羽上飘", "x_ui_cnmenutxt4_"),
    ("中文字5·羽环绕", "x_ui_cnmenutxt5_"),
    ("字·旧", "x_ui_menutxt_"),
    ("面板/框", "x_ui_panel_"),
    ("按钮", "x_ui_btn_"),
    ("方形键", "x_ui_sqkey_"),
    ("页签", "x_ui_tab_"), ("流程图页签", "x_ui_ftab_"),
    ("勾选", "x_ui_check_"), ("开关", "x_ui_tgl_"), ("模式键", "x_ui_opt_"),
    ("滑条", "x_ui_slider_"), ("滚动条", "x_ui_scroll_"), ("缩放条", "x_ui_zoom_"),
    ("平移条", "x_ui_shift_"), ("音量条", "x_ui_vol_"),
    ("箭头", "x_ui_arrow_"), ("关闭键", "x_ui_close_"),
    ("播放控制", "x_ui_pb_"), ("静音", "x_ui_mute_"), ("试听", "x_ui_replay_"),
    ("语音键", "x_ui_spk_"),
    # ★ M49（2026-09-24，ISSUE-20260924-06 回想屏重排）：**逐块「重新播放」键**新件，
    #   与旧 `x_ui_spk_*`（25×27 / 37×40，保留不删）并存 ⇒ 单独成组，避免落进「其它」。
    #   前缀 `x_ui_spk2_` 不以 `x_ui_spk_` 开头（第 9 字符是 `2` 不是 `_`），两条互不吞并。
    #   产出脚本：`工具\m49_make_backlog_assets.py`（44×44 三态，程序化）。
    ("语音键·重播(新)", "x_ui_spk2_"),
    ("跳转键", "x_ui_jump"), ("备注键", "x_ui_fusen_"),
    ("系统条", "x_ui_sysbar_"), ("快捷条", "x_ui_quick_"),
    ("存档槽", "x_ui_slot_"), ("页码", "x_ui_pg_"), ("编辑条", "x_ui_edit_"),
    ("锁定徽章", "x_ui_lock_"),
    ("角色集", "x_ui_charset_"), ("角色行", "x_ui_charrow_"),
    ("立绘控件", "x_ui_dress_"), ("时间图标", "x_ui_time_"), ("初始化", "x_ui_reset_"),
    ("流程图节点", "x_ui_node_"), ("流程图标签", "x_ui_label_"),
    # ★ E2（2026-09-29 · ISSUE-20260929-04_流程图件）：**番外入口块** 1 族 **2 件** ——
    #   `x_ui_entry_frag_{off,on}.png`（263×65 淡黄节点形块，由 `x_ui_node_select_{off,on}.png` 派生，
    #   落在 `fc.entry.<NNNN>`）。无既有前缀能命中 `x_ui_entry_` ⇒ 不加本行会全落「其它」组。
    #   ★ E5 订正（同批收尾）：原注释另列的 `x_ui_entry_note.png`（E3 AI 生图方案的定稿）**未采用、未接线**，
    #     已由 E5 **移出** `assets\ui\`、留档于 `_工作\ISSUE-20260929-04_流程图件\生图\`（移动非删除）
    #     ⇒ 本组现只有 2 件，索引里**不得再出现**该名字。
    ("番外入口", "x_ui_entry_"),
    ("分支底座", "x_ui_branch_"),
    ("选择支", "x_ui_choice_"), ("曲目行", "x_ui_track_"), ("曲名板", "x_ui_music_"),
    ("回放框", "x_ui_replay_"), ("CG框", "x_ui_cg_"),
    # ★ M2（2026-09-24 · ISSUE-20260924-08_鉴赏模式 · CG 页）：两条**新前缀**（加在通用前缀之前，
    #   本函数是「首匹配即返回」）。
    #   ① `x_gal_c<新ID三位>_<n>.png`（703 件 = 286 栏的差分总数，287×162）：栏位差分缩略图；
    #   ② `x_ui_gal_*`（18 件）：CG 鉴赏页 chrome（栏位底板三态 / 栏位内差分键三态 / 页码键三态 /
    #      页签底板三态）。两者均由 `工具\m50_make_gallery_thumbs.py` 程序化生成（幂等、自带断言）。
    #   ⚠️ ①的 703 件是**内容缩略图**、不是「人工挑用的素材」，会占满资料库列表 ⇒ 单独成组，
    #      便于编辑器侧折叠/过滤（是否彻底不写入 `items` 属编辑器侧决定，本行只做分组）。
    ("CG缩略图(鉴赏页)", "x_gal_c"),
    ("CG鉴赏页(chrome)", "x_ui_gal_"),
    # ★ M4（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`x_ui_bgm_` 是 M3 的 BGM 鉴赏页 42 件
    #   （曲目行/播放控制/翻页键/音量，`工具\m51_make_bgm_assets.py` 程序化生成）——此前无前缀条目
    #   会全落「其它」组；`x_ui_rp_` 是 M4 情景回想页 11 件（栏位底板/动画占位缩略图/预览板/页码键，
    #   `工具\m52_make_replay_assets.py` 程序化生成）。两条均加在通用前缀之前（首匹配即返回；
    #   `x_ui_bgm_` 与 `x_ui_btn_`、`x_ui_rp_` 与 `x_ui_replay_` 互不为前缀，不吞并）。
    ("BGM 鉴赏", "x_ui_bgm_"),
    ("情景回想", "x_ui_rp_"),
    ("消息块", "x_ui_msgblock_"), ("标题条", "x_ui_caption_"),
    ("频谱", "x_ui_speana_"), ("转圈", "x_ui_spin_"), ("加载牌", "x_ui_loading_"),
    ("转场遮罩", "x_mask_"),
    ("对话窗(原版)", "x_gen_dialog"), ("功能图标(原版)", "x_gen_dicon_"),
    ("功能图标(旧)", "x_gen_icon_"),
    ("整页底图", "x_gen_gallerypage"), ("整页底图", "x_gen_fragpage"),
    ("标题", "x_gen_logo"), ("标题", "x_title_"),
    # ★ E2（2026-09-29 · ISSUE-20260929-04_流程图件）：**流程图满幅背景** `x_bg_flowchart.png`
    #   （1920×1080，由 `美术统一_超分\CG背景\bg72.png` 2560×1440 0.75× LANCZOS 降采样）。
    #   必须排在通用前缀 `x_bg_`（系统背景）**之前**（本函数首匹配即返回），否则会混进「系统背景」组。
    ("流程图背景", "x_bg_flowchart"),
    ("系统背景", "x_bg_"),
    ("AI 生图(旧)", "x_gen_"),
]
SINGLE = {"x_gen_gallerypage.png": "整页底图", "x_gen_fragpage.png": "整页底图",
          "x_gen_logo.png": "标题", "x_bg_system.png": "系统背景"}


# ★ M47（2026-09-24）：索引范围从「仅 `assets/ui/`」扩到「`assets/ui/` + `assets/face/`」。
#   起因：设置屏的 33 件角色预览按 `首段命名空间` 引用 `face/<族名><基底>.png`（引擎与 `verify_ui.py` 均已支持），
#   而索引只扫 ui/ 会让编辑器报「素材不在资料库里」的误告。该目录**不入库**、由 `_工作\\M44_头像裁切方案\\复现脚本\\m44_make_faces.py` 再生。
FACE_DIR = os.path.join(os.path.dirname(ASSETS), "face")
FACE_GROUP = "角色头像（face/ 命名空间）"


def group_of(name):
    if name in SINGLE:
        return SINGLE[name]
    for g, pre in GROUPS:
        if name.startswith(pre):
            return g
    return "其它"


def main():
    items = []
    for p in sorted(os.listdir(ASSETS)):
        if not p.lower().endswith(".png"):
            continue
        full = os.path.join(ASSETS, p)
        try:
            with Image.open(full) as im:
                w, h = im.size
                mode = im.mode
        except Exception as e:
            print("!! 读不了 %s：%r" % (p, e))
            continue
        items.append({"n": p, "w": w, "h": h, "g": group_of(p),
                      "s": os.path.getsize(full), "m": mode})
    # ★ M47：间接命名空间 `face/`（名字带前缀入索引，供编辑器直接选用）
    if os.path.isdir(FACE_DIR):
        for p in sorted(os.listdir(FACE_DIR)):
            if not p.lower().endswith(".png"):
                continue
            full = os.path.join(FACE_DIR, p)
            try:
                with Image.open(full) as im:
                    w, h = im.size
                    mode = im.mode
            except Exception as e:
                print("!! 读不了 face/%s：%r" % (p, e))
                continue
            items.append({"n": "face/" + p, "w": w, "h": h, "g": FACE_GROUP,
                          "s": os.path.getsize(full), "m": mode})
    groups = collections.OrderedDict()
    for it in items:
        groups.setdefault(it["g"], []).append(it["n"])
    js = ("/* 自动生成：工具\\emit_asset_index.py —— 素材资料库索引。**请勿手改**。\n"
          "   素材目录：UI组\\krkr\\assets\\ui\\（%d 件）"
          "＋ UI组\\krkr\\assets\\face\\（%d 件，以 `face/` 前缀入索引；"
          "该目录**不入库**、由 _工作\\M44_头像裁切方案 的脚本再生）。\n"
          "   浏览器在 file:// 下无法列目录，故离线预生成此清单供编辑器资料库使用。 */\n"
          "window.UI_ASSET_INDEX = {\n"
          "  generated: %s,\n"
          "  count: %d,\n"
          "  groups: %s,\n"
          "  items: %s\n};\n") % (
        # ★ K6（2026-09-23）：生成日**不再写死**（原为字面量 "2026-09-22"：每次重跑都吐旧日期，
        #   且 diff 里看不出这份索引是哪天生成的）——改为运行时当天日期。
        len([1 for i in items if not i["n"].startswith("face/")]),
        len([1 for i in items if i["n"].startswith("face/")]),
        json.dumps(datetime.date.today().isoformat()), len(items),
        json.dumps(groups, ensure_ascii=False, indent=1),
        json.dumps(items, ensure_ascii=False, indent=0))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(js)
    # 顺带产出屏清单（编辑器要「屏 id → screens/*.json 文件名」的映射）
    si = os.path.join(UI, "layout", "screens", "_index.json")
    scr = []
    if os.path.exists(si):
        d = json.load(open(si, encoding="utf-8"))
        for it in d.get("screens", []):
            scr.append({"id": it["id"], "file": it["file"],
                        "title_cn": it.get("title_cn", ""), "owner": it.get("owner", "")})
    sjs = ('/* 自动生成：工具\\emit_asset_index.py —— 屏清单（编辑器用）。**请勿手改**。\n'
           '   来源：layout/screens/_index.json */\n'
           'window.UI_SCREEN_INDEX = %s;\n') % json.dumps(scr, ensure_ascii=False, indent=1)
    open(os.path.join(UI, "复刻", "screen_index.js"), "w", encoding="utf-8").write(sjs)
    print("屏清单：%d 屏 -> 复刻\\screen_index.js" % len(scr))
    print("素材索引：%d 件 / %d 组 -> %s" % (len(items), len(groups), OUT))
    for g, ns in groups.items():
        print("   %-14s %3d 件" % (g, len(ns)))


if __name__ == "__main__":
    main()