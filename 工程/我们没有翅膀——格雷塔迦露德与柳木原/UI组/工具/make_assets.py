# -*- coding: utf-8 -*-
r"""
make_assets.py -- UI 组 M1 · krkr 资产集生成器（可复跑、幂等）
================================================================
Issue  : ISSUE-20260919-11（UI 美术组 · M1）
产出   : <UI组>\krkr\assets\ui\*.png      （krkr 可直接加载的 UI 贴图集）
         <UI组>\_工作\M1_证据\           （目视验收预览 + asset_manifest.tsv）

依据
----
* 00_UI组认知与接口契约.md §三（素材三类判读）/ §四（krkr 引擎事实）
* to-do-list.md §二 M1（验收标准）/ §三（红线）
* 资源组\美术\美术规范.md
    - §一.2 画布 1280×720、D1「全部素材不做放大」
    - §三   缩放算法（默认不缩放；必须缩小时用双线性；放大禁止）
    - §六.2 R2  转场遮罩「在 1280×720 下重绘/重采样为画布尺寸，属 UI 组新建素材，非缩放既有素材」
    - §六.2 R3  音乐条不缩放、引擎横向滚动
    - §六.3 H6  EyeCatch 卡片 1:1 不拉伸
* 资源组\美术\otv素材内容判读.tsv（遮罩逐件中文判读 = 选件依据）

三类产物
--------
A 类 · 原样 1:1 取用
    从**原图集** `资源组\美术统一\系统UI\` **逐字节拷贝**（shutil.copyfile，不缩放、不重编码），
    目标名 = layout 的 asset 串 `ui/<原名>.png` 的 **basename**，即 `krkr/assets/ui/<原名>.png`。
    （目录本身已提供 `ui/` 语义，故文件名**不再加 `ui_` 前缀**；主代理 2026-09-19 裁决。）
B 类 · UI 组自制（2 件关键产物）
    B-1 `panel_frame.png`  由 if_lt/if_rt/if_lb/if_rb(13×5 四角) + if_tbar/if_bbar(1×5 上下边)
                              + if_lbar/rbar(13×1 左右边) **拼合**成 27×11 九宫格边框源图
                              （左中右 13/1/13，上中下 5/1/5；中心 1×1 透明）。
                              对应 layout 的 `ui/panel_frame.png`，九宫格边距 l=13,t=5,r=13,b=5。
    B-2 转场遮罩（≥16 张代表件，本脚本取 18 张，覆盖 13 个风格族）
        `x_mask_<原名>_1x.png`   960×544 RGBA  ← 灰度 L 逐像素转 alpha（RGB 置白）
        `x_mask_<原名>_1280.png` 1280×720 RGBA ← 由 1x 版**双线性重采样**（1.333×）
C 类 · 明确不取（含日文/文字烘焙）——本脚本**不产出**，仅登记（见 C_REGISTRY），
        完整表见 `UI清单.md`「不可直接使用登记表」。

方向约定（每件打印「源 → 目标 / 变化方向」）
-------------------------------------------
    1:1 拷贝 ｜ 拼合 ｜ 格式转换(L→RGBA) ｜ 重采样(bilinear, 1.333×)
本脚本**不做任何「素材放大」**：
    * A 类逐字节，尺寸恒等；
    * B-1 拼合后尺寸 == 各件尺寸之和（27×11）；
    * B-2 的 960×544 → 1280×720 是**新建素材的重采样**，不是把既有素材放大后当原素材用
      —— 明文依据：美术规范 §6.2 **R2**（原文：「在 1280×720 下重绘/重采样为画布尺寸，
      属 UI 组新建素材，非缩放既有素材」）。同时保留 1:1 版，两套并存。

幂等性
------
    A 类 shutil.copyfile（字节恒等）；B 类 PIL PNG 编码器对同一输入确定性输出。
    连跑两次 md5 相同 —— 用 `--check` 自证（生成后与生成前磁盘内容逐件比对 md5）。
    目录内**非本脚本规划**的 PNG 默认被清理（`--no-prune` 关闭），
    以保证「目录内容 == 规划集」这一幂等前提。

用法
----
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    "E:/Tools/Python/python.exe" make_assets.py                # 生成（含清理游离件）
    "E:/Tools/Python/python.exe" make_assets.py --check        # 生成并与生成前比对 md5（幂等自证）
    "E:/Tools/Python/python.exe" make_assets.py --dry-run      # 只打印计划，不写盘
    "E:/Tools/Python/python.exe" make_assets.py                       # 默认含片尾卡 sr_01..24
    "E:/Tools/Python/python.exe" make_assets.py --no-prune     # 不清理游离件
    "E:/Tools/Python/python.exe" make_assets.py --src X --out Y --work Z   # 覆盖路径
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys

from PIL import Image

# ---------------------------------------------------------------- 路径默认值
HERE = os.path.dirname(os.path.abspath(__file__))            # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                             # <UI组>
PROJ = os.path.dirname(UI_GROUP)                             # <工程>\我们没有翅膀…
PROJ_NAME = os.path.basename(PROJ)


def main_worktree_root():
    """本组在独立 worktree（临时\\wt-ui）作业，而**素材本体目录已被 .gitignore**
    （美术统一\\系统UI、美术统一_超分\\系统UI 等），因此 worktree 内不存在，
    只在**主工作树** `E:\\ZCode Workspace\\Galgame\\` 下。上游素材一律从主工作树
    **只读**读取（任务书明文）。用 git 的 common-dir 反推主工作树根，避免硬编码。"""
    try:
        out = subprocess.check_output(["git", "rev-parse", "--git-common-dir"],
                                      cwd=HERE, text=True, stderr=subprocess.DEVNULL).strip()
        p = os.path.abspath(os.path.join(HERE, out))
        return os.path.dirname(p)          # ...\<主工作树>\.git -> ...\<主工作树>
    except Exception:
        return None


def pick_src_orig():
    cands = []
    env = os.environ.get("UI_SRC_ORIG")
    if env:
        cands.append(env)
    mw = main_worktree_root()
    if mw:
        cands.append(os.path.join(mw, "工程", PROJ_NAME, "资源组", "美术统一", "系统UI"))
    cands.append(os.path.join(PROJ, "资源组", "美术统一", "系统UI"))   # 万一素材已在 worktree 内
    for c in cands:
        if os.path.isdir(c):
            return c
    return cands[0] if cands else ""


DEF_SRC = pick_src_orig()
DEF_OUT = os.path.join(UI_GROUP, "krkr", "assets", "ui")
DEF_WORK = os.path.join(UI_GROUP, "_工作", "M1_证据")

BUDGET_BYTES = 16 * 1024 * 1024          # 主代理 2026-09-19 裁决：由 12 MB 放宽到 16 MB
                                         # （片尾角色卡 sr_01..24 为 片尾屏 必需，原 12 MB 预算装不下）

# ---------------------------------------------------------------- A 类清单
# 族名 -> [源 basename...]。全部从**原图集**逐字节拷贝（1:1，不缩放不重编码）。
# 取件口径：layout 实际引用（ui/meswin.png 等 8 条）+ 任务书 A 类清单「未来会用」的族。
A_CLASS = [
    # --- 对话窗 / 名字框 / 文本光标（10_dialog.json 直接引用）---
    ("dialog_window",     ["meswin"]),
    ("name_frame",        ["nm_frm_a", "nm_frm_b", "nm_frm_g"]),
    ("text_cursor",       ["ms_cursr"]),
    # --- 九宫格八件（B-1 拼合 panel_frame 的原料；散件同时保留备用）---
    ("ninepatch_src",     ["if_lt", "if_rt", "if_lb", "if_rb",
                           "if_tbar", "if_bbar", "if_lbar", "if_rbar"]),
    # --- 配置行框 / 滚动条滑块 ---
    ("config_frame",      ["cf_frame", "cf_frm_a"]),
    ("scrollbar",         ["cf_bar", "cf_vbar"]),
    # --- 系统菜单底板 / 选择支窗（10_dialog.json 引用 sm_base）---
    # ★ M45（2026-09-23，用户裁定）：`sysmenu`（系统菜单）屏**已整体废除**
    #   ⇒ 本族**不再被任何屏引用**，且**从未接入资产集**（`krkr/assets/ui/` 内无 `sm_*` 件；
    #     实测 `ls krkr/assets/ui/ | grep -i "sm_\|sysmenu"` 为空）。
    #   屏数据快照归档 `_工作\M45_旧素材归档\`。原注释「10_dialog.json 引用 sm_base」亦已失效
    #   （M38 无框化后对话框屏不再引用它）。
    # ("sysmenu_base",    ["sm_base", "sm_base2"]),   ← M45 已停用
    ("choice_window",     ["selwin"]),
    # --- PSV 空白对话窗三件（实测逐字节相同）---
    ("dlg_blank",         ["dlg_bg_26", "dlg_bg_27", "dlg_bg_28"]),
    # --- 标题背景（01_title.json 引用 tl1_bg1）---
    ("title_bg",          ["tl1_bg1", "tl1_bg2", "tl1_bg", "tl2_bg1"]),
    # --- 角色头像缩略图 / 场景缩略图 ---
    ("thumbnail",         ["th_asu", "th_ai", "th_bar", "ui_bg01", "gc_asu01", "ec_bg01"]),
    # --- 章标题卡：**仅 ec5_bg（800×600 红羽，无字）**。
    #     ec1/2/3/4/6_bg 与 ec5_1_bg/ec5_2_bg（均 1013×658）经目视实测含烘焙章名（日文+英文），
    #     依「含日文烘焙者不得进入资产集」剔除，登记进 C 类（见 C_REGISTRY）---
    # ★ M43（2026-09-23，用户裁定）：`chapter`（主线·章节选择）屏**已整体删除**
    #   ⇒ 本族**不再被任何屏引用**，且**从未接入资产集**（`krkr/assets/ui/` 内无 `ec5*` 件）。
    #   条目保留作溯源（当初的取件理由），但**不必再取**。
    # ("chapter_card",    ["ec5_bg"]),   ← M43 已停用
    # --- 小部件：ga_frame（相册框）+ sv_f1..5。
    #     注：skp1_icon 经目视实测为**烘焙文字雪碧图**（AUTO/SKIP/STOP/Quick Saved），
    #     已剔除并入 C 类；sv_f1..5 实测为**烘焙 Latin 键帽**（"F1".."F5"），
    #     尺寸 17×11、体积极小，保留但按「含烘焙文字」在 UI清单.md 标注。
    #     sm_base/sm_base2 右缘经 14× 放大目视有一列 ≤3px 微小深色标记（疑为装饰/微缩字），
    #     不构成可读文字，仍按空白件取用（报告 §五 观察项）。---
    ("widget",            ["ga_frame"] + ["sv_f%d" % i for i in range(1, 6)]),
    # --- 粒子（纸屑 / 雪）---
    ("particle",          ["paper_%d" % i for i in range(8)] +
                          ["snow_%d" % i for i in range(5)]),
    # --- 选择高亮条（宽 723 > 面板 376，原样取但布局不使用；取来只为完整性/溯源）---
    ("select_bar_unused", ["sel00a", "sel00b", "sel00g", "sel01b", "sel02b"]),
]

# 片尾角色卡：**默认包含**（主代理 2026-09-19 裁决：预算放宽到 16 MB）。
# 内容**无烘焙文字**（24 张片尾角色 CG，已目视确认）；体积 4.88 MB。
# 如需瘦身可用 `--without-ending-cards` 排除。
A_CLASS_OPTIONAL = [
    ("ending_card",       ["sr_%02d" % i for i in range(1, 25)]),
]

# ---------------------------------------------------------------- B-1 九宫格拼合
NINE_SRC = {
    "lt": "if_lt", "rt": "if_rt", "lb": "if_lb", "rb": "if_rb",
    "tbar": "if_tbar", "bbar": "if_bbar", "lbar": "if_lbar", "rbar": "if_rbar",
}
PANEL_OUT = "panel_frame.png"             # == layout 的 asset 串 "ui/panel_frame.png" 的 basename
PANEL_NINE = {"l": 13, "t": 5, "r": 13, "b": 5}

# ---------------------------------------------------------------- B-2 转场遮罩
# 选件依据：`资源组\美术\otv素材内容判读.tsv` 的 content_note（人工中文判读）。
# 覆盖 13 个风格族：水平条纹 / 垂直条纹 / 对角渐变 / 径向渐变 / 径向光晕 / 同心圆 /
#                   放射星芒 / 螺旋 / 棋盘 / 四象限擦除 / 扇形擦除 / 噪波 dissolve / 云状噪波 / Voronoi
# (源 basename, 风格标签, 判读原文)
MASKS = [
    ("rule000", "水平条纹(百叶窗,密度渐变)", "水平细条纹（百叶窗，条纹密度向左渐增）"),
    ("rule013", "水平条纹(等密极密)",        "水平细条纹（极密）"),
    ("rule008", "垂直条纹(密度渐变)",        "垂直细条纹（百叶窗）"),
    ("rule009", "垂直条纹(等密中等)",        "垂直条纹（中等）"),
    ("rule001", "对角渐变(亮->暗)",          "对角渐变（左上亮→右下暗）"),
    ("rule003", "对角渐变(暗带)",            "对角暗带（斜向渐变）"),
    ("rule004", "径向渐变(vignette)",        "径向暗角渐变（vignette）"),
    ("rule047", "径向光晕(中心亮)",          "径向光晕（中心亮）"),
    ("rule002", "同心圆(靶心)",              "同心圆环（靶心/涟漪，中心暗）"),
    ("rule026", "放射星芒",                  "放射状星芒（中心密集）"),
    ("rule097", "螺旋(涡旋)",                "螺旋（涡旋）"),
    ("rule067", "棋盘(3D网格)",              "方格棋盘（3D 网格渐变）"),
    ("rule061", "四象限擦除",                "四象限擦除（左上亮）"),
    ("rule065", "扇形擦除",                  "对角扇形擦除（自左上角放射）"),
    ("rule005", "噪波dissolve(粗颗粒)",      "噪波 dissolve（粗颗粒）"),
    ("rule006", "噪波dissolve(细颗粒)",      "噪波 dissolve（细颗粒）"),
    ("rule071", "云状噪波dissolve",          "云状噪波 dissolve"),
    ("rule076", "Voronoi晶格",               "晶格/多边形噪波（Voronoi）"),
]
MASK_1X = (960, 544)
MASK_1280 = (1280, 720)
MASK_RESAMPLE = Image.BILINEAR
MASK_RESAMPLE_NAME = "bilinear"

# ---------------------------------------------------------------- C 类登记表（不进入资产集）
# (族名, 件数, 尺寸, 烘焙内容举例, 处置建议)
# 依据：任务书 C 类清单 + 00_UI组认知与接口契约.md §3.2 + M1 逐族目视实测。
C_REGISTRY = [
    ("op_01…op_56", "39", "201–731×35–39",
     "整句日文选项文本图（如「これは“たとえば”の話だけど」）",
     "选项一律**引擎绘字**；选项框用 panel_frame.png 九宫格"),
    ("sm_save/load/cfg/skip/auto/win/log/ret/title/end/s_s_ret", "10", "612×26（sm_auto 1224×26）",
     "菜单条日文（セーブ / ロード / 環境設定 / スキップ / オート …）",
     "系统菜单条**引擎绘字**；条底用九宫格/纯色 rect"),
    ("tl_01…tl_06 / tl_01_altotp…", "10", "897×39 / 807×49",
     "标题菜单日文",
     "标题菜单**引擎绘字**（01_title.json 的 list 元素已如此实现）"),
    ("if_ok/ok2/yes/no/cancl", "5", "168–228×25",
     "确认按钮日文（はい / いいえ / キャンセル）",
     "确认框按钮**引擎绘字** + 九宫格边框"),
    ("th_close / cf_ret / sv_ret / ld_ret / ex_ret / ga_ret / gl_exit", "7", "92×17…417×28",
     "返回 / 关闭 / 退出 等动作文字",
     "**引擎绘字**"),
    ("sv_data / ld_data / sv_chk / ld_chk", "4", "1116×83 / 918×33",
     "存读档页签与勾选态文字",
     "存读档页签**引擎绘字**（M5）"),
    ("sv_pg01…10 / ld_pg01…10", "24", "152×25（20 件）/ 224×25（4 件）",
     "页码 / 页签文字",
     "页码**引擎绘字**"),
    ("sv_memo / ld_memo", "2", "132×17", "「メモ」等标签文字", "**引擎绘字**"),
    ("cf_disp1/2 / cf_bgm / cf_se / cf_dfrm / cf_bold / cf_anti / cf_skip1/2 / cf_sskp1/2 等", "37",
     "256×16 / 336×16 / 376×23 …",
     "配置项标签日文（画面表示 / BGM / 効果音 / スキップ …）",
     "配置项标签**引擎绘字**（M5 配置屏）；本族中 cf_frame/cf_frm_a/cf_bar/cf_vbar 为空白件，已作 A 类取用"),
    ("ec_0108…（日期条）", "44", "224×24", "日期条日文文字", "**引擎绘字**（M4 章节屏）"),
    ("ec1_name / ec1_chap / ec*_wing", "17", "126–227×17–24",
     "章名 / 章副题 / 「Wing of …」英文题",
     "**引擎绘字**（章名取自 spine.json，不得自造）"),
    ("ec1_bg / ec2_bg / ec3_bg / ec4_bg / ec6_bg", "5", "1013×658",
     "烘焙章名（「羽田 鷹志 編」「千歳 鷺介 編」「成田 隼人 編」「奈落の底」+ 英文 “Chapter : …” / “Abyss”）",
     "**M1 目视实测**：章名占卡面主区，不可作卡底；章标题卡须重制（取纹理区 + 引擎绘中文章名）"),
    ("ec5_1_bg / ec5_2_bg", "2", "1013×658",
     "烘焙章名「伊丹 伽楼羅 編」/ “Chapter : Karura Itami” / “Wing of Garuda”（ec5_2 另有彩色大字 +「12月3日（日）」）",
     "**M1 目视实测（本次新增）**：同为红羽章卡但含烘焙章名 → 不可用。"
     "⚠ 与 `00_UI组认知与接口契约.md` §3.1 的「`ec1_bg…ec6_bg` 1013×658」不符："
     "**`ec5_bg` 实测为 800×600 且无字**（已作 A 类取用），1013×658 的是 `ec5_1_bg`/`ec5_2_bg`"),
    ("sc_50_1…54_1", "5", "280×105", "卡面标题文字", "**引擎绘字**（画廊/场景卡）"),
    ("ex_10…ex_26", "23", "225×467 / 340×29 / 800×600", "整页界面文字", "不使用（R1 类整页图，须重制）"),
    ("title_bg", "1", "960×965", "PSV 标题整页文字", "不使用（R1：竖幅超画布，重制为 1280×720 版式）"),
    ("bg_config_01/02", "2", "960×833 / 960×761", "配置整页文字", "不使用（R1：重制配置屏版式）"),
    ("ss_bg1…5_full / ss_bg*_base", "10", "800×600 / 960×1012", "场景选择整页文字", "不使用（R1：重制场景选择版式）"),
    ("sl_data", "1", "426×511", "存读档整页文字", "不使用（重制）"),
    ("gm_bg1 / mu_bg / mv_bg / sys_menu", "4", "960×659…960×1626", "画廊/音乐/影片/系统菜单整页文字",
     "不使用（R1：重制为 1280×720 版式）"),
    ("gl_chr1…12", "12", "414×29–32", "角色名标签（角色名文字）", "**引擎绘字**（画廊角色筛选）"),
    ("gl_bgm01…gl_bgm12", "12", "1900×37",
     "曲目标题（英文，如 “Eternal Prelude”“Main Theme “HAWK””）",
     "**M1 目视实测确认含烘焙文字**（任务书 C 类已列「gl_bgm*(ota 1900×37 版)」）。"
     "音乐条须改为**引擎绘字 + 纯色/九宫格条底**；宽度 1900 > 画布 1280，亦不满足 R3 的滚动前提"),
    ("mc_bgm01…mc_bgm96（实存 58 件）", "58", "2036×37",
     "曲目标题（日文，如「放課後の小娘たち」「世界が平和でありますように」）",
     "**M1 目视实测确认含烘焙文字**。同上：引擎绘字 + 纯色条底"),
    ("ev_*", "9", "768×456 / 768×684 / 768×798", "事件画面整页文字", "不使用（R4 类：超画布/竖幅）"),
    ("quick-save", "1", "276×600", "「クイックセーブ」等文字", "**引擎绘字**"),
    ("sv_bg / ld_over", "2", "800×600", "存读档整页文字", "不使用（重制）"),
    ("dm00…dm11", "12", "320×120", "「ロード中…」加载提示文字（H5）",
     "**引擎绘字**；加载屏底可用纯色/九宫格（loading 屏属 M5）"),
    ("ui_ec_bg15a…", "8", "388×570", "竖幅场景卡面标题文字", "**引擎绘字**（M5 画廊/场景卡）"),
    ("skp1_icon", "1", "256×256",
     "烘焙文字雪碧图（AUTO / SKIP / STOP / Quick Saved + 播放控制图标）",
     "**M1 目视实测确认**：非「图标」而是状态文字图集 → 须重制为引擎绘字 + 独立图标"),
    ("noise", "1", "-", "噪波贴图（非文字）", "未纳入 A 类（本次无引用需求；如需由 M2 按需取）"),
]


# ================================================================ 工具
def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def out_name(src_base):
    """原样取用件的命名：layout 的 asset 串 `ui/<原名>.png` 的 basename → `<原名>.png`"""
    return "%s.png" % src_base


def human_dir(before, after):
    if before == after:
        return "1:1 拷贝"
    if after[0] < before[0] and after[1] < before[1]:
        return "缩小"
    if after[0] > before[0] or after[1] > before[1]:
        return "重采样(1.333x, 新建素材)"
    return "重排"


def gray_to_rgba(im_l):
    """灰度 -> 带 alpha 的 RGBA。
    映射：**alpha = 灰度值**（0=全透、255=全不透）；**RGB 恒为白 (255,255,255)**。
    理由：krkr 无 setMaskImage / 无图片遮罩 API（00_UI组认知与接口契约.md §四），
    转场遮罩只能以「白底 + alpha」参与普通 alpha 合成；把灰度信息全部放进 alpha 通道，
    既能被任何带 alpha 的合成路径直接消费，又避免与下层做乘法混色时产生色偏
    （若 RGB 沿用灰度值，会在半透明处叠加出灰雾）。
    美术规范 §二.2 结论 3 同向：「krkr 的 alpha 合成需要带 alpha 的位图，灰度 mask 需转成 alpha 通道」。"""
    a = im_l.convert("L")
    w, h = a.size
    white = Image.new("L", (w, h), 255)
    return Image.merge("RGBA", (white, white, white, a))


def nine_stretch(src, nine, w, h):
    """标准九宫格拉伸（与 krkr copy9Patch 同语义：四角 1:1、四边单向拉伸、中心双向拉伸）。
    krkr 的 copy9Patch 签名未实测（契约 §四），此处用 PIL 复刻同一算法产出预览。"""
    l, t, r, b = nine["l"], nine["t"], nine["r"], nine["b"]
    sw, sh = src.size
    mw, mh = sw - l - r, sh - t - b        # 中心源尺寸
    cw, ch = w - l - r, h - t - b          # 中心目标尺寸
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(src.crop((0, 0, l, t)), (0, 0))                       # 左上角 1:1
    out.paste(src.crop((sw - r, 0, sw, t)), (w - r, 0))             # 右上角 1:1
    out.paste(src.crop((0, sh - b, l, sh)), (0, h - b))             # 左下角 1:1
    out.paste(src.crop((sw - r, sh - b, sw, sh)), (w - r, h - b))   # 右下角 1:1
    out.paste(src.crop((l, 0, sw - r, t)).resize((cw, t), Image.BILINEAR), (l, 0))         # 上边
    out.paste(src.crop((l, sh - b, sw - r, sh)).resize((cw, b), Image.BILINEAR), (l, h - b))  # 下边
    out.paste(src.crop((0, t, l, sh - b)).resize((l, ch), Image.BILINEAR), (0, t))         # 左边
    out.paste(src.crop((sw - r, t, sw, sh - b)).resize((r, ch), Image.BILINEAR), (w - r, t))  # 右边
    out.paste(src.crop((l, t, sw - r, sh - b)).resize((cw, ch), Image.BILINEAR), (l, t))   # 中心
    return out


def compose_panel_frame(src_dir, work_dir):
    """B-1：把 if_* 八件拼成 27×11 的九宫格边框源图。
    左中右 = 13 / 1 / 13，上中下 = 5 / 1 / 5；中心 1×1 取**全透明**
    （面板填充由 layout 的 rect 元素承担，frame 层压在填充之上）。"""
    pieces = {}
    for k, name in NINE_SRC.items():
        p = os.path.join(src_dir, name + ".png")
        if not os.path.exists(p):
            raise IOError("九宫格拼合缺件: %s" % p)
        with Image.open(p) as im:
            pieces[k] = im.convert("RGBA")

    W = 13 + 1 + 13   # 27
    H = 5 + 1 + 5     # 11
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(pieces["lt"],   (0, 0))
    canvas.paste(pieces["tbar"], (13, 0))
    canvas.paste(pieces["rt"],   (14, 0))
    canvas.paste(pieces["lbar"], (0, 5))
    # (13,5) 中心 = 保持透明
    canvas.paste(pieces["rbar"], (14, 5))
    canvas.paste(pieces["lb"],   (0, 6))
    canvas.paste(pieces["bbar"], (13, 6))
    canvas.paste(pieces["rb"],   (14, 6))

    # 拼合自检：四角的外缘行/列必须与相邻边条逐像素一致，否则拉伸会有接缝
    checks = [
        ("左上角下缘 == if_lbar", pieces["lt"].crop((0, 4, 13, 5)).tobytes(), pieces["lbar"].tobytes()),
        ("左上角右缘 == if_tbar", pieces["lt"].crop((12, 0, 13, 5)).tobytes(), pieces["tbar"].tobytes()),
        ("右上角下缘 == if_rbar", pieces["rt"].crop((0, 4, 13, 5)).tobytes(), pieces["rbar"].tobytes()),
        ("右上角左缘 == if_tbar", pieces["rt"].crop((0, 0, 1, 5)).tobytes(), pieces["tbar"].tobytes()),
        ("左下角上缘 == if_lbar", pieces["lb"].crop((0, 0, 13, 1)).tobytes(), pieces["lbar"].tobytes()),
        ("左下角右缘 == if_bbar", pieces["lb"].crop((12, 0, 13, 5)).tobytes(), pieces["bbar"].tobytes()),
        ("右下角上缘 == if_rbar", pieces["rb"].crop((0, 0, 13, 1)).tobytes(), pieces["rbar"].tobytes()),
        ("右下角左缘 == if_bbar", pieces["rb"].crop((0, 0, 1, 5)).tobytes(), pieces["bbar"].tobytes()),
    ]
    seam_ok = True
    for label, a, b in checks:
        if a != b:
            seam_ok = False
            print("   [拼合自检] 不一致: %s" % label)
    print("   [拼合自检] 四角×四边接缝像素逐字节一致: %s" % ("通过" if seam_ok else "**不通过**"))

    # 生成目视验收预览（九宫格拉伸算法，纯 PIL，模拟 krkr copy9Patch / 三切片）
    previews = []
    for (pw, ph) in [(560, 44), (376, 262)]:
        pv = nine_stretch(canvas, PANEL_NINE, pw, ph)
        pv_path = os.path.join(work_dir, "panel_frame_preview_%dx%d.png" % (pw, ph))
        pv.save(pv_path)
        previews.append(pv_path)
        print("   [目视验收预览] %s" % pv_path)

        # ① 合成到底色上（frame 层压在 rect 填充之上，中心透明 -> 应透出填充色）
        bg = Image.new("RGBA", (pw, ph), (0x14, 0x18, 0x24, 200))
        comp = Image.alpha_composite(bg, pv)
        cpath = os.path.join(work_dir, "panel_frame_preview_%dx%d_onfill.png" % (pw, ph))
        comp.save(cpath)
        previews.append(cpath)
        print("   [目视验收·合成] %s" % cpath)

        # ② 四角 8× 最近邻放大（查像素级接缝/错位）
        for tag, box in [("lt", (0, 0, min(48, pw), min(24, ph))),
                         ("rb", (max(0, pw - 48), max(0, ph - 24), pw, ph))]:
            z = pv.crop(box).resize(((box[2] - box[0]) * 8, (box[3] - box[1]) * 8), Image.NEAREST)
            zb = Image.new("RGBA", z.size, (0x14, 0x18, 0x24, 200))
            zc = Image.alpha_composite(zb, z)
            zpath = os.path.join(work_dir, "panel_frame_zoom_%dx%d_%s.png" % (pw, ph, tag))
            zc.save(zpath)
            previews.append(zpath)
            print("   [目视验收·角部8x放大] %s" % zpath)
    return canvas, previews, seam_ok


def make_mask_sheet(out_dir, work_dir, cols=6, cell=(220, 125)):
    """把全部遮罩排成一张对照页（缩略图 + 品红底合成，便于目视判断 alpha 走向）。
    每格左 = 1x 版 / 右 = 1280 版；底色品红，alpha 越低越透出底色。"""
    cw, ch = cell
    rows = (len(MASKS) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw * 2 + 6) + 6, rows * (ch + 6) + 6), (24, 24, 32))
    bg = Image.new("RGBA", (cw, ch), (180, 40, 60, 255))
    for i, (base, style, note) in enumerate(MASKS):
        cx = i % cols
        cy = i // cols
        ox = 6 + cx * (cw * 2 + 6)
        oy = 6 + cy * (ch + 6)
        for j, tag in enumerate(("_1x", "_1280")):
            p = os.path.join(out_dir, "x_mask_%s%s.png" % (base, tag))
            if not os.path.exists(p):
                continue
            with Image.open(p) as im:
                small = im.convert("RGBA").resize(cell, Image.BILINEAR)
            comp = Image.alpha_composite(bg.copy(), small)
            sheet.paste(comp, (ox + j * (cw + 6), oy))
    sp = os.path.join(work_dir, "mask_sheet.png")
    sheet.save(sp)
    print("   [目视验收·遮罩对照页] %s" % sp)
    print("      每格左=1x / 右=1280；底色品红，alpha 越低越透出底色（越亮=越不透）")
    return sp


# ================================================================ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEF_SRC, help="原图集目录（美术统一\\系统UI）")
    ap.add_argument("--out", default=DEF_OUT, help="资产输出目录（krkr\\assets\\ui）")
    ap.add_argument("--work", default=DEF_WORK, help="证据/预览输出目录")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="生成后与生成前磁盘内容比对 md5（幂等自证）")
    ap.add_argument("--no-prune", action="store_true", help="不清理目录内非规划件")
    ap.add_argument("--without-ending-cards", action="store_true",
                    help="排除 sr_01..24（24 件 / 4.88 MB）以瘦身；默认包含")
    args = ap.parse_args()

    src_dir, out_dir, work_dir = args.src, args.out, args.work
    print("=" * 78)
    print("make_assets.py · UI 组 M1 资产集生成")
    print("  源（原图集，只读）: %s" % src_dir)
    print("  输出（资产集）    : %s" % out_dir)
    print("  证据/预览         : %s" % work_dir)
    print("  预算              : %.0f MB" % (BUDGET_BYTES / 1048576.0))
    print("=" * 78)
    if not os.path.isdir(src_dir):
        print("!! 源目录不存在: %s" % src_dir)
        return 2
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(work_dir, exist_ok=True)

    before_md5 = {}
    if args.check and os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            if f.lower().endswith(".png"):
                before_md5[f] = md5_of(os.path.join(out_dir, f))

    rows = []          # (类别, 源, 目标, 源尺寸, 目标尺寸, 方向, 字节, 源模式)
    planned = set()    # 规划内的目标文件名
    missing = []

    # ---------------- A 类 ----------------
    print("\n[A 类] 原样 1:1 取用（逐字节拷贝，不缩放不重编码）")
    print("-" * 78)
    print("%-42s %-32s %-13s %-22s %s" % ("源", "目标", "尺寸", "方向", "字节"))
    a_class = list(A_CLASS) + ([] if args.without_ending_cards else list(A_CLASS_OPTIONAL))
    for family, names in a_class:
        for n in names:
            sp = os.path.join(src_dir, n + ".png")
            if not os.path.exists(sp):
                missing.append(n)
                print("  !! 缺件 %s" % n)
                continue
            tgt = out_name(n)
            planned.add(tgt)
            tp = os.path.join(out_dir, tgt)
            with Image.open(sp) as im:
                ssize = im.size
                smode = im.mode
            if not args.dry_run:
                shutil.copyfile(sp, tp)
            sz = os.path.getsize(sp)
            rows.append((family, n + ".png", tgt, ssize, ssize, "1:1 拷贝", sz, smode))
            print("%-42s %-32s %-13s %-22s %8d" %
                  ("%s/%s.png" % (os.path.basename(src_dir), n), tgt,
                   "%dx%d" % ssize, "1:1 拷贝", sz))

    # ---------------- B-1 九宫格 ----------------
    print("\n[B 类 · 1] 九宫格边框拼合 -> %s" % PANEL_OUT)
    print("-" * 78)
    panel_path = os.path.join(out_dir, PANEL_OUT)
    planned.add(PANEL_OUT)
    if not args.dry_run:
        canvas, previews, seam_ok = compose_panel_frame(src_dir, work_dir)
        canvas.save(panel_path, optimize=True)
        rows.append(("ninepatch_built",
                     "if_lt+if_rt+if_lb+if_rb+if_tbar+if_bbar+if_lbar+if_rbar",
                     PANEL_OUT, (13, 5), canvas.size, "拼合", os.path.getsize(panel_path), "RGBA"))
        print("%-42s %-32s %-13s %-22s %8d" %
              ("if_* 八件(13x5 / 1x5 / 13x1)", PANEL_OUT,
               "%dx%d" % canvas.size, "拼合", os.path.getsize(panel_path)))
        print("   [九宫格边距] l=%d t=%d r=%d b=%d" %
              (PANEL_NINE["l"], PANEL_NINE["t"], PANEL_NINE["r"], PANEL_NINE["b"]))
        if not seam_ok:
            print("!! 拼合自检未通过：四角与边条接缝不一致，请检查拼合方式")
    else:
        print("  (dry-run) 跳过拼合")

    # ---------------- B-2 转场遮罩 ----------------
    print("\n[B 类 · 2] 转场遮罩（灰度 L -> alpha RGBA；960x544 1:1 + 1280x720 重采样）")
    print("-" * 78)
    print("  依据：美术规范 §6.2 R2「在 1280x720 下重绘/重采样为画布尺寸，属 UI 组新建素材，非缩放既有素材」")
    print("  算法：%s（1.333x）；映射：alpha = 灰度值，RGB 恒为白" % MASK_RESAMPLE_NAME)
    print("%-12s %-26s %-32s %-12s %s" % ("源", "风格判读", "目标", "尺寸", "方向"))
    for base, style, note in MASKS:
        sp = os.path.join(src_dir, base + ".png")
        if not os.path.exists(sp):
            missing.append(base)
            print("  !! 缺件 %s" % base)
            continue
        with Image.open(sp) as im:
            smode = im.mode
            g = im.convert("L")
        rgba1 = gray_to_rgba(g)
        t1 = "x_mask_%s_1x.png" % base
        t2 = "x_mask_%s_1280.png" % base
        planned.add(t1)
        planned.add(t2)
        big = rgba1.resize(MASK_1280, MASK_RESAMPLE)
        if not args.dry_run:
            rgba1.save(os.path.join(out_dir, t1), optimize=True)
            big.save(os.path.join(out_dir, t2), optimize=True)
        s1 = os.path.getsize(os.path.join(out_dir, t1)) if not args.dry_run else 0
        s2 = os.path.getsize(os.path.join(out_dir, t2)) if not args.dry_run else 0
        rows.append(("mask_1x", base + ".png", t1, g.size, rgba1.size, "格式转换(L->RGBA)", s1, smode))
        rows.append(("mask_1280", base + ".png", t2, g.size, big.size,
                     "重采样(%s,1.333x,新建素材)" % MASK_RESAMPLE_NAME, s2, smode))
        print("%-12s %-26s %-32s %-13s %s" % (base, style, t1, "%dx%d" % rgba1.size, "格式转换(L->RGBA)"))
        print("%-12s %-26s %-32s %-13s %s" % ("", "", t2, "%dx%d" % big.size, "重采样(bilinear)"))

    if not args.dry_run:
        make_mask_sheet(out_dir, work_dir)

    # ---------------- 清理游离件 ----------------
    if not args.dry_run and not args.no_prune and os.path.isdir(out_dir):
        stray = []
        for f in sorted(os.listdir(out_dir)):
            if f.lower().endswith(".png") and f not in planned:
                stray.append(f)
                os.remove(os.path.join(out_dir, f))
        print("\n[清理] 移除目录内非规划件 %d 件：%s" % (len(stray), ", ".join(stray) if stray else "无"))

    # ---------------- C 类登记（不进入资产集）----------------
    print("\n[C 类] 含日文/文字烘焙，**不进入资产集**（完整表见 UI清单.md「不可直接使用登记表」）")
    print("-" * 78)
    for fam, cnt, size, baked, fix in C_REGISTRY:
        print("  %-42s %3s 件  %-22s  %s" % (fam, cnt, size, baked))
        print("  %-42s      %-22s  处置：%s" % ("", "", fix))

    # ---------------- 清单（供 UI清单.md / verify_ui.py 用）----------------
    if not args.dry_run:
        mpath = os.path.join(work_dir, "asset_manifest.tsv")
        with open(mpath, "w", encoding="utf-8", newline="\n") as f:
            f.write("target\tsource\tfamily\tw\th\tsrc_mode\tdirection\tbytes\n")
            for fam, s, t, ssize, tsize, d, sz, mode in rows:
                f.write("%s\t%s\t%s\t%d\t%d\t%s\t%s\t%d\n" %
                        (t, s, fam, tsize[0], tsize[1], mode, d, sz))
        print("\n[清单] %s  （%d 行，供 UI清单.md 与 verify_ui.py 使用）" % (mpath, len(rows)))

    # ---------------- 汇总 ----------------
    print("\n" + "=" * 78)
    total = 0
    n_png = 0
    if os.path.isdir(out_dir):
        for f in sorted(os.listdir(out_dir)):
            if f.lower().endswith(".png"):
                total += os.path.getsize(os.path.join(out_dir, f))
                n_png += 1
    print("产出 PNG 件数: %d" % n_png)
    print("资产总体积  : %.2f MB (%d 字节)  预算 %.0f MB -> %s" %
          (total / 1048576.0, total, BUDGET_BYTES / 1048576.0,
           "OK" if total <= BUDGET_BYTES else "**超出，须报主代理裁决**"))
    if missing:
        print("缺件清单    : %s" % ", ".join(missing))
    else:
        print("缺件清单    : 无")

    # 幂等自证
    if args.check:
        print("\n[幂等自证] 与生成前磁盘内容比对 md5")
        changed = []
        after = {}
        for f in sorted(os.listdir(out_dir)):
            if f.lower().endswith(".png"):
                after[f] = md5_of(os.path.join(out_dir, f))
        if not before_md5:
            print("  生成前目录为空（首次生成），无法比对；请再跑一次 --check")
        else:
            for k in sorted(set(before_md5) | set(after)):
                if before_md5.get(k) != after.get(k):
                    changed.append(k)
            if changed:
                print("  **非幂等**：以下文件 md5 变化 %s" % changed)
            else:
                print("  通过：%d 件 md5 全部一致（连跑两次结果相同）" % len(after))

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())