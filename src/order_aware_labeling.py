"""
Order-aware vs. order-blind take-profit / stop-loss labeling.

A common shortcut when building a binary "did this trade work out" label is
to check, over some future window: "did price ever touch the take-profit
level?" -> 1, else 0. That is order-blind: it ignores whether price hit the
stop-loss level FIRST. If the stop is hit on day 2 and the target is
(coincidentally) also touched on day 9 before the window closes, the naive
label says "win" for a trade that a real position would have exited at a
loss on day 2.

This silently inflates label quality (and offline AUC) for any setup where
the stop is wide relative to the target, because "eventually touched TP" is
easier to satisfy than "TP before SL." The fix is to walk forward through
the path bar-by-bar and take whichever level is crossed first, with a
conservative tie-break (stop-loss wins on a same-bar double-touch).

Fixing this in the underlying project changed which label design looked
"best" under offline AUC — a design that looked strongest order-blind
stopped looking strongest once evaluated order-aware.
"""
from __future__ import annotations

import numpy as np


def label_order_blind(highs: np.ndarray, lows: np.ndarray, take_profit: float, stop_loss: float) -> int:
    """1 if price ever reaches take_profit within the window, regardless of
    whether stop_loss was crossed first. This is the biased version — `lows`
    and `stop_loss` are accepted (and intentionally unused) only to keep the
    same call signature as `label_order_aware`, so the two are a drop-in
    swap for each other at call sites."""
    del lows, stop_loss
    return int((highs >= take_profit).any())


def label_order_aware(highs: np.ndarray, lows: np.ndarray, take_profit: float, stop_loss: float) -> int:
    """Walk the path forward and resolve whichever level is touched first.
    A bar that touches both levels simultaneously is scored as a stop-loss
    (the conservative assumption — we don't know the intrabar order)."""
    for h, l in zip(highs, lows):
        sl_hit, tp_hit = l <= stop_loss, h >= take_profit
        if sl_hit:
            return 0
        if tp_hit:
            return 1
    return 0  # neither level touched before the window closed


if __name__ == "__main__":
    # Stop hit on bar 1, target only touched on bar 4 — a real position
    # would have been stopped out well before the "eventual" target touch.
    highs = np.array([100.5, 101.0, 101.5, 103.0])
    lows = np.array([97.0, 100.0, 100.5, 101.0])
    entry, take_profit, stop_loss = 100.0, 103.0, 97.5

    print("order-blind label:", label_order_blind(highs, lows, take_profit, stop_loss))  # 1 (wrong)
    print("order-aware label:", label_order_aware(highs, lows, take_profit, stop_loss))   # 0 (correct)
