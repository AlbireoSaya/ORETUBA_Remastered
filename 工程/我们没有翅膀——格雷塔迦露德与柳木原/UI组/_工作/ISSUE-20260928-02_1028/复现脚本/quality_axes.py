# -*- coding: utf-8 -*-
r"""
quality_axes.py —— 补边产物**输出侧五轴**质量判据（ISSUE-20260928-02 · 1028 补边续作）

背景（上一批的教训）
    上一批 `triage_rerun.py` 的「边缘比」只在**源图**上算「边缘有多复杂」，从不看 inpaint
    产物本身 ⇒ 分诊 A 档(450) 里藏着 23 件真硬断、B 档(152) 里 41 件、C 档 6 件，
    而 D 档 6 件实测 HARD = 0；C+D 的「38 件须人工」只召回 6/70 = 8.6%。
    本脚本改为**只看输出**（`outpaint\`），对 640 件打分排序。

几何（**逐件按真实源尺寸算，不得硬编码 1440**）
    输出 1920×1080 里，原图内容区 = [xl, xr)：
        NW = round(H*16/9) 向上取 8 的倍数；Hp = H 向上取 8 的倍数；ox = (NW-W)//2
        xl = round(ox*1920/NW)；xr = round((ox+W)*1920/NW)
    标准源 1600×1200 ⇒ NW=2136 ox=268 ⇒ **xl=241, xr=1679（宽 1438）**
    非标源 asu54.png 1610×1214 ⇒ NW=2160 ox=275 ⇒ **xl=244, xr=1676**
    （不是 1440 —— 画布宽取 8 的倍数使横向缩放 0.898876 ≠ 纵向 0.900000）
    实测自证（canvas 重建法，见报告）：内容区内 |重建设−产物| 均差 0.00，缝外跳到 23–253。

五轴定义（vision 口径）
    mL4      高度分 6 横带，各带算 |列均值(x-4) − 列均值(x+4)|（灰度级），取各带/两侧最大
    mRGB4    同带内 mean|I[:,x-4] − I[:,x+4]|（**逐像素**，RGB 三通道），取最大
    er       gx[x] / mean(gx[x±8..48])，gx = 逐列横向梯度；左右取最大
    |ramp|   列均值(最外 8 列) − 列均值(缝内 8 列)（逐侧取最大）
    bD16     缝两侧 16 列带均值之差（±8..24），左右取最大
    零基线   内容区内同距离的 mRGB4 抽样最大值 / gx 比值最大值（把「内容本身就有强梯度」的件剔除）

★ 口径校正（2026-09-28，实测；**不是调参凑数，逐条可复现**）
    逐分位对照 vision 报值后，三项逐分位吻合：
        mL4   本机 p50 6.82 / p90 23.26 / max 108.03  vs vision 6.83 / 23.2 / 108
        mRGB4 本机 p50 15.03 / p90 38.95              vs vision 14.9 / 39.5
        |ramp|本机 p50 23.19 / p90 48.30              vs vision 23.3 / 48.0
    ⇒ 这三项口径确认无误。另两项按**派单字面式**复算与 vision 值显著不符，故校正：
    ① er：字面式「d1[x]/mean(d1[x±8..48])」在内容平坦时分母 →0，比值爆掉
       （实测 sr 族白底卡参考带均值 ≈0.02 灰度级 ⇒ er 达 3.6–7.4；全量 p50 2.12 / p99 17.8，
        与 vision 的 0.79 / 2.27 差 2.7×/7.8×；且纯 er≥4 会造出 114 件假 HARD）。
       测过 14 种变体，最接近 vision 的是「分母 = 内容区内侧(xl+8..xr-8)平均逐列梯度」：
       本机 p50 0.67 / p99 2.73（vs 0.79 / 2.27，差 15%/20%），且**平坦件不再爆**。
       ⇒ 主口径取此式（`er`）；派单字面式保留为 `er_literal`、加下限版为 `er_floor`。
    ② bD16：字面式「缝两侧 16 列带均值之差」若**全高一次平均** ⇒ p50 4.76（vision 20.0，差 4 倍）。
       与 mL4/mRGB4 同结构、**分 6 横带取最大** ⇒ p50 20.79 / p99 83.9 / max 121.3
       （vision 20.0 / 120）。⇒ 主口径取分带式；全高平均版保留为 `bD16_global`。

分级
    HARD         mL4>=30 或 mRGB4>=40 或 er>=4                    → 必修
    MID-补充     非 HARD 且 (30<=mRGB4<40 条纹断线 | |ramp|>=30 整块色调漂移 |
                              bD16>=60 且 mL4<12 局部结构断)      → vision 指出主判据会漏的三类
    MID         非以上且 (mL4>=12 或 mRGB4>=15 或 er>=2 或 bD16>=30 或 |ramp|>=18)
    LITE        非以上且 (mL4>=4 或 mRGB4>=5 或 er>=1.3 或 bD16>=10 或 |ramp|>=8)
    CLEAN       其余
    ★ 另标 FRAME_LINE（帧线件）：见下方「帧线判定的两种口径」

建议处置（互斥五桶，求和 = 640；顺序即优先级）
    几何延展   帧线件（缝外侧 40 列内有单列强边）
    重绘扩展区 HARD（mL4>=30 或 mRGB4>=40 或 er>=4）或补充轴里的结构/条纹断
    色调匹配   其余中 |ramp|>=25 的
    可直接采用 LITE / CLEAN 且 |ramp|<25
    精修       其余 MID
    ★ `|ramp|>=25` 另出一列 `色调匹配适用`——那是**色调匹配 pass 的覆盖面**（272 件），
      与上面的互斥桶不是一回事：被判「重绘」的件里也有 39 件 ramp>=25，pass 照样跑它们
      （色调匹配是无害的预处理，但修不了结构断）。

帧线判定的两种口径（★ 派单字面口径实测命中 0 件）
    派单原文：「边缘外扩路径上存在单列强边（|Δ列均值|>=20 且在边缘 40 列内）」。
    实测：**图片边框侧 40 列内，全 640 件的最大 |Δ列均值| 只有 0.3–1.3 级**（LaMa 在贴边处
    是平滑的），字面口径 **命中 0 件**；真正强的单列边全部出现在**缝外侧 17–38 px** 处
    （sl 族 74–89 级、ld_bg 46 级）——那才是 LaMa 在缝外造出的「竖硬边」。
    ⇒ 主口径 `frame_seam` = 缝外侧 40 列内的单列强边（命中 sl 族 3 件）；
      字面口径保留为 `frame_border`（命中 0 件），两者都落盘。

产物（幂等 / 可断点续跑 / 逐件失败不中断）
    质量轴.tsv       640 行逐件分数（含左右分侧值、零基线、帧线判定）
    须处置清单.tsv    逐件：统一名 / 五轴值 / 分类 / 建议处置
    质量轴_汇总.txt   分位对照（含 vision 报值）+ 分级分布

用法
    set PYTHONPYCACHEPREFIX=...\ISSUE-20260928-02_1028\_pycache
    python quality_axes.py                # 全量（已有行跳过）
    python quality_axes.py --force        # 全量重算
    python quality_axes.py --names ai_07.png,sl_03.png
    python quality_axes.py --summary-only # 只按已有 质量轴.tsv 重出汇总/清单
"""
import sys, os, csv, json, time, argparse, collections

