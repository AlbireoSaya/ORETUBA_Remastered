# -*- coding: utf-8 -*-
r"""
verify_ui.py -- UI 组 M1 · 一致性校验器（M1 的核心价值）
================================================================
Issue  : ISSUE-20260919-11（UI 美术组 · M1）
职责   : 把「布局数据 / 资产集 / 两侧渲染器数据」三者的一致性做成**可执行、可回归**的检查，
         任何一项不通过即退出码非 0（供主代理二审与后续 M2–M5 回归使用）。

六项检查
--------
1. **引用完整性**：`layout/**/*.json` 里所有 `asset` 与 `item_frame.asset` / `state_assets.*`
   引用的文件必须存在于 `krkr/assets/ui/`。
   命名映射：layout 的 asset 串 `ui/<原名>.png` → 物理文件 `<原名>.png`（同目录内）
   （即把 `/` 换成 `_`；与 `00_UI组认知与接口契约.md` 的 `ui/` 命名空间 + M1 的
   `<原名>.png`（原版派生）/ `x_<语义>.png`（UI 组自制）命名约定一致）。
   若发现目录里存在「带前缀旧命名」（如 `ui_meswin.png`），额外提示命名口径分歧。

2. **尺寸一致性**：
   * `kind=image` 且**无** `nine` → `w/h` 必须**等于** PNG 实际尺寸（1:1，不缩放）；
   * `kind=image` 且**有** `nine` → `w/h` 必须 `≥ nine.l+nine.r` / `nine.t+nine.b`（允许拉伸）。
   * ★ **M06（2026-09-24）扩到 `item_buttons`（`list` 的逐块按钮）与 `slider` 子素材**：
     `item_buttons[i]` 取「会被绘制的那一张」（`state_assets.normal` → `asset`，与 [1]/[2] 的既有
     口径同款），**判据与 image 逐字一致**：无 `nine` ⇒ `w/h` 必须 = PNG 实尺寸；有 `nine` ⇒
     `w ≥ l+r`、`h ≥ t+b`。理由：逐块按钮的 1:1 件（重新播放 44×44）若 w/h 写错，两端都会
     静默拉伸涂抹，而此前**没有任何机器检查**（冻结书 §1b 末行的建议）。
   * ★ **M1（2026-09-24 · ISSUE-20260924-08）再扩到 `list.item_variants`（栏位内差分）**：
     `frames[i][j]`（每栏的差分缩略图）按 `thumb` 区（缺省 = 整项矩形）走同一条判据；
     `prev`/`next` 与 `item_buttons` 完全同一套判据。计数行现在打印
     「N 个 image（其中九宫格 M）＋K 个 item_buttons ＋V 个 item_variants 件 ＋J 条 slider rail」。

3. **三处数据一致**：`layout/ui_layout.json`、`krkr/game/ui_layout.tjs`、`复刻/ui_layout.js`
   同屏同元素的 x/y/w/h/字号/颜色必须相等。
   颜色归一化：`.tjs` 侧为**十进制整数**（生成器实际输出，如 16773320），`.js` 侧为
   `"#RRGGBB"`；本检查把 十进制 / `0xRRGGBB` / `#RRGGBB` **统一折算成 `#RRGGBB` 后比对**
   （即任务要求的「`0xRRGGBB` 与 `#RRGGBB` 互转比对」；当前生成器两侧分别为十进制与 `#` 形式，
   0x 形式一并兼容）。

4. **硬编码坐标扫描**：扫 `krkr/game/*.tjs`（**排除** `ui_layout.tjs` —— 它是自动生成的
   **数据文件**，数字即数据本体），找出「疑似坐标/尺寸/字号」的数字字面量。
   命中行 = 该行（去注释后）含下列关键字之一：
       left | top | width | height | setImageSize | setSizeToImageSize | drawText |
       font.size | colorRect | fillRect | setSize | setSizeToImageSize
   白名单（放行，规则如下，逐条可审）：
       W1  数值 ∈ {0,1,2,3}            —— 原点 / 序号 / 通道步进
       W2  数值 == 255                 —— alpha 满值
       W3  该行含 `interval` / `Timer` / `period` —— 计时参数，非布局
       W4  数值紧跟在 `[` 或 `,` 后且该行含 `[`/`]` 且无赋值 `=` —— 数组下标
       W5  十六进制字面量（`0x…`）      —— 位掩码 / 颜色常量，非十进制坐标
       W6  数值两侧被 `(`/`)`/`,` 包裹且该行同时含 `UILayout`/`uiTheme`/`uiAsset` —— 参数透传
    输出「可疑清单」；**清单为空才算通过**。
    约定：清单不空时，须由 **M2 逐条解释**（说明为何该数字不是硬编码布局值），
    解释写入 M2 交付；解释齐备前本项视为未通过。

5. **PNG 合法性**：`krkr/assets/ui/` 内每个 PNG 都能被 PIL 打开且 IHDR 合法
   （逐件 `Image.open` + `verify()` + 复读尺寸）。同时登记 **P 模式 / L 模式** 清单
   （krkr 支持性实测线索）。

6. **体积预算**：资产总体积 ≤ **96 MB**（＝ `DEF_BUDGET_MB`；2026-09-24 由 56 上调以容纳鉴赏 CG 缩略图；`--budget` 可调），超出即报错。
   （M12 2026-09-20：画布基线 1280×720 → 1920×1080，资产集按 ×1.5 重建后
   像素面积约 ×2.25，故预算由 16 MB 上调到 40 MB；依据见 §六 体积预算条目。）

7. **`opacity` 范围（0–255）**：`layout/**/*.json` 里任何名为 `opacity` 的数值字段越界即报错。
   （M39 2026-09-23 追加：krkr 侧 `uiWidgetNum()` **原样返回**、直接进 `operateStretch(…, omAlpha, opacity, …)`
   **不钳位**；HTML 侧 `opa()` 里 `if (n > 255) n = 255` **静默钳位** ⇒ 一条 `opacity: 300` 会让**两端画面不同
   而两边都不报错**。此检查即为堵这个静默分叉。）

退出码
------
    0  全部通过
    1  存在失败项
    2  环境/路径错误（找不到资产目录等）

用法
----
    export PYTHONPATH="E:/ZCode Workspace/Galgame/工具/pylibs"
    "E:/Tools/Python/python.exe" verify_ui.py
    "E:/Tools/Python/python.exe" verify_ui.py --budget 40 --verbose
"""

