import numpy as np
import yfinance as yf
import pandas as pd


def get_latest_prices(shares, folder_path):
    shares = shares.copy()

    tickers_sheet = pd.read_excel(f"{folder_path}/ticker_symbols.xlsx", header=None, names=["name", "ticker"])
    tickers_sheet = tickers_sheet[tickers_sheet['name'].isin(shares.index)]  # keep only active shares
    names = tickers_sheet['name'].to_list()
    tickers = tickers_sheet['ticker'].to_list()
    prices = yf.download(tickers, period="1d", group_by="ticker")

    shares['current price'] = np.nan
    current_index = shares.columns.get_loc('current price')

    for row_num, (name, shares_row) in enumerate(shares.iterrows()):
        if name in names:
            ticker_num = names.index(name)
            ticker = tickers[ticker_num]
            shares.iat[row_num, current_index] = prices[(ticker, 'Close')].tail(1).values[0]

    return shares

