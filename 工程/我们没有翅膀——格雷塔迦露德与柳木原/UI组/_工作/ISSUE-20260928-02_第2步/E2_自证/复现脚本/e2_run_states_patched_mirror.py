# -*- coding: utf-8 -*-
"""E2（第 2 步）· `--preset states` 巡演用的**镜像修正**运行器（只动运行目录，不动仓库）

背景（**生成器阻塞项**，详见 E2 报告）：
    工具\\gen_layout.py 生成 krkr\\game\\ui_layout.tjs 时，把 `flags_default` 里
    **带点的键**写成了  `"fc.state.0001": "locked",`  这种形式。
    而 TJS2 的**内联字典**语法（源码 `tjs2/syntax/tjs.y` 的 `dic_elm`）只接受
        `T_SYMBOL ":" expr`        ← 键必须是**裸标识符**
      | `expr_no_comma "," expr`   ← 或「键, 值」两元素逗号形式
    ⇒ **带引号的字符串键在内联字典里是语法错误**。实机证据：`--preset states` 的
    `ui_layout.tjs` 第 22293 行（＝第一条 `"fc.state.0001"`）报
        `语法有误 （syntax error） at line 22293`
    ⇒ `execStorage FAIL : ui_layout.tjs` ⇒ `[UI] FATAL : UI 组件库装载失败` ⇒ 弹
    `System.inform` 模态框（进程不退，必须 taskkill）。**默认预设不受影响**（它的
    `flags_default` 只有裸键 `fc_layer: "main"`）。

本脚本做什么：
    把**运行目录镜像**里的 `ui_layout.tjs` 按**语义等价**的方式改写为合法形式
        `"fc.state.0001": "locked",`  →  `"fc.state.0001", "locked",`
    再启动引擎跑巡演。**目的**：绕开生成器序列化缺陷，拿到「五态节点 + 三档连线同屏」
    的实机图，以验证 E2 的**环绘制路径**与两端硬判据。**仓库内一字未改**
    （只写 临时\\ui_run\\ 这个每次运行都会被覆盖的镜像目录；`git status` 可证）。

★ 为什么支持 `--layout <快照>`：
    本 worktree 是**多模块并行**作业，另一个模块（数据层）会随时重跑
    `gen_flow_layout.py` / `gen_layout.py` 把屏文件恢复成别的预设 —— 实测
    「现场生成 states → 立刻镜像」在 2 分钟内就被覆盖过。故推荐流程：
      ① `python 工具/gen_flow_layout.py --preset states && python 工具/gen_layout.py`
      ② **立刻**把 `krkr/game/ui_layout.tjs` 复制成快照（放到 临时\\ 下，不入库）；
      ③ 本脚本 `--layout <快照>` 构建镜像 ⇒ 与其它模块的写操作彻底解耦。

用法（在 UI组 目录下）：
    python "_工作/ISSUE-20260928-02_第2步/E2_自证/复现脚本/e2_run_states_patched_mirror.py" ^
           --layout "<worktree>\\临时\\e2_states_snapshot\\ui_layout.tjs"
    python ... --layer frag1            # 顺带强制 fc_layer
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = <UI组>\_工作\ISSUE-20260928-02_第2步\E2_自证\复现脚本
UI = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(UI, "krkr")

# 值本身也是**带引号字符串**（`"fc.state.0001": "locked",`）⇒ 值类必须允许引号；
# 且**最后一条元素没有尾逗号**（`%[ a: 1, b: 2 ]`）⇒ 逗号可选。
# 两个坑都真踩过（都经实机复现）：
#   ① 只改带尾逗号的行 ⇒ 剩下最后一行仍非法、照样语法错（改写 12/13 行，引擎仍 FATAL）；
#   ② 值类里排除引号     ⇒ 一行都匹配不上（改写 0/13，引擎仍 FATAL）。
KEY_RE = re.compile(rb'^(\s*)"([^"\r\n]+)"\s*:\s*("[^"\r\n]*")(,?)(\r?)$', re.M)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def find_run_dir():
    """运行目录镜像（run_autotour.bat 里 RUN = <WTROOT>\\临时\\ui_run）

    实测落点 = `<worktree>\\临时\\ui_run`（worktree 根 = UI组 上溯 3 层）；
    为稳妥起见把 UI组 上溯 1..5 层的 `临时\\ui_run` 全列成候选，取第一个带 exe 的。
    """
    cands = [os.path.join(UI, "临时", "ui_run")]
    d = UI
    for _ in range(5):
        d = os.path.dirname(d)
        cands.append(os.path.join(d, "临时", "ui_run"))
    for c in cands:
        if os.path.isfile(os.path.join(c, "runtime", "tvpwin32.exe")):
            return c
    raise SystemExit("找不到运行目录（试过）：%r" % cands)


def patch_dotted_keys(path):
    """把内联字典里 `"k": v,` 改成 TJS2 合法的 `"k", v,`；返回改写行数与样例。"""
    raw = open(path, "rb").read()
    hits = []

    def sub(m):
        hits.append(m.group(0))
        return (m.group(1) + b'"' + m.group(2) + b'", ' + m.group(3)
                + m.group(4) + m.group(5))

    out = KEY_RE.sub(sub, raw)
    if hits:
        open(path, "wb").write(out)
    return len(hits), hits


def main():
    layer = ""
    if "--layer" in sys.argv:
        layer = sys.argv[sys.argv.index("--layer") + 1]
    snapshot = ""
    if "--layout" in sys.argv:
        snapshot = os.path.abspath(sys.argv[sys.argv.index("--layout") + 1])
        if not os.path.isfile(snapshot):
            raise SystemExit("快照不存在：%s" % snapshot)

    run = find_run_dir()
    print("[RUN]", run)
    game = os.path.join(run, "game")
    runtime = os.path.join(run, "runtime")
    savedata = os.path.join(runtime, "savedata")
    if os.path.isdir(game):
        shutil.rmtree(game)
    if os.path.isdir(savedata):
        for f in os.listdir(savedata):
            p = os.path.join(savedata, f)
            if os.path.isfile(p):
                os.remove(p)
    if not os.path.isdir(os.path.join(runtime, "plugin")):
        shutil.copytree(os.path.join(SRC, "runtime"), runtime, dirs_exist_ok=True)
    shutil.copytree(os.path.join(SRC, "plugin"), os.path.join(runtime, "plugin"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(SRC, "game"), game)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(game, "assets"))
    open(os.path.join(game, "autotour.txt"), "w").write("autotour")
    if layer != "":
        open(os.path.join(game, "quick_flags.tjs"), "w").write(
            'UIScrFlagForce["fc_layer"] = "%s";\n' % layer)
        print("[layer] forced fc_layer =", layer)

    lay = os.path.join(game, "ui_layout.tjs")
    if snapshot != "":
        shutil.copyfile(snapshot, lay)
        print("[data] 快照 ui_layout.tjs md5 =", md5(snapshot))
    print("[data] 源屏数据 md5 =", md5(os.path.join(UI, "layout", "screens", "32_flowchart.json")),
          "(记下它：其它模块可能正在重生成)")
    print("[data] 源 ui_layout.tjs md5 =", md5(os.path.join(SRC, "game", "ui_layout.tjs")))
    print("[data] 镜像 ui_layout.tjs md5(改前) =", md5(lay))
    n, hits = patch_dotted_keys(lay)
    print("[patch] 镜像 ui_layout.tjs 改写 %d 行（内联字典的引号键 → 逗号形式）" % n)
    for h in hits[:4]:
        print("        ", h.decode("utf-8", "replace").rstrip())
    if n == 0:
        print("        （本预设没有引号键 ⇒ 未改写）")
    else:
        print("[data] 镜像 ui_layout.tjs md5(改后) =", md5(lay))

    exe = os.path.join(runtime, "tvpwin32.exe")
    if "--noplugin" in sys.argv:
        # ★ 负向对照：把镜像里的 layerExDraw.dll 删掉 ⇒ 连线与 `current` 环都必须**优雅降级**
        #   （不画、打一行、**不崩**）。用共享的 `uiFlowLinkEnsure()` 探测路径。
        killed = []
        for p in (os.path.join(runtime, "plugin", "layerExDraw.dll"),
                  os.path.join(game, "layerExDraw.dll")):
            if os.path.isfile(p):
                os.remove(p)
                killed.append(p)
        print("[noplugin] 已移除：", killed)
    DETACHED = 0x00000008 | 0x00000200
    subprocess.Popen([exe, game], cwd=runtime, creationflags=DETACHED, close_fds=True)
    print("[launch]", exe, game)
    print("[poll]  ", os.path.join(savedata, "krkr.console.log"))


if __name__ == "__main__":
    main()