import argparse
import json
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))            # <UI组>\工具
UI_GROUP = os.path.dirname(HERE)                             # <UI组>

DEF_LAYOUT = os.path.join(UI_GROUP, "layout")
DEF_ASSETS = os.path.join(UI_GROUP, "krkr", "assets", "ui")
DEF_TJS = os.path.join(UI_GROUP, "krkr", "game", "ui_layout.tjs")
DEF_JS = os.path.join(UI_GROUP, "复刻", "ui_layout.js")
DEF_JSON = os.path.join(UI_GROUP, "layout", "ui_layout.json")
DEF_GAMEDIR = os.path.join(UI_GROUP, "krkr", "game")
DEF_ROOT = os.path.join(UI_GROUP, "layout", "_root.json")
DEF_BUDGET_MB = 96        # 56 → 96（2026-09-24 主代理裁决）：含鉴赏模式 CG 栏位缩略图 703 张（M2 产出，48.26 MB）
#                          备选方案（未采用）：CG 图改落独立命名空间 gal/ 以保持 ui/ 预算原意

                        # 理由：M30 接入流程图系统 AI 素材 57 件 / 4.49 MB（含 1920x1080 底图 2.5 MB
                        # 与九宫格面板框 1.1 MB），资产集由 162 件 / 43.15 MB 增至 219 件 / 47.64 MB，
                        # 已用到原 48 MB 预算的 99.3%。预算本为护栏而非硬上限，故按实际资产规模上调；
                        # 后续若继续增长，应先做 PNG 优化再议上限。
                        # 原 2026-09-20 裁决：40 -> 48 MB
                        # 依据：画布 1920x1080（×1.5）后资产像素 ×2.25；实测 138 件 / 45.04 MB。
                        # 其中 x_mask_* 36 件 14.5 MB + sr_* 24 件 10.7 MB + x_gen 派生 17 件 9.3 MB。
                        # 可选瘦身：把不透明大件（x_gen_fragpage/gallerypage/bg_system/sr_*）转 JPG 约可降至 8-10 MB，
                        # 但会改 asset 串后缀，本次不做，留待后续按需处理。
# 主代理 2026-09-19 裁决：12 -> 16 MB（片尾卡 sr_* 为必需）。
# M12 2026-09-20 裁决：16 -> 40 MB —— 画布基线 1280×720 -> 1920×1080，资产集按 ×1.5 重建，
#   像素面积约 ×2.25（1.5²），16 × 2.25 = 36 MB，取整留余量到 40 MB。
#   注意：check [2] 的「无 nine 的 image 的 w/h 必须等于 PNG 实尺寸」**逻辑不变**；
#   若 M11 交来的资产物理尺寸与新 w/h 不符，本项会失败 —— 那是真实不一致，不得改校验迁就。

# ---------------------------------------------------------------- 通用
def asset_to_filename(asset):
    """layout 的 asset 串 -> krkr/assets/ui/ 内的物理文件名（**兼容旧调用点保留**）。
    `ui/<原名>.png` -> `<原名>.png`（**目录已提供 `ui/` 语义，文件名不加前缀**；
    主代理 2026-09-19 裁决，取代此前的 `ui_<原名>.png` 扁平命名）。"""
    s = str(asset).strip().replace("\\", "/")
    return s.split("/")[-1]


def asset_to_relpath(asset):
    """layout 的 asset 串 -> **相对 `krkr/assets/` 的路径**（命名空间 = 串的首段）。

    ★ M47（2026-09-24）放开命名空间：此前 [1] 只认 `krkr/assets/ui/` 下的裸文件名
    （`asset_to_filename` 取末段），于是设置屏角色预览引用 `face/<族><基底>.png`
    会被判 **66 处缺件**；而引擎侧一直是按 `assets/<整串>` 解析的
    （`ui_asset.tjs` 的 `uiAssetCandidates` 命中候选②）⇒ 是**守门脚本自己**没跟上。
      · `ui/x.png`    -> `ui/x.png`      （`krkr/assets/ui/x.png`）
      · `face/a.png`  -> `face/a.png`    （`krkr/assets/face/a.png`，该目录不入库、由脚本再生）
      · `x.png`（无命名空间的历史写法）-> `ui/x.png`
    HTML 复刻端（`replica.js` 的 `assetUrl`）由 W4 同步放开，两端口径一致。"""
    s = str(asset).strip().replace("\\", "/")
    return s if "/" in s else ("ui/" + s)


STATE_ASSET_KEYS = ("normal", "hover", "pressed")   # 仅供报错提示用（说明期望的键名）

# ★ M47：**可再生产物命名空间**白名单 —— 这些目录不入库（见 .gitignore），
#   由工作区内的脚本再生（`krkr/assets/face/` ← `_工作\M44_头像裁切方案\复现脚本\m44_make_faces.py`）。
#   目录不存在时 [1] 只登记提示、不报缺件（干净检出的伪阴性）。
REPRODUCIBLE_NS = ("face",)


