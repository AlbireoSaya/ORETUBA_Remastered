# -*- coding: utf-8 -*-
"""ORETUBAR.EXE GBK 补丁器（Lucifen/Easy Game System DX，ISSUE-ORETUBAR-R）。

把引擎的「日文 SJIS 假设」改为「中文 GBK」：
  1) 字体字符集：CreateFontA 的 iCharSet 0x80(SHIFTJIS) → 0x86(GB2312)
     + Font 对象构造器里 LOGFONTA.lfCharSet 的同一处理
  2) 文本遍历前导字节表：SJIS 判定 (0x81-0x9F | 0xE0-0xFC) → GBK 判定 (0x81-0xFE)
     即把 4 连比较里的 0x9F 与 0xFC 两个立即数改成 0xFE

依据（见 报告.md / 机制说明.md）：
  - 参照汉化 DLL（新米汉化组 ORE_TUBA_CHS.dll）的 patch81s 即同类改造；
    本器用 capstone 重新定位 R 版地址（两版 EXE 代码同源、地址不同）。
  - charset 改造的 GDI 层实证：charset=GB2312 时 TextOutA(GBK 字节) 与
    TextOutW(Unicode) 渲染逐像素一致；charset=SHIFTJIS 时不一致。

用法：
  python -X utf8 exe_gbk_patch.py apply  <in.exe> <out.exe> [--report r.json]
  python -X utf8 exe_gbk_patch.py check  <exe>          # 只看扫描结果，不写文件
  python -X utf8 exe_gbk_patch.py verify <exe>          # 校验已打补丁的 exe
"""
import sys, os, json, struct

BASE = 0x400000  # ImageBase（PE32，实测本作 .text 文件偏移 = VA - 0x400000）

# ---------------- 字符集补丁点（R 版 ORETUBAR.EXE 实测签名） ----------------
# (VA, 期望原字节序列, 立即数字节在序列中的下标, 说明)
CHARSET_SITES = [
    (0x00408F1E, b'\x68\x80\x00\x00\x00', 1, 'CreateFontA #1 (ＭＳ Ｐ明朝) iCharSet=SHIFTJIS_CHARSET'),
    (0x00408FD4, b'\x68\x80\x00\x00\x00', 1, 'CreateFontA #2 (ＭＳ ゴシック) iCharSet=SHIFTJIS_CHARSET'),
    (0x004619E9, b'\xc6\x42\x23\x80', 3, 'Font 构造器: mov byte [edx+0x23], 0x80 → LOGFONTA.lfCharSet'),
]

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    _md = Cs(CS_ARCH_X86, CS_MODE_32)
except ImportError:
    _md = None
    print('[警告] capstone 不可用，将退化为纯字节模式扫描（不推荐）', file=sys.stderr)


def _dis(code, off, start_va, nbytes=64):
    """从 code 的 off 处偏移反汇编若干条指令，地址按 start_va 起算。"""
    return list(_md.disasm(code[off:off + nbytes], start_va))[:16]


def scan_leadbyte_checks(data):
    """扫描全部 SJIS 前导字节范围检查（capstone 校验指令流）。

    判据：从某条 `cmp r8, 0x81` 起的指令流中，按顺序出现
    `cmp r8, 0x9F` → `cmp r8, 0xE0` → `cmp r8, 0xFC`（同一寄存器）。
    （cmp 与其后的条件跳转之间可能夹有 1-2 条无关指令，故不要求相邻。）

    返回 [(cmp_start_va, imm9f_va, imm_e0_va, imm_fc_va), ...]
    """
    out = []
    n = len(data)
    i = 0
    REG = {0xF8, 0xF9, 0xFA, 0xFB, 0xFD, 0xFE, 0xFF}
    while i < n - 4:
        b0 = data[i]
        if b0 == 0x3C and data[i + 1] == 0x81:
            pass
        elif b0 == 0x80 and data[i + 1] in REG and data[i + 2] == 0x81:
            pass
        else:
            i += 1
            continue
        if _md is None:
            i += 1
            continue
        va = BASE + i
        ins = _dis(data, i, va)
        if len(ins) < 4 or not (ins[0].mnemonic == 'cmp' and ins[0].op_str.endswith(', 0x81')):
            i += 1
            continue
        reg = ins[0].op_str.split(',')[0].strip()
        seq = []
        for want in ('0x9f', '0xe0', '0xfc'):
            found = None
            for k in range(1, len(ins)):
                if ins[k].mnemonic == 'cmp' and ins[k].op_str == '%s, %s' % (reg, want):
                    found = ins[k]
                    break
            if found is None:
                break
            seq.append(found.address)
        if len(seq) != 3:
            i += 1
            continue
        cmp_va, v9f, ve0, vfc = ins[0].address, seq[0], seq[1], seq[2]
        # 二次校验：立即数字节的确切值
        ok = True
        for (va_cmp, want_imm) in ((v9f, 0x9F), (vfc, 0xFC)):
            if data[imm_offset(va_cmp, data)] != want_imm:
                ok = False
        if not ok:
            i += 1
            continue
        out.append((cmp_va, v9f, ve0, vfc))
        i += 4
    return out


def _dedupe_checks(checks):
    """去掉「伪检查」：指令流自某个地址错位解码也会凑出同样四连比较，
    其补丁目标与真实检查完全相同。判据：目标集被已保留检查完全包含且起点相近。"""
    keep = []
    for c in sorted(checks):
        cs = {c[1], c[3]}
        drop = False
        for k in keep:
            ks = {k[1], k[3]}
            if cs <= ks and c[0] < k[0] + 16:
                drop = True
                break
        if not drop:
            keep.append(c)
    return keep


