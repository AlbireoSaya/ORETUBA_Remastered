# -*- coding: utf-8 -*-
r"""成品组装（纯净版，ISSUE-ORETUBAR-R）。

**本脚本只做加法**：从介质备份复制文件、写补丁、写配置、写说明。
不含任何删除/清空逻辑——目录整理请另行确认后手工执行。

成品落点：`E:\ZCode Workspace\Galgame\ORETSUBA_R\`
    ORETSUBA_R\                 ← 游戏本体（ASCII，与可执行文件名一致）
        ORETUBAR.EXE            ← 已打 GBK 补丁
        SCRIPT.LPK              ← 全量汉化脚本
        ...（其余 LPK / DLL / 数据文件）
    ORETSUBA_R SaveData\        ← 与游戏目录同级
        GAMEDATA.DAT            ← 全解锁
        USER.CFG                ← 指向本目录（SJIS 可表示的纯 ASCII 路径）
    成品说明.md / exe_patch_report.json
"""
import os, re, sys, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP')
CN_LPK = os.path.join(WS, '临时', '_build', 'SCRIPT.LPK')
UNLOCK = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
CFG_TPL = os.path.join(PROJ, '存档备份', 'AppData_USER.CFG.orig')

ROOT = os.path.join(WS, 'ORETSUBA_R')
GAME = os.path.join(ROOT, 'ORETSUBA_R')
SAVE = os.path.join(ROOT, 'ORETSUBA_R SaveData')
SIGN = '来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode'

MEDIA_FILES = ['BGM.LPK', 'CHR.LPK', 'DATA.LPK', 'DS_MOVIE.DLL', 'DS_SPRITE.DLL',
               'ORETUBAR.EXE', 'PIC.LPK', 'READ_ME.TXT', 'SCRIPT.LPK', 'SE.LPK',
               'SYS.LPK', 'USER.CFG', 'UserConfig.exe', 'VOICE.LPK', 'tvpgl.dll', 'wuvorbis.dll']


