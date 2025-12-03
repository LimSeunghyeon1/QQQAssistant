# QQQAssistant

## Running the stack (backend API + frontend)

The FastAPI application lives in `backend/app/main.py` and exposes REST endpoints for products, orders, exports, shipments, and purchase orders. The React/Vite frontend in `frontend/` talks to the same API.

Use the helper script to spin up both services with one command (virtualenv + editable backend install + Vite dev server):

```bash
./start.sh
```

### Quick start script

Use `start.sh` to boot the FastAPI app and hit the main flows with real HTTP calls (no tests involved). From the repository root:

```bash
./start.sh serve  # Just start the API server on 127.0.0.1:8000
./start.sh uc1    # Import a product then save localization data
./start.sh uc2    # Create an order and append status history
./start.sh uc3    # Create a shipment linked to an order
./start.sh        # Run all three use cases sequentially
```

Notes:

- The script will auto-activate `backend/.venv` when present; install dependencies first with `pip install -e backend`.
- Override `HOST`/`PORT` env vars if you want to bind to a different address.

### Running the full test suite

## Running the backend test suite

The repository’s backend unit and integration tests live under `backend/tests`. To execute them end-to-end:

```bash
cd backend
python -m venv .venv            # optional but recommended
source .venv/bin/activate
pip install -e .                # installs FastAPI and other dependencies in editable mode
pytest -q                       # or simply `pytest` for verbose output
```

Notes:

- Tests default to an in-memory SQLite database, so no external DB is required.
- If you already have dependencies installed system-wide, you can skip the virtualenv steps.

## Environment configuration

Backend settings are read from environment variables (or a local `.env` file). Copy `.env.example` to `.env` and adjust values for your environment:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose | Example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string. Defaults to a local SQLite file for quick starts; point this to Postgres/MySQL in production. | `sqlite:///./qqq_assistant.db` or `postgresql+psycopg://user:pass@localhost:5432/qqq_assistant` |
| `TRANSLATION_API_KEY` | API key/token for the translation provider used to prefill localized product text. | `sk-xxxx` |
| `TRANSLATION_PROVIDER` | Translation backend identifier (for example `gcloud`). | `gcloud` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to the Google Cloud service-account JSON file when using the Google translation API. | `/path/to/service-account.json` |
| `SALES_CHANNEL_EXPORT_DIR` | Directory where generated upload/export files will be written. | `./exports` |

FastAPI automatically loads these via `pydantic-settings`; ensure the `.env` file sits at the repository root (same level as `backend/`).

SmartStore CSV exports written by `/api/exports/channel/smartstore` are saved into `SALES_CHANNEL_EXPORT_DIR` in addition to being streamed in the response.

### Translation provider setup

The `/api/products/{product_id}/translate` endpoint now uses the Google Cloud Translation API when `TRANSLATION_PROVIDER=gcloud` (default). Provide either a `TRANSLATION_API_KEY` or a service-account JSON file pointed to by `GOOGLE_APPLICATION_CREDENTIALS` so the backend can authenticate when issuing translation requests.


## Work log

- `pip install -e backend` 실패: 외부 네트워크 프록시로 인해 `setuptools` 다운로드가 차단되어 백엔드 의존성 설치가 완료되지 않음.
- `pytest backend/tests` 실패: 위 의존성 설치 실패로 FastAPI 등을 찾지 못해 테스트 실행 불가.

## TODO

- 오프라인/사설 미러 등 네트워크 제약을 우회하거나 필요한 패키지를 수동으로 다운로드해 `pip install -e backend`가 성공하도록 처리.
- 의존성 설치가 완료된 환경에서 `pytest backend/tests`를 재실행해 유스케이스 테스트가 실제로 통과하는지 검증.
