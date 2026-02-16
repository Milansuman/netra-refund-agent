from db.connections import db
from datetime import datetime
from schemas.refunds import RefundTaxonomy, RefundCalculation


def get_refund_taxonomy() -> list[RefundTaxonomy]:
    db_refund_taxonomy = db.execute("select reason, description from refund_taxonomy;")
    return [{
        "title": taxonomy[0],
        "description": taxonomy[1]
    } for taxonomy in db_refund_taxonomy]

def get_refund_taxonomy_id(reason: str) -> int | None:
    """Get the ID for a refund taxonomy reason"""
    result = db.execute(
        "select id from refund_taxonomy where reason = %s;", 
        (reason,)
    )
    return result[0][0] if result else None

def calculate_refund_amount(order_item_id: int, quantity: int | None = None) -> RefundCalculation:
    """
    Calculate accurate refund amount for an order item including tax and discounts.
    
    Formula: (unit_price × quantity) + tax - discount
    """
    # Get order item details
    result = db.execute(
        "select quantity, unit_price, tax_percent from order_items where id = %s;",
        (order_item_id,)
    )
    
    if not result:
        raise ValueError(f"Order item {order_item_id} not found")
    
    full_quantity, unit_price, tax_percent = result[0]
    refund_quantity = quantity if quantity else full_quantity
    
    if refund_quantity > full_quantity:
        raise ValueError(f"Refund quantity {refund_quantity} exceeds order quantity {full_quantity}")
    
    # Calculate base amount
    item_price = unit_price * refund_quantity
    
    # Calculate proportional tax
    tax_amount = int(item_price * (tax_percent / 100))
    
    # Get proportional discounts
    discounts = db.execute(
        """select d.percent, d.amount from order_discounts od
           inner join discounts d on od.discount_id = d.id
           where od.order_item_id = %s;""",
        (order_item_id,)
    )
    
    discount_amount = 0
    discount_details = []
    
    for percent, amount in discounts:
        if percent:
            # Percentage discount on the refund quantity
            disc = int(item_price * (percent / 100))
            discount_amount += disc
            discount_details.append(f"{percent}% off")
        elif amount:
            # Fixed amount discount, proportional to quantity
            disc = int((amount * refund_quantity) / full_quantity)
            discount_amount += disc
            discount_details.append(f"₹{disc/100:.2f} off")
    
    total_refund = item_price + tax_amount - discount_amount
    
    breakdown = f"Item: ₹{item_price/100:.2f} + Tax: ₹{tax_amount/100:.2f}"
    if discount_amount > 0:
        breakdown += f" - Discounts: ₹{discount_amount/100:.2f} ({', '.join(discount_details)})"
    breakdown += f" = ₹{total_refund/100:.2f}"
    
    return {
        "item_price": item_price,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "total_refund": total_refund,
        "breakdown": breakdown
    }

def get_order_facts(order_id: int, order_item_id: int, user_id: int, thread_id: str) -> dict:
    """
    Get factual information about an order for eligibility checking.
    Returns raw facts without making eligibility decisions.
    """
    # Verify order ownership
    order_check = db.execute(
        "select user_id, status, created_at, delivered_at from orders where id = %s;",
        (order_id,)
    )
    
    if not order_check:
        return {"error": "ORDER_NOT_FOUND", "message": "Order not found"}
    
    order_user_id, order_status, created_at, delivered_at = order_check[0]
    
    if order_user_id != user_id:
        return {"error": "UNAUTHORIZED", "message": "Order does not belong to this user"}
    
    # Check if item belongs to order
    item_check = db.execute(
        "select order_id, quantity, unit_price from order_items where id = %s;",
        (order_item_id,)
    )
    
    if not item_check or item_check[0][0] != order_id:
        return {"error": "ITEM_MISMATCH", "message": "Item does not belong to this order"}
    
    # Check if already refunded in this thread
    existing_refund = db.execute(
        "select status, amount from order_refunds where order_item_id = %s and thread_id = %s;",
        (order_item_id, thread_id)
    )
    
    refund_status = None
    if existing_refund:
        refund_status = existing_refund[0][0]
        if refund_status in ['APPROVED', 'PROCESSING']:
            return {
                "error": "ALREADY_REFUNDED",
                "message": f"Refund already {refund_status.lower()} for this item"
            }
    
    # Calculate days since order and delivery
    days_since_order = (datetime.now() - created_at).days if created_at else None
    days_since_delivery = (datetime.now() - delivered_at).days if delivered_at else None
    
    # Get max refund amount
    calc = calculate_refund_amount(order_item_id)
    
    return {
        "order_id": order_id,
        "order_item_id": order_item_id,
        "order_status": order_status,
        "created_at": created_at.isoformat() if created_at else None,
        "delivered_at": delivered_at.isoformat() if delivered_at else None,
        "days_since_order": days_since_order,
        "days_since_delivery": days_since_delivery,
        "is_delivered": delivered_at is not None,
        "max_refund_amount": calc["total_refund"],
        "refund_breakdown": calc["breakdown"],
        "existing_refund_status": refund_status
    }