def iter_asset_refs(node, path=""):
    """递归收集 JSON 里所有素材引用。返回 [(引用串, 所在路径)]

    ★ M35 修（静默缺陷）：`state_assets` 的值是**字典**，旧实现让它走进 else 分支递归，
      而里层的键名是 normal/hover/pressed —— **都不在白名单里**，其字符串值被静默丢弃。
      实测后果（2026-09-22）：本工程 590 条引用**全部来自 `asset`**，
      `state_assets` 内 **120 条一条都没收** ⇒ **三态图缺件不会被 [1] 发现，
      六项全绿也可能缺图**（恰好覆盖 M35 新做的悬停/按下贴图）。

    ★ M35 一审 Minor-10：**遍历 `state_assets` 的全部字符串值，而不是固定三键**——
      固定白名单只是把「静默丢弃」的范围缩小了一点：日后若出现第四态（如 `focus`），
      仍会被悄悄丢掉。现在任何键的字符串值都收进来。
    ★ M35 一审 Minor-5：`state_assets` 的值**不是字典**时（例如误写成字符串），
      旧版会把它当引用收下、新版原先会完全忽略 —— 两种都是错的。
      现在按「格式异常」计入引用表（引用串 = 该值），由 [1] 的缺件检查报出来，
      从而把这类脏数据暴露而不是静默放行。
    自测见 工具/test_verify_asset_refs.py。
    """
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = "%s.%s" % (path, k) if path else k
            if k in ("asset", "item_frame") and isinstance(v, str):
                out.append((v, p))
            elif k == "state_assets":
                if isinstance(v, dict):
                    for sk in sorted(v.keys()):
                        sv = v.get(sk)
                        if isinstance(sv, str) and sv:
                            out.append((sv, "%s.%s" % (p, sk)))
                elif isinstance(v, str) and v:
                    out.append((v, p))      # 格式异常：当做引用查，缺件即报（见上）
            # ★ M1（2026-09-24 · ISSUE-20260924-08）：`list.item_variants.frames` 是
            #   **「栏位内差分」的逐栏素材表**（`[[asset,…], …]`，按全局项序号索引）。
            #   它的键名既不是 `asset` 也不是 `state_assets`，旧实现会一路递归到最内层的
            #   **裸字符串** —— 那里既不进 dict 也不进 list 分支 ⇒ **全部被静默丢弃**
            #   （与 M35 修 `state_assets` 时同一类缺陷：引用表漏收 = 缺件不被 [1] 发现）。
            elif k == "frames" and isinstance(v, list):
                for i, row in enumerate(v):
                    if isinstance(row, list):
                        for j, s in enumerate(row):
                            if isinstance(s, str) and s:
                                out.append((s, "%s[%d][%d]" % (p, i, j)))
                    elif isinstance(row, str) and row:
                        out.append((row, "%s[%d]" % (p, i)))
            elif k == "asset" and v is None:
                pass
            else:
                out.extend(iter_asset_refs(v, p))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(iter_asset_refs(v, "%s[%d]" % (path, i)))
    return out



# ---------------------------------------------------------------- TJS 字典解析
def _skip_ws(s, i):
    n = len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            i = n if j < 0 else j + 1
        elif c == "/" and i + 1 < n and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            break
    return i


def _parse_string(s, i):
    assert s[i] == '"'
    i += 1
    buf = []
    esc = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
    while i < len(s):
        c = s[i]
        if c == "\\":
            buf.append(esc.get(s[i + 1], s[i + 1]))
            i += 2
        elif c == '"':
            return "".join(buf), i + 1
        else:
            buf.append(c)
            i += 1
    raise ValueError("字符串未闭合")


def _parse_value(s, i):
    i = _skip_ws(s, i)
    if s.startswith("%[", i):
        return _parse_dict(s, i)
    if s[i] == "[":
        return _parse_array(s, i)
    if s[i] == '"':
        return _parse_string(s, i)
    for lit, val in (("true", True), ("false", False), ("null", None), ("void", None)):
        if s.startswith(lit, i) and not re.match(r"[\w]", s[i + len(lit):i + len(lit) + 1] or " "):
            return val, i + len(lit)
    m = re.match(r"-?\d+(\.\d+)?", s[i:])
    if m:
        tok = m.group(0)
        return (float(tok) if "." in tok else int(tok)), i + m.end()
    raise ValueError("无法解析的值 @%d: %r" % (i, s[i:i + 40]))


def _parse_dict(s, i):
    r"""解析 TJS2 内联字典 `%[ … ]`。

    ★ `ISSUE-20260928-03` 修正（**修的是本解析器的完备性，不是放宽判据**）：
    TJS2 的字典元素有**两条**产生式（`tjs2/syntax/tjs.y` 的 `dic_elm`）：
      ① `T_SYMBOL ":" expr` —— **裸标识符键 + 冒号**（`gen_layout.py` 对合法标识符键走这条）；
      ② `expr_no_comma "," expr` —— **逗号式键值对**（`gen_layout.py` 对**非标识符键**走这条，
         例：屏级 `flags_default` 的带点键 `"fc.state.0001", "locked"`）。
    ⇒ 本解析器**两条都必须认**：原实现只认 ①，遇到 `--preset states` 产出的带点键就抛
      「缺少 ':'」⇒ `verify_ui [3]` 误报「解析失败」（**该缺陷先于本次改动存在**：带点键自
      `ISSUE-20260928-02` 第 2 步起就在 `flags_default` 里，只是此前从未在「states 在盘上」的
      状态下跑过 `verify_ui`）。**判据未变**：解析出的字典照样与 `ui_layout.json`/`ui_layout.js`
      逐键比对；语法真错（既无 `:` 又无 `,`）仍然抛错。
    """
    assert s.startswith("%[", i)
    i += 2
    d = {}
    while True:
        i = _skip_ws(s, i)
        if s[i] == "]":
            return d, i + 1
        if s[i] == '"':
            key, i = _parse_string(s, i)
        else:
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", s[i:])
            if not m:
                raise ValueError("无法解析键 @%d: %r" % (i, s[i:i + 40]))
            key = m.group(0)
            i += m.end()
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ":":
            i += 1                                  # 产生式 ①：`key: value`
        elif i < len(s) and s[i] == ",":
            i += 1                                  # 产生式 ②：`key, value`（逗号式）
        else:
            raise ValueError("字典元素既无 ':' 也无 ',' @%d: %r" % (i, s[i:i + 40]))
        val, i = _parse_value(s, i)
        d[key] = val
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ",":
            i += 1


def _parse_array(s, i):
    assert s[i] == "["
    i += 1
    a = []
    while True:
        i = _skip_ws(s, i)
        if s[i] == "]":
            return a, i + 1
        v, i = _parse_value(s, i)
        a.append(v)
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ",":
            i += 1


