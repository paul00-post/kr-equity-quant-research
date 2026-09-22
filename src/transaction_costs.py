"""
Realistic Korean equity transaction costs.

Backtests that skip transaction costs — or apply them asymmetrically, or
forget them entirely on one leg of a strategy — routinely turn a losing
edge into an apparently profitable one. This module is the cost model used
throughout the project's backtests: commission on both legs, securities
transaction tax on the sell leg only (Korean market rule), and a slippage
allowance for market-order execution.

The numbers below are the assumptions actually used in this project's
backtests, not live brokerage figures — check your own broker's schedule
before relying on them.
"""
from __future__ import annotations

COMMISSION_RATE = 0.00015  # 0.015%, charged on both the buy and the sell leg
TAX_RATE = 0.0018          # 0.18%, Korean securities transaction tax — sell leg only
SLIPPAGE_RATE = 0.001      # 0.1%, assumed market-order slippage per leg

ROUND_TRIP_COST = COMMISSION_RATE * 2 + TAX_RATE + SLIPPAGE_RATE * 2  # ≈ 0.41%


def buy_cost(price: float) -> float:
    """Effective price paid per share after buy-side commission + slippage."""
    return price * (1 + COMMISSION_RATE + SLIPPAGE_RATE)


def sell_proceeds(price: float) -> float:
    """Effective price received per share after sell-side commission + tax + slippage."""
    return price * (1 - COMMISSION_RATE - TAX_RATE - SLIPPAGE_RATE)


def net_return(entry_price: float, exit_price: float) -> float:
    """Round-trip return after costs, for one share bought and sold at these prices."""
    return sell_proceeds(exit_price) / buy_cost(entry_price) - 1


if __name__ == "__main__":
    print(f"Round-trip cost: {ROUND_TRIP_COST:.3%}")

    gross = 0.005  # a 0.5% gross move
    entry = 10_000
    exit_ = entry * (1 + gross)
    net = net_return(entry, exit_)
    print(f"Gross move {gross:+.2%} -> net after costs {net:+.3%}")

    # A strategy whose average per-trade edge is smaller than ROUND_TRIP_COST
    # cannot be profitable net of costs no matter how it's sized — a check
    # worth running BEFORE building a portfolio-level backtest around it.
