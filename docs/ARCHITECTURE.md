# QQQ Purchase Agency Assistant Architecture

## Stack Overview
- **Backend**: FastAPI application in `backend/app/main.py` using Python 3.11, SQLAlchemy ORM sessions (`backend/app/database.py`), and Pydantic v2 schemas.
- **Database**: SQLite by default via `DATABASE_URL`, with lightweight in-place schema upgrades to keep existing tables compatible when optional columns are added.
- **Frontend**: React 18 + TypeScript bootstrapped with Vite (`frontend/`), React Router for page structure, and React Query for client-side data fetching and caching.
- **Build/Tooling**: `start.sh` boots the editable FastAPI install and Vite dev server together; environment configuration is read from `.env` through `pydantic-settings`.

## Backend Architecture
### Application startup & persistence
- The ASGI app is created by `create_app()` and includes routers for products, orders, shipments, exports, and purchase orders before exposing `/health` for monitoring.
- Database sessions are provided per-request and committed/rolled back centrally; `apply_schema_upgrades()` patches existing SQLite tables with new columns (e.g., localized option names, cleaned image URLs) after `Base.metadata.create_all` runs.

### Domain model highlights
- **Product** entities store scraped source metadata, raw and cleaned image URLs, and own multiple **ProductOption** rows that can carry a localized name for exports.
- **ProductLocalizedInfo** captures translated titles/descriptions per locale.
- **Order**, **OrderItem**, **Shipment**, and **OrderShipmentLink** track downstream fulfillment, while **OrderStatusHistory** logs changes.
- **PurchaseOrder**, **PurchaseOrderItem**, **PurchaseOrderSourceLink**, and **PurchaseOrderStatusHistory** aggregate customer orders into supplier-facing purchase batches.

### Core services & flows
- **Product import**: `ProductImportService` routes `/api/products/import` requests to a Taobao scraper, deduplicates by source URL, masks text in product images through `ImageCleanupService`, and persists products/options with cleaned image variants.
- **Translation**: `/api/products/{product_id}/translate` calls `TranslationService`, which prefers the Google Cloud Translation API (configurable via `TRANSLATION_PROVIDER`/credentials) and falls back to deterministic stub output when credentials are absent, while saving localized option names and info records.
- **Exports**: `SmartStoreExporter` powers `/api/exports/channel/smartstore`, converting selected products to CSV with pricing adjustments (exchange rate, margin, VAT, shipping) and appending a configurable return-policy image block; files are streamed to the client and also written to `SALES_CHANNEL_EXPORT_DIR`.
- **Orders & shipments**: `/api/orders` supports create/list/status updates; `/api/shipments` links carrier tracking to orders through repository-backed services.
- **Purchase orders**: `/api/purchase-orders` aggregates `NEW` orders by product/option into supplier-facing purchase orders, writes linkage records back to the originating order items, and marks customer orders as `PENDING_PURCHASE`.

### REST API surface (current)
- `POST /api/products/import` — Scrape Taobao/Tmall/1688 product details and create Product + ProductOption rows.
- `GET /api/products` — List stored products.
- `PUT /api/products/{product_id}/localization` — Save localized title/description and option display format.
- `POST /api/products/{product_id}/translate` — Translate titles/options using the configured provider and persist `ProductLocalizedInfo`.
- `POST /api/exports/channel/smartstore` — Export selected products to SmartStore-ready CSV with pricing and return-policy template settings.
- `POST /api/orders` / `GET /api/orders` / `PUT /api/orders/{order_id}/status` — Create/list/update orders with history logging.
- `POST /api/shipments` / `GET /api/shipments` — Create and view shipments linked to orders.
- `POST /api/purchase-orders` / `GET /api/purchase-orders/{po_id}` / `PUT /api/purchase-orders/{po_id}/status` — Generate purchase orders from outstanding customer orders and manage their lifecycle.

## Frontend Architecture
- The SPA root (`frontend/src/main.tsx`) wires React Router routes and a shared QueryClient. Navigation covers product management, imports, SmartStore exports, order upload/list, purchase orders, and shipments.
- Page components live under `frontend/src/pages/` and call the REST API directly (e.g., `ImportProductPage` POSTs to `/api/products/import`). Styling relies on Tailwind CSS classes defined in `index.css` and related configs.

## Source Layout
```
backend/
  app/
    api/              # FastAPI routers for products, orders, shipments, exports, purchase-orders
    services/         # Business logic: scraping, translation, pricing, exports, purchase order aggregation
    repositories/     # Data access helpers wrapping SQLAlchemy sessions
    models/           # Domain entities
    database.py, main.py, config.py
frontend/
  src/
    pages/            # React route components
    components/       # Shared UI (reserved for growth)
  vite.config.ts, tailwind.config.js, package.json
```
