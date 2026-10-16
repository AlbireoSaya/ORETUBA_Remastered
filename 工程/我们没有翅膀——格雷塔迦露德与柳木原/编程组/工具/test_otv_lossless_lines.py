import base64
import unittest

from otv_lossless_lines import scan_lines


def raw_of(rec):
    return base64.b64decode(rec["raw_b64"])


def joined_raw(recs):
    return b"".join(raw_of(r) for r in recs)


class ScanLinesTest(unittest.TestCase):

    def test_cp932_mixed_newlines_byte_offsets(self):
        text = "名前=太郎\r\n次=花子\n三=桜\r四=雪"  # 混合换行且无末尾换行
        data = text.encode("cp932")
        recs = scan_lines(data)
        self.assertTrue(recs)
        self.assertEqual(joined_raw(recs), data)
        self.assertEqual(recs[0]["start"], 0)
        for rec in recs:
            self.assertEqual(rec["end"] - rec["start"], len(raw_of(rec)))
        for prev, cur in zip(recs, recs[1:]):
            self.assertEqual(cur["start"], prev["end"])
        self.assertEqual(recs[-1]["end"], len(data))
        self.assertNotEqual(recs[-1]["end"], len(text))  # 非 Unicode 字符偏移

    def test_quoted_value_keeps_markers(self):
        data = '  :caption "//{path:[Task]:v1}"  '.encode("cp932")
        recs = scan_lines(data)
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["kind"], "property")
        self.assertEqual(rec["key"], "caption")
        self.assertEqual(rec["value_raw"], '"//{path:[Task]:v1}"  ')
        for marker in ("//", "{", "[Task]", ":"):
            self.assertIn(marker, rec["value_raw"])
        self.assertEqual(joined_raw(recs), data)

    def test_unknown_syntax_is_opaque_and_preserved(self):
        data = "*** ??? 未知の構文 @@".encode("cp932")
        recs = scan_lines(data)
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["kind"], "opaque")
        self.assertEqual(raw_of(rec), data)
        self.assertEqual((rec["start"], rec["end"]), (0, len(data)))

    def test_empty_and_invalid_cp932(self):
        self.assertEqual(scan_lines(b""), [])
        recs = scan_lines(b"\x81")
        self.assertEqual(len(recs), 1)  # 不吞行
        rec = recs[0]
        self.assertEqual(raw_of(rec), b"\x81")  # 字节保全
        err = str(rec.get("error", "")) + str(rec["kind"])
        self.assertIn("decode", err.lower())


if __name__ == "__main__":
    unittest.main()