import { useState } from "react";

export default function ImportProductPage() {
  const [status, setStatus] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    setStatus("Submitting...");
    const res = await fetch("/api/products/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_url: payload.source_url,
        source_site: payload.source_site || "TAOBAO"
      })
    });
    if (res.ok) {
      setStatus("Imported and queued for localization");
      e.currentTarget.reset();
    } else {
      const detail = await res.json().catch(() => ({}));
      setStatus(detail?.detail ?? "Failed to import");
    }
  };

  return (
    <div className="max-w-xl space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Collect an overseas product</h1>
        <p className="text-sm text-slate-600">
          Paste a Taobao/Tmall/1688 URL to trigger scraping and Product creation.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-3 bg-white p-4 rounded shadow">
        <label className="block text-sm">Source URL
          <input name="source_url" className="mt-1 w-full border rounded px-3 py-2" required />
        </label>
        <label className="block text-sm">Source Site
          <input name="source_site" className="mt-1 w-full border rounded px-3 py-2" placeholder="TAOBAO" defaultValue="TAOBAO" />
        </label>
        <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Submit</button>
        {status && <div className="text-sm text-slate-600">{status}</div>}
      </form>
    </div>
  );
}