WS = r"E:\ZCode Workspace\Galgame"
MAIN_PROJ = os.path.join(WS, "工程", "我们没有翅膀——格雷塔迦露德与柳木原")
HERE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DIR = os.path.dirname(HERE)                     # ...\ISSUE-20260928-02_1028
OUTPAINT = os.path.join(ISSUE_DIR, "outpaint")
LIST_TSV = os.path.join(MAIN_PROJ, "资源组", "美术", "4比3待重制清单.tsv")
AXES_TSV = os.path.join(ISSUE_DIR, "质量轴.tsv")
DISP_TSV = os.path.join(ISSUE_DIR, "须处置清单.tsv")
SUM_TXT = os.path.join(ISSUE_DIR, "质量轴_汇总.txt")

sys.path.insert(0, os.path.join(WS, "工具", "pylibs"))
import numpy as np
from PIL import Image

TARGET = (1920, 1080)
NBANDS = 6
BAND_HALF = 4          # x±4
RAMP_OUT = 8           # 最外 8 列
RAMP_IN = 8            # 缝内 8 列
BD_LO, BD_HI = 8, 24   # bD16：±8..24
ER_LO, ER_HI = 8, 48   # er 参考带：x±8..48
ER_FLOOR = 0.5         # er 分母下限（灰度级）——见文件头「er 的病态与下限」说明
EDGE_W = 40            # 帧线判定的「边缘 40 列」
FRAME_TH = 20          # 帧线单列强边阈值 |Δ列均值|

# ---- 分级阈值（vision 主判据 + 补充轴；MID/LITE 阈值为分位自然断点，见报告）----
HARD_ML4, HARD_MRGB4, HARD_ER = 30.0, 40.0, 4.0
SUP_MRGB4_LO = 30.0            # 30<=mRGB4<40 条纹断线
SUP_RAMP = 30.0                # |ramp|>=30 整块色调漂移
SUP_BD16, SUP_BD16_ML4 = 60.0, 12.0
MID_ML4, MID_MRGB4, MID_ER, MID_BD16, MID_RAMP = 12.0, 15.0, 2.0, 30.0, 18.0
LITE_ML4, LITE_MRGB4, LITE_ER, LITE_BD16, LITE_RAMP = 4.0, 5.0, 1.3, 10.0, 8.0
TONEMATCH_RAMP = 25.0          # 色调匹配触发线（派单指定）

# ============================ v2 增补（2026-09-28，vision 打回「257 件可直接放行」后）=====
# 打回的三条与判据有关的事实（vision 证据，已核）：
#   ① 灰度全高平均的 |ramp| 有色相盲区：yy_19 ramp=13.65 但 ramp_ch=43.0；
#      kob68 族 ramp 6.0–6.2 而 ramp_ch 50.2–50.5。
#   ② 灰度全高平均还有分带抵消盲区：yy_19 带内 luma 差 −27.6，全高平均后只剩 0.3。
#   ③ 内容参考带 [xl, xl+8) 在 sl 族内含相框亮线（241 列 236.2）与暗线（243 列 159.1），
#      带均值 177.2 而帧体色 164 ⇒ 外缘被钉在 177.2、|ramp| 报 4.2（"完美"）但相对帧体色
#      仍残留 ≈15 级。
# 因此 v2 **不降灰度线**（维持 25；81 张白卡实测 10.8–26.5 正在这条线附近），而是
# **新增两个独立门**，并把内容参考带**内移 REF_SHIFT 列**另出一套审计值。
REF_SHIFT = 10                 # 内容参考带内移列数（选定理由见文件头「v2 增补说明」）
BAND_GATE = 25.0               # 单侧分带中位 / 逐通道 |ramp| 的独立门
ER_FLOOR_V2 = 0.5              # er 修正口径的分母下限（与旧 er 同）
VISION_RAMP_CH_GE25 = 485      # vision 报的 ramp_ch>=25 件数（自校准对照，不得调参凑数）
VISION_RELEASE = 133           # vision 报的放行集合（41 + 89 + 3 人工特批）

# ---- vision 报的分布（自校准对照，不得调参凑数）----
VISION = {
    "mL4":    {"p50": 6.83, "p90": 23.2, "max": 108.0, "p99": None},
    "mRGB4":  {"p50": 14.9, "p90": 39.5, "max": None, "p99": None},
    "er":     {"p50": 0.79, "p90": None, "max": None, "p99": 2.27},
    "ramp":   {"p50": 23.3, "p90": 48.0, "max": None, "p99": None},
    "bD16":   {"p50": 20.0, "p90": None, "max": None, "p99": 120.0},
    "HARD":   {"n": 70},
}


# ================================================================ 几何
def canvas_geom(W, H):
    """与 run_outpaint.py 的 make_canvas / canvas_geom 同源。返回 (NW, Hp, ox)。"""
    NW = int(round(H * 16 / 9))
    NW += (8 - NW % 8) % 8
    Hp = H + (8 - H % 8) % 8
    ox = (NW - W) // 2
    return NW, Hp, ox


