# -*- coding: utf-8 -*-
r"""W4 · 设置屏「两页 + 遮罩浓淡三档」无头截图与量化（HTML 复刻端）

■ 目的（用户要求的核心是观感 + 滑块要真的改遮罩浓度）
  ① 两页**整屏 1:1 截图**：`?screen=config`（系统页）与 `&flags=cfg_page:snd`（声音页）
     —— 用于目视「巨型外框 / 文字锚定 / 页签互斥 / 滑块手柄位置」；
  ② 预览遮罩浓淡三档（`dlg_winopac` = 90 / 50 / 0）**逐像素作差**，差异框必须落在
     `cfg.pv_mask` 的矩形内 ⇒ 「滑块值 → 遮罩浓度」这条链真的通到了画面上；
  ③ 对话框屏同档两图（90 / 0）作差，差异框落在 `dlg.mask_bottom` 矩形内
     ⇒ 「实时生效穿透到对话框」（⑲c 的像素级补证）；
  ④ 两页**互斥量化**：从 DOM 里统计 `vis_flag=cfg_page` 的两批元素的可见数（应严格互斥），
     并**如实列出**带值 flag（`cfg_v_*` / `cfg_vchar`）的元素在「非本页」仍可见的件数
     —— 那是 `vis_flag` 只能带一对导致的已知跨页残留（25_config.json 的 note ⑥），
     本脚本把它**量化登记**，不做断言判定。

■ 为什么自建临时页（而不是直接用 复刻\index.html）
  `dlg_winopac` 没有 URL 入口（设置仓不是 flag，`?flags=` 管不到），而 W4 的白名单只含
  `复刻\replica.js` / `editor_ui.js` / `_selftest_states.html`（**不得改 index.html**）。
  故本脚本把 index.html 读进来、改写三条相对路径 + 注入一段「读 `?set=<键>:<值>` 写设置仓」
  的钩子与一段「隐藏页面外壳」的 CSS，落到本证据目录（跑完删除），再截图。
  页面文件里**没有**任何游戏逻辑改动 —— 渲染完全走 `复刻\replica.js` 本体。

■ 用法
    python _工作\ISSUE-20260924-01_W4_证据\复现脚本\w4_html_config_shots.py
        → 全量：两页 + 遮罩三档 + 横幅头像两档 + 差异量化 + 跨页残留表

    ★ 主代理指定入口（1:1 画布截图，无自研裁切）：
    python _工作\ISSUE-20260924-01_W4_证据\复现脚本\w4_html_config_shots.py \
        --shot "?screen=config" <out.png> [--set dlg_winopac:50] [--click cfg.tab2_hit] [--dump <out.html>]
        · 截图口径 = 隐藏页面外壳 + `setScale(1)` ⇒ **左上 1920×1080 即画布本体**；
        · `--set <键>:<值>` 写设置仓（设置仓没有 URL 入口）；`--click <元素id>` 渲染后真点一下；
        · 查询串里已有 `?` 时自动用 `&` 追加，故 `?screen=config&flags=cfg_page:snd` 也能直接传。
"""
import io
import json
import os
import re
import subprocess
import sys
import urllib.parse

from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)                     # …\ISSUE-20260924-01_W4_证据
UI = os.path.dirname(os.path.dirname(EVID))      # …\UI组
REP = os.path.join(UI, "复刻")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = r"E:\ZCode Workspace\Galgame\临时\edge_w4"
PAGE = os.path.join(EVID, "_w4_temp_page.html")   # 临时页（跑完删）

CANVAS_W, CANVAS_H = 1920, 1080

