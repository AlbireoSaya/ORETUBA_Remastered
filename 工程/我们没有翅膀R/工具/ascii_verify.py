# -*- coding: utf-8 -*-
r"""ASCII 路径验证 + 部署（ISSUE-ORETUBAR-R）

结论前提（实测）：
  * 本作把「存档目录绝对路径」以 **Shift-JIS** 写入 USER.CFG；
  * 「我们没有翅膀R」含简体字（们/没/翅/膀），**在 Shift-JIS 中不存在**，
    该路径无法被引擎表示 → 游戏路径必须纯 ASCII；
  * 原版 2009 能跑，正是因为它位于 `D:\Gal\[Navel]我们没有翅膀\`（纯 ASCII 父目录，
    仅末端日文名，SJIS 可表示）。

本脚本：
  1) 把游戏复制到 `工程\我们没有翅膀R\ORETSUBA_R\`（ASCII 游戏名，父目录含中文，用于对照）
  2) 再把同一份复制到 `_ASC_TEST\ORETSUBA_R\`（纯 ASCII 全路径，对照组）
  3) 用原版结构模板写 USER.CFG，逐一启动，报告是否出现
     「セーブデータ作成フォルダが見つかりません」对话框
"""
import os, re, sys, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
SRC_GAME = os.path.join(BASE, 'ORETSUBA_R')
SRC_SAVE = os.path.join(BASE, 'ORETSUBA_R SaveData')
TEMPLATE = os.path.join(BASE, '存档备份', 'AppData_USER.CFG.orig')
APPDATA_DIR = os.path.join(os.environ['APPDATA'], '壌偨偪偵梼偼側偄俼 SaveData')

DIALOG_MARK = 'セーブデータ作成フォルダ'   # 目标对话框特征串（窗口文本为 SJIS 误读，用长度/结构判定）


def build_usercfg(save_dir_bytes: bytes) -> bytes:
    raw = open(TEMPLATE, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    assert m, '模板中未找到路径段'
    seg = save_dir_bytes + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    return bytes(out)


def probe(pid):
    """返回该进程的可见窗口 (标题, 尺寸, 子控件文本列表)。"""
    ps = r'''
$OutputEncoding=[Text.Encoding]::UTF8
Add-Type @'
using System;using System.Text;using System.Collections.Generic;using System.Runtime.InteropServices;
public class PV {
  public delegate bool E(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(E cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, E cb, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
  public static List<string> ForPid(uint t){
    var res=new List<string>();
    EnumWindows((h,l)=>{ uint p; GetWindowThreadProcessId(h,out p);
      if(p==t && IsWindowVisible(h)){
        var sb=new StringBuilder(600); GetWindowTextW(h,sb,600);
        var r=new RECT(); GetWindowRect(h, out r);
        var ch=new List<string>();
        EnumChildWindows(h,(c,l2)=>{ var s2=new StringBuilder(600); GetWindowTextW(c,s2,600); if(s2.Length>0) ch.Add(s2.ToString()); return true;}, IntPtr.Zero);
        res.Add(sb.ToString()+"|"+(r.R-r.L)+"x"+(r.B-r.T)+"|"+String.Join(" ;; ", ch));
      } return true;}, IntPtr.Zero);
    return res;
  }
}
'@
foreach($w in [PV]::ForPid(%PID%)){ Write-Output $w }
'''.replace('%PID%', str(pid))
    r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return [l for l in r.stdout.splitlines() if l.strip()]


def ensure_pristine():
    """准备一份「原始游戏 + 用户原始存档」的干净来源（只读，供两用例复制）。"""
    global SRC_GAME, SRC_SAVE
    pristine_game = os.path.join(BASE, '_pristine', 'game')
    pristine_save = os.path.join(BASE, '存档备份', '用户原始存档')
    if not os.path.isdir(pristine_game):
        os.makedirs(pristine_game, exist_ok=True)
        live = os.path.join(BASE, 'ORETSUBA_R')
        for f in os.listdir(live):
            s = os.path.join(live, f)
            if os.path.isfile(s):
                shutil.copy2(s, os.path.join(pristine_game, f))
    SRC_GAME = pristine_game
    SRC_SAVE = pristine_save
    print('干净来源: %s (%d 文件) / %s (%d 文件)'
          % (pristine_game, len(os.listdir(pristine_game)),
             pristine_save, len(os.listdir(pristine_save))))


def run_case(label, root):
    game = os.path.join(root, 'ORETSUBA_R')
    save = os.path.join(root, 'ORETSUBA_R SaveData')
    print('=' * 70)
    print('用例: %s' % label)
    print('  路径: %s' % root)
    if os.path.isdir(game):
        shutil.rmtree(game)
    os.makedirs(game)
    n = 0
    for f in os.listdir(SRC_GAME):
        s = os.path.join(SRC_GAME, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(game, f)); n += 1
    os.makedirs(save, exist_ok=True)
    for f in os.listdir(SRC_SAVE):
        if not f.upper().endswith('.CFG'):
            shutil.copy2(os.path.join(SRC_SAVE, f), os.path.join(save, f))
    print('  复制文件 %d 个；存档目录 %s' % (n, os.path.basename(save)))

    cfg = build_usercfg(os.path.abspath(save).encode('ascii'))
    open(os.path.join(save, 'USER.CFG'), 'wb').write(cfg)
    open(os.path.join(game, 'USER.CFG'), 'wb').write(cfg)
    os.makedirs(APPDATA_DIR, exist_ok=True)
    open(os.path.join(APPDATA_DIR, 'USER.CFG'), 'wb').write(cfg)
    print('  USER.CFG 路径段: %s' % cfg.decode('ascii', 'replace').split('\x00')[1].strip()[:120])

    p = subprocess.Popen([os.path.join(game, 'ORETUBAR.EXE')], cwd=game)
    time.sleep(15)
    alive = p.poll() is None
    wins = probe(p.pid)
    print('  进程 %d 存活: %s' % (p.pid, alive))
    for w in wins:
        title, size, children = w.split('|', 2)
        print('    窗口 [%s] %s' % (size, title))
        if children.strip():
            print('      子控件: %s' % children[:200])
    # 判定：出现 486x185 之类的报错框
    bad = any(s.split('|')[1].startswith(('2', '3', '4')) and len(c.strip()) > 20 for s, c in
              [(w.split('|')[1], w.split('|')[2]) for w in wins])
    print('  → 判定: %s' % ('**仍出现对话框（有问题）**' if bad else '未见对话框（正常进入游戏）'))
    if alive:
        p.kill()
        time.sleep(1)
    return not bad


if __name__ == '__main__':
    ensure_pristine()
    ok_cn = run_case('中文父目录 + ASCII 游戏名', BASE)
    ok_ascii = run_case('纯 ASCII 全路径', r'E:\ZCode Workspace\Galgame\_ASC_TEST')
    print()
    print('结论: 中文父目录 %s ｜ 纯 ASCII %s' % ('OK' if ok_cn else 'FAIL', 'OK' if ok_ascii else 'FAIL'))
