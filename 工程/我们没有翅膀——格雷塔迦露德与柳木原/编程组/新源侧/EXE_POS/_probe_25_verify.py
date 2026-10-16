#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_probe_25_verify.py — 「PC 立绘落位/层序」总验 (可失败). 全部只读(源) + 只写本模块目录.

断言(每条都可失败):
  V1 客户端画布 = 800x600 : baseline.png 中 y=550 行非黑像素跨度 = 800
  V2 CHR.LPK 取出 mas01b.elg, 在 (left=178, top=17) 处与截图 **逐像素全等率 >= 0.99**
  V3 同上 asu02a.elg 在 (left=371, top=57) 处 全等率 >= 0.98
  V4 重叠区层序: 与 mas01b 全等率 >= 0.90 且与 asu02a 全等率 <= 0.05
     ⇒ **槽号大者(MAS 槽1)在明日香(槽0)之上**
  V5 静态: 全 PC 二进制里不存在含 >=4 个排布网格值的 8 字窗口(u32/u16) ⇒ 无静态表
  V6 func_lib 字节码的槽循环上界 = 6 (0x2F50 处 `LT i, 6`)

用法: python -X utf8 _probe_25_verify.py
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# 本分支同树兄弟 `../EXE`（`_probe_12_funclib` 等；入库后原位可跑）——优先于下面的旧位置。
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "EXE")))
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\lucifen\Lucifen-Tools")
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\工具\pylibs")
# ⚠️ 旧开发位置（`子代理工作区\ISSUE-20261008-09\EXE\`）= **历史副本，勿用**；
#    仅为 `_probe_12/_probe_23` 的兜底 import 保留（本分支同树兄弟已在上方优先）。
sys.path.insert(0, r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-09\EXE")

import numpy as np
from PIL import Image
import elg2png

SHOT = r"E:\ZCode Workspace\Galgame\临时\layer_exp\shots\baseline.png"
# `_chr\`（mas01b/asu02a 立绘原件）：本模块目录 = 已剔出库的可再生产物；旧开发位置 = 历史副本（只读）。
# 都找不到时从 `临时\layer_exp\game\CHR.LPK` 现取到本模块目录（`.elg` 已被 .gitignore 排除）。
_CHR_OLD = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-09\EXE_POS\_chr"
CHR_LPK = r"E:\ZCode Workspace\Galgame\临时\layer_exp\game\CHR.LPK"
X0, Y0 = 6, 30
GRID = [236, 336, 436, 640, 844, 944, 1044, 304, 404, 204, 150, 190, 608]
RES = []


def chk(tag, ok, detail):
    RES.append((tag, "PASS" if ok else "FAIL", detail))
    print("  [%s] %s  %s" % ("PASS" if ok else "FAIL", tag, detail))


def ensure(name):
    """找 `_chr\\<name>.elg.elg`：本模块 → 旧副本（只读）；都没有则从 CHR.LPK 取到本模块目录。"""
    for d in (os.path.join(HERE, "_chr"), _CHR_OLD):
        p = os.path.join(d, name + ".elg.elg")
        if os.path.exists(p):
            return p
    p = os.path.join(HERE, "_chr", name + ".elg.elg")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    import _probe_23_chrsprite as P23
    lp = P23.open_lpk(P23.LPKPATH)
    open(p, "wb").write(P23.get_entry(lp, name + ".elg"))
    return p


def load(p):
    r = elg2png.Reader(open(p, "rb").read())
    return r, np.asarray(r.decode().convert("RGBA"), dtype=np.int16)


def main():
    # ---- 输入前置（★ 2026-10-09：缺输入给**明确报错**，不再崩 FileNotFoundError）
    miss = []
    if not os.path.exists(SHOT):
        miss.append(SHOT)
    if not os.path.isdir(os.path.join(HERE, "_chr")) and not os.path.isdir(_CHR_OLD) \
            and not os.path.exists(CHR_LPK):
        miss.append("`_chr\\`（mas01b/asu02a 立绘原件）或 `%s`" % CHR_LPK)
    if miss:
        print("== INPUT_MISSING（_probe_25 无法执行：输入缺失，非「判据失败」）==")
        for p in miss:
            print("   缺输入: %s" % p)
        print("   说明: `_chr\\` 与 `work\\` 为已剔出库的可再生产物（见 `..\\说明.md` §三末）；")
        print("         截图/立绘在 `临时\\layer_exp\\`（gitignored，须先做活体实验生成）。")
        print("CHECK_ERROR=INPUT_MISSING  files=%d" % len(miss))
        return 3
    shot_full = np.asarray(Image.open(SHOT).convert("RGB"), dtype=np.int16)
    print("shot", shot_full.shape)

    # V1
    row = shot_full[30 + 550]
    nb = np.where(~np.all(row < 20, axis=1))[0]
    span = int(nb[-1] - nb[0] + 1) if len(nb) else 0
    chk("V1 客户端画布=800x600", span == 800 and shot_full.shape[0] >= 630,
        "y=550 非黑跨度=%d, 起始 col=%d, 图高=%d" % (span, int(nb[0]) if len(nb) else -1, shot_full.shape[0]))

    S = shot_full[Y0:Y0 + 600, X0:X0 + 800]
    rM, M = load(ensure("mas01b"))
    rA, A = load(ensure("asu02a"))
    LM, TM, LA, TA = 178, 17, 371, 57

    def exact(Ss, L, T, x0, x1, y0, y1):
        al = (Ss[:, :, 3] > 240)
        m = np.zeros_like(al)
        m[y0:y1, x0:x1] = True
        al &= m
        ys, xs = np.where(al)
        ys, xs = ys[::2], xs[::2]
        vy, vx = T + ys, L + xs
        ok = (vy >= 0) & (vy < 600) & (vx >= 0) & (vx < 800)
        return float(np.all(S[vy[ok], vx[ok]] == Ss[ys[ok], xs[ok], :3], axis=1).mean()), int(ok.sum())

    r2 = exact(M, LM, TM, 0, 371, 0, 400)
    chk("V2 MAS01B @(178,17) 逐像素全等", r2[0] >= 0.99,
        "全等率=%.4f (%d px), 位图 %dx%d, ELG 原点=(%d,%d)" % (r2[0], r2[1], M.shape[1], M.shape[0], rM.offset_x, rM.offset_y))
    r3 = exact(A, LA, TA, 250, A.shape[1], 0, 400)
    chk("V3 ASU02A @(371,57) 逐像素全等", r3[0] >= 0.98,
        "全等率=%.4f (%d px), 位图 %dx%d, ELG 原点=(%d,%d)" % (r3[0], r3[1], A.shape[1], A.shape[0], rA.offset_x, rA.offset_y))

    # V4 重叠区
    H, W = 470, 800
    def sample(Ss, L, T):
        ph, pw, _ = Ss.shape
        Al = np.zeros((H, W), np.int16)
        Col = np.zeros((H, W, 3), np.int16)
        for i in range(ph):
            yy = T + i
            if yy < 0 or yy >= H:
                continue
            x0 = max(0, -L)
            x1 = min(pw, W - L)
            if x1 <= x0:
                continue
            Al[yy, L + x0:L + x1] = Ss[i, x0:x1, 3]
            Col[yy, L + x0:L + x1] = Ss[i, x0:x1, :3]
        return Al, Col
    AlM, CM = sample(M, LM, TM)
    AlA, CA = sample(A, LA, TA)
    both = (AlM > 250) & (AlA > 250)
    sh = S[:H][both]
    cM, cA = CM[both], CA[both]
    sel = np.abs(cM - cA).sum(axis=1) > 60
    s, a, b = sh[sel], cM[sel], cA[sel]
    eM = float(np.all(s == a, axis=1).mean())
    eA = float(np.all(s == b, axis=1).mean())
    chk("V4 重叠区层序: 槽1(MAS)在上", eM >= 0.90 and eA <= 0.05,
        "可判像素=%d ; 与槽1(MAS01B)全等=%.4f ; 与槽0(ASU02A)全等=%.4f ; 平均色差 %.1f vs %.1f"
        % (int(sel.sum()), eM, eA, np.abs(s - a).sum(axis=1).mean(), np.abs(s - b).sum(axis=1).mean()))

    # V5 静态表穷尽
    # `work\`（exe/DLL 只读副本）为已剔出库的可再生产物：本模块 → 旧开发位置副本（只读）→ 报 (缺)。
    # ⚠️ 旧开发位置 `子代理工作区\ISSUE-20261008-09\EXE_POS\` = **历史副本，勿用**（仅此只读兜底）。
    _work_old = r"E:\ZCode Workspace\Galgame\子代理工作区\ISSUE-20261008-09\EXE_POS\work"

    def _work(name):
        for d in (os.path.join(HERE, "work"), _work_old):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
        return os.path.join(HERE, "work", name)

    files = [("ORE_TUBA.EXE", _work("ORE_TUBA.EXE")),
             ("DS_SPRITE.DLL", _work("DS_SPRITE.DLL")),
             ("tvpgl.dll", _work("tvpgl.dll")),
             ("func_lib.sob", r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob"),
             ("user_var.sob", r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\user_var.sob")]
    G = set(GRID)
    tot = 0
    det = []
    for nm, p in files:
        if not os.path.exists(p):
            det.append(nm + "(缺)")
            continue
        d = open(p, "rb").read()
        c4 = 0
        for unit, win in ((4, 8), (2, 10)):
            n = len(d) // unit
            for i in range(0, n - win):
                vals = [struct.unpack_from("<I" if unit == 4 else "<H", d, (i + k) * unit)[0]
                        for k in range(win)]
                if sum(1 for v in vals if v in G) >= 4:
                    c4 += 1
        tot += c4
        det.append("%s:%d" % (nm, c4))
    chk("V5 无静态排布表", tot == 0, "含>=4个网格值的窗口数 合计=%d (%s)" % (tot, ", ".join(det)))

    # V6 槽循环上界 6
    import _probe_12_funclib as P12
    sob = P12.Sob(r"E:\ZCode Workspace\Galgame\工程\我们没有翅膀\解包\SCRIPT\func_lib.sob")
    i = 0x2F50 // 4
    ok6 = sob.cells[i] == 0x29 and sob.cells[i + 2] == 6      # LT i, 6
    chk("V6 func_lib 槽循环上界=6", ok6,
        "0x2F50: op=0x%02X ops=%s" % (sob.cells[i], [sob.cells[i + 1], sob.cells[i + 2]]))

    npass = sum(1 for _, st, _ in RES if st == "PASS")
    print("\n==== %d/%d PASS ====" % (npass, len(RES)))
    return 0 if npass == len(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
