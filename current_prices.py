import numpy as np
import yfinance as yf
import pandas as pd


def get_latest_prices(shares):
    shares = shares.copy()

    tickers_sheet = pd.read_excel("/c/DATA/CLOUD/Documentos/ticker_symbols.xlsx", header=None, names=["name", "ticker"])
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

