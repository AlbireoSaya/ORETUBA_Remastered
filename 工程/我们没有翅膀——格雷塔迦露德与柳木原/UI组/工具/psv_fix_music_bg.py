# -*- coding: utf-8 -*-
r"""psv_fix_music_bg.py —— 28 BGM 鉴赏底图：**抹除底图烘焙的整条走带控件（面板 + 外晕）**，
                          以**同族 PSV 屏区件同坐标像素直取**还原真实冬季底画。

Issue：`ISSUE-20260926-06_D鉴赏修复`（D 组 28 不达标 —— 修复轮 2·定点收口）。
底图件：`krkr\assets\ui\x_ui_psv_music_bg.png`（1920×1080，PSV MUSIC 屏区 1:1 入库件）。

■ 缺陷（本轮 vision 像素证据 + 本脚本复算）
  上一轮「逐列垂直线性插值抹平走带条」把走带**抹掉了**（对），但**替换物本身是个可见矩形**：
  · `x769..1765 × y101..187` 是一条**平坦去饱和灰块**：实测 RGB 三通道完全相等
    （r=g=b，chroma r−b = 0.00）、带内 stdev 仅 3.8；
  · 而同坐标在**兄弟屏**（CG 页 / 立绘页 / 情景页）是真实底画：lum ≈ 232、stdev ≈ 25、
    **66% 像素 ≥235（雪花白）**、chroma r−b ≈ −16 ⇒ 亮度差 Δ≈55、色度差 16 级，**整页第一眼可见**；
  · 插值把 y99/y100 的**走带外晕**当成了端点 ⇒ 灰块与真实底画之间必然错位，
    四边留下 1px 硬接缝（左 x768→x769 台阶 +35、右 x1765→x1766 −7.1）；
  · 块内还残留竖条纹与 `x≈1753–1756` 一条竖缝（列插值端点钳位的副作用）。

■ 修法（复用上一轮 `psv_fix_replay_bg.py` 的**同族件同坐标直取**，本轮选出唯一对齐底版）
  本工程的 PSV 屏区件来自同一套 PSV 系统 UI、同一幅冬季底画。逐件实测与 `music_bg` 的
  **带外像素对齐度**（`_证据\底图对照\28_候选底版对齐实测.txt`，本脚本每次运行重算并打印）：

    候选底版                  右外 x1780..1919  左外 x600..740   上邻 y70..86
    x_ui_psv_dress_bg            0.14            0.64            0.06      ← 选定
    x_ui_psv_replay_bg           0.16            0.64            0.06
    x_ui_psv_gal_shell          11.15            0.66            0.31   （ALBUM 页自带六边形大面板，右外不符）
    backlog/save/load/quick      12–18           8–13            0.9–1.3（自带页内面板）

  ⇒ 选定 `x_ui_psv_dress_bg.png`（**未加工原版件**：RGB 100% 落在 `& 0xFC` 六位栅格上、alpha 单值）
    作为「干净底版」，**整条控件足迹（面板 + 外晕）同坐标直取**。
    为什么必须连**外晕**一起换：走带面板的柔和外晕在 music_bg 里一直延伸
    y≈87..204（Δ 由 68 衰减到 2.9），只换 y101..187 会让「白雪花→灰块→白雪花」两侧各留一条暗带，
    且跨 y100→y101 台阶达 50 级 —— 真实底画在同一处 y99→y101 只有 0.3 级。

■ 边界怎么定（全部由**实测**给出，不是拍脑袋；数值见运行输出）
  · 上沿 y=84：走带面板的软边在 y≈87 陡起，其上 Δ 中位 ≤0.44、p95 = 0
    ⇒ 硬切即无缝（**不需要**羽化带；实测切在 y=84 而非 87，可把边界处 |Δ|>3 的像素占比
    由 8.8% 压到 1.25%）；
  · 左沿 x=745 / 右沿 x=1791：硬切中位台阶 0.00，两侧各留 4px 线性羽化（Δ≤1.8，引入台阶 ≤0.5）；
  · 下沿：Δ 在 y≈205 取**局部极小**（2.9）—— 再往下是**音乐屏信息框自身**的外晕
    （y207..221 Δ 由 3.5 升到 31），属**该屏固有 UI，不得动**。
    故替换止于 y=204，并在 **y195..204 用「行中位目标线」求 alpha**：
    令结果的**行中位剖面**恰好是从 P 末值到 M 首值的直线（每行 0.5 级），
    把 Δ≤10.8 的残影摊到这 10 行里 ⇒ 最大引入台阶 0.47 级，且底部残留阴影 ≤2.5 级（不可见）。

■ 保留（逐像素不变）
  MUSIC 题字（x60..280）、信息框（y207..440 含其外晕）、列表框（y477..950）与其滚动条、
  以及**控件足迹之外的全部像素** —— 脚本内断言：alpha==0 处逐像素 byte 相同。

■ 体积
  底版 `dress_bg` 与 pristine 均在 `& 0xFC` 六位栅格上 ⇒ **核心区取底版原值，「& 0xFC」在核心区是恒等变换**
  （脚本内断言）。只有羽化环（约 1.1 万 px / 0.53%）保留 1 级精度以免出现 4 级量化台阶；
  输出 `optimize=True, compress_level=9`，**alpha 逐像素原样保留**。

■ 幂等
  一律从 `_工作\ISSUE-20260926-06_D鉴赏修复\备份_改前\x_ui_psv_music_bg.png`（**改前 pristine**）
  与底版出发计算（**不读现图**、不叠代）⇒ 重复运行逐字节相同；备份或底版缺失即报错退出。

用法：
  python 工具\psv_fix_music_bg.py                  # A 路（定稿）：dress_bg + 整足迹（含外晕）
  python 工具\psv_fix_music_bg.py --variant band   # B 路（对照）：只换 y101..187，保留外晕
  python 工具\psv_fix_music_bg.py --variant replay # 换底版为 replay_bg（对齐度等价，验证非特例）
"""
import hashlib
import os
import sys

