# -*- coding: utf-8 -*-
r"""M39 · 无头 Edge 出**遮罩三档对照图**（HTML 复刻端，1:1，同一张底图）

■ 做法（**不改正式数据来出对照图**）
  生成一只**只读夹具页** `_工作\m39_mask_fixture.html`：它是 `复刻\index.html` 的**逐字拷贝**
  ＋ ① 三条相对路径改指 `..\复刻\…`；② 追加一段夹具脚本——
       · 读 `?opa=<0..255>`（缺省 = 数据里的值，即 150）
       · 归零页面外壳并按 **1:1** 呈现画布（`panel-off` + `setScale(1)` + 外壳 padding 归零），
         使无头截图 = 画布逐像素 1:1，且四档**取景完全一致**；
       · 渲染后**只改 `dlg.mask_bottom` 的 `opacity`**，其余一切照 `ui_layout.js` 走。
  除该元素的 opacity 外，四张图的 DOM 与数据完全相同 ⇒ 差异只能来自强度。

■ 产物
  · `_工作\ISSUE-20260923-01_M39_证据\tier_opa000.png / _100 / _150 / _200`（1:1 全画布）
  · `M39_遮罩三档对照.png`   —— 弱 100 / 中 150 / 强 200，裁 x0..1920 / y560..1080，缩到宽 1200，竖排，每档标注 opacity
  · `M39_遮罩有无对照_0vs150.png` —— 0（无遮罩）vs 150（默认档），同一裁切同尺寸，竖排

■ 用法
    python _工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_mask_tiers.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
REP = os.path.join(UI, "复刻")
WORK = os.path.join(UI, "_工作")
FIXTURE = os.path.join(WORK, "m39_mask_fixture.html")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
UD = "E:/ZCode Workspace/Galgame/临时/edge_m39_tier"

CROP = (0, 560, 1920, 1080)          # x0..1920 / y560..1080（含文字与画面亮部）
CANVAS = (0, 0, 1920, 1080)          # 截图先归一化到「画布 1:1」再裁切
OUTW = 1200                          # 对照图缩到宽 1200
FONT = r"C:\Windows\Fonts\msyh.ttc"
# ★ 实验剖面素材（**只用于对照，不替换正式素材**）：同一几何，纵向剖面改 t^0.8（中段更重）。
#   放在证据目录的 剖面实验\ 下，由夹具把该元素的 <img> 源指过去（正式素材与正式数据均不动）。
PROF_DIR = os.path.join(EVID, "剖面实验")
PROF_T08 = "x_ui_dlgmask_bottom_t0.8.png"
PROF_GAMMA = 0.8
# ★ 无头 Edge 的 `--window-size` 是**含窗口装饰**的尺寸，视口更小（本机实测差 24×93）。
#   故取 1920+24 / 1080+93 使**视口恰为 1920×1080**；再按视口探针断言（见 probe()）。
WINDOW = (1944, 1173)

FIXTURE_JS = r"""
<!-- ==========================================================================
     M39 · 只读夹具脚本（临时件，交付前删除本文件）
     作用（**全部只在渲染后的 DOM 上做，不动正式数据**）：
       · `?opa=<0..255>`  覆盖 dlg.mask_bottom 的 opacity（缺省 = 数据里的值）
       · `?extra=<0..255>[,<0..255>…]` **再叠 N 层同素材/同几何的遮罩**（逐个克隆该元素的
                           DOM 节点、z 序依次 +1、+2…，仍低于文字）—— 等价于数据上「多 N 个
                           元素」；0 / 缺省 = 不叠。合成 α = 255·[1−Π(1−aᵢ/255)]
       · `?prof=<文件名>`  把该元素的 <img> 源换成实验剖面素材（放证据目录的 剖面实验\），
                           用于比较 t^1.6 之外的纵向剖面；缺省 = 用正式素材
       · `?my=<画布y>&mh=<高>` 覆盖遮罩元素的**覆盖范围**（元素 top/height）；缺省 = 数据值。
                           配合 `prof` 换一张同高的剖面素材即得到「更高更缓」的档位
       · `?hide=<元素id>[,<id>…]` 把指定元素 `display:none` —— 用于**实测字形范围**：
                           同一档跑「有它 / 无它」两张再作差，差集即该元素**真实绘出的像素**
                           （含描边；比按数据框估算可靠，数据框只是排版盒）
       · `?showchoices=1` 摊开选择肢（★ 与 krkr 侧同一入口语义：跑完最后一句 ⇒ openChoices），
                           用于量选择肢相对于遮罩的位置；几何仍全部取自屏数据
     另把页面外壳归零 + 画布 setScale(1)，使无头截图 = 画布 1:1 且各档取景一致。
     ========================================================================== -->
