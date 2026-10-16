# -*- coding: utf-8 -*-
"""解决 run_pressprobe.bat 的合并冲突（只动 Usage 注释块；GBK + CRLF 必须保持）

两边各自改了相邻行：
  · 本分支（M46）：默认探针 ch.hit_1 → title.menu_hit_1（原默认元素随 M45f 消失）
  · 对方分支（ISSUE-20260923-14）：示例 sysbar.hit_snap → title.menu_hit_1（该屏已删）
解决＝两边意图都保留；注释全 ASCII（该文件是 GBK + CRLF 且 cmd.exe 按 OEM 码页解析）。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # …/UI组
P = os.path.join(UI, "krkr", "run_pressprobe.bat")

RESOLVED = (
    b'rem    run_pressprobe.bat                        default probe = title.menu_hit_1\r\n'
    b'rem    set PROBE=title.menu_txt_start  then run_pressprobe.bat\r\n'
    b'rem    (prior examples "ch.hit_1" / "sysbar.hit_snap" retired 2026-09-23:\r\n'
    b'rem     ch.hit_1 vanished with the M45f list change, and screen id "sysbar"\r\n'
    b'rem     was deleted -- its art is kept, see the UI group _work archive.\r\n'
    b'rem     Per-item list states are covered by the tour "ptr" steps instead:\r\n'
    b'rem     this probe only takes an element id, not an item index.)\r\n'
)

b = open(P, "rb").read()
i = b.find(b"<<<<<<<")
j = b.find(b">>>>>>>")
assert i > 0 and j > i, "没有冲突块"
k = b.index(b"\n", j) + 1
out = b[:i] + RESOLVED + b[k:]
assert b"<<<<<<< " not in out and b">>>>>>> agent" not in out and b"\n=======\n" not in out, "仍有冲突标记"
out.decode("gbk")                                   # 必须仍是合法 GBK
assert out.count(b"\n") - out.count(b"\r\n") == 0, "出现 LF-only 行"
assert sum(1 for x in out if x > 127) <= 4, "非 ASCII 字节数异常（该文件应基本纯 ASCII）"
open(P, "wb").write(out)
print("冲突已解决：CRLF %d 行 / 非 ASCII %d 字节"
      % (out.count(b"\r\n"), sum(1 for x in out if x > 127)))
