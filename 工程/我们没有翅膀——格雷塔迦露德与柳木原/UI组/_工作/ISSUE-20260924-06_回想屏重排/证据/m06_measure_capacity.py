# -*- coding: utf-8 -*-
r"""M06 · 回想屏重排 · 文案容量实测（真实语料 + 引擎折行算法）

■ 为什么必须实测（接口冻结书 §1 排版约束 1 / M43 教训）
  回想块里每行是一条**真实已读台词**，运行期灌入。若文本区放不下就会被截断
  （`uiThemeWrap` 的 `maxLines` 会 `out.pop()` 丢尾），属「静默丢字」——明令禁止。
  故必须用**全部真实语料**按**引擎同口径折行**跑一遍，而不是看示例文案。

■ 引擎同口径（照抄 `krkr\game\ui_theme.tjs`）
  · 折行 `uiThemeWrap(layer, text, maxW, maxLines)`：
      逐字符累加，`font.getTextWidth(line + ch) <= maxW` 则收下；
      超宽时——① 若 ch ∈ `UIThemeNoHeadChars`（行首禁则）**强行并入本行**；
                ② 若本行末字符 ∈ `UIThemeNoTailChars`（行尾禁则）**挪到下一行**；再断行；
      最后 `maxLines` 限制：超出则 `truncated=true` 并**丢弃尾部行**。
  · 度量 `layer.font.getTextWidth(s)` = 字形**步进宽**逐字相加（krkr 不做字距微调）；
    本脚本用 PIL 逐字 advance 相加复现（`ImageFont.getlength` 逐字缓存），
    字体取 fallback_faces 首位 `微软雅黑` → `C:\Windows\Fonts\msyh.ttc`
    （与 `_工作\M18_measure_flowtext.py` 同口径、同字体）。
  · 行距 `lineSpacing`：元素未写 `line_spacing` ⇒ 回落 `layout\ui_layout.json.fonts.line_spacing.body = 1.4`
    ⇒ lineH = floor(30 × 1.4) = 42 px。

■ 文本区几何（本脚本的输入 = 本次选定的数据侧几何）
  `bl.list.item_text = { x:219, y:19, w:1117, h:173 }`、`font.size = 30`、`max_lines = 4`
  · 左界 219 = 卡体左缘 12.5 + PSB `#rects/text` 的 206（**+13 形体修正**：块底板素材是
    「1350×241 卡体 + 四边 12.5px 柔光」，引擎把整张画布画进元素矩形 ⇒ 可见卡体恒内缩 12.5px，
    照抄 PSB 会让文字离可见卡缘近 12.5px，见 `m06_nine_grid_study.py`）；
  · 右界 1336 = 219 + 1117 ≈ 卡体右缘 1336.5（文字不得压进柔光带）；
  · 上界 19、下界 192 同理（卡体上/下缘 12.5 / 192.5）；
  · 4 行 × 42 = 168 ≤ 173 ✓。

■ 用法
    python _工作\ISSUE-20260924-06_回想屏重排\证据\m06_measure_capacity.py
  退出码：0 = 全部台词在 max_lines 内放得下（无截断）；1 = 存在会被截断的台词（须调排版/上报）
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
from collections import Counter

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))          # <UI组>
PROJ = os.path.dirname(UI)
CORPUS = os.path.join(PROJ, "资源组", "剧本")
FONT = "C:/Windows/Fonts/msyh.ttc"

# ── 本次选定的数据侧几何（与 26_backlog.json 的 item_text / font 一致）
TEXT_W = 1117
TEXT_H = 173
FONT_SIZE = 30
MAX_LINES = 4

# ── 禁则字符表（逐字照抄 krkr\game\ui_theme.tjs:33/35）
NO_HEAD = "、。，．！？：；）」』】》〉”’!?,.:;)]}"
NO_TAIL = "（「『【《〈“‘([{"

# 行距：元素无 line_spacing ⇒ 回落 body
LINE_SPACING_BODY = 1.4
LINE_H = int(FONT_SIZE * LINE_SPACING_BODY)


class Metric:
    """引擎口径的字宽度量：逐字 advance 相加（getTextWidth 语义），带缓存"""

    def __init__(self, path, size):
        self.f = ImageFont.truetype(path, size)
        self.cache = {}

    def chw(self, ch):
        v = self.cache.get(ch)
        if v is None:
            v = self.f.getlength(ch)
            self.cache[ch] = v
        return v

    def width(self, s):
        return sum(self.chw(c) for c in s)


def wrap(m, text, max_w, max_lines):
    """照抄 uiThemeWrap：→ (lines, truncated)"""
    out = []
    for para in text.split("\n"):
        if para == "":
            out.append("")
            continue
        line, lw = "", 0.0
        for ch in para:
            w = lw + m.chw(ch)
            if w <= max_w or line == "":
                line += ch
                lw = w
                continue
            if ch in NO_HEAD:                      # 行首禁则：强行并入
                line += ch
                lw = w
                continue
            carry = ""
            if line and line[-1] in NO_TAIL:       # 行尾禁则：末字挪下一行
                carry = line[-1]
                line = line[:-1]
            out.append(line)
            line = carry + ch
            lw = m.width(line)
        if line != "" or para == "":
            out.append(line)
    truncated = False
    if max_lines and len(out) > max_lines:
        truncated = True
        while len(out) > max_lines:
            out.pop()
    return out, truncated


def main():
    if not os.path.exists(FONT):
        print("环境错误：找不到字体 %s" % FONT)
        return 2
    m = Metric(FONT, FONT_SIZE)
    print("=" * 100)
    print("M06 · 回想屏文案容量实测（真实语料 + 引擎折行算法）")
    print("=" * 100)
    print("字体 %s（fallback_faces[0] 微软雅黑）/ 字号 %d / 行距 %.1f ⇒ lineH %d"
          % (os.path.basename(FONT), FONT_SIZE, LINE_SPACING_BODY, LINE_H))
    print("文本区 w=%d ｜ 可用行数 max_lines=%d ｜ 可用高 %d（行距口径 %.1f 行）"
          % (TEXT_W, MAX_LINES, TEXT_H, TEXT_H / float(LINE_H)))
    print("单行可容：全角 %d 字（每字步进 %.1f px）"
          % (int(TEXT_W // m.chw("永")), m.chw("永")))
    print("四行上限：约 %d 全角字" % (int(4 * (TEXT_W // m.chw("永")))))
    print("禁则：行首「%s」／行尾「%s」" % (NO_HEAD, NO_TAIL))
    print()

    files = sorted(glob.glob(os.path.join(CORPUS, "scene_*.jsonl")))
    if not files:
        print("环境错误：%s 下无 scene_*.jsonl" % CORPUS)
        return 2

    stat_bare, stat_named = Counter(), Counter()
    stat_kind = {}          # kind -> Counter(行数)
    trunc_bare, trunc_named = [], []
    worst_bare, worst_named = [], []
    n_lines = n_empty = 0
    for p in files:
        for ln in io.open(p, encoding="utf-8"):
            for L in json.loads(ln).get("lines", []):
                t = (L.get("cn") or "").strip()
                if not t:
                    n_empty += 1
                    continue
                n_lines += 1
                # (a) 仅台词（忠实原状：`labels` 只放台词文本）
                lines, tr = wrap(m, t, TEXT_W, MAX_LINES)
                stat_bare[len(lines)] += 1
                kind = L.get("kind") or "?"
                stat_kind.setdefault(kind, Counter())[len(lines)] += 1
                if tr:
                    trunc_bare.append((len(lines), t))
                worst_bare.append((len(lines), t))
                # (b) 带说话人前缀「名「台词」」（若机制侧决定显示角色名——更保守的假设）
                sp = (L.get("speaker") or "").strip()
                if sp:
                    t2 = "%s「%s」" % (sp, t)
                    lines2, tr2 = wrap(m, t2, TEXT_W, MAX_LINES)
                    stat_named[len(lines2)] += 1
                    if tr2:
                        trunc_named.append((len(lines2), t2))
                    worst_named.append((len(lines2), t2))

    print("语料：%d 个 scene_*.jsonl ｜ 非空台词 %d 条（空 %d 条）" % (len(files), n_lines, n_empty))
    print()
    print("（0）按 kind 分档（折行行数分布；末两列为该档最多行数 / 超 max_lines 条数）：")
    print("      %-10s %7s %7s %7s %7s %7s  %6s %6s" % ("kind", "1行", "2行", "3行", "4行", "5+行", "最多", "超限"))
    for kind in sorted(stat_kind, key=lambda k: -sum(stat_kind[k].values())):
        c = stat_kind[kind]
        mx = max(c)
        over = sum(v for k2, v in c.items() if k2 > MAX_LINES)
        print("      %-10s %7d %7d %7d %7d %7d  %6d %6d"
              % (kind, c[1], c[2], c[3], c[4], over, mx, over))
    print()
    print("（a）仅台词文本　折行后行数分布：")
    for k in sorted(stat_bare):
        print("      %d 行：%6d 条（%.2f%%）" % (k, stat_bare[k], 100.0 * stat_bare[k] / n_lines))
    print("      最多需要 %d 行；超过 max_lines=%d 的条数 = **%d**"
          % (max(stat_bare) if stat_bare else 0, MAX_LINES, len(trunc_bare)))
    print()
    print("（b）说话人「台词」前缀（仅统计有 speaker 的行）　折行后行数分布：")
    tot_b = sum(stat_named.values())
    for k in sorted(stat_named):
        print("      %d 行：%6d 条（%.2f%%）" % (k, stat_named[k], 100.0 * stat_named[k] / tot_b if tot_b else 0))
    print("      最多需要 %d 行；超过 max_lines=%d 的条数 = **%d**"
          % (max(stat_named) if stat_named else 0, MAX_LINES, len(trunc_named)))
    print()

    worst_bare.sort(key=lambda x: (-x[0], -len(x[1])))
    print("最长（折行行数最多）10 条 · 仅台词 —— 逐条折行结果：")
    print("-" * 100)
    for k, t in worst_bare[:10]:
        lines, _ = wrap(m, t, TEXT_W, MAX_LINES + 2)
        print("  [%d 行 / %d 字] %s" % (k, len(t), t))
        for i, l in enumerate(lines, 1):
            print("        %d| %s" % (i, l))
    print("-" * 100)
    if trunc_bare:
        print("\n★ 会被截断的台词（仅台词口径）：%d 条，前 10 条：" % len(trunc_bare))
        for k, t in trunc_bare[:10]:
            print("   [需 %d 行] %s" % (k, t[:120]))

    print()
    print("=" * 100)
    bad = len(trunc_bare)
    print("结论：文本区 %dx%d / 字号 %d / lineH %d / max_lines %d ⇒"
          " 真实语料**最多需 %d 行**，%s"
          % (TEXT_W, TEXT_H, FONT_SIZE, LINE_H, MAX_LINES,
             max(stat_bare) if stat_bare else 0,
             "**无截断风险** ✓" if bad == 0 else "**有 %d 条会截断 ⇒ 必须调排版或上报** ✗" % bad))
    print("（若机制侧改为显示说话人前缀，则最多需 %d 行，截断 %d 条）"
          % (max(stat_named) if stat_named else 0, len(trunc_named)))

    # 硬边界（合成全角串探边界，不用示例文案凑数）
    n_fit = int(TEXT_W // m.chw("永"))
    for n in (n_fit * MAX_LINES - 1, n_fit * MAX_LINES, n_fit * MAX_LINES + 1):
        lines, tr = wrap(m, "永" * n, TEXT_W, MAX_LINES)
        print("   合成全角 %3d 字 ⇒ %d 行%s" % (n, len(lines), "（**截断**）" if tr else ""))
    print("   ⇒ 本几何的硬边界 = **%d 全角字 / 4 行**；语料实测最大值见上（≥4 行档 %d 条）"
          % (n_fit * MAX_LINES, stat_bare.get(4, 0)))
    print("=" * 100)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