HOOK = """
<script>
/* W4 证据专用钩子（**不进任何交付文件**）：
   ① 页面外壳全部隐藏 + 强制 1:1 ⇒ 截图左上角 1920×1080 就是画布本体；
   ② 读 `?set=<键>:<值>` 写设置仓（设置仓没有 URL 入口，见脚本头注）；
   ③ 读 `?click=<元素 id>` 在渲染后**真的点一下**该元素 —— 用于走「页签点击」这条真实路径：
      `?flags=cfg_page:snd` 只改 flag、**不跑切页值 flag 派生**（派生在动作 config_tab_2 里），
      故深链截图会把系统页的值元素留在画面上（本脚本把两种路径**分别截**并分别登记）。 */
(function () {
  var st = document.createElement('style');
  st.textContent = '.shell{max-width:none!important;padding:0!important;margin:0!important}'
    + '.shell-head,.shell-foot{display:none!important}'
    + '#stage-wrap{justify-content:flex-start!important;display:block!important}'
    + '#stage{box-shadow:none!important}';
  document.head.appendChild(st);
  window.addEventListener('load', function () {
    if (!window.UI_REPLICA) return;
    var m = /[?&]set=([A-Za-z0-9_]+):([A-Za-z0-9_]+)/.exec(location.search || '');
    if (m) {
      UI_REPLICA.settingSet(m[1], isNaN(Number(m[2])) ? m[2] : Number(m[2]));
      UI_REPLICA.sliderSyncAllDom();
      /* ★ 关键**时序**修正（主代理 2026-09-24 第四轮指出，W4 实测复现）：
         `?set` 写在 boot（`initFlagsFor` + `configFlagsInitFor` 派生）**之后** ⇒ 对**值键**
         （display / facewindow / mute_* 等）只改仓、不改 flag ⇒ 截图仍是旧值
         （实测：`--set display:full` 后备注仍显示「窗口模式」胶囊）。
         故写仓之后**必须再跑一次派生**（并在其后同步显隐），这样 `--set <值键>` 才等价于
         「进屏时仓里就是这个值」。注意 `?set` 与派生的先后**不能反**（先写仓、后被派生里的
         「播种」按 flag 值覆盖），所以顺序固定为：写仓 → 派生 → 同步显隐。 */
      UI_REPLICA.configFlagsInitFor(UI_REPLICA.state.screen);
      UI_REPLICA.applyFlagVisibility();
      UI_REPLICA.applySettingOverrides();
    }
    UI_REPLICA.setScale(1);
    var c = /[?&]click=([A-Za-z0-9_.\\-]+)/.exec(location.search || '');
    if (c) {
      var n = document.querySelector('[data-ui-id="' + c[1] + '"]');
      if (n) n.click();
      UI_REPLICA.sliderSyncAllDom();
      UI_REPLICA.applyFlagVisibility();
    }
  });
})();
</script>
"""


def build_page():
    """把 复刻\\index.html 改写成证据目录里的临时页（只改相对路径 + 注入钩子）。"""
    html = io.open(os.path.join(REP, "index.html"), encoding="utf-8").read()
    html = html.replace('href="replica.css"', 'href="../../复刻/replica.css"')
    html = html.replace('src="ui_layout.js"', 'src="../../复刻/ui_layout.js"')
    html = html.replace('src="flow_data.js"', 'src="../../复刻/flow_data.js"')
    html = html.replace('src="replica.js"', 'src="../../复刻/replica.js"')
    html = html.replace('<script src="../../复刻/ui_layout.js"></script>',
                        "<script>window.UI_ASSET_ROOT='../../krkr/assets/';</script>\n"
                        '<script src="../../复刻/ui_layout.js"></script>')
    html = html.replace('</body>', HOOK + '\n</body>')
    io.open(PAGE, "w", encoding="utf-8").write(html)


def url(query):
    return "file:///" + urllib.parse.quote(PAGE.replace("\\", "/")) + query


def shot(query, out_png=None, dump=None):
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--window-size=1944,1180  # ★ 视口 = (W−24)×(H−93) ⇒ 1920×1087，覆盖 1920×1080 画布（原用 1920,1080 会静默裁掉最右 24/最下 93px）", "--virtual-time-budget=9000"]
    if out_png:
        cmd.append("--screenshot=" + out_png)
    if dump:
        cmd.append("--dump-dom")
    cmd.append(url(query))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dump:
        dom = r.stdout.decode("utf-8", "replace")
        io.open(dump, "w", encoding="utf-8").write(dom)
        return dom
    return ""


