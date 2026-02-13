import json
import re

def format_order_to_text(order_data: dict) -> str:
    """Convert a single order JSON object to human-friendly text."""
    lines = []
    lines.append(f"Order #{order_data.get('order_id', order_data.get('id', 'N/A'))}")
    lines.append(f"Status: {order_data.get('status', 'N/A')}")
    lines.append(f"Payment Method: {order_data.get('payment_method', 'N/A')}")
    
    total = order_data.get('total_paid') or order_data.get('paid_amount', 0)
    lines.append(f"Total: ₹{total:.2f}")
    
    items = order_data.get('items', [])
    if items:
        lines.append("\nItems:")
        for item in items:
            item_name = item.get('name', 'Unknown')
            qty = item.get('quantity', 1)
            price = item.get('unit_price') or item.get('price', 0)
            lines.append(f"  - {item_name} (x{qty}) - ₹{price:.2f}")
            
            if 'description' in item and item['description']:
                lines.append(f"    {item['description']}")
            
            if 'discounts' in item and item['discounts']:
                for discount in item['discounts']:
                    lines.append(f"    Discount: {discount}")
    
    return "\n".join(lines)

def format_orders_to_text(orders_data: list) -> str:
    """Convert an array of orders to human-friendly text."""
    if not orders_data:
        return "No orders found."
    
    lines = [f"Found {len(orders_data)} order(s):\n"]
    
    for i, order in enumerate(orders_data, 1):
        if i > 1:
            lines.append("\n" + "-" * 40 + "\n")
        
        order_id = order.get('id', 'N/A')
        status = order.get('status', 'N/A')
        total = order.get('paid_amount', 0)
        
        lines.append(f"Order #{order_id}")
        lines.append(f"Status: {status}")
        lines.append(f"Total: ₹{total:.2f}")
        
        items = order.get('items', [])
        if items:
            lines.append("Items:")
            for item in items:
                item_name = item.get('name', 'Unknown')
                qty = item.get('quantity', 1)
                price = item.get('price', 0)
                lines.append(f"  - {item_name} (x{qty}) - ₹{price:.2f}")
    
    return "\n".join(lines)

def convert_tags_to_text(message: str) -> str:
    """Replace <ORDER> and <ORDERS> tags with human-friendly text."""
    
    
    # Replace <ORDER>...</ORDER> tags
    def replace_order(match):
        try:
            json_str = match.group(1)
            order_data = json.loads(json_str)
            return format_order_to_text(order_data)
        except json.JSONDecodeError:
            return match.group(0)  # Return original if parsing fails
    
    message = re.sub(r'<ORDER>(.*?)</ORDER>', replace_order, message, flags=re.DOTALL)
    
    # Replace <ORDERS>...</ORDERS> tags
    def replace_orders(match):
        try:
            json_str = match.group(1)
            orders_data = json.loads(json_str)
            return format_orders_to_text(orders_data)
        except json.JSONDecodeError:
            return match.group(0)  # Return original if parsing fails
    
    message = re.sub(r'<ORDERS>(.*?)</ORDERS>', replace_orders, message, flags=re.DOTALL)
    
    return message