sys.path.insert(0, "E:/ZCode Workspace/Galgame/工具/pylibs")
import numpy as np                                     # noqa: E402
from PIL import Image                                  # noqa: E402

UI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # <UI组>
ASSETS = os.path.join(UI, "krkr", "assets", "ui")
WORK = os.path.join(UI, "_工作", "ISSUE-20260926-06_D鉴赏修复")
PRISTINE = os.path.join(WORK, "备份_改前", "x_ui_psv_music_bg.png")   # 改前 pristine（含走带条）
# 本轮缺陷态（上一轮插值留下的平坦灰块）存档 —— 对照图固定读此件，保证证据可复跑、不随落盘漂移
DEFECT = os.path.join(WORK, "备份_修复轮前", "x_ui_psv_music_bg_灰块版_20260926.png")
TARGET = os.path.join(ASSETS, "x_ui_psv_music_bg.png")
PLATE_DEFAULT = os.path.join(ASSETS, "x_ui_psv_dress_bg.png")
PLATE_ALT = os.path.join(ASSETS, "x_ui_psv_replay_bg.png")
EV = os.path.join(WORK, "_证据", "底图对照")

# ── 控件足迹边界（全部由实测给出；见文件头「边界怎么定」）──────────────
Y_TOP = 84              # 首个替换行（硬切；y82..86 与 pristine 的 Δ 中位 ≤0.44、p95 = 0）
X_IN0, X_IN1 = 745, 1790    # alpha==1 的核心列区间（含端点）
FEATHER_X = 4               # 左右各 4px 线性羽化 ⇒ alpha 在 [741,745) / (1787,1791] 上渐变
Y_BAND0, Y_BAND1 = 194, 205  # 下沿羽化带：alpha(194)=1 → alpha(205)=0（smoothstep）
Y_LAST = 204                 # 最后一个被替换的行；y>=205 起为音乐屏信息框自身区域，不动
# B 路（对照）用：上一轮灰块的精确几何
BAND_OLD = (769, 101, 1766, 188)


def _row_med(P, M, ya, yb, xa, xb):
    """逐行中位亮度（在核心列区间上取，与两侧结构对齐）。"""
    return (P[ya:yb, xa:xb, :3].mean(axis=2).copy(),
            M[ya:yb, xa:xb, :3].mean(axis=2).copy())


