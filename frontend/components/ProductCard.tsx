
import { Package, ShoppingBag, CreditCard } from "lucide-react";

export type ProductItem = {
    id: number;
    name: string;
    description: string;
    quantity: number;
    unit_price: number;
    tax_percent: number;
    discounts: string[];
};

export type ProductData = {
    order_id: number;
    status: string;
    payment_method: string;
    total_paid: number;
    items: ProductItem[];
};

export function ProductCard({ data }: { data: ProductData }) {
    const statusColors: Record<string, string> = {
        pending: "bg-yellow-100 text-yellow-800",
        processing: "bg-blue-100 text-blue-800",
        shipped: "bg-indigo-100 text-indigo-800",
        delivered: "bg-green-100 text-green-800",
        cancelled: "bg-red-100 text-red-800",
    };

    const statusClass = statusColors[data.status.toLowerCase()] || "bg-gray-100 text-gray-800";

    return (
        <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-3 border-b border-neutral-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-purple-600" />
                        <span className="font-semibold text-neutral-900">Order #{data.order_id}</span>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass}`}>
                        {data.status}
                    </span>
                </div>
            </div>

            {/* Products List */}
            <div className="p-4 space-y-4">
                {data.items.map((item) => (
                    <div key={item.id} className="border-b border-neutral-100 pb-3 last:border-0 last:pb-0">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <ShoppingBag className="h-4 w-4 text-purple-500" />
                                    <span className="font-medium text-neutral-800">{item.name}</span>
                                    <span className="text-xs text-neutral-400">ID: {item.id}</span>
                                </div>
                                <p className="text-sm text-neutral-500 mt-1 ml-6">{item.description}</p>
                                <div className="flex items-center gap-4 mt-2 ml-6 text-xs text-neutral-500">
                                    <span>Qty: {item.quantity}</span>
                                    <span>Tax: {item.tax_percent}%</span>
                                    {item.discounts.length > 0 && (
                                        <span className="text-green-600">🏷️ {item.discounts.join(", ")}</span>
                                    )}
                                </div>
                            </div>
                            <span className="font-semibold text-neutral-700">${item.unit_price.toFixed(2)}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="bg-neutral-50 px-4 py-3 border-t border-neutral-100">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-neutral-500">
                        <CreditCard className="h-3.5 w-3.5" />
                        <span>{data.payment_method}</span>
                    </div>
                    <span className="font-bold text-purple-600">${data.total_paid.toFixed(2)}</span>
                </div>
            </div>
        </div>
    );
}
