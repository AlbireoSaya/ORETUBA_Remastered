#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
deploy_product.py —— 部署成品到 `成品\<中文译名>\`（编程组）
============================================================
按 AGENTS §六：
  * 成品＝**可直接游玩的完整交付物**，脱离 `工程\` 与原始目录也能跑；
  * **只放成品，不放过程**（脚本、日志、解包散件一律留在 `工程\`）；
  * 附 `成品说明.md`（改了哪些文件 / 行为变化 / 已知问题 / 运行方式 / 原版位置）；
  * **同名冲突不得静默覆盖**：已存在则要求显式 `--overwrite`，否则改名留档。

做法：把装配好的 `编程组\build\{game,runtime}` 拷成
      `<工作区>\成品\<译名>\{game,runtime}` + `成品说明.md` + `play.bat`。
      清掉调试开关与运行痕迹（storyrun/forcefilefont/videoprobe/storytest_interval/savedata 内容）。

用法：
  python -X utf8 工具/deploy_product.py [--out <工作区>成品目录] [--overwrite]
"""
import argparse, datetime, os, re, shutil, subprocess, sys

# ★ 发布闸门（ISSUE-20261008-01）：与 assemble_game.py 共用，部署**落盘前**核
#   「剧本引用 ⊆ story_assets 实件」；缺一件即硬失败（这是 99 件悬空引用的直接拦截器）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_story_assets import enforce_gate, MARKER as NOASSET_MARKER

NAME = "我们没有翅膀——格雷塔迦露德与柳木原"


def git_branch():
    """当前构建分支 —— 写进 `成品说明.md` 的溯源行。

    ★ 2026-10-01（`ISSUE-20261001-05`）收尾核对发现：该行原先**硬编码**
      `issue/ISSUE-20261001-03-programming-round2`，于是**此后每次部署都在成品里写一个过期的分支名**
      （`成品说明.md` 是随包交付、给玩家看的说明文件，等于误导）。改为**运行时读取**；
      取不到就写「未知」，**不猜、不沿用旧值**。
    """
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=os.path.dirname(os.path.abspath(__file__)),
                           capture_output=True, text=True)
        b = (r.stdout or "").strip()
        return b if (r.returncode == 0 and b and b != "HEAD") else "未知"
    except Exception:
        return "未知"


# ★ 成品说明「外置可维护块」（ISSUE-20261008-07 R1）——两个**相互独立**的可选通道：
#   缺陷：`成品说明.md` 由**静态模板**整篇重写，凡不写在模板里的内容都会被下一次部署刷掉：
#         ① 主代理手补的「已知问题 8–12」（2026-10-08 一天被刷三次，部署后 `grep` 恒为 0）；
#         ② 手补在头部的「Debug 开发版」横幅（2026-10-08 实测被本脚本的部署刷掉）。
#   修法：两类内容各外置成一个**随仓库跟踪**的小文件，部署时按位置插回：
#         · `编程组\成品说明_横幅.md` ⇒ 插到**头部**（`> 生成：…` 行之后、第一个 `##` 之前）；
#         · `编程组\成品说明_增补.md` ⇒ 插到**已知问题段末尾**（`## 原版位置` 之前）。
#   幂等：生成口径是「**模板 + 横幅 + 增补 → 整篇重建**」，不是往既有 `成品说明.md` 里追加
#         ⇒ 连跑两次逐字节一致，不会叠加、不会重复（故无需去重逻辑）。
#   兼容：**两个文件各自缺失时互不影响**，且都缺失时**行为与旧版逐字节一致**（不报错）。
BANNER_FILE = os.path.join("编程组", "成品说明_横幅.md")
SUPP_FILE = os.path.join("编程组", "成品说明_增补.md")


def load_block(proj, rel):
    """读取工程根下的外置块文件。返回 `(文本, 来源路径 或 None)`。

    不存在 ⇒ `("", None)`（调用方按「无此块」处理，不视作异常）；
    读失败 ⇒ `("", "读取失败(...)")`，调用方仅告警。
    """
    p = os.path.join(proj, rel)
    if not os.path.isfile(p):
        return "", None
    try:
        return open(p, encoding="utf-8").read().strip("\n"), p
    except OSError as e:
        return "", "读取失败(%s)" % e


def inject_block(readme, text, anchor):
    """把块插到 `anchor` 之前（块与前后各留一空行）。返回 `(新文本, 是否插入)`。"""
    if not text:
        return readme, False
    i = readme.find(anchor)
    if i < 0:                       # 模板锚点被改 ⇒ 宁可不插，也不破坏 Markdown 结构
        return readme, False
    return readme[:i] + "\n" + text + "\n" + readme[i:], True


