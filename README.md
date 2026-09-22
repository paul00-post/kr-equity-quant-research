# Korean Large-Cap Equities Quant Research

**Walk-forward backtesting with a point-in-time universe and a risk-gated signal pipeline.**

This repo is a write-up of the methodology and validation discipline behind a long-running solo research project on large-cap Korean equities — not a pitch for the returns below. (Not literally "KOSPI200 stocks," either — see [Approach](#approach).) It is **not** a copy of the live trading system — the exact gating thresholds, position sizing, and risk-management parameters used in production are intentionally left out. What's actually here, and actually checkable: the point-in-time and cost-accounting discipline in [`src/`](src/), tests that pin down the claims in [`tests/`](tests/), and the mistakes that were found and fixed along the way, in [BUGS.md](BUGS.md) with real before/after numbers. The performance table below is not checkable from this repo — see the note under it before reading too much into it.

> ⚠️ **Not investment advice.** This is a personal research project shared for educational purposes. Past backtest performance does not predict future results, and nothing here should be read as a recommendation to buy or sell any security.

## Results (reference only — see caveat)

| | Strategy | KOSPI200 buy & hold |
|---|---|---|
| CAGR (2019–2026 YTD) | **32.48%** | 22.30% |
| Max drawdown | **-27.7%** | -40.8% |
| CAGR / \|MDD\| | **1.17** | 0.55 |
| Cumulative | **8.65×** | 4.68× |

> **These numbers can't be independently verified from this repo.** The code here ([`src/`](src/)) illustrates the techniques used, not the full pipeline — the actual backtest depends on licensed/collected Korean market data that isn't (and can't be) included. Read this table as "what came out of a walk-forward, cost-aware backtest for this approach," not as something you can reproduce or take on faith. The methodology sections below are the part you actually *can* evaluate.

Net of realistic transaction costs (commission + Korean securities transaction tax + slippage, ~0.41% round-trip). "KOSPI200 buy & hold" is the KODEX 200 ETF (069500) price series — a price return, not a total return with dividends reinvested, which flatters the strategy comparison somewhat. See also [Limitations](#limitations) — in particular, the most recent fold (2026) underperforms buy-and-hold by a wide margin, and the risk-management parameters have a meta-look-ahead issue.

![Equity curve](results/equity_curve.png)

### Walk-forward results by year

Each year below is an out-of-sample fold: for the model that year is tested on, all training data is strictly earlier (annual walk-forward, no k-fold shuffling — see [`src/walkforward_validation.py`](src/walkforward_validation.py)). Shown per-year rather than only as one aggregate number, since an eight-year average can hide a lot of variance:

| Year | Strategy | KOSPI200 | Excess |
|---|---|---|---|
| 2019 | +7.8% | +15.8% | -8.0pp |
| 2020 | +20.5% | +35.6% | -15.1pp |
| 2021 | +33.2% | +3.0% | +30.2pp |
| 2022 | +34.8% | -24.2% | +59.0pp |
| 2023 | +27.5% | +24.9% | +2.6pp |
| 2024 | -5.7% | -9.4% | +3.7pp |
| 2025 | +136.3% | +94.2% | +42.1pp |
| 2026 (YTD, through Sep 4) | +30.5% | +73.8% | -43.3pp |

(Compounding these year-by-year figures reproduces the 8.65× total above exactly — each year's return is computed year-end to year-end, not first-trading-day to last-trading-day, so the boundary days aren't silently dropped.)

Three years (2019, 2020, 2026) underperform buy-and-hold outright, and 2026 underperforms by a wide margin — a strong KOSPI rally this strategy's regime/sector-cap risk controls didn't fully capture. Included deliberately rather than cut off at a more flattering point.

### Additional diagnostics

The headline CAGR comparison above isn't apples-to-apples on its own — buy-and-hold is always 100% invested, and a lower-drawdown strategy that's just sitting in cash more often isn't actually more skillful. These numbers are here to close that gap:

| | Value |
|---|---|
| Average cash allocation | 50.4% (i.e. ~49.6% average market exposure) |
| Annualized Sharpe ratio | 1.59 |
| Total trades (2019–2026) | 373 |
| Win rate | 44.0% (gross and net of the ~0.41% round-trip cost — identical; see note below) |
| Average hold time | 12.4 trading days |
| Equal-weight universe benchmark (avg. return of all PIT KOSPI200 members, 2019–2026) | 2.04× cumulative |
| Cost sensitivity: CAGR at 2× assumed slippage (0.41% → 0.61% round-trip) | 29.90% (vs. 32.48% base) |

A few of these are worth reading correctly rather than at face value:

- **~50% average exposure while still beating a fully-invested benchmark is the more interesting number than the CAGR itself** — the strategy achieved its return profile with roughly half its capital sitting in cash on an average day, not by being in the market more aggressively than buy-and-hold.
- **44% win rate is not a red flag on its own.** The exit rules are asymmetric by design — the profit target is set further from entry than the stop-loss — so more small losses than wins is expected. What matters is the per-trade expectancy (implied by the CAGR above), not the win rate in isolation. It's defined as "exit price above entry price," checked both before and after the ~0.41% round-trip cost — 0 of 373 trades flip from win to loss once costs are applied (average gross per-trade return is +2.63%, well clear of the cost), so the number isn't hiding a pile of costs-flip-it-negative trades the way a tighter-margin strategy's might.
- **The equal-weight universe comparison is the more honest benchmark than the cap-weighted KOSPI200 ETF.** A cap-weighted index can be dominated by a handful of mega-caps; an approach that only beats the cap-weighted index but not the average stock in its own universe would be a much weaker result. Here the gap is *larger* against the equal-weight benchmark (8.65× vs. 2.04×) than against the cap-weighted one (8.65× vs. 4.68×).
- **Doubling the slippage assumption costs about 2.6 percentage points of CAGR, not the whole edge.** That's a reasonable sanity check that the result isn't a knife-edge function of the exact cost assumptions in [`src/transaction_costs.py`](src/transaction_costs.py) — though it's a stress test of one assumption, not proof of robustness to all of them.
- Strategy capacity (how much capital this scales to before market impact erodes the edge) isn't estimated here — it would need order-book/liquidity data this project doesn't have, so no number is given rather than a guessed one.

### Operational refinement: idle-cash parking (tested, not folded into the headline numbers)

Given ~50% average cash allocation above, an obvious question: can that idle cash earn something instead of sitting at 0%? Tested one approach — parking it in a money-market-rate ETF (KODEX CD금리액티브, ticker 459580) between signals, using the exact same stock-order flow the strategy already uses for regular trades (no new account, no transfer step).

**Why not CMA/RP directly, which would be the more natural fit?** It would — near-instant liquidity, essentially zero price risk. But at this specific broker, a CMA sub-account can't be used to place stock orders directly, and there's no transfer API to move cash from CMA into the trading sub-account programmatically. That's a brokerage account/API limitation, not a property of RP/CMA as an instrument (and it isn't a deposit-insurance question either — the ETF route below isn't deposit-insured either, so that's not what's driving the choice). The money-market ETF was chosen specifically because it trades through the exact same stock-order API already in use, sidestepping that limitation entirely.

**Limitation on the test itself:** this ETF only has real trading history from 2023-06-08 — it didn't exist for most of the 2019–2026 backtest window. So this is only tested on 2023-06-08–2026-09-04 (~3.2 years), which is also why it isn't merged into the headline 2019–2026 table above — the two aren't the same period, and splicing a partial-period improvement into a full-period number is exactly the kind of thing this repo has tried to avoid elsewhere (see [BUGS.md](BUGS.md)).

| | No parking (cash earns 0%) | ETF-parked |
|---|---|---|
| CAGR | 43.22% | **44.20%** |
| MDD | -27.7% | **-27.0%** |
| CAGR / \|MDD\| | 1.56 | **1.64** |

Commission-only cost (this ETF is exempt from Korea's securities transaction tax, unlike regular stocks); modeled at the level of individual cash-in/cash-out events rather than net daily cash change, since 101 of the days in this window had two or more offsetting cash events that a naive daily-net approach would have under-charged for. Event-level accounting added about 25% more modeled commission (₩756,964 → ₩948,516 over the window) and the result barely moved (+1.03pp → +0.98pp CAGR), so the naive version wasn't hiding much.

### Statistical robustness checks

Two Monte Carlo-style checks, run to address a more basic question than anything above: is any of this distinguishable from noise?

**1. Trade-sequencing bootstrap — is the reported MDD a fluke of ordering?** The actual daily returns (same set, ~1,886 trading days) were reshuffled into 5,000 random orderings and the max drawdown recomputed for each. Final cumulative return is identical across every reshuffle by construction (compounding a fixed multiset of returns is order-independent — a useful sanity check that this ran correctly), but MDD is entirely order-dependent:

| | Value |
|---|---|
| Actual MDD | -27.7% |
| Reshuffled MDD — mean | -20.95% |
| Reshuffled MDD — 5th/95th percentile | -29.57% / -14.79% |
| Actual MDD's percentile in the reshuffled distribution | 8.3rd |

The realized drawdown path was on the unlucky side — most reorderings of the exact same trades would have produced a smaller drawdown. Read this as "the CAGR isn't sequencing-dependent, but the specific -27.7% MDD partly is."

**2. Signal permutation test — is Agent Cx's stock selection distinguishable from random?** Agent B's pool and every risk/position-sizing rule were left untouched; only Agent Cx's score was replaced with random noise (same per-day pass rate as the real percentile gate, so trade frequency is comparable — only *which* names pass is randomized). Reran the full backtest 1,000 times:

| | Value |
|---|---|
| Random-signal CAGR — mean / median | 7.48% / 7.47% |
| Random-signal CAGR — 95th percentile | 14.59% |
| Random-signal CAGR — max of 1,000 runs | 23.29% |
| **Actual CAGR (32.48%) exceeds runs out of 1,000** | **1,000 / 1,000 (p ≈ 0.0000)** |
| Random-signal MDD — mean / median | -29.14% / -27.71% (≈ actual -27.7%) |

The real signal's CAGR clears every one of 1,000 random permutations — not marginal. Notably, MDD *doesn't* separate real from random (the random median, -27.71%, is almost identical to the actual result) — drawdown control here comes from the risk-management structure (regime filter, sector caps, stop losses), which stays fixed either way, not from stock selection. The return, on the other hand, comes overwhelmingly from Agent Cx actually picking the right names.

One honest caveat: both permutation runs reuse the same fixed cooldown/regime parameters as the headline backtest, so this doesn't test or clear the meta-look-ahead issue in [Limitations](#limitations) — it isolates a different question (signal quality, not parameter selection) and that other caveat still applies on top of this.

## Approach

Two independent signal sources, combined by intersection rather than by blending scores into one number:

```mermaid
flowchart TD
    subgraph AgentB["Agent B — fundamentals"]
        B1["Market-cap-approximated<br/>large-cap universe"] --> B2["XGBoost ranker<br/>(rank:ndcg)"]
        B2 --> B3["Daily candidate pool<br/>(per-sector cap applied)"]
    end

    subgraph AgentCx["Agent Cx — price action / ML"]
        C1["Official KOSPI200<br/>point-in-time membership"] --> C2["XGBoost classifier<br/>(binary:logistic)"]
        C1 --> C3["CNN-LSTM model"]
        C2 --> C4["Blended cross-sectional<br/>percentile score"]
        C3 --> C4
    end

    B3 --> GATE{"Passes both<br/>on the same day?"}
    C4 --> GATE
    GATE -->|no| SKIP["Not traded"]
    GATE -->|yes| ENTRY["Entry rules<br/>gap filter · volatility-based stop · profit target"]
    ENTRY --> RISK["Risk gates<br/>per-sector cap · drawdown regime filter · re-entry cooldown"]
    RISK --> POS["Position<br/>(timer / stop / target exit)"]
```

- **Agent B** — an XGBoost *ranking* model (`rank:ndcg`) trained on fundamentals, ranking a self-computed large-cap universe (a market-cap approximation, not the official index) to produce a daily candidate pool (with a per-sector cap, so the pool can't collapse into one hot sector).
- **Agent Cx** — a technical/price-action signal blending an XGBoost *classifier* (`binary:logistic`) with a CNN-LSTM variant, scoring stocks within the **actual, point-in-time official KOSPI200 membership**. (A classifier here, not a ranker like Agent B — the two agents were developed at different points in the project rather than to a shared design spec.)
- A stock only becomes a candidate when it clears **both** filters on the same day — i.e. when *both* a market-cap-based approximation and the official index agree it belongs in the large-cap set. This is a deliberate design choice, not an oversight: the two universes disagree on roughly 15–20% of names at any given time, and requiring agreement between two independently-derived definitions turned out to filter better than either one alone (tested directly, not assumed). The tradable universe is therefore this intersection, not "KOSPI200" in the strict sense.

Entries, stop-losses (volatility-based), and profit targets follow a fixed rule set; position risk is managed with per-sector caps and a drawdown-triggered regime filter that blocks new entries during KOSPI-wide selloffs. The exact numeric thresholds for all of this are withheld — the *structure* is what's documented here.

## Methodology / what makes this credible (or not)

- **Point-in-time universe.** KOSPI200 rebalances semi-annually with a real effective date (the trading day after the index provider's announcement, not the 1st of the month) — this matters for the Agent Cx side of the filter above. A backtest using "current members" applied retroactively is a look-ahead bug — see [`src/point_in_time_universe.py`](src/point_in_time_universe.py).
- **Order-aware labeling.** Any label built from "did price reach the target within N bars," checked without regard to whether the stop-loss was hit *first*, silently inflates label quality. See [`src/order_aware_labeling.py`](src/order_aware_labeling.py) for the concrete before/after.
- **Transaction costs modeled from day one on every new idea.** Commission on both legs, tax on the sell leg, slippage — see [`src/transaction_costs.py`](src/transaction_costs.py). More than one promising-looking signal turned out to be smaller than the round-trip cost once this was added honestly.
- **Annual walk-forward folds with an embargo**, not k-fold cross-validation — see [`src/walkforward_validation.py`](src/walkforward_validation.py). Each fold trains only on strictly-past data.
- **Relative, not absolute, entry thresholds.** Every time a fixed score cutoff was replaced with a same-day cross-sectional percentile cutoff, results improved and a look-ahead disappeared at the same time (the fixed cutoff had implicitly been tuned by looking at the whole evaluation period's score distribution).

## Repo structure

```
src/            Standalone, runnable illustrations of the methodology pieces above
                (point-in-time universe, order-aware labeling, transaction costs,
                walk-forward folds) — simplified from the production code, no
                proprietary parameters.
tests/          pytest tests that pin down the actual claims made by src/ and
                this README (not just print-and-eyeball demos).
results/        Equity curve chart used above.
BUGS.md         Concrete before/after numbers for mistakes found and fixed.
```

There is no `data/` directory here — the underlying price/fundamentals data is either commercially licensed or collected from a brokerage API under terms that don't permit redistribution.

## How to run

```bash
pip install -r requirements-dev.txt

python src/point_in_time_universe.py
python src/order_aware_labeling.py
python src/transaction_costs.py
python src/walkforward_validation.py

pytest tests/
```

Requires Python 3.10+. Each `src/` file is self-contained and runs standalone (no shared setup, no external data) — `requirements.txt` alone (pandas, numpy) is enough to run them; `requirements-dev.txt` adds pytest for the test suite.

## Limitations

- Backtest results, not a live track record. A walk-forward selection process for the regime filter and re-entry cooldown (using, for each year, only data from prior years — genuinely honest at the selection step) picked "off" for every year through 2025 and only turned them on for 2026. The backtest above doesn't run that year-by-year schedule, though — it applies the 2026-selected setting as a single fixed constant across the entire 2019–2026 window. That means 2019–2025's results also benefit from a safeguard that an honest process wouldn't have applied to them at the time; it was fixed that way only once 2026 had already shown why it would help. Live performance should be expected to be more modest than the backtest above.
- Universe and cost assumptions are Korea-specific (a KOSPI200-adjacent large-cap universe, Korean transaction tax); nothing here is a claim that the approach generalizes to other markets as-is.

## Tech stack

**Modeling & backtesting:** Python, PyTorch (CNN-LSTM), XGBoost, pandas — walk-forward training and backtesting built from scratch rather than an off-the-shelf backtesting library, to keep full control over the point-in-time and cost-accounting details above.

**Data pipeline:** the underlying data isn't redistributable (see above), but the collection side is its own piece of engineering, built on public sources:

- **Financial statements** — Open DART API (Korea's regulatory filing system), collected per-company and cached locally, with the reporting-date handling that makes a fundamentals factor point-in-time rather than retroactive.
- **Index membership** — `pykrx`, pulling KRX's own published KOSPI200 constituent files per rebalance date. This is what lets the point-in-time universe in [`src/point_in_time_universe.py`](src/point_in_time_universe.py) reflect actual historical membership rather than a reconstruction. Worth knowing before trusting a reconstructed one: measured against the official files at the same date, a market-cap-based approximation of "the top 200" differed on ~17% of names. That's why the Agent Cx side switched to the official source — Agent B keeps the approximation deliberately, and the disagreement between the two is the intersection filter described above.
- **Daily prices** — FinanceDataReader, cached to local Parquet.

## AI assistance

Built with Claude Code (Anthropic) as a research/pair-programming assistant throughout — implementation, debugging, and this writeup included. Research direction, validation decisions, and what to reject were mine.

## License

MIT — see [LICENSE](LICENSE). The code here is illustrative infrastructure, not the trading strategy itself.
