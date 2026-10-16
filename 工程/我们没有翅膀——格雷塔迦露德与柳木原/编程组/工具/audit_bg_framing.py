#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
audit_bg_framing.py —— 逐场景背景落位复算（D-04 全画布口径）
================================================================
**独立于 build_story.py** 重新推导：从装配前的场景数据 `story\scene_*.tjs` 读出每场景的
候选背景与其尺寸，按 `ui_story.tjs::uiStoryApplyScene` 的**运行期规则**重算落位框与黑边。

判据（output 的 [RESULT] 行）：
  · 用 46 件 16:9 覆盖件的场景 → 黑边必须**全 0**（左/右/上/下）
  · 总「零黑边场景数」应与 D-04 前的审计表 `画幅审计\逐场景背景归属.tsv` 对得上账（只增不减）

用法：
  python -X utf8 工具/audit_bg_framing.py --proj "<proj>" [--out <tsv>]
"""
import argparse, io, os, re, sys, glob

CARD_RE = re.compile(r"__ec(\d)")


def is_card(name):
    """与 ui_story.tjs::uiStoryBgIsCard 同判据：basename 里含 `__ec<数字>`。"""
    return bool(CARD_RE.search(os.path.basename(name or "")))


def rd_content_boxes(proj):
    import json
    p = os.path.join(proj, "UI组", "layout", "_root.json")
    o = json.load(io.open(p, encoding="utf-8"))
    cv = o.get("canvas") or {}
    return o.get("content_boxes") or {}, (int(cv.get("width", 1920)), int(cv.get("height", 1080)))


def parse_scenes(story_dir):
    """→ [(id, src, [(asset, w, h), ...]), ...]"""
    out = []
    pat = re.compile(r'id:"([^"]*)",\s*src:"([^"]*)".*?bg:\[(.*?)\],\s*se:', re.S)
    seg = re.compile(r'a:"([^"]*)",\s*w:(\d+),\s*h:(\d+)')
    for fp in sorted(glob.glob(os.path.join(story_dir, "scene_*.tjs"))):
        t = io.open(fp, encoding="utf-8").read()
        m = pat.search(t)
        if not m:
            continue
        bgs = [(a, int(w), int(h)) for a, w, h in seg.findall(m.group(3))]
        out.append((m.group(1), m.group(2), bgs))
    return out


def frame(bgs, cb_by_src, cw, ch):
    """复现 uiStoryApplyScene：取第一张非题卡背景 → 按宽高比接近度选框 → contain。"""
    if not bgs:
        return None
    pick = 0
    for i, (a, _w, _h) in enumerate(bgs):
        if not is_card(a):
            pick = i
            break
    a, aw, ah = bgs[pick]
    full = (0, 0, cw, ch)
    cb = cb_by_src.get("__src__") or full       # 由调用方注入
    if aw > 0 and ah > 0:
        ar = aw / float(ah)
        dsrc = abs(ar - cb[2] / float(cb[3]))
        dfull = abs(ar - cw / float(ch))
        box = full if dfull < dsrc else cb
        k = min(box[2] / float(aw), box[3] / float(ah))
        w, h = int(aw * k), int(ah * k)
        x = box[0] + (box[2] - w) // 2
        y = box[1] + (box[3] - h) // 2
    else:
        box = cb
        x, y, w, h = box
    return pick, a, aw, ah, box, x, y, w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proj", required=True)
    ap.add_argument("--story", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--before", default="",
                    help="D-04 前的审计表（画幅审计\\逐场景背景归属.tsv），用于前后对照")
    args = ap.parse_args()
    proj = os.path.abspath(args.proj)
    story = args.story or os.path.join(proj, "编程组", "krkr", "game", "story")
    cbs, (cw, ch) = rd_content_boxes(proj)
    scenes = parse_scenes(story)
    if not scenes:
        print("[FATAL] 未解析到场景（%s）" % story)
        return 2

    rows, zero, lr, tb = [], 0, 0, 0
    for sid, src, bgs in scenes:
        bx = cbs.get(src)
        box = (bx["x"], bx["y"], bx["w"], bx["h"]) if bx else (0, 0, cw, ch)
        r = frame(bgs, {"__src__": box}, cw, ch)
        if r is None:
            rows.append((sid, src, "", "", 0, 0, "无背景", "", 0, 0, 0, 0, 0, 0, 0, 0))
            continue
        pick, a, aw, ah, box2, x, y, w, h = r
        lb = x - box2[0]
        rb = (box2[0] + box2[2]) - (x + w)
        tbb = y - box2[1]
        bob = (box2[1] + box2[3]) - (y + h)
        nz = (lb == 0 and rb == 0 and tbb == 0 and bob == 0)
        if nz:
            zero += 1
        elif lb or rb:
            lr += 1
        else:
            tb += 1
        rows.append((sid, src, os.path.basename(a), "%dx%d" % (aw, ah),
                     "全画布" if box2 == (0, 0, cw, ch) else "源内容区",
                     pick, lb, rb, tbb, bob, x, y, w, h, "零黑边" if nz else ("左右" if (lb or rb) else "上下")))

    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("scene_id\tsrc\tasset\tasset_size\tbox\tpicked_idx\tleft_bar\tright_bar\ttop_bar\tbottom_bar\tx\ty\tw\th\tverdict\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print("[ok] 明细 → %s" % args.out)

    # 46 件覆盖件的场景必须零黑边
    #   ⚠️ 场景里的引用名是 **flat 名**（`bg__zz_02.jpg`，kind + "__" + 原件 basename），
    #      与清单的 `zz_02.jpg` **不同名** ⇒ 必须先剥掉 `<kind>__` 前缀再比。
    #      （初版忘了剥，导致「命中 0 件」却判 PASS —— 空转假通过，已加下面的防空转守卫。）
    ov_names = set()
    p = os.path.join(proj, "资源组", "美术统一_交付_16比9", "交付清单.tsv")
    if os.path.isfile(p):
        for ln in io.open(p, encoding="utf-8-sig"):
            c = ln.rstrip("\r\n").split("\t")
            if len(c) > 2 and c[0] != "编号":
                ov_names.add(os.path.basename(c[2].replace("\\", "/")))

    def unflat(a):
        return re.sub(r"^[a-z]+__", "", os.path.basename(a or ""))

    ov_rows = [r for r in rows if unflat(r[2]) in ov_names]
    ov_bad = [r for r in ov_rows if r[14] != "零黑边"]

    print("[总账] 场景 %d ｜ 零黑边 %d ｜ 左右留边 %d ｜ 上下留边 %d" % (len(rows), zero, lr, tb))

    # ---- 前后对照（可选）：D-04 前的审计表 ----
    if args.before and os.path.isfile(args.before):
        hdr = None
        bef = {}
        for ln in io.open(args.before, encoding="utf-8-sig"):
            c = ln.rstrip("\r\n").split("\t")
            if hdr is None:
                hdr = c
                continue
            if len(c) != len(hdr):
                continue
            d = dict(zip(hdr, c))
            try:
                bef[d["scene_id"]] = (int(d["left_bar"]), int(d["right_bar"]),
                                      int(d["top_bar"]), int(d["bottom_bar"]))
            except (KeyError, ValueError):
                pass
        now = dict((r[0], (r[6], r[7], r[8], r[9])) for r in rows if isinstance(r[6], int))
        common = sorted(set(bef) & set(now))
        b_bar = [s for s in common if any(bef[s])]
        a_bar = [s for s in common if any(now[s])]
        went0 = [s for s in common if any(bef[s]) and not any(now[s])]
        newbar = [s for s in common if not any(bef[s]) and any(now[s])]
        print("[对照] 与 D-04 前审计表 `%s` 比（共有 %d 场景）："
              % (os.path.basename(args.before), len(common)))
        print("       有黑边：前 %d → 后 %d ｜ 由有变无 %d ｜ 由无变有 %d（须为 0）"
              % (len(b_bar), len(a_bar), len(went0), len(newbar)))
        for s in newbar[:8]:
            print("       ✗ 新增黑边：%s %s → %s" % (s, bef[s], now[s]))
    print("[46件] 清单件 %d ｜ 命中场景 %d 个（去重件 %d）｜ 非零黑边 %d（须为 0）"
          % (len(ov_names), len(ov_rows), len(set(unflat(r[2]) for r in ov_rows)), len(ov_bad)))
    for r in ov_bad[:10]:
        print("     ✗ %s %s → %s" % (r[0], r[2], r[14]))
    print()
    if not ov_rows:
        print("[RESULT] FAIL ｜ 空转：0 个场景命中 46 件清单 —— 判据未生效，结论不可信")
        return 1
    if ov_bad:
        print("[RESULT] FAIL ｜ 46 件仍有 %d 个场景存在黑边" % len(ov_bad))
        return 1
    print("[RESULT] PASS ｜ 46 件 16:9 覆盖件所在场景全部满幅零黑边")
    return 0


if __name__ == "__main__":
    sys.exit(main())
