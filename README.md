# Open-Meteo Weather Web Page

Vercel 배포를 기준으로 만든 날씨 검색 웹 페이지입니다. 사용자가 위치를 입력하면 Vercel Python Function이 Open-Meteo Geocoding API와 Forecast API를 호출하고, 브라우저가 오늘의 시간별 날씨와 기온 그래프를 렌더링합니다.

## Vercel 배포 구조

- `index.html`: Vercel에서 정적으로 제공되는 웹 페이지
- `api/weather.py`: Vercel Python Serverless Function
- `fetch_hourly_weather.py`: Open-Meteo Forecast API 호출 로직
- `vercel.json`: Vercel 함수 번들 제외 설정
- `.vercelignore`: 배포 업로드 제외 파일
- `.python-version`: Vercel Python 런타임 버전
- `requirements.txt`: Vercel Python Function 의존성 파일

웹 페이지 배포에는 별도 Python 패키지가 필요하지 않아 `requirements.txt`에는 런타임 의존성을 넣지 않았습니다. `matplotlib`은 `plot_temperature.py`로 PNG 그래프를 로컬에서 만들 때만 필요합니다.

## 로컬에서 Vercel 방식으로 실행

Vercel CLI를 사용합니다.

```bash
npx vercel dev
```

브라우저에서 표시된 로컬 주소를 엽니다. 보통 아래 주소입니다.

```text
http://localhost:3000
```

검색창에 `Seoul`, `Busan`, `Tokyo`, `New York` 같은 도시명을 입력하면 `/api/weather`가 호출되고 결과가 표시됩니다.

## Vercel에 배포

Vercel CLI로 배포할 수 있습니다.

```bash
npx vercel
```

프로덕션 배포는 다음 명령을 사용합니다.

```bash
npx vercel --prod
```

GitHub 저장소와 Vercel 프로젝트를 연결했다면, 이 폴더를 push하면 Vercel이 자동으로 `index.html`과 `api/weather.py`를 배포합니다.

## API 직접 확인

로컬 또는 배포 환경에서 아래 URL을 호출하면 JSON 응답을 확인할 수 있습니다.

```text
/api/weather?location=Seoul
```

응답에는 위치 정보, 단위, 요약 정보, 00:00부터 23:00까지의 시간별 날씨 데이터가 포함됩니다.

## 로컬 PNG 그래프 생성

웹 페이지는 SVG 그래프를 브라우저에서 직접 그립니다. PNG 파일이 필요하면 로컬 가상환경에 `matplotlib`을 설치한 뒤 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install matplotlib
.venv/bin/python plot_temperature.py --output today_temperature.png
```

## 참고 문서

- Vercel Python Runtime: https://vercel.com/docs/functions/runtimes/python
- Open-Meteo Forecast API: https://open-meteo.com/en/docs
- Open-Meteo Geocoding API: https://open-meteo.com/en/docs/geocoding-api
