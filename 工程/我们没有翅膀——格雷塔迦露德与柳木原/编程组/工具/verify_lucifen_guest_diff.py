import copy
import json
from lucifen_guest_u32_diff import diff_u32

def _snap(words, byte_count=12, base=0x1000):
    return {"base": base, "byte_count": byte_count, "words": words, "sha256": "0" * 64}

def _raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False

def main():
    before = _snap([0, 1, 2])
    after = _snap([4, 1, 6])
    before_copy = copy.deepcopy(before)
    after_copy = copy.deepcopy(after)
    d = diff_u32(before, after, max_changes=1)
    assert before == before_copy and after == after_copy
    assert d["total_changed_words"] == 2 and d["truncated"] is True
    c = d["changes"][0]
    assert (c["offset"], c["va"], c["before"], c["after"], c["xor"]) == (0, 0x1000, 0, 4, 4)
    z = diff_u32(before, before)
    assert z["total_changed_words"] == 0 and z["truncated"] is False and z["changes"] == []
    assert _raises(lambda: diff_u32(before, after, max_changes=0))
    assert _raises(lambda: diff_u32(before, after, max_changes=True))
    bad_len = copy.deepcopy(before)
    bad_len["words"] = [0, 1]
    assert _raises(lambda: diff_u32(bad_len, bad_len))
    bad_bc = copy.deepcopy(before)
    bad_bc["byte_count"] = 8
    bad_bc["words"] = [0, 1]
    assert _raises(lambda: diff_u32(before, bad_bc))
    print(json.dumps({"passed": True}, separators=(",", ":")))

if __name__ == "__main__":
    main()