"use client";

import { Button } from "@/components/ui/button";
import { ArrowLeft, Package, RotateCcw, Truck, CheckCircle2, Clock, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AskAssistantDialog } from "@/components/ask-assistant-dialog";

interface Product {
  title: string;
  description: string;
  price: number;
  tax_percent: number;
}

interface Discount {
  code: string;
  percent: number | null;
  amount: number | null;
}

interface OrderItem {
  id: number;
  quantity: number;
  discounts: Discount[];
  tax_percent: number;
  unit_price: number;
  product: Product;
}

interface Order {
  id: number;
  order_items: OrderItem[];
  status: string;
  paid_amount: number;
  payment_method: string;
  created_at: string;
  delivered_at: string | null;
}

interface OrderResponse {
  orders: Order[];
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch("http://localhost:8000/orders", {
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Failed to fetch orders");
      }

      const data: OrderResponse = await response.json();
      setOrders(data.orders);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load orders");
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (priceInPaisa: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
    }).format(priceInPaisa / 100);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Pending";
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  const getDaysAgo = (dateString: string | null) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return `${diffDays} days ago`;
  };

  const getStatusConfig = (status: string) => {
    switch (status.toUpperCase()) {
      case "DELIVERED":
        return {
          color: "text-emerald-700 bg-emerald-50 border-emerald-200",
          icon: CheckCircle2,
          label: "Delivered"
        };
      case "PROCESSING":
        return {
          color: "text-amber-700 bg-amber-50 border-amber-200",
          icon: Clock,
          label: "Processing"
        };
      case "SHIPPED":
        return {
          color: "text-blue-700 bg-blue-50 border-blue-200",
          icon: Truck,
          label: "Shipped"
        };
      default:
        return {
          color: "text-neutral-700 bg-neutral-50 border-neutral-200",
          icon: Package,
          label: status
        };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center bg-gradient-to-br from-neutral-50 via-white to-indigo-50/30">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 animate-pulse"></div>
            <div className="absolute inset-0 h-16 w-16 rounded-2xl border-4 border-indigo-200 border-t-indigo-600 animate-spin"></div>
          </div>
          <p className="text-neutral-500 font-medium">Loading your orders...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen grid place-items-center bg-gradient-to-br from-neutral-50 via-white to-red-50/30">
        <div className="text-center space-y-4">
          <div className="h-20 w-20 rounded-3xl bg-red-50 flex items-center justify-center mx-auto">
            <Package className="h-10 w-10 text-red-400" />
          </div>
          <div>
            <p className="text-red-600 font-medium mb-2">{error}</p>
            <p className="text-neutral-500 text-sm">Please try again later</p>
          </div>
          <Link href="/landing">
            <Button className="bg-indigo-600 hover:bg-indigo-500">Back to Shop</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-200 font-sans text-neutral-900">
      {/* Decorative background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-200/30 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-violet-200/20 rounded-full blur-3xl"></div>
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-neutral-200/60 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/landing"
            className="flex items-center gap-2 text-sm font-medium text-neutral-600 hover:text-indigo-600 transition-all hover:-translate-x-0.5 group"
          >
            <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
            Back to Shop
          </Link>
          <Link href="/landing" className="text-xl font-bold tracking-tight bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
            Velora.
          </Link>
          <div className="w-24"></div>
        </div>
      </nav>

      <div className="relative mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-neutral-900 mb-2">Your Orders</h1>
          <p className="text-neutral-500">Track, return, or manage your purchases</p>
        </div>

        {/* Order Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-neutral-200/60 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-2xl font-bold text-neutral-900">{orders.length}</p>
            <p className="text-sm text-neutral-500">Total Orders</p>
          </div>
          <div className="bg-white rounded-2xl border border-neutral-200/60 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-2xl font-bold text-emerald-600">
              {orders.filter(o => o.status === "DELIVERED").length}
            </p>
            <p className="text-sm text-neutral-500">Delivered</p>
          </div>
          <div className="bg-white rounded-2xl border border-neutral-200/60 p-4 shadow-sm hover:shadow-md transition-shadow">
            <p className="text-2xl font-bold text-amber-600">
              {orders.filter(o => o.status === "PROCESSING").length}
            </p>
            <p className="text-sm text-neutral-500">Processing</p>
          </div>
        </div>

        {/* Orders List */}
        <div className="space-y-6">
          {orders.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-neutral-200/60 shadow-sm">
              <div className="h-24 w-24 rounded-3xl bg-neutral-100 flex items-center justify-center mx-auto mb-4">
                <Package className="h-12 w-12 text-neutral-400" />
              </div>
              <p className="text-neutral-600 font-medium mb-2">No orders yet</p>
              <p className="text-neutral-400 text-sm mb-6">Start shopping to see your orders here</p>
              <Link href="/landing">
                <Button className="bg-indigo-600 hover:bg-indigo-500">
                  Browse Products
                </Button>
              </Link>
            </div>
          ) : (
            orders.map((order, index) => {
              const statusConfig = getStatusConfig(order.status);
              const StatusIcon = statusConfig.icon;
              
              return (
                <div
                  key={order.id}
                  className="bg-white rounded-3xl border border-neutral-200/60 overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5 group"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* Order Header */}
                  <div className="bg-gradient-to-r from-neutral-50 to-white px-6 py-5 border-b border-neutral-100">
                    <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-indigo-100 flex items-center justify-center">
                          <Package className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                          <p className="text-xs text-neutral-400 uppercase tracking-wider mb-0.5">Order</p>
                          <p className="font-bold text-lg text-neutral-900">
                            #{order.id}
                          </p>
                        </div>
                      </div>
                      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${statusConfig.color}`}>
                        <StatusIcon className="h-3.5 w-3.5" />
                        {statusConfig.label}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="bg-white rounded-xl p-3 border border-neutral-100">
                        <p className="text-xs text-neutral-400 uppercase tracking-wider mb-1">Purchased</p>
                        <p className="font-semibold text-neutral-900 text-sm">{formatDate(order.created_at)}</p>
                        <p className="text-xs text-neutral-500 mt-0.5">{getDaysAgo(order.created_at)}</p>
                      </div>
                      <div className="bg-white rounded-xl p-3 border border-neutral-100">
                        <p className="text-xs text-neutral-400 uppercase tracking-wider mb-1">Delivered</p>
                        <p className="font-semibold text-neutral-900 text-sm">{formatDate(order.delivered_at)}</p>
                        <p className="text-xs text-neutral-500 mt-0.5">
                          {order.delivered_at ? getDaysAgo(order.delivered_at) : "Not yet delivered"}
                        </p>
                      </div>
                      <div className="bg-white rounded-xl p-3 border border-neutral-100">
                        <p className="text-xs text-neutral-400 uppercase tracking-wider mb-1">Total Amount</p>
                        <p className="font-bold text-neutral-900 text-lg">{formatPrice(order.paid_amount)}</p>
                        <p className="text-xs text-neutral-500 mt-0.5">via {order.payment_method}</p>
                      </div>
                    </div>
                  </div>

                  {/* Order Items */}
                  <div className="p-6 space-y-4">
                    {order.order_items.map((item) => (
                      <div
                        key={item.id}
                        className="flex gap-4 p-4 rounded-2xl hover:bg-neutral-50 transition-colors group/item"
                      >
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-neutral-900 group-hover/item:text-indigo-600 transition-colors">
                            {item.product.title}
                          </h3>
                          <p className="text-sm text-neutral-500 mt-1 line-clamp-1">
                            {item.product.description}
                          </p>
                          <div className="flex items-center gap-3 mt-2">
                            <p className="text-sm font-semibold text-indigo-600">
                              {formatPrice(item.unit_price)}
                            </p>
                            <span className="text-neutral-300">×</span>
                            <span className="text-sm text-neutral-600">{item.quantity}</span>
                            {item.discounts.length > 0 && (
                              <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
                                {item.discounts[0].code}
                              </span>
                            )}
                          </div>
                          <div className="mt-4 flex gap-2">
                            <Button
                              size="sm"
                              className="h-9 text-xs bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-200/50 rounded-xl"
                            >
                              <Truck className="mr-2 h-3.5 w-3.5" />
                              Track
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-9 text-xs rounded-xl hover:bg-neutral-50"
                            >
                              <RotateCcw className="mr-2 h-3.5 w-3.5" />
                              Return
                            </Button>
                          </div>
                        </div>
                        <ChevronRight className="h-5 w-5 text-neutral-300 group-hover/item:text-indigo-400 transition-colors self-center" />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Refund Assistant */}
      <AskAssistantDialog />
    </main>
  );
}
