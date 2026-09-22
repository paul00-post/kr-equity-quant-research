"""
Point-in-time (PIT) universe membership.

Index providers publish reconstitution results with a lag: KOSPI200's
semi-annual rebalance is decided in early June / December, but only takes
effect a few days later (in KRX's case, the trading day after the second
Thursday of the month). A backtest that applies a snapshot as of "June 1st"
instead of the actual effective date silently trades on membership
information a market participant would not have had yet.

This module illustrates the fix: keep dated membership snapshots and look
up "who was actually in the index on this date" with no look-ahead,
instead of a single "current members" list applied uniformly across all
history.

The real project maintains snapshots pulled from the exchange's own index
composition files; this file ships a tiny synthetic example so it runs
standalone.
"""
from __future__ import annotations
from bisect import bisect_right
from dataclasses import dataclass

import pandas as pd


@dataclass
class Snapshot:
    effective_date: pd.Timestamp
    members: frozenset[str]


class PointInTimeUniverse:
    def __init__(self, snapshots: list[Snapshot]):
        snapshots = sorted(snapshots, key=lambda s: s.effective_date)
        self._dates = [s.effective_date for s in snapshots]
        self._members = [s.members for s in snapshots]

    def members_at(self, date) -> frozenset[str]:
        d = pd.Timestamp(date).normalize()
        idx = bisect_right(self._dates, d) - 1
        if idx < 0:
            return frozenset()
        return self._members[idx]

    def is_member(self, date, ticker: str) -> bool:
        return ticker in self.members_at(date)


if __name__ == "__main__":
    # A rebalance decided in early June 2024 (B dropped, D added) only takes
    # effect on 2024-06-14 — not on the 1st of the month.
    universe = PointInTimeUniverse([
        Snapshot(pd.Timestamp("2023-12-14"), frozenset({"A", "B", "C"})),
        Snapshot(pd.Timestamp("2024-06-14"), frozenset({"A", "C", "D"})),
    ])

    # Naively bucketing by "month" and applying the new membership from
    # 2024-06-01 would drop B and add D two weeks too early — a look-ahead
    # bug. A point-in-time lookup keeps the OLD membership until the real
    # effective date:
    print("2024-06-10, B in universe:", universe.is_member("2024-06-10", "B"))  # True  (still old membership)
    print("2024-06-10, D in universe:", universe.is_member("2024-06-10", "D"))  # False (not effective yet)
    print("2024-06-20, B in universe:", universe.is_member("2024-06-20", "B"))  # False (correctly dropped)
    print("2024-06-20, D in universe:", universe.is_member("2024-06-20", "D"))  # True  (correctly added)
