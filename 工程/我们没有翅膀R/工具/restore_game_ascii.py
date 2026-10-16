# -*- coding: utf-8 -*-
r"""恢复游戏本体并部署到纯 ASCII 路径（ISSUE-ORETUBAR-R）。

背景：ascii_verify.py 的用例 1 把源目录与目标目录设为同一路径，导致游戏本体被
删空（工具缺陷，已记录）。安装介质备份（备份\我们没有翅膀R-安装介质\SET_UP\）
完好，可完整恢复。

部署决定：游戏本体放 `E:\ZCode Workspace\Galgame\ORETSUBA_R\ORETSUBA_R\`。
理由（实测）：
  * 本作把存档目录绝对路径以 **Shift-JIS** 写入 USER.CFG；
  * 「我们没有翅膀R」含简体字（们/没/翅/膀），Shift-JIS 中不存在 → 路径无法表示；
  * 原版 2009 能跑正因为它在 `D:\Gal\[Navel]我们没有翅膀\`（纯 ASCII 父目录）。
"""
import os, re, sys, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP')
TEMPLATE = os.path.join(PROJ, '存档备份', 'AppData_USER.CFG.orig')
USER_SAVE = os.path.join(PROJ, '存档备份', '用户原始存档')

DEST_ROOT = os.path.join(WS, 'ORETSUBA_R')
GAME = os.path.join(DEST_ROOT, 'ORETSUBA_R')
SAVE = os.path.join(DEST_ROOT, 'ORETSUBA_R SaveData')
APPDATA_DIR = os.path.join(os.environ['APPDATA'], '壌偨偪偵梼偼側偄俼 SaveData')


def main():
    print('=== 1. 从安装介质恢复游戏本体 ===')
    if not os.path.isdir(MEDIA):
        print('[错误] 介质目录不存在:', MEDIA); return
    os.makedirs(GAME, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(MEDIA)):
        s = os.path.join(MEDIA, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(GAME, f)); n += 1
    # 补齐安装目录独有的文件（从工程内其它副本找，找不到就跳过）
    for extra in ['DataLink.exe', 'SET_UP.IFG', 'UNINST.EXE']:
        for cand in [os.path.join(PROJ, 'ORETSUBA_R', extra),
                     os.path.join(PROJ, '_pristine', 'game', extra)]:
            if os.path.exists(cand) and not os.path.exists(os.path.join(GAME, extra)):
                shutil.copy2(cand, os.path.join(GAME, extra)); n += 1
    print('  恢复 %d 个文件 -> %s' % (n, GAME))
    print('  内容:', sorted(os.listdir(GAME)))

    print()
    print('=== 2. 恢复存档（用户原始存档 + 候选A解锁脚本）===')
    os.makedirs(SAVE, exist_ok=True)
    for f in os.listdir(USER_SAVE):
        shutil.copy2(os.path.join(USER_SAVE, f), os.path.join(SAVE, f))
    print('  存档目录:', sorted(os.listdir(SAVE)))

    print()
    print('=== 3. 写 USER.CFG（ASCII 路径）===')
    raw = open(TEMPLATE, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    seg = os.path.abspath(SAVE).encode('ascii') + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    cfg = bytes(out)
    for p in [os.path.join(SAVE, 'USER.CFG'), os.path.join(GAME, 'USER.CFG')]:
        open(p, 'wb').write(cfg)
        print('  [写出] %s' % p)
    os.makedirs(APPDATA_DIR, exist_ok=True)
    open(os.path.join(APPDATA_DIR, 'USER.CFG'), 'wb').write(cfg)
    print('  [写出] %s' % os.path.join(APPDATA_DIR, 'USER.CFG'))
    print('  路径段: %s' % seg[:-1].decode())

    print()
    print('=== 4. 启动验证 ===')
    p = subprocess.Popen([os.path.join(GAME, 'ORETUBAR.EXE')], cwd=GAME)
    time.sleep(16)
    print('  PID %d 仍在运行: %s' % (p.pid, p.poll() is None))
    print('  PID 已记录到 临时\\_pid.txt')
    open(os.path.join(WS, '临时', '_pid.txt'), 'w').write(str(p.pid))


if __name__ == '__main__':
    main()
