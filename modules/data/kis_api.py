import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from modules.config import APP_ROOT, KIS_REAL_BASE_URL, REQUIRED_COLUMNS


def normalize_ticker(ticker):
    ticker = ticker.strip().upper()

    if ticker.isdigit() and len(ticker) == 6:
        return f"{ticker}.KS"

    return ticker


def set_price_data_attrs(df, source, source_detail="", fallback_reason="", requested_source=""):
    if df is None:
        return pd.DataFrame()

    df.attrs["data_source"] = source
    df.attrs["data_source_detail"] = source_detail
    df.attrs["fallback_reason"] = fallback_reason
    df.attrs["requested_source"] = requested_source

    return df


def get_secret_value(key, default=""):
    try:
        value = st.secrets.get(key, "")
        if value:
            return str(value).strip()
    except Exception:
        pass

    secrets_path = APP_ROOT / ".streamlit" / "secrets.toml"

    try:
        for line in secrets_path.read_text(encoding="utf-8-sig").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue

            key_name, key_value = stripped.split("=", 1)

            if key_name.strip() == key:
                return key_value.strip().strip('"').strip("'")
    except Exception:
        return default

    return default


def get_kis_config():
    base_url = get_secret_value("KIS_BASE_URL", KIS_REAL_BASE_URL).rstrip("/")

    return {
        "app_key": get_secret_value("KIS_APP_KEY", ""),
        "app_secret": get_secret_value("KIS_APP_SECRET", ""),
        "base_url": base_url or KIS_REAL_BASE_URL,
        "paper": "openapivts" in (base_url or "").lower(),
    }


def is_kis_configured():
    config = get_kis_config()
    return bool(config["app_key"] and config["app_secret"])


def make_json_request(url, method="GET", headers=None, params=None, body=None, timeout=15):
    request_url = url

    if params:
        request_url = f"{request_url}?{urllib.parse.urlencode(params)}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(
        request_url,
        data=data,
        headers=headers or {},
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(raw)
            message = payload.get("msg1") or payload.get("message") or f"HTTP {error.code}"
        except Exception:
            message = f"HTTP {error.code}"

        if error.code == 403:
            message = (
                f"{message} - KIS 접근이 거절되었습니다. "
                "KIS_BASE_URL, 실전/모의 키 구분, API 사용 권한을 확인하세요."
            )
        raise RuntimeError(message) from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"네트워크 오류: {error.reason}") from None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError("JSON 응답을 해석하지 못했습니다.") from None


def get_kis_access_token(app_key, app_secret, base_url):
    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }
    result = make_json_request(
        f"{base_url}/oauth2/tokenP",
        method="POST",
        headers={"content-type": "application/json; charset=utf-8"},
        body=payload,
        timeout=20,
    )
    token = result.get("access_token")

    if not token:
        message = result.get("msg1") or result.get("error_description") or "KIS 접근 토큰을 발급받지 못했습니다."
        raise RuntimeError(message)

    return token


def get_kis_tr_id(tr_id, is_paper=False):
    if is_paper and isinstance(tr_id, str) and tr_id.startswith("F"):
        return f"V{tr_id[1:]}"
    return tr_id


def kis_get(path, tr_id, params, timeout=20):
    config = get_kis_config()

    if not config["app_key"] or not config["app_secret"]:
        raise RuntimeError("KIS API 키가 설정되지 않았습니다.")

    token = get_kis_access_token(config["app_key"], config["app_secret"], config["base_url"])
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": config["app_key"],
        "appsecret": config["app_secret"],
        "tr_id": get_kis_tr_id(tr_id, config["paper"]),
        "custtype": "P",
    }

    return make_json_request(
        f"{config['base_url']}{path}",
        method="GET",
        headers=headers,
        params=params,
        timeout=timeout,
    )


def parse_kis_number(value):
    try:
        cleaned = str(value or "0").replace(",", "").strip()
        return float(cleaned) if "." in cleaned else int(cleaned)
    except (TypeError, ValueError):
        return np.nan


def get_period_lookback_days(period):
    return {
        "3mo": 130,
        "6mo": 230,
        "1y": 420,
        "2y": 800,
        "5y": 1900,
    }.get(period, 420)


def is_kis_domestic_supported(ticker):
    return bool(get_stock_code(ticker))


def get_stock_code(ticker):
    normalized = normalize_ticker(ticker)
    code = normalized.split(".")[0]

    if code.isdigit() and len(code) == 6:
        return code

    return None


