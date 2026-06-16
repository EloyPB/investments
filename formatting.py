"""European number formatting: 1.234,56 (dot thousands, comma decimals)."""

from __future__ import annotations

import pandas as pd


def fmt_number(value: float, decimals: int = 2) -> str:
    formatted = f"{float(value):,.{decimals}f}"
    return formatted.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def fmt_eur(value: float, decimals: int = 0) -> str:
    return f"{fmt_number(value, decimals)} €"


def fmt_pct(value: float, decimals: int = 2, signed: bool = False) -> str:
    if signed and value > 0:
        return f"+{fmt_number(value, decimals)}%"
    return f"{fmt_number(value, decimals)}%"


def format_df(df: pd.DataFrame, decimals: int = 2) -> pd.DataFrame:
    """Return a copy with numeric columns formatted as strings."""
    out = df.copy()
    for col in out.select_dtypes(include="number").columns:
        out[col] = out[col].map(lambda x: fmt_number(x, decimals) if pd.notna(x) else "")
    return out


def format_df_text(df: pd.DataFrame, decimals: int = 2) -> str:
    return format_df(df, decimals).to_string()
