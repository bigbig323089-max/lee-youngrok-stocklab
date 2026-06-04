import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf


st.set_page_config(
    page_title="이영록 스톡랩",
    layout="wide",
)


REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
SIGNAL_COLUMNS = [
    "Close",
    "Volume",
    "MA5",
    "MA20",
    "MA60",
    "Volume_MA20",
    "RSI",
    "MACD",
    "MACD_Signal",
    "MACD_Histogram",
    "Bollinger_Middle",
    "Bollinger_Upper",
    "Bollinger_Lower",
    "ADX",
    "ATR",
    "ATR_Ratio",
    "OBV",
    "OBV_MA20",
]


def normalize_ticker(ticker):
    ticker = ticker.strip().upper()

    if ticker.isdigit() and len(ticker) == 6:
        return f"{ticker}.KS"

    return ticker


def enable_auto_refresh(minutes=30):
    refresh_ms = minutes * 60 * 1000
    components.html(
        f"""
        <script>
            setTimeout(function() {{
                window.parent.location.reload();
            }}, {refresh_ms});
        </script>
        """,
        height=0,
    )


def load_custom_css():
    st.markdown(
        """
        <style>
            :root {
                --bg: #f6f8fb;
                --panel: #ffffff;
                --line: #e5e7eb;
                --text: #111827;
                --muted: #6b7280;
                --blue: #2563eb;
                --green: #16a34a;
                --red: #dc2626;
                --amber: #d97706;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 32rem),
                    linear-gradient(180deg, #f8fafc 0%, var(--bg) 100%);
                color: var(--text);
            }

            .block-container {
                max-width: 1360px;
                padding-top: 1.7rem;
                padding-bottom: 3rem;
            }

            section[data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid var(--line);
            }

            section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.75rem;
            }

            .hero {
                background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #2563eb 100%);
                border-radius: 18px;
                padding: 28px 30px;
                color: #ffffff;
                box-shadow: 0 18px 48px rgba(15, 23, 42, 0.18);
                margin-bottom: 22px;
            }

            .hero .eyebrow {
                font-size: 0.82rem;
                letter-spacing: 0.08em;
                opacity: 0.78;
                margin-bottom: 8px;
                font-weight: 700;
            }

            .hero h1 {
                margin: 0 0 10px 0;
                font-size: 2rem;
                line-height: 1.25;
                font-weight: 800;
            }

            .hero p {
                margin: 0;
                color: rgba(255, 255, 255, 0.86);
                line-height: 1.65;
                max-width: 920px;
            }

            .notice-row {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                margin-top: 18px;
            }

            .notice {
                border: 1px solid rgba(255, 255, 255, 0.18);
                background: rgba(255, 255, 255, 0.10);
                border-radius: 12px;
                padding: 12px 14px;
                color: rgba(255, 255, 255, 0.92);
                font-size: 0.94rem;
                line-height: 1.5;
            }

            .metric-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin-bottom: 10px;
            }

            .metric-card {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 12px;
                padding: 12px 13px;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
                min-height: 82px;
                text-align: left;
                overflow: hidden;
            }

            .metric-card .label {
                font-size: 0.78rem;
                color: var(--muted);
                font-weight: 700;
                margin-bottom: 6px;
                white-space: nowrap;
            }

            .metric-card .value {
                font-size: clamp(1.18rem, 1.7vw, 1.48rem);
                font-weight: 800;
                color: var(--text);
                line-height: 1.18;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .metric-card .sub {
                margin-top: 5px;
                font-size: 0.75rem;
                color: var(--muted);
                line-height: 1.25;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .signal-badge {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 7px 11px;
                font-weight: 800;
                font-size: 0.92rem;
                white-space: nowrap;
            }

            .signal-good {
                background: #dcfce7;
                color: #166534;
            }

            .signal-neutral {
                background: #fef9c3;
                color: #854d0e;
            }

            .signal-bad {
                background: #fee2e2;
                color: #991b1b;
            }

            .basis-card {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 12px;
                padding: 10px 13px;
                box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
                margin: 6px 0 16px 0;
                color: #374151;
                line-height: 1.45;
                font-size: 0.92rem;
            }

            .empty-guide {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 22px 24px;
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
                margin-top: 16px;
            }

            .empty-guide h3 {
                margin: 0 0 8px 0;
                font-size: 1.15rem;
            }

            .empty-guide p {
                color: var(--muted);
                margin: 0;
                line-height: 1.65;
            }

            .stButton > button {
                border-radius: 10px;
                font-weight: 800;
                min-height: 42px;
            }

            div[data-testid="stMetric"] {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 14px;
                padding: 14px 16px;
                box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
            }

            div[data-testid="stTabs"] button {
                font-weight: 800;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid var(--line);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 10px 26px rgba(15, 23, 42, 0.04);
            }

            @media (max-width: 900px) {
                .notice-row,
                .metric-grid {
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                }

                .hero {
                    padding: 22px 20px;
                }

                .hero h1 {
                    font-size: 1.55rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_stock_code(ticker):
    normalized = normalize_ticker(ticker)
    code = normalized.split(".")[0]

    if code.isdigit() and len(code) == 6:
        return code

    return None


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


@st.cache_data(ttl=60 * 30, show_spinner=False)
def get_daily_data(ticker, period):
    ticker = normalize_ticker(ticker)

    df = yf.download(
        tickers=ticker,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    return normalize_yfinance_data(df, ticker)


@st.cache_data(ttl=60 * 5, show_spinner=False)
def get_intraday_data(ticker, interval):
    ticker = normalize_ticker(ticker)
    period = "1d" if interval == "1m" else "5d"

    df = yf.download(
        tickers=ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    return normalize_yfinance_data(df, ticker)


def get_latest_intraday_session(df):
    if df is None or df.empty:
        return pd.DataFrame()

    session_df = df.dropna(subset=["Close"]).copy()

    if session_df.empty:
        return session_df

    session_dates = pd.Series(session_df.index.date, index=session_df.index)
    latest_date = session_dates.iloc[-1]

    return session_df.loc[session_dates == latest_date].copy()


def calculate_intraday_indicators(df):
    if df is None or df.empty:
        return pd.DataFrame()

    analyzed = df.copy()
    session_dates = pd.Series(analyzed.index.date, index=analyzed.index)

    analyzed["Intraday_MA5"] = analyzed.groupby(session_dates)["Close"].transform(
        lambda series: series.rolling(window=5, min_periods=1).mean()
    )
    analyzed["Intraday_MA20"] = analyzed.groupby(session_dates)["Close"].transform(
        lambda series: series.rolling(window=20, min_periods=1).mean()
    )
    analyzed["Intraday_Volume_MA20"] = analyzed.groupby(session_dates)["Volume"].transform(
        lambda series: series.rolling(window=20, min_periods=1).mean()
    )

    typical_price = (analyzed["High"] + analyzed["Low"] + analyzed["Close"]) / 3
    price_volume = typical_price * analyzed["Volume"]
    cumulative_price_volume = price_volume.groupby(session_dates).cumsum()
    cumulative_volume = analyzed["Volume"].groupby(session_dates).cumsum()
    analyzed["VWAP"] = cumulative_price_volume / cumulative_volume.replace(0, np.nan)

    return analyzed


def score_to_intraday_signal(score):
    if score <= 2:
        return "당일 약세 강함"
    if score <= 4:
        return "당일 약세"
    if score <= 6:
        return "당일 중립"
    if score <= 8:
        return "당일 우세"
    return "당일 우세 강함"


def calculate_intraday_signal(df, interval="-"):
    analyzed = calculate_intraday_indicators(df)
    session_df = get_latest_intraday_session(analyzed)

    if session_df.empty:
        return {
            "flow_score": None,
            "flow_signal": "분석 불가",
            "interval": interval,
            "comments": ["분봉 데이터가 비어 있어 당일 흐름을 계산할 수 없습니다."],
            "score_details": pd.DataFrame(),
        }

    latest = session_df.iloc[-1]
    first = session_df.iloc[0]
    day_open = first["Open"]
    latest_close = latest["Close"]
    day_high = session_df["High"].max()
    day_low = session_df["Low"].min()
    day_volume = session_df["Volume"].sum()
    day_change = latest_close / day_open - 1 if day_open else np.nan
    day_range = (day_high - day_low) / day_open if day_open else np.nan
    range_position = (latest_close - day_low) / (day_high - day_low) if day_high != day_low else 0.5
    momentum_5 = latest_close / session_df["Close"].iloc[-6] - 1 if len(session_df) >= 6 else np.nan
    volume_ratio = latest["Volume"] / latest["Intraday_Volume_MA20"] if latest["Intraday_Volume_MA20"] else np.nan

    score_rows = []
    comments = []

    def add_score(item, score, comment, weight=1.0):
        score = clamp_score(score)
        score_rows.append(
            {
                "평가 항목": item,
                "점수": score,
                "가중치": weight,
                "판정": score_to_intraday_signal(score),
                "해석": comment,
            }
        )
        comments.append(f"{item}: {comment} ({score}/10)")

    change_score = 5
    change_comment = "시가 대비 등락률이 중립에 가깝습니다."
    if pd.notna(day_change):
        if day_change >= 0.02:
            change_score = 9
            change_comment = "시가 대비 상승 폭이 큰 편입니다."
        elif day_change >= 0.007:
            change_score = 8
            change_comment = "시가 대비 상승 흐름이 우세합니다."
        elif day_change > 0:
            change_score = 7
            change_comment = "시가 대비 소폭 상승 흐름입니다."
        elif day_change <= -0.02:
            change_score = 2
            change_comment = "시가 대비 하락 폭이 큰 편입니다."
        elif day_change <= -0.007:
            change_score = 3
            change_comment = "시가 대비 하락 흐름이 우세합니다."
        elif day_change < 0:
            change_score = 4
            change_comment = "시가 대비 소폭 약세 흐름입니다."
    add_score("당일 등락률", change_score, change_comment, 1.3)

    ma_score = 5
    ma_comment = "분봉 이동평균 흐름이 중립에 가깝습니다."
    if latest_close > latest["Intraday_MA5"] > latest["Intraday_MA20"]:
        ma_score = 8
        ma_comment = "최근 분봉 종가가 MA5와 MA20 위에 있어 단기 흐름이 우호적입니다."
    elif latest_close > latest["Intraday_MA20"] and latest["Intraday_MA5"] >= latest["Intraday_MA20"]:
        ma_score = 7
        ma_comment = "분봉 MA5가 MA20 위에 있고 가격도 중기선 위에 있습니다."
    elif latest_close < latest["Intraday_MA5"] < latest["Intraday_MA20"]:
        ma_score = 3
        ma_comment = "최근 분봉 종가가 MA5와 MA20 아래에 있어 단기 흐름이 약합니다."
    elif latest_close < latest["Intraday_MA20"] and latest["Intraday_MA5"] <= latest["Intraday_MA20"]:
        ma_score = 4
        ma_comment = "분봉 MA5가 MA20 아래에 있고 가격도 중기선 아래에 있습니다."
    add_score("분봉 이동평균", ma_score, ma_comment, 1.2)

    vwap_score = 5
    vwap_comment = "최근 가격이 VWAP 근처에 있어 중립적입니다."
    if pd.notna(latest["VWAP"]):
        vwap_gap = latest_close / latest["VWAP"] - 1
        if vwap_gap >= 0.01:
            vwap_score = 8
            vwap_comment = "최근 가격이 VWAP보다 뚜렷하게 높아 당일 매수 흐름이 우세합니다."
        elif vwap_gap > 0:
            vwap_score = 7
            vwap_comment = "최근 가격이 VWAP 위에 있어 당일 흐름이 우호적입니다."
        elif vwap_gap <= -0.01:
            vwap_score = 3
            vwap_comment = "최근 가격이 VWAP보다 뚜렷하게 낮아 당일 약세 압력이 있습니다."
        elif vwap_gap < 0:
            vwap_score = 4
            vwap_comment = "최근 가격이 VWAP 아래에 있어 당일 흐름이 약한 편입니다."
    add_score("VWAP 위치", vwap_score, vwap_comment, 1.2)

    position_score = 5
    position_comment = "최근 가격이 당일 변동 범위 중간권에 있습니다."
    if range_position >= 0.85:
        position_score = 8
        position_comment = "최근 가격이 당일 고가권에 가까워 당일 흐름이 강합니다."
    elif range_position >= 0.65:
        position_score = 7
        position_comment = "최근 가격이 당일 범위 상단 쪽에 있습니다."
    elif range_position <= 0.15:
        position_score = 3
        position_comment = "최근 가격이 당일 저가권에 가까워 당일 흐름이 약합니다."
    elif range_position <= 0.35:
        position_score = 4
        position_comment = "최근 가격이 당일 범위 하단 쪽에 있습니다."
    add_score("당일 고저점 위치", position_score, position_comment, 1.0)

    momentum_score = 5
    momentum_comment = "최근 5개 분봉 모멘텀이 중립에 가깝습니다."
    if pd.notna(momentum_5):
        if momentum_5 >= 0.01:
            momentum_score = 8
            momentum_comment = "최근 5개 분봉 기준 상승 모멘텀이 뚜렷합니다."
        elif momentum_5 > 0:
            momentum_score = 7
            momentum_comment = "최근 5개 분봉 기준 소폭 상승 모멘텀이 있습니다."
        elif momentum_5 <= -0.01:
            momentum_score = 3
            momentum_comment = "최근 5개 분봉 기준 하락 모멘텀이 뚜렷합니다."
        elif momentum_5 < 0:
            momentum_score = 4
            momentum_comment = "최근 5개 분봉 기준 소폭 약세 모멘텀입니다."
    add_score("단기 모멘텀", momentum_score, momentum_comment, 1.0)

    previous_close = session_df["Close"].iloc[-2] if len(session_df) >= 2 else latest_close
    volume_score = 5
    volume_comment = "최근 분봉 거래량이 평균 수준입니다."
    if pd.notna(volume_ratio):
        if volume_ratio >= 1.5 and latest_close >= previous_close:
            volume_score = 8
            volume_comment = "최근 거래량이 평균보다 크고 가격도 버티는 흐름입니다."
        elif volume_ratio >= 1.2 and latest_close >= previous_close:
            volume_score = 7
            volume_comment = "평균보다 높은 거래량에서 가격이 우호적으로 움직였습니다."
        elif volume_ratio >= 1.2 and latest_close < previous_close:
            volume_score = 3
            volume_comment = "거래량이 늘었지만 최근 분봉 가격이 밀려 약세 압력을 참고해야 합니다."
        elif volume_ratio < 0.7:
            volume_score = 5
            volume_comment = "거래량이 낮아 당일 흐름 판단 신뢰도가 제한될 수 있습니다."
    add_score("분봉 거래량", volume_score, volume_comment, 0.8)

    score_details = pd.DataFrame(score_rows)
    weighted_score = np.average(score_details["점수"], weights=score_details["가중치"])
    flow_score = clamp_score(weighted_score)

    return {
        "flow_score": flow_score,
        "flow_signal": score_to_intraday_signal(flow_score),
        "interval": interval,
        "basis_time": latest.name.strftime("%Y-%m-%d %H:%M"),
        "day_open": day_open,
        "latest_close": latest_close,
        "day_change": day_change,
        "day_high": day_high,
        "day_low": day_low,
        "day_volume": day_volume,
        "vwap": latest["VWAP"],
        "ma5": latest["Intraday_MA5"],
        "ma20": latest["Intraday_MA20"],
        "day_range": day_range,
        "comments": comments,
        "score_details": score_details,
    }


def calculate_indicators(df):
    analyzed = df.copy()

    analyzed["MA5"] = analyzed["Close"].rolling(window=5).mean()
    analyzed["MA20"] = analyzed["Close"].rolling(window=20).mean()
    analyzed["MA60"] = analyzed["Close"].rolling(window=60).mean()
    analyzed["Volume_MA20"] = analyzed["Volume"].rolling(window=20).mean()

    delta = analyzed["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    analyzed["RSI"] = 100 - (100 / (1 + rs))
    analyzed["RSI"] = analyzed["RSI"].mask((avg_loss == 0) & (avg_gain > 0), 100)
    analyzed["RSI"] = analyzed["RSI"].mask((avg_gain == 0) & (avg_loss > 0), 0)
    analyzed["RSI"] = analyzed["RSI"].mask((avg_gain == 0) & (avg_loss == 0), 50)
    analyzed["RSI"] = analyzed["RSI"].replace([np.inf, -np.inf], np.nan)

    ema12 = analyzed["Close"].ewm(span=12, adjust=False).mean()
    ema26 = analyzed["Close"].ewm(span=26, adjust=False).mean()
    analyzed["MACD"] = ema12 - ema26
    analyzed["MACD_Signal"] = analyzed["MACD"].ewm(span=9, adjust=False).mean()
    analyzed["MACD_Histogram"] = analyzed["MACD"] - analyzed["MACD_Signal"]

    analyzed["Bollinger_Middle"] = analyzed["Close"].rolling(window=20).mean()
    bollinger_std = analyzed["Close"].rolling(window=20).std()
    analyzed["Bollinger_Upper"] = analyzed["Bollinger_Middle"] + (bollinger_std * 2)
    analyzed["Bollinger_Lower"] = analyzed["Bollinger_Middle"] - (bollinger_std * 2)

    high_low = analyzed["High"] - analyzed["Low"]
    high_close = (analyzed["High"] - analyzed["Close"].shift(1)).abs()
    low_close = (analyzed["Low"] - analyzed["Close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    analyzed["ATR"] = true_range.rolling(window=14).mean()
    analyzed["ATR_Ratio"] = analyzed["ATR"] / analyzed["Close"]

    high_diff = analyzed["High"].diff()
    low_diff = -analyzed["Low"].diff()
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
    plus_di = 100 * pd.Series(plus_dm, index=analyzed.index).rolling(window=14).mean() / analyzed["ATR"]
    minus_di = 100 * pd.Series(minus_dm, index=analyzed.index).rolling(window=14).mean() / analyzed["ATR"]
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di)).replace([np.inf, -np.inf], np.nan)
    analyzed["ADX"] = dx.rolling(window=14).mean()

    direction = np.sign(analyzed["Close"].diff()).fillna(0)
    analyzed["OBV"] = (direction * analyzed["Volume"]).cumsum()
    analyzed["OBV_MA20"] = analyzed["OBV"].rolling(window=20).mean()

    return analyzed


def score_to_signal(score):
    if score <= 2:
        return "매도 우세 강함"
    if score <= 4:
        return "매도 우세"
    if score <= 6:
        return "관망 구간"
    if score <= 8:
        return "매수 우세"
    return "매수 우세 강함"


def clamp_score(score):
    return int(max(1, min(10, round(score))))


def get_risk_level(latest):
    atr_ratio = latest["ATR_Ratio"]

    if pd.isna(atr_ratio):
        return "변동성 판단 불가", "ATR 계산에 필요한 데이터가 부족합니다."
    if atr_ratio >= 0.06:
        return "높음", "최근 평균 변동폭이 큰 편이므로 진입 시점과 비중 관리에 주의가 필요합니다."
    if atr_ratio >= 0.035:
        return "보통", "변동성이 보통 이상입니다. 신호를 단독으로 해석하지 않는 편이 좋습니다."
    return "낮음", "최근 변동성이 비교적 안정적인 편입니다."


def get_signal_badge_class(score):
    if score <= 4:
        return "signal-bad"
    if score <= 6:
        return "signal-neutral"
    return "signal-good"


def calculate_signal(df):
    valid_df = df.dropna(subset=SIGNAL_COLUMNS)

    if len(valid_df) < 2:
        return {
            "technical_score": None,
            "signal": "분석 불가",
            "risk_level": "판단 불가",
            "risk_comment": "기술적 지표 계산에 필요한 데이터가 부족합니다.",
            "reasons": ["기술적 지표 계산에 필요한 데이터가 부족합니다."],
            "score_details": pd.DataFrame(),
        }

    reasons = []
    score_rows = []
    today = valid_df.iloc[-1]
    yesterday = valid_df.iloc[-2]
    recent = valid_df.tail(5)

    def add_score(item, score, comment, weight=1.0):
        score = clamp_score(score)
        score_rows.append(
            {
                "평가 항목": item,
                "점수": score,
                "가중치": weight,
                "판정": score_to_signal(score),
                "해석": comment,
            }
        )
        reasons.append(f"{item}: {comment} ({score}/10)")

    ma_alignment_score = 5
    ma_comment = "단기와 중기 이동평균선이 뚜렷하게 우세하지 않은 중립 구간입니다."
    if today["MA5"] > today["MA20"] > today["MA60"]:
        ma_alignment_score = 9
        ma_comment = "MA5 > MA20 > MA60 배열로 상승 추세 정렬이 좋습니다."
    elif today["MA5"] > today["MA20"]:
        ma_alignment_score = 7
        ma_comment = "MA5가 MA20보다 높아 단기 흐름이 우호적입니다."
    elif today["MA5"] < today["MA20"] < today["MA60"]:
        ma_alignment_score = 2
        ma_comment = "MA5 < MA20 < MA60 배열로 하락 추세 정렬이 강합니다."
    elif today["MA5"] < today["MA20"]:
        ma_alignment_score = 4
        ma_comment = "MA5가 MA20보다 낮아 단기 흐름이 약합니다."
    add_score("이동평균 배열", ma_alignment_score, ma_comment, 1.2)

    cross_score = 5
    cross_comment = "최근 이동평균선 교차 신호가 뚜렷하지 않습니다."
    if yesterday["MA5"] <= yesterday["MA20"] and today["MA5"] > today["MA20"]:
        cross_score = 9
        cross_comment = "MA5가 MA20을 상향 돌파해 골든크로스 성격의 신호가 있습니다."
    elif yesterday["MA5"] >= yesterday["MA20"] and today["MA5"] < today["MA20"]:
        cross_score = 2
        cross_comment = "MA5가 MA20을 하향 돌파해 데드크로스 성격의 신호가 있습니다."
    add_score("이동평균 교차", cross_score, cross_comment, 0.9)

    rsi_score = 5
    rsi_comment = "RSI가 중립 구간에 있습니다."
    if today["RSI"] <= 25:
        rsi_score = 8
        rsi_comment = "RSI가 깊은 과매도권에 있어 반등 가능성을 참고할 수 있습니다."
    elif today["RSI"] <= 30:
        rsi_score = 7
        rsi_comment = "RSI가 과매도 구간에 가깝습니다."
    elif today["RSI"] <= 50:
        rsi_score = 6
        rsi_comment = "RSI가 과열되지 않은 중립 이하 구간입니다."
    elif today["RSI"] >= 75:
        rsi_score = 2
        rsi_comment = "RSI가 높은 과매수권에 있어 단기 과열 주의가 필요합니다."
    elif today["RSI"] >= 70:
        rsi_score = 3
        rsi_comment = "RSI가 과매수 구간에 가깝습니다."
    elif today["RSI"] >= 60:
        rsi_score = 6
        rsi_comment = "RSI가 상승 탄력을 보이나 과열 여부를 함께 봐야 합니다."
    add_score("RSI", rsi_score, rsi_comment, 1.0)

    macd_score = 5
    macd_comment = "MACD가 중립에 가까운 흐름입니다."
    if today["MACD"] > today["MACD_Signal"] and today["MACD_Histogram"] > 0:
        macd_score = 7
        macd_comment = "MACD가 Signal 위에 있고 Histogram도 양수라 모멘텀이 우호적입니다."
    if yesterday["MACD"] <= yesterday["MACD_Signal"] and today["MACD"] > today["MACD_Signal"]:
        macd_score = 9
        macd_comment = "MACD가 Signal을 상향 돌파해 모멘텀 전환 신호가 있습니다."
    if today["MACD"] < today["MACD_Signal"] and today["MACD_Histogram"] < 0:
        macd_score = 4
        macd_comment = "MACD가 Signal 아래에 있고 Histogram도 음수라 모멘텀이 약합니다."
    if yesterday["MACD"] >= yesterday["MACD_Signal"] and today["MACD"] < today["MACD_Signal"]:
        macd_score = 2
        macd_comment = "MACD가 Signal을 하향 돌파해 모멘텀 약화 신호가 있습니다."
    add_score("MACD", macd_score, macd_comment, 1.2)

    volume_ratio = today["Volume"] / today["Volume_MA20"] if today["Volume_MA20"] else np.nan
    volume_score = 5
    volume_comment = "거래량이 평균 수준에 가깝습니다."
    if pd.notna(volume_ratio) and volume_ratio >= 1.5 and today["Close"] > yesterday["Close"]:
        volume_score = 8
        volume_comment = "평균보다 크게 증가한 거래량과 가격 상승이 함께 나타났습니다."
    elif pd.notna(volume_ratio) and volume_ratio > 1 and today["Close"] > yesterday["Close"]:
        volume_score = 7
        volume_comment = "평균보다 높은 거래량에서 가격이 상승했습니다."
    elif today["Volume"] > yesterday["Volume"] and today["Close"] < yesterday["Close"]:
        volume_score = 3
        volume_comment = "거래량은 늘었지만 가격이 하락해 매도 압력을 주의해야 합니다."
    elif pd.notna(volume_ratio) and volume_ratio < 0.7:
        volume_score = 4
        volume_comment = "거래량이 평균보다 낮아 신호 신뢰도가 제한될 수 있습니다."
    add_score("거래량", volume_score, volume_comment, 0.9)

    band_position = (today["Close"] - today["Bollinger_Lower"]) / (today["Bollinger_Upper"] - today["Bollinger_Lower"])
    bollinger_score = 5
    bollinger_comment = "종가가 볼린저 밴드 중간권에 있습니다."
    if band_position <= 0.05:
        bollinger_score = 8
        bollinger_comment = "종가가 볼린저 밴드 하단권에 있어 과매도 가능성을 참고할 수 있습니다."
    elif band_position <= 0.25:
        bollinger_score = 7
        bollinger_comment = "종가가 볼린저 밴드 하단 쪽에 가까워 반등 여지를 참고할 수 있습니다."
    elif band_position >= 0.95:
        bollinger_score = 2
        bollinger_comment = "종가가 볼린저 밴드 상단권에 있어 단기 과열 가능성이 있습니다."
    elif band_position >= 0.75:
        bollinger_score = 4
        bollinger_comment = "종가가 볼린저 밴드 상단 쪽에 가까워 추격 진입은 주의가 필요합니다."
    add_score("볼린저 밴드", bollinger_score, bollinger_comment, 0.9)

    adx_score = 5
    adx_comment = "ADX 기준 추세 강도는 중립 수준입니다."
    if today["ADX"] >= 25 and today["MA5"] > today["MA20"] and today["MACD"] > today["MACD_Signal"]:
        adx_score = 8
        adx_comment = "ADX가 25 이상이고 상승 조건이 함께 나타나 추세 신뢰도가 높아집니다."
    elif today["ADX"] >= 25 and today["MA5"] < today["MA20"] and today["MACD"] < today["MACD_Signal"]:
        adx_score = 3
        adx_comment = "ADX가 25 이상이지만 하락 조건이 함께 나타나 약세 추세를 주의해야 합니다."
    elif today["ADX"] < 18:
        adx_score = 5
        adx_comment = "ADX가 낮아 뚜렷한 추세보다 횡보 가능성이 큽니다."
    add_score("ADX 추세 강도", adx_score, adx_comment, 1.0)

    atr_score = 6
    atr_comment = "ATR 기준 변동성은 감내 가능한 범위로 보입니다."
    if today["ATR_Ratio"] >= 0.08:
        atr_score = 2
        atr_comment = "ATR 비율이 매우 높아 변동성 리스크가 큽니다."
    elif today["ATR_Ratio"] >= 0.06:
        atr_score = 3
        atr_comment = "ATR 비율이 높은 편이라 보수적인 해석이 필요합니다."
    elif today["ATR_Ratio"] >= 0.035:
        atr_score = 5
        atr_comment = "ATR 비율이 보통 이상이라 변동성 관리를 함께 봐야 합니다."
    elif today["ATR_Ratio"] <= 0.015:
        atr_score = 7
        atr_comment = "ATR 비율이 낮아 가격 변동성이 비교적 안정적입니다."
    add_score("ATR 변동성", atr_score, atr_comment, 0.8)

    obv_score = 5
    obv_comment = "OBV 누적 흐름은 중립에 가깝습니다."
    if today["OBV"] > today["OBV_MA20"] and today["OBV"] > yesterday["OBV"]:
        obv_score = 8
        obv_comment = "OBV가 20일 평균보다 높고 상승 중이라 누적 거래 흐름이 우호적입니다."
    elif today["OBV"] < today["OBV_MA20"] and today["OBV"] < yesterday["OBV"]:
        obv_score = 3
        obv_comment = "OBV가 20일 평균보다 낮고 하락 중이라 누적 거래 흐름이 약합니다."
    if len(recent) == 5:
        price_change_5 = recent["Close"].iloc[-1] / recent["Close"].iloc[0] - 1
        obv_change_5 = recent["OBV"].iloc[-1] - recent["OBV"].iloc[0]
        if price_change_5 > 0 and obv_change_5 < 0:
            obv_score = min(obv_score, 4)
            obv_comment = "최근 가격 상승에 비해 OBV가 따라오지 않아 상승 신뢰도가 제한됩니다."
        elif price_change_5 < 0 and obv_change_5 > 0:
            obv_score = max(obv_score, 7)
            obv_comment = "최근 가격은 약했지만 OBV가 개선되어 누적 매수 흐름을 참고할 수 있습니다."
    add_score("OBV", obv_score, obv_comment, 1.0)

    score_details = pd.DataFrame(score_rows)
    weighted_score = np.average(score_details["점수"], weights=score_details["가중치"])
    technical_score = clamp_score(weighted_score)
    risk_level, risk_comment = get_risk_level(today)

    return {
        "technical_score": technical_score,
        "signal": score_to_signal(technical_score),
        "risk_level": risk_level,
        "risk_comment": risk_comment,
        "reasons": reasons,
        "score_details": score_details,
    }


def build_signal_history(df):
    rows = []

    for i in range(60, len(df)):
        sliced = df.iloc[: i + 1]
        result = calculate_signal(sliced)

        if result["technical_score"] is None:
            continue

        latest = sliced.dropna(subset=SIGNAL_COLUMNS).iloc[-1]
        rows.append(
            {
                "Date": latest.name,
                "Close": latest["Close"],
                "기술적 점수": result["technical_score"],
                "보조 판단": result["signal"],
            }
        )

    return pd.DataFrame(rows)


def run_backtest(df, signal_history):
    if signal_history.empty:
        return pd.DataFrame(), {}

    closes = df["Close"]
    rows = []

    for _, signal_row in signal_history.iterrows():
        signal = signal_row["보조 판단"]

        if signal not in ["매수 우세", "매수 우세 강함"]:
            continue

        signal_date = signal_row["Date"]

        if signal_date not in closes.index:
            continue

        position = closes.index.get_loc(signal_date)

        if not isinstance(position, int):
            continue

        entry = closes.iloc[position]
        future_5 = closes.iloc[position + 5] if position + 5 < len(closes) else np.nan
        future_20 = closes.iloc[position + 20] if position + 20 < len(closes) else np.nan
        future_window = closes.iloc[position : min(position + 21, len(closes))]
        max_drawdown = (future_window.min() / entry - 1) if len(future_window) > 0 else np.nan

        rows.append(
            {
                "신호 날짜": signal_date,
                "신호": signal,
                "진입 기준 종가": entry,
                "5거래일 수익률": future_5 / entry - 1 if pd.notna(future_5) else np.nan,
                "20거래일 수익률": future_20 / entry - 1 if pd.notna(future_20) else np.nan,
                "20거래일 내 최대 하락률": max_drawdown,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result, {}

    summary = {
        "매수 우세 신호 발생 횟수": len(result),
        "5거래일 평균 수익률": result["5거래일 수익률"].mean(),
        "20거래일 평균 수익률": result["20거래일 수익률"].mean(),
        "5거래일 승률": (result["5거래일 수익률"] > 0).mean(),
        "20거래일 승률": (result["20거래일 수익률"] > 0).mean(),
        "평균 최대 하락률": result["20거래일 내 최대 하락률"].mean(),
    }

    return result, summary


def format_price(value):
    if pd.isna(value):
        return "-"
    return f"{value:,.2f}"


def format_percent(value):
    if pd.isna(value):
        return "-"
    return f"{value * 100:,.2f}%"


def apply_chart_theme(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial, sans-serif", color="#111827"),
        title_font=dict(size=18, color="#111827"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=24, r=24, t=64, b=32),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f7", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f7", zeroline=False)
    return fig


def create_score_gauge(score):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "점"},
            gauge={
                "axis": {"range": [1, 10]},
                "bar": {"color": "#2563eb"},
                "steps": [
                    {"range": [1, 2], "color": "#fee2e2"},
                    {"range": [3, 4], "color": "#ffedd5"},
                    {"range": [5, 6], "color": "#fef9c3"},
                    {"range": [7, 8], "color": "#dcfce7"},
                    {"range": [9, 10], "color": "#bbf7d0"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return apply_chart_theme(fig)


def create_price_chart(df, signal_history=None):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="일봉",
            increasing_line_color="#ef4444",
            decreasing_line_color="#2563eb",
        )
    )

    line_traces = [
        ("MA5", "MA5", "#f59e0b"),
        ("MA20", "MA20", "#10b981"),
        ("MA60", "MA60", "#6366f1"),
        ("Bollinger_Upper", "볼린저 상단선", "#94a3b8"),
        ("Bollinger_Lower", "볼린저 하단선", "#94a3b8"),
    ]

    for column, name, color in line_traces:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[column],
                mode="lines",
                name=name,
                line=dict(width=1.1, color=color),
            )
        )

    reference_lines = [
        ("20일 고점", df["High"].tail(20).max(), "#dc2626", "dot"),
        ("20일 저점", df["Low"].tail(20).min(), "#2563eb", "dot"),
        ("60일 고점", df["High"].tail(60).max(), "#991b1b", "dash"),
        ("60일 저점", df["Low"].tail(60).min(), "#1d4ed8", "dash"),
    ]

    for name, value, color, dash in reference_lines:
        fig.add_trace(
            go.Scatter(
                x=[df.index.min(), df.index.max()],
                y=[value, value],
                mode="lines",
                name=name,
                line=dict(width=0.9, color=color, dash=dash),
                hovertemplate=f"{name}: {value:,.2f}<extra></extra>",
            )
        )

    if signal_history is not None and not signal_history.empty:
        history = signal_history.copy()
        buy_signals = history[history["보조 판단"].isin(["매수 우세", "매수 우세 강함"])]
        sell_signals = history[history["보조 판단"].isin(["매도 우세", "매도 우세 강함"])]

        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals["Date"],
                    y=buy_signals["Close"],
                    mode="markers",
                    name="매수 우세 신호",
                    marker=dict(symbol="triangle-up", size=10, color="#16a34a", line=dict(width=1, color="#ffffff")),
                    hovertemplate="매수 우세<br>%{x}<br>종가 %{y:,.2f}<extra></extra>",
                )
            )

        if not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=sell_signals["Date"],
                    y=sell_signals["Close"],
                    mode="markers",
                    name="매도 우세 신호",
                    marker=dict(symbol="triangle-down", size=10, color="#dc2626", line=dict(width=1, color="#ffffff")),
                    hovertemplate="매도 우세<br>%{x}<br>종가 %{y:,.2f}<extra></extra>",
                )
            )

    fig.update_layout(
        title="주가 캔들봉 차트",
        xaxis_title="날짜",
        yaxis_title="가격",
        hovermode="x unified",
        height=540,
        xaxis_rangeslider_visible=False,
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1개월", step="month", stepmode="backward"),
                    dict(count=3, label="3개월", step="month", stepmode="backward"),
                    dict(count=6, label="6개월", step="month", stepmode="backward"),
                    dict(step="all", label="전체"),
                ]
            ),
            rangeslider=dict(visible=False),
            type="date",
        ),
    )

    return apply_chart_theme(fig)


def create_volume_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="거래량"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Volume_MA20"], mode="lines", name="거래량 20일 평균"))
    fig.update_layout(title="거래량 차트", xaxis_title="날짜", yaxis_title="거래량", hovermode="x unified", height=420)
    return apply_chart_theme(fig)


def create_rsi_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"))
    fig.add_hline(y=70, line_dash="dash", annotation_text="RSI 기준선 70")
    fig.add_hline(y=30, line_dash="dash", annotation_text="RSI 기준선 30")
    fig.update_layout(title="RSI 차트", xaxis_title="날짜", yaxis_title="RSI", hovermode="x unified", height=420)
    return apply_chart_theme(fig)


def create_macd_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], mode="lines", name="MACD"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], mode="lines", name="MACD Signal"))
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Histogram"], name="MACD Histogram"))
    fig.update_layout(title="MACD 차트", xaxis_title="날짜", yaxis_title="MACD", hovermode="x unified", height=420)
    return apply_chart_theme(fig)


def create_trend_risk_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["ADX"], mode="lines", name="ADX"))
    fig.add_trace(go.Scatter(x=df.index, y=df["ATR_Ratio"] * 100, mode="lines", name="ATR 비율(%)", yaxis="y2"))
    fig.add_hline(y=25, line_dash="dash", annotation_text="ADX 기준선 25")
    fig.update_layout(
        title="ADX / ATR 차트",
        xaxis_title="날짜",
        yaxis=dict(title="ADX"),
        yaxis2=dict(title="ATR 비율(%)", overlaying="y", side="right"),
        hovermode="x unified",
        height=420,
    )
    return apply_chart_theme(fig)


def create_obv_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["OBV"], mode="lines", name="OBV"))
    fig.add_trace(go.Scatter(x=df.index, y=df["OBV_MA20"], mode="lines", name="OBV 20일 평균"))
    fig.update_layout(title="OBV 차트", xaxis_title="날짜", yaxis_title="OBV", hovermode="x unified", height=420)
    return apply_chart_theme(fig)


def create_signal_history_chart(signal_history):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=signal_history["Date"],
            y=signal_history["기술적 점수"],
            mode="lines+markers",
            name="기술적 점수",
        )
    )
    fig.add_hrect(y0=7, y1=10, fillcolor="#dcfce7", opacity=0.35, line_width=0)
    fig.add_hrect(y0=5, y1=6, fillcolor="#fef9c3", opacity=0.35, line_width=0)
    fig.add_hrect(y0=1, y1=4, fillcolor="#fee2e2", opacity=0.35, line_width=0)
    fig.update_layout(title="기술적 점수 히스토리", xaxis_title="날짜", yaxis_title="점수", yaxis_range=[1, 10], height=420)
    return apply_chart_theme(fig)


def create_intraday_chart(df):
    analyzed = calculate_intraday_indicators(df)
    session_df = get_latest_intraday_session(analyzed)

    fig = go.Figure()

    if session_df.empty:
        fig.update_layout(
            title="분봉 캔들 참고 차트",
            xaxis_title="시간",
            yaxis_title="가격",
            hovermode="x unified",
            height=460,
            xaxis_rangeslider_visible=False,
        )
        return apply_chart_theme(fig)

    fig.add_trace(
        go.Candlestick(
            x=session_df.index,
            open=session_df["Open"],
            high=session_df["High"],
            low=session_df["Low"],
            close=session_df["Close"],
            name="분봉 캔들",
            increasing_line_color="#ef4444",
            decreasing_line_color="#2563eb",
        )
    )

    line_traces = [
        ("Intraday_MA5", "분봉 MA5", "#f59e0b", 1.2),
        ("Intraday_MA20", "분봉 MA20", "#10b981", 1.2),
        ("VWAP", "VWAP 참고선", "#7c3aed", 1.4),
    ]

    for column, name, color, width in line_traces:
        if column in session_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=session_df.index,
                    y=session_df[column],
                    mode="lines",
                    name=name,
                    line=dict(color=color, width=width),
                )
            )

    day_high = session_df["High"].max()
    day_low = session_df["Low"].min()
    x_start = session_df.index.min()
    x_end = session_df.index.max()

    fig.add_trace(
        go.Scatter(
            x=[x_start, x_end],
            y=[day_high, day_high],
            mode="lines",
            name="당일 고가",
            line=dict(color="#dc2626", width=0.9, dash="dot"),
            hovertemplate=f"당일 고가: {day_high:,.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[x_start, x_end],
            y=[day_low, day_low],
            mode="lines",
            name="당일 저가",
            line=dict(color="#2563eb", width=0.9, dash="dot"),
            hovertemplate=f"당일 저가: {day_low:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="분봉 캔들 참고 차트",
        xaxis_title="시간",
        yaxis_title="가격",
        hovermode="x unified",
        height=480,
        xaxis_rangeslider_visible=False,
    )
    return apply_chart_theme(fig)


def get_dart_api_key():
    try:
        key = st.secrets.get("DART_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"

    try:
        for line in secrets_path.read_text(encoding="utf-8-sig").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue

            key_name, key_value = stripped.split("=", 1)

            if key_name.strip() == "DART_API_KEY":
                return key_value.strip().strip('"').strip("'")
    except Exception:
        return ""

    return ""


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_dart_corp_code_map(api_key):
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={urllib.parse.quote(api_key)}"

    with urllib.request.urlopen(url, timeout=20) as response:
        data = response.read()

    with zipfile.ZipFile(BytesIO(data)) as zip_file:
        xml_data = zip_file.read("CORPCODE.xml")

    root = ET.fromstring(xml_data)
    mapping = {}

    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        corp_name = (item.findtext("corp_name") or "").strip()

        if stock_code:
            mapping[stock_code] = {"corp_code": corp_code, "corp_name": corp_name}

    return mapping


@st.cache_data(ttl=60 * 30, show_spinner=False)
def get_recent_disclosures(stock_code, api_key, days=30):
    if not stock_code or not api_key:
        return pd.DataFrame()

    corp_map = get_dart_corp_code_map(api_key)

    if stock_code not in corp_map:
        return pd.DataFrame()

    end_date = date.today()
    begin_date = end_date - timedelta(days=days)
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_map[stock_code]["corp_code"],
        "bgn_de": begin_date.strftime("%Y%m%d"),
        "end_de": end_date.strftime("%Y%m%d"),
        "page_count": "20",
    }
    url = "https://opendart.fss.or.kr/api/list.json?" + urllib.parse.urlencode(params)

    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("status") != "000":
        return pd.DataFrame()

    rows = []
    for item in payload.get("list", []):
        rcept_no = item.get("rcept_no", "")
        rows.append(
            {
                "접수일": item.get("rcept_dt", ""),
                "회사명": item.get("corp_name", corp_map[stock_code]["corp_name"]),
                "공시명": item.get("report_nm", ""),
                "제출인": item.get("flr_nm", ""),
                "링크": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}",
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=60 * 30, show_spinner=False)
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


def render_metric_summary(latest, signal_result):
    badge_class = get_signal_badge_class(signal_result["technical_score"])
    cards = [
        (
            "기술적 분석 점수",
            f"{signal_result['technical_score']} / 10",
            "종합 점수",
        ),
        (
            "보조 판단",
            f"<span class='signal-badge {badge_class}'>{signal_result['signal']}</span>",
            "기술적 조건 기준",
        ),
        ("최근 종가", format_price(latest["Close"]), "일봉 Close 기준"),
        ("최근 거래량", f"{int(latest['Volume']):,}", "Volume"),
        ("RSI", f"{latest['RSI']:.2f}", "과열/침체"),
        ("MACD", f"{latest['MACD']:.4f}", f"Signal {latest['MACD_Signal']:.4f}"),
        ("ADX", f"{latest['ADX']:.2f}", "추세 강도"),
        ("ATR 비율", format_percent(latest["ATR_Ratio"]), "변동성 리스크"),
    ]

    card_html = "<div class='metric-grid'>"
    for label, value, sub in cards:
        card_html += (
            "<div class='metric-card'>"
            f"<div class='label'>{label}</div>"
            f"<div class='value'>{value}</div>"
            f"<div class='sub'>{sub}</div>"
            "</div>"
        )
    card_html += "</div>"

    st.markdown(card_html, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="basis-card">
            <b>데이터 기준 날짜:</b> {latest.name.date()}<br>
            <b>변동성 리스크:</b> {signal_result['risk_level']} - {signal_result['risk_comment']}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_intraday_summary(df, result):
    st.subheader("당일 흐름 분석")

    if not result or result.get("flow_score") is None:
        st.info("당일 흐름 분석에 필요한 분봉 데이터가 부족합니다.")
        return

    badge_class = get_signal_badge_class(result["flow_score"])
    cards = [
        ("당일 흐름 점수", f"{result['flow_score']} / 10", "일봉 점수와 별도"),
        (
            "당일 흐름 판단",
            f"<span class='signal-badge {badge_class}'>{result['flow_signal']}</span>",
            "분봉 조건 기준",
        ),
        ("기준 시간", result["basis_time"], "최근 분봉"),
        ("최근 분봉 종가", format_price(result["latest_close"]), "Close 기준"),
        ("당일 등락률", format_percent(result["day_change"]), "시가 대비"),
        ("당일 고가", format_price(result["day_high"]), "분봉 기준"),
        ("당일 저가", format_price(result["day_low"]), "분봉 기준"),
        ("당일 누적 거래량", f"{int(result['day_volume']):,}", "현재 조회 범위"),
        ("VWAP", format_price(result["vwap"]), "당일 거래량 가중 평균"),
        ("분봉 MA5", format_price(result["ma5"]), "단기 평균"),
        ("분봉 MA20", format_price(result["ma20"]), "중기 평균"),
        ("당일 변동폭", format_percent(result["day_range"]), "고가-저가 / 시가"),
    ]

    card_html = "<div class='metric-grid'>"
    for label, value, sub in cards:
        card_html += (
            "<div class='metric-card'>"
            f"<div class='label'>{label}</div>"
            f"<div class='value'>{value}</div>"
            f"<div class='sub'>{sub}</div>"
            "</div>"
        )
    card_html += "</div>"

    st.markdown(card_html, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="basis-card">
            <b>분봉 간격:</b> {result['interval']}<br>
            <b>안내:</b> 분봉 데이터는 실시간 시세가 아니며 지연되거나 일부 누락될 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not result["score_details"].empty:
        with st.expander("당일 흐름 평가 항목 보기", expanded=False):
            st.dataframe(result["score_details"], use_container_width=True)
            for comment in result["comments"]:
                st.write(f"- {comment}")


def main():
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False

    load_custom_css()

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">개인용 주식 분석 대시보드</div>
            <h1>이영록 스톡랩</h1>
            <p>
                기술적 지표와 공개 정보를 함께 확인하는 판단 보조 도구입니다.
                일봉 가격, 거래량, 모멘텀, 추세 강도, 변동성, 공시/뉴스 참고 정보를 한 화면에서 점검합니다.
            </p>
            <div class="notice-row">
                <div class="notice">본 프로그램은 실제 투자 조언이 아닌 기술적 분석 및 공개 정보 확인을 위한 개인용 판단 보조 도구입니다.</div>
                <div class="notice">yfinance 데이터는 실제 증권사/거래소 데이터와 차이가 있을 수 있으며, 분봉 데이터는 실시간 시세가 아니라 지연될 수 있습니다.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dart_api_key = get_dart_api_key()
    dart_available = bool(dart_api_key)

    with st.sidebar:
        st.header("분석 설정")
        ticker = st.text_input("종목 코드를 입력하세요", value="005930.KS", help="예: 005930.KS, 005930, AAPL, MSFT, TSLA")
        period_option = st.selectbox("일봉 분석 기간", ["3개월", "6개월", "1년", "2년", "5년"], index=2)
        period_map = {"3개월": "3mo", "6개월": "6mo", "1년": "1y", "2년": "2y", "5년": "5y"}
        show_intraday = st.checkbox("분봉 참고 차트 표시", value=True)
        intraday_interval = st.selectbox("분봉 간격", ["1m", "5m", "15m", "30m", "60m"], index=1)
        show_dart = st.checkbox("DART 공시 참고 영역 표시", value=dart_available, disabled=not dart_available)
        if not dart_available:
            st.caption("DART API 키를 한 번 설정하면 공시 기능이 자동으로 활성화됩니다.")
        show_news = st.checkbox("뉴스 참고 영역 표시", value=True)
        auto_refresh = st.checkbox("30분마다 자동 새로고침", value=False)
        analyze = st.button("분석 시작", type="primary", use_container_width=True)

    if auto_refresh:
        enable_auto_refresh(minutes=30)
        st.caption("자동 새로고침이 켜져 있습니다. 30분마다 페이지를 다시 불러옵니다.")

    if analyze:
        st.session_state.analysis_started = True

    if not st.session_state.analysis_started:
        st.markdown(
            """
            <div class="empty-guide">
                <h3>분석을 시작해보세요</h3>
                <p>
                    왼쪽 사이드바에서 종목과 분석 기간을 선택한 뒤 <b>분석 시작</b>을 누르면
                    기술적 분석 점수, 보조 판단, 차트, 백테스트, 공시/뉴스 참고 정보를 확인할 수 있습니다.
                    점수 해석은 1-2점 매도 우세 강함, 3-4점 매도 우세, 5-6점 관망 구간,
                    7-8점 매수 우세, 9-10점 매수 우세 강함입니다.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if not ticker.strip():
        st.error("종목 코드를 입력하세요.")
        return

    normalized_ticker = normalize_ticker(ticker)

    with st.spinner("일봉 데이터를 가져오고 기술적 지표를 계산하는 중입니다..."):
        daily_df = get_daily_data(normalized_ticker, period_map[period_option])

    if daily_df.empty:
        st.error("주가 데이터를 가져오지 못했습니다. 종목 코드나 데이터 제공 상태를 확인하세요.")
        return

    if len(daily_df) < 60:
        st.error("60일 이동평균선 계산에 필요한 데이터가 부족합니다. 더 긴 분석 기간을 선택하세요.")
        return

    analyzed_df = calculate_indicators(daily_df)
    valid_df = analyzed_df.dropna(subset=SIGNAL_COLUMNS)

    if len(valid_df) < 2:
        st.error("기술적 지표 계산 후 유효한 데이터가 부족합니다.")
        return

    signal_result = calculate_signal(analyzed_df)
    latest = valid_df.iloc[-1]

    st.subheader(f"{normalized_ticker} 분석 요약")

    summary_col, gauge_col = st.columns([2, 1])
    with summary_col:
        render_metric_summary(latest, signal_result)
    with gauge_col:
        st.plotly_chart(create_score_gauge(signal_result["technical_score"]), use_container_width=True)

    st.subheader("신호 판단 이유")
    for reason in signal_result["reasons"]:
        st.write(f"- {reason}")

    st.subheader("평가 항목별 점수")
    st.dataframe(signal_result["score_details"], use_container_width=True)

    signal_history = build_signal_history(analyzed_df)

    chart_tab, history_tab, backtest_tab, external_tab, data_tab = st.tabs(
        ["기술적 차트", "신호 히스토리", "백테스트", "공시/뉴스 참고", "최근 데이터"]
    )

    with chart_tab:
        price_tab, volume_tab, rsi_tab, macd_tab, trend_tab, obv_tab, intraday_tab = st.tabs(
            ["주가", "거래량", "RSI", "MACD", "ADX/ATR", "OBV", "분봉 참고"]
        )

        with price_tab:
            st.plotly_chart(create_price_chart(analyzed_df, signal_history), use_container_width=True)
        with volume_tab:
            st.plotly_chart(create_volume_chart(analyzed_df), use_container_width=True)
        with rsi_tab:
            st.plotly_chart(create_rsi_chart(analyzed_df), use_container_width=True)
        with macd_tab:
            st.plotly_chart(create_macd_chart(analyzed_df), use_container_width=True)
        with trend_tab:
            st.plotly_chart(create_trend_risk_chart(analyzed_df), use_container_width=True)
        with obv_tab:
            st.plotly_chart(create_obv_chart(analyzed_df), use_container_width=True)
        with intraday_tab:
            if show_intraday:
                with st.spinner("분봉 데이터를 가져오는 중입니다..."):
                    intraday_df = get_intraday_data(normalized_ticker, intraday_interval)

                if intraday_df.empty:
                    st.info("분봉 데이터를 가져오지 못했습니다. yfinance 제공 상태나 장 운영 시간을 확인하세요.")
                else:
                    intraday_analyzed_df = calculate_intraday_indicators(intraday_df)
                    intraday_result = calculate_intraday_signal(intraday_analyzed_df, intraday_interval)
                    render_intraday_summary(intraday_analyzed_df, intraday_result)
                    st.plotly_chart(create_intraday_chart(intraday_analyzed_df), use_container_width=True)
                    st.caption("분봉 데이터는 실시간 시세가 아니며 지연되거나 일부 누락될 수 있습니다.")
            else:
                st.info("사이드바에서 분봉 참고 차트 표시를 켜면 확인할 수 있습니다.")

    with history_tab:
        if signal_history.empty:
            st.info("신호 히스토리를 계산할 수 없습니다.")
        else:
            st.plotly_chart(create_signal_history_chart(signal_history), use_container_width=True)
            st.dataframe(signal_history.tail(30).sort_values("Date", ascending=False), use_container_width=True)

    with backtest_tab:
        backtest_df, backtest_summary = run_backtest(analyzed_df, signal_history)

        if not backtest_summary:
            st.info("백테스트에 사용할 매수 우세 신호가 충분하지 않습니다.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("매수 우세 신호 발생 횟수", f"{backtest_summary['매수 우세 신호 발생 횟수']:,}")
            col1.metric("5거래일 평균 수익률", format_percent(backtest_summary["5거래일 평균 수익률"]))
            col2.metric("20거래일 평균 수익률", format_percent(backtest_summary["20거래일 평균 수익률"]))
            col2.metric("5거래일 승률", format_percent(backtest_summary["5거래일 승률"]))
            col3.metric("20거래일 승률", format_percent(backtest_summary["20거래일 승률"]))
            col3.metric("평균 최대 하락률", format_percent(backtest_summary["평균 최대 하락률"]))
            st.dataframe(backtest_df.tail(50).sort_values("신호 날짜", ascending=False), use_container_width=True)
            st.caption("백테스트는 과거 데이터 기반 검증이며 미래 성과를 보장하지 않습니다.")

    with external_tab:
        st.write("공시와 뉴스는 기술적 점수에 직접 반영하지 않고 참고 정보로만 표시합니다.")

        if show_dart:
            stock_code = get_stock_code(normalized_ticker)

            if not stock_code:
                st.info("DART 공시는 한국 6자리 종목 코드에서만 조회합니다.")
            else:
                try:
                    disclosures = get_recent_disclosures(stock_code, dart_api_key)
                    if disclosures.empty:
                        st.info("최근 30일 내 조회 가능한 공시가 없거나 DART 조회에 실패했습니다.")
                    else:
                        st.subheader("최근 DART 공시")
                        st.dataframe(disclosures, use_container_width=True)
                except Exception as error:
                    st.info(f"DART 공시 조회 중 문제가 발생했습니다: {error}")

        if show_news:
            try:
                news_df = get_yfinance_news(normalized_ticker)
                if news_df.empty:
                    st.info("yfinance 뉴스 데이터를 가져오지 못했습니다.")
                else:
                    st.subheader("최근 뉴스 참고")
                    st.dataframe(news_df, use_container_width=True)
            except Exception as error:
                st.info(f"뉴스 조회 중 문제가 발생했습니다: {error}")

    with data_tab:
        display_columns = [column for column in SIGNAL_COLUMNS if column in valid_df.columns]
        st.dataframe(valid_df[display_columns].tail(120).sort_index(ascending=False), use_container_width=True)


if __name__ == "__main__":
    main()
