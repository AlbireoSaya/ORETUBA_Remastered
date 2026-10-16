# -*- coding: utf-8 -*-
r"""M47 · W2（数据）· 设置（config）屏 **一次性脚手架**
================================================================================
■ 跑一次就够 —— 之后 JSON 才是真相源
  本脚本按 M47 接口冻结书（`_工作\M47_设置屏重设方案.md` §一 几何 / §二 素材 /
  §三 机制契约 / §五 验收）**一次性**产出 `layout/screens/25_config.json`。
  ★ **产出后 `25_config.json` 即人手维护的真相源**：重跑本脚本会**覆盖**用户 /
  编辑器在该 JSON 上做的一切手改（`editor_ui.js` 导出、坐标微调、文案改动）。
  ★ **因此不要把它当生成器用**，也不要登记进 `工具\test_gen_sync.py` 的 GENERATORS
  （前例：M45 `build_sysmenu` / M46 `build_sysbar` 均按「删条目、JSON 转手工维护」处置；
  本脚本对应 M47，**生成器退役动作由主代理统一执行**）。
  ★ 元素一律用**数据表驱动**生成（行表 / 角色表 / 滑块表），便于逐条复核坐标来源。

■ 用法
    python _工作\M47_设置屏重设\复现脚本\m47_build_config.py
  然后：python 工具\gen_layout.py ／ python 工具\verify_ui.py ／ python 工具\test_click_reach.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))          # …\M47_设置屏重设\复现脚本
EVID = os.path.dirname(HERE)                               # …\M47_设置屏重设
UI = os.path.dirname(os.path.dirname(EVID))                # …\UI组
OUT = os.path.join(UI, "layout", "screens", "25_config.json")

# ---------------------------------------------------------------- 素材来源串
SRC_A = ("程序化生成（PIL）→ `工具\\m47_make_config_assets.py`（M47 · W1）；"
         "我们的配色（冰蓝霜白磨砂族），见 `_工作\\M47_设置屏重设方案.md` §二")
SRC_MASK = ("程序化生成（PIL）→ `工具\\m47_make_config_assets.py`（M47 · W1）；"
            "与 `ui/x_ui_dlgmask_bottom_350.png` **同一算法**（α = 255·t 线性）按 612×154 生成，"
            "保证预览浓淡与对话框一致（方案 §二）")
SRC_FACE = ("对话屏同款静态件：`ui/x_ui_dlg_face_demo.png`（= `dlg.face` 当前引用的那张）")

# ---------------------------------------------------------------- 调色板引用
C_TEXT_PRIMARY = "@palette.text_primary"
C_TEXT_NAME = "@palette.text_name"
C_TEXT_MENU = "@palette.text_menu"
C_TEXT_MENU_SEL = "@palette.text_menu_sel"
C_TEXT_HINT = "@palette.text_hint"
C_TEXT_ON_CHIP = "@palette.panel_fill"   # ★ W1 实测：浅色胶囊上的暗字（7.7:1）
C_ACCENT = "@palette.accent"
C_BACKDROP = "@palette.backdrop"

# ---------------------------------------------------------------- z 层带（唯一定义处）
Z = dict(dim=1, frame=10, tab_img=12, pv_bg=14, pv_mask=15, pv_frame=16, avatar=18,
         title=20, plate=22, dot=24, text=26, pill=30, tx=32, tx_sel=33,
         drag=95, hit=96)

# ---------------------------------------------------------------- 构建器
ELEMENTS = []
BLOCKS = []          # (块名, 件数)


def _finish(el, page, vis, tag):
    if vis is not None:
        el["vis_flag"], el["vis_when"] = vis
    elif page is not None:
        el["vis_flag"], el["vis_when"] = "cfg_page", page
    ELEMENTS.append(el)
    return el


def rect(eid, x, y, w, h, color, opacity, z, note):
    return _finish({"id": eid, "kind": "rect", "z": z, "visible_default": True,
                    "x": x, "y": y, "w": w, "h": h,
                    "color": color, "opacity": opacity, "note": note}, None, None, None)


def img(eid, asset, x, y, w, h, z, note, *, nine=None, opacity=None, page=None,
        vis=None, state_assets=None, group=None, source=SRC_A):
    el = {"id": eid, "kind": "image", "z": z, "visible_default": True,
          "asset": asset, "x": x, "y": y, "w": w, "h": h,
          "opacity": 255 if opacity is None else opacity,
          "source": source, "note": note}
    if nine is not None:
        el["nine"] = nine
    if state_assets is not None:
        el["state_assets"] = state_assets
    if group is not None:
        el["state_group"] = group
    return _finish(el, page, vis, None)


def txt(eid, x, y, w, h, sample, size, color, z, note, *, bold=False,
        align="left", valign="middle", wrap=False, max_lines=1, page=None,
        vis=None, outline=False, outline_size=2):
    font = {"size": size, "bold": bold, "color": color, "shadow": False,
            "shadow_color": "@palette.shadow", "shadow_ofs": 0}
    if outline:
        font["outline"] = True
        font["outline_color"] = "#000000"
        font["outline_width"] = outline_size
    el = {"id": eid, "kind": "text", "z": z, "visible_default": True,
          "x": x, "y": y, "w": w, "h": h, "font": font,
          "align": align, "valign": valign, "wrap": wrap,
          "sample": sample, "note": note}
    if max_lines != 1:
        el["max_lines"] = max_lines
    return _finish(el, page, vis, None)


def hit(eid, x, y, w, h, action, z, note, *, value=None, slider=None,
        page=None, group=None, vis=None):
    el = {"id": eid, "kind": "hit", "z": z, "visible_default": True,
          "x": x, "y": y, "w": w, "h": h, "action": action, "label": "",
          "font": {"size": 24, "bold": False, "color": "@palette.node_locked",
                   "shadow": False, "shadow_color": "@palette.shadow", "shadow_ofs": 0},
          "align": "center", "note": note}
    if value is not None:
        el["value"] = value
    if slider is not None:
        el["slider"] = slider
    if group is not None:
        el["state_group"] = group
    return _finish(el, page, vis, None)


def slider(eid, x, y, w, h, setting, value, z, note, *, page=None,
           mn=0, mx=100, step=5, rail="ui/x_ui_cfg_rail.png",
           knob="ui/x_ui_cfg_knob.png", knob_over="ui/x_ui_cfg_knob_over.png"):
    el = {"id": eid, "kind": "slider", "z": z, "visible_default": True,
          "x": x, "y": y, "w": w, "h": h, "min": mn, "max": mx, "step": step,
          "value": value, "setting": setting,
          "rail": {"asset": rail},
          "handle": {"asset": knob,
                     "state_assets": {"normal": knob, "hover": knob_over}},
          "note": note}
    return _finish(el, page, None, None)


def build_slider(sid, x, y, w, h, setting, value, page, note, *,
                 hit_rect=None, ends=None, end_y=None, end_w=46,
                 rail_note="轨道以元素中心线为轴（素材 364×11 ⇒ 元素 w==364；无九宫格）"):
    """滑块本体 + 整行拖动 hit + 两端刻度文字。hit_rect = (x,y,w,h) / ends = (lo文字, hi文字, lo_x, hi_x)。"""
    slider(sid, x, y, w, h, setting, value, Z["plate"],
           "%s。kind=slider（方案 §3.1：`x..x+w` 映射 min..max、step 取整、`value` 为初值；%s；"
           "**不参与** `uiScreenHoverAtIn` 的候选并集 ⇒ 不改判据指纹；手柄不随元素框裁剪）。"
           "setting=%s（设置仓键名，§3.3）。" % (note, rail_note, setting), page=page)
    hx, hy, hw, hh = hit_rect
    hit(sid + "_hit", hx, hy, hw, hh, "", Z["drag"],
        "滑块 %s 的**拖动热区**（方案 §3.2：复用既有鼠标路径，hit 上带 `slider=\"%s\"` 字段 ⇒ "
        "机制侧按下即绑定拖动、悬停期间按 x 持续更新、抬起/换屏解绑）。"
        "★ **不带 state_group**（滑块不入悬停候选并集，见 §3.1）；★ 带**页 flag**：两页的滑块矩形"
        "互相重叠（如不透明度行的 298,663,382,59 与系统音效行的 244,672,620,21），不互斥就会跨页"
        "抢拖动（`_schema` §四 铁律一）。几何=%s。"
        % (sid, sid, hit_rect), slider=sid, page=page)
    lab_lo, lab_hi, lox, hix = ends
    ey = y if end_y is None else end_y
    txt(sid + "_end_lo", lox, ey, end_w, 21, lab_lo, 19, C_TEXT_MENU, Z["text"],
        "%s 的左端刻度文字「%s」（方案 §1.2/§1.3：两端刻度文字 19 号；w/h 未给，取 %d×21）。"
        % (sid, lab_lo, end_w), align="center", page=page)
    txt(sid + "_end_hi", hix, ey, end_w, 21, lab_hi, 19, C_TEXT_MENU, Z["text"],
        "%s 的右端刻度文字「%s」。同左端。" % (sid, lab_hi), align="center", page=page)


# ================================================================================
# 一、数据表
# ================================================================================
PAGE_SYS, PAGE_SND = "sys", "snd"

# 系统页选项（10 行）。每行 2 值：主值（戴 `x_ui_cfg_opt_on.png` 冰蓝胶囊）/ 次值（`opt_off` 透明底）。
# 表列：key, 主值, 次值, 主值文字, 次值文字, 初值, 行标签, 「主值」矩形, 「次值」矩形
OPT_SYS = [
    ("display", "window", "full", "窗口模式", "全屏模式", "window", "画面模式",
     (445, 241, 205, 59), (676, 241, 221, 59)),
    ("facewindow", "on", "off", "ON", "OFF", "on", "立绘窗口",
     (619, 301, 115, 59), (760, 301, 115, 59)),
    ("drama", "on", "off", "ON", "OFF", "on", "演出效果",
     (619, 361, 115, 59), (760, 361, 115, 59)),
    ("effect", "on", "off", "ON", "OFF", "on", "特效",
     (619, 421, 115, 59), (760, 421, 115, 59)),
    ("voicecut", "on", "off", "ON", "OFF", "off", "语音截断",
     (619, 481, 115, 59), (760, 481, 115, 59)),
    ("curhide", "on", "off", "ON", "OFF", "off", "隐藏光标",
     (619, 541, 115, 59), (760, 541, 115, 59)),
    ("savedialog", "on", "off", "ON", "OFF", "on", "存档时的确认信息",
     (619, 841, 115, 59), (760, 841, 115, 59)),
    ("loaddialog", "on", "off", "ON", "OFF", "on", "读档时的确认信息",
     (619, 901, 115, 59), (760, 901, 115, 59)),
    ("allskip", "on", "off", "ON", "OFF", "off", "全部跳过",
     (1567, 481, 115, 59), (1708, 481, 115, 59)),
    ("textcolchg", "on", "off", "ON", "OFF", "on", "文字变色",
     (1567, 541, 115, 59), (1708, 541, 115, 59)),
]

# 声音页音量行（§1.3 左列）：setting, 行名, 行 y, 是否有喇叭 icon
VOL_ROWS = [
    ("vol_master", "主音量", 318, False),
    ("vol_bgm", "背景音乐", 438, False),
    ("vol_se", "音效", 558, True),
    ("vol_sysse", "系统音效", 678, True),
    ("vol_voice", "主音量（语音）", 918, True),
]
ROW_X = 244                     # §1.3 行结构基准 x（PSB `#sliders/<名>` 的 x）
ROW_OFF = dict(rail=63, max=446, mute_lb=531, mute=599, spk=-48)   # 喇叭在行基准左侧 48px（W1 修正 3）
# ★ 2026-09-24 一审 Major 3 修正：九个滑块元素的 `value` **必须与两端设置定义表逐值一致** ——
#   krkr `krkr/game/ui_settings.tjs` 的 `UISettingDef[k].def` 与 HTML `复刻/replica.js` 的
#   `SETTING_DEF[k].def`（replica.js:1566-1575）。渲染实际吃 `def`，JSON 写别的值就是**假初值**。
#   一审实测偏差：textspeed 50/60、vol_master|voice|char 100/80、vol_bgm|se 90/80 ⇒ 已全部改回 def 值。
SLIDER_VAL = {"dlg_winopac": 90, "text_speed": 60, "auto_speed": 50, "vol_master": 80,
              "vol_bgm": 80, "vol_se": 80, "vol_sysse": 80, "vol_voice": 80, "vol_char": 80}

# 角色清单（33 项，方案 §1.3）。第三列 = 作品层术语表是否有该写形的明确条目
CHARS = [
    ("asu", "渡来明日香", "有据"), ("hiy", "日和子", "待入表"), ("eri", "英里子", "待入表"),
    ("miy", "京", "待入表"), ("kin", "纪奈子", "待入表"), # ★ 裁决（2026-09-24）：术语表 §5.1 明写「鳳 鳴」→「凤鸣」
    ("nar", "凤鸣", "有据"),
    ("kob", "小鸠", "有据"), ("ai_", "亚衣", "待入表"), ("mis", "美咲", "待入表"),
    ("har", "春日春惠", "有据"), ("aki", "吉川", "有据"),
    ("kan", "可菜", "待入表"), ("yuu", "优", "待入表"), ("sak", "咲夜", "待入表"),
    ("saw", "布露波卢冴子", "有据"), ("ari", "爱丽丝", "待入表"), ("min", "米内奥拉", "待入表"),
    ("pur", "普纳奇纳", "有据"), ("men", "面魔", "有据"), ("mit", "满夜", "待入表"),
    ("kyo", "狂夜", "待入表"), ("dai", "大主教", "待入表"),
    ("kaz", "和马", "待入表"), ("ten", "狩男", "待入表"), ("kur", "藏人", "待入表"),
    ("mas", "高内", "待入表"), ("ban", "巴尼Ｄ", "有据"), ("chi", "奇肯多", "有据"),
    ("lr", "ＬＲ２００１", "待入表"), ("mar", "马汀内斯", "待入表"), ("kaa", "翔", "有据"),
    ("bok", "牧师", "待入表"), ("dab", "帽子男", "待入表"),
]
# ★ 横幅头像素材：族名 → 文件名（**显式列出，不 glob**；规则 = 该族「图数最多的基底」的基准件）
#   来源：`krkr/assets/face/` 实测 361 件按 `<族><编号>[表情后缀].png` 归组，取每族件数最多的编号；
#   与 `UI组\头像素材清单.md` 的「族 → 头像文件」列一致（该列示例即 `asu07.png`、`chi01.png`…）。
FACE_FILES = {
    "asu": "asu07.png", "hiy": "hiy01.png", "eri": "eri01.png", "miy": "miy01.png",
    "kin": "kin01.png", "nar": "nar01.png", "kob": "kob01.png", "ai_": "ai_01.png",
    "mis": "mis01.png", "har": "har01.png", "aki": "aki01.png", "kan": "kan01.png",
    "yuu": "yuu01.png", "sak": "sak01.png", "saw": "saw01.png", "ari": "ari01.png",
    "min": "min01.png", "pur": "pur01.png", "men": "men01.png", "mit": "mit01.png",
    "kyo": "kyo01.png", "dai": "dai01.png", "kaz": "kaz02.png", "ten": "ten01.png",
    "kur": "kur02.png", "mas": "mas01.png", "ban": "ban01.png", "chi": "chi01.png",
    "lr": "lr201.png", "mar": "mar01.png", "kaa": "kaa01.png", "bok": "bok01.png",
    "dab": "dab01.png",
}


def tag_for(prov):
    """角色名的「待入表」标记（与列表 `_tx` 同一口径）。"""
    return "" if prov == "有据" else "（译名待入表）"


# ★ 2026-09-24 一审阻塞 2 修正：列距由 260 改为 **250**（列 x = 1126 / 1376 / 1626）。
#   原列距 260 使第 3 列右沿落到 **1896**，越过巨型外框右沿（外框 33..1886、框线实测 x≈1876..1880）；
#   且 `name_sel` 素材横向 α 恒 150 直抵边缘（无渐变收边）⇒ 选中第 3 列角色时实色胶囊会**穿出框线**。
#   改后末列右沿 = 1626+250 = **1876**，正好压在框线内侧（列内单元仍 250×36，列间无缝隙：1126..1376 / 1376..1626 / 1626..1876）。
CHAR_COLS = (1126, 1376, 1626)
# ★ 2026-09-24 主代理裁决（W2 实测越界修复）：原方案 §1.3「592 起 / 步进 43 / 单元 250×43」
#   算得末行单元底 = 1065 > 巨型外框内沿 1046（越框 19px）⇒ 改为 **首行 588 / 步进 39 / 单元 250×36**：
#   11 行 ⇒ 588,627,…,978；末行单元 978..1014 ✓（≤ 硬约束 1022 ≤ 外框内沿 1046）。
#   字号随之 22 → 20；圆点 12×12 在 36 高单元内居中 ⇒ y = 行y + 12。
CHAR_ROW0, CHAR_STEP, CHAR_CELL_H = 588, 39, 36
CHAR_DOT_DY = (CHAR_CELL_H - 12) // 2      # = 12

# ================================================================================
# 二、两页共用
# ================================================================================
n0 = len(ELEMENTS)
rect("cfg.dim", 0, 0, 1920, 1080, C_BACKDROP, 70, Z["dim"],
     "全屏压暗（方案 §1.1「全屏压暗 0,0,1920,1080」）。用户要**透明背景** ⇒ 不用底图，"
     "只留这层薄压暗保证文字可读；要更透就把本元素 opacity 改小（单点可调，如 0 = 全透）。")

img("cfg.frame", "ui/x_ui_cfg_frame.png", 33, 93, 1853, 953, Z["frame"],
    "★ 用户说的「总体的巨型方框」（方案 §1.1「巨型外框 33,93,1853,953」= PSB idx80 `システム/"
    "タブレット` 同矩形）。九宫格 l=t=r=b=24（素材 96×96：边缘 24px 内才有像素 ⇒ 面板近全透明）。",
    nine={"l": 24, "t": 24, "r": 24, "b": 24})

img("cfg.page_strip", "ui/x_ui_cfg_page_strip.png", 35, 33, 1851, 113, Z["frame"],
    "页签条底（方案 §1.1「页签条底 35,33,1851,113」= PSB `タブ/オン`）。九宫格 l=t=r=b=20。",
    nine={"l": 20, "t": 20, "r": 20, "b": 20})

# 页签两枚：选中态由 cfg_page 换图（互为互斥态）。★ 图元素 y=26 / h=50 的理由见下 note。
for i, (tabx, tabw, label, act, onv, offv) in enumerate((
        (37, 181, "系统", "config_tab_1", PAGE_SYS, PAGE_SND),
        (237, 180, "声音", "config_tab_2", PAGE_SND, PAGE_SYS)), 1):
    ty = 3 + (96 - 50) // 2
    img("cfg.tab%d_on" % i, "ui/x_ui_cfg_tab_on.png", tabx, ty, tabw, 50, Z["tab_img"],
        "页签 %d「%s」**选中态**底（方案 §1.1 页签 %d = PSB `タブ/#page%d` x%d y3 w%d h96）。"
        "★ 图元素取 y=%d / h=50：素材 120×50 且九宫格 t=b=0（只横向拉伸）⇒ 纵向 1:1 的前提是"
        "**元素高 == 源高**（见 `layout\\_schema.md` §六 与 M37 `QUICK_PILL_H` 口径）；"
        "h=96 会把半径 25 的圆角端部纵向拉伸 1.92× 而变形。y=%d 即页签位(3..99)的纵向居中位。"
        "vis_when=%s。" % (i, label, i, i - 1, tabx, tabw, ty, ty, onv),
        nine={"l": 25, "t": 0, "r": 25, "b": 0}, vis=("cfg_page", onv))
    img("cfg.tab%d_off" % i, "ui/x_ui_cfg_tab_off.png", tabx, ty, tabw, 50, Z["tab_img"],
        "页签 %d「%s」**未选中态**底（同矩形；素材 `_off` 为全透明，只留极小圆角痕）。"
        "vis_when=%s。" % (i, label, offv),
        nine={"l": 25, "t": 0, "r": 25, "b": 0}, vis=("cfg_page", offv))
    txt("cfg.tab%d_tx_sel" % i, tabx, 3, tabw, 96, label, 27, C_TEXT_ON_CHIP, Z["text"],
        "页签「%s」**选中态**页签名（引擎绘制；**三层同矩形** = 方案 §1.1 的 x%d y3 w%d h96；字号 27）。"
        "★ 颜色 @palette.panel_fill #141824（**暗字**）—— **W1 数据侧修正 1**：实测 `tab_on` 胶囊中心 "
        "(122,176,232) 为浅色，浅字(@palette.text_menu)对比仅 **1.87:1（不可读）**，暗字 **7.76:1**。"
        "vis_when=%s。" % (label, tabx, tabw, onv),
        bold=True, align="center", vis=("cfg_page", onv))
    txt("cfg.tab%d_tx" % i, tabx, 3, tabw, 96, label, 27, C_TEXT_MENU, Z["text"],
        "页签「%s」**未选中态**页签名（同矩形；@palette.text_menu 浅字 —— 未选中底为全透明，浅字才可读）。"
        "vis_when=%s。" % (label, offv), bold=True, align="center", vis=("cfg_page", offv))
    hit("cfg.tab%d_hit" % i, tabx, 3, tabw, 96, act, Z["hit"],
        "页签「%s」热区（三层同矩形）。action=%s ⇒ 机制侧 `uiScreenFlagSet(\"cfg_page\",\"%s\")`"
        "（方案 §3.4）。**不带 page flag**：页签条两页共用。" % (label, act, onv))

# 右上三键 +「初始化」。★ 先声明 reset_hit：它与三键热区在 y76..79 有 3px 叠压
#   （三键按方案外扩 6px 所致），平票时**声明更晚者胜** ⇒ 让三键赢下这 3px。
hit("cfg.reset_hit", 1708, 76, 182, 76, "config_reset", Z["hit"],
    "「初始化」热区（方案 §1.1 `タブ/#reset` x1708 y76 w182 h76）。action=config_reset ⇒ "
    "机制侧把全部设置恢复 `UISettingDef` 的 def，并 `uiScreenFlagSet(\"cfg_page\",\"sys\")`（§3.4）；"
    "**只重置设置值，不动页签选择以外的状态**。带 state_group「cfg.reset」（联动按钮底换 `_over`）。"
    "★ 与下方三键热区在 y76..79 有 3px 叠压（三键按方案外扩 6px 所致）⇒ 本件**先声明**，"
    "按平票规则让三键赢下该 3px。", group="cfg.reset")
img("cfg.reset_bg", "ui/x_ui_cfg_btn.png", 1708, 76, 182, 76, Z["plate"],
    "「初始化」按钮底（通用小按钮素材，九宫格 l16 t8 r16 b8）。`state_assets` 与热区 "
    "`cfg.reset_hit` 以 state_group「cfg.reset」联动 ⇒ 悬停换 `x_ui_cfg_btn_over.png`。",
    nine={"l": 16, "t": 8, "r": 16, "b": 8},
    state_assets={"normal": "ui/x_ui_cfg_btn.png", "hover": "ui/x_ui_cfg_btn_over.png"},
    group="cfg.reset")
txt("cfg.reset_tx", 1708, 76, 182, 76, "初始化", 22, C_TEXT_MENU, Z["text"],
    "「初始化」按钮文字（引擎绘制）。", bold=True, align="center")

for bid, bx, by, bw, bh, label, act in (
        ("cfg.btn_game", 1227, 33, 206, 40, "返回游戏", "close"),
        ("cfg.btn_title", 1451, 32, 208, 41, "返回标题画面", "open_title"),
        ("cfg.btn_end", 1674, 32, 201, 41, "退出游戏", "quit_game")):
    img(bid + "_bg", "ui/x_ui_cfg_btn.png", bx, by, bw, bh, Z["plate"],
        "%s按钮底（方案 §1.1 `システム共通/オフ` x%d y%d w%d h%d；九宫格 l16 t8 r16 b8）。"
        "`state_assets` 与同矩形热区以 state_group「%s」联动 ⇒ 悬停换 `x_ui_cfg_btn_over.png`。"
        % (label, bx, by, bw, bh, bid),
        nine={"l": 16, "t": 8, "r": 16, "b": 8},
        state_assets={"normal": "ui/x_ui_cfg_btn.png", "hover": "ui/x_ui_cfg_btn_over.png"},
        group=bid)
    txt(bid + "_tx", bx, by, bw, bh, label, 18, C_TEXT_MENU, Z["text"],
        "%s文字（引擎绘制）。" % label, bold=True, align="center")
    hit(bid + "_hit", bx - 6, by - 6, bw + 12, bh + 12, act, Z["hit"],
        "%s热区（方案 §1.1：矩形外扩 6px，即 `%d,%d,%d,%d`）。action=%s（**既有动作名，非新造**）。"
        "带 state_group「%s」：悬停本件即点亮同组按钮底（联动 `_over`）。"
        % (label, bx - 6, by - 6, bw + 12, bh + 12, act, bid), group=bid)

txt("cfg.title_sys", 60, 110, 1200, 80, "系统设置", 76, C_ACCENT, Z["title"],
    "系统页页标题（字号 76 粗体 @palette.accent）。★ 几何按 **W1 数据侧修正 3**：方案 §1.1 原值 "
    "60,112,1200,110 会与下方分区小标题相撞（W2 截图实测重影）⇒ 改 **y=110 / h=80**。vis_when=sys。",
    bold=True, page=PAGE_SYS)
txt("cfg.title_snd", 60, 110, 1200, 80, "声音设置", 76, C_ACCENT, Z["title"],
    "声音页页标题（同矩形）。vis_when=snd。", bold=True, page=PAGE_SND)
BLOCKS.append(("共用（压暗 / 外框 / 页签条 / 页签 / 右上三键 / 初始化 / 两页标题）",
               len(ELEMENTS) - n0))

# ================================================================================
# 三、系统页
# ================================================================================
n0 = len(ELEMENTS)
txt("cfg.sec_picture", 60, 190, 400, 36, "画面设定", 34, C_TEXT_MENU, Z["text"],
    "分区小标题「画面设定」（**几何按 W1 数据侧修正 3**：参考作实测 ink-top = 底板 93 + bitmap 103 = "
    "canvas 196 ⇒ 取 x=60, y=190, w=400, h=36；方案 §1.2 原值 (60,155) 与页标题相撞）。",
    bold=True, page=PAGE_SYS)
txt("cfg.sec_confirm", 60, 775, 400, 36, "确认信息设定", 34, C_TEXT_MENU, Z["text"],
    "分区小标题（**W1 数据侧修正 3**：放在存档/读档两行上方约 66px ⇒ y=775）。",
    bold=True, page=PAGE_SYS)
txt("cfg.sec_text", 1000, 190, 400, 36, "文本设定", 34, C_TEXT_MENU, Z["text"],
    "分区小标题（**W1 数据侧修正 3**：与左列「画面设定」同 y=190）。", bold=True, page=PAGE_SYS)
txt("cfg.sec_preview", 1000, 672, 400, 36, "预览", 34, C_TEXT_MENU, Z["text"],
    "分区小标题（方案 §1.2「预览(1000,672)」）。", bold=True, page=PAGE_SYS)

# 左列条目名（行步进 60、条目名左沿 x=100；w=330 = 被本列首枚值按钮(445)限制的最大安全宽）
for eid, label, ry in (("cfg.row_display_lb", "画面模式", 241),
                       ("cfg.row_facewindow_lb", "立绘窗口", 301),
                       ("cfg.row_drama_lb", "演出效果", 361),
                       ("cfg.row_effect_lb", "特效", 421),
                       ("cfg.row_voicecut_lb", "语音截断", 481),
                       ("cfg.row_curhide_lb", "隐藏光标", 541),
                       ("cfg.row_savedialog_lb", "存档时的确认信息", 841),
                       ("cfg.row_loaddialog_lb", "读档时的确认信息", 901)):
    txt(eid, 100, ry, 330, 59, label, 26, C_TEXT_MENU, Z["text"],
        "配置项名「%s」（方案 §1.2 左列；y=%d，行步进 60；条目名左沿 x=100）。" % (label, ry),
        page=PAGE_SYS)
# 右列条目名（x=1000；值按钮在 1567 ⇒ 可取宽 450）
for eid, label, ry in (("cfg.row_textspeed_lb", "文字显示速度", 315),
                       ("cfg.row_autospeed_lb", "自动播放速度", 435),
                       ("cfg.row_allskip_lb", "全部跳过", 481),
                       ("cfg.row_textcolchg_lb", "文字变色", 541)):
    txt(eid, 1000, ry, 450, 59, label, 26, C_TEXT_MENU, Z["text"],
        "配置项名「%s」（方案 §1.2 右列，y=%d）。x=1000 = 该列左沿（`文本设定` 小标题同 x）；"
        "w=450 由本列值按钮左沿 1567 界定。★ 文字显示速度 / 自动播放速度的条目名 y 取"
        "「滑块元素 y − 4」（315/435），与方案 §1.2 的行 y（325/445 = 轨道 y）不同行，"
        "否则条目名会与轨道（x1249..1613）重叠。" % (label, ry), page=PAGE_SYS)

# 预留行「播放影片」（方案 §1.2 第 601 行，visible_default=false 留位）：
# ★ 刻意**不带 vis_flag** —— 带 vis_flag 却 visible_default=false 会成为死件（_schema §四 铁律）；
#   本行本就是「留位不显示」，用 visible_default=false 直白表达、不参与 flag 判定。
for eid, kind, args in (
        ("cfg.row_cfmovie_lb", "text", (100, 601, 330, 59, "播放影片", 26, C_TEXT_MENU, Z["text"])),
        ("cfg.row_cfmovie_bg", "image", ("ui/x_ui_cfg_opt_off.png", 619, 601, 115, 59, Z["plate"])),
        ("cfg.row_cfmovie_hit", "hit", (619, 601, 256, 59, "", Z["hit"]))):
    if kind == "text":
        el = txt(eid, *args, "**预留行**「播放影片」配置项名（方案 §1.2 第 601 行："
                             "「预留：播放影片，visible_default=false 留位」）。")
    elif kind == "image":
        el = img(eid, *args, "**预留行**次值底（同 `_off` 口径：透明底 + 无描边）。",
                 nine={"l": 14, "t": 6, "r": 14, "b": 6})
    else:
        el = hit(eid, *args, "**预留行**整行热区（action 留空 = 待编程组定义；本行 visible_default=false，不可达）。")
    el["visible_default"] = False

# ---- 值按钮：每选项 = 2 值底 + 2 值文字（带 cfg_v_<key>）+ 2 hit（带 cfg_page + value）----
for key, von, voff, lon, loff, cur, label, onr, offr in OPT_SYS:
    onx, ony, onw, onh = onr
    offx, offy, offw, offh = offr
    img("cfg.o_%s_on" % key, "ui/x_ui_cfg_opt_on.png", onx, ony, onw, onh, Z["plate"],
        "「%s」**当前值 = %s（%s）**的值底：`x_ui_cfg_opt_on.png`（冰蓝胶囊）九宫格 l14 t6 r14 b6。"
        "★ 当前值由 flag 表达：vis_flag=cfg_v_%s / vis_when=%s（方案 §3.4）；同一选项的两枚值底"
        "互为互斥态。`state_assets` 与同矩形热区 `cfg.o_%s_on_hit` 以 state_group「cfg.o_%s_on」"
        "联动（悬停换 `_over`、按下换 `_on`）。" % (label, lon, von, key, von, key, key),
        nine={"l": 14, "t": 6, "r": 14, "b": 6},
        state_assets={"normal": "ui/x_ui_cfg_opt_on.png",
                      "hover": "ui/x_ui_cfg_opt_over.png",
                      "pressed": "ui/x_ui_cfg_opt_on.png"},
        group="cfg.o_%s_on" % key, vis=("cfg_v_%s" % key, von))
    img("cfg.o_%s_off" % key, "ui/x_ui_cfg_opt_off.png", offx, offy, offw, offh, Z["plate"],
        "「%s」**另一值 = %s（%s）**的值底：`x_ui_cfg_opt_off.png`（方案 §二：透明 + 无描边 = 未选态无底）。"
        "★ 本件带**页 flag**（不是值 flag）：它在两种取值下都该在场 —— 常态透明（不可见），"
        "悬停时换 `opt_over` 给非当前值一侧**「可点」的悬停反馈**；若改由值 flag 控显隐，"
        "则当前值在另一侧时该按钮连悬停反馈都没有（W2 截图确认）。"
        % (label, loff, voff),
        nine={"l": 14, "t": 6, "r": 14, "b": 6},
        state_assets={"normal": "ui/x_ui_cfg_opt_off.png",
                      "hover": "ui/x_ui_cfg_opt_over.png",
                      "pressed": "ui/x_ui_cfg_opt_on.png"},
        group="cfg.o_%s_off" % key, page=PAGE_SYS)
    txt("cfg.o_%s_on_tx_sel" % key, onx, ony, onw, onh, lon, 21, C_TEXT_ON_CHIP, Z["text"],
        "「%s」值文字（%s）**当前值态 = 暗字**。vis_flag=cfg_v_%s / vis_when=%s。"
        "★ 颜色 @palette.panel_fill（**暗字**）—— **W1 数据侧修正 1**：实测 `opt_on` 胶囊中心 "
        "(126,175,225) 为浅色，浅字仅 **1.89:1**、暗字 **7.68:1**。字号 21（值按钮文字 19–22 区间）。"
        % (label, lon, key, von), bold=True, align="center", vis=("cfg_v_%s" % key, von))
    txt("cfg.o_%s_on_tx" % key, onx, ony, onw, onh, lon, 21, C_TEXT_MENU, Z["text"],
        "「%s」值文字（%s）**非当前值态 = 浅字**（该按钮此时不戴胶囊，浅字才可读）。"
        "vis_flag=cfg_v_%s / vis_when=%s。★ 与 `_on_tx_sel` 两件合起来覆盖两种取值 ⇒ 标签恒有可见者"
        "（否则非当前值一侧会「无标签但热区仍在」，控件不可被发现）。"
        % (label, lon, key, voff), bold=True, align="center", vis=("cfg_v_%s" % key, voff))
    txt("cfg.o_%s_off_tx" % key, offx, offy, offw, offh, loff, 21, C_TEXT_MENU, Z["text"],
        "「%s」值文字（%s）—— **常浅字**（带页 flag）：`x_ui_cfg_opt_off.png` 实测**全透明**（α≡0，"
        "W1 件），次值一侧在任何取值下都不戴胶囊 ⇒ 该标签始终是「无底浅字」，无需暗字变体。"
        % (label, loff), bold=True, align="center", page=PAGE_SYS)
    hit("cfg.o_%s_on_hit" % key, onx, ony, onw, onh, "config_set_%s" % key, Z["hit"],
        "「%s → %s」热区。action=**config_set_%s** + `value=\"%s\"`（动作名统一、值放 `value` 字段，"
        "见方案 §3.4 与 W2 派单要求 5）。vis_when=%s（页归属 ⇒ 不会跨页抢点击）。"
        % (label, lon, key, von, PAGE_SYS), value=von, page=PAGE_SYS, group="cfg.o_%s_on" % key)
    hit("cfg.o_%s_off_hit" % key, offx, offy, offw, offh, "config_set_%s" % key, Z["hit"],
        "「%s → %s」热区（action 同上，`value=\"%s\"`）。vis_when=%s。"
        % (label, loff, voff, PAGE_SYS), value=voff, page=PAGE_SYS, group="cfg.o_%s_off" % key)

# ---- 不透明度行（方案 §1.2 第 687 / 749 行）----
txt("cfg.row_winopac_lb", 100, 629, 330, 59, "文本窗口的不透明度", 26, C_TEXT_MENU, Z["text"],
    "配置项名「文本窗口的不透明度」（方案 §1.2 第 687 行）。★ y=629 由参考图反推："
    "参考作该条目名在滑块**上一行**（ref y≈524 ⇒ 基准 (524−52)/0.75 ≈ 629），与轨道 687 不共行 —— "
    "共行则条目名（x100..430）会与轨道（x307..671）重叠。", page=PAGE_SYS)
txt("cfg.row_winopac_hint", 307, 749, 400, 26, "越大越浓（默认 90%）", 20, C_TEXT_HINT, Z["text"],
    "说明小字（方案 §1.2 第 749 行「说明小字（可选）text『越大越浓（默认 90%）』@palette.text_hint 字号 20」；"
    "x 未给，取 307 = 轨道左端）。", page=PAGE_SYS)

# ---- 3 根系统页滑块 ----
build_slider("cfg.sl_winopac", 307, 681, 364, 24, "dlg_winopac", SLIDER_VAL["dlg_winopac"], PAGE_SYS,
             "「文本窗口的不透明度」滑块（方案 §1.2 轨道 307,687,364,11 ⇒ 元素 y=687−6=681、h=24 "
             "= 中心线口径；与 §三.1 的示例逐字一致）",
             hit_rect=(298, 663, 382, 59),                      # 方案 §三.2 示例逐字
             ends=("0%", "100%", 244, 690))                     # 方案 §1.2 两端文字(244,681)/(690,681)
build_slider("cfg.sl_textspeed", 1249, 319, 364, 24, "text_speed", SLIDER_VAL["text_speed"], PAGE_SYS,
             "「文字显示速度」滑块（方案 §1.2 轨道 1249,325,364,11 ⇒ 元素 y=319）",
             hit_rect=(1249, 305, 364, 59),                     # 旧屏 cfg.textspeed_hit 同值（PSB `#rects/textspeed`）
             ends=("慢", "快", 1180, 1630))                      # 方案 §1.2 两端文字(1180,319)/(1630,319)
build_slider("cfg.sl_autospeed", 1249, 439, 364, 24, "auto_speed", SLIDER_VAL["auto_speed"], PAGE_SYS,
             "「自动播放速度」滑块（方案 §1.2 轨道 1249,445,364,11 ⇒ 元素 y=439）",
             hit_rect=(1249, 425, 364, 59),                     # 旧屏 cfg.autospeed_hit 同值
             ends=("慢", "快", 1180, 1630))

# ---- 预览区（要求 6 的核心）----
img("cfg.pv_frame", "ui/x_ui_cfg_preview_frame.png", 1116, 733, 612, 154, Z["pv_frame"],
    "预览框（方案 §1.2「预览框 1116,733,612,154 九宫格 x_ui_cfg_preview_frame.png」）。",
    nine={"l": 24, "t": 24, "r": 24, "b": 24}, page=PAGE_SYS)
img("cfg.pv_bg", "ui/x_ui_cfg_preview_bg.png", 1116, 733, 612, 154, Z["pv_bg"],
    "预览示例底图（方案 §1.2；素材 612×154 程序化示例画面，**不使用任何原版 CG**；z 低于文字）。",
    page=PAGE_SYS)
img("cfg.pv_mask", "ui/x_ui_cfg_preview_mask.png", 1126, 743, 592, 134, Z["pv_mask"],
    "★ **预览遮罩**（方案 §1.2/§3.3）：元素 id **必须正好是 `cfg.pv_mask`** —— 机制侧按此 id 写 "
    "`ctx.opacityOverride[\"cfg.pv_mask\"]`，使其浓度 = `dlg_winopac` 的实时值。素材与 "
    "`ui/x_ui_dlgmask_bottom_350.png` **同一算法**（α = 255·t 线性）⇒ 预览与实机口径一致；"
    "元素 opacity 初值 **229**（= `floor(255×90/100)`，与运行式 `ctx.opacityOverride` 的 90% 档逐值相等；★ 2026-09-24 一审顺带 1：原写 230 与运行式差 1 ⇒ 改为同值免得后人复算；运行期仍由 `dlg_winopac` 覆盖）。"
    "★ 几何与 z 按 **W1 数据侧修正 2**：`_mask` 是满幅线性件、不做圆角（W1 为保证逐行 α 严格线性有意如此），按方案 §1.2 的满幅 (1116,733,612,154) 铺会把 `preview_frame` 的底边描边一起压黑（W1 三档对照图可见）⇒ **四边各让 10px：1126,743,592,134**；**z=15：低于 `cfg.pv_frame`(16)、高于 `cfg.pv_bg`(14)**（修正 2 的 z 次序 + 内缩双保险）。★ 纵向梯度已实测与实机同向：素材顶端 α=3 → 中线 α=128 → 底端 α=252（自上而下变浓）。★ 九宫格取**全零 {0,0,0,0}**（=「允许整图等比缩放」的合法写法，`_schema.md` §六 字段语义补充）：内缩后元素 592×134 ≠ 素材 612×154，`verify_ui` [2] 的「无 nine ⇒ w/h == PNG 实尺寸」要求必须给 nine；而**切边 nine 会在接缝处把线性渐变拉出折点**，本素材是纯线性纵向渐变 ⇒ 取全零、整体线性缩放，α 自始至终严格线性。", nine={"l": 0, "t": 0, "r": 0, "b": 0}, opacity=229, source=SRC_MASK, page=PAGE_SYS)
txt("cfg.pv_text", 1130, 745, 584, 134, "渡来同学\n……羽田君。这个时间，\n你怎么会在这里？",
    22, C_TEXT_PRIMARY, Z["text"],
    "预览文字（方案 §1.2「预览文字 1130,745,584,134；text 3 行样例，字号 22，白字 + 八向描边」）。"
    "★ 三行 = 角色名 + 对话屏既有 `sample` 台词（`dlg.text`）**按框宽折成两行**；`sample` 按 "
    "`_schema.md` 属「演示占位文本（非剧情）」⇒ **不杜撰新台词**。排版与对话框同口径：`font.outline` "
    "八向 2px 黑描边、关 shadow（照 `10_dialog.json` 白字口径）。", wrap=True, max_lines=3,
    outline=True, page=PAGE_SYS)
txt("cfg.pv_note", 1116, 893, 612, 60,
    "用于确认设定的文本窗口浓度、\n文字显示速度以及自动模式换句速度。", 20, C_TEXT_HINT, Z["text"],
    "预览说明两行（方案 §1.2「说明 1116,893,612,60；text 两行（照参考作文案译）」）。字号 20 × "
    "行距 1.4 ⇒ 单行 28px，60 高的框**只容 2 行**，第三行另立 `cfg.pv_note_x`。",
    wrap=True, max_lines=2, page=PAGE_SYS)
txt("cfg.pv_note_x", 1116, 953, 612, 26, "不透明度同时影响实机对话框。", 20, C_TEXT_HINT, Z["text"],
    "预览说明补行（方案 §1.2「＋下一行补『不透明度同时影响实机对话框』」）。★ 单独立件的原因："
    "方案给的说明框只有 60 高（= 2 行 @ 20 号）；本行 y=953 紧接说明框下沿，仍在外框（底 1046）之内。",
    page=PAGE_SYS)
BLOCKS.append(("系统页（分区小标题 / 条目名 / 值按钮 / 不透明度行 / 3 滑块 / 预览区）",
               len(ELEMENTS) - n0))

# ================================================================================
# 四、声音页
# ================================================================================
n0 = len(ELEMENTS)
txt("cfg.sec_volume", 60, 225, 400, 36, "音量设定", 34, C_TEXT_MENU, Z["text"],
    "分区小标题（方案 §1.3「音量设定(60,225)」）。", bold=True, page=PAGE_SND)
txt("cfg.sec_voice", 60, 825, 400, 36, "语音设定", 34, C_TEXT_MENU, Z["text"],
    "分区小标题（方案 §1.3「第二分区 语音设定(60,825)」）。", bold=True, page=PAGE_SND)
txt("cfg.sec_charvoice", 1099, 215, 400, 36, "角色语音设定", 34, C_TEXT_MENU, Z["text"],
    "分区小标题（方案 §1.3 右列「分区标题 1099,215 text『角色语音设定』字号 34」）。",
    bold=True, page=PAGE_SND)


def build_vol_row(setting, label, ry, spk, sid, *, mute_x=ROW_X, with_label=True,
                  label_x=100, label_y=None):
    """声音页音量行（方案 §1.3「每行共用几何」；行基准 x 默认 244，角色音量行 1111）。"""
    if with_label:
        txt("cfg.snd_%s_lb" % setting, label_x, (ry - 42) if label_y is None else label_y,
            300, 32, label, 26, C_TEXT_MENU, Z["text"],
            "音量行行名「%s」（方案 §1.3 行名；方案未给坐标 ⇒ 取条目名左沿 x=100，y = 行 y − 42："
            "参考图行名在滑块**上一行**（ref y≈259 ⇒ (259−52)/0.75 ≈ 276 = 318−42），与轨道不共行。）"
            % label, page=PAGE_SND)
    if spk:
        img("cfg.snd_%s_spk" % setting, "ui/x_ui_cfg_spk.png", mute_x + ROW_OFF["spk"], ry - 9, 22, 32,
            Z["dot"], "喇叭 icon（**几何按 W1 数据侧修正 3**：`x=行基准−48, y=行y−9, 22×32` —— "
                      "参考作实测 `再生/オフ` = (196,315,22,32) 对行 y=318 的换算；与 `MIN`(x=244) 不重叠；"
                      "素材 22×32 无九宫格 ⇒ w/h == 实尺寸）。",
            page=PAGE_SND)
    # 静音勾选框：两枚值底互为互斥态；「静音」标签是常显 chrome ⇒ 带页 flag
    txt("cfg.snd_%s_mute_lb" % setting, mute_x + ROW_OFF["mute_lb"], ry, 89, 21, "静音", 19,
        C_TEXT_MENU, Z["text"],
        "静音标签（方案 §1.3「文字『静音』(775,行y,89,21)」= 行基准 x+531）。★ 本件是**常显标签**"
        "（内容不随勾选态变化）⇒ 带页 flag 而非值 flag。", page=PAGE_SND)
    img("cfg.o_mute_%s_off" % setting, "ui/x_ui_cfg_chk_off.png", mute_x + ROW_OFF["mute"], ry, 21, 21,
        Z["plate"],
        "静音勾选框**未勾选**（空框）态（方案 §1.3「MUTE 勾选框 (843,行y,21,21)」= 行基准 x+599）。"
        "★ 本件带**页 flag**：空框是常显底（勾选态的另一件叠在它之上）⇒ 与真复选框的外观一致"
        "（空框 + 勾），且默认不静音时**不会**有元素泄漏到系统页。", page=PAGE_SND)
    img("cfg.o_mute_%s_on" % setting, "ui/x_ui_cfg_chk_on.png", mute_x + ROW_OFF["mute"], ry, 21, 21,
        Z["plate"] + 1,
        "静音勾选框**已勾选**态（勾 + 框），叠在空框之上（z=%d > 空框的 %d）。"
        "vis_flag=cfg_v_mute_%s / vis_when=on —— 仍是「当前值由 flag 表达」。（方案 §二 未给勾选框的"
        "悬停件 ⇒ 本件不带 state_assets / state_group。）" % (Z["plate"] + 1, Z["plate"], setting),
        vis=("cfg_v_mute_%s" % setting, "on"))
    hit("cfg.o_mute_%s_on_hit" % setting, mute_x + ROW_OFF["mute"], ry, 21, 21,
        "config_set_mute_%s" % setting, Z["hit"],
        "「静音 → 开」热区 = **勾选框本体**。action=config_set_mute_%s + `value=\"on\"`。"
        "★ 复选框只有**一个**方框位（参考作口径），而 `value` 是**静态**字段 ⇒ 两枚 hit 取"
        "**互不重叠**的两个矩形（方框 = 开 / 左邻的「静音」标签 = 关）：若两枚同矩形叠放，"
        "平票只让后声明者可达、另一枚成死件（`_schema` §四 铁律一）。"
        "z=96 > 整行拖动热区(95) ⇒ 按「更具体的子控件赢」不会被子控件被吞（同 §四 铁律二）。"
        % setting, value="on", page=PAGE_SND)
    hit("cfg.o_mute_%s_off_hit" % setting, mute_x + ROW_OFF["mute_lb"], ry, 68, 21,
        "config_set_mute_%s" % setting, Z["hit"],
        "「静音 → 关」热区 = 「静音」标签矩形（**右缘 68px 止于方框左沿，与 `_on_hit` 无重叠**）。"
        "action 同上 + `value=\"off\"`。vis_when=%s。" % PAGE_SND, value="off", page=PAGE_SND)
    build_slider(sid, mute_x + ROW_OFF["rail"], ry - 6, 364, 24, setting, SLIDER_VAL[setting],
                 PAGE_SND,
                 "音量行 %s「%s」滑块（方案 §1.3 每行共用几何：轨道 x=行基准+63、y=行y、w=364、h=11）"
                 % (sid, label or "角色音量"),
                 hit_rect=(mute_x, ry, 620, 21),                # 方案 §1.3「整行命中矩形 (244,行y,620,21)」
                 ends=("MIN", "MAX", mute_x, mute_x + ROW_OFF["max"]),
                 end_y=ry - 6)                                  # 方案 §1.3「MIN(244,行y-6,46,21)」


for setting, label, ry, spk in VOL_ROWS:
    build_vol_row(setting, label, ry, spk, "cfg.sl_" + setting[len("vol_"):])

# 角色音量行（右列；行基准 x=1111 = PSB `#sliders/chvol` (1111,540,620,21) ⇒ 按「行结构同」的偏移：
#   轨道 1111+63=1174、MIN 1111、MAX 1557、静音 1642、勾选框 1710、喇叭 1063、行 hit (1111,540,620,21)；
#   行名「角色音量」放 (1099,498,300,32)（**W1 修正 3c：不压轨道带**，在轨道 y=540 上方、横幅下沿之下）。
build_vol_row("vol_char", "角色音量", 540, True, "cfg.sl_char", mute_x=1111,
              label_x=1099, label_y=498)

# ---- 角色横幅（§1.3 右列）----
img("cfg.banner_frame", "ui/x_ui_cfg_preview_frame.png", 1099, 261, 644, 239, Z["pv_frame"],
    "角色横幅框（方案 §1.3「角色横幅框 1099,261,644,239 九宫格 x_ui_cfg_preview_frame.png（同素材）」）。",
    nine={"l": 24, "t": 24, "r": 24, "b": 24}, page=PAGE_SND)

# ★★ 2026-09-24 主代理裁决（第三轮 · 修功能缺口）：横幅**头像 + 角色名**由「单件静态 demo」
#    改为**每族一件、以 cfg_vchar 互斥可见**（零机制新增，与列表选中态同一套 flag）。
#    · 文件名**显式列出**（见 FACE_FILES；不靠 glob 猜前缀），基底取该族图数最多的基底；
#    · 头像素材 276×345（`face\` 实测；M44 清单写的 360×450 与磁盘实况不符，**以磁盘实测为准**）
#      ⇒ 栏位高 239 等比缩放 ⇒ 191×239，底对齐、水平居中于栏位右端（1540..1731）；
#    · 角色名 = 该族中文名，字号 40，与列表同一套写形（含「待入表」标记口径见 note ⑤.4）。
for fam, name, prov in CHARS:
    fn = FACE_FILES[fam]
    img("cfg.pv_face_%s" % fam, "face/" + fn, 1540, 261, 191, 239, Z["avatar"],
        "★ 角色「%s」的**横幅头像**（族 `%s` ⇒ `face/%s`）。"
        "**纯数据驱动的换人**：vis_flag=cfg_vchar / vis_when=%s ⇒ 点列表里该族即换到这张脸"
        "（33 件互斥，零机制新增；同一张 flag 也是列表选中态用的）。"
        "★ 素材 276×345（`face\\` 磁盘实测；M44 `头像素材清单.md` 写 360×450 与实况不符，**以实测为准**、"
        "W2 已如实登记）⇒ 按**栏位高 239 等比缩放**到 191×239（系数 0.693，缩小无模糊），"
        "九宫格取**全零**（`_schema.md` §六「允许整图等比缩放」的合法写法，故 w/h ≠ PNG 实尺寸属合规）。"
        "★ 栏位沿用第二轮的定版：右端 1540..1731（右留 12px，照参考作人像贴右端），与名字区 1119..1509 不重叠。"
        "★ 运行期：换角色 = 机制侧 `uiScreenFlagSet(\"cfg_vchar\", <族>)`（与列表点击同一动作）。"
        % (name, fam, fn, fam), nine={"l": 0, "t": 0, "r": 0, "b": 0},
        source=SRC_FACE, vis=("cfg_vchar", fam))
    txt("cfg.pv_name_%s" % fam, 1119, 300, 390, 60, name, 40, C_TEXT_NAME, Z["text"],
        "★ 角色「%s」的**横幅角色名**（族 `%s`）。vis_flag=cfg_vchar / vis_when=%s ⇒ 与同族头像、"
        "列表选中态同步换人。字号 40 粗体 @palette.text_name（参考作把名字烘焙在横幅里，我们自己画）；"
        "位置照参考作实测 1119,300,390,60（名字墨迹起于 ref x≈895 ⇒ 基准 ≈1192，在横幅左半）⇒ "
        "名字区 1119..1509，最长 8 字「ＬＲ２００１」@40 号 = 320px 也不与右端头像（1540 起）相撞。%s"
        % (name, fam, fam, tag_for(prov)), vis=("cfg_vchar", fam))

# ---- 角色列表（33 项 × 5 件）----
for idx, (fam, name, prov) in enumerate(CHARS):
    col, row = idx // 11, idx % 11
    cx = CHAR_COLS[col]
    ry = CHAR_ROW0 + CHAR_STEP * row
    tag = "" if prov == "有据" else "（译名待入表）"
    img("cfg.ch_%s_pill" % fam, "ui/x_ui_cfg_name_sel.png", cx, ry, 250, CHAR_CELL_H, Z["pill"],
        "角色「%s」**选中态胶囊**（方案 §1.3「选中态：`cfg.ch_<族>_pill`(image `x_ui_cfg_name_sel.png` "
        "九宫格，同矩形，`z` 比文字低）」）。素材 80×43、圆角 8（方案 §二）⇒ 九宫格取 "
        "**l=r=16 / t=b=8**：上下 8px 带 1:1 保留圆角弧、中段（直边）纵向压缩到 36 高**不产生形变**"
        "（**不得**用 t=b=0：那是「纵向 1:1」口径，元素高须 == 源高 43，36 高会把圆角端压扁）。"
        "vis_flag=cfg_vchar / vis_when=%s（选中项才显示，零新机制）。"
        "★ z=30 **低于** `cfg.ch_%s_tx`(32) 与 `_tx_sel`(33)（否则文字被胶囊盖住，W2 派单要求 6）。"
        % (name, fam, fam),
        nine={"l": 16, "t": 8, "r": 16, "b": 8}, vis=("cfg_vchar", fam))
    img("cfg.ch_%s_dot" % fam, "ui/x_ui_cfg_dot.png", cx + 6, ry + CHAR_DOT_DY, 12, 12, Z["dot"],
        "角色「%s」列表圆点（方案 §1.3「`cfg.ch_<族>_dot`(image `x_ui_cfg_dot.png` 12×12，x=列x+6)」；"
        "y 随单元高改版 **在 36 高单元内居中 ⇒ 行y+12**）。素材 12×12 无九宫格 ⇒ w/h == 实尺寸。"
        % name, page=PAGE_SND)
    txt("cfg.ch_%s_tx" % fam, cx + 26, ry, 224, CHAR_CELL_H, name, 20, C_TEXT_MENU, Z["text"],
        "角色「%s」列表名（方案 §1.3 的 (x=列x+26, y=行y, w=224) 不变；**字号 22 → 20、单元高 43 → 36** "
        "随 2026-09-24 越界修复同步）。%s" % (name, tag), page=PAGE_SND)
    txt("cfg.ch_%s_tx_sel" % fam, cx + 26, ry, 224, CHAR_CELL_H, name, 20, C_TEXT_MENU_SEL, Z["tx_sel"],
        "角色「%s」**选中态**文字（方案 §1.3：同样式但 @palette.text_menu_sel；vis_flag=cfg_vchar / "
        "vis_when=%s）。z=33 **高于**同组胶囊(30) ⇒ 文字压在胶囊之上。"
        "★ 颜色**保持浅字（有意例外于 W1 修正 1）**：实测 `x_ui_cfg_name_sel.png` 中心为 "
        "**(58,90,154,α150) 的深蓝胶囊**（不是 `tab_on`/`opt_on` 那种浅色胶囊）—— 浅字对比 **5.62:1**，"
        "而 @palette.panel_fill 暗字仅 **2.62:1** ⇒ 此处暗字反而不可读，故不改。%s" % (name, fam, tag),
        vis=("cfg_vchar", fam))
    hit("cfg.ch_%s_hit" % fam, cx, ry, 250, CHAR_CELL_H, "config_char_%s" % fam, Z["hit"],
        "角色「%s」选择热区（方案 §1.3「`cfg.ch_<族>_hit`(hit 250×单元高，action=\"config_char_<族>\")」；"
        "单元高与行步进随 2026-09-24 越界修复改为 36 / 39）。"
        "action=config_char_%s ⇒ 机制侧 `uiScreenFlagSet(\"cfg_vchar\",\"%s\")`（§3.4）。"
        "★ 不带 state_group：本项只有常规/选中两态，选中态由 flag 表达（既有机制），不参与悬停检测。"
        % (name, fam, fam), page=PAGE_SND)
BLOCKS.append(("声音页（分区小标题 / 5 音量行 / 角色音量行 / 横幅 / 33 项角色列表）",
               len(ELEMENTS) - n0))

# ================================================================================
# 五、flags_default
# ================================================================================
FLAGS = {"cfg_page": PAGE_SYS, "cfg_vchar": "asu"}
for key, von, voff, lon, loff, cur, label, onr, offr in OPT_SYS:
    FLAGS["cfg_v_%s" % key] = cur
for setting, label, ry, spk in VOL_ROWS:
    FLAGS["cfg_v_mute_%s" % setting] = "off"
FLAGS["cfg_v_mute_vol_char"] = "off"

# ================================================================================
# 六、屏 note
# ================================================================================
TUI = [n for n in CHARS if n[2] == "待入表"]
NOTE = """**M47（2026-09-24）· 设置屏整体重设（两页：系统 / 声音）**。本屏由 W2（数据模块）按接口冻结书 `_工作\\M47_设置屏重设方案.md` 重写，**整体替换 M34 版旧 config 屏**（旧屏 121 件、无 `vis_flag`/`flags_default` ⇒ 分页未实现；`config_tab_1..4` 动作无实现；滑条/勾选框/角色列 action 全空；解出素材仅 12 件 ⇒ 用户裁定整体重做）。

