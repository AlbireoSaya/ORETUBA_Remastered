# -*- coding: utf-8 -*-
"""Strict input-rejection contract verifier for the lucifen window style host bindings.

Targets (imported, never re-implemented here):
    lucifen_host_window_style_query.query_window_style(hwnd, index, source_last_error)
    lucifen_host_window_style_set.set_window_style(hwnd, index, value32, source_last_error)

Scope:
    * invalid-argument rejection only;
    * every case carries exactly one malformed argument while the remaining
      positions carry values inside the host contract, so a conforming
      implementation must raise TypeError / ValueError before it reaches the
      native GetWindowLongPtrA / SetWindowLongPtrA call;
    * no mocking, no stubbing, no cloning of the implementation, no valid
      native call, and no real OS invocation is constructed by this script.

Verdict:
    * TypeError or ValueError raised  => pass;
    * any value returned             => AssertionError;
    * any other exception type       => AssertionError.

Outcome:
    * success -> stdout {"passed": true, "cases": <int>}, exit code 0;
    * failure -> stdout {"passed": false, ...} followed by re-raised
      AssertionError.
"""

import ctypes
import json
import sys

_ACCEPTED_EXCEPTIONS = (TypeError, ValueError)

_PTR_BITS = ctypes.sizeof(ctypes.c_void_p) * 8
if _PTR_BITS not in (32, 64):
    raise AssertionError("unsupported pointer width: %d bits" % (_PTR_BITS,))
_NATIVE_PTR_MAX = (1 << _PTR_BITS) - 1

_VALID_HWND = 1
_VALID_INDEX = -16
_VALID_VALUE32 = 0
_VALID_SOURCE_LAST_ERROR = 0

_BAD_HWND = (True, False, 0, -1, _NATIVE_PTR_MAX + 1)
_BAD_INDEX = (True, False, -21, 0)
_BAD_SOURCE_LAST_ERROR = (True, False, -1, 0x100000000)
_BAD_VALUE32 = (True, False, -1, 0x100000000)

def _load_targets():
    """Import the two bindings under test; report every failure as a contract failure."""
    try:
        from lucifen_host_window_style_query import query_window_style
        from lucifen_host_window_style_set import set_window_style
    except AssertionError:
        raise
    except BaseException as exc:
        raise AssertionError(
            "cannot import target bindings: %s: %s" % (type(exc).__name__, exc)
        )
    for name, candidate in (
        ("lucifen_host_window_style_query.query_window_style", query_window_style),
        ("lucifen_host_window_style_set.set_window_style", set_window_style),
    ):
        if not callable(candidate):
            raise AssertionError("%s is not callable" % (name,))
    return query_window_style, set_window_style

def _build_cases(query_window_style, set_window_style):
    cases = []

    for bad in _BAD_HWND:
        cases.append((
            "query_window_style(hwnd=%r)" % (bad,),
            query_window_style,
            (bad, _VALID_INDEX, _VALID_SOURCE_LAST_ERROR),
        ))
    for bad in _BAD_INDEX:
        cases.append((
            "query_window_style(index=%r)" % (bad,),
            query_window_style,
            (_VALID_HWND, bad, _VALID_SOURCE_LAST_ERROR),
        ))
    for bad in _BAD_SOURCE_LAST_ERROR:
        cases.append((
            "query_window_style(source_last_error=%r)" % (bad,),
            query_window_style,
            (_VALID_HWND, _VALID_INDEX, bad),
        ))

    for bad in _BAD_HWND:
        cases.append((
            "set_window_style(hwnd=%r)" % (bad,),
            set_window_style,
            (bad, _VALID_INDEX, _VALID_VALUE32, _VALID_SOURCE_LAST_ERROR),
        ))
    for bad in _BAD_INDEX:
        cases.append((
            "set_window_style(index=%r)" % (bad,),
            set_window_style,
            (_VALID_HWND, bad, _VALID_VALUE32, _VALID_SOURCE_LAST_ERROR),
        ))
    for bad in _BAD_VALUE32:
        cases.append((
            "set_window_style(value32=%r)" % (bad,),
            set_window_style,
            (_VALID_HWND, _VALID_INDEX, bad, _VALID_SOURCE_LAST_ERROR),
        ))
    for bad in _BAD_SOURCE_LAST_ERROR:
        cases.append((
            "set_window_style(source_last_error=%r)" % (bad,),
            set_window_style,
            (_VALID_HWND, _VALID_INDEX, _VALID_VALUE32, bad),
        ))

    return cases

def _assert_rejects(label, func, args):
    try:
        returned = func(*args)
    except _ACCEPTED_EXCEPTIONS:
        return
    except AssertionError:
        raise
    except BaseException as exc:
        raise AssertionError(
            "%s: expected TypeError or ValueError, got %s: %s"
            % (label, type(exc).__name__, exc)
        )
    raise AssertionError(
        "%s: malformed argument was accepted and returned %r" % (label, returned)
    )

def main():
    cases = []
    try:
        query_window_style, set_window_style = _load_targets()
        cases = _build_cases(query_window_style, set_window_style)
        if not cases:
            raise AssertionError("no rejection cases were constructed")
        for label, func, args in cases:
            _assert_rejects(label, func, args)
    except AssertionError as exc:
        sys.stdout.write(
            json.dumps(
                {"passed": False, "cases": len(cases), "error": str(exc)},
                ensure_ascii=False,
            )
            + "\n"
        )
        sys.stdout.flush()
        raise
    sys.stdout.write(
        json.dumps({"passed": True, "cases": len(cases)}, ensure_ascii=False) + "\n"
    )
    sys.stdout.flush()
    return 0

if __name__ == "__main__":
    sys.exit(main())