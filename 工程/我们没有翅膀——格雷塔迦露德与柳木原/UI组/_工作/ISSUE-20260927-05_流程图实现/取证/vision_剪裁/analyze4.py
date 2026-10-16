from PIL import Image
import sys

BASE = r'E:/ZCode Workspace/Galgame/临时/wt-qbicons/工程/我们没有翅膀——格雷塔迦露德与柳木原/UI组/_工作/ISSUE-20260927-05_流程图实现/取证'
FILLS = [(194,212,243),(95,171,210),(208,176,244)]

def kind(c):
    for i,f in enumerate(FILLS):
        if abs(c[0]-f[0])<12 and abs(c[1]-f[1])<12 and abs(c[2]-f[2])<12:
            return 'CFP'[i]
    return None
def is_link(c):
    return abs(c[0]-101)<5 and abs(c[1]-177)<5 and abs(c[2]-212)<5
def is_ink(c):
    return c[0]<33 and c[1]<41 and c[2]<70 and (c[2]-c[0])>12

def detect(px, xa, xb, ya, yb):
    rows = {}
    for y in range(ya, yb):
        xs = [x for x in range(xa, xb) if kind(px[x,y])]
        if not xs: continue
        L, R = min(xs), max(xs)
        if R-L < 150: continue
        dens = len(xs)/(R-L+1)
        if dens < 0.45: continue
        rows[y] = (L, R, dens)
    out = []
    for y in sorted(rows):
        L,R,d = rows[y]
        if out and y == out[-1][3]+1 and abs(out[-1][0]-L) < 45 and abs(out[-1][1]-R) < 45:
            o = out[-1]; out[-1] = (min(o[0],L), max(o[1],R), o[2], y)
        else:
            out.append((L,R,y,y))
    return [r for r in out if r[3]-r[2] > 25]

def main(path, label):
    im = Image.open(path).convert('RGB'); px = im.load(); W,H = im.size
    print('=== %s (%dx%d)' % (label, W, H))
    for cname, xa, xb in (('LEFT', 490, 850), ('RIGHT', 880, 1300)):
        print('-- column %s --' % cname)
        for i,(a,b,c,d) in enumerate(detect(px, xa, xb, 185, 1030)):
            h=d-c
            t = kind(px[(a+b)//2, c+4]) or '?'
            rows = {}
            for y in range(max(0,c-16), min(H,d+17)):
                n = sum(1 for x in range(a+8,b-7) if is_ink(px[x,y]))
                if n: rows[y]=n
            ys = sorted(rows)
            if not ys:
                print('  %2d x%4d-%4d y%4d-%4d h=%3d %s   NO-INK' % (i,a,b,c,d,h,t)); continue
            lines=[]
            for y in ys:
                if lines and y-lines[-1][1] <= 4: lines[-1][1]=y
                else: lines.append([y,y])
            desc=' | '.join('L%d %d..%d'%(k+1,l[0],l[1]) for k,l in enumerate(lines))
            flag=''
            if ys[0] < c: flag += ' OVERFLOW-TOP %dpx' % (c-ys[0])
            if ys[-1] > d: flag += ' OVERFLOW-BOT %dpx' % (ys[-1]-d)
            print('  %2d x%4d-%4d y%4d-%4d h=%3d %s padT%+3d padB%+3d %s%s' % (i,a,b,c,d,h,t,ys[0]-c,d-ys[-1],desc,flag))
    # links
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
            if len(pts)>30:
                xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
                comps.append((min(xs),max(xs),min(ys),max(ys),len(pts)))
    comps.sort(key=lambda r:(r[2],r[0]))
    print('-- %d link components (tol +-5) --' % len(comps))
    for a,b,c,d,n in comps:
        print('  link x%4d-%4d y%4d-%4d n=%d' % (a,b,c,d,n))

if __name__=='__main__':
    w=sys.argv[1]
    if w=='s1': main(BASE+'/E2_自证/E2_真实数据验收图_shot_84_flowchart.png','S1 shot84')
    if w=='s2': main(BASE+'/E1_09_屏2_巡演图_引擎导出.png','S2 tour')