def inject_banner(readme, text):
    """横幅 ⇒ 头部（第一个 `##` 之前）。"""
    return inject_block(readme, text, "\n## ")


def inject_supplement(readme, text):
    """增补 ⇒ 已知问题段末尾（`## 原版位置` 之前）。"""
    return inject_block(readme, text, "\n## 原版位置")


KILL_FILES = ("storyrun.txt", "forcefilefont.txt", "videoprobe.txt",
              "storytest_interval.tjs", "autotour.txt", "quick_flags.tjs", "press_probe.tjs")


def sync(src, dst):
    """把 src 增量同步到 dst，返回**本次**复制的件数。

    ★ 原实现用可变默认参数 `n=[0]` 累加 ⇒ 两次调用共用同一计数器，第二次的返回值是**累计值**
      （日志里 runtime 件数虚高，误导排障）。改为局部计数。（`ISSUE-20261003-04` 修正。）
    """
    n = 0
    for root, _d, files in os.walk(src):
        rel = os.path.relpath(root, src)
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(tgt, f)
            try:
                if os.path.isfile(d) and os.path.getsize(d) == os.path.getsize(s) \
                        and int(os.path.getmtime(d)) >= int(os.path.getmtime(s)):
                    continue
            except OSError:
                pass
            shutil.copy2(s, d)
            n += 1
    return n


