import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

async function fetchProducts() {
  const res = await fetch("/api/products");
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

export default function SmartStoreExportPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [selected, setSelected] = useState<number[]>([]);
  const [status, setStatus] = useState<string>("");

  const toggle = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
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
      body: JSON.stringify({ product_ids: selected, template_type: "default" })
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
        {data?.map((p: any) => (
          <label key={p.id} className="border rounded-lg p-4 bg-white shadow-sm flex items-start gap-3">
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
