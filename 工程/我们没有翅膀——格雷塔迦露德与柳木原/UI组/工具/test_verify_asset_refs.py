# -*- coding: utf-8 -*-
r"""自测：`verify_ui.iter_asset_refs` 必须覆盖 `state_assets` 里的三态图。

**为什么需要这个自测**：M35 发现 `verify_ui.py` 的 [1] 引用完整性**完全不覆盖 `state_assets`**
（旧实现的白名单要求值是字符串，而 `state_assets` 是字典 → 里层 normal/hover/pressed 被静默丢弃），
后果是三态图缺件**一路绿灯**。这是「静默失效」，靠跑一遍 CLI 是看不出来的——
必须有一条断言把它钉住，否则日后重构很容易把它改回去而无人察觉。

用法：`python test_verify_asset_refs.py` —— 全通过退出码 0，任一断言失败退出码 1。
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_ui as V

FAIL = []


def check(name, cond, detail=""):
    print("  %s %s%s" % ("OK  " if cond else "FAIL", name, ("  —— " + detail) if detail else ""))
    if not cond:
        FAIL.append(name)


def refs(node):
    return V.iter_asset_refs(node)


def main():
    print("=" * 72)
    print("verify_ui.iter_asset_refs 覆盖性自测（state_assets）")
    print("=" * 72)

    # 1. 三态全部收到
    node = {"id": "a", "kind": "hit",
            "state_assets": {"normal": "ui/n.png", "hover": "ui/h.png", "pressed": "ui/p.png"}}
    got = dict((p, r) for r, p in refs(node))
    check("state_assets.normal 被收集", got.get("state_assets.normal") == "ui/n.png", str(got))
    check("state_assets.hover 被收集", got.get("state_assets.hover") == "ui/h.png", str(got))
    check("state_assets.pressed 被收集", got.get("state_assets.pressed") == "ui/p.png", str(got))

    # 2. 缺键/空串不产生假引用
    node2 = {"id": "b", "state_assets": {"normal": "ui/n.png", "hover": "", "pressed": None}}
    got2 = [r for r, _p in refs(node2)]
    check("空串/None 不产生引用", got2 == ["ui/n.png"], str(got2))

    # 3. 与 image 的 asset 共存，不互相吞掉
    node3 = {"elements": [
        {"id": "img", "kind": "image", "asset": "ui/bg.png"},
        {"id": "hit", "kind": "hit", "state_assets": {"normal": "ui/n.png"}},
    ]}
    got3 = sorted(r for r, _p in refs(node3))
    check("asset 与 state_assets 并存", got3 == ["ui/bg.png", "ui/n.png"], str(got3))

    # 4. item_frame 仍被收集（不能为了修 state_assets 而弄坏既有白名单）
    node4 = {"item_frame": "ui/f.png", "asset": "ui/a.png"}
    got4 = sorted(r for r, _p in refs(node4))
    check("item_frame/asset 未回归", got4 == ["ui/a.png", "ui/f.png"], str(got4))

    # 5. 深层嵌套里的 state_assets 也要收到（list 下标路径）
    node5 = {"screens": {"s": {"elements": [{"state_assets": {"pressed": "ui/x.png"}}]}}}
    paths = [p for _r, p in refs(node5)]
    check("深层 list 下标路径", "screens.s.elements[0].state_assets.pressed" in paths, str(paths))

    # 6. 真实 layout 上：state_assets 的引用数必须 > 0（这是当初漏掉的实证）
    lay = os.path.join(os.path.dirname(HERE), "layout")
    n_state = n_all = 0
    if os.path.isdir(lay):
        for root, _d, files in os.walk(lay):
            for f in files:
                if not f.lower().endswith(".json"):
                    continue
                for _r, p in refs(json.load(open(os.path.join(root, f), encoding="utf-8"))):
                    n_all += 1
                    if ".state_assets." in p:
                        n_state += 1
    check("真实 layout 上收到 state_assets 引用（>0）", n_state > 0,
          "state_assets=%d / 总 %d" % (n_state, n_all))

    # 7. 一审 Minor-10：**不固定三键** —— 第四态（如 focus）也必须收进来，
    #    否则只是把「静默丢弃」的范围缩小了一点。
    node7 = {"state_assets": {"normal": "ui/n.png", "focus": "ui/focus.png", "disabled": "ui/dis.png"}}
    got7 = sorted(r for r, _p in refs(node7))
    check("非三键的自定义态也被收集（Minor-10）",
          got7 == ["ui/dis.png", "ui/focus.png", "ui/n.png"], str(got7))

    # 8. 一审 Minor-5：state_assets 的值**不是字典**（误写成字符串）时必须暴露，而不是静默忽略。
    node8 = {"state_assets": "ui/typo.png"}
    got8 = [(r, p) for r, p in refs(node8)]
    check("state_assets 非字典 -> 计入引用表（供 [1] 报缺件）",
          got8 == [("ui/typo.png", "state_assets")], str(got8))

    print("-" * 72)
    if FAIL:
        print("结果：**%d 项失败** —— %s" % (len(FAIL), "；".join(FAIL)))
        return 1
    print("结果：**全部通过**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