def load_tjs_layout(path):
    """从 `var UILayoutData = %[ … ];` 解析出 TJS 字典"""
    text = open(path, encoding="utf-8").read()
    m = re.search(r"%\[", text)
    if not m:
        raise ValueError("未找到 `%[` 起始（%s）" % path)
    val, _ = _parse_value(text, m.start())
    return val


def load_js_layout(path):
    """从 `window.UI_LAYOUT = { … };` 解析出对象"""
    text = open(path, encoding="utf-8").read()
    i = text.find("{")
    if i < 0:
        raise ValueError("未找到 '{' 起始（%s）" % path)
    obj, _ = json.JSONDecoder().raw_decode(text[i:])
    return obj


# ---------------------------------------------------------------- 颜色归一化
COLOR_KEY = re.compile(r"(^|_)colou?r$", re.I)


def is_color_key(k):
    return bool(COLOR_KEY.search(k))


def to_hex_color(v):
    """十进制 / 0xRRGGBB / '#RRGGBB' -> '#RRGGBB'；无法判定返回 None"""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return "#%06X" % (v & 0xFFFFFF)
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("#"):
            h = s[1:].upper()
            return "#" + h[-6:].rjust(6, "0")
        if s.lower().startswith("0x"):
            try:
                return "#%06X" % (int(s, 16) & 0xFFFFFF)
            except ValueError:
                return None
    return None


def same_value(a, b):
    """值等价判定：完全相等，或「十进制/0x 整数 ↔ '#RRGGBB' 字符串」互转后相等。
    这条正是任务书要求的「`.tjs` 的 `0xRRGGBB` 与 `.js` 的 `#RRGGBB` 互转比对」的落点：
    `.tjs` 侧生成器输出**十进制整数**（如 16773320），`.js` 侧输出 `"#RRGGBB"`，
    两侧语义相同、写法不同，必须先折算再比。"""
    if a == b:
        return True
    if isinstance(a, bool) or isinstance(b, bool):
        return False
    ha, hb = None, None
    if isinstance(a, int) and isinstance(b, str) and (b.startswith("#") or b.lower().startswith("0x")):
        ha, hb = to_hex_color(a), to_hex_color(b)
    elif isinstance(b, int) and isinstance(a, str) and (a.startswith("#") or a.lower().startswith("0x")):
        ha, hb = to_hex_color(a), to_hex_color(b)
    if ha is not None and hb is not None:
        return ha == hb
    return False