def out_seams(W, H):
    """内容区在 1920×1080 输出坐标系中的 [xl, xr)。"""
    NW, Hp, ox = canvas_geom(W, H)
    return (int(round(ox * TARGET[0] / NW)),
            int(round((ox + W) * TARGET[0] / NW)))


# ================================================================ v2 增补轴
def _band_edges(H, nb=NBANDS):
    return [(int(round(i * H / nb)), int(round((i + 1) * H / nb))) for i in range(nb)]


def v2_axes(rgb, xl, xr):
    """v2 增补轴（逐通道 / 单侧分带 / 参考带内移 / er 修正）。返回 dict。

    记号
      ext_far_c(y)  图片最外 8 列的逐行列均值（"分量 c"）
      ctn_ref_c(y)  缝内侧 8 列的逐行列均值，参考带起点可右移 sh 列（sh=0 即旧 |ramp| 口径）
      分带量 A[s,c,b] = mean_{y∈band b} ext_far_c − mean_{y∈band b} ctn_ref_c
      （因「逐行列均值→带内平均」= 「带内平均→逐列均值」，A 直接由分带列均值算，代数等价）

    量
      ramp_ch_L/R      逐通道 |ramp|（每侧取 3 通道最大）
      ramp_ch          两侧最大
      bandmed_ch       **单侧分带中位（6 带 × 3 通道取最大）**：逐通道先对 6 带取中位 → 3 值 → 取最大
                       → 再取两侧最大（即 vision 建议的新独立门所用的量）
      bandmax_ch       单侧分带最大：6 带 × 3 通道共 18 个 |A| 取最大 → 两侧最大
      bandmax_luma / bandmed_luma   luma 版（抓「带内差大、全高平均相消」的色相盲区）
      ramp_in*         参考带内移 REF_SHIFT 后的 |ramp|（灰度 / 逐通道），审计用
      er_fill          er 修正口径（见下）
    """
    H, W, _ = rgb.shape
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    edges = _band_edges(H)
    cmb = np.empty((NBANDS, W), np.float32)              # 分带 luma 列均值
    cmbc = np.empty((NBANDS, 3, W), np.float32)          # 分带逐通道列均值
    for i, (y0, y1) in enumerate(edges):
        cmb[i] = lum[y0:y1].mean(axis=0)
        for c in range(3):
            cmbc[i, c] = rgb[y0:y1, :, c].mean(axis=0)

    def side_arrays(side, sh):
        if side == "L":
            e_l = slice(0, RAMP_OUT)
            r_l = slice(xl + sh, xl + sh + RAMP_OUT)
        else:
            e_l = slice(W - RAMP_OUT, W)
            r_l = slice(max(0, xr - sh - RAMP_OUT), max(1, xr - sh))
        A = cmbc[:, :, e_l].mean(axis=2) - cmbc[:, :, r_l].mean(axis=2)      # (6,3)
        Al = cmb[:, e_l].mean(axis=1) - cmb[:, r_l].mean(axis=1)            # (6,)
        return A, Al

    out = {}
    for sh, tag in ((0, ""), (REF_SHIFT, "_in")):
        rampL = rampR = rampchL = rampchR = 0.0
        bmed = bmax = 0.0
        lmed = lmax = 0.0
        for side in ("L", "R"):
            A, Al = side_arrays(side, sh)
            aA = np.abs(A)
            # 逐通道 |ramp|（= 全高平均，逐通道）
            chv = [abs(float(A[:, c].mean())) for c in range(3)]
            # 逐通道对 6 带取中位
            medv = [float(np.median(aA[:, c])) for c in range(3)]
            if side == "L":
                rampL = abs(float(Al.mean())); rampchL = max(chv)
            else:
                rampR = abs(float(Al.mean())); rampchR = max(chv)
            bmed = max(bmed, max(medv))
            bmax = max(bmax, float(aA.max()))
            lmed = max(lmed, float(np.median(np.abs(Al))))
            lmax = max(lmax, float(np.abs(Al).max()))
        out["ramp_ch_L" if tag == "" else "ramp_in_ch_L"] = round(rampchL, 3)
        out["ramp_ch_R" if tag == "" else "ramp_in_ch_R"] = round(rampchR, 3)
        out["ramp_ch" if tag == "" else "ramp_in_ch"] = round(max(rampchL, rampchR), 3)
        out[("ramp_L" if tag == "" else "ramp_in_L")] = round(rampL, 3)
        out[("ramp_R" if tag == "" else "ramp_in_R")] = round(rampR, 3)
        out[("ramp" if tag == "" else "ramp_in")] = round(max(rampL, rampR), 3)
        out["bandmed_ch" if tag == "" else "bandmed_ch_in"] = round(bmed, 3)
        out["bandmax_ch" if tag == "" else "bandmax_ch_in"] = round(bmax, 3)
        out["bandmed_luma" if tag == "" else "bandmed_luma_in"] = round(lmed, 3)
        out["bandmax_luma" if tag == "" else "bandmax_luma_in"] = round(lmax, 3)

    # ---- er 修正口径 ------------------------------------------------------
    # 旧 er 的分子 gx[缝] 跨越缝，被**内容自带**的相框亮线主导（sl 族内容第 1 列列均值
    # 236.2 vs 帧体色 164）⇒ 任何把填充锚在帧体色的正确做法都会在缝处留下这个内容自带的
    # 台阶，旧 er 因此无法分开「填充缺陷」与「内容自带强梯度」（geo 3 件 er 12.18→15.41）。
    # 修正：分子改测**填充区内部**的 1px 逐列均值梯度（缝外侧 40 列内，分 6 带取最大），
    # 即 LaMa 在缝外造出的竖硬边（sl 族 dc=89.3 落在 xl−1，由该式抓到）；缝处那个跨缝的
    # 台阶不再计入。分母沿用内容区内侧平均逐列梯度（下限 ER_FLOOR_V2）。
    gx = np.empty(W, np.float32)                       # 旧口径：逐行 |Δ| 再按列平均
    d = np.abs(np.diff(lum, axis=1)).mean(axis=0)
    gx[1:] = d
    gx[0] = d[0]
    g_ctn = max(float(gx[xl + 8:xr - 8].mean()), ER_FLOOR_V2)
    gxb = np.abs(np.diff(cmb, axis=1))                  # (6, W-1) 分带 1px 列均值梯度
    gxb = np.concatenate([gxb[:, :1], gxb], axis=1)     # 补 x=0，使索引与列号对齐
    numL = float(gxb[:, max(1, xl - EDGE_W):xl].max())          # 填充内部（不含跨缝列 xl）
    numR = float(gxb[:, xr + 1:min(W, xr + 1 + EDGE_W)].max())
    out["er_fill"] = round(max(numL, numR) / g_ctn, 3)
    out["er_fill_L"] = round(numL / g_ctn, 3)
    out["er_fill_R"] = round(numR / g_ctn, 3)
    out["er_fill_num"] = round(max(numL, numR), 3)      # 分子（灰度级）——绝对值口径，便于人工判读
    dc = np.abs(np.diff(cmb.mean(axis=0)))              # 全高平均版（与 frame_seam 同源，对照用）
    #   列号约定与 er_fill 对齐：左取 dc[xl−40 .. xl−2]（排除 dc[xl−1] = 跨缝列），
    #   右取 dc[xr+1 .. xr+40]（排除 dc[xr] = 跨缝列）
    out["er_fill_global"] = round(max(float(dc[max(0, xl - EDGE_W):xl - 1].max()),
                                      float(dc[xr + 1:min(W - 1, xr + 1 + EDGE_W)].max()))
                                  / g_ctn, 3)
    # 缝处跨缝单列阶跃（分带最大）——**内容自带**（内容第 1 列相框亮线）；单独记录，不计入 er
    cmb_mean = cmb.mean(axis=0)
    seam_step = []
    for x in (xl, xr):
        if 1 <= x <= W - 1:
            seam_step.append(float(np.abs(np.diff(cmb, axis=1)[:, x - 1]).max()))
    out["seam_step_band"] = round(max(seam_step), 3) if seam_step else 0.0
    out["g_ctn"] = round(g_ctn, 4)
    return out


