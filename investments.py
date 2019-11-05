import sys
import pandas as pd

transactions_file_path = "/media/windows/Users/Eloy/MEGA/Documentos/transactions.xlsx"
transactions = pd.read_excel(transactions_file_path, index_col=0,
                             dtype={'date': "datetime64[D]", 'company': str, 'shares': float, 'value': float,
                                    'from_parents': float, 'dividend': float})
transactions.fillna(0, inplace=True)

shares = pd.DataFrame(columns=['company', 'shares', 'invested', 'dividends', 'out'])

for index, transaction in transactions.iterrows():
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
            owned_shares_value = (shares.loc[shares['company'] == transaction.company, 'invested']
                                  / shares.loc[shares['company'] == transaction.company, 'shares'])
            shares.loc[shares['company'] == transaction.company, 'out'] += \
                transaction.value - transaction.shares*owned_shares_value

            shares.loc[shares['company'] == transaction.company, 'shares'] += transaction.shares
            shares.loc[shares['company'] == transaction.company, 'invested'] = \
                shares.loc[shares['company'] == transaction.company, 'shares']*owned_shares_value

    # receive dividend
    elif transaction.dividend:
        shares.loc[shares['company'] == transaction.company, 'dividends'] += transaction.dividend

    else:
        sys.exit(f"Invalid transaction type in row {index}")

print(shares)
