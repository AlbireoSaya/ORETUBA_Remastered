# -*- coding: utf-8 -*-
r"""m07_sysbtn_shift.py —— 存/读档屏右上「三系统按钮组」再整体左移 8px
（ISSUE-20260927-07 · 系统按钮模块）

用户指令（原话口径）：「存/读档屏右上角三个系统按钮整体再向左移（渲染窗口上约 5px）」
换算口径（主代理已定，见 `_工作\ISSUE-20260927-07_节点描边与系统按钮\立案.md`）：
  窗口 1280 宽 = 画布 1920 的 2/3  ⇒  屏上 5px ≈ 画布 8px  ⇒  本轮 Δx = −8。

落点：`layout\screens\23_save.json`、`layout\screens\24_load.json`（已核 `sv.sys_*` 只在这两屏）。

★ 改法纪律（本工程明确要求）：
  · **子串级替换**，禁止 `json.dumps` 整文件往返（会重排 + CRLF→LF）；
  · 按元素 id 定位后**只改该元素的 x**，每个替换断言**恰好命中 1 次**；
  · 改完读回 JSON 复核 9 件 x；三按钮两两间距必须不变。

用法：
  python m07_sysbtn_shift.py --check    # 只读核查 / 出对照表，不写盘
  python m07_sysbtn_shift.py            # 应用（幂等：已为新值则只报不写）
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
UI = HERE.parents[3]                       # ...\UI组
SCREENS = UI / "layout" / "screens"
FILES = ("23_save.json", "24_load.json")

DELTA = -8

# id -> 旧 x（在盘上实测确认；新 x = 旧 + DELTA）
OLD_X = [
    ("sv.sys_game",      872),
    ("sv.sys_game_tx",   872),
    ("sv.sys_game_hit",  864),
    ("sv.sys_title",    1122),
    ("sv.sys_title_tx", 1122),
    ("sv.sys_title_hit",1114),
    ("sv.sys_end",      1480),
    ("sv.sys_end_tx",   1480),
    ("sv.sys_end_hit",  1472),
]
ORDER = [i for i, _ in OLD_X]
NEW_X = {i: x + DELTA for i, x in OLD_X}

NOTE_ANCHOR = '",\r\n "elements": ['
NOTE_MARK = ("★ **右上三系统按钮再左移轮（2026-09-27 · ISSUE-20260927-07；"
             "依据＝用户实测反馈，口径＝屏上 5px ≈ 画布 8px）**")

NOTE_SUFFIX = (
    "\n\n" + NOTE_MARK + "：用户实机在**渲染后的窗口**（1280 宽 = 画布 1920 的 2/3）上目测"
    "「**再**向左约 5px」⇒ 按主代理既定口径取 **Δx = −8**（画布单位）对九件**整簇平移**：\n"
    "  · `sv.sys_game` / `_tx` / `_hit`：x **872 / 872 / 864 → 864 / 864 / 856**\n"
    "  · `sv.sys_title` / `_tx` / `_hit`：x **1122 / 1122 / 1114 → 1114 / 1114 / 1106**\n"
    "  · `sv.sys_end` / `_tx` / `_hit`：x **1480 / 1480 / 1472 → 1472 / 1472 / 1464**\n"
    "  ⇒ **可见件组右沿 1690 → 1682**，与页码徽章列左沿 1699（引擎绘 `sv.pgnum_01..10`）"
    "间隙 **9px → 17px**；hit 层右沿 1698 → **1690**，仍不压徽章列 1699。\n"
    "  · **组内相对关系逐项不变**（整簇平移，非重排）：可见件横向间距 40px / 40px（改前改后同为 "
    "1122−1082 与 1480−1440）、hit 层间距 24px / 24px（1114−1090 与 1472−1448）；"
    "`y`/`w`/`h`/`z`/`asset`/`font`/`action`/`vis_flag`/`vis_when` 与全部机制字段**一律未动**"
    "（含 `_hit` 与 `_tx`）。\n"
    "  · **本节终态值取代上一节（ISSUE-20260927-01）记录的 `872/1122/1480` 终态**；"
    "上一节作为该轮历史记录**原文保留不改**（旧号即该轮结束时的真值）。\n"
    "  · 两屏同款处理，改后两屏该组几何逐项相同。改法＝**子串级替换**（按 id 定位、每个替换"
    "恰好命中 1 次；未做 `json.dumps` 整文件往返）；脚本与读回复核："
    "`_工作\\ISSUE-20260927-07_节点描边与系统按钮\\取证\\m07_sysbtn_shift.py`、"
    "同目录 `自证_*.txt`。旧值备份见 `_工作\\ISSUE-20260927-01_存读档按钮\\原形备份\\`"
    "（−190 轮的原形）与本轮取证目录内的改前快照。"
)


def load_text(path):
    return path.read_bytes().decode("utf-8")


def patch_x(text, eid, old, new):
    """按 id 定位该元素块，只改其 x。断言：id 命中 1 次、x 命中 1 次且等于 old。"""
    idtok = '"id": "%s",' % eid
    n_id = text.count(idtok)
    assert n_id == 1, "id %s 命中 %d 次（应为 1）" % (eid, n_id)
    start = text.index(idtok)
    m = re.compile(r'"x": (-?\d+),').search(text, start)
    assert m is not None, "%s 块内未找到 x" % eid
    assert m.group(1) == str(old), "%s 的 x 盘上为 %s，非预期旧值 %s" % (eid, m.group(1), old)
    # 该 x 必须仍属于同一元素块（下一个 id 之前）
    nxt = text.find('"id": "', start + len(idtok))
    assert nxt < 0 or m.start() < nxt, "%s 的 x 越界到下一元素" % eid
    return text[:m.start()] + '"x": %d,' % new + text[m.end():]


def readback_x(text):
    obj = json.loads(text)
    return {e["id"]: e["x"] for e in obj["elements"]}


def gaps(xs):
    vis = [("game", xs["sv.sys_game"], 210), ("title", xs["sv.sys_title"], 318),
           ("end", xs["sv.sys_end"], 210)]
    hit = [("game", xs["sv.sys_game_hit"], 226), ("title", xs["sv.sys_title_hit"], 334),
           ("end", xs["sv.sys_end_hit"], 226)]
    out = []
    for i in range(2):
        out.append((vis[i][0] + "→" + vis[i + 1][0], vis[i + 1][1] - (vis[i][1] + vis[i][2])))
    for i in range(2):
        out.append((hit[i][0] + "→" + hit[i + 1][0] + "(hit)",
                    hit[i + 1][1] - (hit[i][1] + hit[i][2])))
    return out


def main():
    check = "--check" in sys.argv
    rc = 0
    for fn in FILES:
        path = SCREENS / fn
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        assert raw[:3] != b"\xef\xbb\xbf", "%s 有 BOM" % fn
        before = readback_x(text)                       # json 读回（仅复核用）
        # 盘上现值必须等于预期旧值
        for eid, old in OLD_X:
            assert before[eid] == old, "%s %s 盘上 x=%s ≠ 预期 %s" % (fn, eid, before[eid], old)

        print("=" * 96)
        print("%s  （%d 字节，CRLF %d）" % (fn, len(raw), text.count("\r\n")))
        print("  %-18s %8s %8s %6s" % ("元素", "改前 x", "改后 x", "Δ"))
        for eid, old in OLD_X:
            print("  %-18s %8d %8d %6d" % (eid, old, NEW_X[eid], DELTA))

        if check:
            print("  --check：不写盘")
            continue

        new = text
        hits = {}
        for eid, old in OLD_X:
            new2 = patch_x(new, eid, old, NEW_X[eid])
            assert new2 != new, "%s 替换未生效" % eid
            hits[eid] = 1
            new = new2
        assert len(hits) == 9 and all(v == 1 for v in hits.values())

        # 只允许这 9 处数字变化：把两串按同一位置切分，逐段比较
        # 用「除数字外全部相同」的等价判据：把数字替换成占位符后应完全相等
        norm = lambda t: re.sub(r"-?\d+", "#", t)
        assert norm(new) == norm(text), "除 x 数字外还有别处变化，拒绝写盘"

        # 结构计数不变
        assert new.count("\r\n") == text.count("\r\n"), "行尾数量变化（CRLF 被动过）"
        assert new.count('"id": "') == text.count('"id": "'), "元素数变化"

        # note 追加（子串级：插在 note 值结束引号之前）
        if NOTE_MARK not in new:
            assert new.count(NOTE_ANCHOR) == 1, "note 锚点不唯一"
            ins = new.index(NOTE_ANCHOR)          # 锚点以 note 值的结束引号开头 ⇒ 插在该引号之前
            assert new[ins] == '"', "note 锚点未落在结束引号上"
            assert new[ins - 1] != "\\", "note 结束引号前是反斜杠（被转义），锚点判断有误"
            frag = json.dumps(NOTE_SUFFIX, ensure_ascii=False)[1:-1]   # 只转义片段，非整文件往返
            new = new[:ins] + frag + new[ins:]
            print("  note：已追加本轮口径片段（%d 字）" % len(NOTE_SUFFIX))
        else:
            print("  note：本轮标记已存在，跳过追加")

        after = readback_x(new)
        for eid, old in OLD_X:
            assert after[eid] == NEW_X[eid], "%s 读回 x=%s ≠ %s" % (eid, after[eid], NEW_X[eid])
        gb, ga = gaps(before), gaps(after)
        assert gb == ga, "间距改变！%s -> %s" % (gb, ga)

        path.write_bytes(new.encode("utf-8"))
        print("  已写入 %s（%d 字节，Δ%+d；CRLF %d）"
              % (path, len(new.encode("utf-8")), len(new) - len(text), new.count("\r\n")))
        print("  读回复核：%s" % ", ".join("%s=%d" % (i, after[i]) for i in ORDER))
        print("  间距（改前=改后）：%s" % ", ".join("%s %d" % g for g in ga))
    return rc


if __name__ == "__main__":
    sys.exit(main())
