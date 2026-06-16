import streamlit as st
import pandas as pd

from load_transactions import load_transactions
from compare_to_index import IndexComparisonResult, compare_to_index
from irr import lifetime_irr
from plots import compute_rolling_returns, plot_invested_plotly, plot_returns_plotly
from formatting import fmt_eur, fmt_number, fmt_pct
from portfolio import active_columns, completed_columns, enrich_active, process_transactions


_MONEY_COLUMNS = {"invested", "dividends", "out", "current value", "change (EUR)"}


def number_column_config(columns: list[str]) -> dict:
    """Sortable numeric display via Streamlit Intl formatting (browser locale)."""
    config = {}
    for col in columns:
        if col in _MONEY_COLUMNS:
            config[col] = st.column_config.NumberColumn(format="euro")
        else:
            config[col] = st.column_config.NumberColumn(format="localized")
    return config


st.set_page_config(layout="wide")


@st.cache_data
def load_and_process():
    transactions, folder_path = load_transactions()
    transactions, shares = process_transactions(transactions)
    return transactions, shares, folder_path


@st.cache_data(ttl=3600)
def fetch_active_prices(shares: pd.DataFrame, folder_path: str) -> pd.DataFrame:
    return enrich_active(shares, folder_path)


@st.cache_data(ttl=3600)
def fetch_index_comparison(transactions: pd.DataFrame, portfolio_irr: float) -> IndexComparisonResult:
    return compare_to_index(transactions, portfolio_irr=portfolio_irr)


try:
    transactions, shares, folder_path = load_and_process()
except (RuntimeError, FileNotFoundError) as e:
    st.error(str(e))
    st.stop()


st.title("Investments")

# --- sidebar ---
st.sidebar.header("Options")
download_prices = st.sidebar.checkbox("Download current prices", value=False)
if download_prices:
    st.sidebar.caption("Prices cached 1 hour. Clear cache in the app menu to refresh.")
else:
    st.sidebar.caption("Open positions at cost basis for IRR.")

st.sidebar.caption(f"Data: `{folder_path}`")

# --- active holdings ---
active_base = shares.loc[shares.shares > 0]
if download_prices:
    with st.spinner("Downloading current prices…"):
        active = fetch_active_prices(active_base, folder_path)
else:
    active = active_base

# --- metrics ---
total = shares[["dividends", "out"]].sum()
realized_total = total["dividends"] + total["out"]
capital_deployed = transactions["invested"].iloc[-1]

unrealized = None
if download_prices and "change (EUR)" in active.columns:
    unrealized = active["change (EUR)"].sum()

irr, terminal_value, n_at_cost = lifetime_irr(transactions, active)

portfolio_total = realized_total + unrealized if unrealized is not None else realized_total
total_help = (
    "Realized (sales + dividends) plus unrealized gains on open positions."
    if unrealized is not None
    else "Realized gains from sales and dividends."
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Capital deployed", fmt_eur(capital_deployed))
c2.metric("Sale gains", fmt_eur(total["out"]))
c3.metric("Dividends", fmt_eur(total["dividends"]))
c4.metric("Total", fmt_eur(portfolio_total), help=total_help)
c5.metric("IRR", fmt_pct(irr * 100) if irr else "n/a")

if irr is not None and n_at_cost:
    st.caption(f"IRR: {n_at_cost} open position(s) without a live price → cost basis.")

# --- tabs ---
tab_active, tab_completed, tab_charts, tab_index = st.tabs(
    ["Active", "Completed", "Charts", "Index comparison"]
)

with tab_active:
    cols = [c for c in active_columns(download_prices) if c in active.columns]
    active_display = active.loc[:, cols].copy()
    if "invested" in active_display.columns:
        # Display convention: invested is shown as a positive cost basis.
        active_display["invested"] = -active_display["invested"]
    st.dataframe(
        active_display.round(2),
        column_config=number_column_config(cols),
        use_container_width=True,
    )

with tab_completed:
    completed = shares.loc[shares.shares <= 0]
    completed_cols = completed_columns()
    st.dataframe(
        completed.loc[:, completed_cols].round(2),
        column_config=number_column_config(completed_cols),
        use_container_width=True,
    )

with tab_charts:
    rolling_data = compute_rolling_returns(transactions)
    st.plotly_chart(plot_invested_plotly(rolling_data), use_container_width=True)
    st.plotly_chart(plot_returns_plotly(rolling_data), use_container_width=True)

with tab_index:
    if not download_prices:
        st.info("Enable price download in the sidebar to compare vs the index.")
    elif irr is None:
        st.info("IRR could not be computed; index comparison is unavailable.")
    else:
        result = fetch_index_comparison(transactions, irr)
        st.write(
            f"If all buy/sell flows had gone into **A500.MI** (Amundi S&P 500), you would have **{fmt_number(result.shares)}** shares "
            f"worth **{fmt_eur(result.current_value, 2)}**, representing a gain of **{fmt_eur(result.gain, 2)}**"
        )
        if result.index_irr is not None:
            diff = (irr - result.index_irr) * 100
            st.write(f"**Index IRR:** {fmt_pct(result.index_irr * 100)} / year")
            st.write(f"**Portfolio vs index IRR:** {fmt_pct(diff, signed=True)} / year")
