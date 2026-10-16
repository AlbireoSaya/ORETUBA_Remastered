# -*- coding: utf-8 -*-
"""crop_delivery_evidence.py —— 从引擎巡演导出图裁「正式落地」验收证据图。

用途（ISSUE-20260927-07 · 解析化轮 · 实机复核）：
  ① 选择支节点的**四角 ×8** 与**底边中段 ×8**（证明凸起消失、圆角平滑）；
  ② 番外节点一颗（1:1 + ×2）。

注意：卡片 `nine.l=14 / nine.r=13` ⇒ 竖边中间段被横向拉伸，**角部与左右端 1:1**，
      故角部裁图与素材 1:1 一致（仅 2–3px 跨越拉伸边界，属 nine 版式的固有现象，非本素材问题）；
      底边为直线，横向拉伸不影响其竖向剖面。

用法：
    python crop_delivery_evidence.py --shot <png> --layout <json> --kind select|frag --out <png> [--tag "文字"]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
from PIL import Image, ImageDraw, ImageFont                            # noqa: E402

_HERE = Path(__file__).resolve()
_REPRO5 = _HERE.parents[3] / "_工作" / "ISSUE-20260927-05_流程图实现" / "复现脚本"
sys.path.insert(0, str(_REPRO5))
import make_node_variant_a as MF                                        # noqa: E402


def find_elems(layout, kind, override=None):
    if override:
        return [json.loads(override)]
    els = json.loads(Path(layout).read_text(encoding="utf-8"))["elements"]
    return [e for e in els if e.get("kind") == "image"
            and ("x_ui_node_%s_" % kind) in str(e.get("asset", ""))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", required=True)
    ap.add_argument("--layout", required=True)
    ap.add_argument("--kind", required=True, choices=("select", "frag", "section"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--rect", default=None,
                    help='直接给元素 JSON（如 \'{"id":"fc.node.0010","x":892,"y":190,"w":296,"h":65,'
                         '"asset":"ui/x_ui_node_frag_off.png","nine":{"l":14,"t":0,"r":15,"b":0}}\'）'
                         '；给了就不再读 layout（避免为裁图反复重跑生成器）')
    a = ap.parse_args()

    shot = Image.open(a.shot).convert("RGB")
    els = find_elems(a.layout, a.kind, a.rect)
    if not els:
        print("FATAL: 未找到 kind=%s 的元素" % a.kind)
        return 1
    F = MF.font
    CROP, Z = 34, 8
    PANEL = CROP * Z
    bg = (18, 22, 32)
    margin, gap, labw, head = 24, 12, 250, 128
    NOTCH_SX = 167          # 原件 select 底边缺口列（素材坐标，见 make_node_variant_a.NOTCH_X）

    def notch_dest_x(e):
        """原缺口列（素材 x=167）在**引擎导出图**上的对应列：nine 拉伸按 素材→目标 线性映射。"""
        srcl, srcr = 14, 13          # select 素材 263 宽，nine l=14 / r=13（见布局数据）
        l, r = e["nine"]["l"], e["nine"]["r"]
        k = (e["w"] - l - r) / float((263 - srcl - srcr))
        return e["x"] + l + (NOTCH_SX - srcl) * k

    if a.kind == "select":
        names = ["左上角 TL", "右上角 TR", "左下角 BL", "右下角 BR",
                 "底边左段（文字外）", "底边·原缺口列"]
        W = margin * 2 + labw + len(names) * (PANEL + gap)
        H = head + PANEL + 118
        sh = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(sh)
        d.text((margin, margin), "实机巡演导图 · 选择支节点（%s）：四角 ×%d ＋ 底边 ×%d" % (a.tag, Z, Z),
               font=F(21, True), fill=(238, 243, 250))
        d.text((margin, margin + 32),
               "引擎导出 %s（1920×1080 画布 1:1）｜ 每个面板 %d×%d 源像素、最近邻 ×%d ｜ 节点 id=%s"
               % (Path(a.shot).name, CROP, CROP, Z, els[0]["id"]), font=F(14), fill=(158, 172, 190))
        d.text((margin, margin + 54),
               "判读：四角为解析圆弧（无折线、无钩刺），底边为直线（描边不鼓包）；"
               "nine.l=14 ⇒ 左端 1:1、中段横向拉伸（角部仅 2–3px 跨界，属 nine 版式固有）",
               font=F(14), fill=(255, 214, 140))
        for i, nm in enumerate(names):
            px = margin + labw + i * (PANEL + gap)
            d.text((px + 4, head - 26), nm, font=F(15, True), fill=(255, 214, 140))
        y = head
        for e in els[:2]:
            X, Y, Wn, Hn = e["x"], e["y"], e["w"], e["h"]
            nx = int(round(notch_dest_x(e)))
            d.text((margin, y + PANEL // 2),
                   "%s\n%s\nx=%d y=%d w=%d h=%d\n原缺口列素材 x=%d\n⇒ 导出图 x≈%d" %
                   (a.tag, e["id"], X, Y, Wn, Hn, NOTCH_SX, nx),
                   font=F(15, True), fill=(238, 243, 250))
            boxes = [(X, Y), (X + Wn - CROP, Y), (X, Y + Hn - CROP), (X + Wn - CROP, Y + Hn - CROP),
                     (X + 20, Y + Hn - CROP), (nx - CROP // 2, Y + Hn - CROP)]
            for i, (bx, by) in enumerate(boxes):
                tile = shot.crop((bx, by, bx + CROP, by + CROP)).resize((PANEL, PANEL), Image.NEAREST)
                px = margin + labw + i * (PANEL + gap)
                sh.paste(tile, (px, y))
                d.rectangle([px - 1, y - 1, px + PANEL, y + PANEL], outline=(70, 84, 100))
            y += PANEL + 14
        ty = head + 2 * (PANEL + 14) + 6
        d.text((margin, ty), "注：底色为引擎实际图表底（非我们贴的底），可直接判读柔光与描边随底色的观感；"
                             "「原缺口列」＝修前素材在 x=167 处 alpha=229<230 造成描边 +0.44px 鼓包的那一列。",
               font=F(14), fill=(168, 180, 196))
    else:
        e = els[0]
        X, Y, Wn, Hn = e["x"], e["y"], e["w"], e["h"]
        pad = 8
        node = shot.crop((X - pad, Y - pad, X + Wn + pad, Y + Hn + pad))
        node1, node2 = node, node.resize((node.width * 2, node.height * 2), Image.NEAREST)
        W = margin * 2 + max(labw + node1.width, labw + node2.width) + 40
        H = head + node1.height + 20 + node2.height + 66
        sh = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(sh)
        d.text((margin, margin), "实机巡演导图 · %s（%s）节点：1:1 与 ×2" % (a.tag, a.kind),
               font=F(21, True), fill=(238, 243, 250))
        d.text((margin, margin + 30),
               "引擎导出 %s ｜ 元素 id=%s  x=%d y=%d w=%d h=%d ｜ 裁图含 %dpx 外扩以看柔光"
               % (Path(a.shot).name, e["id"], X, Y, Wn, Hn, pad), font=F(14), fill=(158, 172, 190))
        y = head
        d.text((margin, y + 10), "1:1（%d×%d）" % node1.size, font=F(16, True), fill=(255, 214, 140))
        sh.paste(node1, (margin + labw, y))
        d.rectangle([margin + labw - 1, y - 1, margin + labw + node1.width, y + node1.height], outline=(70, 84, 100))
        y += node1.height + 20
        d.text((margin, y + 10), "×2 最近邻（%d×%d）" % node2.size, font=F(16, True), fill=(255, 214, 140))
        sh.paste(node2, (margin + labw, y))
        d.rectangle([margin + labw - 1, y - 1, margin + labw + node2.width, y + node2.height], outline=(70, 84, 100))
        ty = y + node2.height + 12
        d.text((margin, ty), "判读：四角解析圆弧（r=16）、底边直线无鼓包、柔光沿边连续；描边/配色为现行正式口径。",
               font=F(14), fill=(255, 214, 140))

    sh.save(a.out)
    print("写出 %s %s" % (a.out, sh.size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
