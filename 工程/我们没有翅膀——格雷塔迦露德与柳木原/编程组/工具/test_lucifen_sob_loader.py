import unittest, struct
from lucifen_sob_loader import relocate_buffer, parse_sob1, bind_sob1

def G(o, k):
    return o[k] if isinstance(o, dict) else getattr(o, k)

class SobTests(unittest.TestCase):
    def test_relocate(self):
        m = [dict() for _ in range(6)]
        m[4] = {17: 3}
        buf = b'X' * 32
        out, _ = relocate_buffer(buf, m, 16, 0x1000, 0, [[], [], []])
        self.assertEqual(out[17:21], struct.pack('<I', 0x1003))
        self.assertEqual(buf, b'X' * 32)

    def test_bad_args(self):
        buf, vectors = b"X" * 32, [[], [], []]
        maps6 = [{}, {}, {}, {}, {}, {}]
        for maps, base, funcbase in (
            ([{}, {}, {}, {}, {1: 0}, {}], 0x1000, 0),
            (maps6, True, 0),
            (maps6, 0x1000, -1),
        ):
            with self.subTest(base=base, funcbase=funcbase), self.assertRaises(ValueError):
                relocate_buffer(buf, maps, 16, base, funcbase, vectors)

    def sob(self):
        b = b'SOB1' + struct.pack('<I', 8) + b'\0' * 8 + struct.pack('<I', 2)
        b += struct.pack('<BBII', 255, 3, 0, 0x11223344)
        b += struct.pack('<BBII', 1, 2, 4, 4)
        return b + struct.pack('<I', 1) + struct.pack('<II', 0, 4) + struct.pack('<I', 0)

    def test_parse_bind(self):
        r = parse_sob1(self.sob())
        self.assertEqual(len(r['records']), 2)
        rec = r['records'][0]
        self.assertEqual((rec['type'], rec['flags'], rec['extra']), (255, 3, 0x11223344))
        b = bind_sob1(r, 0x1000, 0x2000)
        self.assertEqual(b['data'][:4], struct.pack('<I', 0x1004))
        self.assertEqual(b['variable_addresses'], [0x1000, 0x2000])
        self.assertEqual(b['array_slots'], [0x1004])

    def test_bad_sob(self):
        muts = [('trunc', lambda x: x[:-1]),
                ('reserved', lambda x: x[:-4] + struct.pack('<I', 1)),
                ('extra', lambda x: x + b'X')]
        for name, mut in muts:
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    parse_sob1(mut(self.sob()))

if __name__ == '__main__':
    unittest.main()
