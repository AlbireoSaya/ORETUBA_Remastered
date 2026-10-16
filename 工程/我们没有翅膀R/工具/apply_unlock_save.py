# -*- coding: utf-8 -*-
r"""一键部署：把 R 版全 CG/全回想解锁 GAMEDATA.DAT 装入存档目录（ISSUE-ORETUBAR-R 存档线）。

行为（严格按序，任一步失败即中止，不写线上文件）：
    1. 校验候选文件结构（头自洽 + LZSS 可解 + 条目取值合法）
    2. 备份当前线上 GAMEDATA.DAT → 工程\我们没有翅膀R\存档备份\自动备份\GAMEDATA.DAT.<时间戳>.bak
       （只新增文件，绝不覆盖 存档备份\用户原始存档\ 里的原始备份）
    3. 覆盖 存档目录\GAMEDATA.DAT
    4. 回读校验（sha256 与候选一致 + 结构可解 + 条目数/置位数与候选一致）
    5. 打印回滚命令

用法：
    python -X utf8 apply_unlock_save.py --dry-run     # 只看计划，不动任何文件
    python -X utf8 apply_unlock_save.py               # 真正执行
    python -X utf8 apply_unlock_save.py --candidate <路径> --save-dir <路径>
"""
import argparse
import datetime
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_unlock_save import load  # noqa: E402

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SAVE_DIR_DEFAULT = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R SaveData')
CAND_DEFAULT = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
AUTO_BAK_DIR = os.path.join(PROJ, '存档备份', '自动备份')
PRISTINE_DIR = os.path.join(PROJ, '存档备份', '用户原始存档')
TARGET_NAME = 'GAMEDATA.DAT'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def report_arr(path):
    raw, comp, uncomp, stream, arr = load(path)
    return dict(size=len(raw), comp=comp, uncomp=uncomp,
                ones=sum(1 for b in arr if b),
                odd=[(i, arr[i]) for i in range(len(arr)) if arr[i] not in (0, 1)],
                sha_stream_of_array=hashlib.sha256(arr).hexdigest())


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--candidate', default=CAND_DEFAULT)
    ap.add_argument('--save-dir', default=SAVE_DIR_DEFAULT)
    ap.add_argument('--bak-dir', default=AUTO_BAK_DIR, help='线上文件备份目录（默认 存档备份\\自动备份）')
    a = ap.parse_args()

    cand = a.candidate
    target = os.path.join(a.save_dir, TARGET_NAME)
    print('=== R 版全 CG/全回想解锁存档 部署 ===')
    print('候选文件 :', cand)
    print('存档目录 :', a.save_dir)
    print('目标文件 :', target)
    print('模式     :', 'DRY-RUN（不写任何文件）' if a.dry_run else '实际执行')

    if not os.path.isfile(cand):
        raise SystemExit('[中止] 候选文件不存在')
    if not os.path.isdir(a.save_dir):
        raise SystemExit('[中止] 存档目录不存在')

    # 1) 候选自检
    ci = report_arr(cand)
    print('\n[1] 候选自检: size=%d comp=%d uncomp=%d 置位=%d' %
          (ci['size'], ci['comp'], ci['uncomp'], ci['ones']))
    if ci['comp'] != ci['size'] - 8:
        raise SystemExit('[中止] 候选 comp 字段与文件长度不符')
    if ci['uncomp'] != 3910:
        raise SystemExit('[中止] 候选条目数异常: %d（应为 3910）' % ci['uncomp'])
    print('    结构 OK；展开数组 sha256 =', ci['sha_stream_of_array'])

    # 2) 备份当前线上文件
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    bak = os.path.join(a.bak_dir, '%s.%s.bak' % (TARGET_NAME, ts))
    pre = None
    if os.path.isfile(target):
        pre = dict(sha=sha(target), size=os.path.getsize(target))
        pi = report_arr(target)
        print('\n[2] 当前线上文件: size=%d sha256=%s 置位条目=%d 非0/1=%s'
              % (pre['size'], pre['sha'], pi['ones'], pi['odd']))
        print('    备份目标:', bak)
        if not a.dry_run:
            os.makedirs(a.bak_dir, exist_ok=True)
            shutil.copy2(target, bak)
            if sha(bak) != pre['sha']:
                raise SystemExit('[中止] 备份校验失败')
            print('    备份完成（校验通过）')
    else:
        print('\n[2] 当前线上文件不存在，跳过备份')

    # 3) 覆盖
    print('\n[3] 覆盖:', target)
    if a.dry_run:
        print('    （dry-run：跳过）')
    else:
        shutil.copy2(cand, target)
        # 4) 回读校验
        post = report_arr(target)
        ok = (sha(target) == sha(cand) and post['ones'] == ci['ones']
              and post['sha_stream_of_array'] == ci['sha_stream_of_array'])
        print('[4] 回读校验: sha256=%s 置位=%d 结构=%s -> %s'
              % (sha(target), post['ones'], 'OK', '通过' if ok else '失败'))
        if not ok:
            # 回滚刚才的写入
            if pre:
                shutil.copy2(bak, target)
                print('    [回滚] 已用备份还原:', bak)
            raise SystemExit('[中止] 回读校验失败，已回滚')
    print('\n[5] 回滚命令：')
    print('    python -X utf8 "%s" ' % os.path.join(PROJ, '工具', 'rollback_save.py'))
    if pre:
        print('    或手工还原备份：copy /Y "%s" "%s"' % (bak, target))
    print('\n注意：请勿用 存档备份\\用户原始存档\\USER.CFG 覆盖线上 USER.CFG——')
    print('      那份里的存档路径是旧路径（工程\\我们没有翅膀R\\...），会让游戏找不到存档目录。')


if __name__ == '__main__':
    main()