def flatten(node, path="", out=None, in_color=False):
    """把嵌套结构压平成 {路径: 值}，颜色键的值统一折算成 #RRGGBB"""
    if out is None:
        out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            p = "%s.%s" % (path, k) if path else k
            flatten(v, p, out, in_color=is_color_key(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            flatten(v, "%s[%d]" % (path, i), out, in_color=in_color)
    else:
        if in_color and not isinstance(node, bool):
            h = to_hex_color(node)
            if h is not None:
                out[path] = h
                return out
        out[path] = node
    return out


# ---------------------------------------------------------------- 检查 1
def check_asset_refs(layout_dir, assets_dir, verbose):
    errors, warns, refs = [], [], []
    for root, _dirs, files in os.walk(layout_dir):
        for f in sorted(files):
            if not f.lower().endswith(".json"):
                continue
            p = os.path.join(root, f)
            try:
                data = json.load(open(p, encoding="utf-8"))
            except Exception as e:
                errors.append("布局 JSON 解析失败 %s：%s" % (p, e))
                continue
            rel = os.path.relpath(p, layout_dir)
            for ref, where in iter_asset_refs(data):
                refs.append((rel, where, ref))

    have = set(os.listdir(assets_dir)) if os.path.isdir(assets_dir) else set()
    assets_root = os.path.dirname(assets_dir)          # krkr/assets（命名空间的父目录）
    n_skip_repro = 0
    for rel, where, ref in refs:
        fn = asset_to_filename(ref)
        if os.path.exists(os.path.join(assets_root, asset_to_relpath(ref))):
            if verbose:
                print("      OK  %-28s -> %s" % (ref, asset_to_relpath(ref)))
            continue
        if fn in have:
            if verbose:
                print("      OK  %-28s -> %s" % (ref, fn))
            continue
        # ★ M47：**可再生产物命名空间**（`face/` 被 .gitignore、由 _工作\M44_头像裁切方案
        #   的脚本再生）⇒ 目录整体不存在时不报缺件，只登记一行提示 ——
        #   否则干净检出（新 clone / 未跑再生脚本）必然 [1] 失败，属伪阴性。
        #   只对**白名单里的命名空间**放行：打错的命名空间（如 `faace/x.png`）仍照常报缺件。
        _ns = asset_to_relpath(ref).split("/")[0] if "/" in asset_to_relpath(ref) else "ui"
        if _ns in REPRODUCIBLE_NS and not os.path.isdir(os.path.join(assets_root, _ns)):
            n_skip_repro += 1
            if verbose:
                print("      --  %-28s -> 可再生产物命名空间 `%s/` 缺失（跳过；由再生脚本产出）"
                      % (ref, _ns))
            continue
        prefixed = "ui_" + os.path.basename(ref)
        if prefixed in have:
            errors.append("缺件：%s（%s · %s）—— 目录内存在 **带前缀旧命名** %s，"
                          "命名口径应为无前缀 `%s`（主代理 2026-09-19 裁决）"
                          % (ref, rel, where, prefixed, fn))
        else:
            errors.append("缺件：%s（%s · %s）—— 期望文件 %s 不存在于 %s"
                          % (ref, rel, where, fn, os.path.basename(assets_dir)))
    print("  [1] 引用完整性      ：%d 条引用 / %d 条唯一（其中可再生产物命名空间缺失跳过 %d 条）→ %s"
          % (len(refs), len(set(r for _a, _b, r in refs)), n_skip_repro,
             "通过" if not errors else "**%d 处失败**" % len(errors)))
    for e in errors:
        print("      !! %s" % e)
    for w in warns:
        print("      ~  %s" % w)
    return errors


# ---------------------------------------------------------------- 检查 2
def check_image_sizes(layout_json, assets_dir, verbose):
    errors = []
    data = json.load(open(layout_json, encoding="utf-8"))
    screens = data.get("screens", {})
    n_img = n_nine = n_slider_rail = 0
    n_itembtn = 0        # ★ M06：list 的逐块按钮（item_buttons）参与本项计数
    for sid, scr in screens.items():
        elems = list(scr.get("elements", []))
        if isinstance(scr.get("bg"), dict):
            elems.insert(0, dict(scr["bg"], id=sid + ".bg"))
        for el in elems:
            if el.get("kind") != "image":
                continue
            # ★ M35b 一审（Minor）：参照物取**实际会被绘制**的那张 —— 有 state_assets 时
            #   引擎只在三键全空才回落 `asset`（见 ui_widget.tjs 的 uiWidgetStateAsset /
            #   replica.js 的 pickState），拿 `asset` 比尺寸会漏检、也会对合法数据误判。
            a = (el.get("state_assets") or {}).get("normal") or el.get("asset")
            if not a:
                continue
            fn = asset_to_filename(a)
            fp = os.path.join(assets_dir, fn)
            if not os.path.exists(fp):
                continue          # 已由检查 1 报出
            n_img += 1
            with Image.open(fp) as im:
                aw, ah = im.size
            w, h = el.get("w"), el.get("h")
            nine = el.get("nine")
            eid = el.get("id", "?")
            if nine:
                n_nine += 1
                need_w = nine.get("l", 0) + nine.get("r", 0)
                need_h = nine.get("t", 0) + nine.get("b", 0)
                if w is None or h is None or w < need_w or h < need_h:
                    errors.append("%s（%s）：九宫格 %s 要求 w>=%d h>=%d，实为 w=%s h=%s"
                                  % (eid, a, nine, need_w, need_h, w, h))
                elif verbose:
                    print("      OK  nine %-22s %s  %dx%d（源 %dx%d）"
                          % (eid, a, w, h, aw, ah))
            else:
                if (w, h) != (aw, ah):
                    errors.append("%s（%s）：kind=image 无 nine，w/h 必须等于 PNG 实际尺寸 "
                                  "%dx%d，实为 %sx%s" % (eid, a, aw, ah, w, h))
                elif verbose:
                    print("      OK  1:1  %-22s %s  %dx%d" % (eid, a, aw, ah))
    # ★ M06（2026-09-24 · ISSUE-20260924-06）：`list` 的**逐块按钮** `item_buttons[]` 也纳入本项。
    #   判据与上面 image 分支**逐字一致**：取「会被绘制的那一张」（`state_assets.normal` → `asset`，
    #   与 [1] 的引用表口径同款）；无 nine ⇒ `w/h` 必须等于 PNG 实尺寸；有 nine ⇒ `w ≥ l+r`、`h ≥ t+b`。
    #   为什么必须有：逐块按钮里有 1:1 件（重新播放 44×44）与九宫格件（跳转 94×29，源 52×29），
    #   写错尺寸两端都会**静默**拉伸涂抹（krkr 走 operateStretch、HTML 走 border-image/background），
    #   而此前没有任何机器检查（冻结书 §1b 的建议）。
    for _sid3, _scr3 in screens.items():
        for el in _scr3.get("elements", []):
            if el.get("kind") != "list":
                continue
            btns = el.get("item_buttons")
            if not isinstance(btns, list):
                continue
            for _bi, b in enumerate(btns):
                if not isinstance(b, dict):
                    continue
                bkey = b.get("key") or ("#" + str(_bi))
                bpath = (b.get("state_assets") or {}).get("normal") or b.get("asset")
                if not bpath:
                    continue                    # 缺件/结构非法由 test_click_reach 与引擎守卫分别报出
                bfp = os.path.join(assets_dir, asset_to_filename(bpath))
                if not os.path.exists(bfp):
                    continue                    # 已由检查 1 报出
                n_itembtn += 1
                with Image.open(bfp) as im:
                    bw, bh = im.size
                w, h = b.get("w"), b.get("h")
                bn = b.get("nine")
                if bn:
                    need_w = bn.get("l", 0) + bn.get("r", 0)
                    need_h = bn.get("t", 0) + bn.get("b", 0)
                    if w is None or h is None or w < need_w or h < need_h:
                        errors.append("%s.item_buttons[%s]（%s）：九宫格 %s 要求 w>=%d h>=%d，实为 w=%s h=%s"
                                      % (el.get("id", "?"), bkey, bpath, bn, need_w, need_h, w, h))
                    elif verbose:
                        print("      OK  btn-nine %-18s %s[%s]  %dx%d（源 %dx%d）"
                              % (el.get("id", "?"), bkey, bpath, w, h, bw, bh))
                else:
                    if (w, h) != (bw, bh):
                        errors.append("%s.item_buttons[%s]（%s）：无 nine ⇒ w/h 必须等于 PNG 实际尺寸 "
                                      "%dx%d（1:1，否则静默拉伸），实为 %sx%s"
                                      % (el.get("id", "?"), bkey, bpath, bw, bh, w, h))
                    elif verbose:
                        print("      OK  btn-1:1  %-18s %s[%s]  %dx%d"
                              % (el.get("id", "?"), bkey, bpath, bw, bh))
    # ★ M1（2026-09-24 · ISSUE-20260924-08_鉴赏模式）：`list` 的**栏位内差分**
    #   `item_variants` 也纳入本项（判据与既有 image **逐字一致**）：
    #     · `frames[i][j]`（每栏的差分图）：画进 `thumb` 区（缺省 = 整项矩形）⇒
    #       无 `thumb.nine` ⇒ PNG 实尺寸必须 **等于 thumb 区 w/h**；有 nine ⇒ thumb w/h ≥ l+r / t+b；
    #     · `prev` / `next`（左右差分按钮）：与 `item_buttons` **完全同一套判据**。
    #   为什么必须有：差分图是**程序化生成**的缩略图（M2 的 `m50_make_gallery_thumbs.py`），
    #   尺寸写错会被两端**静默拉伸涂抹**，而此前没有任何机器检查（冻结书 §7 的建议）。
    n_variant = 0
    for _sid4, _scr4 in screens.items():
        for el in _scr4.get("elements", []):
            if el.get("kind") != "list":
                continue
            vv = el.get("item_variants")
            if not isinstance(vv, dict):
                continue
            eid = el.get("id", "?")
            # thumb 区（块内局部矩形；缺省 = 整个项矩形）
            thumb = vv.get("thumb") if isinstance(vv.get("thumb"), dict) else None
            if thumb is None:
                iw = el.get("item_w") if el.get("orientation") == "h" else el.get("w")
                thumb = {"x": 0, "y": 0, "w": iw, "h": el.get("item_h")}
            tw, th = thumb.get("w"), thumb.get("h")
            tn = thumb.get("nine")
            frames = vv.get("frames")
            if isinstance(frames, list):
                for _ri, row in enumerate(frames):
                    if not isinstance(row, list):
                        continue                    # 结构非法由引擎守卫报出
                    for _ci, apath in enumerate(row):
                        if not isinstance(apath, str) or not apath:
                            continue
                        afp = os.path.join(assets_dir, asset_to_filename(apath))
                        if not os.path.exists(afp):
                            continue                # 已由检查 1 报出
                        n_variant += 1
                        with Image.open(afp) as im:
                            aw, ah = im.size
                        if tn:
                            need_w = tn.get("l", 0) + tn.get("r", 0)
                            need_h = tn.get("t", 0) + tn.get("b", 0)
                            if tw is None or th is None or tw < need_w or th < need_h:
                                errors.append("%s.item_variants.frames[%d][%d]（%s）：thumb 九宫格 %s "
                                              "要求 w>=%d h>=%d，实为 w=%s h=%s"
                                              % (eid, _ri, _ci, apath, tn, need_w, need_h, tw, th))
                        else:
                            if (tw, th) != (aw, ah):
                                errors.append("%s.item_variants.frames[%d][%d]（%s）：无 nine ⇒ PNG 实际"
                                              "尺寸必须等于 thumb 区 %sx%s（1:1，否则静默拉伸），实为 %dx%d"
                                              % (eid, _ri, _ci, apath, tw, th, aw, ah))
            for _wk in ("prev", "next"):
                wb = vv.get(_wk)
                if not isinstance(wb, dict):
                    continue                    # 缺/非法由引擎守卫报出
                wpath = (wb.get("state_assets") or {}).get("normal") or wb.get("asset")
                if not wpath:
                    continue
                wfp = os.path.join(assets_dir, asset_to_filename(wpath))
                if not os.path.exists(wfp):
                    continue
                n_variant += 1
                with Image.open(wfp) as im:
                    ww, wh = im.size
                ww_e, wh_e = wb.get("w"), wb.get("h")
                wn = wb.get("nine")
                if wn:
                    need_w = wn.get("l", 0) + wn.get("r", 0)
                    need_h = wn.get("t", 0) + wn.get("b", 0)
                    if ww_e is None or wh_e is None or ww_e < need_w or wh_e < need_h:
                        errors.append("%s.item_variants.%s（%s）：九宫格 %s 要求 w>=%d h>=%d，实为 w=%s h=%s"
                                      % (eid, _wk, wpath, wn, need_w, need_h, ww_e, wh_e))
                else:
                    if (ww_e, wh_e) != (ww, wh):
                        errors.append("%s.item_variants.%s（%s）：无 nine ⇒ w/h 必须等于 PNG 实际尺寸 "
                                      "%dx%d（1:1），实为 %sx%s" % (eid, _wk, wpath, ww, wh, ww_e, wh_e))
    # ★ M47（一审机制模块 M4.4）：`kind=="slider"` 的 rail/handle 单独走一遍 ——
    #   旧实现只遍历 `kind=="image"`，而引擎侧轨道**无 nine 时按 1:1 宽直接 blit**
    #   ⇒ 改宽即静默横向拉伸、两端都不报。这里要求：子素材存在；rail 无 nine 时元素 w 必须等于 PNG 实宽。
    for _sid2, _scr2 in screens.items():
        for el in _scr2.get("elements", []):
            if el.get("kind") != "slider":
                continue
            eid = el.get("id", "?")
            rail_p = (el.get("rail") or {}).get("asset")
            hnd_p = (el.get("handle") or {}).get("asset")
            if not rail_p or not hnd_p:
                errors.append("%s：slider 缺 rail.asset 或 handle.asset" % eid)
                continue
            rail_fp = os.path.join(assets_dir, asset_to_filename(rail_p))
            if not os.path.exists(rail_fp):
                errors.append("%s：slider 的 rail 素材不存在：%s" % (eid, rail_p))
                continue
            with Image.open(rail_fp) as im:
                rw, rh = im.size
            if not (el.get("rail") or {}).get("nine"):
                if el.get("w") != rw:
                    errors.append("%s：slider 的 rail 无 nine ⇒ 元素 w 必须等于 rail PNG 实宽 %d"
                                  "（否则静默横向拉伸），实为 w=%s" % (eid, rw, el.get("w")))
                else:
                    n_slider_rail += 1
            if not os.path.exists(os.path.join(assets_dir, asset_to_filename(hnd_p))):
                errors.append("%s：slider 的 handle 素材不存在：%s" % (eid, hnd_p))
            if verbose:
                print("      OK  slider %-16s rail=%s %dx%d（元素 w=%s）"
                      % (eid, rail_p, rw, rh, el.get("w")))
    print("  [2] 尺寸一致性      ：%d 个 image（其中九宫格 %d）＋%d 个 item_buttons ＋%d 个 "
          "item_variants 件 ＋%d 条 slider rail → %s"
          % (n_img, n_nine, n_itembtn, n_variant, n_slider_rail,
             "通过" if not errors else "**%d 处失败**" % len(errors)))
    for e in errors:
        print("      !! %s" % e)
    return errors


# ---------------------------------------------------------------- 检查 3
def check_three_way(json_path, tjs_path, js_path, verbose, max_report=40):
    errors = []

    def fail(msg):
        print("  [3] 三处数据一致    ：→ **解析失败**")
        print("      !! %s" % msg)
        return [msg]

    try:
        a = flatten(json.load(open(json_path, encoding="utf-8")))
    except Exception as e:
        return fail("ui_layout.json 解析失败：%s" % e)
    try:
        b = flatten(load_tjs_layout(tjs_path))
    except Exception as e:
        return fail("ui_layout.tjs 解析失败：%s" % e)
    try:
        c = flatten(load_js_layout(js_path))
    except Exception as e:
        return fail("ui_layout.js 解析失败：%s" % e)

    def diff(x, y, xn, yn):
        out = []
        for k in sorted(set(x) | set(y)):
            if k not in x:
                out.append("%s 独有键：%s" % (yn, k))
            elif k not in y:
                out.append("%s 独有键：%s" % (xn, k))
            elif not same_value(x[k], y[k]):
                out.append("%s vs %s 在 %s：%r ≠ %r" % (xn, yn, k, x[k], y[k]))
        return out

    d1 = diff(a, b, "json", "tjs")
    d2 = diff(a, c, "json", "js")
    for d in (d1, d2):
        errors.extend(d[:max_report])
    print("  [3] 三处数据一致    ：json %d 键 / tjs %d 键 / js %d 键 → %s"
          % (len(a), len(b), len(c), "通过" if not errors else "**%d 处不一致**" % len(errors)))
    for e in errors[:max_report]:
        print("      !! %s" % e)
    if verbose and not errors:
        ncol = sum(1 for k in a if is_color_key(k.split(".")[-1]))
        print("      颜色键 %d 个已统一折算为 #RRGGBB 后比对（tjs 十进制 / js #RRGGBB）" % ncol)
    return errors


# ---------------------------------------------------------------- 检查 4
SCAN_KEYWORDS = re.compile(
    r"\b(left|top|width|height|setImageSize|setSizeToImageSize|drawText|font\.size|"
    r"colorRect|fillRect|setSize)\b")
NUM_LIT = re.compile(r"(?<![\w.])(\d+)(?![\w.])")
HEX_LIT = re.compile(r"0x[0-9A-Fa-f]+")
WHITELIST_VALUES = {0, 1, 2, 3, 255}
TIMING_HINT = re.compile(r"interval|Timer|period", re.I)
PARAM_HINT = re.compile(r"UILayout|uiTheme|uiAsset|uiLayout")


def check_hardcoded(game_dir, verbose):
    findings = []
    scanned = 0
    for f in sorted(os.listdir(game_dir)):
        if not f.endswith(".tjs") or f == "ui_layout.tjs":
            continue
        scanned += 1
        fp = os.path.join(game_dir, f)
        for ln, raw in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
            code = raw.split("//")[0]
            if not SCAN_KEYWORDS.search(code):
                continue
            if TIMING_HINT.search(code):          # W3
                continue
            code_nohex = HEX_LIT.sub(" ", code)   # W5：先抹掉十六进制字面量
            hits = []
            for m in NUM_LIT.finditer(code_nohex):
                v = int(m.group(1))
                if v in WHITELIST_VALUES:         # W1 / W2
                    continue
                tail = code_nohex[m.end():m.end() + 1]
                if tail == "]":                   # W4：疑似数组下标
                    continue
                if PARAM_HINT.search(code_nohex):  # W6：参数透传
                    continue
                # W7：位运算常量（位掩码 / alpha 移位），非坐标
                prev = code_nohex[:m.start()].rstrip()[-1:]
                nxt = code_nohex[m.end():].lstrip()[:1]
                if prev in "<>&|^" or nxt in "<>&|^":
                    continue
                hits.append(m.group(1))
            if hits:
                findings.append((f, ln, hits, code.strip()))
    print("  [4] 硬编码坐标扫描  ：扫 %d 个 .tjs（排除自动生成的 ui_layout.tjs）→ %s"
          % (scanned, "可疑清单为空，通过" if not findings else "**%d 行可疑**" % len(findings)))
    print("      白名单：W1 值∈{0,1,2,3} ｜ W2 值==255 ｜ W3 行含 interval/Timer/period ｜ "
          "W4 疑似数组下标 ｜ W5 十六进制字面量 ｜ W6 行含 UILayout/uiTheme/uiAsset")
    for f, ln, hits, code in findings:
        print("      ?? %s:%d  数字=%s  | %s" % (f, ln, ",".join(hits), code[:100]))
    if findings:
        print("      约定：本清单须由 **M2 逐条解释**（说明为何不是硬编码布局值）；解释齐备前本项不通过。")
    return findings


# ---------------------------------------------------------------- 检查 5
def check_pngs(assets_dir, verbose):
    errors, p_mode, l_mode = [], [], []
    files = sorted(f for f in os.listdir(assets_dir) if f.lower().endswith(".png"))
    for f in files:
        fp = os.path.join(assets_dir, f)
        try:
            with open(fp, "rb") as fh:
                sig = fh.read(8)
                if sig != b"\x89PNG\r\n\x1a\n":
                    errors.append("%s：PNG 签名非法" % f)
                    continue
                head = fh.read(12)               # 4B 长度 + 4B 类型 + 4B 宽度
            if head[4:8] != b"IHDR":
                errors.append("%s：首个块不是 IHDR" % f)
                continue
            with Image.open(fp) as im:
                w, h = im.size
                im.verify()                      # 校验 CRC / 结构
            with Image.open(fp) as im2:
                mode = im2.mode
                w2, h2 = im2.size
            if (w, h) != (w2, h2):
                errors.append("%s：两次读取尺寸不一致 %s vs %s" % (f, (w, h), (w2, h2)))
            if mode == "P":
                p_mode.append(f)
            if mode == "L":
                l_mode.append(f)
            if verbose:
                print("      OK  %-38s %-5s %dx%d" % (f, mode, w, h))
        except Exception as e:
            errors.append("%s：PIL 打开/校验失败：%s" % (f, e))
    print("  [5] PNG 合法性      ：%d 件 → %s" % (len(files), "通过" if not errors else "**%d 件失败**" % len(errors)))
    for e in errors:
        print("      !! %s" % e)
    print("      P 模式（索引色）清单：%s" % (", ".join(p_mode) if p_mode else "无"))
    print("      L 模式（灰度）清单  ：%s" % (", ".join(l_mode) if l_mode else "无"))
    return errors


# ---------------------------------------------------------------- 检查 6
def check_budget(assets_dir, budget_mb):
    files = sorted(f for f in os.listdir(assets_dir) if f.lower().endswith(".png"))
    total = sum(os.path.getsize(os.path.join(assets_dir, f)) for f in files)
    ok = total <= budget_mb * 1024 * 1024
    print("  [6] 体积预算        ：%d 件 / %.2f MB（%.0f MB 预算）→ %s"
          % (len(files), total / 1048576.0, budget_mb, "通过" if ok else "**超出**"))
    errs = []
    if not ok:
        errs.append("资产总体积 %.2f MB 超出 %.0f MB 预算（%d 字节）"
                    % (total / 1048576.0, budget_mb, total))
        print("      !! %s" % errs[0])
    return errs, total, len(files)


# ---------------------------------------------------------------- main
def check_opacity_range(layout_dir, verbose):
    """[7] opacity 范围（0–255）：krkr 不钳位、HTML 静默钳位 ⇒ 越界会让两端静默分叉（M39 追加）。"""
    errors = []
    checked = 0
    for root, _dirs, files in os.walk(layout_dir):
        for fn in sorted(files):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, layout_dir).replace("\\", "/")
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                errors.append("%s: JSON 解析失败（%s）" % (rel, e))
                continue
            stack = [(rel, data)]
            while stack:
                path, node = stack.pop()
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k == "opacity" and isinstance(v, (int, float)) and not isinstance(v, bool):
                            checked += 1
                            if v < 0 or v > 255:
                                errors.append(
                                    "%s: opacity=%s 越界（允许 0–255）——"
                                    "krkr 不钳位、HTML 静默钳到 255 ⇒ 两端会静默分叉" % (path, v))
                        stack.append(("%s.%s" % (path, k), v))
                elif isinstance(node, list):
                    for i, v in enumerate(node):
                        stack.append(("%s[%d]" % (path, i), v))
    if verbose:
        print("      opacity 字段检查数：%d 个" % checked)
    return errors, checked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default=DEF_LAYOUT)
    ap.add_argument("--assets", default=DEF_ASSETS)
    ap.add_argument("--gamedir", default=DEF_GAMEDIR)
    ap.add_argument("--json", default=DEF_JSON)
    ap.add_argument("--tjs", default=DEF_TJS)
    ap.add_argument("--js", default=DEF_JS)
    ap.add_argument("--budget", type=float, default=DEF_BUDGET_MB, help="体积预算（MB，默认取 DEF_BUDGET_MB）")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    print("=" * 78)
    print("verify_ui.py · UI 组 M1 一致性校验")
    print("  layout : %s" % args.layout)
    print("  assets : %s" % args.assets)
    print("  game   : %s" % args.gamedir)
    # 画布基线一律**从 layout/_root.json 读**，不写死 1280/720（M12 2026-09-20）
    root_path = os.path.join(args.layout, "_root.json")
    canvas_txt = "未知（未找到 _root.json）"
    if os.path.isfile(root_path):
        try:
            _root = json.load(open(root_path, encoding="utf-8"))
            _cv = _root.get("canvas", {})
            canvas_txt = "%sx%s（canvas_baseline=%s）" % (
                _cv.get("width"), _cv.get("height"), _root.get("canvas_baseline"))
        except Exception as e:
            canvas_txt = "解析失败：%s" % e
    print("  canvas : %s  ← 读自 layout/_root.json" % canvas_txt)
    print("=" * 78)
    for p, name in ((args.layout, "layout 目录"), (args.assets, "资产目录"), (args.gamedir, "game 目录")):
        if not os.path.isdir(p):
            print("!! %s 不存在：%s" % (name, p))
            return 2
    for p, name in ((args.json, "ui_layout.json"), (args.tjs, "ui_layout.tjs"), (args.js, "ui_layout.js")):
        if not os.path.isfile(p):
            print("!! %s 不存在：%s" % (name, p))
            return 2

    e1 = check_asset_refs(args.layout, args.assets, args.verbose)
    e2 = check_image_sizes(args.json, args.assets, args.verbose)
    e3 = check_three_way(args.json, args.tjs, args.js, args.verbose)
    f4 = check_hardcoded(args.gamedir, args.verbose)
    e5 = check_pngs(args.assets, args.verbose)
    e6, total, npng = check_budget(args.assets, args.budget)
    e7, nopa = check_opacity_range(args.layout, args.verbose)
    print("[7] opacity 范围      ：检查 %d 个 opacity 字段 → %s"
          % (nopa, "通过" if not e7 else "失败 %d 处" % len(e7)))
    for m in e7:
        print("      !! %s" % m)

    all_errors = e1 + e2 + e3 + e5 + e6 + e7
    print("-" * 78)
    print("汇总：引用 %d ｜ 尺寸 %d ｜ 三处一致 %d ｜ 硬编码可疑 %d 行 ｜ PNG %d ｜ 预算 %d 处 ｜ opacity %d 处"
          % (len(e1), len(e2), len(e3), len(f4), len(e5), len(e6), len(e7)))
    print("资产：%d 件 / %.2f MB" % (npng, total / 1048576.0))
    if all_errors or f4:
        print("结果：**不通过**（退出码 1）")
        print("=" * 78)
        return 1
    print("结果：**全部通过**（退出码 0）")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())