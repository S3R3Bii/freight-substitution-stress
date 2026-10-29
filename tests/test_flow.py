import itertools, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from model import maximum_flow, greedy_flow, graph
from fractions import Fraction


class FlowFixtures(unittest.TestCase):
    def check(self, caps, expected):
        value, flows, cut = maximum_flow(caps)
        self.assertEqual(value, expected)
        nodes = sorted({v for edge in caps for v in edge} - {"S", "T"})
        cuts = []
        for bits in itertools.product([False, True], repeat=len(nodes)):
            left = {"S"} | {v for v, b in zip(nodes, bits) if b}
            cuts.append(
                sum(c for (u, v), c in caps.items() if u in left and v not in left)
            )
        self.assertEqual(value, min(cuts))
        self.assertEqual(
            value, sum(c for (u, v), c in caps.items() if u in cut and v not in cut)
        )
        balance = {v: 0 for edge in caps for v in edge}
        for u, v, q in flows:
            self.assertGreater(q, 0)
            self.assertLessEqual(q, caps[u, v])
            balance[u] -= q
            balance[v] += q
        self.assertEqual(balance.get("S", 0), -value)
        self.assertEqual(balance.get("T", 0), value)
        self.assertTrue(all(q == 0 for v, q in balance.items() if v not in ["S", "T"]))

    def test_single(self):
        self.check({("S", "a"): 7, ("a", "T"): 3}, 3)

    def test_disconnected(self):
        self.check({("S", "a"): 7, ("b", "T"): 3}, 0)

    def test_zero(self):
        self.check({("S", "a"): 0, ("a", "T"): 4}, 0)

    def test_parallel_paths(self):
        self.check({("S", "a"): 4, ("S", "b"): 3, ("a", "T"): 5, ("b", "T"): 6}, 7)

    def test_shared_bottleneck(self):
        self.check(
            {("S", "a"): 8, ("a", "b"): 3, ("a", "c"): 4, ("b", "T"): 9, ("c", "T"): 9},
            7,
        )

    def test_reverse_reallocation(self):
        self.check(
            {
                ("S", "a"): 1,
                ("S", "b"): 1,
                ("a", "c"): 1,
                ("a", "d"): 1,
                ("b", "c"): 1,
                ("c", "T"): 1,
                ("d", "T"): 1,
            },
            2,
        )

    def test_large_integer(self):
        self.check({("S", "a"): 10**25 + 3, ("a", "T"): 10**25 + 1}, 10**25 + 1)

    def test_empty(self):
        self.check({}, 0)

    def test_fraction_scaling(self):
        caps, scale, demand = graph(
            {(801, 6, 1): Fraction("0.125"), (801, 48, 1): Fraction("0.25")},
            6,
            Fraction(1, 4),
            Fraction(1),
            "strict",
        )
        value, _, _ = maximum_flow(caps)
        self.assertEqual(Fraction(value, scale), Fraction(1, 16))

    def test_support_expansion(self):
        f = {
            (801, 6, 1): Fraction(5),
            (801, 48, 2): Fraction(10),
            (802, 48, 1): Fraction(10),
        }
        a, s, d = graph(f, 6, Fraction(1), Fraction(1), "strict")
        b, t, e = graph(f, 6, Fraction(1), Fraction(1), "pooled")
        self.assertEqual(maximum_flow(a)[0], 0)
        self.assertEqual(Fraction(maximum_flow(b)[0], t), 5)

    def test_greedy_can_lose(self):
        f = {
            (801, 6, 1): Fraction(1),
            (801, 6, 2): Fraction(1),
            (801, 2, 1): Fraction(1),
            (801, 2, 2): Fraction(1),
            (801, 4, 1): Fraction(1),
        }
        caps, scale, d = graph(f, 6, Fraction(1, 2), Fraction(1), "strict")
        self.assertLess(greedy_flow(caps, d)[0], maximum_flow(caps)[0])

    def test_origin_constraints(self):
        f = {
            (801, 6, 1): Fraction(9),
            (801, 48, 2): Fraction(1),
            (802, 48, 1): Fraction(20),
        }
        caps, scale, d = graph(f, 6, Fraction(1), Fraction(1), "pooled")
        self.assertEqual(Fraction(maximum_flow(caps)[0], scale), 1)


if __name__ == "__main__":
    unittest.main()
