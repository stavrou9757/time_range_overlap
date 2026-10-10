# time-range-overlap

Compute the intersection and union of multiple datetime ranges, standard library only.

```python
from datetime import datetime
from time_range_overlap import Range, intersect, union

shift_a = Range(datetime(2024, 1, 1, 9), datetime(2024, 1, 1, 17))
shift_b = Range(datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 18))

overlap = intersect([shift_a, shift_b])   # Range(10:00, 17:00)
window  = union([shift_a, shift_b])        # Range(09:00, 18:00)
```

`Range` carries `start_inclusive` (default `True`) and `end_inclusive`
(default `False`) flags, so a half-open interval like a 9-to-5 shift is
expressed directly. `intersect` returns a single `Range` (or `None` when the
common window is empty); `union` returns the smallest single `Range` spanning
all inputs (or `None` when there are no non-empty inputs).

## Why this exists

The problem is simple — find the overlap of two shifts, or the overall span of
a set of events — but doing it by hand means reinventing boundary handling
every time. This library picks one convention and applies it consistently.

The deliberate trade-off: `union` returns a single envelope, **not** a list of
merged intervals. Two disjoint ranges produce a result that includes the gap
between them. That is the right answer for "what window do these events cover?"
and the wrong answer for "what is the total covered duration?". If you need
the latter, sum the ranges yourself — this library does not pretend to offer
it.

## The awkward edge

Boundary inclusivity. `[09:00, 10:00)` and `[10:00, 11:00)` share the instant
`10:00` but their intersection is empty, because neither range includes it.
`[09:00, 10:00]` and `[10:00, 11:00)` intersect at exactly `10:00`. The
implementation honours this: an intersection endpoint is inclusive only when
every contributing range marks it inclusive.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

