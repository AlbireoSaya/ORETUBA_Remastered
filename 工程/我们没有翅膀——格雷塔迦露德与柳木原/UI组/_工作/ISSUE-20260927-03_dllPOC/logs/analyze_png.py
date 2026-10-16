#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  ISSUE-20260927-03 module J  -  layerExDraw.dll POC pixel verification
#  Pure stdlib (zlib + struct + os only). Reads the PNGs the engine exported
#  off-screen via stageLayer.copyToBitmapFromMainImage(), then prints a
#  coordinate-by-coordinate / census-by-census report.
#
#  usage (from this logs\ directory):
#      python analyze_png.py
#      python analyze_png.py > ..\证据\像素核读数.txt
# =============================================================================
import struct, zlib, os

SAVEDATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine', 'savedata')


def load_png(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n', 'not a png: ' + path
    pos, idat = 8, b''
    while pos < len(d):
        ln, typ = struct.unpack_from('>I4s', d, pos); pos += 8
        data = d[pos:pos + ln]; pos += ln + 4
        if typ == b'IHDR':
            w, h, bd, ct, comp, filt, inter = struct.unpack('>IIBBBBB', data)
            assert bd == 8 and inter == 0, ('unsupported depth/interlace', bd, inter)
        elif typ == b'IDAT':
            idat += data
        elif typ == b'IEND':
            break
    raw = zlib.decompress(idat)
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    stride = w * nch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, nch, out


def px(w, nch, buf, x, y):
    o = (y * w + x) * nch
    if nch == 4: return tuple(buf[o:o + 4])
    if nch == 3: return tuple(buf[o:o + 3]) + (255,)
    if nch == 1:
        v = buf[o]; return (v, v, v, 255)
    v, a = buf[o], buf[o + 1]; return (v, v, v, a)


def census(w, h, nch, buf, x0, y0, x1, y1, pred=None, step=1):
    n = 0; hit = 0; col = {}
    for y in range(max(0, y0), min(h, y1), step):
        for x in range(max(0, x0), min(w, x1), step):
            c = px(w, nch, buf, x, y)
            n += 1
            col[c] = col.get(c, 0) + 1
            if pred and pred(c): hit += 1
    return n, hit, col


def top(col, k=6):
    return ', '.join('%s x%d' % (c, v) for c, v in sorted(col.items(), key=lambda kv: -kv[1])[:k])


def main_png():
    path = os.path.join(SAVEDATA, 'poc_layerExDraw.png')
    w, h, nch, buf = load_png(path)
    print('== poc_layerExDraw.png  %dx%d nch=%d ==' % (w, h, nch))
    BG = (0x20, 0x20, 0x28, 255)
    print('  backdrop (builtin fillRect 0xff202028), pixel (620,20) = %s' % (px(w, nch, buf, 620, 20),))

    checks = [
        ('(1) horizontal line w=5   (160,50)', 160, 50, (255, 48, 48, 255)),
        ('(2) DIAGONAL line w=7   (165,145)', 165, 145, (255, 0, 255, 255)),
        ('(3) polyline vert seg   (500,120)', 500, 120, (255, 170, 0, 255)),
        ('(3) polyline horiz seg   (420,60)', 420, 60, (255, 170, 0, 255)),
        ('(4) arrow shaft         (150,250)', 150, 250, (64, 224, 255, 255)),
        ('(7) anchor green        (320,468)', 320, 468, (0, 255, 0, 255)),
    ]
    for name, x, y, exp in checks:
        got = px(w, nch, buf, x, y)
        d = max(abs(got[i] - exp[i]) for i in range(4))
        print('  %-36s -> RGBA%-22s %s' % (name, got, 'MATCH' if d <= 8 else 'MISMATCH exp=%s' % (exp,)))

    print('  line width is 1:1 with pixels (exact-colour column count):')
    for x, req, y0, y1, col in ((60, 5, 30, 70, (255, 48, 48)), (100, 6, 235, 265, (64, 224, 255))):
        ys = [y for y in range(y0, y1) if px(w, nch, buf, x, y)[:3] == col]
        print('     x=%d requested w=%d -> %d px of exact colour' % (x, req, len(ys)))

    print('  anti-aliasing scan across the diagonal, column x=165, y=139..151:')
    for y in range(139, 152):
        print('     y=%d %s' % (y, px(w, nch, buf, 165, y)))

    got = px(w, nch, buf, 480, 330)
    a = 0x99 / 255.0
    exp = tuple(int(BG[i] * (1 - a) + (0x20, 0xff, 0x40)[i] * a) for i in range(3)) + (255,)
    print('  (5) polygon fill alpha=0x99 @(480,330) = %s  expected~%s' % (got, exp))

    n, hit, _ = census(w, h, nch, buf, 25, 398, 210, 422,
                       lambda c: c[0] > 200 and c[1] > 200 and c[2] > 200)
    print('  (6) TEXT-BEFORE band 25..210/398..422 : %d/%d near-white px (drawn before the line)' % (hit, n))
    n, hit, _ = census(w, h, nch, buf, 395, 434, 540, 462,
                       lambda c: c[1] > 200 and c[0] < 200)
    print('  (6) TEXT-AFTER  band 395..540/434..462: %d/%d green px (drawn AFTER the line)' % (hit, n))
    n, hit, _ = census(w, h, nch, buf, 20, 409, 300, 415,
                       lambda c: c[0] > 200 and c[1] > 200 and c[2] > 200)
    print('  (6) white line drawn ACROSS the text, band 20..300/409..415: %d/%d white px' % (hit, n))

    def cyan(c): return c[2] > 200 and c[1] > 170 and c[0] < 130
    for label, x0, x1, y0, y1 in (('A  penW=6 cap=28 (line y=250)', 120, 310, 140, 360),
                                  ('B  penW=3 cap=28 (line y=215)', 420, 640, 100, 340)):
        best = (0, 0, (0, 0))
        for x in range(x0, x1):
            ys = [y for y in range(y0, y1) if cyan(px(w, nch, buf, x, y))]
            if ys and len(ys) > best[0]:
                best = (len(ys), x, (min(ys), max(ys)))
        print('  arrow head %s : max perpendicular extent = %d px at x=%d, y=%s' % (label, best[0], best[1], best[2]))

    n, hit, col = census(w, h, nch, buf, 0, 0, w, h, lambda c: c != BG, step=2)
    print('  whole canvas (every 2nd px): %d sampled, %d non-backdrop, %d distinct colours' % (n, hit, len(col)))
    print()


def alpha_png():
    path = os.path.join(SAVEDATA, 'poc_layerExDraw_alpha.png')
    w, h, nch, buf = load_png(path)
    print('== poc_layerExDraw_alpha.png  %dx%d nch=%d ==' % (w, h, nch))
    for name, x, y in (('line centre (100,10)', 100, 10), ('polygon centre (30,60)', 30, 60),
                       ('UNTOUCHED (400,300)', 400, 300), ('UNTOUCHED (600,450)', 600, 450)):
        print('  %-26s -> RGBA%s' % (name, px(w, nch, buf, x, y)))
    n, _, col = census(w, h, nch, buf, 0, 0, w, h)
    zero = sum(v for c, v in col.items() if c[3] == 0)
    op = sum(v for c, v in col.items() if c[3] == 255)
    print('  census: total=%d  alpha==0: %d  alpha==255: %d  partial(AA): %d' % (n, zero, op, n - zero - op))
    print('  top colours: %s' % top(col))
    print()


def stress_png():
    path = os.path.join(SAVEDATA, 'poc_stress_1920.png')
    w, h, nch, buf = load_png(path)
    print('== poc_stress_1920.png  %dx%d nch=%d ==' % (w, h, nch))
    BG = (16, 16, 24, 255)
    n, hit, col = census(w, h, nch, buf, 0, 0, w, h, lambda c: c != BG, step=2)
    print('  census (every 2nd px): %d sampled, %d non-backdrop (%.1f%%), %d distinct colours'
          % (n, hit, 100.0 * hit / n, len(col)))
    print('  top colours: %s' % top(col))
    exp = {(136, 153, 187): 'node rect outline / edge  0xff8899bb',
           (64, 224, 255): 'thick rounded polyline    0xff40e0ff',
           (16, 16, 24): 'backdrop                  0xff101018'}
    for c, v in sorted(col.items(), key=lambda kv: -kv[1])[:8]:
        tag = exp.get(c[:3], '')
        if tag:
            print('     %s x%-8d %s' % (c, v, tag))
    print('  ASCII map (one char per 16x32 block; "#" dense ink, "+" some, "-" sparse, "." none):')
    for by in range(0, h, 32):
        row = ''
        for bx in range(0, w, 16):
            ink = 0
            for y in range(by, min(by + 32, h), 2):
                for x in range(bx, min(bx + 16, w), 2):
                    if px(w, nch, buf, x, y) != BG:
                        ink += 1
            row += '#' if ink > 100 else ('+' if ink > 25 else ('-' if ink else '.'))
        print('  %4d %s' % (by, row))
    print()


if __name__ == '__main__':
    main_png()
    alpha_png()
    stress_png()
