# 이영록 스톡랩

기술적 분석 기반 판단 보조 대시보드입니다. yfinance 주가 데이터로 일봉 기술 조건 충족도(0~100), 1개월 스윙 점검, 분봉 당일 흐름을 확인하고, 관심자산 스캐너로 먼저 점검할 분석 후보를 정리합니다. DART 공시와 yfinance 뉴스는 참고 정보로 함께 보여줍니다.

## 주요 기능

- 단일 자산 분석
- 관심자산 스캐너
- 자산명 또는 코드 입력 지원
- 일봉 기술 조건 충족도(0~100)와 점수 근거 분해
- 1개월 스윙 조건 충족도
- 당일 흐름 분석
- 리스크 참고 섹션
- 데이터 기준 안내 박스
- 데이터 신뢰도 A~D 등급
- 시장 흐름 참고 탭
- 상대강도 RS20/RS60 참고
- 확대/축소와 날짜 확인을 개선한 인터랙티브 차트
- 기술적 조건 체크리스트
- 한국투자 KIS Open API 우선 조회 구조
- 초보자용 지표 설명 탭
- DART 공시 참고
- yfinance 뉴스 참고
- 과거 조건 발생 사례 확인

## 지원 자산 예시

- 한국 주식: `삼성전자`, `SK하이닉스`, `005930.KS`, `000660.KS`
- 미국 주식: `애플`, `마이크로소프트`, `AAPL`, `MSFT`
- 일반 ETF: `SPY`, `QQQ`
- 레버리지 ETF: `TQQQ`, `SOXL`
- 인버스 레버리지 ETF: `SQQQ`, `SOXS`
- 시장 지수: `^GSPC`

## 자산명 입력

`asset_metadata.csv`에 등록된 자산은 코드 대신 이름이나 별칭으로 입력할 수 있습니다.

예:

- `삼성전자` -> `005930.KS`
- `애플` -> `AAPL`
- `나스닥` -> `^IXIC`
- `코덱스레버리지` -> `122630.KS`
- `나스닥3배` -> `TQQQ`

메타데이터에 없는 자산은 기존처럼 yfinance 티커를 직접 입력하면 됩니다.

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

## 지표 설명 탭

앱 안의 `지표 설명` 탭에서 초보자도 0~100 조건 충족도와 차트를 이해할 수 있도록 주요 용어를 짧은 표로 정리합니다.

- 차트 시간 단위: 일봉, 분봉, 1개월 스윙, 당일 흐름
- 기술적 지표: 이동평균선, RSI, MACD, 볼린저 밴드, ADX, ATR, OBV, VWAP, 거래량
- 점수 해석: 일봉 기술 조건 충족도(0~100), 1개월 스윙 조건 충족도, 당일 흐름 조건 충족도(0~100), 종합 점검 조건 충족도(0~100)
- ETF 용어: ETF, 지수추종 ETF, 섹터 ETF, 레버리지 ETF, 인버스 ETF, NAV, 괴리율, 추적오차
- 기초 투자지표: PER, PBR, ROE, EPS, 시가총액, 배당수익률, 영업이익, 순이익, 부채비율

기초 투자지표는 현재 앱의 기술 조건 충족도에 직접 반영되지 않는 학습용 설명입니다.

## 1차 실전성 개선

- 데이터 신뢰도 A~D 등급을 추가해 가격 데이터를 해석하기 전에 출처, 최근성, 누락 여부, 가격 일관성을 먼저 확인할 수 있게 했습니다.
- 시장 흐름 참고 탭을 추가해 KOSPI, KOSDAQ, S&P 500, NASDAQ, VIX, 환율, 금리, 주요 섹터 ETF 흐름을 별도로 확인할 수 있게 했습니다.
- 단일 자산과 관심자산 스캐너에 RS20/RS60 상대강도 참고값을 추가했습니다. 이는 자산의 최근 20거래일/60거래일 흐름을 벤치마크와 비교한 참고값이며 수익 예측이 아닙니다.
- 시장 흐름과 상대강도 벤치마크 데이터는 현재 yfinance 참고 데이터 기준이며, 실제 거래소/증권사 데이터와 차이가 있을 수 있습니다.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Streamlit Cloud Secrets 설정

Streamlit Community Cloud 배포 후 앱 설정의 Secrets에 아래 형식으로 등록합니다.

```toml
DART_API_KEY = "발급받은_DART_API_KEY"
KIS_APP_KEY = "발급받은_KIS_APP_KEY"
KIS_APP_SECRET = "발급받은_KIS_APP_SECRET"
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"
DATA_SOURCE = "auto"
```

`.streamlit/secrets.toml`은 로컬 전용 파일이며 GitHub에 올리지 않습니다.

`DATA_SOURCE`는 `auto`, `kis`, `yfinance` 중 하나를 사용할 수 있습니다. `auto`는 국내 주식/ETF에서 한국투자 KIS Open API를 우선 사용하고, 미지원 자산이나 조회 실패 시 yfinance 참고 데이터로 보완합니다.

## 보안 주의사항

- DART API 키는 코드에 직접 넣지 않습니다.
- 한국투자 KIS App Key와 App Secret은 코드에 직접 넣지 않습니다.
- `.streamlit/secrets.toml`은 GitHub에 올리지 않습니다.
- `.streamlit/secrets.toml.example`만 예시 파일로 유지합니다.

## 판단 보조 원칙

본 프로그램은 실제 투자 조언이 아닌 기술적 분석 및 공개 정보 확인을 위한 개인용 판단 보조 도구입니다. 표시되는 점수는 수익 확률이 아니라 0~100 범위의 기술 조건 충족도입니다. 일봉 기술 조건 충족도(0~100)는 `강한 약세 주의`, `약세 주의`, `관망/확인 구간`, `상승 관심 조건`, `상승 관심 조건 강함`처럼 조건 중심 표현으로 표시합니다.

가격 데이터는 설정한 데이터 소스 기준으로 조회합니다. KIS 미지원/조회 실패 자산은 yfinance 참고 데이터로 보완될 수 있으며, yfinance 데이터는 실제 증권사/거래소 데이터와 차이가 있을 수 있습니다. 분봉 데이터는 실시간 시세가 아니라 지연될 수 있습니다. 레버리지와 인버스 ETF는 일반 주식보다 변동성과 구조적 위험이 클 수 있으므로 별도 확인이 필요합니다.
