import pandas as pd
import pytest

from irr import lifetime_irr
from portfolio import process_transactions


def _tx(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df = df.fillna(0)
    return df


def test_process_transactions_basic_buy_sell_dividend():
    # Conventions:
    # - value < 0 for buys, value > 0 for sells
    # - shares > 0 for buys, shares < 0 for sells
    tx = _tx(
        [
            {"date": "2020-01-01", "company": "ABC", "shares": 10, "value": -1000.0, "dividend": 0.0},
            {"date": "2020-06-01", "company": "ABC", "shares": 0, "value": 0.0, "dividend": 50.0},
            {"date": "2021-01-01", "company": "ABC", "shares": -10, "value": 1100.0, "dividend": 0.0},
        ]
    )

    tx2, shares = process_transactions(tx)

    # Shares position closed
    assert float(shares.loc["ABC", "shares"]) == 0.0
    # Realized gains: +100 (sale) +50 (dividend) = 150
    assert float(shares.loc["ABC", "out"]) == 100.0
    assert float(shares.loc["ABC", "dividends"]) == 50.0
    # Cost basis and P/L should have fully rolled out after sale
    assert float(shares.loc["ABC", "invested"]) == 0.0

    # Transactions dataframe should have new columns
    assert "invested" in tx2.columns
    assert "out" in tx2.columns
    # Invested series should end at 0 after closing position
    assert float(tx2["invested"].iloc[-1]) == 0.0


def test_process_transactions_requires_sorted_index():
    tx = _tx(
        [
            {"date": "2020-02-01", "company": "ABC", "shares": 10, "value": -1000.0, "dividend": 0.0},
            {"date": "2020-01-01", "company": "ABC", "shares": 5, "value": -500.0, "dividend": 0.0},
        ]
    )
    # Make it explicitly unsorted
    tx = tx.iloc[::-1]
    try:
        process_transactions(tx)
        assert False, "Expected ValueError for unsorted transactions index"
    except ValueError:
        pass


def test_lifetime_irr_simple_one_year():
    # Buy 1000, sell 1100 one year later -> ~10% IRR
    tx = _tx(
        [
            {"date": "2020-01-01", "company": "ABC", "shares": 10, "value": -1000.0, "dividend": 0.0},
            {"date": "2021-01-01", "company": "ABC", "shares": -10, "value": 1100.0, "dividend": 0.0},
        ]
    )
    tx2, shares = process_transactions(tx)
    active = shares.loc[shares.shares > 0]
    irr, terminal, n_fallback = lifetime_irr(tx2, active)

    assert n_fallback == 0
    assert terminal == 0.0
    assert irr is not None
    assert irr == pytest.approx(0.10, abs=0.005)