**① 设计依据**
· **用户 2026-09-24 指令要点**：设置分**两个页面**（系统 / 声音）；从标题界面 / 对话框侧边栏进入后**默认展示「系统」页**；风格简单（同参考作）、**透明背景**、绘出**一个总体巨型方框**放选项、**选项文字直接写在屏上锚定**、**用我们的配色**；按钮 / 滑动件参考参考作设计 + 我们的配色；两页布局**完全复刻**参考作；并复刻「文本窗口的不透明度」⇒ 让用户自定义**对话框遮罩浓度**、像参考作那样**在右侧展示预览**。声音页追加：角色名列表需要很大空间（本作角色远多于参考作）、角色名按钮要**常规态 / 选中态**两形态、人物形象预览**直接用对话框那张头像图**。
· **几何来源**：本屏每个元素的 x/y/w/h 均取自参考作《交汇协奏曲》`locale_cn.xp3` 内 PSB 容器 **idx 80** 的图层 `left/top/width/height`（基准 1920×1080，与本作画布一致）；逐条台账 `_工作\\M34_交汇协奏曲UI布局规格.md:574-718`，方案 §1.1/§1.2/§1.3 已逐行列出。行步进照参考作：系统页左列 60、声音页音量行 120；**角色列表 39**（方案 §1.3 原写 43，2026-09-24 因越框裁决改为 39，见 ⑤.5）。
· **只借结构不借像素**：参考作底板（大标题 / 分区标题 / 条目名 / 点线引导 / 滑块轨道）**都是烘焙图**，本工程铁律禁止图片化文字 ⇒ 文字一律引擎绘制、材质与配色用我方冰蓝霜白族；字形 / 字重与参考作必有差异（方案 §六.6）。
· **透明背景**：不做底图，只留 `cfg.dim`（`@palette.backdrop` × 70）保证文字可读；要更透改此件 opacity（单点可调）。

