"use client";

import { Button } from "@/components/ui/button";
import { ArrowLeft, Package, RotateCcw } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
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

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case "DELIVERED":
        return "text-emerald-600 bg-emerald-50 border-emerald-100";
      case "PROCESSING":
        return "text-blue-600 bg-blue-50 border-blue-100";
      case "CANCELLED":
        return "text-red-600 bg-red-50 border-red-100";
      default:
        return "text-neutral-600 bg-neutral-50 border-neutral-100";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center bg-neutral-50 text-neutral-500">
        <div className="flex flex-col items-center gap-2">
          <div className="h-6 w-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p>Loading your orders...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen grid place-items-center bg-neutral-50">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Link href="/landing">
            <Button>Back to Shop</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-50 font-sans text-neutral-900">
      <nav className="sticky top-0 z-50 border-b border-neutral-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/landing"
            className="flex items-center gap-2 text-sm font-medium text-neutral-600 hover:text-indigo-600 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Shop
          </Link>
          <span className="text-xl font-bold tracking-tighter text-indigo-600">
            Velora.
          </span>
          <div className="w-24"></div>
        </div>
      </nav>

      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-neutral-900 mb-6">
          Your Orders
        </h1>

        <div className="space-y-6">
          {orders.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-neutral-200 text-neutral-500">
              You have no orders yet.
            </div>
          ) : (
            orders.map((order) => (
              <div
                key={order.id}
                className="bg-white rounded-xl border border-neutral-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="bg-neutral-50 px-6 py-4 border-b border-neutral-100 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex gap-8 text-sm">
                    <div>
                      <p className="text-neutral-500">Order ID</p>
                      <p className="font-medium text-neutral-900">
                        VEL-{order.id.toString().padStart(6, "0")}
                      </p>
                    </div>
                    <div>
                      <p className="text-neutral-500">Total</p>
                      <p className="font-medium text-neutral-900">
                        {formatPrice(order.paid_amount)}
                      </p>
                    </div>
                    <div>
                      <p className="text-neutral-500">Payment</p>
                      <p className="font-medium text-neutral-900">
                        {order.payment_method}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div
                      className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(
                        order.status
                      )}`}
                    >
                      {order.status}
                    </div>
                  </div>
                </div>
                <div className="p-6 space-y-4">
                  {order.order_items.map((item) => (
                    <div
                      key={item.id}
                      className="flex gap-4 pb-4 border-b border-neutral-100 last:border-0 last:pb-0"
                    >
                      <div className="relative h-20 w-20 flex-shrink-0 rounded-md bg-neutral-100 overflow-hidden border border-neutral-200">
                        <Image
                          src="https://images.unsplash.com/photo-1607083206968-13611e3d76db?auto=format&fit=crop&w=200&q=80"
                          alt={item.product.title}
                          fill
                          className="object-cover"
                        />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-neutral-900">
                          {item.product.title}
                        </h3>
                        <p className="text-sm text-neutral-500 mt-1 line-clamp-1">
                          {item.product.description}
                        </p>
                        <div className="flex items-center gap-3 mt-2">
                          <p className="text-sm text-indigo-600 font-semibold">
                            {formatPrice(item.unit_price)} × {item.quantity}
                          </p>
                          {item.discounts.length > 0 && (
                            <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full border border-green-200">
                              {item.discounts[0].code}
                            </span>
                          )}
                        </div>
                        <div className="mt-3 flex gap-3">
                          <Button
                            size="sm"
                            className="h-8 text-xs bg-indigo-600 hover:bg-indigo-500"
                          >
                            <Package className="mr-2 h-3 w-3" />
                            Track Package
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 text-xs"
                          >
                            <RotateCcw className="mr-2 h-3 w-3" />
                            Return Item
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      {/* Refund Assistant */}
      <AskAssistantDialog />
    </main>
  );
}
