# 이영록 스톡랩

기술적 분석 기반 판단 보조 대시보드입니다. yfinance 주가 데이터로 일봉 기술 점수, 1개월 스윙 점검, 분봉 당일 흐름을 확인하고, 관심자산 스캐너로 먼저 점검할 분석 후보를 정리합니다. DART 공시와 yfinance 뉴스는 참고 정보로 함께 보여줍니다.

## 주요 기능

- 단일 자산 분석
- 관심자산 스캐너
- 일봉 기술 점수와 점수 근거 분해
- 1개월 스윙 조건 충족도
- 당일 흐름 분석
- 리스크 참고 섹션
- DART 공시 참고
- yfinance 뉴스 참고
- 간단 백테스트

## 지원 자산 예시

- 한국 주식: `005930.KS`, `000660.KS`
- 미국 주식: `AAPL`, `MSFT`
- 일반 ETF: `SPY`, `QQQ`
- 레버리지 ETF: `TQQQ`, `SOXL`
- 인버스 레버리지 ETF: `SQQQ`, `SOXS`
- 시장 지수: `^GSPC`

## 기술적 분석 지표

- 이동평균선 `MA5`, `MA10`, `MA20`, `MA60`
- RSI
- MACD, MACD Signal, MACD Histogram
- Bollinger Upper, Middle, Lower
- Bollinger Band Width
- Bollinger %B
- ADX, +DI, -DI
- ATR, ATR Ratio
- OBV, OBV MA20
- VWAP

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Streamlit Cloud Secrets 설정

Streamlit Community Cloud 배포 후 앱 설정의 Secrets에 아래 형식으로 등록합니다.

```toml
DART_API_KEY = "발급받은_DART_API_KEY"
```

`.streamlit/secrets.toml`은 로컬 전용 파일이며 GitHub에 올리지 않습니다.

## 보안 주의사항

- DART API 키는 코드에 직접 넣지 않습니다.
- `.streamlit/secrets.toml`은 GitHub에 올리지 않습니다.
- `.streamlit/secrets.toml.example`만 예시 파일로 유지합니다.

## 주의 문구

본 프로그램은 실제 투자 조언이 아닌 기술적 분석 및 공개 정보 확인을 위한 개인용 판단 보조 도구입니다. yfinance 데이터는 실제 증권사/거래소 데이터와 차이가 있을 수 있으며, 분봉 데이터는 실시간 시세가 아니라 지연될 수 있습니다. 레버리지와 인버스 ETF는 일반 주식보다 변동성과 구조적 위험이 클 수 있으므로 별도 확인이 필요합니다.
