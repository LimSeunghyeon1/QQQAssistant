import { useQuery } from "@tanstack/react-query";

async function fetchShipments() {
  const res = await fetch("/api/shipments");
  if (!res.ok) throw new Error("Failed to load shipments");
  return res.json();
}

export default function ShipmentsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["shipments"],
    queryFn: fetchShipments
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Shipments</h1>
        <p className="text-sm text-slate-600">Tracking numbers linking overseas and domestic legs.</p>
      </div>
      {isLoading && <div>Loading...</div>}
      {error && <div className="text-red-600">{String(error)}</div>}
      <div className="grid grid-cols-1 gap-3">
        {data?.map((s: any) => (
          <div key={s.id} className="border bg-white rounded p-4 shadow-sm">
            <div className="font-medium">{s.carrier_name}</div>
            <div className="text-sm">Tracking: {s.tracking_number}</div>
            <div className="text-sm">Type: {s.shipment_type}</div>
            <div className="text-sm">Status: {s.last_status ?? "unknown"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
