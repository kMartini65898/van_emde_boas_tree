import unittest

from van_emde_boas_tree import VEBTree


class TestConstruction(unittest.TestCase):
    def test_rejects_non_power_of_two(self):
        with self.assertRaises(ValueError):
            VEBTree(3)
        with self.assertRaises(ValueError):
            VEBTree(6)

    def test_rejects_below_two(self):
        with self.assertRaises(ValueError):
            VEBTree(1)
        with self.assertRaises(ValueError):
            VEBTree(0)

    def test_empty_fresh_tree(self):
        t = VEBTree(16)
        self.assertIsNone(t.find_next(0))
        self.assertIsNone(t.find_prev(15))
        self.assertEqual(len(t), 0)
        self.assertNotIn(0, t)
        self.assertEqual(list(t), [])


class TestBaseCase(unittest.TestCase):
    """u == 2 is the recursion floor and gets its own coverage."""

    def test_insert_both(self):
        t = VEBTree(2)
        t.insert(0)
        t.insert(1)
        self.assertIn(0, t)
        self.assertIn(1, t)
        self.assertEqual(len(t), 2)

    def test_insert_idempotent(self):
        t = VEBTree(2)
        t.insert(0)
        t.insert(0)
        self.assertEqual(len(t), 1)

    def test_delete_to_empty(self):
        t = VEBTree(2)
        t.insert(0)
        t.insert(1)
        t.delete(0)
        self.assertNotIn(0, t)
        self.assertIn(1, t)
        self.assertEqual(len(t), 1)
        t.delete(1)
        self.assertEqual(len(t), 0)

    def test_delete_absent_no_op(self):
        t = VEBTree(2)
        t.insert(0)
        t.delete(1)  # not present, must not raise
        self.assertIn(0, t)
        self.assertEqual(len(t), 1)


class TestBasicOps(unittest.TestCase):
    def test_insert_and_contains(self):
        t = VEBTree(16)
        for k in (0, 5, 15, 8, 3):
            t.insert(k)
        for k in (0, 5, 15, 8, 3):
            self.assertIn(k, t)
        for k in (1, 2, 4, 6, 7, 9, 10, 11, 12, 13, 14):
            self.assertNotIn(k, t)

    def test_rejects_out_of_range(self):
        t = VEBTree(16)
        with self.assertRaises(ValueError):
            t.insert(16)
        with self.assertRaises(ValueError):
            t.insert(-1)
        with self.assertRaises(ValueError):
            t.delete(16)
        # find_next/find_prev clamp out-of-range args per the README.
        self.assertIsNone(t.find_next(16))
        self.assertIsNone(t.find_prev(-1))

    def test_rejects_non_int(self):
        t = VEBTree(16)
        with self.assertRaises(TypeError):
            t.insert("x")
        self.assertNotIn("x", t)
        self.assertFalse(0.5 in t)
        self.assertFalse(True in t)  # bool must not masquerade as int 1


class TestPredecessorSuccessor(unittest.TestCase):
    def test_next_and_prev_boundaries(self):
        t = VEBTree(16)
        for k in (2, 7, 9, 15):
            t.insert(k)
        self.assertEqual(t.find_next(0), 2)
        self.assertEqual(t.find_next(2), 2)
        self.assertEqual(t.find_next(3), 7)
        self.assertEqual(t.find_next(7), 7)
        self.assertEqual(t.find_next(8), 9)
        self.assertEqual(t.find_next(15), 15)
        self.assertIsNone(t.find_next(16))  # clamped

        self.assertEqual(t.find_prev(16), 15)  # clamped
        self.assertEqual(t.find_prev(15), 15)
        self.assertEqual(t.find_prev(14), 9)
        self.assertEqual(t.find_prev(9), 9)
        self.assertEqual(t.find_prev(8), 7)
        self.assertEqual(t.find_prev(3), 2)
        self.assertEqual(t.find_prev(2), 2)
        self.assertIsNone(t.find_prev(0))

    def test_next_on_empty(self):
        t = VEBTree(8)
        self.assertIsNone(t.find_next(0))
        self.assertIsNone(t.find_next(7))

    def test_prev_on_empty(self):
        t = VEBTree(8)
        self.assertIsNone(t.find_prev(7))
        self.assertIsNone(t.find_prev(0))


class TestDelete(unittest.TestCase):
    def test_delete_promotes_summary(self):
        t = VEBTree(16)
        for k in (1, 4, 9, 14):
            t.insert(k)
        t.delete(4)
        self.assertNotIn(4, t)
        self.assertEqual(t.find_next(4), 9)
        self.assertEqual(t.find_prev(4), 1)
        # min/max still correct after an interior deletion
        self.assertEqual(t.find_prev(15), 14)

    def test_delete_min(self):
        t = VEBTree(16)
        for k in (3, 7, 11):
            t.insert(k)
        t.delete(3)
        self.assertNotIn(3, t)
        self.assertEqual(t.find_next(0), 7)
        self.assertEqual(t.find_prev(7), 7)

    def test_delete_max(self):
        t = VEBTree(16)
        for k in (3, 7, 11):
            t.insert(k)
        t.delete(11)
        self.assertNotIn(11, t)
        self.assertEqual(t.find_next(11), None)
        self.assertEqual(t.find_prev(15), 7)

    def test_delete_last_element(self):
        t = VEBTree(16)
        t.insert(5)
        t.delete(5)
        self.assertEqual(len(t), 0)
        self.assertIsNone(t.find_next(0))
        self.assertIsNone(t.find_prev(15))


class TestIteration(unittest.TestCase):
    def test_iter_sorted(self):
        t = VEBTree(256)
        keys = [0, 1, 2, 128, 200, 255]
        for k in keys:
            t.insert(k)
        self.assertEqual(list(t), sorted(keys))

    def test_iter_after_deletions(self):
        t = VEBTree(256)
        keys = list(range(0, 256, 5))
        for k in keys:
            t.insert(k)
        for k in keys[::2]:
            t.delete(k)
        remaining = sorted(set(keys) - set(keys[::2]))
        self.assertEqual(list(t), remaining)


if __name__ == "__main__":
    unittest.main()
