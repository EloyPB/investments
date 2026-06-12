import os
import sys
from pathlib import Path

import pandas as pd

ENV_DATA_DIR = "INVESTMENTS_DATA_DIR"


def load_transactions(data_dir: str | None = None) -> tuple[pd.DataFrame, str]:
    """Load transactions.xlsx from data_dir or $INVESTMENTS_DATA_DIR."""
    if data_dir is None:
        data_dir = os.environ.get(ENV_DATA_DIR)

    if not data_dir:
        sys.exit(
            f"Set {ENV_DATA_DIR} to the folder containing transactions.xlsx "
            f"(e.g. export {ENV_DATA_DIR}=/path/to/Documentos)"
        )

    folder_path = Path(data_dir)
    transactions_file_path = folder_path / "transactions.xlsx"

    transactions = pd.read_excel(transactions_file_path, index_col=0)
    transactions.fillna(0, inplace=True)

    return transactions, str(folder_path)
