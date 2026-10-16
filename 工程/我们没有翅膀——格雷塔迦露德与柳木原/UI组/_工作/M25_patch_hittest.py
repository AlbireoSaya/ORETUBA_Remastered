# -*- coding: utf-8 -*-
"""给运行副本打「九宫格命中自检」补丁：在 uiDialogDraw 首帧对 9 个图标格中心
各跑一次命中判定并打日志（仅用于验证，产物只落在 临时）。"""
import sys

p = sys.argv[1]
raw = open(p, "rb").read()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")

a = ("function uiDialogDraw(stage, screen)\n"
     "{\n"
     "\tif(screen === void || screen.elements === void) return 0;\n")
assert a in s, "anchor missing"

probe = ("var UIProbe25 = false;\n" + a +
         "\t// M25 self-test (temp copy only)\n"
         "\tif(UIProbe25 !== true)\n"
         "\t{\n"
         "\t\tUIProbe25 = true;\n"
         "\t\tvar _els = screen.elements;\n"
         "\t\tfor(var _i = 0; _i < _els.count; _i++)\n"
         "\t\t{\n"
         "\t\t\tvar _e = _els[_i];\n"
         "\t\t\tif(_e === void || _e.id === void) continue;\n"
         "\t\t\tif(('' + _e.id).indexOf('.icon_hit_') < 0) continue;\n"
         "\t\t\tvar _r = uiWidgetRect(_e);\n"
         "\t\t\tvar _res = uiDialogClick(stage, screen, _r.x + _r.w / 2, _r.y + _r.h / 2);\n"
         "\t\t\tDebug.message('[UI][M25HIT] ' + _e.id + ' center=' + (_r.x + _r.w / 2) + ',' + (_r.y + _r.h / 2)\n"
         "\t\t\t\t+ ' -> action=' + _res.action + ' hit=' + _res.hit);\n"
         "\t\t}\n"
         "\t\tvar _t = uiDialogClick(stage, screen, 700, 900);\n"
         "\t\tDebug.message('[UI][M25HIT] text-area(700,900) -> action=' + _t.action + ' hit=' + _t.hit);\n"
         "\t\tvar _g = uiDialogClick(stage, screen, 100, 300);\n"
         "\t\tDebug.message('[UI][M25HIT] above-window(100,300) -> action=' + _g.action + ' hit=' + _g.hit);\n"
         "\t}\n")

s = s.replace(a, probe, 1)
if crlf:
    s = s.replace("\n", "\r\n")
open(p, "wb").write(s.encode("utf-8"))
print("patched M25 hit self-test OK (uiDialogDraw hook)")