**② 数据来源声明（★ 重要）**
· 本屏 JSON 由 `_工作\\M47_设置屏重设\\复现脚本\\m47_build_config.py` **一次性**产出（脚本内元素由数据表驱动：行表 / 角色表 / 滑块表）。
· **此后本 JSON 即真相源、按手工维护**（`editor_ui.js` 导出、坐标微调、文案改动均直接落在本文件）；**生成器已退休**，重跑脚本会覆盖这些手改。
· 退休动作（删 `工具\\m34_build_screens.py` 的 `build_config`、去 `工具\\test_gen_sync.py` 的 GENERATORS 条目）由**主代理统一执行**；本模块不碰 `工具\\**`。
· 素材 **20 件**由 W1 出（`工具\\m47_make_config_assets.py`；方案 §二 表即 20 行 —— ★ 2026-09-24 一审顺带 2 订正本节原写的「19 件」），文件名为冻结项（方案 §二）。本屏**不再引用**旧屏 12 件素材（`x_ui_opt_off` / `btn_m_off` / `tab_on` / `tab_off` / `slider_rail` / `slider_knob` / `vol_rail` / `tgl_off` / `check_off` / `replay_off` / `charset_off` / `charrow`）——**一件都不删除**（`btn_m_off`/`tab_on`/`tab_off` 跨 4 屏共用）。

