# -*- coding: utf-8 -*-
"""ISSUE-20260927-07-b：三系统按钮**再**左移。

用户第二轮指令「再向左移动 10px」；口径与首轮一致（窗口上目测 ×1.5 换算画布）⇒ Δx = −15。
本脚本幂等：以「当前值 − 15」为期望前置态断言（OLD），只改 x，每处恰好命中 1 次。
"""
import io, json, sys
OLD_NEW = {  # 元素 id 前缀 → (本轮前置 x, 本轮目标 x)
    "sv.sys_game":      (864, 849),
    "sv.sys_game_tx":   (864, 849),
    "sv.sys_game_hit":  (856, 841),
    "sv.sys_title":     (1114, 1099),
    "sv.sys_title_tx":  (1114, 1099),
    "sv.sys_title_hit": (1106, 1091),
    "sv.sys_end":       (1472, 1457),
    "sv.sys_end_tx":    (1472, 1457),
    "sv.sys_end_hit":   (1464, 1449),
}
FILES = ["layout/screens/23_save.json", "layout/screens/24_load.json"]


def patch(path):
    s = io.open(path, encoding="utf-8", newline="").read()
    for eid, (old, new) in OLD_NEW.items():
        key = '"id": "%s"' % eid
        assert s.count(key) == 1, (path, eid, "id 命中", s.count(key))
        i = s.index(key)
        j = s.index('"x":', i)
        k = s.index(",", j)
        cur = int(s[j + len('"x":'):k].strip())
        assert cur == old, (path, eid, "前置值", cur, "期望", old)
        s = s[:j] + '"x": %d,' % new + s[k + 1:]
    io.open(path, "w", encoding="utf-8", newline="").write(s)
    print("已改:", path)


for f in FILES:
    patch(f)
# 读回复核
for f in FILES:
    d = json.load(open(f, encoding="utf-8"))
    els = {e["id"]: e for e in d["elements"]}
    xs = {i: els[i]["x"] for i in OLD_NEW}
    ok = all(xs[i] == OLD_NEW[i][1] for i in OLD_NEW)
    print(f"  {f.split('/')[-1]} 读回: {xs}  ⇒ {'PASS' if ok else 'FAIL'}")
    assert ok
print("二轮左移完成（Δx=−15，累计自原始 872/1122/1480 为 −23）")
