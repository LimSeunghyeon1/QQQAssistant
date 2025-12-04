import { useState } from "react";

export default function ImportProductPage() {
  const [status, setStatus] = useState<{
    message: string;
    tone: "idle" | "info" | "success" | "error";
  }>({ message: "", tone: "idle" });

  const parseNumber = (value: FormDataEntryValue | null) => {
    if (value === null || value === "") return undefined;
    const num = Number(value);
    return Number.isFinite(num) ? num : undefined;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    const overrides = {
      exchange_rate: parseNumber(formData.get("exchange_rate")),
      margin_rate: parseNumber(formData.get("margin_rate")),
      vat_rate: parseNumber(formData.get("vat_rate")),
      shipping_fee: parseNumber(formData.get("shipping_fee")),
    };

    if (overrides.exchange_rate !== undefined && overrides.exchange_rate <= 0) {
      setStatus({ message: "환율은 0보다 커야 합니다.", tone: "error" });
      return;
    }
    if (overrides.shipping_fee !== undefined && overrides.shipping_fee < 0) {
      setStatus({ message: "배송비는 0 이상이어야 합니다.", tone: "error" });
      return;
    }

    setStatus({ message: "Submitting...", tone: "info" });
    const res = await fetch("/api/products/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_url: payload.source_url,
        source_site: payload.source_site || "TAOBAO",
      }),
    });
    if (res.ok) {
      const product = await res.json();
      const updatePayload: Record<string, number> = {};
      (Object.keys(overrides) as (keyof typeof overrides)[]).forEach((key) => {
        const value = overrides[key];
        if (value !== undefined) {
          updatePayload[key] = value;
        }
      });

      if (product?.id && Object.keys(updatePayload).length > 0) {
        const updateRes = await fetch(`/api/products/${product.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatePayload),
        });
        if (!updateRes.ok) {
          const detail = await updateRes.json().catch(() => ({}));
          setStatus({
            message: detail?.detail ?? "세부 설정 저장에 실패했습니다.",
            tone: "error",
          });
          return;
        }
      }

      setStatus({
        message: "Imported and queued for localization",
        tone: "success",
      });
      e.currentTarget.reset();
    } else {
      const detail = await res.json().catch(() => ({}));
      setStatus({
        message:
          detail?.detail ??
          "상품 정보를 불러오지 못했습니다. URL을 확인하거나 잠시 후 다시 시도해주세요.",
        tone: "error",
      });
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
          <input name="source_site" className="mt-1 w-full border rounded px-3 py-2" placeholder="TAOBAO" defaultValue="TAOBAO"/>
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm">환율 (선택)
            <input type="number" step="0.0001" name="exchange_rate" className="mt-1 w-full border rounded px-3 py-2" placeholder="환경설정 기본값" />
          </label>
          <label className="block text-sm">마진율 % (선택)
            <input type="number" step="0.1" name="margin_rate" className="mt-1 w-full border rounded px-3 py-2" placeholder="환경설정 기본값" />
          </label>
          <label className="block text-sm">VAT % (선택)
            <input type="number" step="0.1" name="vat_rate" className="mt-1 w-full border rounded px-3 py-2" placeholder="환경설정 기본값" />
          </label>
          <label className="block text-sm">배송비 원 (선택)
            <input type="number" step="100" name="shipping_fee" className="mt-1 w-full border rounded px-3 py-2" placeholder="환경설정 기본값" />
          </label>
        </div>
        <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">Submit</button>
        {status.message && (
          <div
            className={`text-sm px-3 py-2 rounded ${
              status.tone === "error"
                ? "bg-red-100 text-red-700"
                : status.tone === "success"
                  ? "bg-green-100 text-green-700"
                  : "bg-slate-100 text-slate-700"
            }`}
            role={status.tone === "error" ? "alert" : undefined}
          >
            {status.message}
          </div>
        )}
      </form>
    </div>
  );
}
