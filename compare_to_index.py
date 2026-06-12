from typing import Optional

import pandas as pd
import yfinance as yf

from irr import irr_with_terminal, transaction_cash_flows


def compare_to_index(
    transactions: pd.DataFrame,
    ticker: str = "A500.MI",
    portfolio_irr: Optional[float] = None) -> tuple[float, Optional[float]]:
    """
    Simulate routing buy/sell cash flows through an index ETF.

    Returns (gain_eur, index_irr). Index IRR uses the same cash flows as lifetime_irr
    (buys, sells, dividends) with terminal value = simulated index holdings.
    """
    prices = yf.download(ticker, start=transactions.index.min(), progress=False)

    close = prices["Close"]
    if hasattr(close, "columns"):
        close = close[ticker]

    trade_flows = transactions.loc[transactions["value"] != 0, "value"]
    shares = 0.0
    invested = 0.0
    warned = False

    for tx_date, flow in trade_flows.items():
        if tx_date in prices.index:
            price_date = tx_date
        else:
            price_date = prices.index[prices.index.get_indexer([tx_date], method="nearest")[0]]
            if not warned and abs((price_date - tx_date).days) > 14:
                warned = True
                print("Warning: Cannot find appropriate dates in the index data")

        price = close.loc[price_date]
        shares -= flow / price
        invested -= flow

    current_value = float(shares * close.iloc[-1])
    gain = current_value - invested

    index_irr = irr_with_terminal(transaction_cash_flows(transactions), current_value)

    print(f"\nINDEX COMPARISON ({ticker})")
    print(f"If all buy/sell flows had gone into the index: {shares:.2f} shares "
          f"worth {current_value:.2f} EUR (gain {gain:.2f} EUR)")

    if index_irr is not None:
        print(f"Index IRR (same cash flows as portfolio): {index_irr * 100:.2f}%/year")
        print("  (buys/sells move the index; dividends count as cash received; "
              "terminal = index value today)")
        if portfolio_irr is not None:
            diff = (portfolio_irr - index_irr) * 100
            print(f"Portfolio vs index: {diff:+.2f} percentage points/year")
    else:
        print("Index IRR: could not be computed")

    print()
    return gain, index_irr


if __name__ == "__main__":

    from load_transactions import load_transactions

    transactions, _ = load_transactions()
    compare_to_index(transactions)
