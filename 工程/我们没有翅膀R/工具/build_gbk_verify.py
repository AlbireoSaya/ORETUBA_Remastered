# -*- coding: utf-8 -*-
"""构建「GBK 中文显示」实机验证副本（ISSUE-ORETUBAR-R）。

产物：E:\\ZCode Workspace\\Galgame\\_VERIFY\\GBK\\
  ├─ ORETSUBA_R\\                  游戏副本（纯 ASCII 路径）
  │    ├─ ORETUBAR.EXE             ← 已打 GBK 补丁（字符集 + 前导字节判定）
  │    ├─ SCRIPT.LPK               ← 含 GBK 中文测试文本的 s00_00.tob
  │    └─ USER.CFG                 ← 指向本副本的存档目录
  └─ ORETSUBA_R SaveData\\         存档目录（GAMEDATA.DAT 全解锁等）
       └─ USER.CFG

用法：
  python -X utf8 build_gbk_verify.py            # 全量构建 + 自检
  python -X utf8 build_gbk_verify.py --no-copy  # 跳过游戏本体复制（副本已存在时）
"""
import os, re, sys, json, shutil, subprocess

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lpk_patch as P
import exe_gbk_patch as X

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
SRC_GAME = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R')
SRC_SAVE = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R SaveData')
DST_ROOT = os.path.join(WS, '_VERIFY', 'GBK')
GAME = os.path.join(DST_ROOT, 'ORETSUBA_R')
SAVE = os.path.join(DST_ROOT, 'ORETSUBA_R SaveData')
APPDATA_DIRNAME = '壌偨偪偵梼偼側偄俼 SaveData'   # %APPDATA% 下的目录（实测名）
TEST_CN = '【中文渲染测试】你好，世界！ABC 123'
TARGET_TOB = 's00_00.tob'

SKIP_COPY = {'SCRIPT.LPK', 'ORETUBAR.EXE'}


def step0_copy():
    print('=== 0. 复制游戏本体到 %s ===' % GAME)
    os.makedirs(GAME, exist_ok=True)
    r = subprocess.run(['robocopy', SRC_GAME, GAME, '/E', '/MT:8', '/NFL', '/NDL', '/NJH', '/NJS',
                        '/XF', *sorted(SKIP_COPY)],
                       capture_output=True, text=True, errors='replace')
    print('  robocopy 退出码 %s' % r.returncode)
    if r.returncode >= 8:
        print(r.stdout[-2000:]); raise SystemExit('复制失败')


def step1_patch_exe():
    print()
    print('=== 1. 打 EXE 补丁（字符集 + 前导字节判定）===')
    src = os.path.join(SRC_GAME, 'ORETUBAR.EXE')
    dst = os.path.join(GAME, 'ORETUBAR.EXE')
    rep = os.path.join(DST_ROOT, 'exe_patch_report.json')
    plan, checks = X.apply_patch(src, dst, rep)
    print('  自检:', end=' ')
    ok = X.verify_patched(dst)
    if not ok:
        raise SystemExit('EXE 补丁校验失败')
    return plan, checks


def step2_build_test_tob():
    print()
    print('=== 2. 生成含 GBK 中文的 %s ===' % TARGET_TOB)
    rows = json.load(open(os.path.join(PROJ, '语料', 'R版台词.json'), encoding='utf-8'))
    target = None
    for r in rows:
        if r['file'] == TARGET_TOB and r.get('kind') == 'title' and r.get('offset'):
            target = r
            break
    if not target:
        raise SystemExit('未找到 title 槽')
    print('  目标槽 offset=0x%x len=%d 原文=%r' % (target['offset'], target['len'], target['text']))
    mp = os.path.join(DST_ROOT, 'patch_map.json')
    json.dump([{'offset': target['offset'], 'len': target['len'], 'text': TEST_CN}],
              open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    out = os.path.join(DST_ROOT, TARGET_TOB)
    rr = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, 'tob_rewrite.py'),
                         'rebuild', os.path.join(PROJ, '语料', 'R版SCRIPT', TARGET_TOB),
                         mp, out, '--enc', 'gbk'],
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('\n'.join('  ' + l for l in ((rr.stdout or '') + (rr.stderr or '')).splitlines()[:10]))
    if not os.path.exists(out):
        raise SystemExit('rebuild 未产出')
    b = open(out, 'rb').read()
    for probe in ('【', '中', '文', '，', '！'):
        if probe.encode('gbk') not in b:
            raise SystemExit('中文未写入: %r' % probe)
    print('  ✔ GBK 中文已写入（%d 字节，原 %d 字节）' %
          (len(b), os.path.getsize(os.path.join(PROJ, '语料', 'R版SCRIPT', TARGET_TOB))))
    return out


