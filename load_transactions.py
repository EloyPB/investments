from socket import gethostname
import pandas as pd
import sys


def load_transactions():
    host_name = gethostname()
    if host_name == "etp":
        transactions_file_path = "/c/DATA/CLOUD/Documentos/transactions.xlsx"
    elif host_name == "INRC-MPRIDA-17":
        transactions_file_path = "/home/eloy/CLOUD/Documentos/transactions.xlsx"
    else:
        sys.exit("host not recognized")

    transactions = pd.read_excel(transactions_file_path, index_col=0)
    transactions.fillna(0, inplace=True)

    return transactions
