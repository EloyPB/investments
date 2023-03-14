from datetime import date
from matplotlib import pyplot as plt

from yahoo_fin.stock_info import get_data

tickers = ["MSFT", "AMZN", "GOOG"]

fig, ax = plt.subplots()
for ticker in tickers:
    data = get_data(ticker, start_date=date(2020, 1, 1))
    ax.plot(data.index, data.close.values, label=ticker)
    ax.tick_params(axis="x", labelrotation=90)
ax.legend()
fig.tight_layout()
plt.show()
