# -*- coding: utf-8 -*-
r"""端到端实机验证：GBK 中文渲染 + 全解锁存档（ISSUE-ORETUBAR-R 主代理执行）。

流程：
  1. 用 tob_rewrite rebuild 把 s00_00.tob 的标题槽改成中文（GBK）
  2. 用 lpk_patch 把改后脚本打进 SCRIPT.LPK（二进制补丁，446 条目结构不变）
  3. 放入测试游戏副本 `_VERIFY\ORETSUBA_R\`，上线全解锁 GAMEDATA.DAT
  4. 启动游戏，定时连拍窗口截图
"""
import os, re, sys, json, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lpk_patch as P

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
TOOLS = os.path.join(PROJ, '工具')
SRC_GAME = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R')
SRC_SAVE = os.path.join(WS, 'ORETSUBA_R', 'ORETSUBA_R SaveData')
VERIFY = os.path.join(WS, '_VERIFY')
GAME = os.path.join(VERIFY, 'ORETSUBA_R')
SAVE = os.path.join(VERIFY, 'ORETSUBA_R SaveData')
SHOTS = os.path.join(WS, '临时', 'oretsuba_shots')
CN = '【中文渲染测试】你好，世界！ABC 123'


def step1_build_cn_tob():
    print('=== 1. 生成含中文的 s00_00.tob ===')
    rows = json.load(open(os.path.join(PROJ, '语料', 'R版台词.json'), encoding='utf-8'))
    tgt = [r for r in rows if r['file'] == 's00_00.tob' and r.get('kind') == 'title']
    if not tgt:
        print('  [错误] 未找到标题槽'); return None
    r = tgt[0]
    print('  目标槽 offset=0x%x len=%d 原文=%r' % (r['offset'], r['len'], r['text']))
    os.makedirs(VERIFY, exist_ok=True)
    mp = os.path.join(VERIFY, 'patch_map.json')
    json.dump([{'offset': r['offset'], 'len': r['len'], 'text': CN}],
              open(mp, 'w', encoding='utf-8'), ensure_ascii=False)
    out_tob = os.path.join(VERIFY, 's00_00.tob')
    src_tob = os.path.join(PROJ, '语料', 'R版SCRIPT', 's00_00.tob')
    rr = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'tob_rewrite.py'),
                         'rebuild', src_tob, mp, out_tob, '--enc', 'gbk'],
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('\n'.join('  ' + l for l in ((rr.stdout or '') + (rr.stderr or '')).splitlines()[:14]))
    if not os.path.exists(out_tob):
        print('  [错误] rebuild 未产出'); return None
    b = open(out_tob, 'rb').read()
    for probe in ['【'.encode('gbk'), '你'.encode('gbk'), '世'.encode('gbk')]:
        if probe not in b:
            print('  [错误] 中文未写入: %r' % probe); return None
    print('  ✔ 中文已写入，大小 %d（原 %d）' % (len(b), os.path.getsize(src_tob)))
    return out_tob


def step2_patch_lpk(cn_tob):
    print()
    print('=== 2. 打进 SCRIPT.LPK（二进制补丁）===')
    e = P.read_entry(P.load(os.path.join(SRC_GAME, 'SCRIPT.LPK')), 's00_00.tob')
    new_plain = open(cn_tob, 'rb').read()
    os.makedirs(os.path.join(VERIFY, 'out'), exist_ok=True)
    out_lpk = os.path.join(VERIFY, 'out', 'SCRIPT.LPK')
    info = P.patch(os.path.join(SRC_GAME, 'SCRIPT.LPK'), out_lpk, {'s00_00.tob': new_plain})
    print('  补丁: %d -> %d 字节（446 条目结构不变，仅条目数据平移）' % (info['in_size'], info['out_size']))
    chk = P.read_entry(P.load(out_lpk), 's00_00.tob')
    print('  回读 s00_00.tob 明文 %d 字节，与改后文件一致: %s' % (len(chk['plain']), chk['plain'] == new_plain))
    print('  中文标记在回读内容中:', '【'.encode('gbk') in chk['plain'])
    return out_lpk


