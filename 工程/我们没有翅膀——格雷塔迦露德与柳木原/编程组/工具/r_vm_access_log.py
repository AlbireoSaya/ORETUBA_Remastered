U32 = 0xFFFFFFFF


def _u32(x):
    return x & U32


class AccessLog:
    def __init__(self, rd, wr, rb, wb, initial_word, current_word):
        self._rd = rd
        self._wr = wr
        self._rb = rb
        self._wb = wb
        self._initial_word = initial_word
        self._current_word = current_word
        self.initial = {}
        self.writes = []

    def _remember(self, a, n):
        a = _u32(a)
        for q in range(a & ~3, (a + n + 3) & ~3, 4):
            if q not in self.initial:
                self.initial[q] = self._initial_word(q)

    def rd(self, a):
        v = self._rd(a)
        self._remember(a, 4)
        return v

    def rb(self, a):
        v = self._rb(a)
        self._remember(a, 1)
        return v

    def wr(self, a, v):
        self._wr(a, v)
        self._remember(a, 4)
        self.writes.append([4, _u32(a), _u32(v)])

    def wb(self, a, v):
        self._wb(a, v)
        self._remember(a, 1)
        self.writes.append([1, _u32(a), _u32(v) & 0xff])

    def initial_pairs(self):
        return [[q, self.initial[q]] for q in sorted(self.initial)]

    def final_pairs(self):
        return [[q, self._current_word(q)] for q in sorted(self.initial)]