def main():
    t0 = time.time()
    print('成品根:', ROOT)
    os.makedirs(GAME, exist_ok=True)
    os.makedirs(SAVE, exist_ok=True)

    print()
    print('=== 1. 从介质复制游戏本体（只增不删）===')
    copied = 0
    for f in MEDIA_FILES:
        s = os.path.join(MEDIA, f)
        d = os.path.join(GAME, f)
        if not os.path.exists(s):
            print('  [缺失] 介质中无', f); continue
        if os.path.exists(d) and os.path.getsize(d) == os.path.getsize(s) and f != 'ORETUBAR.EXE':
            continue
        shutil.copy2(s, d)
        copied += 1
    print('  复制/覆盖 %d 个文件；当前游戏目录 %d 项' % (copied, len(os.listdir(GAME))))

    print()
    print('=== 2. GBK 补丁 EXE ===')
    exe = os.path.join(GAME, 'ORETUBAR.EXE')
    tmp = exe + '.gbk'
    rep = os.path.join(ROOT, 'exe_patch_report.json')
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'exe_gbk_patch.py'),
                        'apply', exe, tmp, '--report', rep],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('\n'.join('  ' + l for l in ((r.stdout or '') + (r.stderr or '')).splitlines()[:8]))
    if os.path.exists(tmp):
        shutil.move(tmp, exe)
        v = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'exe_gbk_patch.py'),
                            'verify', exe], capture_output=True, text=True, encoding='utf-8', errors='replace')
        print('  verify:', (v.stdout or '').strip()[:120])
    else:
        print('  [错误] 未生成补丁 EXE')

    print()
    print('=== 3. 汉化 SCRIPT.LPK ===')
    if os.path.exists(CN_LPK):
        shutil.copy2(CN_LPK, os.path.join(GAME, 'SCRIPT.LPK'))
        print('  %.2f MB' % (os.path.getsize(os.path.join(GAME, 'SCRIPT.LPK')) / 1048576))
    else:
        print('  [错误] 缺汉化 LPK:', CN_LPK)

    print()
    print('=== 4. USER.CFG ===')
    raw = open(CFG_TPL, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    seg = os.path.abspath(SAVE).encode('ascii') + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    for p in [os.path.join(SAVE, 'USER.CFG'), os.path.join(GAME, 'USER.CFG')]:
        open(p, 'wb').write(bytes(out))
    print('  路径 ->', seg[:-1].decode())

    print()
    print('=== 5. 全解锁存档 ===')
    if os.path.exists(UNLOCK):
        shutil.copy2(UNLOCK, os.path.join(SAVE, 'GAMEDATA.DAT'))
        print('  GAMEDATA.DAT %d 字节' % os.path.getsize(os.path.join(SAVE, 'GAMEDATA.DAT')))
    else:
        print('  [警告] 缺全解锁档')

    print()
    print('=== 6. 成品说明.md ===')
    txt = f'''# 成品说明 · 我们没有翅膀R

《我们没有翅膀R》（俺たちに翼はないＲ，Navel 2011）**简体中文汉化版**。
基于日文原版 DVD 版制作，未回写原始游戏目录，本目录可独立运行。

## 运行方式

双击 **`ORETSUBA_R\\ORETUBAR.EXE`**。

> ⚠️ **路径要求：整条路径必须是纯 ASCII**（不含中文）。
> 本作把存档目录路径以 Shift-JIS 写入 `USER.CFG`，中文路径无法被该引擎表示。
> 若把游戏移到含中文的目录里，会提示「找不到存档文件夹」。
> 当前路径：`{GAME}`

- 需要 **Windows（中文系统区域，ACP=936）**。
- 原版要求 DirectX 9.0c；无其它运行库依赖。

## 相对原版改了什么

| 文件 | 改动 |
| --- | --- |
| `ORETSUBA_R\\ORETUBAR.EXE` | **GBK 补丁**（165 字节）：字体字符集 `SHIFTJIS_CHARSET→GB2312_CHARSET` 3 处；文本前导字节判定 `0x81-0xFC → 0x81-0xFE` 83 处 / 162 字节。使引擎按 GBK 解读中文并渲染 |
| `ORETSUBA_R\\SCRIPT.LPK` | **全量汉化脚本**：58,360 条文本槽 100% 中文化（迁移自新米汉化组原版汉化 51,736 条 + 本次新译 6,624 条）；另 4,000 处残留日文按 GBK 重编码以消除乱码 |
| `SCRIPT.LPK` 内 `ll_app.inf` | 窗口标题改为「我们没有翅膀R」+ 署名 |
| `ORETSUBA_R SaveData\\GAMEDATA.DAT` | **全解锁存档**：CG / 回想全开 |

## 翻译来源与致谢

- 约 89% 译文**迁移自「新米汉化组」的原版（2009）中文汉化**，经字节级逐槽比对确认对应关系。
- 其余（含 R 版新增的香田亜衣路线 34 个场景）为本次新译。
- 迁移中发现的译法不一致处已按本作语境统一。

## 署名

{SIGN}

## 已知问题

1. **系统 UI 仍为日文**（存档/读档/系统菜单等约 141 条，来自 EXE 内嵌字符串）——不影响游玩。
2. **少量演出文字未覆盖**（如个别影片叠字），来源为 `DATA.LPK`/`SYS.LPK` 内数据，尚未处理。
3. 文本历史（Log）与部分系统提示的编码路径未逐一实机核对。
4. 未在 Win7 实测（本机 Windows 10 x64）；未在非中文区域系统实测。

## 其他位置

- 原版安装介质备份：`备份\\我们没有翅膀R-安装介质\\`
- 工程与工具链：`工程\\我们没有翅膀R\\`
- 技术文档：`工程\\我们没有翅膀R\\技术报告.md`、`作品skill\\SKILL.md`
'''
    open(os.path.join(ROOT, '成品说明.md'), 'w', encoding='utf-8').write(txt)
    print('  已写出')

    print()
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(ROOT) for f in fs)
    print('=== 完成，用时 %.0f 秒；成品体积 %.2f GB ===' % (time.time() - t0, total / 1073741824))
    print('游戏本体:', GAME, '(%d 项)' % len(os.listdir(GAME)))


if __name__ == '__main__':
    main()
