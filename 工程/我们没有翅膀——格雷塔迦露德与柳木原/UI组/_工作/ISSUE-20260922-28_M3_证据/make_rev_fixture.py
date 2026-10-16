# -*- coding: utf-8 -*-
"""M3 / C1 反向验证夹具生成器（**证据用，不参与交付**）。

目的：证明 C1 修好后的两条断言**真的会 FAIL**（可证伪），并对照「旧写法为什么会假通过」。
做法：把 复刻/replica.js 复制到本目录并打两处补丁——

  patch R1（渲染器退化）：让**一件**零 nine 元素（`sv.tab_a`）改走 border-image 分支
      （等价于「渲染器不再对全零 nine 走 <img>」的真实缺陷）。
  patch R2（旧写法对照）：在 ⑨ 异步段的断言旁，补上**旧写法的两条断言**（REV-old-*）：
      · `stretched === znImgs.length`  —— 自指恒真（znImgs 是过滤后的子集）
      · `znOk === 13`                  —— 硬编码主语数
      这样同一份输出里就能同时看到「旧写法 PASS / 新写法 FAIL」，差别一目了然。

另支持 `?revhack=drop`（由 rev.html 读取）：把 `sv.tab_a` 从 save 屏数据里删掉，
  模拟「数据一变就假失败」——旧写法（硬编码 13）FAIL、新写法（数据推导 12）PASS。

**H3 反向验证（Esc 行为）**：另外生成 `replica_rev_esc.js` —— 把 Esc 的键位映射**换回旧行为**
  （`doAction('open_sysmenu')`，即「Esc = 展开竖条」），配 `rev_esc.html` 跑同一套断言：
  三条 `esc.*` 断言应全部 FAIL（证明它们真的在验"键位映射"，不是恒真）。

用法：python make_rev_fixture.py
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, "..", ".."))                # <UI组>
SRC = os.path.join(UI, "复刻", "replica.js")
DST = os.path.join(HERE, "replica_rev.js")
DST_ESC = os.path.join(HERE, "replica_rev_esc.js")

t = io.open(SRC, encoding="utf-8").read()

# ---- patch R1：把 sv.tab_a 强制走 border-image（模拟「全零 nine 不再走 <img>」）
a1 = "    if (e.nine && !isZeroNine(e.nine)) {"
assert t.count(a1) == 1, "锚点 R1 不唯一：%d" % t.count(a1)
t = t.replace(a1,
               "    if (e.nine && (!isZeroNine(e.nine)\n"
               "                 || (window.__REV_FORCE_NINE && e.id === 'sv.tab_a')"
               ")) {   /* REV R1 */")

# ---- patch R2：补上旧写法断言（与新增法同段，变量在作用域内）
a2 = "      chk('zeronine.size-differs-from-png-still-rendered',"
assert t.count(a2) == 1, "锚点 R2 不唯一：%d" % t.count(a2)
old_asserts = """      /* —— 反向验证用（REV R2）：复现 C1 修之前的两种写法 —— */
      chk('REV-old-stretch-self-referential', stretched === znImgs.length,
          '旧写法 stretched(' + stretched + ') === znImgs.length(' + znImgs.length + ') ⇒ '
          + ((stretched === znImgs.length) ? 'PASS（**假通过**：被破坏的那件不在 znImgs 里）' : 'FAIL'));
      var allIdsOld = ['sv.thumb1', 'sv.thumb2', 'sv.thumb3', 'sv.thumb4', 'sv.thumb5', 'sv.thumb6',
                       'sv.thumb7', 'sv.thumb8', 'sv.thumb9', 'sv.thumb10', 'sv.thumb11', 'sv.thumb12',
                       'sv.tab_a'];
      chk('REV-old-hardcoded-13', znOk === 13,
          '旧写法 znOk(' + znOk + ') === 硬编码 13（实际主语 ' + zeroNineIds.length + ' 件）');
"""
t = t.replace(a2, old_asserts + a2)

io.open(DST, "w", encoding="utf-8", newline="\n").write(t)
print("已生成：%s（%d 字节）" % (DST, len(t)))

# ---- patch H3：把 Esc 的键位映射换回「旧行为（Esc = 展开竖条）」
a3 = "        escBack();                                                     /* ②③ 见 escBack() */"
assert t.count(a3) == 1, "锚点 H3 不唯一：%d" % t.count(a3)
t_esc = t.replace(a3, "        doAction('open_sysmenu');   /* REV H3：旧行为（Esc = 展开竖条） */")
io.open(DST_ESC, "w", encoding="utf-8", newline="\n").write(t_esc)
print("已生成：%s（%d 字节）" % (DST_ESC, len(t_esc)))
