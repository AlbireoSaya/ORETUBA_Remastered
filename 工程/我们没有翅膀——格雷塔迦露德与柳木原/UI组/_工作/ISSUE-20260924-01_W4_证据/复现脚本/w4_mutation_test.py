# -*- coding: utf-8 -*-
r"""W4 · 变异自证（打废「slider → 设置仓 → 遮罩」链路，自检必须报出来）

■ 判据
  每一处变异都改 `复刻\replica.js` 的一行（改前先备份到本证据目录），跑
  `_工作\ISSUE-20260923-01_M39_证据\复现脚本\m39_run_html_selftests.py --only A`，
  看 `_selftest_states.html` 的 ⑲ 段是否**报失败**。跑完**必须还原并逐字节校验**。

■ 四条变异（源自本轮实测抓到的真缺陷与契约点）
  m1 手柄漏减 wrap 原点   —— 首版真 bug（手柄整体偏一个元素 x，winopac 偏 307px）
  m2 renderScreen 不灌设置仓 —— 「实时生效」的时机链（方案 §三.3）
  m3 设置仓不 clamp/对齐  —— 期望**不报警**（拖动路径上游已 clamp，本变异不改变行为）⇒ 覆盖边界
  m4 切页不派生值 flag    —— 主代理 2026-09-24 追加规则（非本页值元素必须 display:none）

■ 用法
    python _工作\ISSUE-20260924-01_W4_证据\复现脚本\w4_mutation_test.py
"""
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.dirname(HERE)
UI = os.path.dirname(os.path.dirname(EVID))
SRC = os.path.join(UI, "复刻", "replica.js")
BAK = os.path.join(EVID, "replica_原始备份.js")          # 备份落在**工作区内**（铁律 1）
RUNNER = os.path.join(UI, "_工作", "ISSUE-20260923-01_M39_证据", "复现脚本",
                      "m39_run_html_selftests.py")

MUTS = [
    ("m1 手柄漏减 wrap 原点",
     "knob.style.left = px(sliderXOf(e, v) - Math.floor(SLIDER_KNOB / 2) - ox);",
     "knob.style.left = px(sliderXOf(e, v) - Math.floor(SLIDER_KNOB / 2));"),
    ("m2 renderScreen 不灌设置仓",
     "      applySettingOverrides();\n      syncScreenChrome(id);",
     "      syncScreenChrome(id);"),
    ("m3 设置仓不 clamp/对齐",
     "    state.settings[k] = nv;",
     "    state.settings[k] = Number(value);"),
    ("m4 切页不派生值 flag",
     "      var dnum = configDerivePageFlags(page);",
     "      var dnum = 0;"),
    ("m5 进屏不派生（补单①）",
     "      configFlagsInitFor(id);\n",
     "      /* __mut5：进屏那一刻不再派生值 flag __*/\n"),
    # ---- M47 第三轮（一审打回 C2/C3）：「改前」行为的等价复现，用来证明新断言真的钉住了缺陷 ----
    ("m6 初始化不清记忆（C2 改前）",
     "      configMemoClear();\n",
     ""),
    ("m6b 初始化只 ResetAll（C2 改前，9 键时代）",
     "      var nres = settingResetAll();\n      configMemoClear();",
     "      var nres = 0;\n      SETTING_KEYS.slice(0, 9).forEach(function (k) {\n"
     "        state.settings[k] = SETTING_DEF[k].def; sliderSyncSetting(k, SETTING_DEF[k].def); nres++;\n"
     "      });\n      configMemoClear();"),
    ("m7 角色选中不派生（C3 改前）",
     "      configDerivePageFlags(getFlag('cfg_page'));   // ★ 非本页 ⇒ 只进记忆、不上屏\n",
     ""),
    ("m8 进屏捕获记忆（C4 改前）",
     "    return configDerivePageFlags(getFlag('cfg_page'), false);   // ★ false = 不捕获记忆（见上）",
     "    return configDerivePageFlags(getFlag('cfg_page'));"),
]


def run_a():
    r = subprocess.run([sys.executable, RUNNER, "--only", "A"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=UI)
    out = r.stdout.decode("utf-8", "replace")
    fails = [re.sub(r"\s+", " ", l.strip()) for l in out.splitlines() if "SELFTEST FAIL " in l]
    m = re.search(r"判定：(\S+)", out)
    return (m.group(1) if m else "?"), fails


def main():
    src = io.open(SRC, encoding="utf-8").read()
    io.open(BAK, "w", encoding="utf-8").write(src)
    print("原始备份 -> " + BAK)
    print()
    rows = []
    for name, old, new in MUTS:
        assert old in src, "变异锚点未找到：" + name
        io.open(SRC, "w", encoding="utf-8").write(src.replace(old, new))
        verdict, fails = run_a()
        caught = [f for f in fails if "⑲" in f]
        rows.append((name, verdict, len(caught), caught[:2]))
        for f in caught[:2]:
            print("   " + f[:190])
        print("  -> %-26s 判定=%s" % (name, verdict))
        print()
    # 还原
    io.open(SRC, "w", encoding="utf-8").write(src)
    ok = (io.open(SRC, encoding="utf-8").read() == src)
    os.remove(BAK)
    print("已还原 replica.js（逐字节一致=%s），备份已删除" % ok)
    print()
    print("变异 | 套 A 判定 | 被抓的 ⑲ 断言数")
    for name, verdict, n, _ in rows:
        print("  %-26s | %-24s | %d" % (name, verdict, n))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