def normalize_kis_daily_rows(rows):
    parsed_rows = []

    for row in rows or []:
        date_value = row.get("stck_bsop_date") or row.get("bsop_date")
        if not date_value:
            continue

        parsed_rows.append(
            {
                "Date": pd.to_datetime(str(date_value), format="%Y%m%d", errors="coerce"),
                "Open": parse_kis_number(row.get("stck_oprc")),
                "High": parse_kis_number(row.get("stck_hgpr")),
                "Low": parse_kis_number(row.get("stck_lwpr")),
                "Close": parse_kis_number(row.get("stck_clpr") or row.get("stck_prpr")),
                "Volume": parse_kis_number(row.get("acml_vol") or row.get("cntg_vol")),
            }
        )

    if not parsed_rows:
        return pd.DataFrame()

    df = pd.DataFrame(parsed_rows).dropna(subset=["Date", "Close"])
    df = df.set_index("Date").sort_index()
    df = df[REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Close"])
    df = df[~df.index.duplicated(keep="last")]

    return df


def get_kis_daily_data(ticker, period):
    stock_code = get_stock_code(ticker)

    if not stock_code:
        return pd.DataFrame()

    end_date = date.today()
    start_date = end_date - timedelta(days=get_period_lookback_days(period))
    current_end = end_date
    rows = []

    for _ in range(20):
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),
            "FID_INPUT_DATE_2": current_end.strftime("%Y%m%d"),
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "1",
        }
        result = kis_get(
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            "FHKST03010100",
            params,
        )
        output_rows = result.get("output2") or []

        if not output_rows:
            break

        rows.extend(output_rows)
        batch_df = normalize_kis_daily_rows(output_rows)

        if batch_df.empty:
            break

        oldest_date = batch_df.index.min().date()

        if oldest_date <= start_date:
            break

        next_end = oldest_date - timedelta(days=1)

        if next_end >= current_end:
            break

        current_end = next_end

    df = normalize_kis_daily_rows(rows)

    if df.empty:
        return df

    df = df[df.index.date >= start_date]
    return set_price_data_attrs(
        df,
        "한국투자 KIS Open API",
        "국내주식 기간별 시세, 원주가 기준(FID_ORG_ADJ_PRC=1)",
    )


def normalize_kis_intraday_rows(rows):
    parsed_rows = []

    for row in rows or []:
        date_value = row.get("stck_bsop_date") or date.today().strftime("%Y%m%d")
        time_value = str(row.get("stck_cntg_hour") or row.get("cntg_hour") or "").zfill(6)

        if not time_value.strip("0"):
            continue

        timestamp = pd.to_datetime(f"{date_value}{time_value}", format="%Y%m%d%H%M%S", errors="coerce")

        if pd.isna(timestamp):
            continue

        close = parse_kis_number(row.get("stck_prpr") or row.get("stck_clpr"))
        parsed_rows.append(
            {
                "Date": timestamp,
                "Open": parse_kis_number(row.get("stck_oprc")) if row.get("stck_oprc") is not None else close,
                "High": parse_kis_number(row.get("stck_hgpr")) if row.get("stck_hgpr") is not None else close,
                "Low": parse_kis_number(row.get("stck_lwpr")) if row.get("stck_lwpr") is not None else close,
                "Close": close,
                "Volume": parse_kis_number(row.get("cntg_vol") or row.get("acml_vol")),
            }
        )

    if not parsed_rows:
        return pd.DataFrame()

    df = pd.DataFrame(parsed_rows).dropna(subset=["Date", "Close"])
    df = df.set_index("Date").sort_index()
    df = df[REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["Close"])
    df = df[~df.index.duplicated(keep="last")]

    return df


def resample_intraday_ohlcv(df, interval):
    if df.empty or interval == "1m":
        return df

    frequency_map = {
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "60m": "60min",
    }
    frequency = frequency_map.get(interval)

    if not frequency:
        return df

    resampled = df.resample(frequency).agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }
    )
    resampled = resampled.dropna(subset=["Close"])
    resampled.attrs.update(df.attrs)

    return resampled


def get_kis_intraday_data(ticker, interval):
    stock_code = get_stock_code(ticker)

    if not stock_code:
        return pd.DataFrame()

    now = datetime.now()

    if now.hour < 9:
        current_dt = datetime.combine(date.today(), datetime.strptime("153000", "%H%M%S").time())
    elif now.hour > 15 or (now.hour == 15 and now.minute > 30):
        current_dt = datetime.combine(date.today(), datetime.strptime("153000", "%H%M%S").time())
    else:
        current_dt = now

    rows = []
    seen_keys = set()

    for _ in range(8):
        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_HOUR_1": current_dt.strftime("%H%M%S"),
            "FID_PW_DATA_INCU_YN": "Y",
        }
        result = kis_get(
            "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            "FHKST03010200",
            params,
        )
        output_rows = result.get("output2") or []

        if not output_rows:
            break

        for row in output_rows:
            key = (row.get("stck_bsop_date"), row.get("stck_cntg_hour"))
            if key not in seen_keys:
                rows.append(row)
                seen_keys.add(key)

        batch_df = normalize_kis_intraday_rows(output_rows)

        if batch_df.empty:
            break

        oldest_time = batch_df.index.min().to_pydatetime()
        next_dt = oldest_time - timedelta(minutes=1)

        if next_dt >= current_dt:
            break

        current_dt = next_dt

        if current_dt.date() != date.today():
            break

    df = normalize_kis_intraday_rows(rows)

    if df.empty:
        return df

    df = set_price_data_attrs(
        df,
        "한국투자 KIS Open API",
        "국내주식 당일분봉 시세",
    )

    return resample_intraday_ohlcv(df, interval)