def imm_offset(va, data):
    """给 cmp r8,imm 的指令地址，返回其立即数在 data 中的偏移。
    编码：3C imm8（2 字节，imm 在 +1）；80 /? imm8（3 字节，imm 在 +2）。"""
    off = va - BASE
    return off + (1 if data[off] == 0x3C else 2)


def build_plan(data):
    """产出补丁计划：[(file_offset, old_byte, new_byte, 说明)]"""
    plan = []
    # 1) 字符集
    for va, sig, imm_idx, desc in CHARSET_SITES:
        off = va - BASE
        got = data[off:off + len(sig)]
        if got != sig:
            raise SystemExit('[错误] 字符集补丁点 %08x 签名不符：期望 %s 实测 %s' %
                             (va, sig.hex(), got.hex()))
        imm = off + imm_idx
        assert data[imm] == 0x80, '[错误] %08x 立即数实测 %02x' % (va, data[imm])
        plan.append((imm, 0x80, 0x86, desc))
    # 2) 前导字节判定
    checks = scan_leadbyte_checks(data)
    seen = {}
    for cmp_va, v9f, ve0, vfc in checks:
        for va_cmp, want in ((v9f, 0x9F), (vfc, 0xFC)):
            off = imm_offset(va_cmp, data)
            if data[off] != want:
                raise SystemExit('[错误] %08x 处立即数期望 %02x 实测 %02x' % (BASE + off, want, data[off]))
            if off in seen:
                continue          # 错位解码产生的重复检查：目标相同，只记一次
            seen[off] = True
            plan.append((off, want, 0xFE, 'SJIS 前导上界 %02x→0xFE @cmp %08x' % (want, cmp_va)))
    return plan, checks


def apply_patch(in_path, out_path, report_path=None):
    data = bytearray(open(in_path, 'rb').read())
    orig = bytes(data)
    plan, checks = build_plan(orig)
    offs = [o for o, _, _, _ in plan]
    assert len(offs) == len(set(offs)), '补丁计划存在重复位置'
    for off, old, new, desc in plan:
        data[off] = new
    open(out_path, 'wb').write(bytes(data))
    # 自检
    diff = [i for i in range(len(orig)) if orig[i] != data[i]]
    assert len(diff) == len(plan), '改动字节数 %d != 计划 %d' % (len(diff), len(plan))
    print('已写出: %s' % out_path)
    print('  字符集补丁 %d 处；前导字节检查 %d 处（%d 字节）' %
          (len(CHARSET_SITES), len(checks), len(plan) - len(CHARSET_SITES)))
    print('  总改动字节 %d，全部命中计划位置' % len(diff))
    if report_path:
        rep = {
            'input': in_path, 'output': out_path,
            'charset_sites': [{'va': '%08x' % va, 'desc': d} for va, _, _, d in CHARSET_SITES],
            'leadbyte_checks': [{'cmp_va': '%08x' % c[0], 'imm_9f_va': '%08x' % c[1],
                                 'imm_e0_va': '%08x' % c[2], 'imm_fc_va': '%08x' % c[3]} for c in checks],
            'changes': [{'file_offset': o, 'va': '%08x' % (BASE + o), 'old': '%02x' % a,
                         'new': '%02x' % b_, 'desc': d} for o, a, b_, d in plan],
        }
        json.dump(rep, open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('  报告: %s' % report_path)
    return plan, checks


def verify_patched(path):
    data = open(path, 'rb').read()
    ok = True
    # 字符集
    for va, sig, imm_idx, desc in CHARSET_SITES:
        off = va - BASE
        imm = off + imm_idx
        v = data[imm]
        st = 'OK' if v == 0x86 else 'FAIL'
        if v != 0x86:
            ok = False
        print('  字符集 @%08x : 0x%02x (%s) %s' % (BASE + imm, v, st, desc))
    # 前导检查：以打补丁后的数据重新扫描，应得不到任何 0x9F/0xFC 检查点
    checks = scan_leadbyte_checks(data)
    print('  打补丁后仍存在的 SJIS 四连检查: %d 处（应为 0）' % len(checks))
    if checks:
        ok = False
        for c in checks[:10]:
            print('     残留 @%08x' % c[0])
    # 统计 0xFE 立即数（cmp r8, 0xFE 的四连形式应能被扫出）
    nfe = sum(1 for i in range(len(data) - 3)
              if (data[i] == 0x3C and data[i + 1] == 0xFE) or
                 (data[i] == 0x80 and data[i + 1] in (0xF8, 0xF9, 0xFA, 0xFB, 0xFD, 0xFE, 0xFF) and data[i + 2] == 0xFE))
    print('  0xFE 立即数出现次数: %d（含原有非补丁用途，仅供参考）' % nfe)
    print('  校验结果: %s' % ('通过' if ok else '失败'))
    return ok


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'apply':
        rep = None
        args = [a for a in sys.argv[2:] if not a.startswith('--')]
        if '--report' in sys.argv:
            rep = sys.argv[sys.argv.index('--report') + 1]
        apply_patch(args[0], args[1], rep)
    elif cmd == 'check':
        d = open(sys.argv[2], 'rb').read()
        print('字符集补丁点:')
        for va, sig, imm_idx, desc in CHARSET_SITES:
            off = va - BASE
            print('  %08x  %s  %s' % (va, ' '.join('%02x' % x for x in d[off:off + len(sig)]), desc))
        checks = scan_leadbyte_checks(d)
        print('SJIS 前导字节四连检查: %d 处' % len(checks))
        for c in checks:
            print('  cmp@%08x  9F@%08x  E0@%08x  FC@%08x' % c)
    elif cmd == 'verify':
        ok = verify_patched(sys.argv[2])
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)
