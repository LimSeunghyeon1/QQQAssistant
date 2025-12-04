# QQQAssistant

## Overview

QQQAssistant is a purchase-agency helper for Taobao/Shopee-style product sourcing. The FastAPI backend (`backend/app/main.py`) scrapes products, translates and localizes content, aggregates purchase orders, and exports SmartStore-ready CSVs. The React 18 + Vite frontend (`frontend/`) talks to the same API for day-to-day flows like product imports, exports, order uploads, shipment tracking, and purchase-order batching. For deeper details on domain models and services, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Running the stack (backend API + frontend)

You can run everything locally with the helper script or via Docker Compose.

### Prerequisites

1. Install Python 3.10+ and Node.js/npm on your machine. The helper script will create a virtualenv and install dependencies, but the runtimes themselves must be available.
2. Create and populate a `.env` file: `cp .env.example .env`, then fill in the Taobao app key/secret and **active session key** issued from the Taobao Open Platform so product lookups succeed.

### Option A: Local dev servers

Use `start.sh` from the repository root to bootstrap both services (editable backend install + Vite dev server):

```bash
./start.sh
```

This starts the backend on `http://localhost:8000` and the frontend on `http://localhost:5173` (which proxies API calls to the backend). Press `Ctrl+C` in the terminal to stop both processes.

### Option B: Docker Compose

If you prefer containers, bring up the stack with the provided compose file:

```bash
docker compose up --build
```

The backend will be available on port `8000` with a `/health` check, and the frontend dev server on port `5173` configured to talk to the backend service name. Compose mounts your local `backend/` and `frontend/` code for live reload while developing.

### Basic workflow (Taobao → SmartStore)

1. Start the stack (Option A or B) and open `http://localhost:5173`.
2. Paste a Taobao product URL into the landing page to scrape product/options and cleaned image variants.
3. Translate and localize content via the UI, which calls `/api/products/{product_id}/translate` and stores localized names/descriptions.
4. Tweak pricing/margins and export selected products through `/api/exports/channel/smartstore`, which streams a CSV and also writes it to `SALES_CHANNEL_EXPORT_DIR`.
5. Upload orders, manage shipments, and batch outstanding orders into supplier purchase orders from the same UI.

### Manual verification: SmartStore pricing overrides

Because SmartStore uploads are sensitive to pricing, perform a quick manual check when you change per-product overrides:

1. Import a product and set `환율/마진율/VAT/배송비` from the import form or SmartStore export page cards, then click **Save product pricing**.
2. Export a CSV for the same product(s) from **SmartStore Export**.
3. Open the generated CSV and confirm the `판매가` column reflects your saved overrides (e.g., adjust one field and export again to verify the value changes). If the price does not change, re-save the overrides and retry the export.

## Running the backend test suite

Backend unit and integration tests live under `backend/tests`. To execute them end-to-end:

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
| `TRANSLATION_PROVIDER` | Translation backend identifier (for example `gcloud`). Defaults to Google Cloud with a deterministic stub fallback when credentials are absent. | `gcloud` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to the Google Cloud service-account JSON file when using the Google translation API. | `/path/to/service-account.json` |
| `TAOBAO_APP_KEY` / `TAOBAO_APP_SECRET` | Application credentials from the Taobao Open Platform. | `your-app-key` / `your-app-secret` |
| `TAOBAO_SESSION_KEY` | Active Taobao session key (grant token). Required for fetching products by URL. | `your-session-key` |
| `TAOBAO_API_URL` | Taobao Open Platform API host. | `https://gw.api.taobao.com/router/rest` |
| `SALES_CHANNEL_EXPORT_DIR` | Directory where generated upload/export files will be written. | `./exports` |
| `EXCHANGE_RATE` / `DEFAULT_MARGIN` / `VAT_RATE` / `DEFAULT_DELIVERY` | Optional pricing defaults when a product does not define overrides. Leave unset to use the baked-in defaults from `app.config.Settings`. | `185.2` / `15` / `10` / `3500` |
| `RETURN_POLICY_IMAGE_URL` | Optional absolute/public URL appended to exported descriptions as an `<img>` block (e.g., return/AS policy banner). If unset, no image is added. | `https://example.com/return-policy.png` |

FastAPI automatically loads these via `pydantic-settings`; ensure the `.env` file sits at the repository root (same level as `backend/`). SmartStore CSV exports are saved into `SALES_CHANNEL_EXPORT_DIR` in addition to being streamed in the response.

### Frontend channel support toggle

The React/Vite frontend reads `VITE_*` variables from the same `.env` file. To control which sales channels are treated as “지원됨” in the UI dropdowns and status messages, set `VITE_SUPPORTED_CHANNEL_LABELS` to a comma-separated list of channel labels (case-insensitive) that match the visible names in the selector. For example:

```bash
# Enables SmartStore and marks Coupang as supported while leaving others as "지원 예정"
VITE_SUPPORTED_CHANNEL_LABELS=SmartStore,Coupang
```

If you omit this variable, only SmartStore is marked as supported by default.
