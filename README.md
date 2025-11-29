# QQQAssistant

## Use-case tests

End-to-end API happy paths are covered in `backend/tests/test_use_cases.py`:

- Product import and localization update
- Order creation with items and status transition history
- Shipment creation that links to orders and lists shipments

Run them locally:

```bash
cd backend
pip install -e .
pytest
```

## Environment configuration

Backend settings are read from environment variables (or a local `.env` file). Copy `.env.example` to `.env` and adjust values for your environment:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose | Example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string. Defaults to a local SQLite file for quick starts; point this to Postgres/MySQL in production. | `sqlite:///./qqq_assistant.db` or `postgresql+psycopg://user:pass@localhost:5432/qqq_assistant` |
| `SCRAPER_API_BASE_URL` | Base URL for the external product scraper/collector service. | `https://scraper.example.com` |
| `TRANSLATION_API_KEY` | API key/token for the translation provider used to prefill localized product text. | `sk-xxxx` |
| `SHIPPING_TRACKING_API_KEY` | Credential for the shipping-tracking API used to refresh shipment statuses. | `st-xxxx` |
| `SALES_CHANNEL_EXPORT_DIR` | Directory where generated upload/export files will be written. | `./exports` |

FastAPI automatically loads these via `pydantic-settings`; ensure the `.env` file sits at the repository root (same level as `backend/`).

## Work log

- `pip install -e backend` 실패: 외부 네트워크 프록시로 인해 `setuptools` 다운로드가 차단되어 백엔드 의존성 설치가 완료되지 않음.
- `pytest backend/tests` 실패: 위 의존성 설치 실패로 FastAPI 등을 찾지 못해 테스트 실행 불가.

## TODO

- 오프라인/사설 미러 등 네트워크 제약을 우회하거나 필요한 패키지를 수동으로 다운로드해 `pip install -e backend`가 성공하도록 처리.
- 의존성 설치가 완료된 환경에서 `pytest backend/tests`를 재실행해 유스케이스 테스트가 실제로 통과하는지 검증.
