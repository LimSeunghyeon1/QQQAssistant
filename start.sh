#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
PORT=${PORT:-8000}
HOST=${HOST:-127.0.0.1}
API_BASE="http://${HOST}:${PORT}"

usage() {
  cat <<'USAGE'
Usage: ./start.sh [uc1|uc2|uc3|all|serve]

Runs the FastAPI app and exercises the main flows with real HTTP calls:
  uc1   Import a product and update localization
  uc2   Create an order and update its status history
  uc3   Create a shipment linked to orders
  all   Run uc1 → uc2 → uc3 sequentially (default)
  serve Start only the FastAPI server (no demo calls)

Tips:
- If backend/.venv exists, it will be activated automatically.
- Install dependencies beforehand (e.g., `pip install -e backend`).
- Override HOST/PORT env vars to change the server bind address.
USAGE
}

if [[ ${1-} == "-h" || ${1-} == "--help" ]]; then
  usage
  exit 0
fi

run_target=${1-all}

cd "$BACKEND_DIR"

if [[ -d .venv ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

start_server() {
  echo "Starting FastAPI server at ${API_BASE}..."
  python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --log-level warning &
  SERVER_PID=$!
  trap '[[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" >/dev/null 2>&1 || true' EXIT

  for _ in {1..30}; do
    if curl -s "${API_BASE}/health" >/dev/null; then
      echo "Server is ready."
      return
    fi
    sleep 1
  done

  echo "Server did not become ready in time." >&2
  exit 1
}

run_uc1() {
  python - <<PY
import httpx

client = httpx.Client(base_url="${API_BASE}")

print("[uc1] Importing product...")
resp = client.post(
    "/api/products/import",
    json={"source_url": "https://example.com/item/uc1", "source_site": "TAOBAO"},
)
resp.raise_for_status()
product = resp.json()
product_id = product["id"]
print(f"[uc1] Imported product #{product_id}")

print("[uc1] Updating localization...")
loc_resp = client.put(
    f"/api/products/{product_id}/localization",
    json={
        "locale": "ko_KR",
        "title": "데모 가방",
        "description": "가볍고 튼튼한 데일리 백",
        "option_display_name_format": "{color}/{size}",
    },
)
loc_resp.raise_for_status()
print("[uc1] Localization saved.")
PY
}

run_uc2() {
  python - <<PY
from datetime import datetime
import httpx

client = httpx.Client(base_url="${API_BASE}")

print("[uc2] Importing product for order...")
product_resp = client.post(
    "/api/products/import",
    json={"source_url": "https://example.com/item/uc2", "source_site": "TAOBAO"},
)
product_resp.raise_for_status()
product = product_resp.json()
product_id = product["id"]
option_id = product["options"][0]["id"] if product["options"] else None

print("[uc2] Creating order...")
order_resp = client.post(
    "/api/orders",
    json={
        "external_order_id": "ORDER-UC2",
        "channel_name": "COUPANG",
        "customer_name": "홍길동",
        "customer_phone": "010-1234-5678",
        "customer_address": "서울시 어딘가",
        "order_datetime": datetime.utcnow().isoformat(),
        "status": "NEW",
        "total_amount_krw": 23000,
        "items": [
            {
                "product_id": product_id,
                "product_option_id": option_id,
                "quantity": 1,
                "unit_price_krw": 23000,
            }
        ],
    },
)
order_resp.raise_for_status()
order = order_resp.json()
order_id = order["id"]
print(f"[uc2] Created order #{order_id} with status {order['status']}")

print("[uc2] Updating order status to OVERSEA_ORDERED...")
update_resp = client.put(
    f"/api/orders/{order_id}/status",
    params={"new_status": "OVERSEA_ORDERED", "reason": "발주 완료"},
)
update_resp.raise_for_status()
print("[uc2] Status updated. History length:", len(update_resp.json()["status_history"]))
PY
}

run_uc3() {
  python - <<PY
from datetime import datetime
import httpx

client = httpx.Client(base_url="${API_BASE}")

print("[uc3] Importing product for shipment demo...")
product_resp = client.post(
    "/api/products/import",
    json={"source_url": "https://example.com/item/uc3", "source_site": "TAOBAO"},
)
product_resp.raise_for_status()
product = product_resp.json()
product_id = product["id"]
option_id = product["options"][0]["id"] if product["options"] else None

print("[uc3] Creating order linked to shipment...")
order_resp = client.post(
    "/api/orders",
    json={
        "external_order_id": "ORDER-UC3",
        "channel_name": "NAVER",
        "customer_name": "김철수",
        "customer_phone": "010-9999-8888",
        "customer_address": "부산 somewhere",
        "order_datetime": datetime.utcnow().isoformat(),
        "status": "OVERSEA_IN_TRANSIT",
        "total_amount_krw": 15000,
        "items": [
            {
                "product_id": product_id,
                "product_option_id": option_id,
                "quantity": 2,
                "unit_price_krw": 7500,
            }
        ],
    },
)
order_resp.raise_for_status()
order_id = order_resp.json()["id"]
print(f"[uc3] Created order #{order_id}")

print("[uc3] Creating shipment linked to the order...")
shipment_resp = client.post(
    "/api/shipments",
    json={
        "carrier_name": "CJ Logistics",
        "tracking_number": "TRACK-UC3",
        "shipment_type": "OVERSEA",
        "linked_order_ids": [order_id],
    },
)
shipment_resp.raise_for_status()
shipment = shipment_resp.json()
print(f"[uc3] Shipment #{shipment['id']} created with tracking {shipment['tracking_number']}")

print("[uc3] Listing shipments...")
list_resp = client.get("/api/shipments")
list_resp.raise_for_status()
print("[uc3] Total shipments:", len(list_resp.json()))
PY
}

case "$run_target" in
  serve)
    python -m uvicorn app.main:app --host "$HOST" --port "$PORT"
    ;;
  uc1)
    start_server
    run_uc1
    ;;
  uc2)
    start_server
    run_uc2
    ;;
  uc3)
    start_server
    run_uc3
    ;;
  all)
    start_server
    run_uc1
    run_uc2
    run_uc3
    ;;
  *)
    echo "Unknown target: $run_target" >&2
    usage
    exit 1
    ;;
esac
