"""
Actual assertions for the claims made in README.md and BUGS.md — not just
runnable print statements. Run with: pytest tests/
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from point_in_time_universe import PointInTimeUniverse, Snapshot
from order_aware_labeling import label_order_blind, label_order_aware
from transaction_costs import ROUND_TRIP_COST, buy_cost, sell_proceeds, net_return
from walkforward_validation import annual_folds


def test_pit_universe_uses_old_membership_before_effective_date():
    universe = PointInTimeUniverse([
        Snapshot(pd.Timestamp("2023-12-14"), frozenset({"A", "B", "C"})),
        Snapshot(pd.Timestamp("2024-06-14"), frozenset({"A", "C", "D"})),
    ])
    # One day before the new snapshot takes effect: still the OLD membership.
    assert universe.is_member("2024-06-13", "B") is True
    assert universe.is_member("2024-06-13", "D") is False


def test_pit_universe_switches_exactly_on_effective_date():
    universe = PointInTimeUniverse([
        Snapshot(pd.Timestamp("2023-12-14"), frozenset({"A", "B", "C"})),
        Snapshot(pd.Timestamp("2024-06-14"), frozenset({"A", "C", "D"})),
    ])
    assert universe.is_member("2024-06-14", "B") is False
    assert universe.is_member("2024-06-14", "D") is True


def test_pit_universe_before_any_snapshot_is_empty_not_leaked_from_future():
    universe = PointInTimeUniverse([Snapshot(pd.Timestamp("2024-06-14"), frozenset({"A"}))])
    assert universe.members_at("2020-01-01") == frozenset()


def test_order_blind_label_ignores_stop_loss_hit_first():
    # Stop hit on the first bar; target only touched on a later bar. The
    # order-blind label is wrong here by construction — that's the bug.
    highs = np.array([100.5, 101.0, 101.5, 103.0])
    lows = np.array([97.0, 100.0, 100.5, 101.0])
    assert label_order_blind(highs, lows, take_profit=103.0, stop_loss=97.5) == 1


def test_order_aware_label_resolves_the_same_case_correctly():
    highs = np.array([100.5, 101.0, 101.5, 103.0])
    lows = np.array([97.0, 100.0, 100.5, 101.0])
    assert label_order_aware(highs, lows, take_profit=103.0, stop_loss=97.5) == 0


def test_order_aware_same_bar_double_touch_resolves_to_stop_loss():
    # A single bar that touches both levels is scored conservatively as a
    # stop-loss, since we don't know the true intrabar order.
    highs = np.array([105.0])
    lows = np.array([95.0])
    assert label_order_aware(highs, lows, take_profit=103.0, stop_loss=97.0) == 0


def test_round_trip_cost_matches_documented_value():
    assert abs(ROUND_TRIP_COST - 0.0041) < 1e-9


def test_net_return_is_strictly_worse_than_gross_return():
    entry, exit_ = 10_000, 10_050  # +0.5% gross
    gross = exit_ / entry - 1
    net = net_return(entry, exit_)
    assert net < gross
    assert abs(net - 0.00088) < 1e-4  # ~0.088% after ~0.41% round-trip cost


def test_buy_cost_and_sell_proceeds_are_on_opposite_sides_of_price():
    price = 10_000
    assert buy_cost(price) > price
    assert sell_proceeds(price) < price


def test_walkforward_folds_never_train_on_the_test_year_or_later():
    folds = annual_folds(data_start="2019-01-01", test_years=[2022, 2023, 2024], embargo_days=5)
    for fold in folds:
        assert pd.Timestamp(fold.train_end) < pd.Timestamp(fold.test_start)
        assert pd.Timestamp(fold.test_start).year == fold.test_year


def test_walkforward_folds_train_window_grows_each_year():
    folds = annual_folds(data_start="2019-01-01", test_years=[2022, 2023, 2024])
    ends = [pd.Timestamp(f.train_end) for f in folds]
    assert ends[0] < ends[1] < ends[2]


def test_walkforward_embargo_shrinks_the_training_window():
    no_embargo = annual_folds(data_start="2019-01-01", test_years=[2022], embargo_days=0)[0]
    with_embargo = annual_folds(data_start="2019-01-01", test_years=[2022], embargo_days=5)[0]
    assert pd.Timestamp(with_embargo.train_end) < pd.Timestamp(no_embargo.train_end)
