# -*- coding: utf-8 -*-
"""C9-B 反向：verify_editor_export 的「守门是否真的拒绝写」+ 粒度缺口。
以及 C8 的补充：数据里是否存在 z/visible_default 为 null（会让判据复算崩或偏）。"""
import io, os, json, sys, copy, glob, importlib.util, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(UI, "工具")
sys.path.insert(0, TOOLS)

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def hdr(t):
    print("\n" + "=" * 78); print(t); print("=" * 78)

vee = load_mod("vee2", os.path.join(TOOLS, "verify_editor_export.py"))
vee.run = lambda *a, **k: (0, "")          # 隔离：不跑 gen_layout / verify_ui
root = os.path.join(HERE, "rev_exp")
if os.path.isdir(root): shutil.rmtree(root)

def setup(variant):
    screens = os.path.join(root, variant, "layout", "screens")
    os.makedirs(screens, exist_ok=True)
    inbox = os.path.join(root, variant, "编辑器修改区")
    os.makedirs(inbox, exist_ok=True)
    old = json.load(io.open(os.path.join(UI, "layout", "screens", "01_title.json"), encoding="utf-8"))
    io.open(os.path.join(screens, "01_title.json"), "w", encoding="utf-8").write(
        json.dumps(old, ensure_ascii=False, indent=2))
    new = copy.deepcopy(old)
    for e in new["elements"]:
        if e["id"] == "title.menu_txt_start":
            if variant == "full":
                e.pop("state_group", None); e.pop("state_assets", None)
            else:                      # partial：只丢 state_assets，保留 state_group
                e.pop("state_assets", None)
    io.open(os.path.join(inbox, "01_title.json"), "w", encoding="utf-8").write(
        json.dumps(new, ensure_ascii=False, indent=2))
    return screens, inbox

for variant, expect in (("full", "应被拦下（rc=1）"), ("partial", "? 粒度缺口待定")):
    hdr("C9-B 反向 [%s]：%s" % (variant, expect))
    screens, inbox = setup(variant)
    vee.SCREENS = screens
    vee.ROLLBACK = os.path.join(root, variant, "rollback")
    before = io.open(os.path.join(screens, "01_title.json"), encoding="utf-8").read()
    old_argv = sys.argv[:]
    sys.argv = ["verify_editor_export.py", "--from", inbox]
    try:
        rc = vee.main()
    finally:
        sys.argv = old_argv
    after = io.open(os.path.join(screens, "01_title.json"), encoding="utf-8").read()
    print("  → 退出码 =", rc, "｜ 目标文件是否被改写 =", before != after)

# ── C8 补充：null 值检查 ─────────────────────────────────────────
hdr("C8 补充：layout/screens 里是否有 z / visible_default / state_assets 为 null")
bad = []
for f in sorted(glob.glob(os.path.join(UI, "layout", "screens", "[0-9]*.json"))):
    d = json.load(io.open(f, encoding="utf-8"))
    for e in d.get("elements") or []:
        for k in ("z", "x", "y", "w", "h"):
            if k in e and e[k] is None:
                bad.append((os.path.basename(f), e["id"], k))
        if "state_assets" in e and e["state_assets"] is None:
            bad.append((os.path.basename(f), e["id"], "state_assets=null"))
        if "state_group" in e and e["state_group"] is None:
            bad.append((os.path.basename(f), e["id"], "state_group=null"))
print("  null 出现处 =", len(bad))
for b in bad[:10]:
    print("    ", b)

# ── 生成物是否保持源顺序（平票规则依赖声明序）──────────────────────
hdr("C8 补充：ui_layout.js 的元素顺序是否 == 源 JSON 顺序（平票=后来者胜，依赖此序）")
import re
jsf = os.open(os.path.join(UI, "复刻", "ui_layout.js"), os.O_RDONLY); os.close(jsf)
js = io.open(os.path.join(UI, "复刻", "ui_layout.js"), encoding="utf-8").read()
# 直接比对屏幕级 id 序列
def ids_from_src(screen):
    p = os.path.join(UI, "layout", "screens", screen)
    d = json.load(io.open(p, encoding="utf-8"))
    return [e.get("id") for e in (d.get("elements") or [])]
start = js.find('"screens"')
seg = js[start:]
for screen in ("01_title.json", "25_config.json", "36_choices.json"):
    src_ids = ids_from_src(screen)
    # 取该屏在 js 中的片段：用 "id": "<first>" 到下一个屏
    i = seg.find('"%s"' % src_ids[0])
    j = seg.find('"__end_screen"')
    print("  %s：源 %d 个 id，首=%s" % (screen, len(src_ids), src_ids[0]))
