# -*- coding: utf-8 -*-
r"""把《我们没有翅膀R》汉化补丁从工程产物重新组装成「可直接覆盖原版游戏目录」的独立补丁包。

为什么需要这个脚本（教训）：补丁成品曾经只存在于游戏实体目录
（`_game_ascii\ORETSUBA_R\`）里，该目录被清理后**成品一并消失**；
好在构建链可复现，本脚本把「重新生成补丁包」固化下来。

补丁构成（与《成品说明.md》一致，共 2 个必装文件 + 1 个可选存档）：

  1. `ORETUBAR.EXE`  ← 原版 + GBK 字符集补丁（165 字节；`exe_gbk_patch.py`）
  2. `SCRIPT.LPK`    ← 原版 + 全量等长汉化（4,604,893 → 5,039,575 字节；`build_padded.py`）
  3. `GAMEDATA.DAT`  ← 全 CG/全回想解锁存档（可选，装到「存档目录」而非游戏目录）

用法：
  python -X utf8 build_patch_package.py [--out DIR] [--skip-save]

默认输出：`E:\ZCode Workspace\Galgame\成品\我们没有翅膀R_汉化补丁\`

自检：重建完成后比对两个已实机验证过的 md5，不符即报错（避免静默产出坏包）。
"""
import hashlib
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

TOOLS = os.path.dirname(os.path.abspath(__file__))
WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP')
SAVE_CAND = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
OUT_DEFAULT = os.path.join(WS, '成品', '我们没有翅膀R_汉化补丁')
STAGE = os.path.join(WS, '临时', 'oretsuba_r_patch')

# 已实机验证过的成品指纹（《成品说明.md》/ 会话交接记录）
EXPECT_LPK = '5c94a3fe2a068ca815b99fd0cd9a7ff5'          # 正文 + 系统界面全汉化（ISSUE-20261007-06 二审定稿）
EXPECT_LPK_BODY_ONLY = '22dda536f8bc51b7cd6274df18eeb76a'  # 仅正文汉化、系统界面仍乱码（旧版）
EXPECT_EXE = '3fb2f9b410e23deb930d3cad82d11cd0'

GAME_SUB = '覆盖到游戏目录'
SAVE_SUB = '可选_全解锁存档'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def build_lpk(dst):
    """用主构建器重建汉化 SCRIPT.LPK（等长 + 标题 + 全部 ISSUE-06/07 修复已在语料中生效）。"""
    r = subprocess.run([sys.executable, '-X', 'utf8',
                        os.path.join(TOOLS, 'build_padded.py'), '--out', dst],
                       capture_output=True, text=True, encoding='utf-8')
    tail = (r.stdout or '').strip().splitlines()[-3:]
    for ln in tail:
        print('   ', ln)
    if r.returncode != 0 or not os.path.exists(dst):
        print(r.stderr)
        raise SystemExit('[错误] SCRIPT.LPK 重建失败')


def build_sysui(lpk):
    """在重建出的 LPK 上叠加**系统界面汉化**（标题菜单说明/退出确认/存读档/设置屏/报错等，
    ISSUE-20261007-06）。等长 GBK 覆写、零重定位；译文与裁决见
    `子代理工作区\\ISSUE-20261007-06\\` 与 `工具\\build_sysui.py`。"""
    r = subprocess.run([sys.executable, '-X', 'utf8',
                        os.path.join(TOOLS, 'build_sysui.py'), '--apply', '--lpk', lpk],
                       capture_output=True, text=True, encoding='utf-8')
    for ln in (r.stdout or '').strip().splitlines():
        print('   ', ln)
    if r.returncode != 0:
        print(r.stderr)
        raise SystemExit('[错误] 系统界面汉化叠加失败')


