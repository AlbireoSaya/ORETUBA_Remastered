#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
assemble_game.py —— 装配可运行游戏目录（编程组）
============================================================
把 UI 组交付的 krkr 工程与编程组的模块**合并**成一个可直接启动的游戏目录：

  <out>\game\        ← UI 组 game\*（16 个 tjs）+ 编程组 game\*（ui_boot/ui_audio/ui_story）
                       + story\（剧本数据）+ story_assets\（被引用素材）
                       + assets\ui\、assets\face\（UI 组素材并入 game 内，命中 ui_asset 候选名②）
  <out>\runtime\     ← tvpwin32.exe + plugin\*.dll（含 layerExDraw.dll 与音频 dll）

★ 对 UI 组文件的改动＝在 `startup.tjs` 注入**两处扩展点**（幂等）：① 模块装载完成后
  execStorage("ui_boot.tjs")；② 主窗口建立后调用 uiStoryWindowInit(窗口实例)。
  除新增行外，仅**追加赋值**改写 1 行（`var uiWindow = new UiWindow();` → 同行追加
  ` UIBootWindow = uiWindow;`，语义等价；见一审提示-5 的措辞订正）。UI 组原文件保持权威；
  锚点缺失时**硬失败**（`die`），不静默跳过。

用法：
  python assemble_game.py --data-root "E:/ZCode Workspace/Galgame" --out <dir> [--storyrun]
