# -*- coding: utf-8 -*-
"""E2（第 2 步）复现脚本：给 krkr/run_autotour.bat 加「强制流程图层」的可选参数

用法（无参 = 与改动前逐字节等价的行为）：
    cmd //c "krkr\\run_autotour.bat"
    cmd //c "krkr\\run_autotour.bat frag1"     <- 强制 fc_layer=frag1（独立层截图）
幂等：已打过则第二次运行会断言失败（说明已存在）。
"""
import io
import os

P = os.path.join("krkr", "run_autotour.bat")

OLD_DOC = (
    "rem     ui_state.txt / ui_flow_state.txt\r\n"
    "rem\r\n"
    "rem  Expected runtime: about 45 seconds for 19 screens.\r\n"
)

NEW_DOC = (
    "rem     ui_state.txt / ui_flow_state.txt\r\n"
    "rem\r\n"
    "rem  Expected runtime: about 45 seconds for 19 screens.\r\n"
    "rem\r\n"
    "rem  ------------------------------------------------------------\r\n"
    "rem   [NEW - ISSUE-20260928-02 第 2 步] 可选参数 1 = 强制流程图层\r\n"
    "rem     usage:  run_autotour.bat            (无参：不强制)\r\n"
    "rem             run_autotour.bat frag1      (强制 fc_layer=frag1 -> 番外独立层截图)\r\n"
    "rem     做法：写 RUN\\game\\quick_flags.tjs，内容\r\n"
    "rem               UIScrFlagForce[\"fc_layer\"] = \"<arg>\";\r\n"
    "rem           startup.tjs 的 uiInitQuickFlags() 用项目根 flag 文件机制执行它（本轮实测\r\n"
    "rem           唯一可用的外部开关），在 flags_default 之后套用 => 换屏也保留；日志会打\r\n"
    "rem           `[UI][QBAR] quickflags 已生效： fc_layer='frag1'`。\r\n"
    "rem     为什么需要它：番外独立层的「零点击截图」要由**屏级 flag 机制**给出（不靠脚本\r\n"
    "rem           伪造状态）；再由巡演的 flowclick 步骤点「返回主干」切回 main 取第二张。\r\n"
    "rem     注意：文件写在**运行目录的镜像工程根**里，源码树的 game\\ 不会被污染\r\n"
    "rem           （每次运行 [2/6] 会 rd /s /q 清掉镜像，源树本来也没有该文件）。\r\n"
    "rem  ------------------------------------------------------------\r\n"
)

OLD_WRITE = (
    "echo [5/6] enabling auto-tour (project root autotour.txt) ...\r\n"
    "echo autotour>\"%RUN%\\game\\autotour.txt\"\r\n"
)

NEW_WRITE = (
    "echo [5/6] enabling auto-tour (project root autotour.txt) ...\r\n"
    "echo autotour>\"%RUN%\\game\\autotour.txt\"\r\n"
    "\r\n"
    "rem ------------------------------------------------------------\r\n"
    "rem  [5b/6] optional forced flowchart layer (ISSUE-20260928-02 第 2 步)\r\n"
    "rem    arg1 非空 => 写 quick_flags.tjs（UIScrFlagForce[\"fc_layer\"]=<arg1>）。\r\n"
    "rem    无参 => 什么都不做（行为与改动前一致）。\r\n"
    "rem    NOTE: no parentheses inside the echo lines (an unescaped \")\" would close\r\n"
    "rem          the if-block), and the redirect goes first so cmd does not echo it.\r\n"
    "rem ------------------------------------------------------------\r\n"
    "if not \"%~1\"==\"\" (\r\n"
    "  echo [5b/6] forcing flowchart layer fc_layer=%~1 via quick_flags.tjs ...\r\n"
    "  >\"%RUN%\\game\\quick_flags.tjs\" echo UIScrFlagForce[\"fc_layer\"] = \"%~1\";\r\n"
    ") else (\r\n"
    "  echo [5b/6] no forced flowchart layer - quick_flags.tjs not written.\r\n"
    ")\r\n"
)


def main():
    s = io.open(P, encoding="gbk", newline="").read()
    for label, old, new in (("doc", OLD_DOC, NEW_DOC), ("write", OLD_WRITE, NEW_WRITE)):
        n = s.count(old)
        assert n == 1, "%s : found %d (expected 1)" % (label, n)
        s = s.replace(old, new)
        print("ok:", label)
    io.open(P, "w", encoding="gbk", newline="").write(s)
    print("patched:", P)


if __name__ == "__main__":
    main()
