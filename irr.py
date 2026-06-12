"""Money-weighted return (XIRR) from irregular cash flows."""

from __future__ import annotations

import datetime
from typing import Optional

import pandas as pd

DAYS_PER_YEAR = 365.25


def _xnpv(rate: float, dates: list[pd.Timestamp], amounts: list[float]) -> float:
    t0 = dates[0]
    return sum(
        amount / (1 + rate) ** ((date - t0).days / DAYS_PER_YEAR)
        for date, amount in zip(dates, amounts)
    )


def xirr(dates: list[pd.Timestamp], amounts: list[float]) -> Optional[float]:
    """Annual IRR that sets NPV of dated cash flows to zero."""
    if not dates or len(dates) != len(amounts):
        return None

    if all(amount >= 0 for amount in amounts) or all(amount <= 0 for amount in amounts):
        return None

    low, high = -0.9999, 10.0
    npv_low = _xnpv(low, dates, amounts)
    npv_high = _xnpv(high, dates, amounts)
    if npv_low * npv_high > 0:
        return None

    for _ in range(200):
        mid = (low + high) / 2
        npv_mid = _xnpv(mid, dates, amounts)
        if abs(npv_mid) < 1e-7:
            return mid
        if npv_mid * npv_low > 0:
            low, npv_low = mid, npv_mid
        else:
            high = mid

    return (low + high) / 2


def terminal_portfolio_value(active: pd.DataFrame) -> tuple[float, int]:
    """Mark-to-market open positions; NaN/missing prices use cost basis (-invested)."""
    if active.empty:
        return 0.0, 0

    if "current value" in active.columns:
        missing = active["current value"].isna()
        n_fallback = int(missing.sum())
        total = active["current value"].fillna(-active["invested"]).sum()
    else:
        n_fallback = len(active)
        total = (-active["invested"]).sum()

    return float(total), n_fallback


def transaction_cash_flows(transactions: pd.DataFrame) -> dict[pd.Timestamp, float]:
    flows: dict[pd.Timestamp, float] = {}
    for date, row in transactions.iterrows():
        amount = 0.0
        if row["value"] != 0:
            amount += row["value"]
        if row.get("dividend", 0):
            amount += row["dividend"]
        if amount:
            ts = pd.Timestamp(date)
            flows[ts] = flows.get(ts, 0.0) + amount
    return flows


def irr_with_terminal(flows: dict[pd.Timestamp, float], terminal: float) -> Optional[float]:
    """IRR for dated cash flows plus a terminal inflow on today."""
    flows = dict(flows)
    if terminal > 0:
        today = pd.Timestamp(datetime.date.today())
        flows[today] = flows.get(today, 0.0) + terminal

    if len(flows) < 2:
        return None

    dates = sorted(flows.keys())
    amounts = [flows[date] for date in dates]
    return xirr(dates, amounts)


def lifetime_irr(transactions: pd.DataFrame, active: pd.DataFrame) -> tuple[Optional[float], float, int]:
    """
    Money-weighted annual return (IRR) including terminal value of open positions.

    Returns (irr, terminal_value, n_positions_at_cost_basis).
    """
    flows = transaction_cash_flows(transactions)
    terminal, n_fallback = terminal_portfolio_value(active)
    return irr_with_terminal(flows, terminal), terminal, n_fallback
