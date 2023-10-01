from socket import gethostname
import pandas as pd
import sys


def load_transactions():
    host_name = gethostname()
    if host_name == "etp":
        folder_path = "/c/DATA/CLOUD/Documentos"
    elif host_name == "INRC-MPRIDA-17":
        folder_path = "/home/eloy/CLOUD/Documentos"
    else:
        sys.exit("host not recognized")

    transactions_file_path = f"{folder_path}//transactions.xlsx"

    transactions = pd.read_excel(transactions_file_path, index_col=0)
    transactions.fillna(0, inplace=True)

    return transactions, folder_path
