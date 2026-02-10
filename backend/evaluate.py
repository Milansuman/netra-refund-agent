from netra import Netra
from netra.simulation import BaseTask, TaskResult
from dotenv import load_dotenv
import os
from typing import Optional
from uuid import uuid4
from agent import invoke_graph
import json
import re

load_dotenv()

NETRA_API_KEY = os.getenv("NETRA_API_KEY")
if not NETRA_API_KEY:
    raise ValueError("NETRA_API_KEY not set")

def format_order_to_text(order_data: dict) -> str:
    """Convert a single order JSON object to human-friendly text."""
    lines = []
    lines.append(f"Order #{order_data.get('order_id', order_data.get('id', 'N/A'))}")
    lines.append(f"Status: {order_data.get('status', 'N/A')}")
    lines.append(f"Payment Method: {order_data.get('payment_method', 'N/A')}")
    
    total = order_data.get('total_paid') or order_data.get('paid_amount', 0)
    lines.append(f"Total: ${total:.2f}")
    
    items = order_data.get('items', [])
    if items:
        lines.append("\nItems:")
        for item in items:
            item_name = item.get('name', 'Unknown')
            qty = item.get('quantity', 1)
            price = item.get('unit_price') or item.get('price', 0)
            lines.append(f"  - {item_name} (x{qty}) - ${price:.2f}")
            
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
        lines.append(f"Total: ${total:.2f}")
        
        items = order.get('items', [])
        if items:
            lines.append("Items:")
            for item in items:
                item_name = item.get('name', 'Unknown')
                qty = item.get('quantity', 1)
                price = item.get('price', 0)
                lines.append(f"  - {item_name} (x{qty}) - ${price:.2f}")
    
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

class RefundAgentTask(BaseTask):
    
    def run(self, message: str, session_id: Optional[str] = None) -> TaskResult:
        # Generate thread_id similar to chat endpoint in main.py
        raise ValueError("test exception")
        thread_id = uuid4().hex if not session_id else session_id
        user_id = 1  # Using test user for simulation

        # Invoke the agent graph and collect the response (similar to chat endpoint)
        final_message = ""
        for chunk in invoke_graph(thread_id, message, user_id):
            try:
                # Parse the JSON chunk from the stream
                chunk_data = json.loads(chunk.strip())
                
                # Check for new streaming format: {"type": "message", "content": "..."}
                if chunk_data.get("type") == "message" and chunk_data.get("content"):
                    final_message = chunk_data["content"]
                elif chunk_data.get("type") == "error":
                    # Handle error responses
                    final_message = f"Error: {chunk_data.get('content', 'Unknown error')}"
            except (json.JSONDecodeError, KeyError, AttributeError):
                # Skip malformed or incomplete chunks
                continue

        # Convert structured tags to human-friendly text
        final_message = convert_tags_to_text(final_message)

        return TaskResult(
            message=final_message,
            session_id=thread_id
        )
    
def run_simulation(dataset_id: str) -> None:
    Netra.simulation.run_simulation( #type: ignore
        name="Refund Agent Simulation",
        dataset_id=dataset_id,
        task=RefundAgentTask()
    )


def main():
    Netra.init(
        headers=f"x-api-key={os.getenv('NETRA_API_KEY')}",
        app_name="Refund agent simulation",
        debug_mode=True,
        trace_content=True
    )

    run_simulation("b7e09b66-2ccc-4610-8fa5-591c50d61ad6")

    
if  __name__ == "__main__":
    main()