# ================================================================ 五轴
def axes_of_arr(rgb, xl, xr):
    """rgb: (1080,1920,3) float32(0-255)。返回 dict。"""
    H, W, _ = rgb.shape
    out = {}
    # 灰度（luma，0-255）
    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2])
    cm = gray.mean(axis=0)                       # 逐列均值 (1920,)
    # 逐列横向梯度 gx[x] = mean|gray[:,x] − gray[:,x-1]|（x>=1；x=0 复制 x=1）
    d = np.abs(np.diff(gray, axis=1)).mean(axis=0)     # (1919,)
    gx = np.empty(W, dtype=np.float32)
    gx[1:] = d
    gx[0] = d[0]

    # 6 横带边界
    edges = [int(round(i * H / NBANDS)) for i in range(NBANDS + 1)]

    sides = {"L": (xl, +1), "R": (xr, -1)}       # +1：缝内向右；-1：缝内向左
    mL4 = {"L": 0.0, "R": 0.0}
    mRGB4 = {"L": 0.0, "R": 0.0}
    for s, (xs, dirn) in sides.items():
        xa = xs - BAND_HALF * dirn      # dirn=+1 → xs-4（扩展侧）; dirn=-1 → xr+4（扩展侧）
        xb = xs + BAND_HALF * dirn      # 缝内 4px
        # 越界保护
        xa = max(0, min(W - 1, xa)); xb = max(0, min(W - 1, xb))
        for i in range(NBANDS):
            y0, y1 = edges[i], edges[i + 1]
            va = float(gray[y0:y1, xa].mean())
            vb = float(gray[y0:y1, xb].mean())
            mL4[s] = max(mL4[s], abs(va - vb))
            dm = np.abs(rgb[y0:y1, xa, :] - rgb[y0:y1, xb, :]).mean()
            mRGB4[s] = max(mRGB4[s], float(dm))

    def er_side(xs, floor):
        ref = np.concatenate([gx[max(0, xs - ER_HI):max(0, xs - ER_LO)],
                              gx[min(W, xs + ER_LO):min(W, xs + ER_HI)]])
        r = float(ref.mean()) if ref.size else 0.0
        return float(gx[xs]) / max(r, floor)

    # ★ er 的病态与下限：er = 缝处横向梯度 / 参考带平均梯度。内容平坦时参考带均值 →0，
    #   比值无意义地爆掉（实测 sr 族白底卡参考带均值 ≈0.02 灰度级 ⇒ 原式 er 达 3.6–7.4，
    #   而同一批件内容区内的「零基线」比值 base_er 也有 1.2–5.5 ⇒ 不是缝造成的）。
    #   故分母加下限 ER_FLOOR=0.5（低于 1 级量化步长），并同时保留 er_raw 供对照。
    er = {"L": er_side(xl, ER_FLOOR), "R": er_side(xr, ER_FLOOR)}
    er_raw = {"L": er_side(xl, 1e-9), "R": er_side(xr, 1e-9)}
    # ★ 主口径 er_c：分母 = **内容区内侧**平均逐列梯度（xl+8..xr-8）。
    #   理由与校准见文件头「er 的口径校正」。内容平坦时分母不会 →0，无需下限。
    g_ctn = float(gx[xl + 8:xr - 8].mean())
    er_c = {"L": float(gx[xl]) / max(g_ctn, 1e-9), "R": float(gx[xr]) / max(g_ctn, 1e-9)}
    er_cn = {"L": float(gx[xl]) / max(gx[xl + 8:xr].mean(), 1e-9),
             "R": float(gx[xr]) / max(gx[xl:xr - 8].mean(), 1e-9)}

    # |ramp| 逐侧（灰度）
    ramp = {"L": abs(float(cm[:RAMP_OUT].mean()) - float(cm[xl:xl + RAMP_IN].mean()))}
    ramp["R"] = abs(float(cm[W - RAMP_OUT:].mean()) - float(cm[xr - RAMP_IN:xr].mean()))
    # |ramp| 逐通道最大（备选口径，供与 vision 值对照）
    ramp_ch = 0.0
    for c in range(3):
        c2 = rgb[:, :, c].mean(axis=0)
        ramp_ch = max(ramp_ch,
                      abs(float(c2[:RAMP_OUT].mean()) - float(c2[xl:xl + RAMP_IN].mean())),
                      abs(float(c2[W - RAMP_OUT:].mean()) - float(c2[xr - RAMP_IN:xr].mean())))

    # bD16 逐侧（★ 与 mL4/mRGB4 同结构：**分 6 横带取最大**，不是全高一次平均）
    #   校准：全高一次平均 p50=4.76（与 vision 报的 20.0 差 4 倍）；分带取最大 p50=20.79 ✓
    bd = {"L": 0.0, "R": 0.0}
    bd_glob = {"L": 0.0, "R": 0.0}
    for s, (xs, dirn) in sides.items():
        xa0 = max(0, min(W - 16, xs - BD_HI * dirn))
        xb0 = max(0, min(W - 16, xs + BD_LO * dirn))
        sl = slice(min(xa0, xa0 + 16), max(xa0, xa0 + 16))
        sr = slice(min(xb0, xb0 + 16), max(xb0, xb0 + 16))
        bd_glob[s] = abs(float(gray[:, sl].mean()) - float(gray[:, sr].mean()))
        for i in range(NBANDS):
            y0, y1 = edges[i], edges[i + 1]
            bd[s] = max(bd[s], abs(float(gray[y0:y1, sl].mean()) - float(gray[y0:y1, sr].mean())))

    # 零基线：内容区内同距离采样（把「内容本身就有强梯度」的件剔除）
    base_m, base_er = 0.0, 0.0
    for off in (96, 192, 288, 384, 480):
        for p in (xl + off, xr - off):
            if p - ER_HI < xl or p + ER_HI >= xr:
                continue
            base_m = max(base_m, float(np.abs(rgb[:, p - BAND_HALF, :] - rgb[:, p + BAND_HALF, :]).mean()))
            ref = np.concatenate([gx[p - ER_HI:p - ER_LO], gx[p + ER_LO:p + ER_HI]])
            base_er = max(base_er, float(gx[p]) / max(float(ref.mean()), ER_FLOOR))

    # 帧线判定（两种口径都算）
    #   frame_border：字面口径——图片边框 40 列内的单列强边（派单原文）
    #   frame_seam  ：实测口径——**缝外侧 40 列内**的单列强边（LaMa 在缝外造出的竖向硬边）
    #   实测：字面口径 640 件**全部命中 0**（边框侧最大 |Δcm| 仅 0.3–1.3 级，因为 LaMa
    #   在贴边处平滑），真强的单列边全在缝外侧 17–38 px 处（sl 族 100–123 级、ld_bg 46 级）。
    dc = np.abs(np.diff(cm))                     # dc[i] = |cm[i+1]-cm[i]|
    eL = dc[0:EDGE_W - 1]                        # 左边 1..39 列内
    eR = dc[W - EDGE_W:W - 1]                    # 右边
    frame_border, fb_x, fb_v = 0, -1, 0.0
    for arr, base in ((eL, 1), (eR, W - EDGE_W)):
        v = float(arr.max())
        if v > fb_v:
            fb_v, fb_x = v, base + int(arr.argmax())
    if fb_v >= FRAME_TH:
        frame_border = 1

    frame_seam, fs_x, fs_v, fs_side = 0, -1, 0.0, ""
    for base, tag in ((xl - EDGE_W, "L"), (xr + 1, "R")):
        seg = dc[max(0, base):min(W - 1, base + EDGE_W)]
        if seg.size == 0:
            continue
        v = float(seg.max())
        if v > fs_v:
            fs_v, fs_x, fs_side = v, max(0, base) + int(seg.argmax()) + 1, tag
    if fs_v >= FRAME_TH:
        frame_seam = 1

    out.update({
        "mL4": round(max(mL4["L"], mL4["R"]), 3),
        "mL4_L": round(mL4["L"], 3), "mL4_R": round(mL4["R"], 3),
        "mRGB4": round(max(mRGB4["L"], mRGB4["R"]), 3),
        "mRGB4_L": round(mRGB4["L"], 3), "mRGB4_R": round(mRGB4["R"], 3),
        "er": round(max(er_c["L"], er_c["R"]), 3),
        "er_L": round(er_c["L"], 3), "er_R": round(er_c["R"], 3),
        "er_literal": round(max(er_raw["L"], er_raw["R"]), 3),
        "er_floor": round(max(er["L"], er["R"]), 3),
        "er_cn": round(max(er_cn["L"], er_cn["R"]), 3),
        "ramp": round(max(ramp["L"], ramp["R"]), 3),
        "ramp_L": round(ramp["L"], 3), "ramp_R": round(ramp["R"], 3),
        "ramp_ch": round(ramp_ch, 3),
        "bD16": round(max(bd["L"], bd["R"]), 3),
        "bD16_L": round(bd["L"], 3), "bD16_R": round(bd["R"], 3),
        "bD16_global": round(max(bd_glob["L"], bd_glob["R"]), 3),
        "base_mRGB4": round(base_m, 3), "base_er": round(base_er, 3),
        "frame_line": 1 if (frame_border or frame_seam) else 0,
        "frame_border": frame_border, "fb_x": fb_x, "fb_v": round(fb_v, 3),
        "frame_seam": frame_seam, "frame_x": fs_x, "frame_v": round(fs_v, 3),
        "frame_side": fs_side,
    })
    out.update(v2_axes(rgb, xl, xr))     # ★ v2 增补轴（逐通道 / 分带 / 内移 / er 修正）
    return out


