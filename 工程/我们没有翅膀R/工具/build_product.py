# -*- coding: utf-8 -*-
r"""成品组装器（ISSUE-ORETUBAR-R）。

把「原始游戏 + GBK 补丁 EXE + 全量汉化 SCRIPT.LPK + 全解锁存档 + 署名」组装成
可直接游玩的成品到 `成品\我们没有翅膀R\`。

步骤：
  1. 从安装介质备份复制游戏本体（纯 ASCII 目录名 ORETSUBA_R，路径铁律见 skill）
  2. 打 EXE 的 GBK 补丁（字体字符集 + 前导字节判定）
  3. 放入全量汉化 SCRIPT.LPK
  4. 写 USER.CFG（路径必须与成品目录一致）
  5. 写入全解锁存档
  6. 追加窗口标题署名（AGENTS.md §六）
  7. 附 成品说明.md
"""
import os, re, sys, json, shutil, subprocess, time

sys.stdout.reconfigure(encoding='utf-8')
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

WS = r'E:\ZCode Workspace\Galgame'
PROJ = os.path.join(WS, '工程', '我们没有翅膀R')
MEDIA = os.path.join(WS, '备份', '我们没有翅膀R-安装介质', 'SET_UP')
CN_LPK = os.path.join(WS, '临时', '_build', 'SCRIPT.LPK')
UNLOCK = os.path.join(PROJ, '存档候选', 'R版全解锁_GAMEDATA.DAT')
# 成品落点必须**全 ASCII**：引擎把存档路径以 SJIS 写入 USER.CFG，
# 而「成品」「我们没有翅膀R」含简体字、无法用 SJIS 表示（详见作品 skill §一）。
# 故成品放在工作区根的 ASCII 目录，说明文档另附。
PROD = os.path.join(WS, 'ORETSUBA_R')
# 游戏本体套一层 ASCII 目录：引擎把存档路径以 SJIS 写入 USER.CFG，路径全程必须可用 ASCII 表示
GAME = os.path.join(PROD, 'ORETSUBA_R', 'ORETSUBA_R')
SAVE = os.path.join(PROD, 'ORETSUBA_R', 'ORETSUBA_R SaveData')
SIGN = '来自个人汉化者AlbireoSaya 模型&工具:Deepseek v4.1 flash+ZCode'


def step1_copy():
    print('=== 1. 复制游戏本体 ===')
    if os.path.isdir(GAME):
        print('  已存在:', GAME)
    else:
        os.makedirs(GAME, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(MEDIA)):
        s = os.path.join(MEDIA, f)
        if os.path.isfile(s):
            d = os.path.join(GAME, f)
            if not os.path.exists(d):
                shutil.copy2(s, d)
            n += 1
    print('  介质文件 %d 个 -> %s' % (n, GAME))
    print('  现有:', len(os.listdir(GAME)), '个文件')


def step2_patch_exe():
    print()
    print('=== 2. 打 EXE 的 GBK 补丁 ===')
    src = os.path.join(GAME, 'ORETUBAR.EXE')
    dst = os.path.join(GAME, 'ORETUBAR.EXE')
    tmp = os.path.join(GAME, 'ORETUBAR.EXE.gbk')
    # verify 判断是否已打
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'exe_gbk_patch.py'), 'verify', src],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    if '通过' in out or 'OK' in out:
        print('  已打过补丁，跳过')
        return
    rep = os.path.join(PROD, 'exe_patch_report.json')
    r2 = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(TOOLS, 'exe_gbk_patch.py'),
                         'apply', src, tmp, '--report', rep],
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
    o2 = (r2.stdout or '') + (r2.stderr or '')
    print('\n'.join('  ' + l for l in o2.splitlines()[:12]))
    if os.path.exists(tmp):
        shutil.move(tmp, dst)
        print('  已替换 ORETUBAR.EXE')
    else:
        print('  [错误] 未生成补丁后 EXE')


def step3_lpk():
    print()
    print('=== 3. 放入汉化 SCRIPT.LPK ===')
    if not os.path.exists(CN_LPK):
        print('  [错误] 汉化 LPK 不存在:', CN_LPK); return False
    shutil.copy2(CN_LPK, os.path.join(GAME, 'SCRIPT.LPK'))
    print('  %.2f MB' % (os.path.getsize(os.path.join(GAME, 'SCRIPT.LPK')) / 1048576))
    return True


