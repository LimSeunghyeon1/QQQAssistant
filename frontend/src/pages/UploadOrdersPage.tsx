import { useState } from "react";

export default function UploadOrdersPage() {
  const [message, setMessage] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);
    setMessage("Uploading...");
    const res = await fetch("/api/orders:upload", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      setMessage("Uploaded and parsed");
      form.reset();
    } else {
      setMessage("Failed to upload");
    }
  };

  return (
    <div className="max-w-xl space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Upload order spreadsheet</h1>
        <p className="text-sm text-slate-600">Excel/CSV exports from Coupang or Naver.</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-3 bg-white p-4 rounded shadow">
        <input type="file" name="file" accept=".csv,.xlsx" required />
        <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Upload</button>
        {message && <div className="text-sm text-slate-700">{message}</div>}
      </form>
    </div>
  );
}