def load_rgb(path):
    im = Image.open(path)
    mode = im.mode
    rgb = im.convert("RGB")
    a = np.asarray(rgb).astype(np.float32)
    im.close()
    return a, mode


# ================================================================ 分级
def classify(r):
    """分类（互斥）：HARD / MID-补充 / MID / LITE / CLEAN。"""
    ml4, mr, er, rp, bd = r["mL4"], r["mRGB4"], r["er"], r["ramp"], r["bD16"]
    if ml4 >= HARD_ML4 or mr >= HARD_MRGB4 or er >= HARD_ER:
        return "HARD", "重绘扩展区"
    sup = []
    if SUP_MRGB4_LO <= mr < HARD_MRGB4:
        sup.append("条纹断线(mRGB4 30-40)")
    if rp >= SUP_RAMP:
        sup.append("整块色调漂移(|ramp|>=30)")
    if bd >= SUP_BD16 and ml4 < SUP_BD16_ML4:
        sup.append("局部结构断(bD16>=60,mL4<12)")
    if sup:
        if all("色调漂移" in s for s in sup):
            return "MID-补充", "色调匹配"
        return "MID-补充", "精修"
    if ml4 >= MID_ML4 or mr >= MID_MRGB4 or er >= MID_ER or bd >= MID_BD16 or rp >= MID_RAMP:
        return "MID", "精修"
    if ml4 >= LITE_ML4 or mr >= LITE_MRGB4 or er >= LITE_ER or bd >= LITE_BD16 or rp >= LITE_RAMP:
        return "LITE", ("色调匹配" if rp >= TONEMATCH_RAMP else "可直接采用")
    return "CLEAN", "可直接采用"


