#!/usr/bin/env python3

import argparse
import datetime
import socket
import sys
import warnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

from compare_to_index import compare_to_index
from get_latest_prices import get_latest_prices
from irr import lifetime_irr
from load_transactions import load_transactions

warnings.simplefilter(action="ignore", category=FutureWarning)

LINE_LENGTH = 58

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


def enrich_active(shares: pd.DataFrame, folder_path: str) -> pd.DataFrame:
    active = get_latest_prices(shares.loc[shares.shares > 0], folder_path)
    active["current value"] = active["shares"] * active["current price"]
    active["change (EUR)"] = active["current value"] + active["invested"]
    active["change (%)"] = active["change (EUR)"] / active["invested"] * -100
    return active


def print_report(
    transactions: pd.DataFrame,
    shares: pd.DataFrame,
    active: pd.DataFrame,
    download: bool) -> float | None:
    print("\nCOMPLETED")
    print("=" * LINE_LENGTH)
    print(shares.loc[shares.shares <= 0, shares.columns[:-1]].round(2))

    print("\nDownloading current prices..." if download else "\nACTIVE (no price download)")
    if download:
        print()

    print("\nACTIVE")
    print("=" * LINE_LENGTH)
    cols = [c for c in active_columns(download) if c in active.columns]
    print(active.loc[:, cols].round(2))

    print("\nSUMMARY")
    print("=" * LINE_LENGTH)
    total = shares[["dividends", "out"]].sum()
    print(f"Total dividends: {total['dividends']:.2f}\nTotal out: {total['out']:.2f}\nTOTAL: {sum(total):.2f}\n")
    if download and "change (EUR)" in active.columns:
        print(f"Unrealized gains: {active['change (EUR)'].sum():.2f}\n")

    irr, terminal_value, n_at_cost = lifetime_irr(transactions, active)
    if irr is not None:
        print(f"Lifetime IRR (money-weighted): {irr * 100:.2f}%/year")
        if n_at_cost:
            print(
                f"  (terminal value {terminal_value:.2f} EUR; "
                f"{n_at_cost} open position(s) without price → cost basis)"
            )
        elif terminal_value > 0:
            print(f"  (includes open positions valued at {terminal_value:.2f} EUR)")
        print()
    else:
        print("Lifetime IRR: could not be computed from cash flows\n")

    return irr


def plot_rolling_returns(transactions: pd.DataFrame) -> None:
    frequency = 7
    today = datetime.date.today()
    days = int((today - transactions.index[0].date()).days / frequency) * frequency
    end_dates = pd.date_range(start=today - datetime.timedelta(days), end=today, freq=f"{frequency}D")
    start_dates = end_dates - datetime.timedelta(365)

    out_rate = []
    dividend_rate = []
    invested = []

    for start_date, end_date in zip(start_dates, end_dates):
        window = transactions[start_date:end_date]
        invested.append(window["invested"].iloc[-1])
        mean_invested = window["invested"].mean()
        out_rate.append(window["out"].sum() / mean_invested)
        dividend_rate.append(window["dividend"].sum() / mean_invested)

    out_rate = 100 * np.array(out_rate)
    dividend_rate = 100 * np.array(dividend_rate)

    register_matplotlib_converters()

    fig, ax = plt.subplots(2, sharex="col", figsize=(7, 6), gridspec_kw={"height_ratios": (0.6, 1)})

    ax[0].plot(end_dates, np.array(invested))
    ax[0].fmt_xdata = mdates.DateFormatter("%Y-%m-%d")
    ax[0].set_ylabel("Total invested (EUR)")
    ax[0].set_ylim(bottom=0)

    ax[1].fill_between(end_dates, 0, out_rate, label="Completed transactions", facecolor="C0", edgecolor="k")
    ax[1].fill_between(
        end_dates, out_rate, out_rate + dividend_rate, label="Dividends", facecolor="C2", edgecolor="k"
    )
    mean_return = np.mean(out_rate + dividend_rate)
    ax[1].plot(
        (end_dates[0], end_dates[-1]),
        [mean_return] * 2,
        linestyle="dashed",
        color="C7",
        label="mean trailing 12m return",
    )
    ax[1].fmt_xdata = mdates.DateFormatter("%Y-%m-%d")
    ax[1].set_ylabel("Trailing 12m realized return\n(% of avg invested)")

    ax[1].legend(loc="upper left")
    fig.align_ylabels()
    fig.tight_layout()
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Track stock transactions, returns, and IRR.")
    parser.add_argument("--download", action="store_true", help="Download current prices from yfinance")
    args = parser.parse_args()
    download = args.download

    if download:
        try:
            socket.create_connection(("www.google.com", 80), timeout=1)
        except OSError:
            download = False

    pd.set_option("display.max_rows", None, "display.max_columns", None, "display.expand_frame_repr", False)

    transactions, folder_path = load_transactions()
    transactions, shares = process_transactions(transactions)

    if download:
        active = enrich_active(shares, folder_path)
    else:
        active = shares.loc[shares.shares > 0]

    irr = print_report(transactions, shares, active, download)

    if download:
        compare_to_index(transactions, portfolio_irr=irr)

    plot_rolling_returns(transactions)


if __name__ == "__main__":
    main()
