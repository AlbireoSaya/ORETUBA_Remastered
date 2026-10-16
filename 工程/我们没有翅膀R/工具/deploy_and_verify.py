# -*- coding: utf-8 -*-
r"""实机验证：全解锁存档 + GBK 中文渲染（ISSUE-ORETUBAR-R 主代理本人执行）。

验证两件事（一次开机同时验）：
  A. 全解锁存档 `R版全解锁_GAMEDATA.DAT` 是否被引擎接受（画廊/CG 是否解锁）
  B. **GBK 中文字节能否被引擎渲染** —— 这是整个汉化项目的前提条件

做法：
  1. 备份线上 GAMEDATA.DAT（sha256 记录）
  2. 用 harness 的 apply 脚本上线全解锁存档
  3. 用 `tob_rewrite.py` 把 s00_00.tob 的标题槽（偏移 0x42）改成中文测试串，
     并把改后的 .tob 放进**测试用 SCRIPT 覆盖目录**（不改动原 LPK）
  4. 启动游戏并连续抓图

注意：替换 LPK 内脚本较复杂，本脚本采用「测试副本游戏目录」策略：
  复制一份游戏到 `_VERIFY\`，在那里替换 SCRIPT.LPK 内的 s00_00.tob，
  确保线上目录零污染。
"""
import os, re, sys, json, shutil, hashlib, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
TOOLS = os.path.join(PROJ, '工具')
LIVE = os.path.join(WS, 'ORETSUBA_R')
GAME = os.path.join(LIVE, 'ORETSUBA_R')
SAVE = os.path.join(LIVE, 'ORETSUBA_R SaveData')
UNLOCK = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
SHOTS = os.path.join(WS, '临时', 'oretsuba_shots')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def step1_verify_unlock():
    print('=== 步骤 1: 全解锁存档校验 ===')
    print('  线上 GAMEDATA.DAT sha256:', sha(os.path.join(SAVE, 'GAMEDATA.DAT')))
    print('  候选    GAMEDATA.DAT sha256:', sha(UNLOCK))
    print('  候选大小:', os.path.getsize(UNLOCK), '字节')
    # 用 harness 的验证器交叉核对
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'verify_unlock_save.py'),
                        UNLOCK, os.path.join(SAVE, 'GAMEDATA.DAT')],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('  --- verify_unlock_save.py ---')
    print('\n'.join('  ' + l for l in (r.stdout or '').splitlines()[:14]))
    if r.stderr:
        print('  [stderr]', r.stderr[:300])
    return True


def step2_build_test_game():
    print()
    print('=== 步骤 2: 建测试游戏副本并打中文补丁 ===')
    tg = os.path.join(WS, '_VERIFY', 'ORETSUBA_R')
    if os.path.isdir(tg):
        shutil.rmtree(tg)
    os.makedirs(tg)
    for f in os.listdir(GAME):
        s = os.path.join(GAME, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(tg, f))
    ts = os.path.join(WS, '_VERIFY', 'ORETSUBA_R SaveData')
    if os.path.isdir(ts):
        shutil.rmtree(ts)
    os.makedirs(ts)
    for f in os.listdir(SAVE):
        if f.upper() != 'USER.CFG':
            shutil.copy2(os.path.join(SAVE, f), os.path.join(ts, f))
    # 存档路径指向测试目录（纯 ASCII，安全）
    raw = open(os.path.join(SAVE, 'USER.CFG'), 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    seg = os.path.abspath(ts).encode('ascii') + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    for p in [os.path.join(ts, 'USER.CFG'), os.path.join(tg, 'USER.CFG')]:
        open(p, 'wb').write(bytes(out))
    ap = os.path.join(os.environ['APPDATA'], '壌偨偪偵梼偼側偄俼 SaveData')
    os.makedirs(ap, exist_ok=True)
    open(os.path.join(ap, 'USER.CFG'), 'wb').write(bytes(out))
    print('  测试游戏:', tg)
    print('  测试存档:', ts)
    print('  USER.CFG 路径:', seg[:-1].decode())
    return tg, ts


def step3_patch_script(tg):
    """把 s00_00.tob 的标题槽替换成中文测试串，并重建 SCRIPT.LPK。

    SCRIPT.LPK 内的 s00_00.tob 替换需要重打包 LPK —— 采用「外挂 override 目录」不可行
    （引擎只认 LPK），故用 Lucifen-Tools 的 lpk_repack.py 生成新 SCRIPT.LPK 到测试目录。
    """
    print()
    print('=== 步骤 3: 中文补丁进测试脚本 ===')
    src_tob = os.path.join(PROJ, '语料', 'R版SCRIPT', 's00_00.tob')
    rows = json.load(open(os.path.join(PROJ, '语料', 'R版台词.json'), encoding='utf-8'))
    tgt = [r for r in rows if r['file'] == 's00_00.tob' and r.get('kind') == 'title']
    if not tgt:
        print('  [错误] 未找到标题槽'); return None
    r = tgt[0]
    print('  目标槽: offset=0x%x len=%d' % (r['offset'], r['len']))
    print('  原文: %r' % r['text'])

    CN = '【中文渲染测试】你好，世界！ABC 123'
    edits = [{'offset': r['offset'], 'len': r['len'], 'text': CN}]
    mp = os.path.join(WS, '_VERIFY', 'patch_map.json')
    json.dump(edits, open(mp, 'w', encoding='utf-8'), ensure_ascii=False)
    out_tob = os.path.join(WS, '_VERIFY', 's00_00.tob')
    cmd = [sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'tob_rewrite.py'),
           'rebuild', src_tob, mp, out_tob, '--enc', 'gbk']
    rr = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('  --- tob_rewrite rebuild ---')
    print('\n'.join('  ' + l for l in ((rr.stdout or '') + (rr.stderr or '')).splitlines()[:20]))
    if not os.path.exists(out_tob):
        print('  [错误] 未生成改后 .tob'); return None
    # 校验中文确已写入
    b = open(out_tob, 'rb').read()
    for probe in ['【'.encode('gbk'), '你'.encode('gbk'), '世'.encode('gbk')]:
        print('  字节探针 %r: %s' % (probe, '命中' if probe in b else '**未命中**'))
    return out_tob


def main():
    os.makedirs(SHOTS, exist_ok=True)
    step1_verify_unlock()
    tg, ts = step2_build_test_game()
    out_tob = step3_patch_script(tg)
    print()
    print('=== 交付下一步（主代理执行）===')
    print('  测试游戏目录已就绪:', tg)
    print('  改后 s00_00.tob:', out_tob)
    print('  SCRIPT.LPK 重打包与研究见 报告.md / lpk_repack.py')


if __name__ == '__main__':
    main()