def build_exe(dst):
    """在**原版** EXE 上重新施加 GBK 补丁（幂等，永不叠加）。"""
    src = os.path.join(MEDIA, 'ORETUBAR.EXE')
    r = subprocess.run([sys.executable, '-X', 'utf8',
                        os.path.join(TOOLS, 'exe_gbk_patch.py'), 'apply', src, dst],
                       capture_output=True, text=True, encoding='utf-8')
    for ln in (r.stdout or '').strip().splitlines():
        print('   ', ln)
    if r.returncode != 0 or not os.path.exists(dst):
        print(r.stderr)
        raise SystemExit('[错误] ORETUBAR.EXE 补丁失败')


INTRO = u"""# 《我们没有翅膀R》简体中文汉化补丁 · 安装说明

本补丁**只含改动过的文件**：把它覆盖到**原版日文游戏目录**上即可生效，
不需要重新安装游戏，也不改动其它任何文件。

- 游戏：我们没有翅膀R（俺たちに翼はないＲ，Navel 2011-06-24，一般向）
- 引擎：Lucifen「Easy Game System DX」
- 补丁包生成：{date}
- 适配原版：DVD 版（`SET_UP\\` 16 文件那一版）

---

## 一、目录说明

```
覆盖到游戏目录\\           ← 这两个文件覆盖到「原版游戏目录」根目录（与 ORETUBAR.EXE 同级）
    ORETUBAR.EXE            （原版 + GBK 字符集补丁，165 字节改动）
    SCRIPT.LPK              （原版 + 全量中文汉化）
可选_全解锁存档\\
    GAMEDATA.DAT            （全 CG / 全回想解锁；**不放游戏目录**，见 §三）
```

## 二、必装：覆盖到游戏目录

1. 找到原版游戏目录——就是**放着 `ORETUBAR.EXE` 的那一级目录**（内含
   `BGM.LPK` `CHR.LPK` `DATA.LPK` `PIC.LPK` `SCRIPT.LPK` `SE.LPK` `SYS.LPK`
   `VOICE.LPK` `ORETUBAR.EXE` `tvpgl.dll` `wuvorbis.dll` 等，共 16 个文件）。
2. 把 `覆盖到游戏目录\\` 里的 **`ORETUBAR.EXE`** 与 **`SCRIPT.LPK`** 复制进去，**覆盖同名文件**。
   （建议先把原版这两个文件另存备份，本补丁未附带原版备份。）
3. 双击 `ORETUBAR.EXE` 启动，即为中文版。

⚠️ **游戏目录的完整路径必须是纯 ASCII**（不含中文/日文/全角字符），例如
`D:\\Games\\ORETSUBA_R\\`。原因：引擎把存档目录的绝对路径按 Shift-JIS 写入
`USER.CFG`，中文路径无法表示，会弹「セーブデータ作成フォルダが見つかりません」。

⚠️ **不要**只把补丁文件夹拷走当游戏用——补丁只含 2 个文件，其余归档仍来自原版。

## 三、可选：全 CG / 全回想解锁存档

`GAMEDATA.DAT` 属于**存档文件**，位置**不在游戏目录内**，而在**与游戏目录同级的
存档目录**里，名字固定为「`<游戏目录名> SaveData`」：

```
D:\\Games\\ORETSUBA_R\\              ← 游戏目录（上面覆盖补丁的地方）
D:\\Games\\ORETSUBA_R SaveData\\     ← 存档目录 ← GAMEDATA.DAT 放这里
```

- 目录不存在时，先启动游戏一次（引擎会自动创建），再放入 `GAMEDATA.DAT`。
- 放入前建议先备份原有 `GAMEDATA.DAT`。
- 只影响画廊 / 回想解锁状态，不含剧情进度。

**首次启动若弹出询问框（标题与正文都是乱码汉字）**，那是引擎在问
「存档文件夹找不到，是否新建？」——**选「是(Y)」**即可，它会在提示的路径新建并记住。
想换存档位置：删掉 `%APPDATA%\\<窗口标题> SaveData\\USER.CFG`（窗口标题即「我们没有翅膀R」）
后重启，或进 CONFIG 画面改。**提示框本身乱码**属下面第 2 条已知问题。

⚠️ 本补丁**不改动**你机器上已有的存档配置。若此前装过本作并留下配置，引擎会沿用其中
记录的存档目录（可能指向别处）——上一条的「删 `USER.CFG` 后重启」是重置它的办法。

## 四、卸载 / 回滚

把原版 `ORETUBAR.EXE` 与 `SCRIPT.LPK` 覆盖回去即可（本补丁未改动注册表、
未改动其它文件、未改动游戏目录之外的任何文件，`USER.CFG` 由游戏自行生成）。

## 五、已知问题（照实说明）

1. **场景描述**（每个场景开头的简介栏）**保留日文**——用户已裁定不译。
2. ~~系统界面文字为乱码~~ → **已于本次补丁补齐**（2026-10-07）：标题画面菜单说明、
   退出确认框、存档/读档对话框、设置画面、错误提示等 **286 条**已按**等长 GBK**写入
   `SCRIPT.LPK` 的系统 SOB（`title` / `title2` / `saveload` / `config.dat` / `config1` /
   `config2` / `gameinit` / `main` / `gallery` / `bgmmode` / `voiceinf.dat`）。
   **残留 3 处**：设置画面的字体名 `ＭＳ ゴシック`（config1 ×2 / config2 ×1）**按原字节保留**——
   该串是引擎据以创建字体的**资源名**，改动有失效风险，故不译（在这三处仍会显示为乱码汉字）。
   另有 **23 处单字符**（`gallery.sob` 11 / `config2.sob` 11 / `title.sob` 1）位于**数字索引表**内，
   判定为字节码误判（非显示串），**未改动**。
3. **5,368 条译文因超长被截断**（引擎对文本字节长度有硬依赖，译文必须与原文严格等长）。
4. **47 条译文疑与原文错配**（迁移自参照汉化的配对边界情况）。
5. **窗口标题无法带署名**：标题字段被引擎同时用作存档配置目录名，含空格与 `&`
   会导致目录创建失败。署名另见《成品说明.md》。
6. 未在 **Win7** 与**非中文区域系统**实测（当前实测环境：Windows 10 x64 中文区域）。
7. **系统界面汉化只做了字节级与启动级验证**：244 条的写入位置/长度已逐条核对（零重定位），
   游戏可正常启动到标题画面；但**设置画面 / 存读档对话框 / 报错框未逐屏目视确认**
   （本机窗口被其它程序占住前台，抓不到游戏画面）。若某屏显示异常，请截图回报。

## 六、这次汉化改了什么

| 文件 | 改动 |
| --- | --- |
| `ORETUBAR.EXE` | GBK 补丁 165 字节：字体字符集 `SHIFTJIS → GB2312`（3 处）；文本前导字节判定 `0x81–0xFC → 0x81–0xFE`（83 处 / 162 字节） |
| `SCRIPT.LPK` | **正文**：全量汉化 58,360 条文本槽 100% 中文化，**全部译文与原文字节数严格等长**；角色名（名字框）全部中文、无方块；选项按钮中文；窗口标题「我们没有翅膀R」 |
| `SCRIPT.LPK` | **系统界面**（2026-10-07 新增）：标题菜单说明、退出确认、存读档对话框、设置画面、错误提示等 **286 条**等长汉化 |
| `GAMEDATA.DAT` | 全 CG / 全回想解锁（可选） |

约 89% 译文迁移自「新米汉化组」的原版（2009）中文汉化（逐字节比对确认对应关系），
其余（含 R 版新增的香田亜衣线）为新译；系统界面文案为新译（术语沿用作术语表与参照汉化）。
译名按新米写法统一：`ガルーダ→伽鲁炟`、`プラチナ→普纳奇纳`、`ファルコン→法卢空`、`ハリュー→哈里`。

### 系统界面汉化是怎么做的（供后续维护）

与正文同一套方法：**在文件内原位置等长覆写 GBK 字节，零地址重定位**。
- 生成步骤已固化进本脚本的 `build_sysui()`（第 2 步）→ 依赖
  `工具/build_sysui.py`（含 `OVERRIDE` 裁决表）与译文 `工程/我们没有翅膀R/工具/sysui/out_A.tsv、out_B.tsv`；
- **每个串的 GBK 字节数必须等于原串字节数**（偏短补全角空格、偏长按 GBK 字符边界截断，
  本次实测 77 条等长 / 209 条补齐 / **0 条截断**）。
- 抽取判据见 `工具/scan_sysui_v2.py`（**第二版**：把 SJIS 单字节 `｢｣`、2 字串、
  CJK 标点、含半角空格的姓名也纳入候选——第一版只认 SJIS 双字节且要求 ≥3 字符，
  漏掉它们会在 GBK 下造成**两字节错位**与整屏乱码）；
  译文与逐条裁决见 `工具/fix_sysui_round2.py`（含一审打回项的修法与理由）。

---

## 附：校验指纹（md5）

```
ORETUBAR.EXE  {exe_md5}
SCRIPT.LPK    {lpk_md5}
GAMEDATA.DAT  {dat_md5}
```

来自个人汉化者 AlbireoSaya 　模型&工具: Deepseek v4.1 flash + ZCode
"""