**③ 分页与选中态（`flags_default` + `vis_flag`/`vis_when`）**
· 屏级 `flags_default`：`cfg_page=sys`（**默认系统页**，用户要求 2）｜`cfg_vchar=asu`（默认选中角色 = 列表首项）｜`cfg_v_<key>` = 系统页 10 个选项的当前值（`display=window`、`facewindow=on`、`drama=on`、`effect=on`、`voicecut=off`、`curhide=off`、`savedialog=on`、`loaddialog=on`、`allskip=off`、`textcolchg=on`）｜`cfg_v_mute_<行>=off`（声音页 6 行静音勾选，默认不静音）。
· **两页互斥**：属某页的元素一律 `vis_flag="cfg_page"` + `vis_when="sys"|"snd"`，且 `visible_default:true`（铁律：靠 flag 控显隐的元素写 false 会成死件）。页签条两页共用，故页签图/字/热区**不带页 flag**。
· **选中角色**：33 项各带 `vis_flag="cfg_vchar"` + `vis_when="<族名>"` 的胶囊与选中态文字（既有 flag 机制的既有用法，零新机制）。
· **当前值（实际采用的写法，见 note ⑥ 的取舍）**：
  · 值底：**主值底** `cfg.o_<key>_on`（冰蓝胶囊）带 `vis_flag="cfg_v_<key>"` + `vis_when=<主值>`（`on`／`window`）；**次值底** `cfg.o_<key>_off` 带**页 flag** —— 实测该素材**全透明**（α≡0），它是「未选态无底 + 悬停换 `_over`」的静态层，两种取值下都该在场。
  · 值文字：主值标签**两件互斥** —— `cfg.o_<key>_on_tx_sel`（**暗字**，当前值态、压在胶囊上）与 `cfg.o_<key>_on_tx`（浅字，非当前值态），两件都带 `vis_flag="cfg_v_<key>"`（`vis_when` 分别为主值 / 次值）⇒ 标签恒有可见者；次值标签 `cfg.o_<key>_off_tx` 带**页 flag**（次值侧任何取值都不戴胶囊 ⇒ 常浅字）。
  · 字色依 **W1 数据侧修正 1**：`opt_on`/`tab_on` 实测为浅色胶囊（中心 (126,175,225)/(122,176,232)），浅字对比仅 1.89/1.87:1 ⇒ **胶囊上的字一律暗色**（暗字 7.68/7.76:1）。
