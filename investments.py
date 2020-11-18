#!/usr/bin/env python3

import sys
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


transactions_file_path = "/c/DATA/MEGA/Documentos/transactions.xlsx"
transactions = pd.read_excel(transactions_file_path, index_col=0,
                             dtype={'date': "datetime64[D]", 'company': str, 'shares': float, 'value': float,
                                    'dividend': float})
transactions.fillna(0, inplace=True)

transactions['out'] = 0.0
out_index = transactions.columns.get_loc('out')

transactions['invested'] = 0.0
invested_index = transactions.columns.get_loc('invested')


shares = pd.DataFrame(columns=['company', 'shares', 'invested', 'dividends', 'out'])

for i, (index, transaction) in enumerate(transactions.iterrows()):
    # buy first shares of a company
    if transaction.value < 0 and transaction.company not in shares.company.values:
        shares = shares.append({'company': transaction.company, 'shares': transaction.shares,
                                'invested': transaction.value, 'dividends': 0, 'out': 0}, ignore_index=True)

    # buy more shares
    elif transaction.value < 0:
        shares.loc[shares['company'] == transaction.company, 'shares'] += transaction.shares
        shares.loc[shares['company'] == transaction.company, 'invested'] += transaction.value

    # sell shares
    elif transaction.value > 0:
        owned_shares_value = (shares.loc[shares['company'] == transaction.company, 'invested'].values[0]
                              / shares.loc[shares['company'] == transaction.company, 'shares'].values[0])
        out = transaction.value - transaction.shares*owned_shares_value
        shares.loc[shares['company'] == transaction.company, 'out'] += out
        transactions.iat[i, out_index] = out

        shares.loc[shares['company'] == transaction.company, 'shares'] += transaction.shares
        shares.loc[shares['company'] == transaction.company, 'invested'] = \
            shares.loc[shares['company'] == transaction.company, 'shares']*owned_shares_value

    # receive dividend
    elif transaction.dividend:
        shares.loc[shares['company'] == transaction.company, 'dividends'] += transaction.dividend

    else:
        sys.exit(f"Invalid transaction type in row {index}")

    transactions.iat[i, invested_index] = shares['invested'].sum()

print(shares)
total = shares.loc[:, ['dividends', 'out']].sum()
print(f"\nTotal dividends: {total['dividends']:.2f}\nTotal out: {total['out']:.2f}\nTOTAL: {sum(total):.2f}")

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
    out_rate.append(transactions[start_date:end_date]['out'].sum() / invested[-1])
    dividend_rate.append(transactions[start_date:end_date]['dividend'].sum() / invested[-1])

out_rate = -100*np.array(out_rate)
dividend_rate = -100*np.array(dividend_rate)

register_matplotlib_converters()

fig, ax = plt.subplots(2, sharex='col')

ax[0].plot(end_dates, -np.array(invested))
ax[0].fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
ax[0].set_ylabel('Total invested (EUR)')
ax[0].set_ylim(bottom=0)

ax[1].fill_between(end_dates, 0, dividend_rate + out_rate, label='Capital gain')
ax[1].fill_between(end_dates, 0, dividend_rate, label='Dividends')
ax[1].fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
ax[1].legend(loc='upper left')
ax[1].set_ylabel('Annual rate (%)')

fig.align_ylabels()
plt.show()
