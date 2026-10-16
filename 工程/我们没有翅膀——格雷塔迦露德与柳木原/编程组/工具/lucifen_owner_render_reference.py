from lucifen_owner_list_reference import owner_reorder_reference


def render_tail_order(order):
    return list(reversed(order))


def native_owner_reorder_reference(order, keys, child, new_key, truth_word, after_equals=False):
    """Fixture-only. Valid primary object only. No secondary fallback/cast model."""
    result = owner_reorder_reference(
        order,
        keys,
        child,
        new_key,
        1 if (truth_word & 0xffffffff) != 0 else 0,
        after_equals,
    )
    result["render_order"] = render_tail_order(result["order"])
    result["native_return"] = result["al"]
    return result
