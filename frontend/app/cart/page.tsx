"use client";

import { AskAssistantDialog } from "@/components/ask-assistant-dialog";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Trash2, Plus, Minus, ShoppingBag } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";

const initialCartItems = [
  {
    id: 1,
    name: "Velora Smart Speaker",
    price: 4999,
    quantity: 1,
    image: "https://images.unsplash.com/photo-1589561253898-768105ca91a8?auto=format&fit=crop&w=400&q=80",
  },
  {
    id: 2,
    name: "Noise Cancelling Pro",
    price: 12999,
    quantity: 1,
    image: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=400&q=80",
  },
];

export default function CartPage() {
  const [items, setItems] = useState(initialCartItems);

  const total = items.reduce((acc, item) => acc + item.price * item.quantity, 0);

  const updateQuantity = (id: number, delta: number) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, quantity: Math.max(1, item.quantity + delta) }
          : item
      )
    );
  };

  const removeItem = (id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <main className="min-h-screen bg-neutral-50 font-sans text-neutral-900">
      <nav className="sticky top-0 z-50 border-b border-neutral-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/landing"
            className="flex items-center gap-2 text-sm font-medium text-neutral-600 hover:text-indigo-600 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Continue Shopping
          </Link>
          <span className="text-xl font-bold tracking-tighter text-indigo-600">
            Velora.
          </span>
          <div className="w-24"></div> {/* Spacer */}
        </div>
      </nav>

      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-neutral-900 mb-8 flex items-center gap-3">
          <ShoppingBag className="h-8 w-8 text-indigo-600" />
          Your Shopping Bag
        </h1>

        <div className="lg:grid lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-8">
            {items.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-2xl border border-neutral-200">
                <p className="text-neutral-500">Your bag is empty.</p>
                <Link href="/landing">
                    <Button variant="link" className="text-indigo-600 mt-2">Start Shopping</Button>
                </Link>
              </div>
            ) : (
                <div className="space-y-4">
                    {items.map((item) => (
                    <div
                        key={item.id}
                        className="flex gap-6 bg-white p-6 rounded-2xl border border-neutral-200"
                    >
                        <div className="relative h-24 w-24 flex-shrink-0 rounded-xl bg-neutral-100 overflow-hidden">
                        <Image
                            src={item.image}
                            alt={item.name}
                            fill
                            className="object-cover"
                        />
                        </div>
                        <div className="flex-1 flex flex-col justify-between">
                            <div className="flex justify-between items-start">
                                <div>
                                <h3 className="font-semibold text-neutral-900 text-lg">{item.name}</h3>
                                <p className="text-sm text-neutral-500">In Stock</p>
                                </div>
                                <p className="font-bold text-lg text-neutral-900">₹{item.price.toLocaleString()}</p>
                            </div>
                            <div className="flex justify-between items-center mt-4">
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center border border-neutral-200 rounded-lg">
                                        <button 
                                            onClick={() => updateQuantity(item.id, -1)}
                                            className="p-1 hover:bg-neutral-50 text-neutral-600"
                                        >
                                            <Minus className="h-4 w-4" />
                                        </button>
                                        <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                                        <button 
                                            onClick={() => updateQuantity(item.id, 1)}
                                            className="p-1 hover:bg-neutral-50 text-neutral-600"
                                        >
                                            <Plus className="h-4 w-4" />
                                        </button>
                                    </div>
                                    <button 
                                        onClick={() => removeItem(item.id)}
                                        className="text-sm text-red-500 hover:text-red-600 hover:underline flex items-center gap-1"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                        Remove
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    ))}
                </div>
            )}
          </div>

          <div className="lg:col-span-4 mt-8 lg:mt-0">
            <div className="bg-white p-6 rounded-2xl border border-neutral-200 sticky top-24">
              <h2 className="text-lg font-semibold text-neutral-900 mb-4">
                Order Summary
              </h2>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-neutral-600">
                  <span>Subtotal</span>
                  <span>₹{total.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-neutral-600">
                  <span>Shipping</span>
                  <span className="text-emerald-600 font-medium">Free</span>
                </div>
                <div className="border-t border-neutral-100 pt-3 flex justify-between font-bold text-neutral-900 text-base">
                  <span>Total</span>
                  <span>₹{total.toLocaleString()}</span>
                </div>
              </div>
              <Button className="w-full mt-6 bg-indigo-600 hover:bg-indigo-500 h-12 text-base">
                Proceed to Checkout
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Assistant is only available here */}
      <AskAssistantDialog />
    </main>
  );
}
