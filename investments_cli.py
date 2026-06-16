#!/usr/bin/env python3

import argparse
import socket
import sys
import warnings

import matplotlib.pyplot as plt
import pandas as pd

from compare_to_index import compare_to_index
from formatting import fmt_eur, fmt_number, fmt_pct, format_df_text
from irr import lifetime_irr
from load_transactions import load_transactions
from portfolio import active_columns, completed_columns, enrich_active, process_transactions
from plots import compute_rolling_returns, plot_rolling_returns_matplotlib

warnings.simplefilter(action="ignore", category=FutureWarning)

LINE_LENGTH = 58


def print_report(
    transactions: pd.DataFrame,
    shares: pd.DataFrame,
    active: pd.DataFrame,
    download: bool) -> float | None:
    print("\nCOMPLETED")
    print("=" * LINE_LENGTH)
    print(format_df_text(shares.loc[shares.shares <= 0, completed_columns()]))

    print("\nDownloading current prices..." if download else "\nACTIVE (no price download)")
    if download:
        print()

    print("\nACTIVE")
    print("=" * LINE_LENGTH)
    cols = [c for c in active_columns(download) if c in active.columns]
    active_display = active.loc[:, cols].copy()
    if "invested" in active_display.columns:
        # Display convention: invested is shown as a positive cost basis.
        active_display["invested"] = -active_display["invested"]
    print(format_df_text(active_display))

    print("\nSUMMARY")
    print("=" * LINE_LENGTH)
    total = shares[["dividends", "out"]].sum()
    print(
        f"Total dividends: {fmt_number(total['dividends'])}\n"
        f"Total out: {fmt_number(total['out'])}\n"
        f"TOTAL: {fmt_number(sum(total))}\n"
    )
    if download and "change (EUR)" in active.columns:
        print(f"Unrealized gains: {fmt_number(active['change (EUR)'].sum())}\n")

    irr, terminal_value, n_at_cost = lifetime_irr(transactions, active)
    if irr is not None:
        print(f"Lifetime IRR (money-weighted): {fmt_pct(irr * 100)}/year")
        if n_at_cost:
            print(
                f"  (terminal value {fmt_number(terminal_value)} EUR; "
                f"{n_at_cost} open position(s) without price → cost basis)"
            )
        elif terminal_value > 0:
            print(f"  (includes open positions valued at {fmt_number(terminal_value)} EUR)")
        print()
    else:
        print("Lifetime IRR: could not be computed from cash flows\n")

    return irr


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

    rolling_data = compute_rolling_returns(transactions)
    fig = plot_rolling_returns_matplotlib(rolling_data)
    plt.show()


if __name__ == "__main__":
    main()
