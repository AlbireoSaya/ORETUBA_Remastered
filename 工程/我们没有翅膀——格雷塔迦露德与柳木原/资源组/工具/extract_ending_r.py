#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""从 R 版（otr）安装介质 PIC.LPK 补提「片尾 / 结局」素材并解码为 PNG，产出清单。

范围（R 版 PIC.LPK，717 条目中按名筛出）：
  sr*  110 件 = 97 页片尾 STAFF ROLL 分页（sr0 16 / sr1 15 / sr2 15 / sr3 16 / sr4 19 / sr5 16）
              + 6 件角色胸像卡（sr2_c01-c03、sr2_c11-c13）
              + 7 件歌词字幕条（sr2_t01-t07）
  ec*   31 件 = 结局卡（ec01-19、ec21-29、ec31-33；R 版与 ot 同缺 ec20/ec30）
  合计 141 件。

产物：
  <输出目录>/otr_<原名小写>.png        （默认 资源组\片尾\_src\r_staff\，已 gitignore）
  <清单路径>                            （默认 资源组\片尾\_raw_r_sr.tsv，LF/制表符/UTF-8 无 BOM）

清单列（15 列，按序）：
  原名 / 归档条目名 / 输出文件名 / 用途 / 宽 / 高 / 色彩模式 / PNG字节 / PNG的md5 /
  ELG原字节 / 含图片化文字 / W19口径 / 文字语言 / 备注 / 与ot篇同名件
其中「含图片化文字」（像素事实）与「W19口径」（既有 W19 登记口径）**两套口径并列、互不覆盖**，
差异在「备注」列逐件说明——见下方 EC_CAVEAT 与 w19_flag() 的说明。

纪律：
  * 只读 R 版安装介质（备份目录）、只读 ot 参照 PNG，**不写入工作树之外的任何路径**；
    所有写路径均经 guard_write() 硬校验落在工作树内（本工程有 os.path.join(main,"..") 逃逸前例）。
  * 幂等：同名 PNG 内容一致时不重写（不产生 mtime/内容漂移）；重跑产物逐字节一致。
  * 缺条目 = 硬错误：请求了不存在的条目名必须报错，绝不静默产出 0 件。

用法：
  python -X utf8 extract_ending_r.py                     # 全量提取 + 出清单
  python -X utf8 extract_ending_r.py --only sr2_c01.elg  # 只提指定条目（不存在则报错）
  python -X utf8 extract_ending_r.py --selftest          # 负向自证（不进主流程）
  python -X utf8 extract_ending_r.py --list              # 只列条目，不落盘
