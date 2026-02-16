from typing import TypedDict
from schemas.products import Product

class OrderDiscount(TypedDict):
    code: str
    percent: float | None
    amount: int | None

class OrderItem(TypedDict):
    id: int
    product: Product
    discounts: list[OrderDiscount]
    quantity: int
    unit_price: int
    tax_percent: float

class Order(TypedDict):
    id: int
    status: str
    paid_amount: int
    payment_method: str
    order_items: list[OrderItem]
    created_at: str
    delivered_at: str | None