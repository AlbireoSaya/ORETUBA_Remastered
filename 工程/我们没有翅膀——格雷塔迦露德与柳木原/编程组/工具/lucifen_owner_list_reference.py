def owner_reorder_reference(order, key_by_child, child, new_key,
                            skip_same_word=0, after_equals=False):
    """Fixture-only reference for the original owner-list reorder (entry 0x459890
    before-equal / 0x4599A0 after-equal, ret 0xC).  This is NOT the engine, the
    original allocator, or the original node lifecycle: `order` stands in for the
    owner's chained nodes (head+4 / tail+8) as a list of child ids sorted by u32
    key with unique children, and `key_by_child` stands in for the node key at
    +0x14.  Comparison is unsigned 32-bit.

    Inputs are never mutated (order and keys are copied).  Returns a dict with:
    order (new list), keys (new dict), al (0/1), changed (bool).
    al=0 with no change when child is NULL(0) or is absent from order.
    When (skip_same_word & 0xff) is nonzero and the normalized old key equals the
    normalized new key: al=1, changed=False, nothing moves.  Otherwise the child
    is unlinked, its key is set to new_key & 0xffffffff (other keys keep their
    values), and it is relinked before the first existing key >= new_key
    (after_equals=False) or > new_key (after_equals=True), else at the tail;
    al=1 and changed=True even if the resulting order equals the original, since
    the original truly unlinked/relinked and set the child mark byte+9=1.
    Missing keys raise as bad fixtures only for already-existing children, while non-member missing keys still return AL0.
    """
    if child == 0:  # NULL child: no change
        return {"order": list(order), "keys": dict(key_by_child),
                "al": 0, "changed": False}
    if child not in order:
        return {"order": list(order), "keys": dict(key_by_child),
                "al": 0, "changed": False}
    if child not in key_by_child:
        raise ValueError("invalid fixture: child not in key_by_child")

    keys = dict(key_by_child)
    old_key = keys[child] & 0xFFFFFFFF
    new_key = new_key & 0xFFFFFFFF

    if (skip_same_word & 0xFF) and old_key == new_key:
        return {"order": list(order), "keys": keys, "al": 1, "changed": False}

    order = list(order)
    order.remove(child)          # unlink selected node
    keys[child] = new_key        # update only the selected child's key
    for i, other in enumerate(order):
        k = keys[other] & 0xFFFFFFFF
        if k > new_key or (k == new_key and not after_equals):
            order.insert(i, child)
            break
    else:
        order.append(child)
    return {"order": order, "keys": keys, "al": 1, "changed": True}
