import { useState } from "react";

interface PurchaseOrderItem {
  id: number;
  product_id: number;
  product_option_id?: number | null;
  quantity: number;
  unit_cost: number;
  line_total: number;
  source_links?: { id: number; order_id: number; order_item_id: number; source_quantity: number }[];
}

interface PurchaseOrder {
  id: number;
  supplier_name: string;
  status: string;
  currency: string;
  total_amount: number;
  items: PurchaseOrderItem[];
}

const STATUSES = ["CREATED", "SENT", "PARTIAL_RECEIVED", "RECEIVED", "CANCELLED"];

export default function PurchaseOrdersPage() {
  const [orderIds, setOrderIds] = useState<string>("");
  const [poIdQuery, setPoIdQuery] = useState<string>("");
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [message, setMessage] = useState<string>("");

  const parseOrderIds = (): number[] | null => {
    const ids = orderIds
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean)
      .map((v) => Number(v))
      .filter((v) => !Number.isNaN(v));
    return ids.length > 0 ? ids : null;
  };

  const handleCreate = async () => {
    setMessage("Creating purchase orders...");
    const res = await fetch("/api/purchase-orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_ids: parseOrderIds() })
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      setMessage(detail?.detail ?? "Creation failed");
      return;
    }
    const data = await res.json();
    setPurchaseOrders(data);
    setMessage(`Created ${data.length} purchase order(s).`);
  };

  const handleFetchById = async () => {
    if (!poIdQuery) return;
    setMessage("Loading purchase order...");
    const res = await fetch(`/api/purchase-orders/${poIdQuery}`);
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      setMessage(detail?.detail ?? "Lookup failed");
      return;
    }
    const data = await res.json();
    setPurchaseOrders([data]);
    setMessage(`Loaded purchase order #${data.id}`);
  };

  const handleStatusUpdate = async (poId: number, newStatus: string) => {
    setMessage("Updating status...");
    const res = await fetch(`/api/purchase-orders/${poId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_status: newStatus })
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      setMessage(detail?.detail ?? "Status update failed");
      return;
    }
    const updated = await res.json();
    setPurchaseOrders((prev) =>
      prev.map((po) => (po.id === updated.id ? updated : po))
    );
    setMessage(`Purchase order #${poId} set to ${newStatus}`);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Purchase Orders</h1>
          <p className="text-sm text-slate-600">Aggregate NEW sales orders into supplier-facing purchase orders.</p>
        </div>
        {message && <div className="text-sm text-slate-600">{message}</div>}
      </div>

      <div className="bg-white rounded shadow p-4 space-y-3">
        <div className="text-sm font-medium text-slate-700">Create from NEW orders</div>
        <label className="text-sm block">
          Order IDs (optional, comma separated)
          <input
            value={orderIds}
            onChange={(e) => setOrderIds(e.target.value)}
            className="mt-1 w-full border rounded px-3 py-2"
            placeholder="Leave empty to include all NEW orders"
          />
        </label>
        <button onClick={handleCreate} className="px-4 py-2 bg-indigo-600 text-white rounded">
          Create purchase order
        </button>
      </div>

      <div className="bg-white rounded shadow p-4 space-y-3">
        <div className="text-sm font-medium text-slate-700">Fetch by ID</div>
        <div className="flex gap-2 items-center">
          <input
            value={poIdQuery}
            onChange={(e) => setPoIdQuery(e.target.value)}
            className="border rounded px-3 py-2"
            placeholder="Purchase order ID"
          />
          <button onClick={handleFetchById} className="px-3 py-2 bg-slate-700 text-white rounded">Load</button>
        </div>
      </div>

      <div className="space-y-3">
        {purchaseOrders.map((po) => (
          <div key={po.id} className="border rounded-lg p-4 bg-white shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">#{po.id} · {po.supplier_name}</div>
                <div className="text-sm text-slate-600">Total: {po.total_amount} {po.currency}</div>
                <div className="text-sm text-slate-600">Status: {po.status}</div>
              </div>
              <select
                onChange={(e) => handleStatusUpdate(po.id, e.target.value)}
                defaultValue=""
                className="border rounded px-2 py-1 text-sm"
              >
                <option value="" disabled>Update status</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="text-sm text-slate-600">Items</div>
            <div className="space-y-2 text-sm">
              {po.items.map((item) => (
                <div key={item.id} className="bg-slate-50 border rounded p-2">
                  <div>Product #{item.product_id} / Option {item.product_option_id ?? "-"}</div>
                  <div>Qty: {item.quantity} · Unit: {item.unit_cost} · Line: {item.line_total}</div>
                  {item.source_links && item.source_links.length > 0 && (
                    <div className="text-slate-700">Links: {item.source_links.map((l) => `Order ${l.order_id} (${l.source_quantity})`).join(", ")}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
