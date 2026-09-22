# NoLookahead

**Korean equity quant research — fundamental + ML signal blending, walk-forward validated, point-in-time correct.**

This repo documents a long-running solo research project building a systematic long-only strategy for KOSPI200 stocks. It is **not** a copy of the live trading system — the exact gating thresholds, position sizing, and risk-management parameters used in production are intentionally left out. What's here is the methodology, the validation approach, the honest results, and — probably the most useful part for anyone reading this — the mistakes that were found and fixed along the way.

> ⚠️ **Not investment advice.** This is a personal research project shared for educational purposes. Past backtest performance does not predict future results, and nothing here should be read as a recommendation to buy or sell any security.

## TL;DR

| | Strategy | KOSPI200 buy & hold |
|---|---|---|
| CAGR (2022–2026 YTD) | **40.99%** | 26.36% |
| Max drawdown | **-27.7%** | -40.8% |
| CAGR / \|MDD\| | **1.48** | 0.65 |
| Cumulative | **4.97×** | 2.99× |

Net of realistic transaction costs (commission + Korean securities transaction tax + slippage, ~0.41% round-trip). Backtest, not live-verified — see [Limitations](#limitations).

![Equity curve](results/equity_curve.png)

## Approach

Two independent signal sources, combined by intersection rather than by blending scores into one number:

- **Agent B** — a fundamentals/market-cap-based factor model that ranks the investable universe and produces a daily candidate pool (with a per-sector cap, so the pool can't collapse into one hot sector).
- **Agent Cx** — a technical/price-action model (gradient-boosted + a CNN-LSTM variant, blended) that scores the same universe on near-term momentum characteristics, evaluated against the **actual, point-in-time** KOSPI200 membership.
- A stock only becomes a candidate when it clears **both** filters on the same day. Neither filter alone performs as well — this was tested directly, not assumed.

Entries, stop-losses (volatility-based), and profit targets follow a fixed rule set; position risk is managed with per-sector caps and a drawdown-triggered regime filter that blocks new entries during KOSPI-wide selloffs. The exact numeric thresholds for all of this are withheld — the *structure* is what's documented here.

## Methodology / what makes this credible (or not)

- **Point-in-time universe.** KOSPI200 rebalances semi-annually with a real effective date (the trading day after the index provider's announcement, not the 1st of the month). A backtest using "current members" applied retroactively is a look-ahead bug — see [`src/point_in_time_universe.py`](src/point_in_time_universe.py).
- **Order-aware labeling.** Any label built from "did price reach the target within N bars," checked without regard to whether the stop-loss was hit *first*, silently inflates label quality. See [`src/order_aware_labeling.py`](src/order_aware_labeling.py) for the concrete before/after.
- **Transaction costs modeled from day one on every new idea.** Commission on both legs, tax on the sell leg, slippage — see [`src/transaction_costs.py`](src/transaction_costs.py). Several promising-looking ideas below failed only after this was added.
- **Annual walk-forward folds with an embargo**, not k-fold cross-validation — see [`src/walkforward_validation.py`](src/walkforward_validation.py). Each fold trains only on strictly-past data.
- **Relative, not absolute, entry thresholds.** Every time a fixed score cutoff was replaced with a same-day cross-sectional percentile cutoff, results improved and a look-ahead disappeared at the same time (the fixed cutoff had implicitly been tuned by looking at the whole evaluation period's score distribution).

## What didn't work

Documented here because negative results are still results, and because "we tried X and it failed after fixing the accounting" is a more useful signal than a cherry-picked win:

- **Intraday (same-day) trading on 5-minute bars**, across four different label designs (order-aware ATR-relative, fixed-percentage, 3× ATR, and a 5-minute-vs-10-minute bar-size comparison): every design's average per-trade edge came out to roughly 1/10–1/15 of the realistic 0.41% round-trip cost. Net of fees, every configuration was catastrophically unprofitable, regardless of how the entry threshold was tuned.
- **Multi-day holds (3–5 trading days) with 5-minute-bar features**, ranked cross-sectionally with a pairwise ranking loss: this did produce a real, walk-forward-validated signal (Spearman IC ≈ 0.03–0.04 across 5 test years, positive in all of them) — but the average edge was too small to clear transaction costs, and stacking it as an entry-timing filter on top of the main strategy produced no improvement.
- **Intraday direction prediction on leveraged KOSPI200 ETFs** (2× long/inverse): no exploitable signal at 5-minute or 10-minute bar resolution (IC ≈ 0, hit rate ≈ 50%) — bar size was not the bottleneck; the underlying few-hours-ahead index move just isn't predictable from short-window technical features at this granularity.

The common thread: extreme model confidence (the single highest-scored signal of the day, or the tightest percentile cutoff) consistently performed *worse*, not better — a pattern that shows up independently in several of the above.

## Repo structure

```
src/            Standalone, runnable illustrations of the methodology pieces above
                (point-in-time universe, order-aware labeling, transaction costs,
                walk-forward folds) — simplified from the production code, no
                proprietary parameters.
results/        Equity curve chart used above.
```

There is no `data/` directory here — the underlying price/fundamentals data is either commercially licensed or collected from a brokerage API under terms that don't permit redistribution.

## Limitations

- Backtest results, not a live track record. The final risk-management parameters (regime filter threshold, re-entry cooldown) were arrived at after having already seen how a 2026 drawdown period played out — a form of meta-look-ahead that likely makes the backtest somewhat optimistic. Live performance should be expected to be more modest.
- Universe and cost assumptions are Korea-specific (KOSPI200, Korean transaction tax); nothing here is a claim that the approach generalizes to other markets as-is.

## Tech stack

Python, PyTorch (CNN-LSTM), LightGBM/XGBoost, pandas — walk-forward training and backtesting built from scratch rather than an off-the-shelf backtesting library, to keep full control over the point-in-time and cost-accounting details above.

## License

MIT — see [LICENSE](LICENSE). The code here is illustrative infrastructure, not the trading strategy itself.
