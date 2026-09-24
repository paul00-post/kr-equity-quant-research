# Bugs found and fixed

Concrete before/after numbers for mistakes caught during this project, rather than a vague claim that "mistakes were made." All of them were found and fixed during development, and each entry says how it relates to the current model. Numbers are from the research log at the time each bug was found, on the pipeline as configured then — not necessarily the final system.

## 1. Fundamentals factors used today's share count for past dates

*Fixed during development; the fix is part of the current model — its fundamentals features are built on the masked dataset described below.*

Market-cap-based factors (price-to-sales, PEG, cash-to-market-cap) were computed with the latest share count on every historical date. Stock splits were already handled by adjusted prices, but bonus issues, rights offerings and buybacks change the share count without changing the price series — so past market caps were quietly distorted with information from the future.

- Evidence: where a company's share count had moved by more than ±5%, these factors' single-factor IC was about 2× stronger than where it hadn't.
- Fix: naively rescaling by the share-count ratio would have corrupted the split-adjusted cases, so rows were classified as clean or changed using point-in-time filings, and the nine affected columns were masked (not the rows) in the changed ones — about 42% of rows — keeping the other 45 features.
- Walk-forward selection t-statistic: **3.24 (leaky) → 1.44 (honest)**. Every later experiment used the masked dataset.

## 2. A price feature's 52-week window included future prices

*Found and fixed during development, before the current model was built — it does not affect the current model, whose training data was rebuilt after the fix (the affected column is empty in it, and the remaining 52-week-high columns have single-factor IC of 0.025 or less in absolute value).*

A "position relative to the 52-week high" feature was computed with no upper bound on the window, so it mixed in prices from after the date being scored.

- Evidence: one derived column had a single-factor IC of **-0.2378**; the other 53 features were all at 0.041 or below in absolute value. The sign fit the mechanism — stocks that go on to rise have higher future highs, so they look "low" today.
- The first patch fixed two of three derived columns and skipped the third on the reasoning that its history looked fine; it was caught later by checking that the stored data could be reproduced from the current code, then measuring it. After recomputing: IC **-0.2378 → -0.0033**.
- Backtest at that point: CAGR **29.76% → 13.34%**, below the 15.37% KOSPI200 CAGR for the same period; mean walk-forward IC **+0.0881 → +0.0236** (t = 1.31, not significant). The earlier conclusion that the strategy was robust had to be withdrawn, and the signal was later rebuilt on clean data.

## 3. The headline number was inflated by applying full-period parameters retroactively

*Fixed; the headline in the README is the corrected number.*

The regime filter and re-entry cooldown had been selected by a grid search over the whole 2019–2026 window, then applied to every year — including years where an honest, year-by-year process would not have used them.

- Re-run with each year's parameters chosen using only prior years' data: **32.48% CAGR / 1.17 → 31.36% / 1.13**. The gap is small, but the honest number is the one reported.
- Related: the per-year table once compounded to 8.32× against an 8.65× headline, because each year was measured first-trading-day to last-trading-day and the boundary day between years was dropped from both. It was caught by someone else checking the arithmetic, not by any special diligence here.

## 4. A t-statistic of 3.11 that was really 1.06

*Found in a rejected experiment; that label was dropped and never became part of the current model.*

A label built from a 60-day rolling average was scored on weekly snapshots, so adjacent snapshots shared about 92% of their observation window and the yearly samples weren't independent. It wasn't feature leakage, but the t-test's independence assumption was broken.

- Non-overlapping re-test: overall IC t **3.11 → 1.06**; the t for the top-ranked names' IC **2.05 → 1.16**. The real backtest matched the deflated numbers (about zero excess over the universe), so the idea was dropped.
- The correction itself had a flaw: the "non-overlapping" figure used about 32 dates as its sample while the weekly figure used 8 yearly means, and a larger n raises t by itself. Re-done on the same basis, the earlier reported figures were 20–30% too high.
