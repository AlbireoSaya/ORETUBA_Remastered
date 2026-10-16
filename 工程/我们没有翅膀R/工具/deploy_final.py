# -*- coding: utf-8 -*-
r"""成品部署（ISSUE-ORETUBAR-R 收尾）。

把当前可运行的汉化版整理为规范成品：
    成品\我们没有翅膀R\
        ORETSUBA_R\                 ← 游戏本体（ASCII 名；引擎把存档路径以 SJIS 写入，路径需可表示）
            ORETUBAR.EXE            ← 已打 GBK 补丁（字体字符集 + 前导字节判定）
            SCRIPT.LPK              ← 全量汉化（等长化，含中文角色名）
            ...（其余 LPK / DLL / 数据）
        ORETSUBA_R SaveData\        ← 与游戏目录同级
            GAMEDATA.DAT            ← 全解锁（CG/回想 100%）
            USER.CFG                ← 指向本目录
        成品说明.md
        exe_patch_report.json

并修正 `%APPDATA%\我们没有翅膀R SaveData\USER.CFG` 指向新路径。
**只做移动与复制，不删除任何用户文件。**
"""
import os, re, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
PROD = os.path.join(WS, '成品', '我们没有翅膀R')
SRC_ROOT = os.path.join(WS, 'ORETSUBA_R')
GAME = os.path.join(PROD, 'ORETSUBA_R')
SAVE = os.path.join(PROD, 'ORETSUBA_R SaveData')
APPDATA_DIR = os.path.join(os.environ['APPDATA'], '我们没有翅膀R SaveData')


def main():
    print('=== 1. 移动游戏本体到成品目录 ===')
    src_game = os.path.join(SRC_ROOT, 'ORETSUBA_R')
    src_save = os.path.join(SRC_ROOT, 'ORETSUBA_R SaveData')
    if os.path.isdir(PROD):
        print('  成品目录已存在:', PROD)
    if os.path.isdir(src_game) and not os.path.isdir(GAME):
        os.makedirs(PROD, exist_ok=True)
        shutil.move(src_game, GAME)
        print('  move: %s -> %s' % (src_game, GAME))
    else:
        print('  跳过移动（源不存在或目标已存在）')
    if os.path.isdir(src_save) and not os.path.isdir(SAVE):
        shutil.move(src_save, SAVE)
        print('  move: %s -> %s' % (src_save, SAVE))
    # 说明文件
    for f in ('exe_patch_report.json', '成品说明.md'):
        s = os.path.join(SRC_ROOT, f)
        if os.path.exists(s):
            shutil.move(s, os.path.join(PROD, f))
            print('  move:', f)
    # 源目录若已空则移除
    if os.path.isdir(SRC_ROOT) and not os.listdir(SRC_ROOT):
        os.rmdir(SRC_ROOT)
        print('  已移除空的旧目录', SRC_ROOT)

    print()
    print('=== 2. 修正 USER.CFG（存档路径） ===')
    tpl = os.path.join(WS, '工程', '我们没有翅膀R', '存档备份', 'AppData_USER.CFG.orig')
    raw = open(tpl, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    seg = os.path.abspath(SAVE).encode('ascii') + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    os.makedirs(SAVE, exist_ok=True)
    for p in (os.path.join(SAVE, 'USER.CFG'), os.path.join(GAME, 'USER.CFG')):
        open(p, 'wb').write(bytes(out))
        print('  写出', p)
    os.makedirs(APPDATA_DIR, exist_ok=True)
    open(os.path.join(APPDATA_DIR, 'USER.CFG'), 'wb').write(bytes(out))
    print('  写出', os.path.join(APPDATA_DIR, 'USER.CFG'))
    print('  路径 ->', seg[:-1].decode())

    print()
    print('=== 3. 校验 ===')
    for p in (os.path.join(GAME, 'SCRIPT.LPK'), os.path.join(GAME, 'ORETUBAR.EXE'),
              os.path.join(SAVE, 'GAMEDATA.DAT')):
        print('  %-58s %10d' % (p, os.path.getsize(p) if os.path.exists(p) else -1))
    print('  游戏文件数:', len(os.listdir(GAME)) if os.path.isdir(GAME) else 0)


if __name__ == '__main__':
    main()
