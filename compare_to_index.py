import yfinance as yf


def compare_to_index(transactions, ticker="A500.MI"):
    prices = yf.download(ticker, start=transactions.index.min(), progress=False)

    close = prices["Close"]
    if hasattr(close, "columns"):
        close = close[ticker]

    flows = transactions.loc[transactions["value"] != 0, "value"]
    shares = 0.0
    invested = 0.0
    warned = False

    for tx_date, flow in flows.items():
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

    current_value = shares * close.iloc[-1]

    print(
        f"\nIf all the money had flowed into {ticker}, you'd now have {shares:.2f} shares "
        f"worth {current_value:.2f}, resulting in a gain of {current_value - invested:.2f}\n"
    )


if __name__ == "__main__":

    from load_transactions import load_transactions

    transactions, _ = load_transactions()
    compare_to_index(transactions)
