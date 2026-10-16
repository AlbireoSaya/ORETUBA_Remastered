# -*- coding: utf-8 -*-
r"""e2_reverse_selfcheck.py —— ISSUE-20260929-02 · E2：**豁免集反向自证**（B.6 要求的「集外仍严格拒绝」）

做法：把生成器复制到**同目录**（保证 `__file__` 相对路径解析一致）再打**变异**，从不动真文件：

  变体 A：`STATIC_FLAG_EXEMPT = set()`               ⇒ 载入处 `_dup` 自检必须**如旧报错**；
  变体 B：`STATIC_FLAG_EXEMPT = set()` ＋ 把载入处 `_dup` 的豁免**硬编码**为那两件
          （⇒ 只留落盘前 `shell_flagged` 用空集）      ⇒ 落盘前自检必须报错。

任一变体不报错，说明豁免集把反向自证能力削掉了 ⇒ 脚本判 FAIL。
用法：python "_工作/ISSUE-20260929-02_右栏大改/复现脚本/e2_reverse_selfcheck.py"
"""
from __future__ import annotations

import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …\UI组
TOOLS = os.path.join(UI, "工具")
GEN = os.path.join(TOOLS, "gen_flow_layout.py")
TMPA = os.path.join(TOOLS, "_tmp_e2_exempt_empty_a.py")
TMPB = os.path.join(TOOLS, "_tmp_e2_exempt_empty_b.py")

ENV = dict(os.environ)
ENV["PYTHONPATH"] = r"E:/ZCode Workspace/Galgame/工具/pylibs"

src = io.open(GEN, encoding="utf-8").read()
OLD = 'STATIC_FLAG_EXEMPT = {"fc.pbkick", "fc.pbkick_pause"}'
assert OLD in src, "未找到 STATIC_FLAG_EXEMPT 字面量"
tmpa = src.replace(OLD, "STATIC_FLAG_EXEMPT = set()")
# ★ 只替换**载入处 `_dup`**那一处（含其前导表达式 ⇒ 唯一）；`shell_flagged` 那处**保持**用空集。
#   （踩过的坑：只写 `and e["id"] not in STATIC_FLAG_EXEMPT]` 会**同时命中两处** ⇒ 变异退化为「两处都豁免」，
#     变体 B 会假 PASS —— 这正是本工程「负向对照必须真命中它所声称的那条守卫」的教训。）
NEEDLE = 'if ("vis_flag" in e or "vis_when" in e) and e["id"] not in STATIC_FLAG_EXEMPT]'
assert tmpa.count(NEEDLE) == 1, "载入处 _dup 的锚串在副本里不是唯一（count=%d）" % tmpa.count(NEEDLE)
tmpb = tmpa.replace(NEEDLE, 'if ("vis_flag" in e or "vis_when" in e) and e["id"] not in {"fc.pbkick", "fc.pbkick_pause"}]')
assert tmpb != tmpa, "变体 B 的 _dup 硬编码替换未生效"

io.open(TMPA, "w", encoding="utf-8", newline="\n").write(tmpa)
io.open(TMPB, "w", encoding="utf-8", newline="\n").write(tmpb)

fails = 0
for tag, path, expect in (("A（载入处 _dup）", TMPA, "静态元素快照已带 vis_flag/vis_when"),
                          ("B（落盘前 shell_flagged）", TMPB, "外壳件带层旗标")):
    p = subprocess.run([sys.executable, path, "--dry-run"], cwd=UI, env=ENV,
                       capture_output=True)
    out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
    hit = expect in out
    print("=" * 78)
    print("变体 %s ⇒ exit=%d ｜ 命中期望报错串 %r：%s" % (tag, p.returncode, expect,
                                                    "✓ PASS" if hit else "✗ FAIL"))
    for ln in out.splitlines():
        if "FAIL" in ln or expect in ln:
            print("   ", ln.strip())
    if not hit or p.returncode == 0:
        fails += 1

for f in (TMPA, TMPB):
    if os.path.exists(f):
        os.remove(f)
print("=" * 78)
print("豁免集反向自证：%s（临时副本已删除）" % ("**全部 PASS**（集外仍严格拒绝）" if not fails
                                        else "**FAIL %d 项**" % fails))
sys.exit(1 if fails else 0)
