# -*- coding: utf-8 -*-
"""把运行副本 ui_dialog.tjs 的折行结果打到日志（仅用于验证，产物只落在 临时）。"""
import sys

p = sys.argv[1]
s = open(p, "rb").read().decode("utf-8")
a1 = "var part = uiDialogPartialLines(stage, el, full, UIDlgTyped);"
a2 = 'ctx.textOverride[id] = part.lines.join("' + chr(92) + 'n");'
assert a1 in s and a2 in s, "anchor missing"
NL = chr(92) + "n"
new = (
    "\t\t\t" + a1 + "\n"
    "\t\t\ttry {\n"
    '\t\t\t\tvar _d = "";\n'
    "\t\t\t\tfor(var _k = 0; _k < part.lines.count; _k++)\n"
    '\t\t\t\t\t_d = _d + " [" + _k + "|" + ("" + part.lines[_k]).length + "]" + ("" + part.lines[_k]);\n'
    '\t\t\t\tDebug.message("[UI][M25WRAP] typed=" + UIDlgTyped + "/" + full.length\n'
    '\t\t\t\t\t+ " w=" + el.w + " maxlines=" + el.max_lines + " trunc=" + part.truncated\n'
    '\t\t\t\t\t+ " lines=" + part.lines.count + _d);\n'
    '\t\t\t} catch(_e) { Debug.message("[UI][M25WRAP][ERR] " + _e.message); }\n'
    "\t\t\t" + a2
)
s = s.replace(a1 + "\n\t\t\t" + a2, new)
open(p, "wb").write(s.encode("utf-8"))
print("patched wrap logging OK")