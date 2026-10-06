from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional


@dataclass(frozen=True)
class Range:
    """A closed, half-open or fully closed span between two datetimes.

    ``start`` must be less than or equal to ``end``; this is enforced at
    construction. Whether the endpoints are inclusive is controlled by the
    boolean flags ``start_inclusive`` (default ``True``) and
    ``end_inclusive`` (default ``False``). The default of
    ``[start, end)`` matches the most common convention for time intervals:
    a 9-to-5 shift is ``[09:00, 17:00)`` and two adjacent shifts share a
    boundary without overlapping.
    """

    start: datetime
    end: datetime
    start_inclusive: bool = True
    end_inclusive: bool = False

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(
                f"start ({self.start!r}) must not be after end ({self.end!r})"
            )

    def covers_instant(self, instant: datetime) -> bool:
        """Return ``True`` if ``instant`` lies inside this range.

        Boundary handling depends on the inclusivity flags, so a point that
        sits exactly on an endpoint may or may not count as covered.
        """
        if instant < self.start:
            return False
        if instant > self.end:
            return False
        if instant == self.start:
            return self.start_inclusive
        if instant == self.end:
            return self.end_inclusive
        return True

    def is_empty(self) -> bool:
        """Return ``True`` if the range contains no instants.

        A range is empty when ``start == end`` and at least one endpoint is
        exclusive — there is no instant that satisfies both boundary
        conditions at once.
        """
        if self.start != self.end:
            return False
        # start == end: the range is empty unless both endpoints are inclusive,
        # in which case it contains exactly the single instant start == end.
        return not (self.start_inclusive and self.end_inclusive)


def _max(left: datetime, right: datetime) -> datetime:
    return left if left >= right else right


def _min(left: datetime, right: datetime) -> datetime:
    return left if left <= right else right


def _touch(left: Range, right: Range) -> bool:
    """Return ``True`` if ``left`` and ``right`` are adjacent or overlapping.

    Two ranges touch when the gap between them collapses to a single point
    and that point is included by at least one range. This matters for
    intersection: ``[09:00, 10:00)`` and ``[10:00, 11:00)`` share the boundary
    ``10:00``, but because the first range excludes it the intersection is
    empty. ``[09:00, 10:00]`` and ``[10:00, 11:00)`` *do* intersect, at the
    single instant ``10:00``.
    """
    if left.end < right.start or right.end < left.start:
        return False
    # If left ends strictly before right starts (or vice versa) we've already
    # returned False above. The only remaining question is whether a shared
    # boundary point is actually included by at least one side.
    if left.end == right.start:
        return left.end_inclusive or right.start_inclusive
    if right.end == left.start:
        return right.end_inclusive or left.start_inclusive
    return True


def intersect(ranges: Iterable[Range]) -> Optional[Range]:
    """Return the single range common to all of ``ranges``, or ``None``.

    The result is empty (``None``) when any two ranges fail to overlap, when
    the common window collapses to an excluded point, or when ``ranges`` is
    empty. The returned range keeps the inclusivity of the *tightest* boundary
    among the inputs: an intersection endpoint is inclusive only when every
    range that contributes that endpoint marks it inclusive.
    """
    materialised = list(ranges)
    if not materialised:
        return None

    # Drop ranges that contain no instants up front; they cannot contribute.
    live = [r for r in materialised if not r.is_empty()]
    if not live:
        return None

    current = live[0]
    for nxt in live[1:]:
        if not _touch(current, nxt):
            return None

        new_start = _max(current.start, nxt.start)
        new_end = _min(current.end, nxt.end)

        # An endpoint is inclusive in the intersection only when the range
        # that contributes that boundary marks it inclusive. When both ranges
        # share the boundary, both must mark it inclusive.
        if new_start == current.start and new_start == nxt.start:
            start_inclusive = current.start_inclusive and nxt.start_inclusive
        elif new_start == current.start:
            start_inclusive = current.start_inclusive
        else:
            start_inclusive = nxt.start_inclusive

        if new_end == current.end and new_end == nxt.end:
            end_inclusive = current.end_inclusive and nxt.end_inclusive
        elif new_end == current.end:
            end_inclusive = current.end_inclusive
        else:
            end_inclusive = nxt.end_inclusive

        candidate = Range(
            start=new_start,
            end=new_end,
            start_inclusive=start_inclusive,
            end_inclusive=end_inclusive,
        )
        if candidate.is_empty():
            return None
        current = candidate

    return current


def union(ranges: Iterable[Range]) -> Optional[Range]:
    """Return the smallest single range spanning every range in ``ranges``.

    Returns ``None`` when ``ranges`` is empty or contains only empty ranges.
    The result is *not* a merge of disjoint intervals: the returned range runs
    from the earliest start to the latest end and includes any gaps in
    between. Use this when you want the overall envelope, not the covered
    duration. The start (respectively end) inclusivity of the result is the
    inclusivity of whichever input range provides the earliest start
    (respectively latest end).
    """
    materialised = list(ranges)
    if not materialised:
        return None

    live = [r for r in materialised if not r.is_empty()]
    if not live:
        return None

    earliest = min(live, key=lambda r: r.start)
    latest = max(live, key=lambda r: r.end)

    return Range(
        start=earliest.start,
        end=latest.end,
        start_inclusive=earliest.start_inclusive,
        end_inclusive=latest.end_inclusive,
    )
