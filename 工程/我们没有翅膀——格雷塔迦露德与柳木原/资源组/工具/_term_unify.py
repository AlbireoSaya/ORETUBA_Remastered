# -*- coding: utf-8 -*-
r"""`_term_unify.py` — `fix_type=term_unify` 的**唯一**消费实现（ISSUE-20260930-12）

六个语料构建器（`build_scene_{ot,otp,ota,otv,np,jsonl}.py`）共用本模块，保证**语义只有一处实现**。
配套硬闸门：`verify_schema_enums.py`（枚举）＋ 生成器 `build_rulings_fixtable.py` G0b（正则必须可编译）
＋ 负向自证 `selftest_term_unify.py`（本模块的三个分支必须都能真的走到，且子串陷阱不得自爆）。

规则（**`old_text` / `new_text` 的语义按 `fix_type` 分叉**，见 `修正\_README.md` §三.3）：

| `fix_type` | `old_text` | `new_text` | 消费方式 |
| --- | --- | --- | --- |
| `term_unify`（**本模块**） | 被替换**词形**（正则） | **替换值**（不是整句） | `re.sub` 词形替换 |
| 其余（`retranslate` / `quote_add` / …） | 该槽**整句**（逐字符等于基准层） | 该槽**整句**修正后文本 | 整槽覆盖 `cn` |

    命中 old_text      → re.sub 替换（只碰术语那几个字，其余字保持当前值）      → "applied"
    未命中，但已是后态  → 幂等 no-op（本表在本槽已生效过）                      → "noop"
    两者都不是         → fail loud（locator 漂移 / 词形已变 / 表与语料脱节）      → SystemExit

**为什么是正则而不是裸 `str.replace`**：实测 3 个变体是采用值的**子串**——`空学`／`空学院`／`美空学` ⊆
`美空学院`，裸替换会自爆（`美空学院` → `美美空学院院`）。「空学族」因此必须带上下文守卫
（`(?<!美)空学(?!院|府|园)` 等）。全部 16 个变体均不含正则元字符，故其余 95 行以正则可读性无损失。

**为什么不再需要整句基准层**：旧语义下消费方 `cn = new_text`（整槽覆盖），该槽**别的字**会被一并写回旧句——
上游一旦润色/重译，这条行会**静默把改进顶回去**，只能靠「`old_text` 逐字符等于基准层」把它转成 fail loud。
词形级替换只碰术语那几个字，**其余字永远是当前值** ⇒ 不再依赖整句基准层、也不再依赖本项目之外的
`工程\我们没有翅膀\汉化\剧情汉化\`。

**`noop` 的已知边界（如实登记，不要当成独立检错器）**：判据是「本槽文本已含采用值且不含变体」。
采用值越短（如 `隼` 只有 1 字），`noop` 越容易被无关文本误触发 ⇒ **它不是 locator 漂移的检出器**，
漂移由生成器 G6（独立消费键定位 ＋ JP 门控 ＋ 基准句命中）承担。故消费方命中 `noop` 时**必须留痕**
（`TERM_NOOP` 计入构建统计并打印），不得静默。
"""
from __future__ import annotations

import re

APPLIED = "applied"
NOOP = "noop"
U3000 = "\u3000"        # 全角空格：otr 的构建器 ②.5 在套修正表之后统一删除（见 verify 的 ignore_u3000）


def apply(cn, old_text, new_text):
    """把 `old_text`（词形正则）在 `cn` 中替换为 `new_text`。

    返回 `(新 cn, 状态)`，状态 ∈ `{"applied", "noop"}`；两个分支都不成立则 fail loud（抛 `SystemExit`）。
    调用方**必须**处理 `"noop"`：不得记 `fix_refs`、不得计命中（它是「本表已生效过」的幂等路径）。
    """
    cn = cn or ""
    if re.search(old_text, cn):
        return re.sub(old_text, new_text, cn), APPLIED
    if new_text and new_text in cn:
        return cn, NOOP
    raise SystemExit(
        "!! term_unify 词形未命中且文本非后态（locator 疑漂移 / 词形已变 / 表与语料脱节）：\n"
        "  old_text=%r\n  new_text=%r\n  cn=%r" % (old_text, new_text, cn))


def verify(cn_before, cn_after, old_text, new_text, later_layers_touched=False,
           ignore_u3000=False):
    """**校验器专用**：给定「修正前文本 / 修正后文本 / 本行 old_text、new_text」，判定本行是否真的生效。

    判据（`later_layers_touched=True` 表示该槽其后又过了别的层，如 ③ 译名替换，
    此时 `cn_after` 允许不等于纯 `re.sub` 结果）：

        ① `cn_before` 必须命中 `old_text`（否则该槽不是本行的目标槽 ⇒ locator 漂移）
        ② `cn_after == re.sub(old_text, new_text, cn_before)`，或 `later_layers_touched=True`

    `ignore_u3000=True`（ISSUE-20260930-12 补）：比对前把两侧的 **U+3000（全角空格）** 去掉。
    必要性：`build_scene_jsonl.py`（otr）的 ②.5 在**套修正表之后**调用 `_strip_u3000`，而该函数是
    `s.replace(U3000, "")` —— 删的是**全部** U+3000（不只前导；实测 otr 全库残留已归零），故豁免也必须是
    无差别删除（实测 otr 46 个 term 槽里 19 个 `cn_before` 因此与纯 `re.sub` 结果对不上）。
    **只豁免 U+3000 这一个字符**，其余字符仍逐字符相等 ⇒ 判据 ② 不会被整体放弃
    （若图省事把这类槽并进 `later_layers_touched`，判据 ② 就退化成只查词形，那才是真的守错层）。

    返回 `(ok: bool, why: str)`。判据与消费方 `_term_unify.apply` 同源但**不共用同一份实现**：
    校验器要的是「**已经落盘的两个值**是否满足关系」，消费方要的是「**该怎么改**」——两者相互独立，
    才可能互证（共用实现会变成自证）。
    """
    a = (cn_before or "").replace(U3000, "") if ignore_u3000 else (cn_before or "")
    b = (cn_after or "").replace(U3000, "") if ignore_u3000 else (cn_after or "")
    if not re.search(old_text, a):
        return False, "cn_before 未命中 old_text（该槽不是本行的目标槽）"
    want = re.sub(old_text, new_text, a)
    if b == want:
        return True, ""
    if later_layers_touched:
        return True, "cn_after 与纯替换结果不同，但该槽其后过了别的层（留痕复核）"
    return False, "cn_after != re.sub(old_text, new_text, cn_before)"
