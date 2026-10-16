# -*- coding: utf-8 -*-
r"""一键回滚：把存档目录里的文件还原成「用户原始存档」（ISSUE-ORETUBAR-R 存档线）。

默认只还原 GAMEDATA.DAT（存档线唯一的改动对象）。
    --all          额外还原 APP_CFG.DAT 与 TEXT_LOG.DAT
    --with-usercfg 连 USER.CFG 一起还原（**危险**：那份记录的是旧存档路径，
                   除非你确定路径已改回，否则不要用）

行为：
    1. 把当前线上文件备份到 工程\我们没有翅膀R\存档备份\自动备份\回滚前_<时间戳>\
       （只新增，绝不删除）
    2. 从 工程\我们没有翅膀R\存档备份\用户原始存档\ 复制回线上
    3. 逐字节校验（sha256 比对）

用法：
    python -X utf8 rollback_save.py --dry-run
    python -X utf8 rollback_save.py
    python -X utf8 rollback_save.py --all
"""
import argparse
import datetime
import hashlib
import os
import shutil
import sys

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SAVE_DIR_DEFAULT = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R SaveData')
PRISTINE_DIR = os.path.join(PROJ, '存档备份', '用户原始存档')
AUTO_BAK_ROOT = os.path.join(PROJ, '存档备份', '自动备份')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--save-dir', default=SAVE_DIR_DEFAULT)
    ap.add_argument('--source-dir', default=PRISTINE_DIR)
    ap.add_argument('--all', action='store_true', help='连 APP_CFG.DAT / TEXT_LOG.DAT 一起还原')
    ap.add_argument('--with-usercfg', action='store_true', help='连 USER.CFG 一起还原（危险）')
    ap.add_argument('--bak-root', default=AUTO_BAK_ROOT, help='回滚前留档根目录（默认 存档备份\自动备份）')
    a = ap.parse_args()

    names = ['GAMEDATA.DAT']
    if a.all:
        names += ['APP_CFG.DAT', 'TEXT_LOG.DAT']
    if a.with_usercfg:
        names += ['USER.CFG']

    print('=== 存档回滚（还原为用户原始存档）===')
    print('源目录   :', a.source_dir)
    print('存档目录 :', a.save_dir)
    print('还原清单 :', ', '.join(names))
    print('模式     :', 'DRY-RUN（不写任何文件）' if a.dry_run else '实际执行')

    if not os.path.isdir(a.source_dir):
        raise SystemExit('[中止] 源目录不存在: %s' % a.source_dir)
    if not os.path.isdir(a.save_dir):
        raise SystemExit('[中止] 存档目录不存在: %s' % a.save_dir)

    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    pre_dir = os.path.join(a.bak_root, '回滚前_%s' % ts)

    for n in names:
        src = os.path.join(a.source_dir, n)
        dst = os.path.join(a.save_dir, n)
        if not os.path.isfile(src):
            print('[跳过] 源缺文件:', src); continue
        print('\n--- %s' % n)
        if os.path.isfile(dst):
            print('  当前 : %d 字节 sha256=%s' % (os.path.getsize(dst), sha(dst)[:16]))
        print('  源   : %d 字节 sha256=%s' % (os.path.getsize(src), sha(src)[:16]))
        if a.dry_run:
            print('  （dry-run：跳过拷贝）')
            continue
        if os.path.isfile(dst):
            os.makedirs(pre_dir, exist_ok=True)
            shutil.copy2(dst, os.path.join(pre_dir, n))
        shutil.copy2(src, dst)
        same = sha(dst) == sha(src)
        print('  已还原 -> 校验 %s' % ('通过' if same else '失败'))
        if not same:
            raise SystemExit('[中止] 校验失败: %s' % dst)
    if not a.dry_run and os.path.isdir(pre_dir):
        print('\n回滚前的线上文件已留档:', pre_dir)
    if 'USER.CFG' in names:
        print('\n警告：USER.CFG 里记录的是旧存档路径；若游戏提示找不到存档目录，')
        print('      请运行 工具\\fix_savedata_path.py 或 工具\\rebuild_usercfg.py 修正路径。')


if __name__ == '__main__':
    main()