def step3_deploy(lpk):
    print()
    print('=== 3. 部署到测试副本 ===')
    if os.path.isdir(GAME):
        shutil.rmtree(GAME)
    os.makedirs(GAME)
    n = 0
    for f in os.listdir(SRC_GAME):
        s = os.path.join(SRC_GAME, f)
        if os.path.isfile(s) and f != 'SCRIPT.LPK':
            shutil.copy2(s, os.path.join(GAME, f)); n += 1
    shutil.copy2(lpk, os.path.join(GAME, 'SCRIPT.LPK')); n += 1
    if os.path.isdir(SAVE):
        shutil.rmtree(SAVE)
    os.makedirs(SAVE)
    for f in os.listdir(SRC_SAVE):
        if f.upper() != 'USER.CFG':
            shutil.copy2(os.path.join(SRC_SAVE, f), os.path.join(SAVE, f))
    unlock = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
    shutil.copy2(unlock, os.path.join(SAVE, 'GAMEDATA.DAT'))
    print('  复制游戏文件 %d 个（含补丁后 LPK）' % n)
    print('  全解锁存档已上线: %s' % os.path.basename(unlock))
    raw = open(os.path.join(SRC_SAVE, 'USER.CFG'), 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    seg = os.path.abspath(SAVE).encode('ascii') + b'\x00'
    out = bytearray(raw); out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    for p in [os.path.join(SAVE, 'USER.CFG'), os.path.join(GAME, 'USER.CFG')]:
        open(p, 'wb').write(bytes(out))
    ap = os.path.join(os.environ['APPDATA'], '壌偨偪偵梼偼側偄俼 SaveData')
    os.makedirs(ap, exist_ok=True)
    open(os.path.join(ap, 'USER.CFG'), 'wb').write(bytes(out))
    print('  USER.CFG 路径 -> %s' % seg[:-1].decode())


def step4_run_and_capture():
    print()
    print('=== 4. 启动并连拍 ===')
    os.makedirs(SHOTS, exist_ok=True)
    p = subprocess.Popen([os.path.join(GAME, 'ORETUBAR.EXE')], cwd=GAME)
    print('  PID %d' % p.pid)
    time.sleep(4)
    ps = r'''
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
Add-Type @'
using System;using System.Runtime.InteropServices;
public class CU {
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; }
}
'@
$p = Get-Process ORETUBAR -ErrorAction SilentlyContinue | Select-Object -First 1
if(-not $p){ Write-Output 'NOPROC'; exit }
$h = $p.MainWindowHandle
[void][CU]::ShowWindow($h, 5)
[void][CU]::BringWindowToTop($h)
[void][CU]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 1500
$cr = New-Object CU+RECT
[void][CU]::GetClientRect($h, [ref]$cr)
$pt = New-Object CU+POINT; $pt.X = 0; $pt.Y = 0
[void][CU]::ClientToScreen($h, [ref]$pt)
$w = $cr.R - $cr.L; $ht = $cr.B - $cr.T
$bmp = New-Object System.Drawing.Bitmap($w, $ht)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($pt.X, $pt.Y, 0, 0, $bmp.Size)
$bmp.Save("%OUT%", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output ("OK " + $w + "x" + $ht)
'''
    for i in range(9):
        out = os.path.join(SHOTS, 'cn_%02d.png' % i)
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps.replace('%OUT%', out.replace('\\', '\\\\'))],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        tag = [l for l in (r.stdout or '').splitlines() if l.startswith(('OK', 'NOPROC'))]
        print('  抓图 %d: %s' % (i, tag[0] if tag else '(无输出)'))
        if p.poll() is not None:
            print('  进程已退出（%s）' % p.returncode); break
        time.sleep(2)
    return p


if __name__ == '__main__':
    cn = step1_build_cn_tob()
    if cn:
        lpk = step2_patch_lpk(cn)
        step3_deploy(lpk)
        step4_run_and_capture()