def main():
    args = sys.argv[1:]
    out = args[args.index('--out') + 1] if '--out' in args else OUT_DEFAULT
    skip_save = '--skip-save' in args

    game_dir = os.path.join(out, GAME_SUB)
    save_dir = os.path.join(out, SAVE_SUB)
    os.makedirs(game_dir, exist_ok=True)

    stage = os.path.join(STAGE, '_rebuild')
    os.makedirs(stage, exist_ok=True)

    print('[1/5] 重建 SCRIPT.LPK（正文汉化）')
    lpk = os.path.join(stage, 'SCRIPT.LPK')
    build_lpk(lpk)

    print('[2/5] 叠加系统界面汉化（标题/存读档/设置/报错等）')
    build_sysui(lpk)

    print('[3/5] 重建 ORETUBAR.EXE')
    exe = os.path.join(stage, 'ORETUBAR.EXE')
    build_exe(exe)

    print('[4/5] 指纹自检')
    hl, he = md5(lpk), md5(exe)
    print('    SCRIPT.LPK   %s  %s' % (hl, 'OK' if hl == EXPECT_LPK else '!!不符 期望 ' + EXPECT_LPK))
    print('    ORETUBAR.EXE %s  %s' % (he, 'OK' if he == EXPECT_EXE else '!!不符 期望 ' + EXPECT_EXE))
    if hl != EXPECT_LPK or he != EXPECT_EXE:
        raise SystemExit('[错误] 重建结果与已实机验证的成品不一致，已中止（不写出补丁包）')

    shutil.copy2(lpk, os.path.join(game_dir, 'SCRIPT.LPK'))
    shutil.copy2(exe, os.path.join(game_dir, 'ORETUBAR.EXE'))

    hd = '（未包含）'
    if not skip_save:
        os.makedirs(save_dir, exist_ok=True)
        shutil.copy2(SAVE_CAND, os.path.join(save_dir, 'GAMEDATA.DAT'))
        hd = md5(SAVE_CAND)

    print('[5/5] 写安装说明')
    import datetime
    txt = INTRO.format(date=datetime.date.today().isoformat(),
                       exe_md5=he, lpk_md5=hl, dat_md5=hd)
    with open(os.path.join(out, '安装说明.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)

    print()
    print('补丁包已生成:', out)
    for root, dirs, files in os.walk(out):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            print('   %10d  %s' % (os.path.getsize(p), os.path.relpath(p, out)))


if __name__ == '__main__':
    main()
