def blend_rgb_floor256(dest, src, hold_dest_alpha=False):
    for v in (dest, src):
        if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 0xFFFFFFFF:
            raise ValueError("dest/src must be non-bool uint32 int")
    if not isinstance(hold_dest_alpha, bool):
        raise ValueError("hold_dest_alpha must be bool")
    a = src >> 24
    out = (dest & 0xFF000000) if hold_dest_alpha else 0
    for sh in (0, 8, 16):
        d = (dest >> sh) & 0xFF
        s = (src >> sh) & 0xFF
        out |= (d + ((s - d) * a // 256)) << sh
    return out

def blend_argb_mmx_pairs(dest,src,dst_address=0):
    if not (type(dst_address) is int and 0<=dst_address<=0xffffffff and dst_address%4==0): raise ValueError
    if len(dest)!=len(src): raise ValueError
    for x in list(dest)+list(src):
        if not (type(x) is int and 0<=x<=0xffffffff): raise ValueError
    n=len(dest)
    if dst_address+n*4>2**32: raise ValueError
    out=list(dest)
    def mix(d,s,c):
        a=s>>24
        if c and a==255: return s
        r=0
        for sh in (0,8,16,24):
            dc=(d>>sh)&255; sc=(s>>sh)&255
            r|=((dc+((sc-dc)*a//256))&255)<<sh
        return r
    i=0
    if n>4:
        if dst_address&4:
            out[0]=mix(out[0],src[0],True); i=1
        while i<n-4:
            c=(src[i]>>24)==255 and (src[i+1]>>24)==255
            out[i]=mix(out[i],src[i],c); out[i+1]=mix(out[i+1],src[i+1],c)
            i+=2
    while i<n:
        out[i]=mix(out[i],src[i],True); i+=1
    return out