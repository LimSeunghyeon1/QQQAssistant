import { useState } from "react";

export default function ImportProductPage() {
  const [status, setStatus] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    setStatus("Submitting...");
    const res = await fetch("/api/products:import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_url: payload.source_url,
        source_site: payload.source_site,
        raw_title: payload.raw_title,
        raw_price: Number(payload.raw_price),
        raw_currency: payload.raw_currency,
        options: []
      })
    });
    if (res.ok) {
      setStatus("Imported!");
      e.currentTarget.reset();
    } else {
      setStatus("Failed to import");
    }
  };

  return (
    <div className="max-w-xl space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Add overseas product URL</h1>
        <p className="text-sm text-slate-600">Submit a link to scrape and store.</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-3 bg-white p-4 rounded shadow">
        <label className="block text-sm">Source URL
          <input name="source_url" className="mt-1 w-full border rounded px-3 py-2" required />
        </label>
        <label className="block text-sm">Source Site
          <input name="source_site" className="mt-1 w-full border rounded px-3 py-2" placeholder="TAOBAO" required />
        </label>
        <label className="block text-sm">Raw Title
          <input name="raw_title" className="mt-1 w-full border rounded px-3 py-2" required />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm">Raw Price
            <input name="raw_price" type="number" step="0.01" className="mt-1 w-full border rounded px-3 py-2" required />
          </label>
          <label className="block text-sm">Currency
            <input name="raw_currency" className="mt-1 w-full border rounded px-3 py-2" defaultValue="CNY" required />
          </label>
        </div>
        <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Submit</button>
        {status && <div className="text-sm text-slate-600">{status}</div>}
      </form>
    </div>
  );
}