· 动作：`config_tab_1/2`（页签）、`config_char_<族>`（角色）、`config_set_<key>` + `value`（值按钮）、`config_reset`（初始化）；右上三键复用**既有**动作名 `close` / `open_title` / `quit_game`（未新造动作名）。

**④ 滑块与设置键对照表**（字段按方案 §三.1：`min/max/step/value/setting/rail/handle`）

| 元素 id | setting（设置仓键名） | 元素框 x,y,w,h | min–max / step | 初值 value | 刻度 |
| --- | --- | --- | --- | --- | --- |
| `cfg.sl_winopac` | `dlg_winopac` | 307,681,364,24 | 0–100 / 5 | 90 | `0%` / `100%` |
| `cfg.sl_textspeed` | `text_speed` | 1249,319,364,24 | 0–100 / 5 | 50 | `慢` / `快` |
| `cfg.sl_autospeed` | `auto_speed` | 1249,439,364,24 | 0–100 / 5 | 50 | `慢` / `快` |
| `cfg.sl_master` | `vol_master` | 307,312,364,24 | 0–100 / 5 | 100 | `MIN` / `MAX` |
| `cfg.sl_bgm` | `vol_bgm` | 307,432,364,24 | 0–100 / 5 | 90 | `MIN` / `MAX` |
| `cfg.sl_se` | `vol_se` | 307,552,364,24 | 0–100 / 5 | 90 | `MIN` / `MAX` |
| `cfg.sl_sysse` | `vol_sysse` | 307,672,364,24 | 0–100 / 5 | 80 | `MIN` / `MAX` |
| `cfg.sl_voice` | `vol_voice` | 307,912,364,24 | 0–100 / 5 | 100 | `MIN` / `MAX` |
| `cfg.sl_char` | `vol_char` | 1174,534,364,24 | 0–100 / 5 | 100 | `MIN` / `MAX` |

