from typing import NamedTuple, Optional

import pandas as pd
import yfinance as yf

from irr import irr_with_terminal, transaction_cash_flows
from formatting import fmt_number, fmt_pct


class IndexComparisonResult(NamedTuple):
    shares: float
    current_value: float
    gain: float
    index_irr: Optional[float]


def compare_to_index(
    transactions: pd.DataFrame,
    ticker: str = "A500.MI",
    portfolio_irr: Optional[float] = None) -> IndexComparisonResult:
    """
    Simulate routing buy/sell cash flows through an index ETF.

    Returns shares held, terminal value, gain vs net invested, and index IRR.
    Index IRR uses the same cash flows as lifetime_irr (buys, sells, dividends)
    with terminal value = simulated index holdings.
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
    print(
        f"If all buy/sell flows had gone into the index: {fmt_number(shares)} shares "
        f"worth {fmt_number(current_value)} EUR (gain {fmt_number(gain)} EUR)"
    )

    if index_irr is not None:
        print(f"Index IRR (same cash flows as portfolio): {fmt_pct(index_irr * 100)}/year")
        print("  (buys/sells move the index; dividends count as cash received; "
              "terminal = index value today)")
        if portfolio_irr is not None:
            diff = (portfolio_irr - index_irr) * 100
            print(f"Portfolio vs index: {fmt_pct(diff, signed=True)}/year")
    else:
        print("Index IRR: could not be computed")

    print()
    return IndexComparisonResult(shares, current_value, gain, index_irr)


if __name__ == "__main__":

    from load_transactions import load_transactions

    transactions, _ = load_transactions()
    compare_to_index(transactions)
