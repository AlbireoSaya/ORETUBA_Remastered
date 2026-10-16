# -*- coding: utf-8 -*-
"""反向验证：证明三道守门/自测「真的会失败」。
只读被审代码（import 而不修改），临时数据全部落在本目录下。"""
import io, os, json, sys, shutil, importlib.util, copy

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
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)

# ─────────────────────────────────────────────── C7 反向：iter_asset_refs / [1] 缺件
hdr("C7 反向：verify_ui.check_asset_refs 能否报出 state_assets 里的缺失引用")
vu = load_mod("vu", os.path.join(TOOLS, "verify_ui.py"))
tmp = os.path.join(HERE, "rev_ui", "layout")
os.makedirs(os.path.join(tmp, "screens"), exist_ok=True)
fake = {"id": "s1", "elements": [
    {"id": "ok.a", "kind": "image", "asset": "ui/x_ui_check_off.png",
     "state_assets": {"normal": "ui/x_ui_check_off.png", "hover": "ui/__NOT_EXIST_HOVER__.png"}},
    {"id": "bad.b", "kind": "hit", "state_assets": "ui/__NOT_DICT___.png"},
    {"id": "bad.c", "kind": "image", "state_assets": {"focus": "ui/__FOURTH_STATE__.png"}},
]}
io.open(os.path.join(tmp, "screens", "99_fake.json"), "w", encoding="utf-8").write(
    json.dumps(fake, ensure_ascii=False, indent=2))
errs = vu.check_asset_refs(tmp, os.path.join(UI, "krkr", "assets", "ui"), False)
print("  → 报错条数 =", len(errs), "（期望 3：hover 缺件 / 非字典 / 第四态 focus）")
for e in errs:
    print("     !!", e[:150])

# ─────────────────────────────────────────────── C8 反向：test_state_targets 能否失败
hdr("C8 反向 a：test_state_targets 遇到「高 z 异组遮挡」是否报不可达")
tst = load_mod("tst", os.path.join(TOOLS, "test_state_targets.py"))
tmp2 = os.path.join(HERE, "rev_targets")
if os.path.isdir(tmp2): shutil.rmtree(tmp2)
os.makedirs(os.path.join(tmp2, "screens"))
src = json.load(io.open(os.path.join(UI, "layout", "screens", "01_title.json"), encoding="utf-8"))
mod = copy.deepcopy(src)
mod["elements"].append({"id": "zzz.blocker", "kind": "hit", "z": 999,
                        "x": 140, "y": 360, "w": 252, "h": 96, "state_group": "zzz.other"})
io.open(os.path.join(tmp2, "screens", "01_title.json"), "w", encoding="utf-8").write(
    json.dumps(mod, ensure_ascii=False))
tst.SCREENS = os.path.join(tmp2, "screens")
rc = tst.main()
print("  → 退出码 =", rc, "（期望 1）")

hdr("C8 反向 b：把判据换回「收紧前的宽松版」，本守门是否还能发现 Major-1 那类回归")
loose = lambda e: (e.get("state_assets") is not None) or (e.get("kind") == "hit")
tst2 = load_mod("tst2", os.path.join(TOOLS, "test_state_targets.py"))
tst2.is_candidate = loose           # 只改模块内全局，不动文件
rc2 = tst2.main()
print("  → 退出码 =", rc2, "（0 = 守门对「判据放宽」**无感**）")

# ─────────────────────────────────────────────── C9-A 反向：调色板按 id 配对
hdr("C9-A 反向：restore_palette_refs 是否按 id 配对（而非下标）")
vee = load_mod("vee", os.path.join(TOOLS, "verify_editor_export.py"))
pal = {"text_small": "#AAAACC", "shadow": "#000000"}
olde = {"elements": [{"id": "A", "font": {"color": "@palette.text_small"}},
                     {"id": "B", "font": {"color": "@palette.shadow"}}]}
newe = {"elements": [{"id": "B", "font": {"color": "#000000"}},
                     {"id": "A", "font": {"color": "#AAAACC"}}]}   # 顺序颠倒
rep = []
vee.restore_palette_refs(newe, olde, pal, rep, "T")
print("  还原条数 =", len(rep), "（期望 2 —— 按下标只会错配/漏配）")
print("  还原后 =", json.dumps(newe, ensure_ascii=False))

print("\n  对照：把 old 的 elements 去掉 id（退化为下标配对）")
olde2 = {"elements": [{"font": {"color": "@palette.text_small"}},
                      {"font": {"color": "@palette.shadow"}}]}
newe2 = {"elements": [{"id": "B", "font": {"color": "#000000"}},
                      {"id": "A", "font": {"color": "#AAAACC"}}]}
rep2 = []
vee.restore_palette_refs(newe2, olde2, pal, rep2, "T")
print("  还原条数 =", len(rep2), " 结果 =", json.dumps(newe2, ensure_ascii=False))
