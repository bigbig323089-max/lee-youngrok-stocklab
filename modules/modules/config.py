from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
SIGNAL_COLUMNS = [
    "Close",
    "Volume",
    "MA5",
    "MA10",
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
    "Bollinger_Width",
    "Bollinger_Percent_B",
    "ADX",
    "Plus_DI",
    "Minus_DI",
    "ATR",
    "ATR_Ratio",
    "OBV",
    "OBV_MA20",
]
WATCHLIST_MAX_COUNT = 20
LEVERAGED_LONG_TICKERS = {
    "TQQQ",
    "UPRO",
    "SPXL",
    "QLD",
    "SSO",
    "SOXL",
    "FAS",
    "TNA",
    "SOXL",
    "122630.KS",
    "233740.KS",
    "204450.KS",
}
INVERSE_TICKERS = {
    "SQQQ",
    "SPXU",
    "SDS",
    "QID",
    "PSQ",
    "SH",
    "SOXS",
    "252670.KS",
    "251340.KS",
    "114800.KS",
}
COMMON_ETF_TICKERS = {
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    "VOO",
    "IVV",
    "VTI",
    "XLF",
    "XLK",
    "XLE",
    "XLV",
    "TLT",
    "GLD",
    "SLV",
}
ASSET_METADATA_COLUMNS = [
    "ticker",
    "name",
    "aliases",
    "asset_type",
    "market",
    "underlying_index",
    "leverage_factor",
    "direction",
    "category",
    "currency",
    "risk_note",
]
ASSET_METADATA_PATH = APP_ROOT / "asset_metadata.csv"
DATA_SOURCE_OPTIONS = {
    "auto": "자동(KIS 우선, 실패 시 yfinance)",
    "kis": "한국투자 KIS 우선",
    "yfinance": "yfinance 참고 데이터",
}
KIS_REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
KIS_PAPER_BASE_URL = "https://openapivts.koreainvestment.com:29443"