def validate_basic_constraints(order_id: int, order_item_id: int, user_id: int, thread_id: str) -> dict:
    """
    Validate only the basic constraints: ownership, item match, no existing refund.
    Returns {"valid": True} or {"valid": False, "error": ..., "message": ...}
    """
    facts = get_order_facts(order_id, order_item_id, user_id, thread_id)
    
    if "error" in facts:
        return {"valid": False, "error": facts["error"], "message": facts["message"]}
    
    return {"valid": True, "facts": facts}

def create_refund(
    order_item_id: int,
    refund_type: str,
    reason: str,
    amount: int,
    evidence: str | None = None,
    status: str | None = "PENDING",
    quantity: int | None = None,
    thread_id: str | None = None
) -> int:
    """Create a refund record in the database"""
    taxonomy_id = get_refund_taxonomy_id(refund_type)
    
    if not taxonomy_id:
        raise ValueError(f"Invalid refund type: {refund_type}")
    
    result = db.execute(
        """insert into order_refunds 
           (order_item_id, refund_taxonomy_id, reason, status, amount, evidence, thread_id)
           values (%s, %s, %s, %s, %s, %s, %s)
           returning id;""",
        (order_item_id, taxonomy_id, reason, status, amount, evidence, thread_id)
    )
    
    return result[0][0]

def get_refund_status(refund_id: int) -> dict | None:
    """Get the status of a refund"""
    result = db.execute(
        """select or_.id, or_.status, or_.amount, or_.reason, or_.created_at,
                  oi.id as item_id, p.title as product_name,
                  rt.reason as refund_type
           from order_refunds or_
           inner join order_items oi on or_.order_item_id = oi.id
           inner join products p on oi.product_id = p.id
           inner join refund_taxonomy rt on or_.refund_taxonomy_id = rt.id
           where or_.id = %s;""",
        (refund_id,)
    )
    
    if not result:
        return None
    
    return {
        "id": result[0][0],
        "status": result[0][1],
        "amount": result[0][2],
        "reason": result[0][3],
        "created_at": result[0][4],
        "item_id": result[0][5],
        "product_name": result[0][6],
        "refund_type": result[0][7]
    }

def get_user_refunds(user_id: int, thread_id: str | None = None) -> list[dict]:
    """Get all refunds for a specific user, optionally filtered by thread_id"""
    if thread_id:
        result = db.execute(
            """select or_.id, or_.status, or_.amount, or_.reason, or_.created_at,
                      or_.processed_at, oi.id as item_id, oi.order_id, p.title as product_name,
                      rt.reason as refund_type, o.created_at as order_date
               from order_refunds or_
               inner join order_items oi on or_.order_item_id = oi.id
               inner join products p on oi.product_id = p.id
               inner join refund_taxonomy rt on or_.refund_taxonomy_id = rt.id
               inner join orders o on oi.order_id = o.id
               where o.user_id = %s and or_.thread_id = %s
               order by or_.created_at desc;""",
            (user_id, thread_id)
        )
    else:
        result = db.execute(
            """select or_.id, or_.status, or_.amount, or_.reason, or_.created_at,
                      or_.processed_at, oi.id as item_id, oi.order_id, p.title as product_name,
                      rt.reason as refund_type, o.created_at as order_date
               from order_refunds or_
               inner join order_items oi on or_.order_item_id = oi.id
               inner join products p on oi.product_id = p.id
               inner join refund_taxonomy rt on or_.refund_taxonomy_id = rt.id
               inner join orders o on oi.order_id = o.id
               where o.user_id = %s
               order by or_.created_at desc;""",
            (user_id,)
        )
    
    refunds = []
    for row in result:
        refunds.append({
            "id": row[0],
            "status": row[1],
            "amount": row[2],
            "reason": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "processed_at": row[5].isoformat() if row[5] else None,
            "item_id": row[6],
            "order_id": row[7],
            "product_name": row[8],
            "refund_type": row[9],
            "order_date": row[10].isoformat() if row[10] else None
        })
    
    return refunds

def approve_refund(refund_id: int) -> bool:
    """Approve a pending refund"""
    db.execute(
        "update order_refunds set status = 'APPROVED', processed_at = now() where id = %s;",
        (refund_id,)
    )
    return True

def reject_refund(refund_id: int, rejection_reason: str) -> bool:
    """Reject a refund with a reason"""
    db.execute(
        """update order_refunds 
           set status = 'REJECTED', 
               reason = reason || ' | REJECTED: ' || %s,
               processed_at = now() 
           where id = %s;""",
        (rejection_reason, refund_id)
    )
    return True

def clear_refunds() -> None:
    """
    Clear the refunds table
    """
    db.execute("delete from order_refunds;");