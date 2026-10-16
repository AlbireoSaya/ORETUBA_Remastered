# -*- coding: utf-8 -*-
r"""M46 · 从巡演产物刷新 krkr 端证据（日志摘录 + 三张导图 + 对照图 + 两端对照）

■ 前置：先跑一次 `krkr\run_autotour.bat`（约 80 秒自退）
■ 用法：`python _工作\M46_逐项三态证据\复现脚本\m46_refresh_krkr_evidence.py`

■ 产出（覆盖写，全部落在本证据目录）
  M46_巡演_krkr摘录.txt            日志摘录（UTF-16LE → UTF-8）
  M46_krkr_shot05_常态.png         巡演导出的选择支屏（常态）
  M46_krkr_shot06_悬停第2项.png    合成指针悬停第 2 项之后
  M46_krkr_shot07_按住第3项.png    合成指针按住第 3 项之后
  M46_krkr_三态对照.png            上面三张裁到选项区竖排对照
  M46_两端对照_krkr左_HTML右.png    与 HTML 端同状态并排（需要先跑 m46_html_state_shots.py）

■ 同时打印**逐像素判据**（不必肉眼）：
  常态 vs 悬停 / 常态 vs 按住 的差异框 —— 必须各自**恰好落在一条选项带**（1113×83）。
"""
import io
import os
import re

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))                     # …\UI组
WT = os.path.dirname(os.path.dirname(os.path.dirname(UI)))      # …\wt-qbicons
SAVE = os.path.join(WT, "临时", "ui_run", "runtime", "savedata")

ROW_H, GAP, Y0, ITEM_W, X0 = 83, 17, 300, 1113, 404
CROP = (380, 340, 1540, 600)                                    # 画布坐标裁剪区（含三行）


def read_log():
    raw = io.open(os.path.join(SAVE, "krkr.console.log"), "rb").read()
    return raw.decode("utf-16-le", "replace").splitlines()


def main():
    lines = read_log()
    keep = [l for l in lines
            if ("M46PTR" in l or "合成指针" in l or "共记录" in l or "缺件元素" in l
                or "PNG 导出" in l or "转场 成功" in l or "quit (autotour" in l
                or "巡演结束" in l)]
    io.open(os.path.join(EVID, "M46_巡演_krkr摘录.txt"), "w", encoding="utf-8").write(
        "\n".join(keep) + "\n")
    print("日志摘录 %d 行" % len(keep))
    for l in keep:
        if "M46PTR" in l:
            print("   " + l[l.index("说明=") + 3:][:210])
    assert sum(1 for l in lines if "★M46PTR★ PASS" in l) >= 2, "巡演里没看到两条 PASS 判词"
    assert any("★M46PTR-REJECT★" in l for l in lines), "负向对照未出现 REJECT 判词"

    # 巡演导图：seq 05/06/07 = 选择支常态 / 悬停 / 按住（步骤表顺序固定）
    shots = [("M46_krkr_shot05_常态.png", "shot_05_choices.png"),
             ("M46_krkr_shot06_悬停第2项.png", "shot_06_choices.png"),
             ("M46_krkr_shot07_按住第3项.png", "shot_07_choices.png")]
    ims = []
    for dst, src in shots:
        im = Image.open(os.path.join(SAVE, src)).convert("RGB")
        im.save(os.path.join(EVID, dst))
        ims.append(im)
    a, b, c = ims

    def bbox_of(x, y):
        return ImageChops.difference(x, y).getbbox()

    band = (X0, Y0, X0 + ITEM_W, Y0 + ROW_H)
    band2 = (X0, Y0 + ROW_H + GAP, X0 + ITEM_W, Y0 + 2 * (ROW_H + GAP))
    print("常态 vs 悬停 差异框 =", bbox_of(a, b), "  期望 ≈ 第 2 条带", band2)
    print("常态 vs 按住 差异框 =", bbox_of(a, c), "  期望 ≈ 第 3 条带",
          (X0, Y0 + 2 * (ROW_H + GAP), X0 + ITEM_W, Y0 + 2 * (ROW_H + GAP) + ROW_H))
    print("（第 1 条带内是否被波及：常态 vs 悬停 =", bbox_of(a.crop(band), b.crop(band)),
          "／常态 vs 按住 =", bbox_of(a.crop(band), c.crop(band)), "）")
    assert bbox_of(a.crop(band), b.crop(band)) is None, "第 1 条带被误改"
    assert bbox_of(a.crop(band), c.crop(band)) is None, "第 1 条带被误改"

    crops = [im.crop(CROP) for im in ims]
    W, H = crops[0].size
    out = Image.new("RGB", (W, H * 3 + 16), (20, 20, 20))
    for i, cr in enumerate(crops):
        out.paste(cr, (0, i * (H + 8)))
    out.resize((int(W * 0.62), int((H * 3 + 16) * 0.62)), Image.LANCZOS).save(
        os.path.join(EVID, "M46_krkr_三态对照.png"))
    print("对照图 = M46_krkr_三态对照.png")

    # 两端对照（HTML 三张必须已存在，否则跳过）
    hs = ["M46_html_常态.png", "M46_html_悬停第2项.png", "M46_html_按住第3项.png"]
    if not all(os.path.exists(os.path.join(EVID, h)) for h in hs):
        print("（HTML 三张不在，跳过两端对照图 —— 先跑 m46_html_state_shots.py）")
        return 0
    m = re.search(r'id="canvas"[^>]*transform:\s*scale\(([0-9.]+)\)',
                  io.open(os.path.join(EVID, "M46_html_probe_dump.html"), encoding="utf-8").read())
    s = float(m.group(1))
    ox, oy = 490.6, 195.0        # HTML 页里画布原点（与 m46_html_state_shots 同口径）
    W2, H2 = 1160, 260

    def html_crop(name):
        im = Image.open(os.path.join(EVID, name))
        return im.crop((int(CROP[0] * s + ox), int(CROP[1] * s + oy),
                        int(CROP[2] * s + ox), int(CROP[3] * s + oy))).resize((W2, H2), Image.LANCZOS)

    out2 = Image.new("RGB", (W2 * 2 + 24, H2 * 3 + 32), (16, 16, 16))
    for i, (k, h) in enumerate(zip(crops, hs)):
        kk = k.resize((W2, H2), Image.LANCZOS)
        out2.paste(kk, (0, i * (H2 + 16)))
        out2.paste(html_crop(h), (W2 + 24, i * (H2 + 16)))
    out2.resize((int(out2.width * 0.62), int(out2.height * 0.62)), Image.LANCZOS).save(
        os.path.join(EVID, "M46_两端对照_krkr左_HTML右.png"))
    print("两端对照图 = M46_两端对照_krkr左_HTML右.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
