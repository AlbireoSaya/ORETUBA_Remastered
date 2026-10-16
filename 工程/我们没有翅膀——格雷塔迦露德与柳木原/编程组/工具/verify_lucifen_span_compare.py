import json, hashlib
from lucifen_verify_bgrx_spans import compare_bgrx_spans

def main():
    e = bytes(8)
    a = bytearray([7, 0, 0, 99, 0, 0, 0, 99])

    r = compare_bgrx_spans(e, a, 2, 1, [(0, 0, 2)])
    assert r['matches'] is False
    assert r['differing_pixels'] == 1
    assert r['differing_color_bytes'] == 1
    assert r['compared_pixels'] == 2

    r = compare_bgrx_spans(e, a, 2, 1, [(0, 1, 2)])
    assert r['matches'] is True
    assert r['compared_pixels'] == 1

    r = compare_bgrx_spans(e, a, 2, 1, [])
    assert r['compared_pixels'] == 0
    assert r['expected_RGB_SHA256'] == hashlib.sha256(b'').hexdigest()
    assert r['actual_RGB_SHA256'] == hashlib.sha256(b'').hexdigest()

    for args in [
        (bytes(7), a, 2, 1, [(0, 0, 2)]),
        (e, a, True, 1, [(0, 0, 2)]),
        (e, a, 2, 1, [(0, 0, 2), (0, 1, 2)]),
    ]:
        try:
            compare_bgrx_spans(*args)
            raise AssertionError('expected ValueError')
        except ValueError:
            pass

    print(json.dumps({'passed': True}))

if __name__ == '__main__':
    main()
