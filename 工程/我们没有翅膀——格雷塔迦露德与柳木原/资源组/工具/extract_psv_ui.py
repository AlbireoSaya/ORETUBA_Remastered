"""W3 · 补提 PSV 美咲线 UI / 系统素材（SystemData.cpk 182 + ETC.cpk 124 = 306 张）。

来源（只读）：工程\\我们没有翅膀PSV\\解密\\PCSG00299\\media\\{SystemData.cpk, ETC.cpk}
输出：工程\\我们没有翅膀——格雷塔迦露德与柳木原\\资源组\\krkr素材库\\otv\\{sys,etc}\\

命名规范（总纲 §七 I1 + 本模块派单）：
    otv_<原条目 basename 去扩展名> + 正确扩展名，统一小写
    例：otv_sys_menu.png / otv_ec_bg01.png

产出：
    otv\\_清单.json      每条 = {archive,index,orig_name,out_relpath,src_bytes,out_bytes,width,height,colortype,content_note}
    otv\\_提取摘要.txt   两档条目数/成功数/失败数/输出体积 + 失败项 + 总耗时

content_note 由外部映射文件填充（人工判读），映射文件不存在或未命中则写「待判读」。
映射文件格式（JSON）：{ "otv_sys_menu.png": "菜单 sprite sheet（英文 QUICK SAVE/SAVE/LOAD…）", ... }

用法：
    PYTHONPATH=<工作区>\\工具\\pylibs python extract_psv_ui.py
    PYTHONPATH=<工作区>\\工具\\pylibs python extract_psv_ui.py --notes <notes.json>
"""
import argparse
import io
import json
import os
import sys
import time

sys.path.insert(0, r'E:\ZCode Workspace\Galgame\工具\pylibs')
from cricodecs import cpk as C  # noqa: E402
from PIL import Image  # noqa: E402

MEDIA = r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀PSV\解密\PCSG00299\media'
OUT_ROOT = (r'E:\ZCode Workspace\Galgame\工程\我们没有翅膀——格雷塔迦露德与柳木原'
            r'\资源组\krkr素材库\otv')

ARCHIVES = [('SystemData.cpk', 'sys'), ('ETC.cpk', 'etc')]
PLACEHOLDER = '待判读'


def load_notes(path):
    if not path:
        return {}
    if not os.path.isfile(path):
        print('!! 映射文件不存在，content_note 全部写占位: %s' % path)
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--notes', default=None, help='content_note 映射 JSON 路径')
    args = ap.parse_args()
    notes = load_notes(args.notes)

    t0 = time.time()
    os.makedirs(OUT_ROOT, exist_ok=True)
    manifest = []
    summary = []
    failures = []

    for archive, sub in ARCHIVES:
        outdir = os.path.join(OUT_ROOT, sub)
        os.makedirs(outdir, exist_ok=True)
        # cricodecs 的 C++ reader 不支持非 ASCII 路径：先 chdir 到 media
        os.chdir(MEDIA)
        c = C.load(archive)
        n_ok = n_fail = 0
        vol = 0
        for i, f in enumerate(c.files):
            base = os.path.splitext(f.filename)[0].lower()
            out_name = 'otv_%s.png' % base
            out_rel = os.path.join('otv', sub, out_name).replace('\\', '/')
            try:
                data = c.file_bytes(i)               # ⚠️ 必须传列表下标，不能传 f.id
                assert len(data) == f.file_size, \
                    'size mismatch: got %d expected %d' % (len(data), f.file_size)
                assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
                with Image.open(io.BytesIO(data)) as im:
                    width, height = im.size
                    colortype = im.mode
                out_abs = os.path.join(OUT_ROOT, sub, out_name)
                with open(out_abs, 'wb') as fh:
                    fh.write(data)
                out_bytes = os.path.getsize(out_abs)
                assert out_bytes == f.file_size, 'write size mismatch'
                vol += out_bytes
                n_ok += 1
                manifest.append({
                    'archive': archive,
                    'index': i,
                    'orig_name': f.filename,
                    'out_relpath': out_rel,
                    'src_bytes': f.file_size,
                    'out_bytes': out_bytes,
                    'width': width,
                    'height': height,
                    'colortype': colortype,
                    'content_note': notes.get(out_name, PLACEHOLDER),
                })
            except Exception as e:                    # noqa: BLE001
                n_fail += 1
                failures.append({'archive': archive, 'index': i,
                                 'orig_name': f.filename, 'error': repr(e)})
                print('!! FAIL %s[%d] %s : %r' % (archive, i, f.filename, e))
        summary.append({'archive': archive, 'subdir': 'otv/' + sub,
                        'entries': len(c.files), 'ok': n_ok, 'fail': n_fail,
                        'out_bytes': vol})
        print('%-16s entries=%d ok=%d fail=%d out=%d B' %
              (archive, len(c.files), n_ok, n_fail, vol))

    elapsed = time.time() - t0

    with open(os.path.join(OUT_ROOT, '_清单.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)

    lines = []
    lines.append('# otv UI/系统素材 提取摘要')
    lines.append('# 生成: %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
    lines.append('# 源: %s' % MEDIA)
    lines.append('# 映射文件: %s' % (args.notes or '(未指定)'))
    lines.append('')
    lines.append('%-16s %-10s %8s %6s %6s %14s' %
                 ('archive', 'outdir', 'entries', 'ok', 'fail', 'out_bytes'))
    tot_e = tot_ok = tot_f = tot_v = 0
    for s in summary:
        lines.append('%-16s %-10s %8d %6d %6d %14d' %
                     (s['archive'], s['subdir'], s['entries'], s['ok'], s['fail'],
                      s['out_bytes']))
        tot_e += s['entries']; tot_ok += s['ok']; tot_f += s['fail']; tot_v += s['out_bytes']
    lines.append('%-16s %-10s %8d %6d %6d %14d' %
                 ('TOTAL', 'otv/', tot_e, tot_ok, tot_f, tot_v))
    lines.append('')
    lines.append('失败项: %d' % len(failures))
    for x in failures:
        lines.append('  - %s[%d] %s : %s' % (x['archive'], x['index'],
                                             x['orig_name'], x['error']))
    lines.append('')
    lines.append('总耗时: %.2f s' % elapsed)
    with open(os.path.join(OUT_ROOT, '_提取摘要.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')

    print()
    print('TOTAL entries=%d ok=%d fail=%d out=%d B  %.2fs' %
          (tot_e, tot_ok, tot_f, tot_v, elapsed))
    print('清单: %s' % os.path.join(OUT_ROOT, '_清单.json'))


if __name__ == '__main__':
    main()