"""

import argparse
import hashlib
import io
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
GAME = '我们没有翅膀——格雷塔迦露德与柳木原'
GAME_KEY = 'Ore-tachi ni Tsubasa wa Nai R'      # LPK-Keys.json 中的作品键名

# 脚本位于 <WT>\工程\<GAME>\资源组\工具\extract_ending_r.py
#   parents[0]=工具 [1]=资源组 [2]=<GAME> [3]=工程 [4]=<WT>
WT_ROOT = Path(__file__).resolve().parents[4]

_MAIN = Path(r'E:\ZCode Workspace\Galgame')     # 主工作区（只读源）
DEFAULT_LPK = _MAIN / '备份' / '我们没有翅膀R-安装介质' / 'SET_UP' / 'PIC.LPK'
DEFAULT_OUT = WT_ROOT / '工程' / GAME / '资源组' / '片尾' / '_src' / 'r_staff'
DEFAULT_MANIFEST = WT_ROOT / '工程' / GAME / '资源组' / '片尾' / '_raw_r_sr.tsv'
# ot（2009 本篇）参照：① 美术统一交付件（优先，含 md5 溯源清单）② 素材库原始提取
DEFAULT_OT_UNIFIED = _MAIN / '工程' / GAME / '资源组' / '美术统一' / 'CG背景'
DEFAULT_OT_MANIFEST = _MAIN / '工程' / GAME / '资源组' / '美术统一' / '清单_CG背景.tsv'
DEFAULT_OT_LIB = _MAIN / '工程' / GAME / '资源组' / 'krkr素材库' / 'ot' / 'pic'

LUCIFEN_TOOLS = _MAIN / '工具' / 'lucifen' / 'Lucifen-Tools'

TSV_HEADER = ['原名', '归档条目名', '输出文件名', '用途', '宽', '高', '色彩模式',
              'PNG字节', 'PNG的md5', 'ELG原字节', '含图片化文字', 'W19口径', '文字语言', '备注',
              '与ot篇同名件']

# ---------------------------------------------------------------------------
# 判读表（既有判读 + 本次目视判读；依据见下方 EVIDENCE）
# ---------------------------------------------------------------------------
# 既有判读来源：
#   A = 工程\...\资源组\美术\背景CG编目.md §3.5/§3.5 更正块（sr 族全量）
#   B = 子代理工作区\ISSUE-20260919-05\W12_判读\_判读终裁.tsv 行 79–140
#   C = 资源组\美术统一\清单_CG背景.tsv 的「图片化日文」列（W19 补标）
# 本次目视（2026-09-29，接触印相表见 _src\_contact\，均为全分辨率拼接）：
#   sr5_01–16 逐页目视 = 片尾 STAFF 页（日文【キャスト】【スタッフ】名单 + 角色/背景）
#   sr2_c01–c13 目视 = 胸像卡（3 名角色 × 2 尺寸），画面内无任何文字
#   sr2_t01–t07 目视 = 日文歌词条（浅蓝描边，sr2_t03 含拉丁 "Ah … sympathy"）
#   ec01–ec33 逐件目视 = 结局卡；除 ec29 外均含「俺たちに翼はないＲ」日文 logo 图字
EVIDENCE = '依据：背景CG编目.md §3.5；_判读终裁.tsv 行 79–140；清单_CG背景.tsv「图片化日文」列；本次目视'

EC_JP_LOGO = '含日文「俺たちに翼はないＲ」图字（整幅 logo 页）'
EC_EN_NOTE = '另含角色英文名小字'
# ---- 「图片化日文」两套口径并列（主代理 2026-09-29 裁决 1）----
#   列 `含图片化文字` = **像素事实**（本模块目视 + 既有判读）：像素中确有图字即「是」。
#   列 `W19口径`     = **既有 W19 登记口径**：只有属「汉化须重绘或改引擎绘字」者才「计入」；
#                      作品 skill §二·补明列的排除项含「**纯品牌标识**」
#                      （`brandlogo_5pb`/`criware1280x720sw`/`sr_logo`）与背景内世界观招牌。
#   两列互不覆盖、并存；差异一句写在「备注」。
#   实测锚点：`美术统一\清单_CG背景.tsv` 的「图片化日文」列对 sr0–sr4 页 81 / sr2_t 7 标「是」，
#             对 sr2_c 6 留空、对 ec01–ec28 全部留空，且无 sr5（R 独有件，W19 补标未覆盖）。
EC_CAVEAT = ('口径差异：像素内确有标题 logo 图字（含图片化文字=是），'
             '但按 W19 口径属「纯品牌标识」不计入（W19口径=不计入）')
SR5_NOTE = 'sr5 为 R 版独有片尾 STAFF 族，具体引用其的剧情未查'
SRC_NOTE = '画面内无文字，两口径无冲突'
EC33_NOTE = 'R 版独有结局卡；是否回并入美术统一待后续裁决'
EC33_STEMS = {'ec31', 'ec32', 'ec33'}

# 逐件特例（键 = 去扩展名小写原名；值 = (用途, 含图片化文字, 文字语言, 备注)）
SPECIAL = {
    'ec27': ('结局卡', '是', '日文', '整幅标题 logo 页（含拉丁副题 under the innocent sky）'),
    'ec28': ('结局卡', '是', '日文', '整幅标题 logo 页（含拉丁副题 under the innocent sky）'),
    'ec29': ('结局卡', '是', '英文', 'Navel 品牌标识页（拉丁文 Navel／Limited Edition，无日文）'),
    'ec06': ('结局卡', '是', '日文', EC_JP_LOGO + '；' + EC_EN_NOTE),
    'ec07': ('结局卡', '是', '日文', EC_JP_LOGO + '；' + EC_EN_NOTE),
    'ec08': ('结局卡', '是', '日文', EC_JP_LOGO + '；' + EC_EN_NOTE),
    'ec09': ('结局卡', '是', '日文', EC_JP_LOGO + '；' + EC_EN_NOTE),
    'ec10': ('结局卡', '是', '日文', EC_JP_LOGO + '；' + EC_EN_NOTE),
    'ec32': ('结局卡', '是', '日文', EC_JP_LOGO + '；' + EC_EN_NOTE),
}


def w19_flag(stem: str) -> str:
    """W19「图片化日文」登记口径（2026-09-29 主代理裁决 1）。

    计入 = 属「汉化须重绘或改引擎绘字」的文字：
        sr0–sr4 页 81 件（与既有 W19 一致）、sr2_t 7 件（一致）、sr5 16 件（职员表，属片尾 STAFF 子族）。
    不计入 = 按 W19 口径排除的「纯品牌标识」/无字件：
        ec 31 件（结局卡上的「俺たちに翼はないＲ」属标题 logo）、sr2_c 6 件（画面内无文字）。
    """
    s = stem.lower()
    if s.startswith('ec') or s.startswith('sr2_c'):
        return '不计入'
    return '计入'


def classify(stem: str):
    """→ (用途, 含图片化文字, 文字语言, 备注)。无法判定一律 '待判读'，不猜。"""
    s = stem.lower()
    if s in SPECIAL:
        u, pic, lang, note = SPECIAL[s]
        return u, pic, lang, note
    if s.startswith('sr2_c'):
        return '胸像', '否', '无', '片尾角色胸像卡（背景已烘进画面，RGB 无 alpha）；3 名角色 × 2 尺寸'
    if s.startswith('sr2_t'):
        return '歌词', '是', '日文', '片尾歌词字幕条（透明底 RGBA；sr2_t03 另含拉丁 "Ah/sympathy"）'
    if re.fullmatch(r'sr5_\d+', s):
        return '片尾STAFF', '是', '日文', 'R 版独有追加片尾 STAFF 页（ot 篇无 sr5）'
    if re.fullmatch(r'sr[0-4]_\d+', s):
        return '片尾STAFF', '是', '日文', '片尾 STAFF ROLL 分页（800x600 蓝框相框式，日文名单）'
    if re.fullmatch(r'ec\d+', s):
        return '结局卡', '是', '日文', EC_JP_LOGO
    return '待判读', '待判读', '待判读', ''


# ---------------------------------------------------------------------------
# 写路径守卫（硬校验）
# ---------------------------------------------------------------------------
class PathGuardError(RuntimeError):
    pass


def guard_write(p) -> Path:
    """把待写路径解析为绝对路径并断言它落在工作树 <WT_ROOT> 之内，否则抛错。"""
    rp = Path(os.path.realpath(str(p)))
    try:
        rp.relative_to(WT_ROOT)
    except ValueError:
        raise PathGuardError('拒绝写入工作树之外的路径：%s（工作树=%s）' % (rp, WT_ROOT))
    return rp


def guard_read(p) -> Path:
    """读路径只要求存在（不设工作区边界——读自由）。"""
    rp = Path(os.path.realpath(str(p)))
    if not rp.exists():
        raise FileNotFoundError('读取源不存在：%s' % rp)
    return rp


# ---------------------------------------------------------------------------
# 归档与解码
# ---------------------------------------------------------------------------
def load_lpk(lpk_path: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent))   # 本目录的 lpk_media.py（多作品版）
    sys.path.insert(0, str(LUCIFEN_TOOLS))                     # 社区 lpk_extractor / elg2png
    import lpk_media as M                                      # noqa: E402
    import elg2png                                             # noqa: E402
    lp = M.load(str(lpk_path), game=GAME_KEY)
    return M, elg2png, lp


def md5_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def decode_png(M, elg2png, lp, entry: str) -> tuple:
    """取条目 → 解 ELG → 返回 (PNG 字节, PIL 图, ELG 字节数)。条目不存在则抛错。"""
    elg = M.read(lp, entry)                       # 不存在 → KeyError
    im = elg2png.Reader(elg).decode()
    buf = io.BytesIO()
    im.save(buf, format='PNG', optimize=False, compress_level=6)
    return buf.getvalue(), im, len(elg)


def write_idempotent(path: Path, data: bytes) -> bool:
    """内容一致则不写。返回 True 表示本次真正写了盘。"""
    if path.exists() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


# ---------------------------------------------------------------------------
# 与 ot 篇同名件比对
# ---------------------------------------------------------------------------
def load_ot_selection(manifest: Path) -> dict:
    """读美术统一清单，返回 {统一名: 选中源}；文件缺失返回 {}。"""
    if not manifest.exists():
        return {}
    out = {}
    for line in manifest.read_text(encoding='utf-8').splitlines()[1:]:
        f = line.split('\t')
        if len(f) > 8:
            out[f[0]] = f[8]
    return out


def ot_reference(stem: str, ot_unified: Path, ot_sel: dict, ot_lib: Path):
    """返回 (参照 PNG 路径 or None, 参照所记来源说明)。"""
    bare = stem + '.png'
    sel = ot_sel.get(bare)
    if sel == 'ot' and (ot_unified / bare).exists():
        return ot_unified / bare, '美术统一/选中源=ot'
    # 美术统一未选 ot（跨源同名不同图）→ 回退到 ot 素材库原始提取
    alt = ot_lib / ('ot_' + bare)
    if alt.exists():
        why = ('美术统一/选中源=%s（跨源同名不同图）' % sel) if sel else '美术统一无此件'
        return alt, '素材库ot原始提取（%s）' % why
    if sel == 'ot' and not (ot_unified / bare).exists():
        return None, '美术统一清单记为 ot 但文件缺失'
    return None, ''


def diff_stats(ra, rb):
    """RGBA 逐像素差异：返回 (差异像素数, 总像素数, 最大通道差, bbox)。

    手写循环（不用 ImageChops.getbbox）：实测 Pillow 12 对 RGBA 的
    ImageChops.difference(...).getbbox() 恒返回 None（差异明明存在），会给出误导性结果。
    """
    w, h = ra.size
    a = ra.tobytes()
    b = rb.tobytes()
    n = 0
    mx = 0
    x0, y0, x1, y1 = w, h, -1, -1
    for idx, (pa, pb) in enumerate(zip(memoryview(a).cast('I'), memoryview(b).cast('I'))):
        if pa == pb:
            continue
        n += 1
        for sh in (0, 8, 16, 24):
            d = ((pa >> sh) & 0xFF) - ((pb >> sh) & 0xFF)
            if d < 0:
                d = -d
            if d > mx:
                mx = d
        x = idx % w
        y = idx // w
        if x < x0:
            x0 = x
        if x > x1:
            x1 = x
        if y < y0:
            y0 = y
        if y > y1:
            y1 = y
    bbox = None if n == 0 else (x0, y0, x1 + 1, y1 + 1)
    return n, w * h, mx, bbox


def compare_pixels(a, b):
    """逐像素比对（统一在 RGBA 空间，模式不同也能判）。

    返回 (判定, 附加说明, 差异统计)：
      判定 ∈ {'同', '同模异', '异', '尺寸异'}
      差异统计 = (差异像素数, 总像素数, 最大通道差, bbox) 或 None
    """
    if a.size != b.size:
        return '尺寸异', '%dx%d vs %dx%d' % (a.width, a.height, b.width, b.height), None
    ra, rb = a.convert('RGBA'), b.convert('RGBA')
    n, tot, mx, bbox = diff_stats(ra, rb)
    stats = (n, tot, mx, bbox)
    if n == 0:
        return ('同', '', stats) if a.mode == b.mode else ('同模异', '%s vs %s' % (a.mode, b.mode), stats)
    return '异', '', stats


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def collect_entries(M, lp, only=None):
    names = M.names(lp)
    if only:
        have = {n.lower(): n for n in names}
        miss = [o for o in only if o.lower() not in have]
        if miss:
            raise SystemExit('错误：归档中不存在以下条目名（拒绝静默产出）: %s\n'
                             '（若要自查，见 --selftest）' % ', '.join(miss))
        return [have[o.lower()] for o in only]
    sel = [n for n in names if re.match(r'(?i)^sr', n) or re.match(r'(?i)^ec', n)]
    if not sel:
        raise SystemExit('错误：PIC.LPK 中未筛到任何 sr*/ec* 条目——归档或密钥可疑，拒绝产出空清单')
    return sorted(sel)


def run(args):
    from PIL import Image  # noqa: F401  （PIL 由 elg2png 依赖，此处仅显式声明）

    lpk = guard_read(args.lpk)
    out_dir = guard_write(args.out)
    manifest = guard_write(args.manifest)
    if args.ot_unified:
        args.ot_unified = Path(args.ot_unified)
    if args.ot_lib:
        args.ot_lib = Path(args.ot_lib)

    M, elg2png, lp = load_lpk(lpk)
    entries = collect_entries(M, lp, args.only)
    print('PIC.LPK: %d 条目 flags=0x%02x ｜ 本次选中 %d 件' % (lp['cnt'], lp['flags'], len(entries)))

    if args.list:
        for n in entries:
            print('   %s' % n)
        print('   合计 %d 件' % len(entries))
        return 0

    ot_sel = load_ot_selection(Path(args.ot_manifest)) if args.ot_manifest else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    fam = {}
    wrote = 0
    for e in entries:
        stem = e.rsplit('.', 1)[0].lower()
        out_name = 'otr_%s.png' % stem
        out_path = guard_write(out_dir / out_name)
        png, im, elg_len = decode_png(M, elg2png, lp, e)
        if write_idempotent(out_path, png):
            wrote += 1
        purpose, pic_text, lang, note = classify(stem)
        w19 = w19_flag(stem)
        # 裁决 1/2/3 的备注落地（备注恒含「两列口径差异」一句）
        if stem.startswith('ec'):
            note = (note + '；' if note else '') + EC_CAVEAT
            if stem in EC33_STEMS:
                note += '；' + EC33_NOTE
        elif re.fullmatch(r'sr5_\d+', stem):
            note = (note + '；' if note else '') + SR5_NOTE
        elif stem.startswith('sr2_c'):
            note = (note + '；' if note else '') + SRC_NOTE

        # ---- 与 ot 篇同名件逐像素比对 ----
        ref, ref_why = ot_reference(stem, Path(args.ot_unified), ot_sel, Path(args.ot_lib))
        if ref is None:
            cmp_cell = 'ot 无此件' + ('（%s）' % ref_why if ref_why else '')
        else:
            try:
                with Image.open(ref) as other:
                    kind, extra, stats = compare_pixels(im, other)
                    other_bytes = ref.read_bytes()
                if kind == '同':
                    cmp_cell = '逐像素相同'
                    note = (note + '；' if note else '') + 'ot 同名件逐像素相同（%s）' % ref_why
                elif kind == '同模异':
                    cmp_cell = '像素相同（色彩模式不同：%s）' % extra
                    note = (note + '；' if note else '') + 'ot 同名件像素相同、模式不同（%s）' % ref_why
                elif kind == '尺寸异':
                    cmp_cell = '像素不同（尺寸不同 %s；md5 R=%s / ot=%s）' % (
                        extra, md5_bytes(png), md5_bytes(other_bytes))
                else:
                    cmp_cell = '像素不同（md5 R=%s / ot=%s）' % (md5_bytes(png), md5_bytes(other_bytes))
                    n, tot, mx, bbox = stats
                    note = (note + '；' if note else '') + (
                        'ot 同名件差异 %.2f%% 像素（%d/%d，最大通道差 %d，bbox %s）'
                        % (100.0 * n / tot, n, tot, mx, bbox))
            except Exception as ex:                        # 参照坏 → 如实登记，不假装通过
                cmp_cell = '比对失败（参照 %s 读取异常：%s）' % (ref.name, ex)

        key = re.match(r'(?i)(sr\d+|ec)', stem).group(1).lower()
        fam[key] = fam.get(key, 0) + 1
        rows.append([stem, e, out_name, purpose, str(im.width), str(im.height), im.mode,
                     str(len(png)), md5_bytes(png), str(elg_len), pic_text, w19, lang, note, cmp_cell])

    # ---- 本批内部「同名不同件 / 同图多件」核账（md5 分组，防按名合并） ----
    by_md5 = {}
    for r in rows:
        by_md5.setdefault(r[8], []).append(r[0])
    dup_groups = 0
    for digest, stems in by_md5.items():
        if len(stems) > 1:
            dup_groups += 1
            for r in rows:
                if r[8] == digest:
                    r[13] = (r[13] + '；' if r[13] else '') + \
                        '与本批同图共 %d 件（%s）' % (len(stems), '、'.join(stems))
    print('本批同图多件组 %d（已登记进备注列）' % dup_groups)

    # ---- 清单（LF / 制表符 / UTF-8 无 BOM）----
    body = '\n'.join(['\t'.join(TSV_HEADER)] +
                     ['\t'.join(r) for r in rows]) + '\n'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    changed = write_idempotent(manifest, body.encode('utf-8'))
    print('本次实写 PNG %d 件（其余 %d 件内容一致未重写）' % (wrote, len(rows) - wrote))
    print('清单：%s（%s）' % (manifest, '已更新' if changed else '无变化'))
    print('逐族：%s' % ' '.join('%s=%d' % (k, fam[k]) for k in sorted(fam)))
    print('合计 %d 件' % len(rows))
    return 0


# ---------------------------------------------------------------------------
# 负向自证
# ---------------------------------------------------------------------------
def selftest():
    lpk = Path(DEFAULT_LPK)
    M, elg2png, lp = load_lpk(lpk)
    fails = []

    # 1) 不存在的条目名必须报错（不得静默 → 空）
    try:
        M.read(lp, 'no_such_entry_zzzz.elg')
        fails.append('① 不存在的条目名未报错')
    except KeyError:
        print('① PASS 不存在的条目名 → KeyError')
    except Exception as ex:                                    # 任何异常都算拦住了
        print('① PASS 不存在的条目名 → %s: %s' % (type(ex).__name__, ex))

    try:
        collect_entries(M, lp, only=['sr0_01.elg', 'no_such_entry_zzzz.elg'])
        fails.append('② --only 含不存在条目时未报错')
    except SystemExit as ex:
        print('② PASS --only 含不存在条目 → SystemExit: %s' % ex)

    # 2) 输出路径逃逸工作树必须被拒
    esc = WT_ROOT / '..' / 'r_staff_escape_test'
    try:
        guard_write(esc)
        fails.append('③ 逃逸路径未被拒绝')
    except PathGuardError as ex:
        print('③ PASS 逃逸路径被拒：%s' % ex)

    # 3) 正例：合法路径必须通过（防止守卫写成"一律拒绝"的假绿）
    okp = guard_write(DEFAULT_OUT / 'probe.png')
    print('④ PASS 合法路径通过：%s' % okp)

    # 4) 真正不落盘：③ 之后工作树外不应出现任何文件
    outside = Path(os.path.realpath(str(esc)))
    if outside.exists():
        fails.append('⑤ 逃逸路径竟然被创建：%s' % outside)
    else:
        print('⑤ PASS 工作树外未产生文件：%s' % outside)

    if fails:
        print('\nSELFTEST FAIL: ' + '; '.join(fails))
        return 1
    print('\nSELFTEST PASS（负向全部被拦，正例未误拦）')
    return 0


def main():
    ap = argparse.ArgumentParser(description='R 版（otr）片尾/结局素材补提 + 清单')
    ap.add_argument('--lpk', default=str(DEFAULT_LPK))
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    ap.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    ap.add_argument('--ot-unified', default=str(DEFAULT_OT_UNIFIED))
    ap.add_argument('--ot-manifest', default=str(DEFAULT_OT_MANIFEST))
    ap.add_argument('--ot-lib', default=str(DEFAULT_OT_LIB))
    ap.add_argument('--only', action='append', default=None, help='只提指定归档条目名（可重复；不存在则报错）')
    ap.add_argument('--list', action='store_true', help='只列条目不落盘')
    ap.add_argument('--selftest', action='store_true', help='负向自证')
    args = ap.parse_args()
    if not (WT_ROOT / '工程' / GAME).is_dir():
        raise SystemExit('工作树结构不符：%s 下找不到 工程\\%s' % (WT_ROOT, GAME))
    if args.selftest:
        return selftest()
    return run(args)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
