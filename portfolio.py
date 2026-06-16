"""Core portfolio computations shared by CLI and Streamlit dashboard."""

from __future__ import annotations

import sys
import pandas as pd

from get_latest_prices import get_latest_prices

ACTIVE_COLUMNS = [
    "shares",
    "invested",
    "price per share",
    "dividends",
    "out",
]
ACTIVE_COLUMNS_WITH_PRICES = [
    "shares",
    "invested",
    "price per share",
    "current price",
    "current value",
    "change (EUR)",
    "change (%)",
    "dividends",
    "out",
]
COMPLETED_COLUMNS = ["dividends", "out"]


def process_transactions(transactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply buy/sell/dividend logic; return enriched transactions and per-company shares."""
    if not transactions.index.is_monotonic_increasing:
        raise ValueError("Error: Transactions are not sorted.")

    transactions = transactions.copy()
    transactions["out"] = 0.0
    out_index = transactions.columns.get_loc("out")
    transactions["invested"] = 0.0
    invested_index = transactions.columns.get_loc("invested")

    names: list[str] = []
    shares: list[dict] = []
    company_idx: dict[str, int] = {}

    for i, (index, transaction) in enumerate(transactions.iterrows()):
        transactions.iat[i, invested_index] = transactions.iat[max(0, i - 1), invested_index]

        if transaction.dividend:
            shares[company_idx[transaction.company]]["dividends"] += transaction.dividend

        elif transaction.shares >= 0 and transaction.company not in company_idx:
            company_idx[transaction.company] = len(names)
            names.append(transaction.company)
            shares.append(
                {"shares": transaction.shares, "invested": transaction.value, "dividends": 0, "out": 0}
            )
            transactions.iat[i, invested_index] -= transaction.value

        elif transaction.shares >= 0:
            j = company_idx[transaction.company]
            shares[j]["shares"] += transaction.shares
            shares[j]["invested"] += transaction.value
            transactions.iat[i, invested_index] -= transaction.value

        elif transaction.shares < 0:
            j = company_idx[transaction.company]
            owned_shares_value = shares[j]["invested"] / shares[j]["shares"]
            out = transaction.value - transaction.shares * owned_shares_value
            shares[j]["out"] += out
            transactions.iat[i, out_index] = out

            change = transaction.shares * owned_shares_value
            transactions.iat[i, invested_index] -= change
            shares[j]["invested"] += change
            shares[j]["shares"] += transaction.shares

        else:
            sys.exit(f"Invalid transaction type in row {index}")

    shares_df = pd.DataFrame.from_records(shares, index=names)
    shares_df.sort_index(inplace=True)
    shares_df["price per share"] = -shares_df["invested"] / shares_df["shares"]

    return transactions, shares_df


def active_columns(with_prices: bool) -> list[str]:
    return ACTIVE_COLUMNS_WITH_PRICES if with_prices else ACTIVE_COLUMNS


def completed_columns() -> list[str]:
    return COMPLETED_COLUMNS


def enrich_active(shares: pd.DataFrame, folder_path: str) -> pd.DataFrame:
    active = get_latest_prices(shares.loc[shares.shares > 0], folder_path)
    active["current value"] = active["shares"] * active["current price"]
    active["change (EUR)"] = active["current value"] + active["invested"]
    active["change (%)"] = active["change (EUR)"] / active["invested"] * -100
    return active
