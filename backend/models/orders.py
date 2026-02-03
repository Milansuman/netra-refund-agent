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

        orders.append(order)

    return orders

def get_order_by_id(order_id: int, user_id: int) -> Order | None:
    """Get a specific order by ID, verifying ownership"""
    orders = get_user_orders(user_id)
    for order in orders:
        if order["id"] == order_id:
            return order
    return None

def validate_order_ids(order_ids_input: str, user_id: int) -> dict:
    """
    Validate and parse order IDs from various input formats.
    Accepts: single ID, comma-separated, space-separated, or newline-separated
    Returns: validated IDs, invalid IDs, and deduped list
    """
    import re
    
    # Parse input - handle multiple formats
    # Remove common separators and split
    cleaned = re.sub(r'[,\s\n\r]+', ',', order_ids_input.strip())
    id_strings = [s.strip() for s in cleaned.split(',') if s.strip()]
    
    valid_ids = []
    invalid_ids = []
    
    for id_str in id_strings:
        # Remove # symbol if present
        id_str = id_str.replace('#', '').strip()
        try:
            order_id = int(id_str)
            if order_id > 0:
                valid_ids.append(order_id)
            else:
                invalid_ids.append(id_str)
        except ValueError:
            invalid_ids.append(id_str)
    
    # Deduplicate while preserving order
    deduped_ids = list(dict.fromkeys(valid_ids))
    
    # Verify which orders exist and belong to user
    user_orders = get_user_orders(user_id)
    user_order_ids = {order["id"] for order in user_orders}
    
    found_ids = [oid for oid in deduped_ids if oid in user_order_ids]
    not_found_ids = [oid for oid in deduped_ids if oid not in user_order_ids]
    
    return {
        "found_ids": found_ids,
        "not_found_ids": not_found_ids,
        "invalid_ids": invalid_ids,
        "total_input": len(id_strings),
        "total_valid": len(found_ids)
    }

def get_order_timeline(order_id: int) -> dict | None:
    """Get timeline information for an order"""
    result = db.execute(
        "select created_at, delivered_at, status from orders where id = %s;",
        (order_id,)
    )
    
    if not result:
        return None
    
    created_at, delivered_at, status = result[0]
    
    return {
        "order_id": order_id,
        "created_at": created_at,
        "delivered_at": delivered_at,
        "status": status,
        "days_since_order": (datetime.now() - created_at).days if created_at else None,
        "days_since_delivery": (datetime.now() - delivered_at).days if delivered_at else None
    }

from datetime import datetime