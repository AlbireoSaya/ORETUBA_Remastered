# -*- coding: utf-8 -*-
"""一次性补丁：把 m01/m06 的**盘面** md5 改为按 LF 规范化后再比（ISSUE-20260929-02 第 4 轮）。

动因（合并验证时实测）：金标按定义是 **LF 规范化值**（`layout/_schema.md` 金标表明载
「LF 规范化值；盘面 CRLF 因 `core.autocrlf=true`，字节 md5 …」），而**新检出的 worktree 是 CRLF**
⇒ 直接对盘面字节取 md5 会得到另一个值（同一份内容：LF `a84a1876…` / CRLF `a7a47fb0…`）
⇒ 在 CRLF 检出面上 m06 **假失败**（并给出误导性提示「多半是上一次跑了别的预设」），
m01 则多打一条假警告并无谓重跑一次生成器。
（`git show <rev>:` 取到的是 git 存储形态＝LF，故基线侧本来没有这个问题。）
"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8")

NOTE = (
    "# ★ 第 11 批第 4 轮（合并验证时实测）：**盘面 md5 必须按 LF 规范化后再比**。\n"
    "#   金标（`GOLDEN` / `PRESET_TABLE` / `layout\\_schema.md` 金标表）按定义是 **LF 规范化值**\n"
    "#   （`_schema.md` 金标表明载：「LF 规范化值；盘面 CRLF 因 `core.autocrlf=true`，字节 md5 …」）。\n"
    "#   而**新检出的 worktree 是 CRLF** ⇒ 直接对盘面字节取 md5 会得到另一个值（同一份内容：\n"
    "#   LF `a84a1876…` vs CRLF `a7a47fb0…`）⇒ 在 CRLF 检出面上**假失败**，还会给出误导性提示\n"
    "#   （「多半是上一次跑了别的预设」），诱导人无谓地重跑生成器。\n"
    "#   （`git show <rev>:` 取到的是 git 存储形态＝LF，故基线侧本来就没有这个问题。）\n"
)

HELPER = (
    "\ndef lf_bytes(b):\n"
    '    """把盘面字节按 **LF 规范化**（`core.autocrlf=true` 下检出面可能是 CRLF）——见上方注。"""\n'
    '    return b.replace(b"\\r\\n", b"\\n")\n'
)


def patch(path, anchor, pairs):
    s = io.open(path, encoding="utf-8", newline="").read()
    assert anchor in s, (path, "anchor 不存在")
    assert "def lf_bytes" not in s, (path, "已打过补丁")
    s = s.replace(anchor, NOTE + HELPER + "\n" + anchor, 1)
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:60], s.count(old))
        s = s.replace(old, new)
    io.open(path, "w", encoding="utf-8", newline="").write(s)
    print("  ok", path)


patch("m06_delivered_sample_ledger.py", "def git_show(ref, path_rel):", [
    ('    disk_md5 = hashlib.md5(disk_raw.encode("utf-8")).hexdigest()',
     '    disk_md5 = hashlib.md5(lf_bytes(disk_raw.encode("utf-8"))).hexdigest()'),
])
patch("m01_screen1_appearance_diff.py", "def git_show_head(path_rel):", [
    ('    got = hashlib.md5(open(SCREEN, "rb").read()).hexdigest()',
     '    got = hashlib.md5(lf_bytes(open(SCREEN, "rb").read())).hexdigest()'),
    ('    got2 = hashlib.md5(open(SCREEN, "rb").read()).hexdigest()',
     '    got2 = hashlib.md5(lf_bytes(open(SCREEN, "rb").read())).hexdigest()'),
])
print("done")