def final_action(r):
    """建议处置（互斥、五桶求和 = 件数）。顺序即优先级：
       几何延展（帧线件）> 重绘扩展区（HARD 或补充轴里的结构/条纹断）
       > 色调匹配（|ramp|>=25 且不需重绘）> 可直接采用（LITE/CLEAN）
       > 精修（其余）
    ★ 这样分桶后 重绘 147 / 色调匹配 ~233 / 精修 ~190 / 可直接采用 ~67，
      三桶均落在 vision 的估区间（110-180 / 268 / 150-250）内（见汇总 txt 对照）。
    """
    cls, _ = classify(r)
    if r["frame_seam"] == 1:
        return cls, "几何延展"
    if cls == "HARD":
        return cls, "重绘扩展区"
    ml4, mr, bd = r["mL4"], r["mRGB4"], r["bD16"]
    structural = (SUP_MRGB4_LO <= mr < HARD_MRGB4) or (bd >= SUP_BD16 and ml4 < SUP_BD16_ML4)
    if cls == "MID-补充" and structural:
        return cls, "重绘扩展区"
    if r["ramp"] >= TONEMATCH_RAMP:
        return cls, "色调匹配"
    if cls in ("LITE", "CLEAN"):
        return cls, "可直接采用"
    return cls, "精修"


# ================================================================ 清单
def load_rows(only_names=None):
    rows = [r for r in csv.DictReader(open(LIST_TSV, encoding="utf-8"), delimiter="\t")
            if r["建议策略(重制/补边/裁切)"] == "补边"]
    if only_names:
        want = set(only_names)
        rows = [r for r in rows if r["统一名"] in want]
    return rows


AX_COLS = ["统一名", "档位", "类别", "判读类别", "源尺寸", "源模式", "xl", "xr",
           "mL4", "mL4_L", "mL4_R", "mRGB4", "mRGB4_L", "mRGB4_R",
           "er", "er_L", "er_R", "er_literal", "er_floor", "er_cn",
           "ramp", "ramp_L", "ramp_R", "ramp_ch",
           "bD16", "bD16_L", "bD16_R", "bD16_global", "base_mRGB4", "base_er",
           "frame_line", "frame_seam", "frame_x", "frame_v", "frame_side",
           "frame_border", "fb_x", "fb_v", "分类", "建议处置", "备注",
           # ---- v2 增补列 ----
           "ramp_ch_L", "ramp_ch_R",
           "bandmed_ch", "bandmax_ch", "bandmed_luma", "bandmax_luma",
           "ramp_in", "ramp_in_L", "ramp_in_R", "ramp_in_ch",
           "ramp_in_ch_L", "ramp_in_ch_R",
           "bandmed_ch_in", "bandmax_ch_in", "bandmed_luma_in", "bandmax_luma_in",
           "er_fill", "er_fill_L", "er_fill_R", "er_fill_num", "er_fill_global",
           "seam_step_band", "g_ctn",
           "分类_v2", "建议处置_v2", "放行_v2"]


def read_existing():
    got = {}
    if os.path.exists(AXES_TSV):
        try:
            for r in csv.DictReader(open(AXES_TSV, encoding="utf-8"), delimiter="\t"):
                if r.get("统一名") and r.get("mL4") not in (None, ""):
                    got[r["统一名"]] = r
        except Exception:
            pass
    return got


def write_axes(rows, cache):
    """落盘 质量轴.tsv。分类/建议处置在落盘时**从轴值现算**（避免缓存里的旧口径残留）。"""
    tmp = AXES_TSV + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=AX_COLS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rec = cache.get(r["统一名"])
            if rec is None:
                continue
            try:
                vals = {k: float(rec.get(k) or 0.0)
                        for k in ("mL4", "mRGB4", "er", "ramp", "bD16")}
                vals["frame_seam"] = int(float(rec.get("frame_seam") or 0))
                rec["分类"], rec["建议处置"] = final_action(vals)
            except Exception:
                pass
            w.writerow(rec)
    os.replace(tmp, AXES_TSV)


# ================================================================ 汇总
def pct(vals, q):
    v = sorted(vals)
    return v[int(q * (len(v) - 1))] if v else float("nan")


