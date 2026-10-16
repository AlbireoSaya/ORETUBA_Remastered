from PIL import Image
import sys

BASE = r'E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证'

FILLS = [(194,212,243),(95,171,210),(208,176,244)]
def is_fill(c):
    for f in FILLS:
        if abs(c[0]-f[0])<22 and abs(c[1]-f[1])<22 and abs(c[2]-f[2])<22: return True
    return False
def is_link(c):
    return abs(c[0]-101)<7 and abs(c[1]-177)<7 and abs(c[2]-212)<7
def is_ink(c):
    return c[0]<33 and c[1]<41 and c[2]<70 and (c[2]-c[0])>12

def rects(px, x0, x1, y0, y1, minw=150):
    # find node rects: rows with a fill run wider than minw
    cand = {}
    for y in range(y0, y1):
        xs = [x for x in range(x0, x1) if is_fill(px[x,y])]
        if not xs: continue
        runs = []; s = xs[0]; p = xs[0]
        for x in xs[1:]:
            if x-p > 12: runs.append((s,p)); s = x
            p = x
        runs.append((s,p))
        wide = [r for r in runs if r[1]-r[0] >= minw]
        if len(wide) == 1: cand[y] = wide[0]
    out = []
    for y in sorted(cand):
        a,b = cand[y]
        if out and y == out[-1][3]+1 and abs(out[-1][0]-a) < 45 and abs(out[-1][1]-b) < 45:
            o = out[-1]; out[-1] = (min(o[0],a), max(o[1],b), o[2], y)
        else:
            out.append((a,b,y,y))
    return [r for r in out if r[3]-r[2] > 20]

def main(path, label):
    im = Image.open(path).convert('RGB'); px = im.load(); W,H = im.size
    print('=== %s (%dx%d)' % (label, W, H))
    rs = rects(px, 490, 1300, 185, 1030)
    print('-- %d node rects --' % len(rs))
    for i,(a,b,c,d) in enumerate(rs):
        h = d-c
        rows = {}
        for y in range(max(0,c-14), min(H,d+15)):
            n = sum(1 for x in range(a+8,b-7) if is_ink(px[x,y]))
            if n: rows[y] = n
        ys = sorted(rows)
        if not ys:
            print('%2d x%4d-%4d y%4d-%4d h=%3d  NO-INK' % (i,a,b,c,d,h)); continue
        # split ink rows into lines
        lines = []
        for y in ys:
            if lines and y-lines[-1][1] <= 3: lines[-1][1] = y
            else: lines.append([y,y])
        desc = ' | '.join('L%d ink %d..%d' % (k+1, l[0], l[1]) for k,l in enumerate(lines))
        ov_top = c - ys[0]; ov_bot = ys[-1] - d
        flag = ''
        if ov_top < 0: flag += ' !!OVERFLOW-TOP %dpx' % (-ov_top)
        if ov_bot > 0: flag += ' !!OVERFLOW-BOT %dpx' % ov_bot
        print('%2d x%4d-%4d y%4d-%4d h=%3d padTop=%+3d padBot=%+3d %s%s' % (i,a,b,c,d,h,c-ys[0],ys[-1]-d,desc,flag))
    # link components
    seen=set(); comps=[]
    for y in range(185,1030):
        for x in range(490,1300):
            if (x,y) in seen or not is_link(px[x,y]): continue
            st=[(x,y)]; seen.add((x,y)); pts=[]
            while st:
                cx,cy=st.pop(); pts.append((cx,cy))
                for nx,ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                    if 185<=ny<1030 and 490<=nx<1300 and (nx,ny) not in seen and is_link(px[nx,ny]):
                        seen.add((nx,ny)); st.append((nx,ny))
            if len(pts)>40:
                xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
                comps.append((min(xs),max(xs),min(ys),max(ys),len(pts)))
    comps.sort(key=lambda r:(r[2],r[0]))
    print('-- %d link components --' % len(comps))
    for a,b,c,d,n in comps:
        print('  link x%4d-%4d y%4d-%4d  n=%d  w=%d h=%d' % (a,b,c,d,n,b-a,d-c))

if __name__=='__main__':
    w=sys.argv[1]
    if w=='s1': main(BASE+'/E2_自证/E2_真实数据验收图_shot_84_flowchart.png','S1 real shot84')
    if w=='s2': main(BASE+'/E1_09_屏2_巡演图_引擎导出.png','S2 tour')
