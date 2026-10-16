import json
from lucifen_guest_script_prefix_scan import scan_script_prefixes

DATA = {1000: b"TOB0", 3000: b"XXXX", 4000: b"SOB2"}

def _reader(calls):
    def read(base, n):
        calls.append((base, n))
        assert base != 2000
        assert n == 4
        return DATA[base]
    return read

def test_positive():
    regions = [(1000, 4), (2000, 3), (3000, 8), (4000, 4)]
    original = list(regions)
    calls = []
    result = scan_script_prefixes(_reader(calls), regions)
    assert calls == [(1000, 4), (3000, 4), (4000, 4)]
    assert regions == original
    assert result["total_regions"] == 4
    assert result["scanned_regions"] == 3
    assert result["skipped_small"] == 1
    assert result["matches"] == [
        {"base": 1000, "registered_size": 4, "magic": "TOB0"},
        {"base": 4000, "registered_size": 4, "magic": "SOB2"},
    ]

def test_negative_max_regions():
    regions = [(1000, 4), (2000, 3), (3000, 8), (4000, 4)]
    calls = []
    try:
        scan_script_prefixes(_reader(calls), regions, max_regions=1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    assert calls == []

def main():
    test_positive()
    test_negative_max_regions()
    print(json.dumps({"passed": True}))

if __name__ == "__main__":
    main()