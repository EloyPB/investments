import yfinance as yf


def compare_to_index(transactions, ticker='A500.MI'):
    # get historic price data
    prices = yf.download(ticker, start=transactions.index.min())

    shares = 0
    invested = 0
    all_good = True

    flows = transactions['value']
    for row in range(len(flows)):
        flow = flows.iloc[row]
        if flow != 0:
            date = flows.index[row]
            if date not in prices.index:
                date = prices.index.to_series().sub(date).abs().idxmin()
                if all_good and (date - flows.index[row]).days > 14:
                    all_good = False
                    print("Warning: Cannot find appropriate dates in the index data")
            price = prices.loc[date, 'Close'][ticker]
            shares -= flow / price
            invested -= flow

    current_value = shares * prices.iloc[-1]['Close', ticker]

    print(f"\nIf all the money had flowed into {ticker}, you'd now have {shares:.2f} shares worth {current_value:.2f}, resulting in a gain of {current_value-invested:.2f}\n")


if __name__ == "__main__":

    from load_transactions import load_transactions

    transactions, _ = load_transactions()
    compare_to_index(transactions)
