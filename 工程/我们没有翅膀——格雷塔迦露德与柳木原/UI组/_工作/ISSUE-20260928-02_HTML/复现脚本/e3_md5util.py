# -*- coding: utf-8 -*-
r"""E3（HTML 侧）· **行尾健壮**的文件指纹工具（本工程通用写法）

■ 为什么需要（一审 Major/Minor 指出的失真点）
  本仓库 `core.autocrlf=true` ⇒ 同一份内容在工作区可能是 **CRLF**，而生成器/记录里写的是 **LF**
  规范化值。若直接拿 `md5(读到的字节)` 与记录值比，就会在「盘面是 CRLF、记录是 LF」时**误判不一致**，
  或者反过来把已变的文件判成没变。故所有涉及锚点的脚本一律按本工具的口径取值：

  · `raw`  —— 磁盘上**实际字节**的 md5（可能是 CRLF 或 LF）；
  · `lf`   —— 把 CRLF 规范化成 LF 后的 md5（**记录/冻结书里的值一律用这一形态**）；
  · `crlf` —— 把 LF 规范化成 CRLF 后的 md5（Windows 工作区实际字节通常等于它）。

  锚点比较 = **三形态里任一命中即算命中**，并在输出里**同时打印三个值 + 命中形态**，
  避免"按错形态哈希 ⇒ 误判不一致"。

■ 用法
    from e3_md5util import forms, accepts, describe
    f = forms(path)                       # {"raw":…, "lf":…, "crlf":…, "has_crlf":bool}
    ok, form = accepts(f, {"lf": "4c8f…", "crlf": "cded…"})
    print(describe(path))
"""
import hashlib
import io


def raw_bytes(path):
    return io.open(path, "rb").read()


def forms_of_bytes(b):
    """三种形态的 md5；`has_crlf` = 原始字节里是否含 CRLF。"""
    lf = b.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {"raw": hashlib.md5(b).hexdigest(),
            "lf": hashlib.md5(lf).hexdigest(),
            "crlf": hashlib.md5(crlf).hexdigest(),
            "has_crlf": (b"\r\n" in b),
            "n": len(b)}


def forms(path):
    return forms_of_bytes(raw_bytes(path))


def accepts(f, anchors):
    """anchors 形如 {"lf": "<hex 或 None>", "crlf": "<hex 或 None>", "raw": …}。
    返回 (命中?, 命中的形态名, 命中值)。三形态按 raw → lf → crlf 顺序查。"""
    for form in ("raw", "lf", "crlf"):
        want = anchors.get(form)
        if want and f.get(form) == want:
            return True, form, want
    return False, None, None


def describe(path, anchors=None, label=None):
    """一行可贴进日志的描述：同时给三形态 md5 + 是否含 CRLF + 锚点命中情况。"""
    f = forms(path)
    s = "%s%s 原始 %s（%s）｜ LF %s ｜ CRLF %s" % (
        (label + " ") if label else "", path, f["raw"],
        "含 CRLF" if f["has_crlf"] else "纯 LF", f["lf"], f["crlf"])
    if anchors:
        if not any(anchors.get(k) for k in ("raw", "lf", "crlf")):
            s += " ｜ 锚点：**未设**（跳过哈希锚）"
        else:
            ok, form, val = accepts(f, anchors)
            s += " ｜ 锚点%s（命中形态=%s，值=%s）" % ("命中 ✓" if ok else "未命中 ✗", form or "-", val or "-")
    return s
