from PIL import Image
import sys, collections

BASE = r'E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证'

def masks(im):
    px = im.load(); W, H = im.size
    def is_fill(c):
        return (abs(c[0]-194) < 20 and abs(c[1]-212) < 20 and abs(c[2]-243) < 20) or \
               (abs(c[0]-95) < 20 and abs(c[1]-171) < 20 and abs(c[2]-210) < 20) or \
               (abs(c[0]-210) < 24 and abs(c[1]-178) < 24 and abs(c[2]-246) < 24)  # purple frag
    def is_ink(c):
        return c[0] < 40 and c[1] < 48 and c[2] < 78
    return px, is_fill, is_ink

def components(px, is_fill, x0, x1, y0, y1, minsize=800):
    seen = set()
    comps = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in seen: continue
            if not is_fill(px[x, y]): continue
            # BFS
            stack = [(x, y)]; seen.add((x, y)); pts = []
            while stack:
                cx, cy = stack.pop(); pts.append((cx, cy))
                for nx, ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                    if x0 <= nx < x1 and y0 <= ny < y1 and (nx,ny) not in seen and is_fill(px[nx,ny]):
                        seen.add((nx,ny)); stack.append((nx,ny))
            if len(pts) >= minsize:
                xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                comps.append((min(xs), max(xs), min(ys), max(ys), len(pts)))
    return comps

def analyze(path, x0, x1, y0, y1):
    im = Image.open(path).convert('RGB')
    px, is_fill, is_ink = masks(im)
    comps = components(px, is_fill, x0, x1, y0, y1)
    comps.sort(key=lambda r: (r[2], r[0]))
    print('=== %s  (%d, %d)  region x%d-%d y%d-%d' % (path.split('/')[-1], im.size[0], im.size[1], x0, x1, y0, y1))
    for i, (a, b, c, d, n) in enumerate(comps):
        # ink inside expanded rect
        xs = []; ys = []
        for y in range(c-20, d+21):
            for x in range(a-6, b+7):
                if 0 <= x < im.size[0] and 0 <= y < im.size[1] and is_ink(px[x, y]):
                    xs.append(x); ys.append(y)
        if not xs:
            print('%2d NODE x%4d-%4d y%4d-%4d w=%3d h=%3d  ink: none' % (i, a, b, c, d, b-a, d-c)); continue
        it, ib, il, ir = min(ys), max(ys), min(xs), max(xs)
        print('%2d NODE x%4d-%4d y%4d-%4d w=%3d h=%3d | ink x%4d-%4d y%4d-%4d | margins T%+4d B%+4d L%+4d R%+4d' % (
            i, a, b, c, d, b-a, d-c, il, ir, it, ib, c-it, ib-d, il-a, b-ir))

if __name__ == '__main__':
    which = sys.argv[1]
    if which == 's1':
        analyze(BASE + '/E2_自证/E2_真实数据验收图_shot_84_flowchart.png', 480, 1260, 185, 1040)
    elif which == 's2':
        analyze(BASE + '/E1_09_屏2_巡演图_引擎导出.png', 480, 1260, 185, 1040)
