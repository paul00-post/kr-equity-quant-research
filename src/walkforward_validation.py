"""
Annual walk-forward folds with an embargo gap.

Cross-validation that shuffles time-series samples randomly across folds
leaks information from the future into training (e.g. a stock's price
three days after the "test" date can easily correlate with its price on
the test date itself). Walk-forward validation avoids this by training
only on data strictly before the test period. An embargo gap between the
end of training and the start of testing further prevents leakage through
labels whose outcome window extends past the training cutoff (e.g. a
"5-day-forward return" label computed near the cutoff peeks past it).

This project also found a second-order version of the same mistake:
re-fitting the training/test cutoff, or picking hyperparameters, using
information about how a specific historical period (e.g. a later crash)
turned out. Walk-forward alone doesn't protect against that — it only
protects against ordinary temporal leakage in the fold split itself.
"""
from __future__ import annotations
import datetime as dt
from dataclasses import dataclass

import pandas as pd


@dataclass
class Fold:
    test_year: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str


def annual_folds(data_start: str, test_years: list[int], embargo_days: int = 0) -> list[Fold]:
    """One fold per test year: train on everything from data_start through
    Dec 31 of the prior year (minus an embargo gap), test on the full
    test_year. Each fold's training set only grows — no fold is ever
    trained on data from its own test year or later."""
    folds = []
    for year in test_years:
        train_end = pd.Timestamp(f"{year - 1}-12-31") - dt.timedelta(days=embargo_days)
        folds.append(Fold(
            test_year=year,
            train_start=data_start,
            train_end=train_end.strftime("%Y-%m-%d"),
            test_start=f"{year}-01-01",
            test_end=f"{year}-12-31",
        ))
    return folds


if __name__ == "__main__":
    for fold in annual_folds(data_start="2019-01-01", test_years=[2022, 2023, 2024], embargo_days=5):
        print(f"test={fold.test_year}  train=[{fold.train_start} .. {fold.train_end}]  "
              f"test=[{fold.test_start} .. {fold.test_end}]")
