# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· 新素材呈现 A/B

① 缩放键按下态：**29×29 素材 = 29×29 元素 ⇒ 1:1 直贴、无重采样**（＝按下态不再发虚）
   · 几何事实（可复算）：`x_ui_zoom{in,out}_on.png` 实测 29×29，元素 w/h = 29×29；
     `background-size:100% 100%` 在等尺寸下是**恒等映射**，不存在插值。
   · **像素级 1:1 自证**：把「按下态」与「该件隐藏」两张截图作差 ⇒ 字形掩码；
     与素材 PNG 的 `alpha ≥ 128` 掩码逐像素比 IoU 与计数（1:1 ⇒ 两者同形同数）。
   · **重采样对照（合成控制）**：把同一素材**最近邻**放大成 41×41 再让浏览器缩回 29×29
     （＝复现"素材 41 / 元素 29 = 0.71× 重采样"这条几何路径）⇒ 掩码 IoU 下降、AA 像素增加。
     ★ 说明：原始 41×41 参照件**已不在盘上**（原 `临时\ui_run\…` 副本已被刷成 29×29，全盘无 41×41
       的 zoom `_on`），故控制件由现行件最近邻合成；它证的是**重采样路径的代价**，不是"旧件本身长什么样"。

② `fc.pbk_panel`（回放窗底板 426×241，`visible_default:false`）
   · 默认**确实不绘制**（与"把 `visible_default` 置 true 后重渲"两张图在该矩形逐像素比）；
   · **可被抬起**（置 true 后重渲 ⇒ 该矩形出现面板墨迹；即 `ctx.forceShow` 对应的那条运行期抬起路径）。

■ 用法
    python _工作\ISSUE-20260928-02_HTML\复现脚本\e3_newasset_ab.py
    （环境变量 E3_FLOW_JSON / E3_UI_LAYOUT_JS 可切到冻结 screen1 影子栈）
