# -*- coding: utf-8 -*-
r"""修正被移动后的存档路径记录（ISSUE-ORETUBAR-R）。

背景：本作把「存档目录绝对路径」以 Shift-JIS + NUL 形式记在
    %APPDATA%\<游戏目录名> SaveData\USER.CFG      （游戏每次启动读取，权威来源）
    工程\<译名>\<游戏目录名>\USER.CFG              （安装目录内副本）
目录被移动（工程\Navel → 工程\我们没有翅膀R）后该路径失效，游戏启动即弹
「セーブデータ作成フォルダが見つかりません／新しくセーブデータ作成フォルダを設定しますか？」。

本脚本把这两份 USER.CFG 里的旧路径原地改写为新路径，保持其余字节不变。
所有改动均先备份为 .bak。
"""
import os, re, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
EXCLUDE = {'参照', '语料', '工具', '存档备份', '存档候选', '作品skill'}

game_dir = [d for d in os.listdir(BASE)
            if os.path.isdir(os.path.join(BASE, d)) and 'SaveData' not in d and d not in EXCLUDE][0]

# 关键：磁盘上的目录名是「SJIS 字节被误当 GBK 解码」的产物，Unicode 层面无法重新 encode('cp932')。
# 但需要的恰恰是它在磁盘上的原始字节 —— 直接向文件系统索取，绕开 Unicode 往返。
GAME_DIR_BYTES = os.fsencode(game_dir)

OLD_PATH = b'E:\\ZCode Workspace\\Galgame\\' + '工程'.encode('cp932') + b'\\Navel\\' + GAME_DIR_BYTES + b' SaveData'
NEW_PATH = b'E:\\ZCode Workspace\\Galgame\\' + '工程'.encode('cp932') + b'\\' + '我们没有翅膀R'.encode('cp932') + b'\\' + GAME_DIR_BYTES + b' SaveData'

print('游戏目录名:', game_dir)
print('  原始字节:', GAME_DIR_BYTES)
print('旧路径 :', OLD_PATH.decode('cp932', errors='replace'))
print('新路径 :', NEW_PATH.decode('cp932', errors='replace'), '(%d 字节)' % len(NEW_PATH))
print()

targets = [
    os.path.join(os.environ['APPDATA'], game_dir + ' SaveData', 'USER.CFG'),
    os.path.join(BASE, game_dir, 'USER.CFG'),
]

for t in targets:
    if not os.path.exists(t):
        print('[跳过] 不存在:', t)
        continue
    raw = open(t, 'rb').read()
    if OLD_PATH in raw:
        shutil.copy2(t, t + '.bak')
        open(t, 'wb').write(raw.replace(OLD_PATH, NEW_PATH))
        print('[改写] %s  (%d -> %d 字节)' % (t, len(raw), len(raw.replace(OLD_PATH, NEW_PATH))))
        print('        备份: %s.bak' % t)
    else:
        m = re.search(rb'E:\\[^\x00]{0,200}\x00', raw)
        found = m.group(0).decode('cp932', errors='replace') if m else '(未找到路径串)'
        print('[注意] 未含旧路径，实际存的是: %s' % found)
        print('       文件:', t)
