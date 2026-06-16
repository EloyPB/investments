## Investments tracker

Small personal tool to load stock transactions from an Excel file, compute realized returns + IRR, optionally fetch current prices from Yahoo Finance, and view everything in a Streamlit dashboard.

### Requirements

- Python 3
- `transactions.xlsx` (see format below)
- (Optional, for `--download`) `ticker_symbols.xlsx` (see format below)
- Environment variable `INVESTMENTS_DATA_DIR` pointing to the folder containing those spreadsheets 

### Data format

#### `transactions.xlsx`

**Required columns**:
  - `date`: date (yyyy-mm-dd; used as index)
  - `company`: company name (string)
  - `shares`: positive for buys, negative for sells, empty for dividend rows
  - `value`: negative for buys (cash out), positive for sells (cash in), empty for dividend rows
  - `dividend`: cash received (positive), empty for non-dividend rows

#### `ticker_symbols.xlsx` (only needed for price download)

**Required columns (no header)**:

  - `name`: must match the `company` names used in `transactions.xlsx`
  - `ticker`: Yahoo Finance symbol (e.g. `AAPL`, `IBE.MC`)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the data path (example):

```bash
export INVESTMENTS_DATA_DIR="/path/to/data"
```

### Run (CLI)

```bash
python investments.py
python investments.py --download
```

### Run (Dashboard)

```bash
streamlit run app.py
```

### Tests

```bash
pytest -q
```

