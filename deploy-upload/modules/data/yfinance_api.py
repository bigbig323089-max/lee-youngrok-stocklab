import contextlib
from io import StringIO

import pandas as pd
import streamlit as st
import yfinance as yf

from modules.config import REQUIRED_COLUMNS


def normalize_ticker(ticker):
    ticker = ticker.strip().upper()

    if ticker.isdigit() and len(ticker) == 6:
        return f"{ticker}.KS"

    return ticker


def safe_yfinance_download(**kwargs):
    with contextlib.redirect_stdout(StringIO()), contextlib.redirect_stderr(StringIO()):
        return yf.download(**kwargs)


def normalize_yfinance_data(df, ticker):
    if df is None or df.empty:
        return pd.DataFrame()

    normalized = df.copy()

    if isinstance(normalized.columns, pd.MultiIndex):
        for level in range(normalized.columns.nlevels):
            level_values = normalized.columns.get_level_values(level).astype(str)
            if ticker in set(level_values):
                normalized = normalized.xs(ticker, axis=1, level=level, drop_level=True)
                break

    if isinstance(normalized.columns, pd.MultiIndex):
        flattened_columns = []
        for column in normalized.columns:
            matched = [str(part) for part in column if str(part) in REQUIRED_COLUMNS]
            flattened_columns.append(matched[0] if matched else "_".join(map(str, column)))
        normalized.columns = flattened_columns
    else:
        normalized.columns = [str(column) for column in normalized.columns]

    if not set(REQUIRED_COLUMNS).issubset(normalized.columns):
        return pd.DataFrame()

    normalized = normalized[REQUIRED_COLUMNS].copy()
    normalized.index = pd.to_datetime(normalized.index, errors="coerce")

    if getattr(normalized.index, "tz", None) is not None:
        normalized.index = normalized.index.tz_localize(None)

    for column in REQUIRED_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized = normalized.dropna(subset=["Close"])
    normalized = normalized.sort_index()

    return normalized


def get_yfinance_news(ticker):
    try:
        news = yf.Ticker(normalize_ticker(ticker)).news or []
    except Exception:
        return pd.DataFrame()

    rows = []
    for item in news[:10]:
        publish_time = item.get("providerPublishTime")
        rows.append(
            {
                "제목": item.get("title", ""),
                "매체": item.get("publisher", ""),
                "시간": pd.to_datetime(publish_time, unit="s") if publish_time else pd.NaT,
                "링크": item.get("link", ""),
            }
        )

    return pd.DataFrame(rows)
