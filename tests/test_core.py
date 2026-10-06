import unittest
from datetime import datetime

from time_range_overlap import Range, intersect, union


def dt(text: str) -> datetime:
    return datetime.fromisoformat(text)


class TestRangeConstruction(unittest.TestCase):
    def test_start_after_end_raises(self):
        with self.assertRaises(ValueError):
            Range(dt("2024-01-02T00:00:00"), dt("2024-01-01T00:00:00"))

    def test_start_equal_end_allowed(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T09:00:00"))
        self.assertEqual(r.start, r.end)

    def test_defaults_half_open(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        self.assertTrue(r.start_inclusive)
        self.assertFalse(r.end_inclusive)


class TestRangeIsEmpty(unittest.TestCase):
    def test_half_open_point_is_empty(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T09:00:00"))
        self.assertTrue(r.is_empty())

    def test_open_both_point_is_empty(self):
        r = Range(
            dt("2024-01-01T09:00:00"),
            dt("2024-01-01T09:00:00"),
            start_inclusive=False,
            end_inclusive=False,
        )
        self.assertTrue(r.is_empty())

    def test_closed_point_is_not_empty(self):
        r = Range(
            dt("2024-01-01T09:00:00"),
            dt("2024-01-01T09:00:00"),
            start_inclusive=True,
            end_inclusive=True,
        )
        self.assertFalse(r.is_empty())

    def test_spanning_range_is_not_empty(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        self.assertFalse(r.is_empty())


class TestCoversInstant(unittest.TestCase):
    def test_inside_half_open(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        self.assertTrue(r.covers_instant(dt("2024-01-01T12:00:00")))

    def test_start_boundary_inclusive(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        self.assertTrue(r.covers_instant(dt("2024-01-01T09:00:00")))

    def test_end_boundary_exclusive(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        self.assertFalse(r.covers_instant(dt("2024-01-01T17:00:00")))

    def test_end_boundary_inclusive_when_flag_set(self):
        r = Range(
            dt("2024-01-01T09:00:00"),
            dt("2024-01-01T17:00:00"),
            end_inclusive=True,
        )
        self.assertTrue(r.covers_instant(dt("2024-01-01T17:00:00")))

    def test_before_start(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        self.assertFalse(r.covers_instant(dt("2024-01-01T08:00:00")))


class TestIntersect(unittest.TestCase):
    def test_empty_input_returns_none(self):
        self.assertIsNone(intersect([]))

    def test_single_range_returns_itself(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        result = intersect([r])
        self.assertEqual(result, r)

    def test_two_overlapping_half_open(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        b = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T18:00:00"))
        result = intersect([a, b])
        self.assertEqual(result.start, dt("2024-01-01T10:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T17:00:00"))
        self.assertTrue(result.start_inclusive)
        self.assertFalse(result.end_inclusive)

    def test_disjoint_returns_none(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T10:00:00"))
        b = Range(dt("2024-01-01T11:00:00"), dt("2024-01-01T12:00:00"))
        self.assertIsNone(intersect([a, b]))

    def test_adjacent_half_open_returns_none(self):
        # [09:00, 10:00) and [10:00, 11:00) share 10:00 but neither includes it.
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T10:00:00"))
        b = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T11:00:00"))
        self.assertIsNone(intersect([a, b]))

    def test_adjacent_one_side_inclusive(self):
        # [09:00, 10:00] and [10:00, 11:00) intersect at the single instant 10:00.
        a = Range(
            dt("2024-01-01T09:00:00"),
            dt("2024-01-01T10:00:00"),
            end_inclusive=True,
        )
        b = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T11:00:00"))
        result = intersect([a, b])
        self.assertEqual(result.start, dt("2024-01-01T10:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T10:00:00"))
        self.assertTrue(result.start_inclusive)
        self.assertTrue(result.end_inclusive)

    def test_identical_ranges(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        b = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        result = intersect([a, b])
        self.assertEqual(result, a)

    def test_one_contains_other(self):
        outer = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        inner = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T11:00:00"))
        result = intersect([outer, inner])
        self.assertEqual(result.start, dt("2024-01-01T10:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T11:00:00"))

    def test_three_ranges(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T15:00:00"))
        b = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T14:00:00"))
        c = Range(dt("2024-01-01T11:00:00"), dt("2024-01-01T13:00:00"))
        result = intersect([a, b, c])
        self.assertEqual(result.start, dt("2024-01-01T11:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T13:00:00"))

    def test_empty_range_ignored_when_live_present(self):
        # Empty ranges are dropped up front; they cannot contribute.
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T09:00:00"))
        b = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        result = intersect([a, b])
        self.assertEqual(result.start, dt("2024-01-01T09:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T17:00:00"))

    def test_generator_input(self):
        def gen():
            yield Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
            yield Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T18:00:00"))

        result = intersect(gen())
        self.assertEqual(result.start, dt("2024-01-01T10:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T17:00:00"))


class TestUnion(unittest.TestCase):
    def test_empty_input_returns_none(self):
        self.assertIsNone(union([]))

    def test_single_range_returns_itself(self):
        r = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        result = union([r])
        self.assertEqual(result, r)

    def test_two_overlapping(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        b = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T18:00:00"))
        result = union([a, b])
        self.assertEqual(result.start, dt("2024-01-01T09:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T18:00:00"))

    def test_disjoint_spans_gap(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T10:00:00"))
        b = Range(dt("2024-01-01T11:00:00"), dt("2024-01-01T12:00:00"))
        result = union([a, b])
        self.assertEqual(result.start, dt("2024-01-01T09:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T12:00:00"))

    def test_inclusivity_from_extreme_ranges(self):
        # The earliest start comes from b (exclusive start); the latest end
        # also comes from b (exclusive end). The union inherits both.
        a = Range(
            dt("2024-01-01T09:00:00"),
            dt("2024-01-01T10:00:00"),
            end_inclusive=True,
        )
        b = Range(
            dt("2024-01-01T08:00:00"),
            dt("2024-01-01T12:00:00"),
            start_inclusive=False,
        )
        result = union([a, b])
        self.assertFalse(result.start_inclusive)
        self.assertFalse(result.end_inclusive)

    def test_only_empty_ranges_returns_none(self):
        a = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T09:00:00"))
        b = Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T10:00:00"))
        self.assertIsNone(union([a, b]))

    def test_empty_range_ignored_when_live_present(self):
        live = Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
        empty = Range(dt("2024-01-01T18:00:00"), dt("2024-01-01T18:00:00"))
        result = union([live, empty])
        self.assertEqual(result.start, dt("2024-01-01T09:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T17:00:00"))

    def test_generator_input(self):
        def gen():
            yield Range(dt("2024-01-01T09:00:00"), dt("2024-01-01T17:00:00"))
            yield Range(dt("2024-01-01T10:00:00"), dt("2024-01-01T18:00:00"))

        result = union(gen())
        self.assertEqual(result.start, dt("2024-01-01T09:00:00"))
        self.assertEqual(result.end, dt("2024-01-01T18:00:00"))


if __name__ == "__main__":
    unittest.main()
