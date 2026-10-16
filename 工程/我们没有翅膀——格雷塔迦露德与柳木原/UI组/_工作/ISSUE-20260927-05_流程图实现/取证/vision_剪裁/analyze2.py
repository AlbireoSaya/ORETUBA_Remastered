from PIL import Image
import sys

BASE = r'E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证'

def load(p):
    im = Image.open(p).convert('RGB')
    return im, im.load()

def is_fill(c):
    return (abs(c[0]-194) < 22 and abs(c[1]-212) < 22 and abs(c[2]-243) < 22) or \
           (abs(c[0]-95) < 22 and abs(c[1]-171) < 22 and abs(c[2]-210) < 22) or \
           (abs(c[0]-212) < 26 and abs(c[1]-177) < 26 and abs(c[2]-246) < 26)

def is_ink(c):
    # text ink over fill is ~ (22,34,58); bg is (39,45,59); require clearly darker than bg
    return c[0] < 33 and c[1] < 41 and c[2] < 70 and (c[2]-c[0]) > 12

def comps(px, x0, x1, y0, y1, minsize=2000):
    seen = set(); out = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in seen or not is_fill(px[x, y]): continue
            st = [(x, y)]; seen.add((x, y)); pts = []
            while st:
                cx, cy = st.pop(); pts.append((cx, cy))
                for nx, ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                    if x0 <= nx < x1 and y0 <= ny < y1 and (nx, ny) not in seen and is_fill(px[nx, ny]):
                        seen.add((nx, ny)); st.append((nx, ny))
            if len(pts) >= minsize:
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                out.append((min(xs), max(xs), min(ys), max(ys), len(pts)))
    out.sort(key=lambda r: (r[2], r[0]))
    return out

def report(path, x0, x1, y0, y1, label):
    im, px = load(path)
    print('=== %s  region x%d-%d y%d-%d' % (label, x0, x1, y0, y1))
    for i, (a, b, c, d, n) in enumerate(comps(px, x0, x1, y0, y1)):
        # ink strictly inside a vertical search window that excludes the node's own shadowed edge:
        # search x within [a+12, b-12] and y within [c-30, d+30] but count ink that is
        # *surrounded* by fill horizontally on that row (text over fill) or over bg (overflow)
        rows_ink = {}
        for y in range(c-30, d+31):
            cnt_in = 0; cnt_out = 0
            for x in range(a+8, b-7):
                if is_ink(px[x, y]):
                    # inside node?
                    if c-2 <= y <= d+2: cnt_in += 1
                    else: cnt_out += 1
            if cnt_in or cnt_out: rows_ink[y] = (cnt_in, cnt_out)
        if rows_ink:
            ys = sorted(rows_ink)
            above = [y for y in ys if y < c-2]
            below = [y for y in ys if y > d+2]
            it = min(ys); ib = max(ys)
            # ink column extent
            cols = [x for x in range(a+8, b-7) for y in ys if is_ink(px[x, y])]
            il, ir = (min(cols), max(cols)) if cols else (0, 0)
            print('%2d NODE x%4d-%4d y%4d-%4d w=%3d h=%3d' % (i, a, b, c, d, b-a, d-c))
            print('   ink rows %d..%d (h=%d) | ink cols %d..%d | padTop %+d padBot %+d padL %+d padR %+d'
                  % (it, ib, ib-it, il, ir, c-it, ib-d, il-a, b-ir))
            if above: print('   !! ink ABOVE node top by up to %d px (rows %d..%d)' % (c-min(above), min(above), max(above)))
            if below: print('   !! ink BELOW node bottom by up to %d px (rows %d..%d)' % (max(below)-d, min(below), max(below)))
        else:
            print('%2d NODE x%4d-%4d y%4d-%4d w=%3d h=%3d  (no ink found)' % (i, a, b, c, d, b-a, d-c))

if __name__ == '__main__':
    w = sys.argv[1]
    if w == 's1':
        report(BASE + '/E2_自证/E2_真实数据验收图_shot_84_flowchart.png', 490, 1250, 185, 1020, 'screen1')
    elif w == 's2':
        report(BASE + '/E1_09_屏2_巡演图_引擎导出.png', 490, 1250, 185, 1020, 'screen2')
