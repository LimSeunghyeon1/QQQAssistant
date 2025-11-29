import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

async function fetchProducts() {
  const res = await fetch("/api/products");
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

async function translateProduct(productId: number) {
  const res = await fetch(`/api/products/${productId}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_locale: "ko-KR", provider: "gcloud" })
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? "Translation failed");
  }
  return res.json();
}

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["products"],
    queryFn: fetchProducts
  });
  const translateMutation = useMutation({
    mutationFn: translateProduct,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["products"] })
  });
  const [message, setMessage] = useState<string>("");

  const handleTranslate = async (productId: number) => {
    setMessage("Translating...");
    try {
      await translateMutation.mutateAsync(productId);
      setMessage("Translation completed");
    } catch (err) {
      setMessage((err as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">Products</h1>
          <p className="text-sm text-slate-600">
            Overseas items collected for resale. Import a URL, then translate and export them for SmartStore.
          </p>
        </div>
        {message && <div className="text-sm text-slate-600">{message}</div>}
      </div>
      {isLoading && <div>Loading...</div>}
      {error && <div className="text-red-600">{String(error)}</div>}
      <div className="grid grid-cols-1 gap-3">
        {data?.map((p: any) => (
          <div key={p.id} className="border rounded-lg p-4 bg-white shadow-sm space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{p.raw_title}</div>
                <div className="text-sm text-slate-600">{p.source_site}</div>
                <div className="text-sm text-slate-600 break-all">{p.source_url}</div>
              </div>
              <button
                onClick={() => handleTranslate(p.id)}
                className="px-3 py-1 text-sm bg-emerald-600 text-white rounded"
                disabled={translateMutation.isPending}
              >
                Translate to ko-KR
              </button>
            </div>
            <div className="text-sm text-slate-600">
              {p.options?.length ?? 0} options, {p.localizations?.length ?? 0} localizations
            </div>
            {p.localizations?.length > 0 && (
              <div className="bg-slate-50 border rounded p-2 text-sm space-y-1">
                <div className="font-medium text-slate-700">Localizations</div>
                {p.localizations.map((loc: any) => (
                  <div key={loc.id} className="flex items-center justify-between">
                    <span>{loc.locale}: {loc.title}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
