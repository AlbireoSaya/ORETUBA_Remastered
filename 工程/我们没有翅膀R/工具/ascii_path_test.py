# -*- coding: utf-8 -*-
r"""对照实验：把游戏放到纯 ASCII 路径下运行，判定「多字节父目录（工程）」是否为
「セーブデータ作成フォルダが見つかりません」的成因。

原版 2009 的路径就是纯 ASCII（D:\Gal\[Navel]我们没有翅膀\），可正常运行；
R 版当前路径含双字节父目录「工程」，若 ASCII 路径下不再报错，即证实成因。
"""
import os, re, sys, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC = os.path.join(BASE, 'ORETSUBA_R')
TEST_ROOT = r'E:\ZCode Workspace\Galgame\临时\ASC_TEST'      # 本层仍含中文「临时」——先测
TEST_ROOT2 = r'E:\ZCode Workspace\Galgame\_ASC_TEST'          # 纯 ASCII 顶层（备选）

KEEP = ['ORETUBAR.EXE', 'tvpgl.dll', 'wuvorbis.dll', 'DS_MOVIE.DLL', 'DS_SPRITE.DLL',
        'SCRIPT.LPK', 'DATA.LPK', 'SYS.LPK', 'PIC.LPK', 'CHR.LPK', 'BGM.LPK', 'SE.LPK',
        'USER.CFG', 'SET_UP.IFG', 'READ_ME.TXT', 'UserConfig.exe', 'DataLink.exe', 'UNINST.EXE']


def setup(root):
    game = os.path.join(root, 'ORETSUBA_R')
    if os.path.isdir(game):
        shutil.rmtree(game)
    os.makedirs(game)
    for f in KEEP:
        s = os.path.join(SRC, f)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(game, f))
    sd_src = os.path.join(BASE, 'ORETSUBA_R SaveData')
    sd_dst = os.path.join(root, 'ORETSUBA_R SaveData')
    if os.path.isdir(sd_dst):
        shutil.rmtree(sd_dst)
    shutil.copytree(sd_src, sd_dst)
    return game, sd_dst


def patch_usercfg(game, sd_path):
    """把 USER.CFG 里的路径段改成 sd_path（ASCII 编码）。"""
    uc = os.path.join(game, 'USER.CFG')
    raw = open(uc, 'rb').read()
    m = re.search(rb'E:\\[^\x00]{0,240}\x00', raw)
    if not m:
        print('  [警告] USER.CFG 未含路径串'); return
    new_seg = os.fsencode(sd_path) + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = new_seg
    # 同步 2 字节长度前缀
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(new_seg) - 1).to_bytes(2, 'little')
        print('  长度前缀已同步为 %d' % (len(new_seg) - 1))
    open(uc, 'wb').write(bytes(out))
    print('  USER.CFG 路径 -> %s' % sd_path)
    # 同步 AppData 副本
    ap = os.path.join(os.environ['APPDATA'], '壌偨偪偵梼偼側偄俼 SaveData', 'USER.CFG')
    if os.path.exists(ap):
        r2 = open(ap, 'rb').read()
        m2 = re.search(rb'E:\\[^\x00]{0,240}\x00', r2)
        if m2:
            o2 = bytearray(r2)
            o2[m2.start():m2.end()] = new_seg
            p2 = m2.start() - 2
            if int.from_bytes(r2[p2:p2 + 2], 'little') == len(m2.group(0)) - 1:
                o2[p2:p2 + 2] = (len(new_seg) - 1).to_bytes(2, 'little')
            open(ap, 'wb').write(bytes(o2))
            print('  AppData USER.CFG 已同步')


def run(game, wait=13):
    p = subprocess.Popen([os.path.join(game, 'ORETUBAR.EXE')], cwd=game)
    time.sleep(wait)
    alive = p.poll() is None
    return p, alive


def probe_windows(pid):
    """用 PowerShell 抓窗口与子控件文本，判断是否仍为报错对话框。"""
    ps = r'''
$OutputEncoding=[Text.Encoding]::UTF8
Add-Type @'
using System;using System.Text;using System.Collections.Generic;using System.Runtime.InteropServices;
public class P2 {
  public delegate bool E(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(E cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, E cb, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  public static List<IntPtr> ForPid(uint t){ var r=new List<IntPtr>(); EnumWindows((h,l)=>{ uint p; GetWindowThreadProcessId(h,out p); if(p==t) r.Add(h); return true;}, IntPtr.Zero); return r; }
  public static List<string> Ch(IntPtr p){ var r=new List<string>(); EnumChildWindows(p,(h,l)=>{ var sb=new StringBuilder(600); GetWindowTextW(h,sb,600); if(sb.Length>0) r.Add(sb.ToString()); return true;}, IntPtr.Zero); return r; }
  public static string T(IntPtr h){ var sb=new StringBuilder(600); GetWindowTextW(h,sb,600); return sb.ToString(); }
}
'@
foreach($h in [P2]::ForPid(%PID%)){
  Write-Output ("WIN " + [P2]::T($h))
  foreach($c in [P2]::Ch($h)){ Write-Output ("  CH " + $c) }
}
'''.replace('%PID%', str(pid))
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'temp_root'
    root = TEST_ROOT if mode == 'temp_root' else TEST_ROOT2
    print('=== 对照实验 root = %s ===' % root)
    game, sd = setup(root)
    print('文件数 %d，存档目录 %s' % (len(os.listdir(game)), sd))
    patch_usercfg(game, sd)
    p, alive = run(game)
    print('进程 %d 仍在运行: %s' % (p.pid, alive))
    print('--- 窗口文本 ---')
    print(probe_windows(p.pid))
    if alive:
        p.kill()
        print('已结束进程')


if __name__ == '__main__':
    main()
