"""Time Range Overlap: compute the intersection and union of datetime ranges.

This package exposes a single value type, :class:`Range`, and two operations:
:func:`intersect` and :func:`union`. Both operate on iterables of ``Range``
objects and return a single ``Range`` (or ``None`` when the result is empty).

Design choice: intersection and union are folded into a single range rather
than returned as a list of ranges. This keeps the return type predictable and
avoids the ambiguity of how to order or merge a list of disjoint results. The
trade-off is that a union of two non-overlapping ranges is represented by the
span from the earliest start to the latest end, which includes the gap in
between. This is the right answer for questions like "what is the overall
window these events cover?" and the wrong answer for questions like "what is
the total covered duration?". The README states this plainly.
"""

from .core import Range, intersect, union

__all__ = ["Range", "intersect", "union"]