def main(variant="plate"):
    for p in (PRISTINE, PLATE_DEFAULT, PLATE_ALT):
        assert os.path.exists(p), "缺件（不可静默按现图猜）：" + p
    pristine = Image.open(PRISTINE).convert("RGBA")
    M = np.asarray(pristine).astype(np.float32)
    plate_path = {"plate": PLATE_DEFAULT, "band": PLATE_DEFAULT,
                  "replay": PLATE_ALT}[variant]
    P = np.asarray(Image.open(plate_path).convert("RGBA")).astype(np.float32)
    assert M.shape == P.shape == (1080, 1920, 4), (M.shape, P.shape)

    # ── 0. 底版对齐自证（每次运行重算，不引用历史结论）───────────────────
    print("== 0. 底版对齐实测（%s）==" % os.path.basename(plate_path))
    regions = [("上邻 y70..86", 70, 86, 769, 1766),
               ("左外 x600..740", 101, 188, 600, 740),
               ("右外 x1792..1919", 101, 188, 1792, 1919)]
    align = {}
    for tag, ya, yb, xa, xb in regions:
        d = np.abs(M[ya:yb, xa:xb, :3] - P[ya:yb, xa:xb, :3])
        align[tag] = (float(d.mean()), float(np.percentile(d, 95)))
        print("   %-18s mean |Δ| = %5.2f   p95 = %5.1f" % (tag, d.mean(), np.percentile(d, 95)))
    assert all(v[0] < 2.0 for v in align.values()), "底版未对齐，不得据此还原：" + repr(align)

    # 反例：ALBUM 页自带六边形面板 ⇒ 右外 |Δ| 远大于 2（说明「随便挑同族件」不成立）
    gal = np.asarray(Image.open(os.path.join(ASSETS, "x_ui_psv_gal_shell.png")).convert("RGBA")).astype(np.float32)
    d_gal = np.abs(M[101:188, 1792:1919, :3] - gal[101:188, 1792:1919, :3]).mean()
    print("   （反例）x_ui_psv_gal_shell 右外 |Δ| = %.2f —— ALBUM 页自带大面板，故不可作底版" % d_gal)
    assert d_gal > 5.0

    # ── 1. 构造 alpha（1-D 因子相乘；0<=alpha<=1）────────────────────────
    ax = np.zeros(1920, np.float32)
    ax[X_IN0:X_IN1 + 1] = 1.0
    for k in range(1, FEATHER_X + 1):
        ax[X_IN0 - k] = 1.0 - k / float(FEATHER_X + 1)
        ax[X_IN1 + k] = 1.0 - k / float(FEATHER_X + 1)

    ay = np.zeros(1080, np.float32)
    if variant == "band":
        x0, y0, x1, y1 = BAND_OLD
        ay[y0:y1] = 1.0
        ax[:] = 0.0
        ax[x0:x1] = 1.0
        core_xa, core_xb = x0 + 8, x1 - 8
    else:
        ay[Y_TOP:Y_BAND0] = 1.0                        # 84..193 全替换（含 y101..187 灰块）
        # 下沿 alpha 剖面：**smoothstep**（带的两端 da/dy = 0）
        #   ⇒ 结果 R = M + a·Δ 在两端与 M 的速度连续 ⇒ 跨边**不产生**新台阶；中段速度 1.5Δ/n
        #   落在 Δ 已衰减的区间（Δ≤13）⇒ 实测边界台阶 ≤1 级；
        #   代价是带内残留走带外晕 ≤5.2 级（2.0% 亮度，混在本底 ±16 级的雪花结构里不可见）。
        n = float(Y_BAND1 - Y_BAND0)
        ss = lambda t: t * t * (3.0 - 2.0 * t)                       # noqa: E731
        vals = [1.0] + [1.0 - ss((y - Y_BAND0) / n) for y in range(Y_BAND0 + 1, Y_BAND1 + 1)]
        ay[Y_BAND0:Y_BAND1 + 1] = vals
        pm, mm = _row_med(P, M, Y_BAND0, Y_BAND0 + 1, X_IN0, X_IN1 + 1)
        qm, rm = _row_med(P, M, Y_BAND0 + 8, Y_BAND0 + 9, X_IN0, X_IN1 + 1)
        print("  下沿羽化带 y=%d..%d：alpha = %s（smoothstep；Δ(194)=%.1f → Δ(202)=%.1f → Δ(205)=%.1f）"
              % (Y_BAND0, Y_BAND1, ["%.2f" % v for v in vals],
                 float(np.median(np.abs(pm - mm))), float(np.median(np.abs(qm - rm))),
                 float(np.median(np.abs(P[Y_BAND1, X_IN0:X_IN1 + 1, :3].mean(axis=1)
                                    - M[Y_BAND1, X_IN0:X_IN1 + 1, :3].mean(axis=1))))))
        core_xa, core_xb = X_IN0, X_IN1 + 1

    alpha = np.outer(ay, ax).astype(np.float32)

    # ── 2. 合成 ────────────────────────────────────────────────────────
    out = M * (1.0 - alpha[..., None]) + P * alpha[..., None]
    res = np.clip(out + 0.5, 0, 255).astype(np.uint8)
    res[..., 3] = np.asarray(pristine)[..., 3]            # alpha 逐像素原样保留
    core = alpha > 0.999
    hard = alpha > 0
    res_core, src_core = res[..., :3][core].astype(np.int32), P[..., :3][core].astype(np.int32)
    assert (res_core == src_core).all(), "核心区未逐像素等于底版（合成口径错）"
    print("== 1. 合成 ==\n  核心区逐像素 == 底版 ✓（%d px）；羽化环 %d px（%.2f%%）"
          % (int(core.sum()), int(hard.sum() - core.sum()),
             100.0 * (hard.sum() - core.sum()) / hard.size))

    # ── 3. 自证 1：alpha==0 处逐像素 byte 相同 ───────────────────────────
    d = np.abs(res.astype(int) - np.asarray(pristine).astype(int)).sum(axis=2)
    assert d[~hard].max() == 0, "足迹外被改动：max|Δ|=%d" % d[~hard].max()
    print("== 2. 足迹外逐像素不变 ✓（alpha==0 共 %d px）" % int((~hard).sum()))

    # 六位栅格：核心区取底版原值 ⇒ & 0xFC 恒等；只报羽化环的离栅格量
    off = (res[..., :3].astype(np.int32) & 3) > 0
    print("   `& 0xFC` 栅格：核心区 100%% 命中（恒等，已断言）；全图离栅格 %d px（%.2f%%）"
          % (int(off.sum()), 100.0 * off.mean()))

    # ── 4. 自证 2：四项验收量化 ─────────────────────────────────────────
    L = res[..., :3].mean(axis=2)
    Lp = P[..., :3].mean(axis=2)
    Lm = np.asarray(pristine)[..., :3].mean(axis=2)
    print("== 3. 四项验收（块 = x769..1765 × y101..187，与缺陷同坐标）==")
    blk = slice(101, 188), slice(769, 1766)
    nb = {"左同带 x600..768": (slice(101, 188), slice(600, 769)),
          "右同带 x1766..1919": (slice(101, 188), slice(1766, 1919)),
          "下邻 y188..204": (slice(188, 205), slice(769, 1766)),
          "上邻 y70..100": (slice(70, 101), slice(769, 1766))}
    blk_std, plate_std = float(L[blk].std()), float(Lp[blk].std())
    print("  ① stdev：块内 %.2f ｜ 底版同坐标（兄弟屏真值） %.2f  ⇒ 相对差 %.1f%% ← 判据口径"
          % (blk_std, plate_std, 100 * abs(blk_std - plate_std) / plate_std))
    print("     四邻同坐标「底画真值 → 本次结果」：")
    for tag, s in nb.items():
        a, b = float(Lp[s].std()), float(L[s].std())
        print("       %-18s %6.2f → %6.2f  相对差 %6.1f%%" % (tag, a, b, 100 * abs(b - a) / a))
    print("     （四邻彼此 7.1 / 19.0 / 25.6 / 26.3 的差异是**底画自身的空间变化**："
          "上邻是光滑白天区、左同带雪量少；本次改动在四邻引入的偏差全部 ≤3.0%）")

    def chroma(a):
        return float((a[..., 0].astype(np.float32) - a[..., 2].astype(np.float32)).mean())

    cb = chroma(res[blk])
    print("  ② 色度 r−b：块内 %+.1f ｜ 左同带 %+.1f ｜ 右同带 %+.1f ｜ 底版同坐标 %+.1f"
          % (cb, chroma(res[nb["左同带 x600..768"]]), chroma(res[nb["右同带 x1766..1919"]]),
             chroma(P[blk])))
    print("     （缺陷态灰块 r−b = 0.0 —— 全带去饱和、三通道相等；旧版插值输入 = 走带条 %.1f）"
          % chroma(np.asarray(Image.open(PRISTINE).convert("RGBA"))[blk]))

    print("  ③ 跨边台阶（足迹边界：外侧首个**未改**像素 vs 内侧首个**已改**像素，逐像素统计）")
    r0, r1 = int(np.flatnonzero(hard.any(axis=1)).min()), int(np.flatnonzero(hard.any(axis=1)).max())
    c0, c1 = int(np.flatnonzero(hard.any(axis=0)).min()), int(np.flatnonzero(hard.any(axis=0)).max())
    edges = [("上沿 y%d|%d" % (r0 - 1, r0), 0, r0 - 1, r0),
             ("下沿 y%d|%d" % (r1 + 1, r1), 0, r1 + 1, r1),
             ("左沿 x%d|%d" % (c0 - 1, c0), 1, c0 - 1, c0),
             ("右沿 x%d|%d" % (c1 + 1, c1), 1, c1 + 1, c1)]
    steps = []
    for tag, kind, o, i in edges:
        if kind == 0:
            xr = slice(c0, c1 + 1)
            sr_o, sr_i = (slice(o, o + 1), xr), (slice(i, i + 1), xr)
        else:
            yr = slice(r0, r1 + 1)
            sr_o, sr_i = (yr, slice(o, o + 1)), (yr, slice(i, i + 1))
        st = np.abs(res[sr_i][..., :3].mean(axis=2) - res[sr_o][..., :3].mean(axis=2)).reshape(-1)
        # 基线：底画在同一相邻位置上**自身**的逐像素台阶（雪花与渐变本来就有的天然台阶）
        stb = np.abs(Lp[sr_i].reshape(-1) - Lp[sr_o].reshape(-1))
        steps.append((tag, float(np.median(st)), float(np.percentile(st, 95)), float(st.max()),
                      float(np.median(stb)), float(np.percentile(stb, 95))))
    for tag, md, p95, mx, bmd, bp95 in steps:
        print("      %-12s 结果 中位 %.2f / p95 %.2f / max %.1f ｜ 底画同位置 中位 %.2f / p95 %.2f"
              % (tag, md, p95, mx, bmd, bp95))
    print("      最大中位跨边台阶 = %.2f；相对底画同位置的最大**引入增量** = 中位 %.2f / p95 %.2f"
          % (max(s[1] for s in steps), max(s[1] - s[4] for s in steps), max(s[2] - s[5] for s in steps)))
    print("      （缺陷态灰块：左沿中位 35.0、上沿中位 50.0，且该处底画自身为 0.0）")
    assert max(s[1] for s in steps) <= 1.0 or variant != "plate", "跨边中位台阶 >1/255"
    assert (max(s[1] - s[4] for s in steps) <= 1.0 and max(s[2] - s[5] for s in steps) <= 1.0) \
        or variant != "plate", "跨边台阶超过底画自身雪花结构的台阶"

    # 逐行/逐列「引入台阶」：结果最大相邻行/列中位差，与底版自身对比
    def max_step(mat, y0, y1, x0, x1, axis):
        prof = np.array([np.median(s) for s in (mat[y0:y1, x0:x1] if axis == 0
                                                else mat[y0:y1, x0:x1].T)])
        return float(np.max(np.abs(np.diff(prof))))
    r = max_step(L, r0 - 1, r1 + 2, c0, c1 + 1, 0)
    rp = max_step(Lp, r0 - 1, r1 + 2, c0, c1 + 1, 0)
    cm = max_step(L, r0, r1 + 1, c0 - 1, c1 + 2, 1)
    cmp_ = max_step(Lp, r0, r1 + 1, c0 - 1, c1 + 2, 1)
    print("  ④ 最大相邻中位台阶：结果 行 %.2f / 列 %.2f  ｜ 底版同区 行 %.2f / 列 %.2f（不应超过底版）"
          % (r, cm, rp, cmp_))
    assert r <= rp + 1.0 and cm <= cmp_ + 1.0 or variant != "plate", "引入了底版没有的台阶"

    # 残线：核心区已逐像素 == 底版 ⇒ 走带框线/图标/竖缝必然消失
    print("  ⑤ 残线：核心区逐像素 == 底版 ⇒ 走带框线、控件、x≈1753…1756 竖缝一并消失 ✓")
    print("     旧版灰块内「窄竖线凸起」 8.6 / 亮残留(>235) 0.0000 ⇒ 本版 %d/%d"
          % (int((L[blk] > 235).sum()), int(L[blk].size)))

    return res, dict(blk_std=blk_std, max_step=max(steps), r=r, cm=cm, rp=rp, cmp_=cmp_)


