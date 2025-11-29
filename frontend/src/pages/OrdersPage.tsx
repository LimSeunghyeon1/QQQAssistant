import { useQuery } from "@tanstack/react-query";

async function fetchOrders() {
  const res = await fetch("/api/orders");
  if (!res.ok) throw new Error("Failed to load orders");
  return res.json();
}

export default function OrdersPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["orders"], queryFn: fetchOrders });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Orders</h1>
        <p className="text-sm text-slate-600">Status tracking for domestic sales orders.</p>
      </div>
      {isLoading && <div>Loading...</div>}
      {error && <div className="text-red-600">{String(error)}</div>}
      <div className="grid grid-cols-1 gap-3">
        {data?.map((order: any) => (
          <div key={order.id} className="border bg-white rounded p-4 shadow-sm">
            <div className="font-medium">{order.external_order_id} ({order.channel_name})</div>
            <div className="text-sm">{order.customer_name}</div>
            <div className="text-sm">Status: {order.status}</div>
            <div className="text-sm">Items: {order.items?.length ?? 0}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