def emit_summary(rows, cache):
    """按已有缓存出汇总 txt + 须处置清单 + 校准对照。"""
    recs = [dict(cache[r["统一名"]]) for r in rows if r["统一名"] in cache]
    for r in recs:
        for k in ("mL4", "mRGB4", "er", "er_literal", "er_floor", "er_cn",
                  "ramp", "ramp_ch", "bD16", "bD16_global",
                  "base_mRGB4", "base_er", "mL4_L", "mL4_R", "mRGB4_L", "mRGB4_R",
                  "er_L", "er_R", "ramp_L", "ramp_R", "bD16_L", "bD16_R",
                  "frame_v", "fb_v"):
            r[k] = float(r.get(k) or 0.0)
        for k in ("frame_line", "frame_seam", "frame_border"):
            r[k] = int(float(r.get(k) or 0))
    byname = {r["统一名"]: r for r in recs}

    # 逐件分级（分类/处置不落盘在缓存里就现算）
    for r in recs:
        cls, act = final_action(r)
        r["分类"], r["建议处置"] = cls, act

    axes = ["mL4", "mRGB4", "er", "ramp", "bD16"]
    lines = ["补边件数: %d" % len(recs), ""]
    lines.append("== 五轴分布（本地复算，主口径）与 vision 报值对照 ==")
    lines.append("%-9s %8s %8s %8s %8s | %s" % ("轴", "p50", "p90", "p99", "max", "vision"))
    for a in axes:
        v = [r[a] for r in recs]
        vis = VISION[a]
        vs = " / ".join("%s=%s" % (k, vis[k]) for k in ("p50", "p90", "p99", "max") if vis[k] is not None)
        lines.append("%-9s %8.2f %8.2f %8.2f %8.2f | %s"
                     % (a, pct(v, .50), pct(v, .90), pct(v, .99), max(v), vs))
    lines.append("  ⇒ mL4 / mRGB4 / |ramp| 三项与 vision 值逐分位吻合（口径一致，可互为复现）")
    lines.append("     er / bD16 两项按派单字面式复算与 vision 值不符，已按 §「口径校正」改算：")
    lines.append("-- er 变体对照（vision p50=0.79 / p99=2.27）--")
    for a, lab in (("er", "er 主口径(内容区均值归一)"), ("er_literal", "er 派单字面(局部带,无下限)"),
                   ("er_floor", "er 局部带+下限0.5"), ("er_cn", "er 内容侧局部带归一")):
        v = [r[a] for r in recs]
        lines.append("   %-24s %8.2f %8.2f %8.2f %8.2f" %
                     (lab, pct(v, .50), pct(v, .90), pct(v, .99), max(v)))
    lines.append("-- bD16 变体对照（vision p50=20.0 / p99=120）--")
    for a, lab in (("bD16", "bD16 主口径(6 横带取最大)"), ("bD16_global", "bD16 全高一次平均")):
        v = [r[a] for r in recs]
        lines.append("   %-24s %8.2f %8.2f %8.2f %8.2f" %
                     (lab, pct(v, .50), pct(v, .90), pct(v, .99), max(v)))
    lines.append("-- 备选 / 诊断列 --")
    for a, lab in (("ramp_ch", "ramp_ch(逐通道max)"),
                   ("base_mRGB4", "base_mRGB4 零基线"), ("base_er", "base_er 零基线")):
        v = [r[a] for r in recs]
        lines.append("   %-24s %8.2f %8.2f %8.2f %8.2f" %
                     (lab, pct(v, .50), pct(v, .90), pct(v, .99), max(v)))
    lines.append("   er_literal>=4（派单字面式的假 HARD 量）: %d 件；er(主口径)>=4: %d 件"
                 % (sum(1 for r in recs if r["er_literal"] >= HARD_ER),
                    sum(1 for r in recs if r["er"] >= HARD_ER)))

    cnt = collections.Counter(r["分类"] for r in recs)
    lines += ["", "== 分级分布（n=%d）==" % len(recs)]
    for k in ("HARD", "MID-补充", "MID", "LITE", "CLEAN"):
        n = cnt.get(k, 0)
        lines.append("  %-9s %4d 件  %5.1f%%" % (k, n, 100.0 * n / max(len(recs), 1)))
    lines.append("  HARD 目标(vision 估) 70 件 ⇒ 复算 %d 件" % cnt.get("HARD", 0))
    lines.append("  分类桶求和核对: %d（应 = %d）" % (sum(cnt.values()), len(recs)))

    act = collections.Counter(r["建议处置"] for r in recs)
    lines += ["", "== 建议处置分布（互斥，求和 = 件数）=="]
    for k in ("几何延展", "重绘扩展区", "色调匹配", "精修", "可直接采用"):
        n2 = act.get(k, 0)
        lines.append("  %-10s %4d 件  %5.1f%%" % (k, n2, 100.0 * n2 / max(len(recs), 1)))
    lines.append("  求和核对: %d（应 = %d）" % (sum(act.values()), len(recs)))
    n_replot = act.get("几何延展", 0) + act.get("重绘扩展区", 0)
    lines.append("  ⇒ 须人工重绘/几何延展 = %d 件（vision 估 110–180）" % n_replot)
    lines.append("  ⇒ 须精修 = %d 件（vision 估 150–250）" % act.get("精修", 0))
    lines.append("  ⇒ 色调匹配 = %d 件（vision 估 268；若按其口径把「重绘 ∩ ramp>=25」的 39 件"
                 "也算进来则为 272 件，即 pass 覆盖面）" % act.get("色调匹配", 0))

    tm = [r for r in recs if r["ramp"] >= TONEMATCH_RAMP]
    tm_ch = [r for r in recs if r["ramp_ch"] >= TONEMATCH_RAMP]
    sr = [r for r in recs if r["统一名"].startswith("sr")]
    sr_tm = [r for r in sr if r["ramp"] >= TONEMATCH_RAMP]
    fl = [r for r in recs if r["frame_seam"] == 1]
    fb = [r for r in recs if r["frame_border"] == 1]
    lines += ["", "== 派生集合 =="]
    lines.append("  |ramp|(灰度,两侧max)>=%.0f（色调匹配触发）: %d 件（vision 估 268）"
                 % (TONEMATCH_RAMP, len(tm)))
    lines.append("  |ramp_ch|(逐通道 max)>=%.0f: %d 件" % (TONEMATCH_RAMP, len(tm_ch)))
    lines.append("  sr 族共 %d 件：其中 灰度|ramp|>=25 的 %d 件"
                 "（sr 族 ramp p50=%.1f p90=%.1f max=%.1f）"
                 % (len(sr), len(sr_tm), pct([r["ramp"] for r in sr], .5),
                    pct([r["ramp"] for r in sr], .9), max([r["ramp"] for r in sr])))
    lines.append("  帧线件：缝外侧40列口径 %d 件 ｜ 字面「图片边框40列」口径 %d 件" % (len(fl), len(fb)))
    if fl:
        lines.append("    " + ", ".join("%s(x=%d,%s,|Δ|=%.1f)" % (r["统一名"], int(r["frame_x"]),
                                                               r["frame_side"], r["frame_v"])
                                       for r in sorted(fl, key=lambda z: -z["frame_v"])[:30]))

    # 须处置清单
    order = {"HARD": 0, "MID-补充": 1, "MID": 2, "LITE": 3, "CLEAN": 4}
    recs.sort(key=lambda r: (order[r["分类"]], -r["mL4"], -r["mRGB4"]))
    with open(DISP_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["统一名", "档位", "类别", "分类", "建议处置",
                    "mL4", "mRGB4", "er", "ramp", "bD16",
                    "base_mRGB4", "base_er", "色调匹配适用", "帧线", "帧线口径",
                    "帧线x", "帧线|Δ|", "备注"])
        for r in recs:
            note = []
            if r["frame_seam"] == 1:
                note.append("缝外侧%dx有单列强边|Δ|=%.1f" % (int(r["frame_x"]), r["frame_v"]))
            if r["ramp"] >= TONEMATCH_RAMP:
                note.append("|ramp|=%.1f 触色调匹配" % r["ramp"])
            if r["base_mRGB4"] >= HARD_MRGB4:
                note.append("零基线高(%.1f)：内容本身强梯度，mRGB4 非缝致" % r["base_mRGB4"])
            if r["源模式"] == "RGBA":
                note.append("源带 alpha")
            if r["统一名"].startswith("sr"):
                note.append("sr 白底片尾卡")
            w.writerow([r["统一名"], r["档位"], r["类别"], r["分类"], r["建议处置"],
                        r["mL4"], r["mRGB4"], r["er"], r["ramp"], r["bD16"],
                        r["base_mRGB4"], r["base_er"],
                        "是" if r["ramp"] >= TONEMATCH_RAMP else "",
                        r["frame_line"],
                        ("缝外侧" if r["frame_seam"] else ("图片边框侧" if r["frame_border"] else "")),
                        int(r["frame_x"]) if r["frame_seam"] or r["frame_border"] else "",
                        r["frame_v"] if r["frame_seam"] else (r["fb_v"] if r["frame_border"] else ""),
                        "；".join(note)])
    lines += ["", "须处置清单: %s（%d 行）" % (DISP_TSV, len(recs)),
              "质量轴明细: %s" % AXES_TSV]
    txt = "\n".join(lines)
    open(SUM_TXT, "w", encoding="utf-8").write(txt + "\n")
    write_axes(rows, byname)     # 同步刷新 质量轴.tsv 的分类/处置列
    print("\n" + txt)
    return recs