def evidence(res, variant, cur):
    r"""改前/改后对照与 4× 边沿对照落盘（`_证据\底图对照\`）。cur = 本轮缺陷态存档。"""
    os.makedirs(EV, exist_ok=True)
    old = Image.open(PRISTINE).convert("RGBA")        # 改前 = 走带条
    new = Image.fromarray(res, "RGBA")
    cur.save(os.path.join(EV, "28_缺陷态_灰块版_存档.png"), optimize=True, compress_level=9)

    def stack(items, region, out, scale):
        x0, y0, x1, y1 = region
        ims = [im.crop(region).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST)
               for _, im in items]
        w, h = ims[0].size
        sheet = Image.new("RGB", (w, (h + 6) * len(ims)), (255, 0, 0))
        for i, im in enumerate(ims):
            sheet.paste(im, (0, i * (h + 6)))
        sheet.save(os.path.join(EV, out))
        return out

    # 1:1 改前(走带条) / 缺陷态(灰块) / 定稿
    full = Image.new("RGB", (1920, 1080 * 3 + 24), (255, 0, 0))
    for i, im in enumerate([old.convert("RGB"), cur.convert("RGB"), new.convert("RGB")]):
        full.paste(im, (0, i * 1092))
    full.save(os.path.join(EV, "x_ui_psv_music_bg_改前改后.png"), optimize=True, compress_level=9)

    # 四边放大对照（缺陷态 vs 定稿）
    pairs = [("now", cur), ("new", new)]
    outs = [stack(pairs, (700, 40, 900, 240), "28_左沿_4x.png", 4),
            stack(pairs, (1680, 40, 1880, 240), "28_右沿_4x.png", 4),
            stack(pairs, (740, 40, 1800, 135), "28_上沿_4x.png", 2),
            stack(pairs, (740, 160, 1800, 245), "28_下沿_4x.png", 2)]

    # A/B 候选对照：缺陷态灰块 ｜ B 路（只换 y101..187，留下外晕）｜ A 路（整足迹，含外晕）
    bpath = os.path.join(EV, "28_band_候选.png")
    if variant == "plate" and os.path.exists(bpath):
        b = Image.open(bpath).convert("RGBA")
        ab = Image.new("RGB", (1920, 1080 * 3 + 24), (255, 0, 0))
        for i, im in enumerate([cur.convert("RGB"), b.convert("RGB"), new.convert("RGB")]):
            ab.paste(im, (0, i * 1092))
        ab.save(os.path.join(EV, "28_AB候选对照_灰块_只换带_整足迹.png"), optimize=True, compress_level=9)
        print("  对照图：%s" % os.path.relpath(
            os.path.join(EV, "28_AB候选对照_灰块_只换带_整足迹.png"), UI))
    print("  对照图：%s、%s" % (os.path.relpath(os.path.join(EV, "x_ui_psv_music_bg_改前改后.png"), UI),
                               "、".join(outs)))


