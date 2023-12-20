#!/usr/bin/env python3

import os
import sys
import datetime
import socket
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from get_latest_prices import get_latest_prices
from load_transactions import load_transactions
from compare_to_index import compare_to_index
from gui import DataFrameGUI


# check for internet connection
try:
    socket.create_connection(("www.google.com", 80), timeout=1)
    internet_available = True
except OSError:
    internet_available = False


pd.set_option("display.max_rows", None, "display.max_columns", None, 'display.expand_frame_repr', False)

transactions, folder_path = load_transactions()

transactions['out'] = 0.0
out_index = transactions.columns.get_loc('out')
transactions['invested'] = 0.0
invested_index = transactions.columns.get_loc('invested')

names = []
shares = []

for i, (index, transaction) in enumerate(transactions.iterrows()):
    transactions.iat[i, invested_index] = transactions.iat[max(0, i - 1), invested_index]

    # buy first shares of a company
    if transaction.shares > 0 and transaction.company not in names:
        names.append(transaction.company)
        shares.append({'shares': transaction.shares, 'invested': transaction.value, 'dividends': 0, 'out': 0})
        transactions.iat[i, invested_index] -= transaction.value

    # buy more shares
    elif transaction.shares > 0:
        j = names.index(transaction.company)
        shares[j]['shares'] += transaction.shares
        shares[j]['invested'] += transaction.value
        transactions.iat[i, invested_index] -= transaction.value

    # sell shares
    elif transaction.shares < 0:
        j = names.index(transaction.company)
        owned_shares_value = shares[j]['invested'] / shares[j]['shares']
        out = transaction.value - transaction.shares*owned_shares_value
        shares[j]['out'] += out
        transactions.iat[i, out_index] = out

        change = transaction.shares * owned_shares_value
        transactions.iat[i, invested_index] -= change
        shares[j]['invested'] += change
        shares[j]['shares'] += transaction.shares

    # receive dividend
    elif transaction.dividend:
        j = names.index(transaction.company)
        shares[j]['dividends'] += transaction.dividend

    else:
        sys.exit(f"Invalid transaction type in row {index}")

shares = pd.DataFrame.from_records(shares, index=names)
shares.sort_index(inplace=True)
shares['price per share'] = -shares['invested'] / shares['shares']

line_length = 58
print("\nCOMPLETED")
print("=" * line_length)
print(shares.loc[shares.shares <= 0, shares.columns[:-1]].round(2))

# get current prices
print("\nDownloading current prices...")
if internet_available:
    active = get_latest_prices(shares.loc[shares.shares > 0], folder_path)
    active['current value'] = active['shares'] * active['current price']
    active['change (EUR)'] = active['current value'] + active['invested']
    active['change (%)'] = active['change (EUR)'] / active['invested'] * -100
else:
    active = shares.loc[shares.shares > 0]

print("\nACTIVE")
print("=" * line_length)

cols = active.columns.tolist()
new_cols = cols[:2] + cols[4:] + cols[2:4]
print(active.loc[:, new_cols].round(2))

print("\nSUMMARY")
print("=" * line_length)
total = shares[['dividends', 'out']].sum()
print(f"Total dividends: {total['dividends']:.2f}\nTotal out: {total['out']:.2f}\nTOTAL: {sum(total):.2f}\n")
if 'change (EUR)' in active.columns:
    print(f"Unrealized gains: {active['change (EUR)'].sum():.2f}\n")

if internet_available:
    compare_to_index(transactions)

# app = DataFrameGUI(shares)
# app.mainloop()


# PLOTS

frequency = 7
today = datetime.date.today()
days = int((today - transactions.index[0].date()).days / frequency)*frequency
end_dates = pd.date_range(start=today - datetime.timedelta(days), end=today, freq=f'{frequency}D')
start_dates = end_dates - datetime.timedelta(365)

out_rate = []
dividend_rate = []
invested = []

for start_date, end_date in zip(start_dates, end_dates):
    invested.append(transactions[start_date:end_date].tail(1)['invested'].values[0])
    mean_invested = transactions[start_date:end_date]['invested'].mean()
    out_rate.append(transactions[start_date:end_date]['out'].sum() / mean_invested)
    dividend_rate.append(transactions[start_date:end_date]['dividend'].sum() / mean_invested)

out_rate = 100*np.array(out_rate)
dividend_rate = 100*np.array(dividend_rate)

register_matplotlib_converters()

fig, ax = plt.subplots(2, sharex='col', figsize=(7, 6), gridspec_kw={'height_ratios': (0.6, 1)})

ax[0].plot(end_dates, np.array(invested))
ax[0].fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
ax[0].set_ylabel('Total invested (EUR)')
ax[0].set_ylim(bottom=0)

ax[1].fill_between(end_dates, 0, out_rate, label='Completed transactions', facecolor='C0', edgecolor='k')
ax[1].fill_between(end_dates, out_rate, out_rate + dividend_rate, label='Dividends', facecolor='C2', edgecolor='k')
mean_return = np.mean(out_rate + dividend_rate)
ax[1].plot((end_dates[0], end_dates[-1]), [mean_return]*2, linestyle='dashed', color='C7', label="mean annual return")
ax[1].fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
ax[1].set_ylabel('Annual return (%)')

ax[1].legend(loc='upper left')
fig.align_ylabels()
fig.tight_layout()

plt.show()
