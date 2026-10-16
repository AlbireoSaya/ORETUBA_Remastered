# -*- coding: utf-8 -*-
"""层序实验 · 两变量分开跑。

  round P : 只改【位置枚举】= CharacterOpen(0x1C43C) 的第 4 个实参（文件偏移 call_file-20）
  round S : 只改【槽号】      = 开立节点的第 1 个实参（文件偏移 call_file-44）—— 上轮改的就是这一格
  restore : 还原到原始件
  show    : 只读核对

用法:  python patch_round.py P|S|restore|show
"""
import sys, os, shutil, hashlib, struct

GAME = r'E:\ZCode Workspace\Galgame\临时\layer_exp\game\SCRIPT_CHS'
SOB  = os.path.join(GAME, 's01_04i.sob')
BAK  = SOB + '.bak'            # 原始未打任何补丁的副本
sys.path.insert(0, r'E:\ZCode Workspace\Galgame\临时\wt-ns\工程\我们没有翅膀——格雷塔迦露德与柳木原\编程组\新源侧\EXE')
from _probe_12_funclib import Sob
from _probe_17_scene_args import calls_of
import _probe_19_layer_exp as P19

# —— 不硬编码：用探针的 open_sites() 取真实格位 ——
#   槽号 = 逻辑 arg[0] 的单元（探针 slot_cell_file，已含 code_base）
#   位置枚举 = 逻辑 arg[3] 的单元 = 槽号单元 + 8*3（同一节点内向后 3 个 push）
_sob = Sob(SOB)
_rows = [r for r in P19.open_sites(_sob) if (r[3] or '').startswith('ASU')]
ASU_SLOT_CELL = [r[5] for r in _rows if r[5] is not None]
# 位置枚举：**只取 0x1C43C 族的两个节点**（其 argc=6，逻辑 arg[3] = 槽号格 + 24）。
# 0x14084 族 argc=3，同节点内没有 arg[3]；PAIR 称其枚举在配对的 0x17514 节点，本轮不碰。
# 已用字节核对：0x3050 与 0x30F4 正是 0x1C43C 两次开立（ASU02 / ASU02A）的第 4 个 push。
ASU_ENUM_CELL = [0x3050, 0x30F4]

def md5(b): return hashlib.md5(b).hexdigest()

def dump(tag, d):
    s = [struct.unpack_from('<i', d, c)[0] for c in ASU_SLOT_CELL]
    e = [struct.unpack_from('<i', d, c)[0] for c in ASU_ENUM_CELL]
    print('%s\n   明日香 槽号格 = %s\n   明日香 枚举格 = %s  (0=中央? 2=右?)' % (tag, s, e))

mode = (sys.argv[1] if len(sys.argv) > 1 else 'show').upper()
if not os.path.exists(BAK):
    sys.exit('缺少原始备份 %s' % BAK)
d = bytearray(open(SOB, 'rb').read())

if mode == 'SHOW':
    dump('当前：', d)
elif mode == 'RESTORE':
    shutil.copyfile(BAK, SOB)
    d = bytearray(open(SOB, 'rb').read()); dump('已还原：', d)
elif mode in ('P', 'S'):
    dump('改前：', d)
    cells = ASU_ENUM_CELL if mode == 'P' else ASU_SLOT_CELL
    for c in cells:
        struct.pack_into('<i', d, c, 2)
    open(SOB, 'wb').write(d)
    print('已应用 round %s（改了 %d 格 -> 2）  新 md5=%s' % (mode, len(cells), md5(bytes(d))))
    dump('改后：', bytearray(open(SOB, 'rb').read()))
else:
    sys.exit('未知参数 %s' % mode)
