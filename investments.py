#!/usr/bin/env python3

import sys
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# import http.client as httplib
# import nasdaqdatalink


pd.set_option("display.max_rows", None, "display.max_columns", None)

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
    if transaction.shares > 0 and transaction.company not in shares.company.values:
        new_row = pd.DataFrame({'company': [transaction.company], 'shares': [transaction.shares],
                                'invested': [transaction.value], 'dividends': [0], 'out': [0]})
        shares = pd.concat((shares, new_row), ignore_index=True)

    # buy more shares
    elif transaction.shares > 0:
        shares.loc[shares['company'] == transaction.company, 'shares'] += transaction.shares
        shares.loc[shares['company'] == transaction.company, 'invested'] += transaction.value

    # sell shares
    elif transaction.shares < 0:
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

print(shares.round(2))
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

fig, ax = plt.subplots(2, sharex='col', figsize=(7, 6), gridspec_kw={'height_ratios': (0.6, 1)})

ax[0].plot(end_dates, -np.array(invested))
ax[0].fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
ax[0].set_ylabel('Total invested (EUR)')
ax[0].set_ylim(bottom=0)

ax[1].fill_between(end_dates, 0, out_rate, label='Completed transactions', facecolor='C0', edgecolor='k')
ax[1].fill_between(end_dates, out_rate, out_rate + dividend_rate, label='Dividends', facecolor='C2', edgecolor='k')
mean_return = np.mean(out_rate + dividend_rate)
ax[1].plot((end_dates[0], end_dates[-1]), [mean_return]*2, linestyle='dashed', color='C7', label="mean annual return")
ax[1].fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
ax[1].set_ylabel('Annual return (%)')


# # if there is an active internet connection, try to get inflation data using nasdaq data link
# def have_internet():
#     conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
#     try:
#         conn.request("HEAD", "/")
#         return True
#     except OSError:
#         return False
#     finally:
#         conn.close()
#
#
# if have_internet():
#     inflation = nasdaqdatalink.get("RATEINF/INFLATION_EUR", start_date=end_dates[0].strftime("%Y-%m-%d"))
#     ax[1].plot(inflation, color='k', linestyle='dotted', label="inflation euro area")

ax[1].legend(loc='upper left')
fig.align_ylabels()
fig.tight_layout()
plt.show()