· 每根滑块配 1 枚**拖动 hit**（`<slider id>_hit`，带 `slider="<slider id>"` 字段，方案 §3.2）；元素 y = 轨道 y − 6（h=24 ⇒ 轨道落在元素中心线）。
· **`value` 三方一致（★ 2026-09-24 一审 Major 3 订正后的硬口径）**：元素 `value` 必须与 **① 本 JSON 的元素 `value`、② `krkr\\game\\ui_settings.tjs` 的 `UISettingDef[k].def`、③ `复刻\\replica.js` 的 `SETTING_DEF[k].def`（replica.js:1566-1575）** 三者**逐值相同**；**改任一处必须同改另两处**（渲染实际吃 `def`，JSON 写别的值就是假初值 —— 一审实测曾偏差：`text_speed` 50/60、`vol_master|voice|char` 100/80、`vol_bgm|se` 90/80，**已全部改回 def 值**）。下表为订正后终值。
· 不透明度实时生效链路（方案 §3.3）：`cfg.sl_winopac` → `UISettingGet("dlg_winopac")` → `ctx.opacityOverride["dlg.mask_bottom"]`（实机对话框遮罩）与 `ctx.opacityOverride["cfg.pv_mask"]`（本屏预览遮罩；元素 id 即 **`cfg.pv_mask`**，元素 opacity 初值 **229** = floor(255×90/100) 与运行式逐值相等）。

