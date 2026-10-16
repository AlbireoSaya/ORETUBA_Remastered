# -*- coding: utf-8 -*-
r"""重建 USER.CFG（正确版）——路径段一律取「磁盘真实字节」，不手打字符。

本作（Lucifen / Easy Game System DX）启动时**必须**能读到 USER.CFG，否则弹
「環境設定ファイルの読み込みに失敗」；而 USER.CFG 内含「存档目录绝对路径」，
目录移动后该路径失效，于是弹「セーブデータ作成フォルダが見つかりません」。

关键教训（实测）：
  手打中文字符串再 encode('cp932') 会得到与 Windows 目录枚举 API 不同的字节
  （GBK/CP932 转换差异），游戏据此校验会判定目录不存在。
  → 必须用 os.fsencode(真实目录名) 取字节。

USER.CFG 结构（实测 174~211 字节）：
  [0x00, P-2)   头部：配置位 + 浮点（音量/窗口位置）等
  [P-2, P)      路径长度前缀（u16 little-endian = 路径字节数）
  [P, ...)      存档目录绝对路径（SJIS 字节 + NUL）
"""
import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀R'
EXCLUDE = {'参照', '语料', '工具', '存档备份', '存档候选', '作品skill'}
GAME = 'ORETSUBA_R'
SAVE = GAME + ' SaveData'


def real_bytes(path):
    """取路径在文件系统上的真实字节（不做 Unicode 往返）。"""
    return os.fsencode(os.path.abspath(path))


def rebuild(template_path, target_save_dir, out_paths):
    raw = open(template_path, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    if not m:
        print('[错误] 模板中没有路径串:', template_path); return False
    new_seg = real_bytes(target_save_dir) + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = new_seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(new_seg) - 1).to_bytes(2, 'little')
        synced = True
    else:
        synced = False
    print('模板: %s (%d 字节)' % (template_path, len(raw)))
    print('  原路径段 %d 字节: %r' % (len(m.group(0)) - 1, m.group(0)[:-1]))
    print('  新路径段 %d 字节: %r  [长度前缀同步: %s]' % (len(new_seg) - 1, new_seg[:-1], synced))
    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            os.replace(p, p + '.prev')
        open(p, 'wb').write(bytes(out))
        print('  [写出] %s (%d 字节)' % (p, len(out)))
    return True


def main():
    game_dir = os.path.join(BASE, GAME)
    save_dir = os.path.join(BASE, SAVE)

    # 优先级：原版 2009 的 USER.CFG（同引擎、同结构）> 本作旧配置备份
    templates = [
        r'D:\Gal\[Navel]我们没有翅膀\我们没有翅膀\USER.CFG',
        os.path.join(BASE, '存档备份', 'AppData_USER.CFG.orig'),
    ]
    # 原版的 USER.CFG 位置可能不同，探测一下
    cand = []
    for t in templates:
        if os.path.exists(t):
            cand.append(t)
        else:
            print('[跳过] 模板不存在:', t)
    # 再扫一遍原版目录里的 USER.CFG
    for root in [r'D:\Gal\[Navel]我们没有翅膀', r'D:\Gal\[Navel]我们没有翅膀\我们没有翅膀']:
        if os.path.isdir(root):
            p = os.path.join(root, 'USER.CFG')
            if os.path.exists(p) and p not in cand:
                cand.append(p)
    if not cand:
        print('[错误] 找不到可用模板'); return
    tpl = cand[0]
    print('使用模板:', tpl)
    print()
    targets = [
        os.path.join(save_dir, 'USER.CFG'),                                        # 存档目录（游戏读取源）
        os.path.join(game_dir, 'USER.CFG'),                                        # 安装目录副本
        os.path.join(os.environ['APPDATA'], '壌偨偪偵梼偼側偄俼 SaveData', 'USER.CFG'),
    ]
    rebuild(tpl, save_dir, targets)


if __name__ == '__main__':
    main()
