import numpy as np
import pandas as pd
import yfinance as yf


def get_latest_prices(shares, folder_path):
    shares = shares.copy()

    tickers_sheet = pd.read_excel(
        f"{folder_path}/ticker_symbols.xlsx", header=None, names=["name", "ticker"]
    )
    name_to_ticker = (
        tickers_sheet.loc[tickers_sheet["name"].isin(shares.index), ["name", "ticker"]]
        .set_index("name")["ticker"]
        .to_dict()
    )

    prices = yf.download(
        list(name_to_ticker.values()), period="1d", group_by="ticker", progress=False
    )

    shares["current price"] = np.nan

    for name, ticker in name_to_ticker.items():
        try:
            close = prices[(ticker, "Close")].dropna()
            if close.empty:
                print(f"Warning: no current price for {name} ({ticker})")
            else:
                shares.loc[name, "current price"] = close.iloc[-1]
        except (KeyError, TypeError, IndexError):
            print(f"Warning: no current price for {name} ({ticker})")

    return shares