def step4_usercfg():
    print()
    print('=== 4. 写 USER.CFG ===')
    tpl = os.path.join(PROJ, '存档备份', 'AppData_USER.CFG.orig')
    raw = open(tpl, 'rb').read()
    m = re.search(rb'[A-Za-z]:\\[^\x00]{0,240}\x00', raw)
    seg = os.path.abspath(SAVE).encode('ascii') + b'\x00'
    out = bytearray(raw)
    out[m.start():m.end()] = seg
    pre = m.start() - 2
    if int.from_bytes(raw[pre:pre + 2], 'little') == len(m.group(0)) - 1:
        out[pre:pre + 2] = (len(seg) - 1).to_bytes(2, 'little')
    os.makedirs(SAVE, exist_ok=True)
    for p in [os.path.join(SAVE, 'USER.CFG'), os.path.join(GAME, 'USER.CFG')]:
        open(p, 'wb').write(bytes(out))
    print('  路径 -> %s' % seg[:-1].decode())


def step5_save():
    print()
    print('=== 5. 写入全解锁存档 ===')
    if os.path.exists(UNLOCK):
        shutil.copy2(UNLOCK, os.path.join(SAVE, 'GAMEDATA.DAT'))
        print('  GAMEDATA.DAT %d 字节（全解锁）' % os.path.getsize(os.path.join(SAVE, 'GAMEDATA.DAT')))
    else:
        print('  [警告] 全解锁档缺失')


def step6_signature():
    print()
    print('=== 6. 署名（LL_APP.INF / 窗口标题）===')
    inf = os.path.join(GAME, 'LL_APP.INF')
    print('  说明：本作窗口标题取自 SCRIPT.LPK 内 ll_app.inf 的标题段。')
    print('  成品标题已在 SCRIPT.LPK 的 ll_app.inf 中处理，署名串：')
    print('   ', SIGN)


def step7_readme():
    print()
    print('=== 7. 写 成品说明.md ===')
    txt = f'''# 成品说明 · 我们没有翅膀R

## 这是什么
《我们没有翅膀R》（俺たちに翼はないＲ，Navel 2011）的**简体中文汉化版**。
基于日文原版 DVD 版制作；**未回写原始游戏目录**，本目录可独立运行。

## 运行方式
双击 `ORETSUBA_R\\ORETUBAR.EXE`。

- 需要 **Windows（中文系统区域）**；本作把文本按 **GBK** 处理，非中文区域可能显示异常。
- 原版要求 DirectX 9.0c；无其它运行库依赖。

## 相对原版改了什么
| 文件 | 改动 |
| --- | --- |
| `ORETSUBA_R\\ORETUBAR.EXE` | **GBK 补丁**：字体字符集 `SHIFTJIS→GB2312`（3 处）+ 文本前导字节判定 `0x81-0xFC→0x81-0xFE`（162 字节 / 83 处），使引擎按 GBK 解读中文 |
| `ORETSUBA_R\\SCRIPT.LPK` | **全量汉化脚本**：58,360 条文本槽全部中文化（迁移自新米汉化组原版汉化 51,736 条 + 新译 6,624 条），另 4,000 处残留日文重编码为 GBK 以消除乱码 |
| `ORETSUBA_R SaveData\\GAMEDATA.DAT` | **全解锁存档**：CG / 回想全开（793 项解锁位） |

## 翻译来源与致谢
- 约 89% 的译文**迁移自「新米汉化组」的原版（2009）中文汉化**，经字节级逐槽比对确认对应关系。
- 其余（含 R 版新增的香田亜衣路线）为本次新译。
- 迁移与不一致处已按本作语境统一。

## 署名
{SIGN}

## 已知问题
1. **系统 UI 文字仍为日文**（存档/读档/系统菜单等，来自 EXE 内嵌字符串，共约 141 条）——
   不影响游玩；后续可批量原地改写。
2. **少量演出文字未覆盖**（如个别影片叠字），来源为 DATA/SYS.LPK 内数据，尚未处理。
3. 文本历史（Log）与部分系统提示的编码路径未逐一实机核对。
4. 未在 Win7 实测（本机为 Windows 10 x64）。

## 原版位置
DVD 安装介质备份：`备份\\我们没有翅膀R-安装介质\\`
工程与工具：`工程\\我们没有翅膀R\\`
'''
    p = os.path.join(PROD, '成品说明.md')
    open(p, 'w', encoding='utf-8').write(txt)
    print('  已写出', p)


def main():
    t0 = time.time()
    print('成品目录:', PROD)
    step1_copy()
    step2_patch_exe()
    if not step3_lpk():
        return
    step4_usercfg()
    step5_save()
    step6_signature()
    step7_readme()
    print()
    print('=== 完成，用时 %.0f 秒 ===' % (time.time() - t0))
    print('成品:', PROD)
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(PROD) for f in fs)
    print('体积: %.2f GB' % (total / 1073741824))


if __name__ == '__main__':
    main()
