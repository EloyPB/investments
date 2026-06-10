from pathlib import Path
from socket import gethostname
import sys

import pandas as pd


def load_transactions():
    host_name = gethostname()
    if host_name == "etp":
        folder_path = Path("/c/DATA/CLOUD/Documentos")
    else:
        sys.exit("host not recognized")

    transactions_file_path = folder_path / "transactions.xlsx"

    transactions = pd.read_excel(transactions_file_path, index_col=0)
    transactions.fillna(0, inplace=True)

    return transactions, str(folder_path)
