# -*- coding: utf-8 -*-
r"""把游戏本体与 SaveData 改为纯 ASCII 目录名（ISSUE-ORETUBAR-R）。

原因（实测）：本作把「存档目录绝对路径」以 **Shift-JIS + NUL** 写进 USER.CFG。
    路径里出现中文（我们没有翅膀R）时 'string'.encode('cp932') 直接抛
    UnicodeEncodeError —— 即中文路径根本无法被该引擎表示。
    故游戏本体目录必须走纯 ASCII。

同时清掉记录旧绝对路径的 %APPDATA% 配置，让游戏按新位置重建。
"""
import os, sys, shutil, glob

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
EXCLUDE = {'参照', '语料', '工具', '存档备份', '存档候选', '作品skill'}
NEW_GAME_DIR = 'ORETSUBA_R'          # 纯 ASCII；R 版专用，不与原版混淆

game_dir = [d for d in os.listdir(BASE)
            if os.path.isdir(os.path.join(BASE, d)) and 'SaveData' not in d and d not in EXCLUDE][0]
src_game = os.path.join(BASE, game_dir)
src_save = os.path.join(BASE, game_dir + ' SaveData')
dst_game = os.path.join(BASE, NEW_GAME_DIR)
dst_save = os.path.join(BASE, NEW_GAME_DIR + ' SaveData')

print('原游戏目录:', game_dir, '->', NEW_GAME_DIR)
if os.path.isdir(dst_game):
    print('[跳过] 目标已存在:', dst_game)
else:
    shutil.move(src_game, dst_game)
    print('[移动] 游戏本体 ->', dst_game)
    print('       文件数:', len(os.listdir(dst_game)))

if os.path.isdir(src_save):
    if os.path.isdir(dst_save):
        print('[跳过] 目标存档目录已存在:', dst_save)
    else:
        shutil.move(src_save, dst_save)
        print('[移动] SaveData ->', dst_save)
        print('       文件:', os.listdir(dst_save))

# 清掉记录旧绝对路径的 %APPDATA% 配置（游戏下次启动会重建）
old_appdata = os.path.join(os.environ['APPDATA'], game_dir + ' SaveData')
if os.path.isdir(old_appdata):
    keep = os.path.join(BASE, '存档备份', 'AppData_USER.CFG.orig')
    uc = os.path.join(old_appdata, 'USER.CFG')
    if os.path.exists(uc):
        shutil.copy2(uc, keep)
        print('[备份]', uc, '->', keep)
    shutil.rmtree(old_appdata)
    print('[删除] 旧 AppData 配置目录（含旧绝对路径）:', old_appdata)

print()
print('=== 现状 ===')
print('游戏目录:', dst_game)
print('  存在:', os.path.isdir(dst_game), ' 文件数:', len(os.listdir(dst_game)) if os.path.isdir(dst_game) else 0)
print('存档目录:', dst_save)
print('  存在:', os.path.isdir(dst_save), ' 文件:', os.listdir(dst_save) if os.path.isdir(dst_save) else [])