def step3_patch_lpk(tob):
    print()
    print('=== 3. 打进 SCRIPT.LPK（二进制补丁）===')
    new_plain = open(tob, 'rb').read()
    out_lpk = os.path.join(GAME, 'SCRIPT.LPK')
    info = P.patch(os.path.join(SRC_GAME, 'SCRIPT.LPK'), out_lpk, {TARGET_TOB: new_plain})
    print('  %d 字节 -> %d 字节；改动条目 %s；条目总数 %d' %
          (info['in_size'], info['out_size'], info['changed'], info['n_entries']))
    # 回读校验
    lp_new = P.load(out_lpk)
    chk = P.read_entry(lp_new, TARGET_TOB)
    print('  回读 %s：%d 字节，与改后文件一致: %s；含中文标记: %s' %
          (TARGET_TOB, len(chk['plain']), chk['plain'] == new_plain, '【'.encode('gbk') in chk['plain']))
    if chk['plain'] != new_plain:
        raise SystemExit('LPK 回读不一致')
    # 其他条目逐一比对（明文层面）
    lp_old = P.load(os.path.join(SRC_GAME, 'SCRIPT.LPK'))
    bad = []
    for n, num in lp_old['ents']:
        if n == TARGET_TOB:
            continue
        a = P.read_entry(lp_old, n)['plain']
        bb = P.read_entry(lp_new, n)['plain']
        if a != bb:
            bad.append(n)
    print('  其余 %d 条目明文逐字节一致: %s' % (len(lp_old['ents']) - 1, 'YES' if not bad else bad[:5]))
    if bad:
        raise SystemExit('其他条目被改动')
    return out_lpk


def step4_savedata():
    print()
    print('=== 4. 存档目录与 USER.CFG ===')
    os.makedirs(SAVE, exist_ok=True)
    for f in os.listdir(SRC_SAVE):
        if f.upper() == 'USER.CFG':
            continue
        shutil.copy2(os.path.join(SRC_SAVE, f), os.path.join(SAVE, f))
    unlock = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
    if os.path.exists(unlock):
        shutil.copy2(unlock, os.path.join(SAVE, 'GAMEDATA.DAT'))
        print('  已上线全解锁 GAMEDATA.DAT')
    # USER.CFG：以「原始存档目录的 USER.CFG」为模板，改写路径段
    tmpl = os.path.join(SRC_SAVE, 'USER.CFG')
    raw = open(tmpl, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    new_seg = os.fsencode(os.path.abspath(SAVE)) + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = new_seg
    pre = m.start() - 2
    synced = False
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(new_seg) - 1).to_bytes(2, 'little')
        synced = True
    paths = [os.path.join(SAVE, 'USER.CFG'), os.path.join(GAME, 'USER.CFG'),
             os.path.join(os.environ['APPDATA'], APPDATA_DIRNAME, 'USER.CFG')]
    for p in paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            os.replace(p, p + '.prev')
        open(p, 'wb').write(bytes(out))
        print('  [USER.CFG] %s' % p)
    print('  路径段 -> %s（长度前缀同步: %s）' % (new_seg[:-1].decode('ascii'), synced))
    # 校验
    for p in paths:
        rb = open(p, 'rb').read()
        mm = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', rb)
        assert mm.group(0) == new_seg, 'USER.CFG 路径不符: %s' % p
    print('  三份 USER.CFG 路径段校验通过')
    return paths


def main():
    do_copy = '--no-copy' not in sys.argv
    os.makedirs(DST_ROOT, exist_ok=True)
    if do_copy:
        step0_copy()
    else:
        assert os.path.isdir(GAME), '副本不存在'
    step1_patch_exe()
    tob = step2_build_test_tob()
    step3_patch_lpk(tob)
    step4_savedata()
    print()
    print('=' * 78)
    print('构建完成。实机验证入口:')
    print('  %s' % os.path.join(GAME, 'ORETUBAR.EXE'))
    print('（存档目录: %s）' % SAVE)
    print('应看到：序章标题位置显示「%s」而非乱码。' % TEST_CN)


if __name__ == '__main__':
    main()