**⑤ 如实登记（未完成 / 待编程组 / 待入表）**
1. **五人格主角（鹰志 / 鹫介 / 隼人 / 迦楼罗 / 小鹰志）无立绘与头像素材**（侦察 C：`chr` 前缀计数 0）⇒ **不进**角色列表。列表 33 项 = 35 族 − `kab`（与 `kaa` 同属翔，合并为 1 项）− `y`（杂项待判读）。是否给主角做「无头像占位」**留给用户裁决**。
2. **音量类滑块只存值、无音频可接**：本作引擎侧**零音频代码**（无 SoundBuffer / volume）⇒ `vol_master/bgm/se/sysse/voice/char` 六键仅落设置仓 + 持久化，**待编程组接音频**后才有实效果。
3. **横幅头像与角色名已改为「每族一件、flag 互斥」**（★ 2026-09-24 第三轮主代理裁决，修「点别的角色名横幅不变」这一**无人负责的功能缺口**；纯数据、零机制新增）：
   · 新增 **33 件 `cfg.pv_face_<族>`**（`asset` = `face/<族><基底>.png`，文件名**显式列出**于脚本 `FACE_FILES`，不靠 glob）与 **33 件 `cfg.pv_name_<族>`**（文案 = 该族中文名），两类都带 `vis_flag="cfg_vchar"` + `vis_when="<族名>"`（与列表选中态**同一套 flag**）⇒ 点列表即换脸换名；原「单件静态 demo」两件（`cfg.banner_face` / `cfg.banner_name`）**已删除**（否则默认族双显）。
   · 头像素材 **实测 276×345**（`face\\` 33 件尺寸集合 = {(276,345)}；M44 `头像素材清单.md` 记的 360×450 与磁盘实况不符，**以实测为准**）⇒ 按栏位高 239 等比缩到 **191×239**（系数 0.693，缩小无模糊），九宫格全零（`_schema.md` §六「允许整图等比缩放」）；栏位沿用第二轮定版 1540,261（右端、右留 12px）。
   · **族→文件取自「该族图数最多的基底」**：`asu07 / hiy01 / eri01 / miy01 / kin01 / nar01 / kob01 / ai_01 / mis01 / har01 / aki01 / kan01 / yuu01 / sak01 / saw01 / ari01 / min01 / pur01 / men01 / mit01 / kyo01 / dai01 / kaz02 / ten01 / kur02 / mas01 / ban01 / chi01 / lr201 / mar01 / kaa01 / bok01 / dab01`（**33 族 33 件，无缺族**；生成期自检断言存在 + 尺寸一致）。
   · **命名空间：三端均已支持 `face/`（★ 2026-09-24 更新，本项已闭环）** —— ① **守门** `工具\\verify_ui.py`：`asset_to_filename` 改为「相对 `krkr/assets/` 的路径，首段即命名空间」，并新增**可再生产物命名空间白名单** `REPRODUCIBLE_NS = ("face",)`（无命名空间的历史写法仍回落 `ui/x.png`；打错的命名空间仍报缺件）⇒ 本屏 `face/…` 引用**已通过 [1]**（此前 66 处失败的那一轮根因是该规则尚未放开）；② **HTML 复刻** `复刻\\replica.js`：资产根改 `krkr/assets/`、命名空间 = 串首段 ⇒ `face/asu07.png` 落到 `krkr/assets/face/`（第三轮截图里的「缺件」框已消失，横幅头像**可见**）；③ **引擎** `krkr\\game\\ui_asset.tjs:75-83` 的候选名 ② `assets/<串>` 本就命中。⇒ 数据侧无需改动，**本项闭环**。
   · **音量行简化（如实登记，对齐参考作结构）**：`cfg.sl_char` 的 `setting` 固定为单一 `vol_char`，即「**一条滑块作用于当前选中角色**」（选中者由 `cfg_vchar` 决定，机制侧写入该键即作用于当前角色）；**不**为 33 族各开一个设置键 —— 与参考作「一条角色音量滑块 + 一个选中列表」的结构一致（★ 2026-09-24 主代理裁决「保持现状」，不改数据）。
4. **角色名译名待入表 @@TUI_N@@ 条**（作品层 `术语表.md` 无该写形的明确条目；按派单用方案 §1.3 的暂定写法并标注；**逐条清单见 `_工作\\M47_设置屏重设\\角色名待入表.md`**，含族名 / 中文暂定名 / 原文写法 / 证据来源 / 置信度）：@@TUI_LIST@@。
   有明确条目者（**11 条**）：渡来明日香（§5.1/§六 写形）、小鸠（§2.6）、春日春惠（§2.1 `春日春恵`→春惠）、吉川（§5.2）、布露波卢冴子（§2.1 `ブルボンヌ冴子`）、普纳奇纳（§2.1 `プラチナ`）、面魔（§2.1 `メンマ`）、巴尼Ｄ（§2.1 `バニィＤ`）、奇肯多（§2.1 `チケドン`）、翔（§2.6/§5.2）、**凤鸣（★ 2026-09-24 裁决：术语表 §5.1 明写 `鳳 鳴`（鳳翔之妹）→「中文均作『凤鸣』」；本屏原暂定「鸣」已按作品层术语表改正）**。
5. **角色列表几何（2026-09-24 两条硬约束 —— 纵向见第一轮、横向见一审阻塞 2）**：3 列 × 11 行，**列距 250 ⇒ 列 x = 1126 / 1376 / 1626**（一审阻塞 2：原列距 260 使第 3 列右沿落到 1896，越过巨型外框右沿 —— 外框 33..1886、框线实测 x≈1876..1880，且 `name_sel` 横向 α 恒 150 直抵边缘 ⇒ 选中第 3 列角色时实色胶囊会**穿出框线**）；**横向硬约束 = 末列右沿 1626+250 = 1876 ≤ 1876 ✓**（已用渲染像素复核）；**单元 250×36、行步进 39、首行 y=588** ⇒ 行 y = 588,627,…,978，**末行单元 978..1014**（≤ 硬约束 1022，≤ 巨型外框内沿 1046）✓；随单元高变化，**文字字号 22 → 20**、**圆点 y = 行y+12**（12×12 在 36 高单元内居中）、胶囊九宫格由 t=b=0 改为 **t=b=8**（保圆角弧 1:1、中段直边压缩无形变）。
   改前（方案 §1.3 原值「首行 592 / 步进 43 / 单元 43」）末行单元底 = **1065**（越外框内沿 19px）、第 3 列右沿 = **1896**（越外框右沿 20px）⇒ 两处均按 2026-09-24 裁决修正。
6. **预留行三件 `cfg.row_cfmovie_lb` / `cfg.row_cfmovie_bg` / `cfg.row_cfmovie_hit`**（方案 §1.2 第 601 行「预留：播放影片」）：**刻意 `visible_default:false` 且不带任何 flag** —— 它们不是「靠 flag 控显隐」的元素，而是**永久预留**的占位（「带 vis_flag 却关默认」才是死件；本组连 flag 都没有，故**不**受死件铁律约束）。**后人勿按铁律改成带 flag**；启用该行时再补 flag 与动作名。
7. 预览说明框（方案 §1.2「1116,893,612,60」）在字号 20 × 行距 1.4（28px/行）下**只容 2 行** ⇒ 方案要求的第三行另立 `cfg.pv_note_x`（1116,953）。
8. **胶囊只戴在「主值」一侧（素材语义，非数据缺陷）**：实测 `x_ui_cfg_opt_off.png` 全透明（α≡0）、`x_ui_cfg_opt_on.png` 是浅色胶囊 ⇒ 视觉语言 =「主值（ON／窗口模式）戴胶囊，次值（OFF／全屏模式）无底」。故主值当前时 = 胶囊 + 暗字；次值当前时 = 无胶囊 + 两侧皆浅字。两种取值仍可读出（有胶囊 = 主值，无胶囊 = 次值），但与参考作「当前值那枚一律戴高亮」有一处差异。若要两侧都戴高亮底，需 W1 另出一版不透明次值底（**待裁决**）。
9. **选中角色名文字保持浅字（有意例外于 W1 修正 1）**：实测 `x_ui_cfg_name_sel.png` 中心 = **(58,90,154,α150) 深蓝胶囊**（不是 `tab_on`/`opt_on` 的浅色胶囊）⇒ 浅字 5.62:1、`@palette.panel_fill` 暗字仅 2.62:1，暗字反而不可读，故不改。
10. 页签图元素取 **y=26 / h=50**（页签位 37,3,181,96 的纵向居中位）而非表值的 h=96：素材 120×50 且九宫格 **t=b=0（只横向拉伸）**，纵向 1:1 的前提是元素高 == 源高；h=96 会把半径 25 的圆角端部纵向拉伸 1.92× 而变形。文字与热区仍用方案表值的三层同矩形（37,3,181,96）。

