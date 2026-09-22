# Bugs found and fixed

Concrete before/after numbers for mistakes that were caught during this project, rather than a vague claim that "mistakes were made." Each one changed a real result, not just a code comment.

*Items 1–4 are from an experimental intraday signal project, separate from the main strategy behind the [results](README.md) above — noted per item below. Item 5 is about this repo itself.*

## 1. Order-blind labels looked better than order-aware ones — and were wrong

*(experimental intraday signal, not the main strategy)*

An early signal design labeled a trade "1" if price ever reached a take-profit level within a future window, without checking whether the stop-loss was hit *first*. This is easier to satisfy than "target before stop," so it silently inflates label quality for any setup where the stop is wide relative to the target.

- **Order-blind label, offline AUC: 0.6544**
- **Order-aware label (same underlying signal, re-labeled by walking the path forward and resolving whichever level is crossed first): AUC 0.5707**

The order-blind number looked like the better model. It wasn't — it was measuring a different, easier, and unrealistic question. See [`src/order_aware_labeling.py`](src/order_aware_labeling.py).

## 2. A signal was used before it was actually available

*(experimental intraday signal, not the main strategy)*

A secondary signal, dated by its "as of" date, was in fact computed from a window that already included that date's own closing information. Using it to make a decision *on* that date was look-ahead — the same mistake as trading on a piece of news before it's been published.

- Correlation between the signal (as dated) and **that same date's** return: ≈ 0.25
- Correlation between the signal and the **next** date's return — i.e., its actual predictive value once you could realistically have acted on it: ≈ 0.00
- After lagging the signal by one period before using it: a walk-forward validation Spearman IC that had read **≈ +0.09 to +0.10** (two separate runs of the leaky version gave +0.099 and +0.093) came down to a more honest **+0.039**.

A >2x inflation in an IC estimate, from a bug that's invisible unless you specifically check what date range a "point-in-time" signal actually covers.

## 3. Releasing capital too early in a concurrent-position simulation

*(experimental intraday signal, not the main strategy)*

A portfolio backtest released cash from a closed position and made it available for the next trade immediately, even on days when multiple positions were still simultaneously open and that capital was, in reality, still committed.

- Naive (capital released instantly): **CAGR 100.45%, efficiency (CAGR / |MDD|) 4.82**
- Correct (capital tracked per-position, released only at actual exit time, new trades skipped if insufficient *available* — not merely committed — cash): **CAGR 33.92%, efficiency 5.85**

The "wrong" version wasn't just optimistic on CAGR — it was optimistic on CAGR *and* still ended up with worse risk-adjusted efficiency, which is the version of this bug that's easiest to miss because both headline numbers look plausible on their own.

## 4. No transaction costs modeled at all, on an otherwise-complete pipeline

*(experimental intraday signal, not the main strategy)*

An entire experimental pipeline — feature engineering, labeling, model training, backtest simulation — had zero commission, tax, or slippage modeling anywhere in it, unlike the project's main system (see [`src/transaction_costs.py`](src/transaction_costs.py)).

- Best configuration, fee-free (gross): profitable.
- Same configuration, realistic ~0.41% round-trip cost applied: **net CAGR in the -50% to -70% range**, across every variant tried.

Nothing else in the pipeline was wrong — the model, the labels, the walk-forward split were all fine. The absence of a single cost model was enough to flip the entire conclusion.

## 5. (Meta) This README's own yearly-returns table didn't match its own headline number

*(about this repo's own numbers — i.e. the main strategy's results table above, not the experimental signal in items 1–4)*

While writing this repo, the year-by-year table below the [results summary](README.md) was computed as "first trading day of year → last trading day of year." Compounding those numbers gave a different total than the headline cumulative return computed directly from the full equity curve:

- Product of the (wrong) per-year figures: **8.32×**
- Actual total, computed directly: **8.65×**

The bug: each year's figure was computed independently, so the single trading day between "last day of year N" and "first day of year N+1" was silently dropped from *both* years' reported returns, at every year boundary. The fix is to compute annual returns from consecutive year-*end* marks (previous year-end → this year-end), anchoring only the very first year to the actual starting capital — see the corrected computation reflected in the table in [README.md](README.md).

Kept in here on purpose: it's a mistake made in the course of writing the "we're careful about backtest arithmetic" repo, caught by having someone else's eyes independently check the numbers rather than by any special diligence on the author's part. That's the actual lesson.
