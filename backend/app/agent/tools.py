from langchain_core.tools import tool
from models import orders, refunds, tickets, products
import json
from db.connections import db
from netra.decorators import task

def create_refund_agent_tools(user_id: int, thread_id: str):
    """
    Factory function to create refund agent tools bound to a specific user and thread.
    
    Args:
        user_id: The ID of the user
        thread_id: The ID of the conversation thread
    
    Returns:
        Dictionary of tools bound to the user and thread
    """
    
    @tool
    @task
    def get_order_by_product_name(product_name: str) -> str:
        """
        Search for user's orders containing a specific product by name.
        
        Args:
            product_name: The name or partial name of the product to search for. Use an empty string to get all orders
        
        Returns:
            JSON string with matching orders or error message
        """
        try:
            user_orders = orders.get_user_orders(user_id)
            matching_orders = []
            
            for order in user_orders:
                matching_items = []
                for item in order["order_items"]:
                    if product_name.lower() in item["product"]["title"].lower():
                        matching_items.append({
                            "id": item["id"],
                            "name": item["product"]["title"],
                            "quantity": item["quantity"],
                            "price": item["unit_price"] / 100.0,  # Convert cents to dollars
                            "tax_percent": item["tax_percent"]
                        })
                
                if matching_items:
                    matching_orders.append({
                        "id": order["id"],
                        "status": order["status"],
                        "paid_amount": order["paid_amount"] / 100.0,  # Convert cents to dollars
                        "payment_method": order["payment_method"],
                        "items": matching_items
                    })
            
            if not matching_orders:
                return json.dumps({"error": "No orders found with that product name"})
            
            return json.dumps({"orders": matching_orders})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    @task
    def get_order_by_id(order_id: int) -> str:
        """
        Get detailed information about a specific order by its ID.
        
        Args:
            order_id: The ID of the order
        
        Returns:
            JSON string with order details or error message
        """
        try:
            order = orders.get_order_by_id(order_id, user_id)
            
            if not order:
                return json.dumps({"error": "Order not found or does not belong to this user"})
            
            # Transform to frontend schema
            formatted_order = {
                "order_id": order["id"],
                "status": order["status"],
                "payment_method": order["payment_method"],
                "total_paid": order["paid_amount"] / 100.0,  # Convert cents to dollars
                "items": [{
                    "id": item["id"],
                    "name": item["product"]["title"],
                    "description": item["product"]["description"] or "",
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"] / 100.0,  # Convert cents to dollars
                    "tax_percent": item["tax_percent"],
                    "discounts": [
                        f"{d['code']}: {d['percent']}% off" if d["percent"] 
                        else f"{d['code']}: ₹{d['amount']/100:.2f} off" #type: ignore
                        for d in item["discounts"]
                    ]
                } for item in order["order_items"]]
            }
            
            return json.dumps({"order": formatted_order})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    @task
    def check_refund_eligibility(order_id: int, order_item_id: int):
        """
        Check if an order item is eligible for refund by verifying:
        - Order ownership
        - Item belongs to order
        - No existing refund for this item
        
        Args:
            order_id: The ID of the order
            order_item_id: The ID of the specific order item
        
        Returns:
            JSON string with eligibility status and details
        """
        try:
            validation = refunds.validate_basic_constraints(order_id, order_item_id, user_id, thread_id)
            
            if not validation["valid"]:
                return json.dumps({
                    "eligible": False,
                    "error": validation["error"],
                    "message": validation["message"]
                })
            
            facts = validation["facts"]
            if db.return_real:
                return json.dumps({
                    "order_id": facts["order_id"],
                    "order_item_id": facts["order_item_id"],
                    "order_status": facts["order_status"],
                    "days_since_order": facts["days_since_order"],
                    "days_since_delivery": facts["days_since_delivery"],
                    "is_delivered": facts["is_delivered"],
                    "max_refund_amount": facts["max_refund_amount"],
                    "refund_breakdown": facts["refund_breakdown"]
                })
            else:
                return None

        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    @task
    def process_refund(
        order_item_id: int,
        refund_type: str,
        reason: str,
        evidence: str | None = None
    ) -> str:
        """
        Process a refund request for an order item. Creates a refund record.
        
        Args:
            order_item_id: The ID of the order item to refund
            refund_type: Type of refund from taxonomy (e.g., "Defective Product", "Wrong Item")
            reason: Detailed reason for the refund request
            evidence: Optional evidence or additional information
        
        Returns:
            JSON string with refund ID and details or error message
        """
        try:
            # Calculate refund amount
            calc = refunds.calculate_refund_amount(order_item_id)
            
            # Create refund
            refund_id = refunds.create_refund(
                order_item_id=order_item_id,
                refund_type=refund_type,
                reason=reason,
                amount=calc["total_refund"],
                evidence=evidence,
                status="PENDING",
                thread_id=thread_id
            )
            
            return json.dumps({
                "success": True,
                "refund_id": refund_id,
                "amount": calc["total_refund"],
                "breakdown": calc["breakdown"],
                "status": "PENDING"
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    @task
    def escalate_to_manager(order_id: int, title: str, description: str | None = None) -> str:
        """
        Escalate an issue to a manager by creating a support ticket. Only execute this with the user's consent
        
        Args:
            order_id: The ID of the order related to this issue
            title: Brief title describing the issue
            description: Optional detailed description of the issue
        
        Returns:
            JSON string with ticket ID or error message
        """
        try:
            ticket_id = tickets.create_ticket(
                user_id=user_id,
                order_id=order_id,
                title=title,
                description=description
            )
            
            return json.dumps({
                "success": True,
                "ticket_id": ticket_id,
                "message": "Ticket created successfully. A manager will review your case."
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    @task
    def check_product_stock(product_id: int, quantity: int = 1) -> str:
        """
        Check if a product has sufficient stock available for replacement or new order.
        Use this when considering product replacements or verifying product availability.
        
        Args:
            product_id: The ID of the product to check
            quantity: The quantity needed (default: 1)
        
        Returns:
            JSON string with stock availability details or error message
        """
        try:
            stock_info = products.check_stock_availability(product_id, quantity)
            
            return json.dumps({
                "available": stock_info["available"],
                "product_name": stock_info.get("product_name"),
                "quantity_available": stock_info["quantity"],
                "quantity_requested": quantity,
                "message": stock_info["message"]
            })
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    @tool
    @task
    def get_user_refunds() -> str:
        """
        Get all refund requests for the current user.
        Shows status, amount, product details, and dates for each refund.
        
        Returns:
            JSON string with list of user's refunds or error message
        """
        try:
            user_refunds = refunds.get_user_refunds(user_id, thread_id)
            
            if not user_refunds:
                return json.dumps({"message": "No refunds found for this user"})
            
            # Format amounts in dollars
            formatted_refunds = []
            for refund in user_refunds:
                formatted_refunds.append({
                    "refund_id": refund["id"],
                    "status": refund["status"],
                    "amount": refund["amount"] / 100.0,
                    "product_name": refund["product_name"],
                    "refund_type": refund["refund_type"],
                    "reason": refund["reason"],
                    "order_id": refund["order_id"],
                    "created_at": refund["created_at"],
                    "processed_at": refund["processed_at"]
                })
            
            return json.dumps({"refunds": formatted_refunds})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    return {
        "get_order_by_product_name": get_order_by_product_name,
        "get_order_by_id": get_order_by_id,
        "check_refund_eligibility": check_refund_eligibility,
        "process_refund": process_refund,
        "escalate_to_manager": escalate_to_manager,
        "check_product_stock": check_product_stock,
        "get_user_refunds": get_user_refunds
    }
