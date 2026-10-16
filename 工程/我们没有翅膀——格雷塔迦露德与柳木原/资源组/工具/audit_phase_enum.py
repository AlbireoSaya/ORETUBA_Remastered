# -*- coding: utf-8 -*-
r"""
W10b · 六源 `phase` 取值审计 + 枚举负向对照（证明「越界即报错」）

只读六源 `资源组\剧本\scene_*.jsonl`，输出：
  1) 六源全部实际取值表（值 + 条数 + 所属源 + 合计）；
  2) 逐源 `phase_violations()` 结果（应为空）；
  3) **负向对照**：在内存中把某场景 `phase` 改成 `"转折"`（不在八值域内），
     确认 `phase_violations()` 能捕获 → 证明校验器不是「放宽为不校验」。
只写 `子代理工作区\ISSUE-20260918-06\W10b\phase审计.json`，不改任何产物。

复跑：python "工程/我们没有翅膀——格雷塔迦露德与柳木原/资源组/工具/audit_phase_enum.py"
"""
import json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _schema_enums import PHASE_ALLOWED, phase_ok, phase_violations

ROOT = r"E:\ZCode Workspace\Galgame"
PRJ  = os.path.join(ROOT, r"工程\我们没有翅膀——格雷塔迦露德与柳木原")
OUT  = os.path.join(PRJ, r"资源组", "剧本")
STG  = os.path.join(ROOT, r"子代理工作区\ISSUE-20260918-06\W10b")

FILES = ["scene_ot.jsonl", "scene_otr.jsonl", "scene_ota.jsonl",
         "scene_otp.jsonl", "scene_otv.jsonl", "scene_np.jsonl"]
ORDER = ["序", "个人线", "结局", "真相", "主线", "框架", "系统", None]


def main():
    per_source, total, scenes_all = {}, collections.Counter(), {}
    viol = {}
    for fn in FILES:
        src = fn[len("scene_"):-len(".jsonl")]
        objs = [json.loads(l) for l in open(os.path.join(OUT, fn), encoding="utf-8")]
        scenes_all[src] = objs
        c = collections.Counter(o["phase"] for o in objs)
        per_source[src] = {str(k): v for k, v in c.items()}
        total.update(c)
        viol[src] = phase_violations(objs)

    # 负向对照：内存注入越界值
    probe = dict(scenes_all["otv"][0])
    probe["phase"] = "转折"
    probe_viol = phase_violations([probe])
    neg_ok = probe_viol == [(probe.get("scene_id"), "转折")]

    # 另一负向对照：把 ota 的 null 改成未登记值 "番外"
    probe2 = dict(scenes_all["ota"][0])
    probe2["phase"] = "番外"
    probe2_viol = phase_violations([probe2])
    neg2_ok = len(probe2_viol) == 1

    # 静态核对：六个校验器都 import 了共享值域模块（证明「统一校验」而非各自硬编码/不校验）
    tools = os.path.dirname(os.path.abspath(__file__))
    verifiers = ["verify_scene_jsonl.py", "verify_scene_ot.py", "verify_scene_ota.py",
                 "verify_scene_otp.py", "verify_scene_otv.py", "verify_scene_np.py"]
    vcheck = {}
    for v in verifiers:
        txt = open(os.path.join(tools, v), encoding="utf-8").read()
        vcheck[v] = {"imports_shared_enum": "from _schema_enums import" in txt,
                     "calls_phase_check": ("phase_violations(" in txt or "phase_ok(" in txt)}

    rep = {
        "phase_allowed": [str(v) for v in PHASE_ALLOWED],
        "verifier_wiring": vcheck,
        "verifier_wiring_ok": all(x["imports_shared_enum"] and x["calls_phase_check"]
                                  for x in vcheck.values()),
        "per_source": per_source,
        "total": {str(k): v for k, v in total.items()},
        "grand_total": sum(total.values()),
        "violations_per_source": viol,
        "all_in_enum": all(not v for v in viol.values()),
        "negative_control": {
            "inject_otv_phase_转折": probe_viol,
            "caught": neg_ok,
            "inject_ota_phase_番外": probe2_viol,
            "caught_2": neg2_ok,
        },
        "negative_control_pass": neg_ok and neg2_ok,
    }
    os.makedirs(STG, exist_ok=True)
    json.dump(rep, open(os.path.join(STG, "phase审计.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 控制台表（`None` 显示为 `null`）
    cols = [("null" if v is None else v) for v in ORDER]
    keys = [str(v) for v in ORDER]
    print("源".ljust(10), "".join(c.rjust(7) for c in cols), "  合计")
    for src in ["ot", "otr", "ota", "otp", "otv", "np"]:
        row = per_source[src]
        print(src.ljust(10), "".join(str(row.get(k, 0)).rjust(7) for k in keys),
              "%6d" % sum(row.values()))
    tot_s = {str(k): v for k, v in total.items()}
    print("合计".ljust(10), "".join(str(tot_s.get(k, 0)).rjust(7) for k in keys),
          "%6d" % sum(total.values()))
    print("")
    print("值域         :", [str(v) for v in PHASE_ALLOWED])
    print("六源越界条数 :", {k: len(v) for k, v in viol.items()})
    print("全部合规     :", rep["all_in_enum"])
    print("负向对照     : 注入 otv.phase='转折' → 捕获", neg_ok,
          "｜注入 ota.phase='番外' → 捕获", neg2_ok)
    print("校验器接线   :", rep["verifier_wiring_ok"],
          {k: (v["imports_shared_enum"], v["calls_phase_check"]) for k, v in vcheck.items()})
    print("->", os.path.join(STG, "phase审计.json"))


if __name__ == "__main__":
    main()