import "./index.css";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes, Link } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import ProductsPage from "./pages/ProductsPage";
import ImportProductPage from "./pages/ImportProductPage";
import OrdersPage from "./pages/OrdersPage";
import UploadOrdersPage from "./pages/UploadOrdersPage";
import ShipmentsPage from "./pages/ShipmentsPage";
import SmartStoreExportPage from "./pages/SmartStoreExportPage";
import PurchaseOrdersPage from "./pages/PurchaseOrdersPage";
import { ChannelProvider } from "./ChannelContext";
import ChannelSelector from "./components/ChannelSelector";

const queryClient = new QueryClient();

function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow px-6 py-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="text-lg font-semibold">QQQ Purchase Agency Assistant</div>
          <ChannelSelector />
        </div>
        <nav className="flex flex-wrap gap-4 text-sm text-slate-700">
          <Link to="/products">Products</Link>
          <Link to="/products/import">Import</Link>
          <Link to="/exports/smartstore">SmartStore Export</Link>
          <Link to="/orders">Orders</Link>
          <Link to="/orders/upload">Upload Orders</Link>
          <Link to="/purchase-orders">Purchase Orders</Link>
          <Link to="/shipments">Shipments</Link>
        </nav>
      </header>
      <main className="p-6">
        <Routes>
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/import" element={<ImportProductPage />} />
          <Route path="/exports/smartstore" element={<SmartStoreExportPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/upload" element={<UploadOrdersPage />} />
          <Route path="/purchase-orders" element={<PurchaseOrdersPage />} />
          <Route path="/shipments" element={<ShipmentsPage />} />
          <Route path="*" element={<ProductsPage />} />
        </Routes>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ChannelProvider>
        <BrowserRouter>
          <Layout />
        </BrowserRouter>
      </ChannelProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
