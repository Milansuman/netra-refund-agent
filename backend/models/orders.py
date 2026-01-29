from db import db
from typing import TypedDict

class Product(TypedDict):
    title: str
    description: str | None
    price: int
    tax_percent: float

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

def get_user_orders(user_id: int) -> list[Order]:
    db_orders = db.execute("select id, status, paid_amount, payment_method from orders where user_id = %s;", (user_id,))

    orders: list[Order] = []
    for db_order in db_orders:
        order: Order = {
            "id": db_order[0],
            "order_items": [],
            "status": db_order[1],
            "paid_amount": db_order[2],
            "payment_method": db_order[3]
        }

        db_order_items = db.execute("select order_items.id, order_items.quantity, order_items.unit_price, order_items.tax_percent, products.title, products.description, products.price, products.tax_percent from order_items inner join products on order_items.product_id = products.id where order_items.order_id = %s;", (order["id"],))

        for (
            item_id,
            item_quantity, 
            item_unit_price, 
            item_tax_percent, 
            product_title, 
            product_description, 
            product_price, 
            product_tax_percent
        ) in db_order_items:
            order_item: OrderItem = {
                "id": item_id,
                "quantity": item_quantity,
                "discounts": [],
                "tax_percent": item_tax_percent,
                "unit_price": item_unit_price,
                "product": {
                    "title": product_title,
                    "description": product_description,
                    "price": product_price,
                    "tax_percent": product_tax_percent
                }
            }

            db_discounts = db.execute("select discounts.code, discounts.percent, discounts.amount from order_discounts inner join discounts on order_discounts.discount_id = discounts.id where order_discounts.order_item_id = %s;", (order_item["id"],))

            order_item["discounts"] = [{
                "code": discount[0],
                "percent": discount[1],
                "amount": discount[2],
            } for discount in db_discounts]

            order["order_items"].append(order_item)

    return orders