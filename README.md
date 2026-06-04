# 이영록 스톡랩

개인용 주식 분석 대시보드입니다. yfinance 주가 데이터로 일봉 기술적 지표와 분봉 당일 흐름을 확인하고, DART 공시와 yfinance 뉴스는 참고 정보로 함께 보여줍니다.

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

## 주의 문구

본 프로그램은 실제 투자 조언이 아닌 기술적 분석 및 공개 정보 확인을 위한 개인용 판단 보조 도구입니다. yfinance 데이터는 실제 증권사/거래소 데이터와 차이가 있을 수 있으며, 분봉 데이터는 실시간 시세가 아니라 지연될 수 있습니다.