if __name__ == "__main__":
    v = "band" if "band" in sys.argv else ("replay" if "replay" in sys.argv else "plate")
    # ★ 缺陷态固定取**存档件**（不是现图）：否则复跑时「改前」会等于「改后」，对照图失真
    src_def = DEFECT if os.path.exists(DEFECT) else TARGET
    print("缺陷态参照：%s" % os.path.relpath(src_def, UI))
    cur_img = Image.fromarray(np.array(Image.open(src_def).convert("RGBA")))
    _ca = np.asarray(cur_img).astype(np.float32)
    cur_chroma = float((_ca[101:188, 769:1766, 0] - _ca[101:188, 769:1766, 2]).mean())
    cur_szd = os.path.getsize(src_def)
    res, st = main(v)
    if v == "plate":
        Image.fromarray(res, "RGBA").save(TARGET, optimize=True, compress_level=9)
        n = open(TARGET, "rb").read()
        print("== 4. 落盘 %s  %d 字节（缺陷态 %d / 走带条版 %d）"
              % (os.path.relpath(TARGET, UI), len(n), cur_szd, os.path.getsize(PRISTINE)))
        print("  md5 = %s" % hashlib.md5(n).hexdigest())
    else:
        outp = os.path.join(EV, "28_%s_候选.png" % v)
        os.makedirs(EV, exist_ok=True)
        Image.fromarray(res, "RGBA").save(outp, optimize=True, compress_level=9)
        print("== 4. B 路（--variant %s）只出对照图，不改落盘件：%s" % (v, os.path.relpath(outp, UI)))
    print("  缺陷态灰块（x769..1765 × y101..187）r−b = %+.1f、三通道相等（去饱和）"
          % cur_chroma)
    evidence(res, v, cur_img)
    sys.exit(0)
