
import { Package, ShoppingBag, CreditCard } from "lucide-react";

export type OrderItem = {
    id: number;
    name: string;
    quantity: number;
    price: number;
};

export type Order = {
    id: number;
    status: string;
    paid_amount: number;
    payment_method: string;
    items: OrderItem[];
};

export function OrderCard({ order, onOrderClick }: { order: Order; onOrderClick: (id: number) => void }) {
    // Status color mapping
    const statusColors: Record<string, string> = {
        pending: "bg-yellow-100 text-yellow-800",
        completed: "bg-green-100 text-green-800",
        shipped: "bg-blue-100 text-blue-800",
        cancelled: "bg-red-100 text-red-800",
        delivered: "bg-emerald-100 text-emerald-800",
    };

    const statusClass = statusColors[order.status.toLowerCase()] || "bg-gray-100 text-gray-800";

    return (
        <div
            onClick={() => onOrderClick(order.id)}
            className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow cursor-pointer hover:border-indigo-300"
        >
            {/* Card Header */}
            <div className="bg-gradient-to-r from-indigo-50 to-violet-50 px-4 py-3 border-b border-neutral-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-indigo-600" />
                        <span className="font-semibold text-neutral-900">Order #{order.id}</span>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass}`}>
                        {order.status}
                    </span>
                </div>
            </div>

            {/* Card Body - Items List */}
            <div className="p-4 space-y-2">
                {order.items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                            <ShoppingBag className="h-3.5 w-3.5 text-neutral-400" />
                            <span className="text-neutral-700">{item.name}</span>
                            <span className="text-neutral-400">×{item.quantity}</span>
                        </div>
                        <span className="text-neutral-600">${item.price.toFixed(2)}</span>
                    </div>
                ))}
            </div>

            {/* Card Footer */}
            <div className="bg-neutral-50 px-4 py-3 border-t border-neutral-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-neutral-500">
                        <CreditCard className="h-3.5 w-3.5" />
                        <span>{order.payment_method}</span>
                    </div>
                    <span className="font-semibold text-indigo-600">${order.paid_amount.toFixed(2)}</span>
                </div>
            </div>
        </div>
    );
}