"""
import argparse, os, shutil, sys

# ★ 发布闸门（ISSUE-20261008-01）：引用 ⊆ story_assets 实件，缺一件即硬失败。
#   与 deploy_product.py 共用 工具\gate_story_assets.py（口径＝M6 scan_missing_assets.py）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_story_assets import enforce_gate, MARKER as NOASSET_MARKER

HOOK1_ANCHOR = 'if(!uiExec("ui_fragment.tjs"))    uiBootOK = false;'
HOOK1 = (
    HOOK1_ANCHOR + "\n"
    "// ==== 编程组扩展点 ①（ISSUE-20261001-01，assemble_game.py 注入；只增不改）====\n"
    "//   一切 UI 模块装载完成后装载编程组模块；ui_boot.tjs 不存在则行为与改动前完全一致。\n"
    "try { if(Storages.isExistentStorage(\"ui_boot.tjs\")) Scripts.execStorage(\"ui_boot.tjs\"); }\n"
    "catch(eGretaBoot1) { Debug.message(\"[BOOT][ERR] 编程组扩展装载失败：\" + eGretaBoot1.message); }"
)
HOOK2_ANCHOR = "\tvar uiWindow = new UiWindow();"
HOOK2 = "\tvar uiWindow = new UiWindow(); UIBootWindow = uiWindow;"
HOOK2_AFTER = (
    "\n// ==== 编程组扩展点 ②（窗口交接）====\n"
    "try { uiStoryWindowInit(UIBootWindow); }\n"
    "catch(eGretaBoot2) { Debug.message(\"[BOOT][ERR] 窗口交接失败：\" + eGretaBoot2.message); }"
)


def die(m):
    print("[FATAL] " + m, file=sys.stderr)
    sys.exit(2)


def sync_tree(src, dst, force=False, skip_top=()):
    """按 size+mtime 增量同步（只复制新增/变化文件）。

    ★ 一审（数据管线）Minor-7：`force=True` 时**无条件复制** —— 编程组的覆盖层必须始终
      胜过 UI 组同名文件，否则「同名同大小且 UI 组更新」会让编程组版本静默失效。
    ★ `skip_top`：按**相对 src 的顶层目录名**跳过（用于诊断构建不搬 3.6 GB 的 story_assets）。
    """
    n = 0
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        if rel == "." and skip_top:
            dirs[:] = [d for d in dirs if d not in skip_top]
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(tgt, f)
            if not force:
                try:
                    if os.path.isfile(d) and os.path.getsize(d) == os.path.getsize(s) \
                            and int(os.path.getmtime(d)) >= int(os.path.getmtime(s)):
                        continue
                except OSError:
                    pass
            shutil.copy2(s, d)
            n += 1
    return n


def patch_startup(path):
    raw = open(path, "rb").read()
    crlf = b"\r\n" in raw
    txt = raw.decode("utf-8").replace("\r\n", "\n")
    if "编程组扩展点" in txt:
        return "already"
    if HOOK1_ANCHOR not in txt:
        die("未找到扩展点①锚点（UI 组 startup.tjs 结构变了？）：%s" % HOOK1_ANCHOR)
    if HOOK2_ANCHOR not in txt:
        die("未找到扩展点②锚点：%s" % repr(HOOK2_ANCHOR))
    txt = txt.replace(HOOK1_ANCHOR, HOOK1, 1)
    txt = txt.replace(HOOK2_ANCHOR, HOOK2, 1)
    # 扩展点②：主窗口建立语句在文件末尾，直接在文件尾追加（保证在窗口建立之后执行）
    if not txt.endswith("\n"):
        txt += "\n"
    txt += HOOK2_AFTER + "\n"
    # 声明 UIBootWindow（避免未声明标识符）
    txt = txt.replace("try\n{\n" + HOOK2, "var UIBootWindow = void;\ntry\n{\n" + HOOK2, 1)
    if "var UIBootWindow = void;" not in txt:
        die("UIBootWindow 声明注入失败")
    out = txt.replace("\n", "\r\n") if crlf else txt
    open(path, "wb").write(out.encode("utf-8"))
    return "patched(crlf)" if crlf else "patched(lf)"


def main():
    here = os.path.dirname(os.path.abspath(__file__))          # <proj>\编程组\工具
    proj_default = os.path.dirname(os.path.dirname(here))     # <proj>
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=r"E:\ZCode Workspace\Galgame",
                    help="只读数据根（美术交付层/素材库在此，通常=主工作区）")
    ap.add_argument("--proj", default=proj_default,
                    help="本 checkout 的工程目录（含 UI组\\、编程组\\）；默认取脚本自身位置")
    ap.add_argument("--out", required=True)
    ap.add_argument("--storyrun", action="store_true", help="放 storyrun.txt（无人值守剧情自测）")
    ap.add_argument("--no-assets", action="store_true", help="跳过 UI 素材同步（快速迭代）")
    ap.add_argument("--no-story-assets", action="store_true",
                    help="跳过 3.6 GB 的 story_assets 同步（**仅供机检/诊断构建**："
                         "流程图屏只吃 UI 素材，不依赖它；正式部署不得带此开关）")
    ap.add_argument("--diagnostic-build", action="store_true",
                    help="显式确认这是**诊断构建**（才允许 --no-story-assets）；"
                         "会在装配根写标记文件 %s，deploy_product.py 见到即拒绝部署" % NOASSET_MARKER)
    args = ap.parse_args()

    # ★ 发布闸门之开关纪律（ISSUE-20261008-01）：草案里的 99 件悬空引用，根因就是
    #   生产装配带了 `--no-story-assets`（跳过整棵 story_assets）却照常当成品部署。
    #   ⇒ 该开关**必须**另配 `--diagnostic-build` 才放行；否则拒跑（非零退出）。
    #   放行的诊断构建会落标记文件，由 deploy_product.py 兜底拒绝部署。
    if args.no_story_assets and not args.diagnostic_build:
        die("--no-story-assets 属诊断开关，正式装配**不得**使用（会跳过 story_assets ⇒ "
            "成品出现悬空素材引用，见 ISSUE-20261008-01 的 99 件）。"
            "确为诊断构建请显式加 --diagnostic-build（该产物会被 deploy_product.py 拒绝部署）。")

    proj = os.path.abspath(args.proj)
    ui_krkr = os.path.join(proj, "UI组", "krkr")
    prog_krkr = os.path.join(proj, "编程组", "krkr")
    out = os.path.abspath(args.out)
    if not os.path.isdir(ui_krkr):
        die("UI krkr 目录不存在：%s" % ui_krkr)
    if not os.path.isdir(prog_krkr):
        die("编程组 krkr 目录不存在：%s" % prog_krkr)

    game = os.path.join(out, "game")
    rt = os.path.join(out, "runtime")
    os.makedirs(game, exist_ok=True)
    os.makedirs(rt, exist_ok=True)

    # 诊断构建标记：只要带了 --no-story-assets（已由上方确认是 --diagnostic-build），
    # 就在装配根留下标记，供 deploy_product.py **拒绝部署**（诊断产物不得当成品）。
    if args.no_story_assets:
        with open(os.path.join(out, NOASSET_MARKER), "w", encoding="ascii", newline="\n") as _mf:
            _mf.write("diagnostic build: story_assets skipped (--no-story-assets)\n")
        print("[warn] 诊断构建：已跳过 story_assets，并落标记 %s（deploy 将拒部署）" % NOASSET_MARKER)
    elif os.path.isfile(os.path.join(out, NOASSET_MARKER)):
        os.remove(os.path.join(out, NOASSET_MARKER))   # 正常装配清掉旧诊断标记

    # 1) UI 组 game\*.tjs → build\game
    n1 = sync_tree(os.path.join(ui_krkr, "game"), game)
    # 2) 编程组 game\*（含 story\、story_assets\）覆盖上去——**无条件覆盖**（编程组层优先）
    pg = os.path.join(prog_krkr, "game")
    skip = ("story_assets",) if args.no_story_assets else ()
    n2 = sync_tree(pg, game, force=True, skip_top=skip) if os.path.isdir(pg) else 0
    # 3) UI 素材并入 game\assets（命中 ui_asset 候选名② assets/…）
    n3 = 0
    if not args.no_assets:
        n3 = sync_tree(os.path.join(ui_krkr, "assets"), os.path.join(game, "assets"))
    # 4) runtime（exe + plugin）
    n4 = sync_tree(os.path.join(ui_krkr, "runtime"), rt)
    # 4b) krkr\plugin\（layerExDraw.dll 等）→ runtime\plugin
    n5 = sync_tree(os.path.join(ui_krkr, "plugin"), os.path.join(rt, "plugin"))

    # 4c) ★ G2：随包内嵌中文字体兜底（Ark Pixel，OFL-1.1）——见 ui_boot 的 [FONT] 逻辑
    font_src = os.path.join(args.data_root, "工具", "pixel-fonts")
    if os.path.isdir(font_src):
        fdst = os.path.join(game, "fonts")
        os.makedirs(fdst, exist_ok=True)
        for fn in ("ark-pixel-16px-monospaced-zh_cn.ttf",):
            s2 = os.path.join(font_src, fn)
            if os.path.isfile(s2):
                shutil.copy2(s2, os.path.join(fdst, fn))
        lic = os.path.join(font_src, "OFL.txt")
        if os.path.isfile(lic):
            shutil.copy2(lic, os.path.join(fdst, "OFL_ark-pixel.txt"))

    # ★ 发布闸门（硬失败）：装配树已成，落盘完成前核「剧本引用 ⊆ story_assets 实件」。
    #   诊断构建（--no-story-assets）本就无 payload ⇒ 跳过（其标记已保证 deploy 拒部署）。
    if not args.no_story_assets:
        enforce_gate(game, label="装配闸门（assemble_game）")

    # 5) 打补丁
    st = patch_startup(os.path.join(game, "startup.tjs"))

    # 6) 自测开关
    flag = os.path.join(game, "storyrun.txt")
    flag_auto = os.path.join(game, "autotour.txt")
    if os.path.isfile(flag_auto):
        os.remove(flag_auto)          # 自测时不得与 UI 组巡演同时开
    if args.storyrun:
        with open(flag, "w", encoding="ascii", newline="\n") as f:
            f.write("storytest\n")
    elif os.path.isfile(flag):
        os.remove(flag)

    print("[ok] 装配完成 → %s" % out)
    print("     UI game %d / 编程组覆盖 %d / UI素材 %d / runtime %d / plugin %d | startup=%s"
          % (n1, n2, n3, n4, n5, st))
    print("     启动：%s" % os.path.join(rt, "tvpwin32.exe"))


if __name__ == "__main__":
    main()
