#!/usr/bin/env python3
"""只读目录树比较工具（仅 Python 标准库）。

串行元数据校验：不执行源文件、不联网、不读取配置；遇到 symlink/junction/reparse
立即 raise，不跳过任何错误。本工具不是 OS sandbox，也不阻止其他进程并发写入。
"""
import argparse
import hashlib
import json
import os
import stat as st_mod

WORKSPACE = r"E:/ZCode Workspace/Galgame"
OUT_BASE = os.path.join(WORKSPACE, "临时", "ISSUE-20261011-02")
CHUNK = 1 << 20
REPARSE = getattr(st_mod, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
NOTE = ("仅串行元数据校验：不执行源文件、不联网、不读取配置、不写源树；"
        "非 OS sandbox，不保证阻止并发写入；发现 symlink/junction/reparse 即报错，不跳过。")


def die(msg):
    raise SystemExit("error: " + msg)


def raise_walk_error(err):
    raise err


def is_reparse(path):
    s = os.lstat(path)
    return st_mod.S_ISLNK(s.st_mode) or bool(getattr(s, "st_file_attributes", 0) & REPARSE)


def under(child, parent):
    c = os.path.normcase(os.path.abspath(child))
    p = os.path.normcase(os.path.abspath(parent)).rstrip("\\/")
    return c == p or c.startswith(p + os.sep)


def check_chain(path, stop):
    stop = os.path.abspath(stop)
    cur = os.path.abspath(path)
    while True:
        if os.path.lexists(cur) and is_reparse(cur):
            die("reparse point in output path: " + cur)
        if os.path.normcase(cur) == os.path.normcase(stop):
            return
        parent = os.path.dirname(cur)
        if parent == cur:
            return
        cur = parent


def scan_tree(root):
    root = os.path.abspath(root)
    check_chain(root, os.path.splitdrive(root)[0] + os.sep)
    if os.path.lexists(root) and is_reparse(root):
        die("reparse root: " + root)
    files, total = {}, 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False, onerror=raise_walk_error):
        if is_reparse(dirpath):
            die("reparse dir reached: " + dirpath)
        for d in dirnames:
            p = os.path.join(dirpath, d)
            if is_reparse(p):
                die("reparse dir: " + p)
        for f in filenames:
            p = os.path.join(dirpath, f)
            if is_reparse(p):
                die("reparse file: " + p)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            s1 = os.stat(p)
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for blk in iter(lambda: fh.read(CHUNK), b""):
                    h.update(blk)
            s2 = os.stat(p)
            if (s1.st_size, s1.st_mtime_ns, s1.st_ino) != (s2.st_size, s2.st_mtime_ns, s2.st_ino):
                die("file changed while hashing: " + p)
            files[rel] = {"sha256": h.hexdigest(), "size": s2.st_size, "mtime_ns": s2.st_mtime_ns}
            total += s2.st_size
    for rel in sorted(files):
        s3 = os.stat(os.path.join(root, rel.replace("/", os.sep)))
        m = files[rel]
        if (s3.st_size, s3.st_mtime_ns) != (m["size"], m["mtime_ns"]):
            die("tree changed during scan: " + rel)
    return files, total


def main():
    ap = argparse.ArgumentParser(description="read-only tree compare (stdlib only)")
    ap.add_argument("--source", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    for label, p in (("source", a.source), ("reference", a.reference)):
        if not os.path.isdir(p) or is_reparse(p):
            die("%s is not a plain directory: %s" % (label, p))

    out = os.path.abspath(a.output)
    if not under(os.path.realpath(out), os.path.realpath(OUT_BASE)):
        die("output must resolve under " + OUT_BASE)
    for p in (a.source, a.reference):
        if under(os.path.realpath(out), os.path.realpath(p)):
            die("output must not be inside source/reference tree: " + out)
    if os.path.lexists(out):
        die("output already exists: " + out)
    check_chain(out, WORKSPACE)

    src, src_bytes = scan_tree(a.source)
    ref, ref_bytes = scan_tree(a.reference)

    rows = []
    n = {"identical": 0, "size_different": 0, "hash_different": 0, "source_only": 0, "reference_only": 0}
    for p in sorted(set(src) | set(ref)):
        x, y = src.get(p), ref.get(p)
        if x and y:
            if x["size"] != y["size"]:
                status = "size_different"
            elif x["sha256"] != y["sha256"]:
                status = "hash_different"
            else:
                status = "identical"
        elif x:
            status = "source_only"
        else:
            status = "reference_only"
        n[status] += 1
        rows.append({"path": p, "status": status, "source": x, "reference": y})
    changed = n["size_different"] + n["hash_different"]

    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    check_chain(out, WORKSPACE)

    manifest = {
        "tool": "readonly-tree-compare",
        "issue": "ISSUE-20261011-02",
        "note": NOTE,
        "source_root": os.path.abspath(a.source),
        "reference_root": os.path.abspath(a.reference),
        "source": {"files": {k: src[k] for k in sorted(src)}, "bytes": src_bytes},
        "reference": {"files": {k: ref[k] for k in sorted(ref)}, "bytes": ref_bytes},
        "comparison": rows,
        "summary": {
            "source_files": len(src), "source_bytes": src_bytes,
            "reference_files": len(ref), "reference_bytes": ref_bytes,
            "identical": n["identical"], "changed": changed,
            "size_different": n["size_different"], "hash_different": n["hash_different"],
            "source_only": n["source_only"], "reference_only": n["reference_only"],
        },
    }
    with open(out, "x", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print("files source=%d reference=%d" % (len(src), len(ref)))
    print("bytes source=%d reference=%d" % (src_bytes, ref_bytes))
    print("identical=%d changed=%d source_only=%d reference_only=%d"
          % (n["identical"], changed, n["source_only"], n["reference_only"]))


if __name__ == "__main__":
    main()