def main():
    here = os.path.dirname(os.path.abspath(__file__))          # <proj>\编程组\工具
    proj = os.path.dirname(os.path.dirname(here))              # <proj>
    ws = os.path.dirname(os.path.dirname(proj))                # <checkout>（PROJ 上面还有 工程\）
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ws, "成品", NAME))
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--allow-partial", action="store_true", help="允许部署非全量剧本（仅供调试）")
    ap.add_argument("--ws-root", default="",
                    help="额外允许写入的工作区根（用于把成品部署到主工作树的 成品\）")
    args = ap.parse_args()

    build = os.path.join(proj, "编程组", "build")
    out = os.path.abspath(args.out)
    if not os.path.isdir(os.path.join(build, "game")):
        print("[FATAL] 未找到装配产物，请先跑 assemble_game.py：%s" % build)
        sys.exit(2)
    roots = [os.path.abspath(ws)]
    if args.ws_root:
        roots.append(os.path.abspath(args.ws_root))
    ok = False
    for r in roots:
        if out == r or out.startswith(r.rstrip("/" + "\\") + os.sep):
            ok = True
    if not ok:
        print("[FATAL] 成品目录必须落在允许的工作区内（AGENTS 铁律 1）：%s" % out)
        print("        允许的根：" + " ｜ ".join(roots))
        sys.exit(2)
    if os.path.exists(out) and not args.overwrite:
        bak = out.rstrip("\\/") + "_" + datetime.datetime.now().strftime("%Y%m%d")
        print("[warn] 成品目录已存在，按「不静默覆盖」改为留档改名：%s" % bak)
        if os.path.exists(bak):
            print("[FATAL] 留档目录也已存在，请人工处理：%s" % bak)
            sys.exit(2)
        os.rename(out, bak)

    # ★ 闸门：确认待部署的剧本是**全量**（`--act/--scenes` 的短跑会覆盖 story\，
    #   曾把只含 114 场景的产物部署成「成品」——必须挡住）
    idx = os.path.join(build, "game", "story", "_index.tjs")
    n_scene = 0
    index_ids = set()
    if os.path.isfile(idx):
        txt = open(idx, encoding="utf-8").read()
        i0 = txt.find("UIStoryIndex = [")
        i1 = txt.find("];", i0)
        seg = txt[i0:i1] if i0 >= 0 else ""
        n_scene = seg.count(chr(34)) // 2 if i0 >= 0 else 0
        index_ids = set(re.findall(r'"([^"]+)"', seg))
    print("[gate] 待部署剧本场景数 = %d" % n_scene)
    if n_scene < 600 and not args.allow_partial:
        print("[FATAL] 剧本不是全量（%d < 600）——请先跑 build_story.py --all 再装配。" % n_scene)
        print("        确认要部署短跑产物请加 --allow-partial")
        sys.exit(3)

    # ★ 发布闸门（ISSUE-20261008-01）——在**复制落盘前**硬失败：
    #   ① 诊断构建标记（assemble_game.py --no-story-assets）⇒ 拒部署；
    #   ② 「剧本引用 ⊆ build\game\story_assets 实件」缺一件即拒部署。
    #   口径同 M6 scan_missing_assets.py：story\scene_*.tjs 正则 story_assets/[^"']+。
    if os.path.isfile(os.path.join(build, NOASSET_MARKER)):
        print("[FATAL] 该 build 是诊断构建（存在 %s：装配时带了 --no-story-assets ⇒ 无 story_assets）。"
              "禁止部署：会产出悬空素材引用的成品（ISSUE-20261008-01 的 99 件即此成因）。"
              % NOASSET_MARKER)
        print("        请重跑 assemble_game.py（不带 --no-story-assets）后再部署。")
        sys.exit(5)
    enforce_gate(os.path.join(build, "game"), label="部署闸门（deploy_product）")

    print("[1/3] 复制 game/ ...")
    n_game = sync(os.path.join(build, "game"), os.path.join(out, "game"))    # ★ ISSUE-20261004-12：**story/ 剪枝**——`sync`（含 assemble_game.sync_tree）只增不删，
    #   去（D15/D30）之后目标目录会留下不再被 `_index.tjs` 引用的陈旧 scene_*.tjs（本轮实测
    #   成品与 build 里各残留 4 个 `otv_P03_*`、剧本文件数 680 ≠ 构建集 676）。
    #   剪枝权威＝**build 的 `_index.tjs`**（不是 build 目录内容——build 自己也会陈旧）：
    #   目标 story/ 里凡 `scene_<id>.tjs` 不在 index 清单内的一律删除；`_` 开头的元数据与
    #   其它非 scene 文件一律保留。只剪 story/，不碰 game/ 下其它目录。
    dst_story = os.path.join(out, "game", "story")
    pruned = 0
    if index_ids and os.path.isdir(dst_story):
        for nm in sorted(os.listdir(dst_story)):
            m = re.match(r"^scene_(.+)\.tjs$", nm)
            if m and m.group(1) not in index_ids:
                os.remove(os.path.join(dst_story, nm))
                pruned += 1
        if pruned:
            print("[prune] story/ 剪掉目标侧陈旧场景文件 %d 件（sync 只增不删的收口）" % pruned)
    print("[2/3] 复制 runtime/ ...")
    n_rt = sync(os.path.join(build, "runtime"), os.path.join(out, "runtime"))

    # 清掉调试开关与运行痕迹（成品只放成品）
    for f in KILL_FILES:
        p = os.path.join(out, "game", f)
        if os.path.isfile(p):
            os.remove(p)
    # 一审重要-4：`story\_c16_有差异替代.tsv` 是**过程留痕**（C16 待裁决清单），不随成品发布
    for rel in ("story/_c16_有差异替代.tsv",):
        p = os.path.join(out, "game", rel.replace("/", os.sep))
        if os.path.isfile(p):
            os.remove(p)
    save = os.path.join(out, "runtime", "savedata")
    if os.path.isdir(save):
        for f in os.listdir(save):
            try:
                os.remove(os.path.join(save, f))
            except OSError:
                pass

    # 启动 bat（纯 ASCII + CRLF，相对路径）
    bs = chr(92)
    bat = "\r\n".join([
        "@echo off", "chcp 936 >nul",
        'set "HERE=%~dp0"',
        'start "" "%HERE%runtime' + bs + 'tvpwin32.exe" "%HERE%game"',
        "exit /b 0", ""])
    open(os.path.join(out, "play.bat"), "wb").write(bat.encode("ascii"))

    size_mb = 0
    for root, _d, files in os.walk(out):
        for f in files:
            try:
                size_mb += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    today = datetime.date.today().isoformat()
    readme = """# 成品说明 ·《%s》

> 生成：%s ｜ 构建分支：`%s` ｜ 部署脚本：`编程组\\工具\\deploy_product.py`

## 这是什么

用 **krkrz 1.4.0.8** ＋《我们没有翅膀》全系列六源既有素材**自建**的视觉小说（非原版移植）。
**分级＝R18**（按总纲 D8 取 R18 原版文本，翻译完整、不除敏）。

## 怎么运行

双击本目录下的 `play.bat`（或直接运行 `runtime\\tvpwin32.exe` 并指向 `game`）。
**支持中文路径**（已实测）。窗口标题含署名串。

## 相对原版的行为变化

- 引擎换成 krkrz 1.4.0.8（Windows 原生窗口；原系列为 Lucifen / BGI / 5pb 自研引擎）。
- 画布 **1920×1080**，窗口化 1280×720；**画面区为全画布**（`ISSUE-20261002-06` D-04），素材按自身宽高比
  **contain** 落位 ⇒ 16:9 素材满幅、4:3 素材左右留边。**46 件 4:3 背景已由 AI 整幅扩图为 16:9 满幅**
  （`ISSUE-20261003-02`；取件走资源组清单驱动的覆盖层，不改素材引用映射）。
- 文本为**中文**（既有译文 + 本工程修正层；新米汉化只取人名/地名，剧情独立翻译）。
- 新增系统：BGM 播放与切换点、存档/读档 12 槽（含缩略图）、章节简介/流程图取数、内嵌中文字体兜底；
  **流程图「已读／当前节点」随剧情进度回写**（`ISSUE-20261003-03`，不必先点过流程图），
  **选择支全部可解析**（全库无空目标，不会点到一半终止剧情）。
- **逐行演出已接入**（`ISSUE-20261001-17`）：立绘（23,410 条 op）与逐行音效（7,248 条）按资源组的
  **逐行演出表**随台词行生效。`otv` 源用其**原始位置/层序/退场**；其余五源（本篇/R/AS/前奏诗/涅布）
  **源侧没有位置数据**，用**本工程自定的摆位规则**；且源侧无立绘退场信号 ⇒ 策略是「场景内保持、换场景清空」。
- **对话框头像随说话人切换**（`ISSUE-20261001-16`）：28 个说话人有头像；无映射者（含旁白）不显示头像。
- 便捷操作：**滚轮**向下＝推进、向上＝打开回想；**按住 CTRL**＝强制快进（快进中不播语音与逐行音效）；
  回想界面**按右键**直接返回对话；回想/鉴赏/音乐三屏的页脚「返回」可用。
- **影片已接入（三个槽位 + 片尾 ED）**：① 启动 exe 时播厂牌标（`movies\\np_makerlogo.mp4`）；
  ② 点「开始游戏」后播本篇 OP①（`movies\\ot_op1.mp4`）再进序章；③ **剧情中按源侧有据处插入**
  （`otv_M09_01` → 美咲线终场、`otv_P03_01D` → PSV OP03、`ot_s04_06j2` → D 页 OP02）；④ **片尾 ED**：按 PSV 原版脚本，
  **每条线「最后一场常规剧情戏」的末尾**播该线女主 ED（明日香 `ot_s01_15b`／京 `ot_s01_17a`／
  日和子 `ot_s02_15c`／凤鸣 `ot_s03_21c`／亚衣 `otr_s03c_19a`／小鸠 `ot_s04_27a`／美咲 `otv_M09_01`），
  播完**继续**接该线的「终章 → 解缆」；仅真终局才回标题。番外／前奏诗／后日谈／涅布篇源侧无 ED ⇒ 不播。
  **播放中点击任意处或按任意键＝跳过**。共同前提：影片走 **Media Foundation**（DirectShow 路放不了 H.264）。
  ⚠️ **Win7 风险**：MF 的 H.264/**AAC** 解码器随系统，Win7 可能缺 ⇒ **可能无声**（未实测）。
- **游戏内鼠标右键已禁用**（`ISSUE-20261001-05`，用户 2026-10-01 裁定）：右键不再呼出 9 图标浮层；
  存档/读档/快速存取/设置/回想/流程图请用**右侧快捷条**（指针移到画面右缘即展开）。
- **本成品会新增一个状态文件** `ui_flowscene_state.txt`（写在**存档目录**，与既有 `ui_flow_state.txt`
  **分开**）：记录「已看过哪些**场景**」（键＝场景 id），供流程图等界面判断已读。
  首次进入每个新场景时写入（几 KB、幂等；写失败只记一行日志）。**不打断剧情、不改任何原文件、
  不碰 UI 组的状态文件**。（来源 `ISSUE-20261004-03`：流程图分页重做所依赖的**场景级**已读。）

## 已知问题（如实列出）

0. **流程图「分页新自绘」尚未发布**（`ISSUE-20261004-03`）：成品内**已含**分页几何
   `game\\story\\_flowpages.tjs`（9 页 / 712 节点；页内独立坐标 ⇒ 同坐标叠字归零）与自绘渲染器，
   但**自绘默认关闭**（缺 `game\\flowfull.txt` ⇒ 一律不启用）⇒ **本成品当前仍显示 UI 组的原生流程图屏**。
   要预览新自绘：在 `game\\` 下放一个空文件 `flowfull.txt` 再启动（页签切页 / 滚轮缩放 / 拖动平移 /
   点选进场景 / 已读三态 / 跳转确认卡均在；确认卡默认关，见模块变量 `UIFullAskJump`）。

1. **背景数据缺口**（上游，定性「严重暂不处理」）：原脚本的演出语义未逆向，部分场景在源数据里
   只有「章节题卡」（key visual + Logo）可用，会按题卡显示（680 场景中 **181 个**候选全是题卡）；
   另有 **36 个场景源侧无任何背景数据**、**14 个场景**的候选第 0 位是整幅纯黑帧。已逐场景记 `[STORY][GAP]` 日志。
2. **影片**：**MP4 / H.264 + AAC 可播，但必须走 Media Foundation**（`vo.mode = 3`，且须在 `open` 之前设；
   DirectShow 路按**扩展名白名单**派发 ⇒ `.mp4` 会被拒、报「Unknown video format extension」）。
   片源自 `ISSUE-20261004-07` 起已随包（`game\\movies\\`，10 支 1920×1080 60fps H.264）。
   **画面与声音只能肉眼验收**：EVR 合成在引擎图层之上且内容不在引擎位图里，`exportPng`／GDI 抓屏／
   `PrintWindow` 都取不到。
3. **流程图右栏「画面窗」**现显示该幕首场景的**静态背景**——该屏尚未接逐行演出取数
   （逐行演出本身已在对话画面生效，此为该屏的独立缺口）。
4. 部分系统动作仍为占位（BGM 鉴赏 8 枚、回想跳转/重播、确认框两键、存读档页码 `page_*`）。
5. **Win7 SP1 未实测**；本构建在 Win10/Win11 上实测通过。
6. **黑边**：4:3 素材**左右留边**是有意的（美术裁决 D1）。`ISSUE-20261003-02` 引入 `audit_bg_framing.py`
   逐场景复算（**独立于构建器重推**运行期落位）：680 场景中**有黑边 295 个**（左右 269 / 上下 26），
   比 D-04 ＋ 16:9 接入前**少 70 个**（由有变无 70、由无变有 0）。**黑边全部来自素材画幅，不是绘制逻辑问题**；
   余下 4:3 素材（事件 CG、滚动全景、题卡等）按用户裁定**保留留边**，待将来统一处理。
7. 素材版权：素材取自原系列各作，仅作个人汉化学习用途，**请勿分发**。

## 原版位置

六源原始目录见工作区 `Galgame.md` 索引（一律只读）。**本成品不回写任何原始目录。**

## 技术来源（便于复核）

- 界面：UI 美术组交付的**自研 TJS2**（17 屏 / 1359 贴图 / HTML 1:1 复刻）。
- 剧本/素材：资源组交付的**结构化剧本**（680 场景）与**美术统一交付层**（按 C14/C16 两层清单取件）。
- 编程组：`ui_story.tjs`（剧情引擎）/ `ui_staging.tjs`（逐行演出：立绘槽位 + 逐行音效）/
  `ui_audio.tjs`（音频 + 语音不中断）/ `ui_save.tjs`（存档）/
  `ui_flowwire.tjs`（流程图取数）/ `ui_flowscene.tjs`（**场景级**已读）/
  `ui_flowfull.tjs`（流程图**分页自绘**，默认关）/ `ui_boot.tjs`（启动与兜底）。
- 署名：来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode
""" % (NAME, today, git_branch())

    # ★ 并入两个外置块（ISSUE-20261008-07 R1）——**每次都从模板重建**，故连续部署两次的产物
    #   逐字节一致（幂等），不会把上一版的手补内容叠成两份。两通道各自独立、各自可缺失。
    for tag, rel, inject, where in (
            ("横幅", BANNER_FILE, inject_banner, "头部（第一个 `##` 之前）"),
            ("增补", SUPP_FILE, inject_supplement, "`## 原版位置` 之前")):
        text, src = load_block(proj, rel)
        readme, injected = inject(readme, text)
        if injected:
            print("[ext] 已并入成品说明%s（%s）⇒ %s，%d 字符" % (tag, src, where, len(text)))
        elif src:
            print("[warn] 成品说明%s读取异常，按无此块处理：%s" % (tag, src))
        else:
            print("[ext] 无成品说明%s（%s 不存在）⇒ 该位置按模板原样"
                  % (tag, os.path.join(proj, rel)))

    open(os.path.join(out, "成品说明.md"), "w", encoding="utf-8", newline="\n").write(readme)

    print("[3/3] 成品就绪 → %s" % out)
    print("      game 新复制 %d 件 / runtime %d 件 / 合计 %.1f MiB" % (n_game, n_rt, size_mb / 1048576))
    print("      入口：%s" % os.path.join(out, "play.bat"))


if __name__ == "__main__":
    main()
