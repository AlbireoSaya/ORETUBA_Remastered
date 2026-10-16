# -*- coding: utf-8 -*-
r"""m09_pill_blank.py —— ISSUE-20260926-09 任务 A：药丸底图 14 件 → 1 支共用件

把用户裁定的干净底图（生图去字版 `_ai_fit.png`，纹理=生图 / alpha=原图）编码为
`krkr\assets\ui\x_ui_psv_pill_blank.png`（**新文件**，不覆盖任何既有件）。

编码口径（派单口径，与本族 `x_ui_psv_*` 既有件结果一致：RGB 值全部 ≡ 0 (mod 4)）：
  · RGB 三通道 `& 0xFC`（降色深，低 2 bit 清零）
  · alpha 通道**逐字节不动**
  · `optimize=True, compress_level=9`

自证（不符即报错退出）：
  1. 源件尺寸 = 560×72 RGBA；产出尺寸同；
  2. 量化前后 alpha 逐字节一致；
  3. RGB 逐像素 max|Δ| ≤ 4；
  4. 目标文件若已存在：字节级一致 ⇒ no-op（幂等）；不一致 ⇒ 报错停手（不覆盖既有件）。

用法（在 <UI组>\ 下）：
    set PYTHONPATH=E:\ZCode Workspace\Galgame\工具\pylibs
    python "_工作\ISSUE-20260926-09_config\复现脚本\m09_pill_blank.py"
"""
import hashlib
import io
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", "..", ".."))          # …/UI组
SRC = os.path.join(UI, "_工作", "ISSUE-20260926-09_药丸底图", "取证", "_ai_fit.png")
DST = os.path.join(UI, "krkr", "assets", "ui", "x_ui_psv_pill_blank.png")
EXP_SIZE = (560, 72)


def md5(b):
    return hashlib.md5(b).hexdigest()


def quant(ch):
    """低 2 bit 清零（& 0xFC）"""
    return ch.point(lambda v: v & 0xFC)


def encode(im):
    r, g, b, a = im.split()
    im2 = Image.merge("RGBA", (quant(r), quant(g), quant(b), a))
    buf = io.BytesIO()
    im2.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def main():
    if not os.path.isfile(SRC):
        raise SystemExit("!! 源件缺失：%s" % SRC)
    src = Image.open(SRC)
    if src.mode != "RGBA":
        raise SystemExit("!! 源件不是 RGBA：%s" % src.mode)
    if src.size != EXP_SIZE:
        raise SystemExit("!! 源件尺寸 %s ≠ %s" % (src.size, EXP_SIZE))
    data = encode(src)
    out = Image.open(io.BytesIO(data))

    # ── 自证 ─────────────────────────────────────────────────────────
    fails = []
    if out.size != EXP_SIZE:
        fails.append("产出尺寸 %s ≠ %s" % (out.size, EXP_SIZE))
    sa, oa = src.getchannel("A").tobytes(), out.getchannel("A").tobytes()
    alpha_ok = sa == oa
    if not alpha_ok:
        fails.append("alpha 不一致（%d 处差异）"
                     % sum(1 for x, y in zip(sa, oa) if x != y))
    maxd = 0
    for ch in range(3):
        sb = src.getchannel(ch).tobytes()
        ob = out.getchannel(ch).tobytes()
        maxd = max(maxd, max(abs(x - y) for x, y in zip(sb, ob)))
    if maxd > 4:
        fails.append("RGB max|Δ| = %d > 4" % maxd)
    lowbits = set()
    for ch in range(3):
        lowbits |= set(v & 3 for v in out.getchannel(ch).tobytes())
    if lowbits != {0}:
        fails.append("RGB 低 2 bit 未清零：%s" % sorted(lowbits))

    print("=" * 100)
    print("m09 任务 A · 药丸共用底图产出")
    print("=" * 100)
    print("源件      ：%s" % SRC)
    print("源件      ：%s %dx%d   md5=%s" % (src.mode, src.size[0], src.size[1], md5(open(SRC, 'rb').read())))
    print("目标      ：%s" % DST)
    print("产出字节  ：%d   md5=%s" % (len(data), md5(data)))
    print("尺寸      ：%s（期望 %s）" % ("%dx%d" % out.size, "%dx%d" % EXP_SIZE))
    print("alpha     ：逐字节一致 = %s" % ("是 ✓" if alpha_ok else "否 ✗"))
    print("RGB 量化  ：& 0xFC ｜ max|Δ| = %d（要求 ≤ 4）｜ 低 2bit 集合 = %s"
          % (maxd, sorted(lowbits)))
    print("落盘口径  ：optimize=True, compress_level=9 ｜ 模式 %s（非 P ✓）" % out.mode)
    if fails:
        print("!! 自证失败：%s" % "；".join(fails))
        raise SystemExit(2)

    existed = os.path.isfile(DST)
    if existed:
        old = open(DST, "rb").read()
        if old == data:
            print("盘上已有同字节文件 ⇒ no-op（幂等，不重写）")
        else:
            print("!! 盘上已存在**不同内容**的 %s —— 派单要求「新文件、勿覆盖既有件」，停止。"
                  % os.path.basename(DST))
            raise SystemExit(3)
    else:
        with open(DST, "wb") as fh:
            fh.write(data)
        print("已落盘（新文件）：%s" % DST)
    print("自证：尺寸 560×72 ✓ ｜ alpha 逐字节不动 ✓ ｜ RGB max|Δ|=%d ≤ 4 ✓ ｜ 新文件 ✓" % maxd)


if __name__ == "__main__":
    main()
