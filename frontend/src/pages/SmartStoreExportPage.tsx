import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

type Product = {
  id: number;
  raw_title: string;
  source_url: string;
  localizations?: any[];
  exchange_rate?: number | null;
  margin_rate?: number | null;
  vat_rate?: number | null;
  shipping_fee?: number | null;
};

type PricingForm = {
  exchange_rate: string;
  margin_rate: string;
  vat_rate: string;
  shipping_fee: string;
};

async function fetchProducts() {
  const res = await fetch("/api/products");
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

export default function SmartStoreExportPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [selected, setSelected] = useState<number[]>([]);
  const [status, setStatus] = useState<string>("");
  const [messages, setMessages] = useState<Record<number, string>>({});
  const [formState, setFormState] = useState<Record<number, PricingForm>>({});

  useEffect(() => {
    if (!data) return;
    setFormState((prev) => {
      const next = { ...prev };
      data.forEach((p: Product) => {
        if (!next[p.id]) {
          next[p.id] = {
            exchange_rate: p.exchange_rate?.toString() ?? "",
            margin_rate: p.margin_rate?.toString() ?? "",
            vat_rate: p.vat_rate?.toString() ?? "",
            shipping_fee: p.shipping_fee?.toString() ?? "",
          };
        }
      });
      return next;
    });
  }, [data]);

  const toggle = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const updateField = (id: number, field: keyof PricingForm, value: string) => {
    setFormState((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || { exchange_rate: "", margin_rate: "", vat_rate: "", shipping_fee: "" }),
        [field]: value,
      },
    }));
  };

  const handleSave = async (productId: number) => {
    const form = formState[productId] || { exchange_rate: "", margin_rate: "", vat_rate: "", shipping_fee: "" };
    const payload: Record<string, number> = {};

    const parseNumber = (value: string) => (value === "" ? undefined : Number(value));

    const exchangeRate = parseNumber(form.exchange_rate);
    const margin = parseNumber(form.margin_rate);
    const vat = parseNumber(form.vat_rate);
    const shipping = parseNumber(form.shipping_fee);

    if (exchangeRate !== undefined && (!Number.isFinite(exchangeRate) || exchangeRate <= 0)) {
      setMessages((prev) => ({ ...prev, [productId]: "환율은 0보다 커야 합니다." }));
      return;
    }
    if (shipping !== undefined && (!Number.isFinite(shipping) || shipping < 0)) {
      setMessages((prev) => ({ ...prev, [productId]: "배송비는 0 이상이어야 합니다." }));
      return;
    }
    if (margin !== undefined && !Number.isFinite(margin)) {
      setMessages((prev) => ({ ...prev, [productId]: "마진율은 숫자여야 합니다." }));
      return;
    }
    if (vat !== undefined && !Number.isFinite(vat)) {
      setMessages((prev) => ({ ...prev, [productId]: "VAT는 숫자여야 합니다." }));
      return;
    }

    if (exchangeRate !== undefined) payload.exchange_rate = exchangeRate;
    if (margin !== undefined) payload.margin_rate = margin;
    if (vat !== undefined) payload.vat_rate = vat;
    if (shipping !== undefined) payload.shipping_fee = shipping;

    if (Object.keys(payload).length === 0) {
      setMessages((prev) => ({ ...prev, [productId]: "변경할 값이 없습니다." }));
      return;
    }

    const res = await fetch(`/api/products/${productId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      setMessages((prev) => ({ ...prev, [productId]: detail?.detail ?? "저장에 실패했습니다." }));
      return;
    }

    setMessages((prev) => ({ ...prev, [productId]: "저장되었습니다." }));
    queryClient.invalidateQueries({ queryKey: ["products"] });
  };

  const handleExport = async () => {
    if (selected.length === 0) {
      setStatus("Select at least one product");
      return;
    }
    setStatus("Preparing CSV...");
    const res = await fetch("/api/exports/channel/smartstore", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_ids: selected, template_type: "default" }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      setStatus(detail?.detail ?? "Export failed");
      return;
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "smartstore_products.csv";
    anchor.click();
    window.URL.revokeObjectURL(url);
    setStatus("Export ready. Download started.");
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">SmartStore Export</h1>
          <p className="text-sm text-slate-600">Choose localized products and download the SmartStore bulk upload CSV.</p>
        </div>
        {status && <div className="text-sm text-slate-600">{status}</div>}
      </div>
      {isLoading && <div>Loading products...</div>}
      {error && <div className="text-red-600">{String(error)}</div>}
      <div className="grid grid-cols-1 gap-3">
        {data?.map((p: Product) => (
          <div key={p.id} className="border rounded-lg p-4 bg-white shadow-sm space-y-3">
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={selected.includes(p.id)}
                onChange={() => toggle(p.id)}
                className="mt-1"
              />
              <div className="space-y-1">
                <div className="font-medium">{p.raw_title}</div>
                <div className="text-sm text-slate-600">Localizations: {p.localizations?.length ?? 0}</div>
                <div className="text-sm text-slate-600 break-all">{p.source_url}</div>
              </div>
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <label className="block">
                <div className="text-slate-700">환율</div>
                <input
                  type="number"
                  step="0.0001"
                  className="mt-1 w-full border rounded px-2 py-1"
                  value={(formState[p.id]?.exchange_rate) ?? ""}
                  onChange={(e) => updateField(p.id, "exchange_rate", e.target.value)}
                  placeholder="기본값"
                />
              </label>
              <label className="block">
                <div className="text-slate-700">마진율 %</div>
                <input
                  type="number"
                  step="0.1"
                  className="mt-1 w-full border rounded px-2 py-1"
                  value={(formState[p.id]?.margin_rate) ?? ""}
                  onChange={(e) => updateField(p.id, "margin_rate", e.target.value)}
                  placeholder="기본값"
                />
              </label>
              <label className="block">
                <div className="text-slate-700">VAT %</div>
                <input
                  type="number"
                  step="0.1"
                  className="mt-1 w-full border rounded px-2 py-1"
                  value={(formState[p.id]?.vat_rate) ?? ""}
                  onChange={(e) => updateField(p.id, "vat_rate", e.target.value)}
                  placeholder="기본값"
                />
              </label>
              <label className="block">
                <div className="text-slate-700">배송비</div>
                <input
                  type="number"
                  step="100"
                  className="mt-1 w-full border rounded px-2 py-1"
                  value={(formState[p.id]?.shipping_fee) ?? ""}
                  onChange={(e) => updateField(p.id, "shipping_fee", e.target.value)}
                  placeholder="기본값"
                />
              </label>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <button
                onClick={() => handleSave(p.id)}
                className="px-3 py-1 bg-emerald-600 text-white rounded"
                type="button"
              >
                Save product pricing
              </button>
              {messages[p.id] && <span className="text-slate-700">{messages[p.id]}</span>}
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={handleExport}
        className="px-4 py-2 bg-indigo-600 text-white rounded"
        disabled={isLoading}
      >
        Export selected
      </button>
    </div>
  );
}