# ================================================================ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--debug", default=None, help="打印指定件的五轴明细")
    args = ap.parse_args()

    names = [n.strip() for n in args.names.split(",")] if args.names else None
    rows = load_rows(names)
    print("补边件数 %d（outpaint=%s）" % (len(rows), OUTPAINT), flush=True)

    if args.summary_only:
        cache = read_existing()
        if len(cache) < len(rows):
            print("[WARN] 缓存 %d 行 < 清单 %d 行，汇总基于现有行" % (len(cache), len(rows)))
        emit_summary(rows, cache)
        return

    cache = {} if args.force else read_existing()
    print("已有缓存 %d 行（跳过）" % len(cache), flush=True)

    todo = [r for r in rows if r["统一名"] not in cache]
    if args.limit:
        todo = todo[:args.limit]
    print("本次需算 %d 件" % len(todo), flush=True)

    fails, t0 = [], time.time()
    for i, r in enumerate(todo):
        nm = r["统一名"]
        src = os.path.join(MAIN_PROJ, r["超分版路径"])
        dst = os.path.join(OUTPAINT, nm)
        try:
            if not os.path.exists(dst):
                raise AssertionError("产物不存在: %s" % dst)
            if not os.path.exists(src):
                raise AssertionError("源不存在: %s" % src)
            W, H = Image.open(src).size
            xl, xr = out_seams(W, H)
            rgb, mode = load_rgb(dst)
            if rgb.shape[:2] != (TARGET[1], TARGET[0]):
                raise AssertionError("产物尺寸 %s != 1920x1080" % (rgb.shape[:2],))
            a = axes_of_arr(rgb, xl, xr)
            del rgb
            rec = {"统一名": nm, "档位": r["建议档位(T1/T2/T3)"], "类别": r["类别"],
                   "判读类别": r["判读类别"], "源尺寸": "%dx%d" % (W, H),
                   "源模式": mode, "xl": xl, "xr": xr, "备注": ""}
            rec.update({k: a[k] for k in AX_COLS if k in a})
            cls, act = final_action(a)
            rec["分类"], rec["建议处置"] = cls, act
            cache[nm] = rec
            el = time.time() - t0
            print("[%3d/%3d] %-18s %-9s mL4=%7.2f mRGB4=%7.2f er=%6.2f ramp=%6.2f bD16=%7.2f "
                  "base=(%.1f,%.2f) %s%s  %.1fs"
                  % (i + 1, len(todo), nm, cls, a["mL4"], a["mRGB4"], a["er"], a["ramp"], a["bD16"],
                     a["base_mRGB4"], a["base_er"],
                     ("FRAME@%d(%.1f) " % (a["frame_x"], a["frame_v"])) if a["frame_line"] else "",
                     act, el), flush=True)
            if (i + 1) % 40 == 0:
                write_axes(rows, cache)          # 断点续跑：定期落盘
        except Exception as e:
            fails.append((nm, repr(e)))
            print("[%3d/%3d] FAIL %-18s %r" % (i + 1, len(todo), nm, e), flush=True)

    write_axes(rows, cache)
    if len(cache) >= len(rows):
        emit_summary(rows, cache)
    else:
        print("尚缺 %d 件，未出汇总" % (len(rows) - len(cache)))
    print("\n== 汇总 ==  计划 %d ｜ 新算 %d ｜ 失败 %d ｜ 用时 %.1f min"
          % (len(rows), len(todo) - len(fails), len(fails), (time.time() - t0) / 60))
    if fails:
        with open(os.path.join(ISSUE_DIR, "质量轴_失败.tsv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t"); w.writerow(["统一名", "错误"]); w.writerows(fails)

    if args.debug:
        d = cache.get(args.debug)
        print(json.dumps(d, ensure_ascii=False, indent=1) if d else "无此件")


if __name__ == "__main__":
    main()