**⑥ 跨页泄漏：机制侧**已实现**派生（★ 2026-09-24 一审后重写 —— 本段为现状说明，不再是待办）**

· **背景（数据为何只能这样写）**：判定语义里 `vis_flag` 只允许**一对**（`layout\\_schema.md` §四；`ui_screens.tjs::uiScreenElementVisible` 有判据指纹守门），而本屏有 **4 类元素只带「值 / 选中」flag、不带页 flag**：① 值按钮的主值底与主值标签（`cfg.o_<key>_on` / `cfg.o_<key>_on_tx_sel` / `cfg.o_<key>_on_tx`）；② 静音勾选态（`cfg.o_mute_<行>_on`）；③ 角色选中胶囊与选中名（`cfg.ch_<族>_pill` / `cfg.ch_<族>_tx_sel`）；④ **横幅头像与角色名（`cfg.pv_face_<族>` / `cfg.pv_name_<族>`，第三轮新增，同样只带 `cfg_vchar`）**。若不做派生，它们会在另一页显形。

· **机制侧实现（两端同名函数、同口径）**：
  · krkr：`ui_screens.tjs::uiScreenConfigSyncPage(page)`（**第 1343 行**）—— 三步 **「记忆 → 播种 → 派生」**：先记住每个值键的当前有效值（`uiScreenConfigMemoSet`；`cfg_vchar` 这类**无设置项**的值键只靠它跨页存活）→ 把仓里还没有的设置键按当前 flag 播种（`noApply`）→ 最后**非新页的键置空串、新页的键按三级优先链取回**（`uiScreenConfigRestoreValue`）。
  · HTML：`replica.js::configDerivePageFlags(page)`（**第 3452 行**）同口径。
· **三个装入点 + 单设写完后各自重派生**：
  · ① 进屏：krkr `uiScreenConfigFlagsInitFor`（`ui_screens.tjs:1390`）｜② 切页：krkr `ui_screens.tjs:2038` · HTML `replica.js:3314` ｜③ 初始化：krkr `ui_screens.tjs:2055` · HTML `replica.js:3331`；
  · `config_set_<key>` 与 `config_char_<族>` **写完后各自再派生一次**（krkr `ui_screens.tjs:2118` / `:2069`；HTML `replica.js:3446` —— 目的：在非本页派发时**值只进记忆、不上屏**，切回该页再恢复）。
· **派生后实测**：**系统页可见 115 件、声音页可见 187 件、跨页残留 0 件**（本模块按「非本页键置空」规则独立复算，与机制侧实测一致；复算脚本口径 = 键→页归属取自 hit 的 `vis_flag/vis_when`，见下条）。
· **数据侧义务（已满足；改数据时须同步）**：每个值键的**页归属必须能从本屏数据导出** —— 本屏把它写在 `config_set_<key>` / `config_char_<族>` 的 hit 上（`vis_flag:"cfg_page"` + `vis_when:"sys"|"snd"`），机制即按此判页。**改键名、增删选项或改页归属时，必须同步改这些 hit 的 `vis_when`**，否则派生会把该键判到错误的页上。**旗标结构（一对 flag/元素）不得再动。**

**⑦ 旧 id → 新 id 对照要点**（旧 121 件 id 除本节末行注明的 5 个外**一律未沿用**，避免与旧语义混淆）
· `cfg.tab1..4`（4 页签）→ `cfg.tab1/tab2`（**两页**，各 `_on`/`_off` 两态图 + `_tx` + `_hit`）
· `cfg.it_<key>`（整行底）→ `cfg.o_<key>_on/off`（值底）+ `_on_tx/_off_tx`（值文字）+ `_on_hit/_off_hit`（值热区）；行名保留可读名 `cfg.it_<key>_tx`
· `cfg.sl1..sl6_{lb,rail,knob,bar,hit}` → `cfg.sl_<音量名>`（**kind=slider**，轨道 / 手柄由机制绘制）+ `_hit`（拖动）+ `_end_lo/_end_hi`（刻度）
· `cfg.textspeed_*` / `cfg.autospeed_*` → `cfg.sl_textspeed` / `cfg.sl_autospeed`（带 `setting` 键名）
· `cfg.mute_lb/mute_off/mute_hit` → `cfg.snd_<行>_mute_lb` + `cfg.o_mute_<行>_on/off`（勾选图）+ `_on_hit/_off_hit`
· **有意保留的 5 个旧 id**：`cfg.dim`（**方案 §1.1 亲自命名**）与 `cfg.tab1_tx/hit`、`cfg.tab2_tx/hit`（与旧屏**同矩形、同动作、同语义**，且 W3 的巡演步骤已按 `cfg.tab2_hit` 写好 —— 见 `ui_screens.tjs:2154` 注释「步骤 id 依赖 W2 的 config 屏数据」）
· `cfg.charset`（角色集底板）/ `cfg.charrow`（角色行条）→ **未沿用**（改 `cfg.banner_frame` + **33 件 `cfg.pv_face_<族>` / 33 件 `cfg.pv_name_<族>`**，见 ⑤.3）；`cfg.char1..12`（12 热区）→ `cfg.ch_<族>_*`（33 项 × 5 件）
· `cfg.preview`（预览窗）→ `cfg.pv_frame` + `cfg.pv_bg` + `cfg.pv_mask`（★ id 冻结）+ `cfg.pv_text` + `cfg.pv_note(_x)`
· `cfg.window/full`、`cfg.on/off` 并入 `cfg.o_<key>_*`；**试听键（`cfg.replay*`）本屏不做**（方案 §1.3 未列，参考作声音页亦无）
· `cfg.sys_game/title/end` 三键语义沿用（id 改 `cfg.btn_game/title/end_*`）；`cfg.hit_reset`（空动作）→ `cfg.reset_hit`（**action=config_reset**）
· `cfg.it_<key>_tx`（旧屏把条目名**画在值矩形里**，几何不同）→ `cfg.row_<key>_lb`（本屏条目名在左沿 x=100 / 右列 x=1000）⇒ 换名

**⑧ W1（素材）数据侧修正 4 条逐条回执**
| # | W1 要求 | 本屏处置 |
| --- | --- | --- |
| 1 | 选中态文字改暗色（浅色胶囊上浅字仅 1.87:1） | **采纳**：新增 `cfg.tabN_tx_sel`（选中页签、暗字 `@palette.panel_fill`）与 `cfg.o_<key>_on_tx_sel`（当前值标签、暗字）；原 `cfg.tabN_tx` / `cfg.o_<key>_on_tx` 改为未选中 / 非当前值态的浅字件。**一处例外**：选中角色名 `cfg.ch_<fam>_tx_sel` 保持浅字 —— 实测 `name_sel` 是 (58,90,154,α150) **深蓝**胶囊，浅字 5.62:1 vs 暗字 2.62:1（见 ⑤.8） |
| 2 | 预览遮罩内缩 + z 低于预览框 | **采纳**：`cfg.pv_mask` → **(1126,743,592,134)**（四边各让 10px）、z=15（低于 `pv_frame` 16、高于 `pv_bg` 14）；因元素小于素材实尺寸，按 `_schema.md` §六 补**全零九宫格**（整体线性缩放，不破坏渐变的线性）。纵向梯度已实测同向（顶端 α=3 / 中线 128 / 底端 252）。★ **口径限定**（2026-09-24 机制模块 M5 建议、主代理转达）：「预览浓淡与对话框一致」应限定为**端点浓度与映射一致**（两端同由 `dlg_winopac` 经 `floor(255×v/100)` 驱动，90 档 = 229），**剖面长度按框缩放**（遮罩元素 592×134 由 612×154 素材整体线性缩放而来 ⇒ α 仍严格线性，但**单位长度的浓度上升率**与对话框满幅件不同）；跨件作差比对请**按框归一**，不要按像素行对齐 |
| 3 | 三处几何按参考作实测改正 | **采纳**：页标题 → `60,110,1200,80`；`画面设定` → `60,190,400,36`、`文本设定` → `1000,190,400,36`、`确认信息设定` → `60,775,400,36`（`音量设定` 225 / `语音设定` 825 原值即符合）；喇叭 → `x=行基准−48, y=行y−9, 22×32`（`MIN` 仍 244）；角色音量行以行基准 1111（PSB `#sliders/chvol`）按行结构偏移，行名 `(1099,498,300,32)` 不压轨道 —— **终值**：轨道 1174 / MIN 1111 / MAX 1557 / 静音 1642 / 勾选框 1710 / 喇叭 1063 / 行 hit (1111,540,620,21)，最大右沿 1731 < 1885 ✓ 互不重叠 ✓ |
| 4 | `rail` 只放在 `kind:"slider"` 里 | **已符合**：本屏没有独立的 rail `image` 元素；轨道 / 手柄只出现在 9 个 `kind:"slider"` 的 `rail` / `handle` 字段内 |""".replace(
    "@@TUI_N@@", str(len(TUI))).replace("@@TUI_LIST@@", "、".join(n[1] for n in TUI))

# ================================================================================
# 七、落盘
# ================================================================================
doc = {"id": "config", "title_cn": "配置", "owner": "M47", "note": NOTE,
       "flags_default": FLAGS, "elements": ELEMENTS}

# ---- 生成期自检：横幅头像 33 件必须在磁盘上（face/ 不入库，但本机应存在）----
try:
    from PIL import Image as _Im
    _face_dir = os.path.join(UI, "krkr", "assets", "face")
    _miss = [f for f in FACE_FILES.values() if not os.path.exists(os.path.join(_face_dir, f))]
    assert not _miss, "face/ 缺件：%s" % _miss
    _sizes = {_Im.open(os.path.join(_face_dir, f)).size for f in FACE_FILES.values()}
    print("横幅头像自检：33 件齐备，尺寸集合 %s" % sorted(_sizes))
except ImportError:
    print("横幅头像自检：PIL 不可用，跳过尺寸核对")

ids = [e["id"] for e in ELEMENTS]
dup = sorted({i for i in ids if ids.count(i) > 1})
assert not dup, "元素 id 重复：%s" % dup

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("写出 %s" % OUT)
for name, n in BLOCKS:
    print("  %-46s %3d 件" % (name, n))
print("合计 %d 件（visible_default=false 留位 %d 件）｜ flags_default %d 键｜ JSON %.1f KB"
      % (len(ELEMENTS), sum(1 for e in ELEMENTS if e.get("visible_default") is False),
         len(FLAGS), os.path.getsize(OUT) / 1024.0))