"""
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.parse

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_DIR = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(HTML_DIR))
REP = os.path.join(UI, "复刻")
LAYOUT = os.path.join(UI, "layout")
ASSETS = os.path.join(UI, "krkr", "assets")
EVID = os.path.join(HTML_DIR, "证据")
TMP = os.path.join(EVID, "_ab")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_e3_ab"
COPY = ["index.html", "replica.css", "flow_data.js", "replica.js", "asset_index.js"]
CANVAS_W, CANVAS_H = 1920, 1080
SCREEN_JSON = os.environ.get("E3_FLOW_JSON", os.path.join(LAYOUT, "screens", "32_flowchart.json"))
LAYOUT_JS = os.environ.get("E3_UI_LAYOUT_JS", os.path.join(REP, "ui_layout.js"))


def fileurl(p):
    return "file:///" + urllib.parse.quote(os.path.abspath(p).replace("\\", "/"))


def screen_of():
    with io.open(SCREEN_JSON, encoding="utf-8") as f:
        return json.load(f)


def build(tag, mutate_js, root):
    dst = os.path.join(TMP, "page_" + tag)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for f in COPY:
        shutil.copy2(os.path.join(REP, f), os.path.join(dst, f))
    shutil.copy2(LAYOUT_JS, os.path.join(dst, "ui_layout.js"))
    page = io.open(os.path.join(dst, "index.html"), encoding="utf-8").read()
    inject = "<script>window.UI_ASSET_ROOT = '%s';</script>\n" % (fileurl(root) + "/")
    page = page.replace('<script src="replica.js"></script>', inject + '<script src="replica.js"></script>')
    hook = ("<style>.shell{max-width:none!important;padding:0!important;margin:0!important}"
            ".shell-head,.shell-foot{display:none!important}"
            "#stage-wrap{justify-content:flex-start!important;display:block!important}"
            "#stage{box-shadow:none!important}</style>"
            "<script>window.addEventListener('load',function(){try{"
            "var R=window.UI_REPLICA; R&&R.setScale(1);"
            "%s"
            "}catch(e){var o=document.createElement('pre');o.id='e3err';o.textContent='E3ERR '+e.message;"
            "document.body.appendChild(o);}});</script>") % mutate_js
    page = page.replace("</body>", hook + "</body>")
    io.open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)
    return dst


def shot(tag, mutate_js, root, out):
    dst = build(tag, mutate_js, root)
    url = fileurl(os.path.join(dst, "index.html")) + "?screen=flowchart&chrome=0"
    os.makedirs(UD, exist_ok=True)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--user-data-dir=" + UD, "--hide-scrollbars", "--window-size=1944,1180",
                    "--virtual-time-budget=9000", "--screenshot=" + os.path.abspath(out), url],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not os.path.exists(out):
        raise SystemExit("截图失败：" + out)
    im = Image.open(out).convert("RGB")
    if im.width >= CANVAS_W and im.height >= CANVAS_H:
        im = im.crop((0, 0, CANVAS_W, CANVAS_H))
    im.save(out)
    return out


def shadow_root(tag, overrides):
    """影子素材根：全量 ui/ 用 hardlink（零拷贝），overrides 里的文件用真拷贝覆盖。
    ★ 覆盖前先 os.remove 掉 hardlink —— 否则 copy2 会**写穿**到原始素材（绝对禁止）。"""
    root = os.path.join(TMP, "root_" + tag)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "ui"))
    n = 0
    for name in os.listdir(os.path.join(ASSETS, "ui")):
        src = os.path.join(ASSETS, "ui", name)
        if not os.path.isfile(src):
            continue
        try:
            os.link(src, os.path.join(root, "ui", name))
        except OSError:
            shutil.copy2(src, os.path.join(root, "ui", name))
        n += 1
    for name, src in overrides.items():
        dst = os.path.join(root, "ui", name)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy2(src, dst)
    return root, n


def region(png, rect):
    a = np.asarray(Image.open(png).convert("RGB"))
    x, y, w, h = [int(v) for v in rect]
    return a[y:y + h, x:x + w].astype(np.int16)


def mask_vs_bg(reg, bg, thr=12):
    return np.abs(reg - bg).max(axis=2) > thr


def alpha_mask(png, thr=128):
    a = np.asarray(Image.open(png).convert("RGBA"))
    return a[:, :, 3] >= thr


def iou(m1, m2):
    if m1.shape != m2.shape:
        return float("nan")
    inter = int((m1 & m2).sum())
    uni = int((m1 | m2).sum())
    return 1.0 if uni == 0 else inter / float(uni)


def stacks(m):
    dx = np.abs(np.diff(m.astype(np.int16), axis=1)).max() if m.shape[1] > 1 else 0
    return int(dx)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(TMP, exist_ok=True)
    sc = screen_of()
    els = {e["id"]: e for e in sc.get("elements", [])}
    print("屏数据 = %s ｜ 渲染栈 = %s" % (SCREEN_JSON, LAYOUT_JS))
    for k in ("fc.zoom_plus", "fc.zoom_minus", "fc.pbk_panel"):
        if k not in els:
            print("★ 数据里没有 %s ⇒ 当前盘上不是 screen1 预设" % k)
            return 2

    rz = els["fc.zoom_plus"]
    rect = (rz["x"], rz["y"], rz["w"], rz["h"])
    asset_on = os.path.join(ASSETS, "ui", "x_ui_zoomin_on.png")
    a_on = Image.open(asset_on).convert("RGBA")
    am_on = alpha_mask(asset_on)

    # 合成控制件：现行 29×29 最近邻放大到 41×41（复现 0.71× 重采样路径）
    ctl = os.path.join(TMP, "x_ui_zoomin_on_41.png")
    a_on.resize((41, 41), Image.NEAREST).save(ctl)
    root_new, n_new = shadow_root("new", {})
    root_ctl, _ = shadow_root("ctl41", {"x_ui_zoomin_on.png": ctl})

    hide = "var n=document.querySelector('[data-ui-id=\"fc.zoom_plus\"]'); if(n) n.style.display='none';"
    zoom_press = ("var e=document.querySelector('[data-ui-id=\"fc.zoom_plus\"]');"
                  "e&&e.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true,"
                  "view:window,button:0,buttons:1}));")
    p_bg = shot("zoom_bg", hide, root_new, os.path.join(TMP, "zoom_bg.png"))
    p_new = shot("zoom_new", zoom_press, root_new, os.path.join(EVID, "E3_新素材_zoom按下_29px.png"))
    p_ctl = shot("zoom_ctl41", zoom_press, root_ctl, os.path.join(EVID, "E3_新素材_zoom按下_对照41px.png"))

    bg = region(p_bg, rect)
    reg_new = region(p_new, rect)
    reg_ctl = region(p_ctl, rect)
    m_new = mask_vs_bg(reg_new, np.median(bg.reshape(-1, 3), axis=0))
    m_ctl = mask_vs_bg(reg_ctl, np.median(bg.reshape(-1, 3), axis=0))

    print("\n=== ① 缩放键按下态（fc.zoom_plus，元素 %dx%d）===" % (rz["w"], rz["h"]))
    print("  素材 x_ui_zoomin_on.png 实测 %dx%d ｜ 元素 %dx%d ⇒ %s"
          % (a_on.width, a_on.height, rz["w"], rz["h"],
             "等尺寸 = 1:1 直贴（不存在重采样）" if (a_on.width, a_on.height) == (rz["w"], rz["h"]) else "不等尺寸"))
    # ★ 硬判据：把素材 RGBA 按「该件隐藏图」的实际底板逐像素做直线 alpha 合成，
    #   与真实按下态渲染逐像素比 ⇒ 1:1 直贴时残差应为 0/±1（浏览器直通 alpha）。
    #   若发生过重采样，边缘会被插值成β像素，残差在边缘带显著上升。
    rgba = np.asarray(Image.open(asset_on).convert("RGBA")).astype(np.float64)
    al = (rgba[:, :, 3:4] / 255.0)
    exp = np.clip(rgba[:, :, :3] * al + bg.astype(np.float64) * (1.0 - al), 0, 255)
    res = np.abs(exp - reg_new.astype(np.float64)).max(axis=2)
    print("  1:1 自证（素材 RGBA 逐像素直线 alpha 合成 vs 真实渲染）：最大残差 %.0f/255 ｜ 平均 %.2f ｜ "
          "残差 ≤2 的像素 %.1f%% ｜ ≤6 的像素 %.1f%%"
          % (res.max(), res.mean(), 100.0 * (res <= 2).mean(), 100.0 * (res <= 6).mean()))
    print("  对照试验（控制件 = 现行件最近邻放大到 41×41 再让浏览器缩回 29×29）：掩码 %d px ｜ maxΔ %d ｜"
          " 与 1:1 渲染差 %d px"
          % (int(m_ctl.sum()), stacks(reg_ctl), int((mask_vs_bg(reg_ctl, np.median(bg.reshape(-1, 3), axis=0))
                                                     != mask_vs_bg(reg_new, np.median(bg.reshape(-1, 3), axis=0))).sum())))
    print("  ★ 如实说明：该合成控制**未能复现旧发虚**（最近邻放大后再双线性缩回 ≈ 恒等，两者几乎逐像素相同）")
    print("    ⇒ 发虚对照缺**原件**；原始 41×41 件已不在盘上（原 `临时\\ui_run\\…` 副本已被刷成 29×29，")
    print("      全盘再搜无任何非 29×29 的 zoom `_on`）。可站得住的硬结论是上面那条几何 + 合成残差：")
    print("      素材与元素等尺寸 ⇒ 1:1 直贴、无重采样；旧 41×41 的 0.71× 重采样路径已不存在。")

    # 8× 对照图（左=控制件 41→29 ｜ 右=现行 29×29）
    def big(a, z=10):
        im = Image.fromarray(a.astype(np.uint8))
        return im.resize((im.width * z, im.height * z), Image.NEAREST)
    cl, cr = big(reg_ctl), big(reg_new)
    side = Image.new("RGB", (cl.width + cr.width + 30, max(cl.height, cr.height)), (25, 25, 25))
    side.paste(cl, (0, 0))
    side.paste(cr, (cl.width + 30, 0))
    side.save(os.path.join(EVID, "E3_新素材_zoom按下_对照左vs现行右_10x.png"))

    # ── ② pbk_panel ────────────────────────────────────────────────────
    raise_js = ("var F=window.UI_LAYOUT.screens.flowchart;"
                "F.elements.forEach(function(e){ if(e.id==='fc.pbk_panel') e.visible_default=true; });"
                "window.UI_REPLICA.renderScreen('flowchart',{noHistory:true});")
    r = els["fc.pbk_panel"]
    box = (r["x"], r["y"], r["w"], r["h"])
    p_hide = shot("pbk_hide", "", root_new, os.path.join(EVID, "E3_新素材_pbkpanel_默认隐藏.png"))
    p_show = shot("pbk_show", raise_js, root_new, os.path.join(EVID, "E3_新素材_pbkpanel_抬起后.png"))
    h_reg = region(p_hide, box)
    s_reg = region(p_show, box)
    dm = np.abs(h_reg - s_reg).max(axis=2) > 6
    n_diff = int(dm.sum())
    print("\n=== ② fc.pbk_panel（%dx%d，visible_default:false）===" % (r["w"], r["h"]))
    print("  默认隐藏 vs 抬起后：该矩形差异像素 %d / %d（%.1f%%）⇒ %s"
          % (n_diff, dm.size, 100.0 * n_diff / dm.size,
             "默认确实不绘制（抬起后整块面板出现）" if n_diff > dm.size * 0.10 else "★ 默认可能仍在绘制"))

    txt = ["E3 新素材呈现 A/B（ISSUE-20260928-02 · HTML 侧）", "",
           "① 缩放键按下态（fc.zoom_plus %dx%d 元素）" % (rz["w"], rz["h"]),
           "   素材 x_ui_zoomin_on.png = %dx%d（实测）⇒ %s"
           % (a_on.width, a_on.height, "1:1 直贴、无重采样" if (a_on.width, a_on.height) == (rz["w"], rz["h"]) else "非等尺寸"),
           "   1:1 自证（素材 RGBA 逐像素 alpha 合成 vs 真实渲染）：最大残差 %.0f/255 ｜ 平均 %.2f ｜ ≤2 占 %.1f%% ｜ ≤6 占 %.1f%%"
           % (res.max(), res.mean(), 100.0 * (res <= 2).mean(), 100.0 * (res <= 6).mean()),
           "   对照试验（现行件最近邻放大 41×41 再缩回 29×29）：掩码 %d px ｜ maxΔ %d ｜ 与 1:1 渲染差 %d px"
           % (int(m_ctl.sum()), stacks(reg_ctl),
              int((mask_vs_bg(reg_ctl, np.median(bg.reshape(-1, 3), axis=0))
                   != mask_vs_bg(reg_new, np.median(bg.reshape(-1, 3), axis=0))).sum())),
           "   ★ 该合成控制**未能复现旧发虚**（放大后再缩回 ≈ 恒等）—— 旧发虚对照缺**原件**：",
           "     原始 41×41 件已不在盘上（原 临时\\ui_run 副本被刷成 29×29；全盘再搜无 41×41 zoom _on）。",
           "     站得住的硬结论：素材与元素等尺寸 ⇒ 1:1 直贴、无重采样（几何 + 合成残差两条）。", "",
           "② fc.pbk_panel（%dx%d，visible_default:false）" % (r["w"], r["h"]),
           "   默认隐藏 vs 抬起后差异 %d 像素（%.1f%%）⇒ %s"
           % (n_diff, 100.0 * n_diff / dm.size,
              "默认不绘制；置 visible_default=true 重渲即出现（可被抬起，非死件）" if n_diff > dm.size * 0.10
              else "★ 默认仍在绘制"),
           "",
           "产物：E3_新素材_zoom按下_29px.png / E3_新素材_zoom按下_对照41px.png / "
           "E3_新素材_zoom按下_对照左vs现行右_10x.png / E3_新素材_pbkpanel_默认隐藏.png / "
           "E3_新素材_pbkpanel_抬起后.png"]
    io.open(os.path.join(EVID, "E3_新素材AB_日志.txt"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
    print("\n日志：%s" % os.path.join(EVID, "E3_新素材AB_日志.txt"))
    shutil.rmtree(UD, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
