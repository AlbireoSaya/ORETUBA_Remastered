from lucifen_inline_vm_reference import record_value
from r_dynamic_item_reference import write_record_item

_U32 = 0xFFFFFFFF


def run_record(record, base, params, rd, wr, eval_expr, var_map):
    c = record_value(record["condition"], base, rd, eval_expr, var_map) & _U32
    if record["opcode"] == 0:
        c = int(c == 0)
    if c == 0:
        return {"accepted": False, "condition_value": 0,
                "parameter_count": 0, "parameter_end": params}
    items = record["items"]
    for i, item in enumerate(items):
        write_record_item(item, base, (params + 8 * i) & _U32,
                          rd, wr, eval_expr, var_map)
    return {"accepted": True, "condition_value": c,
            "parameter_count": len(items),
            "parameter_end": (params + 8 * len(items)) & _U32}
