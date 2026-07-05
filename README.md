# Open-Meteo Weather Web Page

Flask와 Open-Meteo API로 만든 날씨 검색 웹 페이지입니다. 사용자가 위치를 입력하면 Flask API가 Open-Meteo Geocoding API와 Forecast API를 호출하고, 브라우저가 오늘의 시간별 날씨와 기온 그래프를 렌더링합니다.

## 구조

- `app.py`: Flask 앱 엔트리포인트. Vercel이 이 파일의 `app` 변수를 로드합니다.
- `index.html`: 검색 UI와 SVG 기온 그래프 렌더링
- `api/weather.py`: 위치 검색 및 Open-Meteo 날씨 데이터 payload 생성 로직
- `fetch_hourly_weather.py`: Open-Meteo Forecast API 호출 공통 함수
- `requirements.txt`: Flask 런타임 의존성
- `vercel.json`: Vercel 함수 번들 제외 설정
- `.python-version`: Vercel Python 런타임 버전

## 로컬 실행

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:5000
```

검색창에 `Seoul`, `Busan`, `Tokyo`, `New York` 같은 도시명을 입력하면 `/api`가 호출되고 결과가 표시됩니다.

## Vercel 로컬 실행

Vercel 환경과 비슷하게 확인하려면 Vercel CLI를 사용합니다.

```bash
npx vercel dev
```

보통 아래 주소로 실행됩니다.

```text
http://localhost:3000
```

## Vercel 배포

```bash
npx vercel --prod
```

GitHub 저장소와 Vercel 프로젝트가 연결되어 있다면 `main` 브랜치에 push하면 자동으로 배포됩니다.

## API 직접 확인

```text
/api?location=Seoul
```

응답에는 위치 정보, 단위, 요약 정보, 00:00부터 23:00까지의 시간별 날씨 데이터가 포함됩니다.

## 로컬 PNG 그래프 생성

웹 페이지는 SVG 그래프를 브라우저에서 직접 그립니다. PNG 파일이 필요하면 로컬 가상환경에 `matplotlib`을 별도로 설치한 뒤 실행합니다.

```bash
.venv/bin/python -m pip install matplotlib
.venv/bin/python plot_temperature.py --output today_temperature.png
```

## 참고 문서

- Vercel Python Runtime: https://vercel.com/docs/functions/runtimes/python
- Open-Meteo Forecast API: https://open-meteo.com/en/docs
- Open-Meteo Geocoding API: https://open-meteo.com/en/docs/geocoding-api