<script>
(function () {
  function q(re) { var m = new RegExp('[?&]' + re + '=([^&]*)').exec(location.search || '');
                  return m ? m[1] : null; }
  var opaRaw = q('opa');
  var extraRaw = q('extra');
  var prof = q('prof');
  var myRaw = q('my');
  var mhRaw = q('mh');
  var hideRaw = q('hide');
  var showChoices = q('showchoices');
  var want = opaRaw === null ? null : Number(opaRaw);
  var extraRaw = q('extra');
  var extras = (extraRaw === null) ? []
             : String(extraRaw).split(',').map(Number).filter(function (v) { return v > 0; });
  document.addEventListener('DOMContentLoaded', function () {
    var RPC = window.UI_REPLICA;
    if (RPC && RPC.setScale) RPC.setScale(1);                 // 画布 1:1（不依赖窗口尺寸）
    var sh = document.querySelector('.shell');
    if (sh) { sh.style.maxWidth = 'none'; sh.style.margin = '0';
              sh.style.padding = '0'; }
    document.body.classList.add('panel-off');
    var n = document.querySelector('[data-ui-id="dlg.mask_bottom"]');
    var note = document.createElement('div');
    note.id = 'fixture-note'; note.style.display = 'none';
    if (n) {
      if (want === null) {
        var d = (window.UI_LAYOUT.screens.dialog.elements || []).filter(function (e) {
          return e.id === 'dlg.mask_bottom'; })[0];
        want = d ? Number(d.opacity) : 255;
      }
      n.style.opacity = String(want / 255);
      if (prof) {                                              // 换剖面素材（仅改 <img> 源）
        var im = n.querySelector('img');
        if (im) im.src = 'ISSUE-20260923-01_M39_证据/剖面实验/' + prof;
      }
      if (myRaw !== null) n.style.top = myRaw + 'px';           // 覆盖范围（上沿）
      if (mhRaw !== null) n.style.height = mhRaw + 'px';        // 覆盖范围（高）
      note.setAttribute('data-fixture-geo',
        (myRaw === null ? '(数据值)' : myRaw) + ',' + (mhRaw === null ? '(数据值)' : mhRaw));
      /* 叠 N 层：逐个克隆同素材同几何的遮罩节点，z 序依次 +1（仍远低于文字 z=2203） */
      if (extras.length > 0) {
        var zb = Number(getComputedStyle(n).zIndex || 0);
        var prev = n;
        for (var k = 0; k < extras.length; k++) {
          var cl = n.cloneNode(true);
          cl.setAttribute('data-ui-id', 'dlg.mask_bottom__stack' + (k + 1));
          cl.setAttribute('data-fixture-stack', String(extras[k]));
          cl.style.zIndex = String(zb + 1 + k);
          cl.style.opacity = String(extras[k] / 255);
          prev.parentNode.insertBefore(cl, prev.nextSibling);
          prev = cl;
        }
        note.setAttribute('data-stack-node', String(extras.length));
        var im2 = n.parentNode.querySelector('[data-ui-id="dlg.mask_bottom__stack1"] img');
        note.setAttribute('data-stack-src', im2 ? im2.getAttribute('src') : '(无)');
      }
      var im0 = n.querySelector('img');
      note.setAttribute('data-img-src', im0 ? im0.getAttribute('src') : '(无)');
      document.title = 'FIXTURE opa=' + want
                     + (extras.length ? ' +stack' + extras.join('+') : '')
                     + (prof ? ' prof=' + prof : '');
    }
    note.setAttribute('data-fixture-opa', String(want));
    note.setAttribute('data-fixture-extra', String(extras.join(',')));
    note.setAttribute('data-fixture-prof', String(prof || ''));
    note.setAttribute('data-mask-found', n ? '1' : '0');
    /* 取景自证：把关键 rect 写进 DOM，供 --dump-dom 读取（证明截图 = 画布 1:1） */
    try {
      var st = document.getElementById('stage'), cv = document.getElementById('canvas');
      var r1 = st.getBoundingClientRect(), r2 = cv.getBoundingClientRect();
      note.setAttribute('data-viewport', window.innerWidth + 'x' + window.innerHeight);
      note.setAttribute('data-scale', String(RPC ? RPC.state.scale : '?'));
      note.setAttribute('data-stage-rect', [r1.left, r1.top, r1.width, r1.height].join(','));
      note.setAttribute('data-canvas-rect', [r2.left, r2.top, r2.width, r2.height].join(','));
      note.setAttribute('data-body-h', String(document.body.scrollHeight));
      note.setAttribute('data-doc-h', String(document.documentElement.scrollHeight));
      /* z 序自证：遮罩必须**低于**文字（CSS z-index 是「压在画面之上、文字之下」的落点） */
      var zv = {};
      ['dlg.mask_bottom', 'dlg.mask_bottom__stack1', 'dlg.mask_bottom__stack2',
       'dlg.text', 'dlg.name', 'dlg.content', 'dlg.letterbox'].forEach(
        function (id) {
          var el2 = document.querySelector('[data-ui-id="' + id + '"]');
          zv[id] = el2 ? getComputedStyle(el2).zIndex : '缺';
        });
      note.setAttribute('data-z', JSON.stringify(zv));
      /* 画面层（dynamic story_background）的实绘矩形 —— 供差值统计界定「画面内容」范围 */
      var cv2 = document.querySelector('[data-ui-id="dlg.content"]');
      if (cv2) {
        var r3 = cv2.getBoundingClientRect();
        note.setAttribute('data-content-rect',
          [Math.round(r3.left), Math.round(r3.top),
           Math.round(r3.right), Math.round(r3.bottom)].join(','));
      }
    } catch (e) { note.setAttribute('data-probe-err', String(e)); }
    /* 字形范围实测：把指定元素藏掉（display:none），与未藏的同一档作差即得该元素的实绘像素 */
    if (hideRaw) {
      var ids = String(hideRaw).split(',');
      var done = [];
      ids.forEach(function (id) {
        var el3 = document.querySelector('[data-ui-id="' + id + '"]');
        if (el3) { el3.style.display = 'none'; done.push(id); }
      });
      note.setAttribute('data-hide', done.join(','));
    }
    /* 摊开选择肢：与 krkr 侧同一入口语义（播完最后一句 ⇒ openChoices 用屏数据的几何画） */
    if (showChoices) {
      try {
        var s = RPC.script();
        if ((!s.choices || !s.choices.length) && s.lines && s.lines.length) {
          var last = s.lines[s.lines.length - 1];
          if (last && last.choices && last.choices.length) s.choices = last.choices;
        }
        if (!s.choices || !s.choices.length) {
          s.choices = [{ text_cn: '为了国家与民众' }, { text_cn: '为了阿斯嘉公主' }];
        }
        RPC.endDialog();                              // 与 krkr 侧同一入口：播完末句 ⇒ openChoices
        note.setAttribute('data-choices', '1');
      } catch (e2) { note.setAttribute('data-choices', 'ERR:' + e2); }
    }
    document.body.appendChild(note);
  });
})();
</script>
</body>"""


def build_fixture():
    src = io.open(os.path.join(REP, "index.html"), encoding="utf-8").read()
    out = src
    out = out.replace('href="replica.css"', 'href="../复刻/replica.css"')
    out = out.replace('src="ui_layout.js"', 'src="../复刻/ui_layout.js"')
    out = out.replace('src="replica.js"', 'src="../复刻/replica.js"')
    assert out != src, "index.html 里的三条相对路径一条都没替换到 —— 夹具会指向错文件"
    assert "</body>" in out, "index.html 结构变了（找不到 </body>）"
    out = out.replace("</body>", FIXTURE_JS, 1)
    io.open(FIXTURE, "w", encoding="utf-8").write(out)
    print("  夹具已写：%s（%d 字节）" % (FIXTURE, len(out.encode("utf-8"))))


def probe(opa=150, extra=(), prof=None, my=None, mh=None):
    """把夹具写进 DOM 的取景/机制数据 dump 出来（证明截图 = 画布 1:1 且注入真的生效）"""
    url = ("file:///" + urllib.parse.quote(FIXTURE.replace("\\", "/"))
           + "?screen=dialog&chrome=0&opa=%d" % opa)
    if extra:
        url += "&extra=" + ",".join(str(v) for v in extra)
    if prof:
        url += "&prof=" + prof
    if my is not None:
        url += "&my=%d" % my
    if mh is not None:
        url += "&mh=%d" % mh
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--force-device-scale-factor=1",
           "--window-size=%d,%d" % WINDOW, "--virtual-time-budget=14000",
           "--dump-dom", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dom = r.stdout.decode("utf-8", "replace")
    keys = ["viewport", "scale", "stage-rect", "canvas-rect", "body-h",
            "mask-found", "fixture-opa", "fixture-extra", "fixture-prof",
            "fixture-geo", "stack-node", "stack-src", "img-src", "z", "content-rect"]
    got = {}
    for k in keys:
        m = re.search(r'data-%s="([^"]*)"' % k, dom)
        got[k] = m.group(1) if m else "(缺)"
    return got


def shot(opa, out_name, budget=14000, extra=(), prof=None, my=None, mh=None,
         hide=None, showchoices=False):
    out = os.path.join(EVID, out_name)
    q = "?screen=dialog&chrome=0&opa=%d" % opa
    if extra:
        q += "&extra=" + ",".join(str(v) for v in extra)
    if prof:
        q += "&prof=" + prof
    if my is not None:
        q += "&my=%d" % my
    if mh is not None:
        q += "&mh=%d" % mh
    if hide:
        q += "&hide=" + ",".join(hide)
    if showchoices:
        q += "&showchoices=1"
    url = "file:///" + urllib.parse.quote(FIXTURE.replace("\\", "/")) + q
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + UD, "--hide-scrollbars",
           "--force-device-scale-factor=1",
           "--window-size=%d,%d" % WINDOW, "--virtual-time-budget=%d" % budget,
           "--screenshot=" + out, url]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ok = os.path.exists(out)
    tag = "opa=%3d%s%s%s%s" % (opa,
                               "+叠%s" % "+".join(str(v) for v in extra) if extra else "",
                               " prof=%s" % prof if prof else "",
                               " y%s h%s" % (my, mh) if my is not None else "",
                               " hide=%s" % ",".join(hide) if hide else "")
    if showchoices:
        tag += " choices"
    if ok:
        im = Image.open(out)
        print("  %-52s → %-26s %s  %dx%d（裁到画布 1:1 后 %dx%d）"
              % (tag, out_name, "OK", im.width, im.height, CANVAS[2], CANVAS[3]))
    else:
        print("  %-52s → %-26s **FAILED**" % (tag, out_name))
    return ok


def normalize(path):
    """截图 → 画布 1:1（1920×1080）。取景由 probe() 断言过，故直接按视口原点裁。"""
    im = Image.open(path).convert("RGB")
    return im.crop(CANVAS)


def label_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def stack(panels, out_name, caption, outw=None):
    """panels = [(文本, PIL.Image)]；outw=None ⇒ **保持 1:1 不缩放**，否则等比缩到该宽。
    每档上方画一条标注带。"""
    f = label_font(30)
    band = 46
    scaled = []
    for txt, im in panels:
        if outw is None:
            scaled.append((txt, im, im.height))
        else:
            h = int(round(im.height * outw / float(im.width)))
            scaled.append((txt, im.resize((outw, h), Image.LANCZOS), h))
    W = max(i.width for _t, i, _h in scaled)
    H = sum(h + band for _t, _i, h in scaled) + 10
    canvas = Image.new("RGB", (W, H), (24, 26, 30))
    d = ImageDraw.Draw(canvas)
    y = 0
    for txt, im, h in scaled:
        d.rectangle([0, y, W, y + band - 1], fill=(18, 20, 24))
        d.text((12, y + 8), txt, font=f, fill=(235, 240, 248))
        y += band
        canvas.paste(im, (0, y))
        y += h + 10
    p = os.path.join(EVID, out_name)
    canvas.save(p)
    print("  → %s（%dx%d）｜ %s" % (out_name, W, H, caption))
    return p


def build_profile_asset():
    """生成**实验剖面**素材（只放证据目录，不替换正式素材）：alpha = 255 × t^GAMMA。
    与正式素材同几何（1920×400、RGB 纯黑、底部 255），只有纵向剖面不同 ⇒ 差异只能来自剖面。"""
    from PIL import Image as _I
    W, H = int(CANVAS[2]), 400
    raw = bytearray()
    for y in range(H):
        a = int(round(255.0 * ((y / float(H - 1)) ** PROF_GAMMA)))
        a = 0 if a < 0 else (255 if a > 255 else a)
        raw += bytes((0, 0, 0, a)) * W
    os.makedirs(PROF_DIR, exist_ok=True)
    p = os.path.join(PROF_DIR, PROF_T08)
    _I.frombytes("RGBA", (W, H), bytes(raw)).save(p)
    aa = [int(round(255.0 * ((y / float(H - 1)) ** PROF_GAMMA))) for y in range(H)]
    print("  实验剖面素材已写：%s（t^%.1f，1920x400；中线 alpha=%d vs 正式 t^1.6 的 84）"
          % (os.path.join("剖面实验", PROF_T08), PROF_GAMMA, aa[H // 2]))


def main():
    os.makedirs(UD, exist_ok=True)
    os.makedirs(EVID, exist_ok=True)
    print("=" * 78)
    print("M39 遮罩对照（无头 Edge，HTML 复刻端 1:1，同一底图）")
    print("=" * 78)
    build_fixture()
    build_profile_asset()
    print("")

    print("■ 取景自证（夹具把 #stage / #canvas 的 rect 写进 DOM，用 --dump-dom 读回）")
    g = probe()
    print("   window-size=%s ｜ 实测视口=%s ｜ scale=%s" % (WINDOW, g["viewport"], g["scale"]))
    print("   #stage rect (l,t,w,h) = %s" % g["stage-rect"])
    print("   #canvas rect(l,t,w,h) = %s" % g["canvas-rect"])
    print("   遮罩元素存在=%s ｜ 夹具写入 opa=%s" % (g["mask-found"], g["fixture-opa"]))
    print("   CSS z-index（遮罩须 < 文字）= %s" % g["z"])
    print("   dlg.content 实绘矩形 (l,t,r,b) = %s" % g["content-rect"])
    # ★ 两条注入机制各自单独探针自证（否则「图变暗了」可能来自别的原因）
    gs = probe(150, extra=(150,))
    gp = probe(150, prof=PROF_T08)
    print("   [双叠探针] extra=%s ｜ 注入层数=%s ｜ 层级 z=%s"
          % (gs["fixture-extra"], gs["stack-node"], gs["z"]))
    print("   [换剖面探针] prof=%s ｜ 该元素 <img> src = %s"
          % (gp["fixture-prof"], gp["img-src"]))
    print("   正式素材 src（未注入时）= %s" % g["img-src"])
    framing_ok = (g["stage-rect"] == "0,0,1920,1080" and g["canvas-rect"] == "0,0,1920,1080"
                  and g["scale"] == "1")
    print("   ⇒ 画布位于截图原点且 1:1 = %s" % framing_ok)
    io.open(os.path.join(EVID, "M39_夹具取景自证.json"), "w", encoding="utf-8").write(
        json.dumps({"基本": g, "双叠注入探针": gs, "换剖面注入探针": gp},
                   ensure_ascii=False, indent=2) + "\n")
    print("   （取景自证已落盘：M39_夹具取景自证.json，供差值自证脚本读回画面层矩形）")
    if not framing_ok:
        print("\n   **取景未对齐**：请据实测视口调整 WINDOW（本机差 = %d×%d）后重跑"
              % (WINDOW[0] - 1920, WINDOW[1] - 1080))
        shutil.rmtree(UD, ignore_errors=True)
        return 1
    print("")

    tiers = [(0, "tier_opa000.png"), (100, "tier_opa100.png"),
             (150, "tier_opa150.png"), (200, "tier_opa200.png"),
             # opa=255 = 素材满强度：用于证明「文字在遮罩之上」（文字最亮像素不被压暗）
             (255, "tier_opa255.png"),
             # ★ 第二轮（用户想看"更重"）：贴近单层上限
             (220, "tier_opa220.png"), (250, "tier_opa250.png")]
    ok = True
    for opa, name in tiers:
        ok &= shot(opa, name)
    # ★ 第二轮：② 双叠 / 叠满（同素材同几何多层）；③ 换剖面（t^0.8，中段更重）
    ok &= shot(150, "tier_stack150x2.png", extra=(150,))
    ok &= shot(255, "tier_stack255x2.png", extra=(255,))
    ok &= shot(255, "tier_stack255x3.png", extra=(255, 255))
    ok &= shot(150, "tier_t08_150.png", prof=PROF_T08)
    if not ok:
        shutil.rmtree(UD, ignore_errors=True)
        return 1

    print("")
    for a, name, cap in [
        ([("弱档 opacity=100", "tier_opa100.png"),
          ("中档 opacity=150", "tier_opa150.png"),
          ("强档 opacity=200", "tier_opa200.png")],
         "M39_遮罩三档对照.png",
         "裁 x0..1920 / y560..1080，等比缩到宽 %d" % OUTW),
        ([("无遮罩 opacity=0（对照参照）", "tier_opa000.png"),
          ("默认档 opacity=150", "tier_opa150.png")],
         "M39_遮罩有无对照_0vs150.png",
         "同一裁切、同一尺寸，仅遮罩强度不同"),
    ]:
        panels = [(t, normalize(os.path.join(EVID, n)).crop(CROP)) for t, n in a]
        stack(panels, name, cap, outw=OUTW)

    # 追加一张 **1:1 正文带**对照（不做任何缩放：等比缩小会削弱「字边更清楚」的观感）
    DETAIL = (200, 770, 1500, 1020)     # 含名字框、四行正文与正文带内画面亮部
    panels = [("弱档 opacity=100", normalize(os.path.join(EVID, "tier_opa100.png")).crop(DETAIL)),
              ("中档 opacity=150", normalize(os.path.join(EVID, "tier_opa150.png")).crop(DETAIL)),
              ("强档 opacity=200", normalize(os.path.join(EVID, "tier_opa200.png")).crop(DETAIL))]
    stack(panels, "M39_遮罩三档对照_正文带1比1.png",
          "裁 x200..1500 / y770..1020，**1:1 不缩放**（%dx%d/档）" % (1300, 250), outw=None)

    # ================= ★ 第二轮：更强档位对照 =================
    print("\n" + "=" * 78)
    print("★ 第二轮：更强档位（单层 220/250/255 · 双叠 150×2 · 换剖面 t^0.8）")
    print("=" * 78)
    STRONG = [("单层 150（现行默认）", "tier_opa150.png"),
              ("单层 220", "tier_opa220.png"),
              ("单层 250", "tier_opa250.png"),
              ("单层 255（底部纯黑上限）", "tier_opa255.png")]
    # ① 四档并排（整幅，含文字与画面亮部）
    panels = [(t, normalize(os.path.join(EVID, n)).crop(CROP)) for t, n in STRONG]
    stack(panels, "强档对照_150_220_250_255.png",
          "裁 x0..1920 / y560..1080，等比缩到宽 %d（同一底图、同一裁切）" % OUTW, outw=OUTW)
    # ①b 四档 1:1 不缩放
    panels = [(t, normalize(os.path.join(EVID, n)).crop(DETAIL)) for t, n in STRONG]
    stack(panels, "强档对照_150_220_250_255_正文带1比1.png",
          "裁 x200..1500 / y770..1020，**1:1 不缩放**（%dx%d/档）" % (1300, 250), outw=None)
    # ② 单层 255 vs 双叠 150×2（重点看**中段**差异）
    MID = (200, 640, 1500, 1020)        # 含遮罩中段（y640..806 为纯画面）+ 正文带
    panels = [("单层 150（现行默认）", normalize(os.path.join(EVID, "tier_opa150.png")).crop(MID)),
              ("单层 255（底部纯黑、中段轻）", normalize(os.path.join(EVID, "tier_opa255.png")).crop(MID)),
              ("双叠 150×2（中段也重）", normalize(os.path.join(EVID, "tier_stack150x2.png")).crop(MID))]
    stack(panels, "强档对照_单层255_vs_双叠150x2.png",
          "裁 x200..1500 / y640..1020，**1:1 不缩放**（%dx%d/档）—— 上段看**中段**差异，下段看正文带"
          % (1300, 380), outw=None)
    # ③ 换剖面对照（同样 150：t^1.6 vs t^0.8）
    panels = [("现行剖面 t^1.6 · 150", normalize(os.path.join(EVID, "tier_opa150.png")).crop(MID)),
              ("换剖面 t^0.8 · 150（中段更重）",
               normalize(os.path.join(EVID, "tier_t08_150.png")).crop(MID)),
              ("双叠 150×2（作横向参照）",
               normalize(os.path.join(EVID, "tier_stack150x2.png")).crop(MID))]
    stack(panels, "强档对照_换剖面t08_vs_现行.png",
          "裁 x200..1500 / y640..1020，**1:1 不缩放**（%dx%d/档）" % (1300, 380), outw=None)
    # ④ 「叠满」家族：越叠越平 ⇒ 渐变被抹成硬边矩形的量化观感
    panels = [("单层 255（底部纯黑、形状不变）",
               normalize(os.path.join(EVID, "tier_opa255.png")).crop(MID)),
              ("双叠 150×2（中段增益最大）",
               normalize(os.path.join(EVID, "tier_stack150x2.png")).crop(MID)),
              ("双叠 255×2（中段再压、底部已满）",
               normalize(os.path.join(EVID, "tier_stack255x2.png")).crop(MID)),
              ("三叠 255×3（趋近硬边矩形）",
               normalize(os.path.join(EVID, "tier_stack255x3.png")).crop(MID))]
    stack(panels, "强档对照_叠满家族_趋近硬边.png",
          "裁 x200..1500 / y640..1020，**1:1 不缩放**（%dx%d/档）—— 自上而下「更强 = 越平」"
          % (1300, 380), outw=None)

    shutil.rmtree(UD, ignore_errors=True)
    print("\n（已清理无头 Edge 的 user-data-dir：%s）" % UD)
    print("（夹具 %s 为临时件，交付前删除；对照图保留）" % FIXTURE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