def main():
    # ---- ★ 主代理 2026-09-24 要求 ⑤：`--shot <查询串> <out.png>` 直接产 1:1 画布截图 ----
    #      口径 =「隐藏页面外壳 + setScale(1)」⇒ 截图的**左上 1920×1080 就是画布本体**，
    #      不需要任何自研裁切（原 M47 对照脚本的扫描式裁切不准，已由截图方改用本入口）。
    #      `--set <键>:<值>` 写设置仓；`--click <元素id>` 渲染后点一下；`--dump <out.html>` 存 DOM。
    if "--shot" in sys.argv:
        a = sys.argv
        q = a[a.index("--shot") + 1]
        png = a[a.index("--shot") + 2]
        setk = a[a.index("--set") + 1] if "--set" in a else ""
        click = a[a.index("--click") + 1] if "--click" in a else ""
        dump = a[a.index("--dump") + 1] if "--dump" in a else ""
        extra = ""
        if setk:
            extra += "&set=" + setk
        if click:
            extra += "&click=" + click
        qq = (q + extra) if ("?" in q) else (q + "?" + extra.lstrip("&"))
        if qq.endswith("?") or qq.endswith("&"):
            qq = q
        os.makedirs(UD, exist_ok=True)
        build_page()
        # ⚠️ 路径一律转**绝对**：Edge 的 `--screenshot=` 对相对路径（尤其含中文的）不可靠
        #   （实测相对路径不落盘）。相对路径按**当前工作目录**解析。
        png = os.path.abspath(png)
        dump = os.path.abspath(dump) if dump else ""
        if os.path.dirname(png):
            os.makedirs(os.path.dirname(png), exist_ok=True)
        ok = shot(qq, out_png=png, dump=(dump or None))
        os.remove(PAGE)
        print("shot %s -> %s（1:1 画布，左上 1920×1080）" % (qq, png))
        print("文件存在=" + str(os.path.exists(png)))
        return 0 if os.path.exists(png) else 1

    os.makedirs(EVID, exist_ok=True)
    os.makedirs(UD, exist_ok=True)
    build_page()
    out = []

    shots = [
        ("?screen=config&set=dlg_winopac:90", "W4_系统页_遮罩90.png", "W4_系统页.dom.html"),
        ("?screen=config&set=dlg_winopac:50", "W4_系统页_遮罩50.png", None),
        ("?screen=config&set=dlg_winopac:0",  "W4_系统页_遮罩0.png",  None),
        # 声音页走**真实路径**：渲染后再点页签 cfg.tab2_hit（跑 config_tab_2 的值 flag 派生）
        ("?screen=config&set=dlg_winopac:90&click=cfg.tab2_hit",
         "W4_声音页_遮罩90.png", "W4_声音页.dom.html"),
        # 深链 `?flags=cfg_page:snd`（**只改 flag、不派生**）—— 对照用，量化「深链 vs 点击」的差
        ("?screen=config&flags=cfg_page:snd", None, "W4_声音页_深链.dom.html"),
        # ★ 主代理指定的「角色横幅头像」验收两档（默认 asu / 指定 kob）——见报告
        ("?screen=config&flags=cfg_page:snd", "W4_横幅头像_asu.png", None),
        ("?screen=config&flags=cfg_page:snd,cfg_vchar:kob", "W4_横幅头像_kob.png",
         "W4_横幅头像_kob.dom.html"),
        # ★ M47 第三轮（一审 C3）：在**系统页**程序化派发角色动作（巡演 / 探针 / 深链路径）
        #   ⇒ 选中值必须只进记忆、不上屏（残留应为 0）
        ("?screen=config&click=cfg.ch_kaa_hit", "W4_系统页_派发角色kaa.png",
         "W4_系统页_派发角色.dom.html"),
        ("?screen=dialog&set=dlg_winopac:90", "W4_对话框_遮罩90.png", None),
        ("?screen=dialog&set=dlg_winopac:0",  "W4_对话框_遮罩0.png",  None),
    ]
    for q, png, dump in shots:
        dom = shot(q, out_png=(os.path.join(EVID, png) if png else None),
                   dump=(os.path.join(EVID, dump) if dump else None))
        out.append("shot %-56s -> %s" % (q, png or "（仅取 DOM）"))

    # ---- ② 预览遮罩三档作差 ----
    base = Image.open(os.path.join(EVID, "W4_系统页_遮罩90.png")).convert("RGB")
    p50 = Image.open(os.path.join(EVID, "W4_系统页_遮罩50.png")).convert("RGB")
    p0 = Image.open(os.path.join(EVID, "W4_系统页_遮罩0.png")).convert("RGB")
    bb50 = ImageChops.difference(base, p50).getbbox()
    bb0 = ImageChops.difference(base, p0).getbbox()
    out.append("系统页 90 vs 50 差异框 = %s" % (bb50,))
    out.append("系统页 90 vs  0 差异框 = %s" % (bb0,))
    mask_box = (1126, 743, 1126 + 592, 743 + 134)     # cfg.pv_mask（读数据，非猜）
    knob_band = (280, 660, 990, 720)                  # 不透明度滑块手柄的行程带（值 0..100）

    def diff_count(a, b, box=None):
        """逐像素作差（阈值 6），可限定矩形；返回差异像素数。"""
        pa, pb = a.load(), b.load()
        x0, y0, x1, y1 = box if box else (0, 0, a.width, a.height)
        n = 0
        for y in range(y0, y1):
            for x in range(x0, x1):
                if sum(abs(pa[x, y][i] - pb[x, y][i]) for i in range(3)) > 6:
                    n += 1
        return n

    def outside(a, b, boxes):
        """boxes 之外的差异像素数（含若干白名单矩形）。"""
        pa, pb = a.load(), b.load()
        n = 0
        for y in range(0, a.height):
            for x in range(0, a.width):
                if any(bx0 <= x < bx1 and by0 <= y < by1 for bx0, by0, bx1, by1 in boxes):
                    continue
                if sum(abs(pa[x, y][i] - pb[x, y][i]) for i in range(3)) > 6:
                    n += 1
        return n

    in_mask_50 = diff_count(base, p50, mask_box)
    in_mask_0 = diff_count(base, p0, mask_box)
    out_50 = outside(base, p50, [mask_box, knob_band])
    out_0 = outside(base, p0, [mask_box, knob_band])
    out.append("  ⇒ cfg.pv_mask 矩形内差异像素：90↔50 = %d、90↔0 = %d（应 >0，且随档位差递增）"
               % (in_mask_50, in_mask_0))
    out.append("  ⇒ 白名单（遮罩矩形 ∪ 滑块手柄行程带）**之外**的差异像素：90↔50 = %d、90↔0 = %d"
               "（应 0 —— 证明除「手柄位置 + 遮罩浓淡」外画面未变）" % (out_50, out_0))
    out.append("  ⇒ 手柄行程带内差异：90↔50 = %d、90↔0 = %d（应 >0 —— 滑块手柄随值移动）"
               % (diff_count(base, p50, knob_band), diff_count(base, p0, knob_band)))

    # ---- ③ 对话框穿透 ----
    d90 = Image.open(os.path.join(EVID, "W4_对话框_遮罩90.png")).convert("RGB")
    d0 = Image.open(os.path.join(EVID, "W4_对话框_遮罩0.png")).convert("RGB")
    bbd = ImageChops.difference(d90, d0).getbbox()
    out.append("对话框 90 vs 0 差异框 = %s" % (bbd,))
    if bbd:
        out.append("  ⇒ 差异框高度 = %d px（遮罩带 350 ⇒ 90↔0 应约为整条 350 的可见部分）"
                   % (bbd[3] - bbd[1]))

    # ---- ④ 两页互斥 / 值 flag 残留（量化登记）----
    #    元素元数据取自**数据源** `layout/screens/25_config.json`（与页面渲染同一上游），
    #    不在 ui_layout.js 的文本里做正则（那是生成物，格式随生成器变）。
    cfg_json = json.loads(io.open(os.path.join(UI, "layout", "screens", "25_config.json"),
                                  encoding="utf-8").read())
    cfg_els = cfg_json["elements"]
    sys_dom = io.open(os.path.join(EVID, "W4_系统页.dom.html"), encoding="utf-8").read()
    snd_dom = io.open(os.path.join(EVID, "W4_声音页.dom.html"), encoding="utf-8").read()
    deep_dom = io.open(os.path.join(EVID, "W4_声音页_深链.dom.html"), encoding="utf-8").read()
    kaa_dom = io.open(os.path.join(EVID, "W4_系统页_派发角色.dom.html"), encoding="utf-8").read()

    def visible(dom):
        """id → 是否可见（无 display:none 即视为可见；无该节点 → 不在表中）"""
        seen = {}
        for m in re.finditer(r'data-ui-id="([^"]+)"([^>]*)>', dom):
            i, rest = m.group(1), m.group(2)
            st = re.search(r'style="([^"]*)"', rest)
            seen[i] = not (st and 'display: none' in st.group(1))
        return seen

    def ids_of(fname, fval):
        return [e["id"] for e in cfg_els
                if str(e.get("vis_flag")) == fname and str(e.get("vis_when")) == fval]

    def value_flag_page():
        mp = {"cfg_vchar": "snd"}
        for e in cfg_els:
            a = str(e.get("action") or "")
            if a.startswith("config_set_"):
                mp["cfg_v_" + a[len("config_set_"):]] = str(e.get("vis_when"))
        return mp

    vp = value_flag_page()
    sys_ids, snd_ids = ids_of('cfg_page', 'sys'), ids_of('cfg_page', 'snd')
    out.append("数据里带页 flag 的元素：sys=%d 件 / snd=%d 件；值 flag 键 %d 个" % (len(sys_ids), len(snd_ids), len(vp)))
    for tag, dom, mine, other, page in (("系统页（进屏初值态）", sys_dom, sys_ids, snd_ids, "sys"),
                                        ("系统页（**派发 config_char_kaa 后**）", kaa_dom, sys_ids, snd_ids, "sys"),
                                        ("声音页（**点击页签**的真实路径）", snd_dom, snd_ids, sys_ids, "snd"),
                                        ("声音页（深链 ?flags= 路径，对照）", deep_dom, snd_ids, sys_ids, "snd")):
        vis = visible(dom)
        a = sum(1 for i in mine if vis.get(i, False))
        b = sum(1 for i in other if vis.get(i, False))
        out.append("  %s：本页（页 flag）元素可见 %d/%d、**另一页元素可见 %d 件**（应 0）"
                   % (tag, a, len(mine), b))
        leak = []
        for e in cfg_els:
            f = str(e.get("vis_flag") or "")
            if not (f == "cfg_vchar" or f.startswith("cfg_v_")):
                continue
            if vis.get(e["id"], False) and vp.get(f) != page:
                leak.append("%s(%s，属 %s 页)" % (e["id"], f, vp.get(f)))
        n_val = sum(1 for e in cfg_els
                    if str(e.get("vis_flag") or "").startswith("cfg_v_")
                    or e.get("vis_flag") == "cfg_vchar")
        out.append("  %s：带值 flag 的元素共 %d 件 —— **非本页仍可见 %d 件**"
                   % (tag, n_val, len(leak)))
        if leak:
            out.append("     " + "、".join(leak[:8]) + ("…" if len(leak) > 8 else ""))

    # ---- ④b 角色横幅头像（主代理指定）：两档都要**真脸可见、不红框**，且换人正确 ----
    kb_dom = io.open(os.path.join(EVID, "W4_横幅头像_kob.dom.html"), encoding="utf-8").read()

    def missing_of(dom):
        return re.findall(r'ui-missing-label[^>]*>([^<]*)<', dom)

    miss_asu = missing_of(snd_dom)
    miss_kob = missing_of(kb_dom)
    face_imgs = re.findall(r'src="\.\./\.\./krkr/assets/(face/[^"]+)"', kb_dom)
    out.append("④b 横幅头像：声音页(asu) 缺件占位 %d 件；kob 档 缺件占位 %d 件"
               % (len(miss_asu), len(miss_kob)))
    out.append("     kob 档已加载的 face/ 图 = %s" % (sorted(set(face_imgs))[:6],))
    for tag, dom in (("asu", snd_dom), ("kob", kb_dom)):
        vis = visible(dom)
        ids = ["cfg.pv_face_" + tag, "cfg.pv_name_" + tag]
        out.append("     %s 档：%s 可见=%s" % (tag, ids, [vis.get(i, False) for i in ids]))
    # 两档作差：横幅区必须有差异（换人换图）
    fb_a = Image.open(os.path.join(EVID, "W4_横幅头像_asu.png")).convert("RGB")
    fb_k = Image.open(os.path.join(EVID, "W4_横幅头像_kob.png")).convert("RGB")
    banner = (1099, 261, 1099 + 644, 261 + 239)
    out.append("     两档在横幅区（1099,261,644,239）内差异像素 = %d（应 >0）"
               % diff_count(fb_a, fb_k, banner))
    # 并排对照图
    ca, ck = fb_a.crop(banner), fb_k.crop(banner)
    sheet2 = Image.new("RGB", (banner[2] - banner[0], (banner[3] - banner[1]) * 2 + 30), (18, 18, 18))
    d3 = ImageDraw.Draw(sheet2)
    sheet2.paste(ca, (0, 14)); d3.text((6, 2), "cfg_vchar = asu（默认）", fill=(160, 220, 255))
    sheet2.paste(ck, (0, banner[3] - banner[1] + 24))
    d3.text((6, banner[3] - banner[1] + 12), "cfg_vchar = kob", fill=(255, 230, 160))
    p2 = os.path.join(EVID, "W4_横幅头像两档对照.png")
    sheet2.save(p2)
    out.append("     对照图 -> %s" % p2)

    # ---- 对照图：预览区三档 ----
    box = (1090, 715, 1740, 900)
    crops = [im.crop(box) for im in (base, p50, p0)]
    W, H = crops[0].size
    sheet = Image.new("RGB", (W, H * 3 + 44), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    for i, (cr, lab) in enumerate(zip(crops, ["dlg_winopac = 90（默认档）",
                                              "dlg_winopac = 50", "dlg_winopac = 0（全透）"])):
        sheet.paste(cr, (0, i * (H + 14) + 14))
        d.text((6, i * (H + 14) + 2), lab, fill=(160, 220, 255))
    sheet_path = os.path.join(EVID, "W4_预览遮罩三档对照.png")
    sheet.save(sheet_path)
    out.append("对照图 -> %s" % sheet_path)

    # ---- 两页整屏并排 ----
    snd = Image.open(os.path.join(EVID, "W4_声音页_遮罩90.png")).convert("RGB")
    side = Image.new("RGB", (CANVAS_W, CANVAS_H * 2 + 30), (18, 18, 18))
    d2 = ImageDraw.Draw(side)
    side.paste(base, (0, 14))
    d2.text((6, 2), "系统页（cfg_page=sys，默认）", fill=(160, 220, 255))
    side.paste(snd, (0, CANVAS_H + 24))
    d2.text((6, CANVAS_H + 12), "声音页（flags=cfg_page:snd）", fill=(255, 230, 160))
    side_path = os.path.join(EVID, "W4_两页并排.png")
    side.save(side_path)
    out.append("并排图 -> %s" % side_path)

    os.remove(PAGE)
    out.append("（已删除临时页 %s）" % PAGE)
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
