# -*- coding: utf-8 -*-
r"""ISSUE-20260924-04 · 把 25_config.json 屏顶 note 里的**行号引用**换成函数名 / 动作名

理由：一审实测 note ⑥ 的 6 处行号引用**全部陈旧**（M47 之后代码行号漂移），
类同「陈旧数字」；行号在每次改动后必然再漂 ⇒ 只写「文件::函数名」与「动作名」是根治。
§④ 的 `replica.js:1566-1575` 同样处理。

手法：**字节级精确子串替换**（每处先断言命中 1 次），不经 JSON 序列化回写（避免格式化/转义被翻新）。
搜索串按 JSON 的转义口径生成（json.dumps(...)[1:-1]），因此含 `\n` / `\` 的片段也能精确命中。
"""
import io
import json
import sys

P = r"E:\ZCode Workspace\Galgame\临时\wt-qbicons\工程\我们没有翅膀——格雷塔迦露德与柳木原\UI组\layout\screens\25_config.json"

REPL = [
    # ⑥ 机制行：函数名已在句中，行号删掉
    ("`ui_screens.tjs::uiScreenConfigSyncPage(page)`（**第 1343 行**）",
     "`ui_screens.tjs::uiScreenConfigSyncPage(page)`"),
    ("`replica.js::configDerivePageFlags(page)`（**第 3452 行**）同口径。",
     "`replica.js::configDerivePageFlags(page)` 同口径。"),
    # ⑥ 进屏装入点：补 HTML 侧同名函数、去掉行号
    ("① 进屏：krkr `uiScreenConfigFlagsInitFor`（`ui_screens.tjs:1390`）",
     "① 进屏：krkr `ui_screens.tjs::uiScreenConfigFlagsInitFor` / HTML `replica.js::configFlagsInitFor`"),
    # ⑥ ②③ 装入点：改成动作名（两端同名，行号必漂）
    ("② 切页：krkr `ui_screens.tjs:2038` · HTML `replica.js:3314` ｜③ 初始化：krkr `ui_screens.tjs:2055` · HTML `replica.js:3331`；",
     "② 切页：动作 `config_tab_1` / `config_tab_2` 分支 ｜③ 初始化：动作 `config_reset` 分支；"),
    # ⑥ 写完后重派生：同样改成动作名
    ("（krkr `ui_screens.tjs:2118` / `:2069`；HTML `replica.js:3446` —— 目的：",
     "（两端同动作名 `config_set_*` / `config_char_*` 的分支 —— 目的："),
    # ④ SETTING_DEF 行号（一审实测实际区间与写的不同）
    ("的 `SETTING_DEF[k].def`（replica.js:1566-1575）",
     "的 `SETTING_DEF[k].def`（该文件里的 `SETTING_DEF` 表）"),
]


def esc(s):
    """按 JSON 源码口径转义（与文件里 note 字符串的写法一致）"""
    return json.dumps(s, ensure_ascii=False)[1:-1]


def main():
    raw = io.open(P, encoding="utf-8", newline="").read()
    before = json.loads(raw)["note"]
    cr_before = raw.count("\r")

    for old, new in REPL:
        o, n = esc(old), esc(new)
        c = raw.count(o)
        if c != 1:
            print("★ 命中 %d 次（期望 1）：%r" % (c, old[:70]))
            return 1
        raw = raw.replace(o, n)
        print("OK 替换：%s" % old[:62].replace("\n", " "))

    # 校验可解析 + note 内已无行号引用
    after = json.loads(raw)
    assert after["note"] != before
    el_b, el_a = before, after["note"]
    import re
    left = [l for l in el_a.split("\n") if re.search(r"\.tjs:\d+|\.js:\d+|第 \d+ 行", l)]
    print("\n=== 校验 ===")
    print("JSON 可解析 = True ｜ 元素数 =", len(after["elements"]),
          "｜ 除 note 外的顶层键：", [k for k in after if k != "note"])
    print("note 里剩余行号引用行数 =", len(left))
    for l in left:
        print("   仍含行号：", l[:160])
    io.open(P, "w", encoding="utf-8", newline="").write(raw)
    print("已写回（CR 数 改前/改后 = %d / %d）" % (cr_before, raw.count("\r")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
