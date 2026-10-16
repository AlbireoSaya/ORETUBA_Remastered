# -*- coding: utf-8 -*-
r"""M4 · `verify_editor_export.py` 守门「按字段粒度」的**反向自证**（可复跑）

■ 守的是什么（复审 Major-2）
  入库守门原先按**元素集合**比较：`state_carriers(old) - state_carriers(new)` 把
  `state_group` 与 `state_assets` 合并成一个 id 集合 ⇒ **只丢其中一件仍然放行**
  （独立复审实测：只丢 `state_assets`、保留 `state_group` 的导出件被放行并**实际覆盖落盘**，rc=0）。

■ 本脚本做的三件事（全部在**临时副本**上做；被审原文件只读 + md5 前后比对）
  C1：构造「某元素**只丢 `state_assets`**（保留 `state_group`）」的导出件
  C2：构造「某元素**只丢 `state_group`**（保留 `state_assets`）」的导出件
      ⇒ 两者都必须 **rc≠0**（拒绝写入）且 `layout/screens/01_title.json` **字节未变**
  C3：C1 再加 `--allow-drop --dry` ⇒ 必须 **rc=0 放行**，且**逐条打印**丢失明细
      （元素 id + 丢的字段名）

■ 用法
  python 工具/test_gate_field_granularity.py      # 退出码 0 = 三项都符合预期
"""
import os, io, json, sys, hashlib, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(HERE)
SCREENS = os.path.join(UI, "layout", "screens")
BASE = os.path.join(UI, "_工作", "ISSUE-20260922-28_M4_证据", "t1_gate")
TARGET = os.path.join(SCREENS, "01_title.json")

# (用例名, 要丢的字段, 承载该字段的元素 id)  —— 均为**元素顶层**字段
CASES = (("C1_only_state_assets_lost", "state_assets", "title.menu_hit_1"),
         ("C2_only_state_group_lost", "state_group", "title.menu_txt_start"))

# ★ M46（一审 Minor-6）：**嵌套**状态字段的用例 —— `list` 的逐项态图在
#   `item_frame.state_assets` 下，浅层比较看不见它。用选择支屏（真带该字段）造 C4：
#   只删这一层嵌套键，守门必须同样拒绝入库。
NESTED_CASE = ("C4_nested_item_frame_states_lost", "36_choices.json",
               "item_frame.state_assets", "ch.choices")


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(case, drop_field, victim_id):
    """在 BASE/<case>/01_title.json 造一份「只丢 drop_field」的导出件。"""
    d = json.load(io.open(TARGET, encoding="utf-8"))
    hit = False
    for e in d["elements"]:
        if e.get("id") == victim_id:
            assert drop_field in e, "%s 本来就没有 %s" % (victim_id, drop_field)
            del e[drop_field]
            hit = True
    assert hit, "找不到 %s" % victim_id
    out = os.path.join(BASE, case)
    os.makedirs(out, exist_ok=True)
    io.open(os.path.join(out, "01_title.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    return out


def build_nested(case, fname, path, victim_id):
    """造「只丢嵌套字段 `path`」的导出件（逐段删除，父级保留）。"""
    src = os.path.join(SCREENS, fname)
    d = json.load(io.open(src, encoding="utf-8"))
    hit = False
    for e in d["elements"]:
        if e.get("id") == victim_id:
            cur = e
            ks = path.split(".")
            for k in ks[:-1]:
                assert k in cur, "%s 没有 %s" % (victim_id, k)
                cur = cur[k]
            assert ks[-1] in cur, "%s 的 %s 本来就没有 %s" % (victim_id, path, ks[-1])
            del cur[ks[-1]]
            hit = True
    assert hit, "找不到 %s" % victim_id
    out = os.path.join(BASE, case)
    os.makedirs(out, exist_ok=True)
    io.open(os.path.join(out, fname), "w", encoding="utf-8", newline="\n").write(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    return out, src


def run(src_dir, extra=()):
    cmd = [sys.executable, os.path.join(HERE, "verify_editor_export.py"), "--from", src_dir]
    cmd += list(extra)
    p = subprocess.run(cmd, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    before = io.open(TARGET, "rb").read()
    print("=" * 78)
    print("守门字段粒度反向自证 ｜ 被审原文件 %s" % TARGET)
    print("  跑前 md5 = %s" % md5b(before))
    print("=" * 78)
    ok = True

    for case, drop, victim in CASES:
        src = build(case, drop, victim)
        rc, out = run(src)
        after = io.open(TARGET, "rb").read()
        print("\n───── %s（元素 %s 只丢 %s）─────" % (case, victim, drop))
        for line in out.rstrip("\n").splitlines():
            print("   | " + line)
        good = (rc != 0) and (after == before)
        print("   ⇒ 退出码 %d（期望 ≠0）；原文件 md5 %s（%s）⇒ %s"
              % (rc, md5b(after), "未变" if after == before else "**被改写！**",
                 "符合预期 ✓" if good else "**不符合预期** ✗"))
        ok = ok and good

    # C3：放行开关必须放行 + 逐条明细
    src = os.path.join(BASE, CASES[0][0])
    rc, out = run(src, ("--allow-drop", "--dry"))
    after = io.open(TARGET, "rb").read()
    print("\n───── C3 = C1 + --allow-drop --dry（放行开关）─────")
    for line in out.rstrip("\n").splitlines():
        print("   | " + line)
    detail = ("丢失字段 state_assets" in out) and ("title.menu_hit_1" in out)
    good = (rc == 0) and detail and (after == before)
    print("   ⇒ 退出码 %d（期望 0）；逐条明细已打印=%s；原文件 md5 %s ⇒ %s"
          % (rc, detail, md5b(after), "符合预期 ✓" if good else "**不符合预期** ✗"))
    ok = ok and good

    print("\n" + "=" * 78)
    # C4：嵌套状态字段（item_frame.state_assets）单独丢弃 —— 必须拒绝
    case, fname, path, victim = NESTED_CASE
    src, orig = build_nested(case, fname, path, victim)
    bef = io.open(orig, "rb").read()
    rc, out = run(src)
    aft = io.open(orig, "rb").read()
    print("\n───── %s（%s :: %s 只丢嵌套字段 %s）─────" % (case, fname, victim, path))
    for line in out.rstrip("\n").splitlines():
        print("   | " + line)
    detail = (path in out) and (victim in out)
    good = (rc != 0) and detail and (bef == aft)
    print("   ⇒ 退出码 %d（期望 ≠0）；逐条明细含 `%s`+`%s`=%s；原文件 md5 %s ⇒ %s"
          % (rc, path, victim, detail, md5b(aft), "符合预期 ✓" if good else "**不符合预期** ✗"))
    ok = ok and good

    print("结果：%s" % ("四项全部符合预期 ✓" if ok else "**有项不符合预期** ✗"))
    print("（被审原文件 01_title.json md5 始终 = %s）" % md5b(before))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
