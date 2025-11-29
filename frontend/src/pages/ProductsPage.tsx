import { useQuery } from "@tanstack/react-query";

async function fetchProducts() {
  const res = await fetch("/api/products");
  if (!res.ok) throw new Error("Failed to load products");
  return res.json();
}

export default function ProductsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["products"],
    queryFn: fetchProducts
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Products</h1>
        <p className="text-sm text-slate-600">
          Overseas items collected for resale. Add more via the Import page.
        </p>
      </div>
      {isLoading && <div>Loading...</div>}
      {error && <div className="text-red-600">{String(error)}</div>}
      <div className="grid grid-cols-1 gap-3">
        {data?.map((p: any) => (
          <div key={p.id} className="border rounded-lg p-4 bg-white shadow-sm">
            <div className="font-medium">{p.raw_title}</div>
            <div className="text-sm text-slate-600">{p.source_site}</div>
            <div className="text-sm text-slate-600">{p.source_url}</div>
            <div className="text-sm text-slate-600">
              {p.options?.length ?? 0} options, {p.localizations?.length ?? 0} localizations
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
