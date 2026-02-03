"""
REFUND AGENT WITH TOOLS
========================

This agent can:
1. Have conversations about refunds
2. CALL TOOLS to perform actions (like fetching orders)

KEY CONCEPT: Tools
------------------
A "tool" is a function the LLM can decide to call. Think of it like giving
the AI assistant access to your phone - it can make calls when needed.

The LLM sees:
- Tool name: "get_user_orders"
- Tool description: "Fetch all orders for the current user"
- Tool parameters: None (we handle user_id internally for security)

When user says "list my orders", the LLM thinks:
"I should call get_user_orders to get this information"
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)
from langchain_groq import ChatGroq
from langchain_litellm import ChatLiteLLM
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
import operator
import os
from models import refunds, orders, policies, tickets, products
import json
from pydantic import BaseModel
from db import db

load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY not set")

LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
if not LITELLM_API_KEY:
    raise ValueError("LITELLM_API_KEY not set")


# =============================================================================
# STATE DEFINITION
# =============================================================================
#
# The "state" is like the agent's memory. It holds:
# - messages: The conversation history
# - user_id: Who is talking (so tools know whose orders to fetch)
# - refund: The final refund classification (if determined)
#
# The `Annotated[list, operator.add]` means: when updating messages,
# ADD new messages to the existing list (don't replace them)
# =============================================================================


class RefundAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # Append-only message list
    user_id: int  # The logged-in user's ID
    refund: dict | None
    is_complete: bool
    # Refund processing state
    selected_order_ids: list[int] | None  # Orders user wants to process
    selected_items: dict | None  # {order_item_id: quantity}
    refund_details: dict | None  # Collected refund information
    evidence_required: bool  # Whether evidence is needed
    eligibility_checked: bool  # Whether eligibility was verified
    wants_replacement: bool  # Whether user wants replacement instead of refund
    replacement_available: bool  # Whether replacement product is in stock


# =============================================================================
# LLM SETUP
# =============================================================================

# _llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-scout-17b-16e-instruct") #type: ignore
_llm = ChatLiteLLM(api_base="https://llm.keyvalue.systems", api_key=LITELLM_API_KEY, model="litellm_proxy/gpt-4-turbo")

# =============================================================================
# TOOLS
# =============================================================================
#
# Tools are functions decorated with @tool. The decorator:
# 1. Tells LangChain this is a tool
# 2. Extracts the function's docstring as the tool description
# 3. Extracts parameters from the function signature
#
# IMPORTANT: Tools receive the full state, so they can access user_id
# =============================================================================


# We'll create the tool dynamically to access user_id from state
def create_get_orders_tool(user_id: int):
    """
    Create a tool that fetches orders for a specific user.

    WHY create it dynamically?
    --------------------------
    The tool needs to know the user_id, but tools can't directly access
    the agent's state. So we create the tool with user_id "baked in".

    This is called a "closure" in programming - the function "remembers"
    the user_id from when it was created.
    """

    @tool
    def get_user_orders() -> str:
        """
        Fetch all orders for the current user.
        Use this when the user asks about their orders, order history,
        or wants to see what they've purchased.

        IMPORTANT: Always share the FULL order details with the user including
        order IDs, product names, quantities, and prices. Do not summarize.
        """
        try:
            user_orders = orders.get_user_orders(user_id)

            if not user_orders:
                return "You don't have any orders yet."

            # Create structured data for frontend to render as cards
            # The special <!--ORDER_DATA:...--> marker tells the frontend
            # to render this as cards instead of plain text
            orders_data = []
            for order in user_orders:
                order_info = {
                    "id": order["id"],
                    "status": order["status"],
                    "paid_amount": order["paid_amount"]
                    / 100,  # Convert cents to dollars
                    "payment_method": order["payment_method"],
                    "items": [
                        {
                            "id": item["id"],
                            "name": item["product"]["title"],
                            "quantity": item["quantity"],
                            "price": item["unit_price"] / 100,
                        }
                        for item in order["order_items"]
                    ],
                }
                orders_data.append(order_info)

            # Return both: structured data for frontend AND text for LLM
            # The frontend will extract ORDER_DATA and render cards
            result = f"<!--ORDER_DATA:{json.dumps(orders_data)}-->\n\n"
            result += f"Here are your {len(user_orders)} orders:\n\n"
            for order in user_orders:
                result += f"**Order #{order['id']}** - Status: {order['status']}\n"
                result += f"Total: ${order['paid_amount']/100:.2f}\n"
                result += "Items:\n"
                for item in order["order_items"]:
                    result += f"  • {item['product']['title']} x{item['quantity']} @ ${item['unit_price']/100:.2f}\n"
                result += "\n"

            result += "Would you like to request a refund for any of these orders?"
            return result
        except Exception as e:
            return f"Sorry, I couldn't fetch your orders: {str(e)}"

    return get_user_orders


def create_get_order_details_tool(user_id: int):
    """
    Create a tool that fetches details of a specific order.

    WHY do we need user_id?
    -----------------------
    For SECURITY! We verify the order belongs to the current user.
    Otherwise, a user could request details of someone else's order.
    """

    @tool
    def get_order_details(order_id: str | int) -> str:
        """
        Get detailed information about a specific order including all products.
        Use this when the user asks about a specific order by ID, like
        "show me order #1" or "what's in order 2".

        Args:
            order_id: The order ID to look up (e.g., 1, 2, 3)
        """
        try:
            # Convert to int if string
            order_id = int(order_id)
            
            # Fetch all orders for this user
            user_orders = orders.get_user_orders(user_id)

            # Find the specific order (and verify it belongs to this user!)
            target_order = None
            for order in user_orders:
                if order["id"] == order_id:
                    target_order = order
                    break

            if not target_order:
                return f"Order #{order_id} not found. Please check the order number and try again."

            # Create structured data for frontend to render as product cards
            # Using <!--PRODUCT_DATA:...--> marker (similar to ORDER_DATA)
            products_data = {
                "order_id": target_order["id"],
                "status": target_order["status"],
                "payment_method": target_order["payment_method"],
                "total_paid": target_order["paid_amount"] / 100,
                "items": [],
            }

            for item in target_order["order_items"]:
                product = item["product"]
                item_data = {
                    "id": item["id"],
                    "name": product["title"],
                    "description": product["description"] or "N/A",
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"] / 100,
                    "tax_percent": item["tax_percent"],
                    "discounts": [],
                }

                # Add discount info
                for discount in item.get("discounts", []):
                    if discount.get("percent"):
                        item_data["discounts"].append(
                            f"{discount['code']} ({discount['percent']}% off)"
                        )
                    elif discount.get("amount") and discount["amount"]:
                        item_data["discounts"].append(
                            f"{discount['code']} (${discount['amount']/100:.2f} off)"
                        )

                products_data["items"].append(item_data)

            # Return structured data for frontend AND text for LLM
            result = f"<!--PRODUCT_DATA:{json.dumps(products_data)}-->\n\n"
            result += f"**Order #{target_order['id']}** - {target_order['status']}\n"
            result += f"Total: ${target_order['paid_amount']/100:.2f}\n\n"
            result += "Products:\n"
            for item in target_order["order_items"]:
                result += f"• {item['product']['title']} (Item ID: {item['id']}) - ${item['unit_price']/100:.2f} x{item['quantity']}\n"

            result += "\nWould you like to request a refund for any of these items?"
            return result

        except Exception as e:
            return f"Sorry, I couldn't fetch order details: {str(e)}"

    return get_order_details


def create_validate_order_ids_tool(user_id: int):
    """Tool to validate and parse order IDs from user input"""
    
    @tool
    def validate_order_ids(order_ids: str) -> str:
        """
        Validate order IDs provided by the user. Accepts multiple formats:
        - Single ID: "123"
        - Comma-separated: "123, 456, 789"
        - Space-separated: "123 456 789"
        - With # symbols: "#123, #456"
        - Pasted list with newlines
        
        Returns which orders are valid and belong to the user.
        
        Args:
            order_ids: The order IDs to validate (any format)
        """
        try:
            result = orders.validate_order_ids(order_ids, user_id)
            
            response = f"📋 Order ID Validation:\n\n"
            
            if result["found_ids"]:
                response += f"✅ Found {len(result['found_ids'])} valid order(s): {', '.join(f'#{oid}' for oid in result['found_ids'])}\n\n"
            
            if result["not_found_ids"]:
                response += f"❌ Not found or not yours: {', '.join(f'#{oid}' for oid in result['not_found_ids'])}\n\n"
            
            if result["invalid_ids"]:
                response += f"⚠️ Invalid format: {', '.join(result['invalid_ids'])}\n\n"
            
            if result["found_ids"]:
                response += "Would you like to proceed with the refund for these orders?"
            else:
                response += "No valid orders found. Please check your order numbers and try again."
            
            return response
        except Exception as e:
            return f"Error validating order IDs: {str(e)}"
    
    return validate_order_ids


def create_get_policy_tool(user_id: int):
    """Tool to retrieve policy text for a refund category"""
    
    @tool
    def get_refund_policy(refund_type: str) -> str:
        """
        Get the full policy text for a specific refund category.
        Use this to understand the eligibility rules, time windows, and requirements.
        
        Args:
            refund_type: The refund type (e.g., DAMAGED_ITEM, MISSING_ITEM, LATE_DELIVERY)
        """
        try:
            policy = policies.get_policy_by_category(refund_type)
            
            if not policy:
                return f"Policy not found for {refund_type}. Available categories: {', '.join(policies.get_all_categories())}"
            
            response = f"📜 **{policy['title']} Policy**\n\n"
            response += policy['content']
            
            return response
        except Exception as e:
            return f"Error retrieving policy: {str(e)}"
    
    return get_refund_policy


def create_get_general_terms_tool(user_id: int):
    """Tool to retrieve general policy terms"""
    
    @tool
    def get_general_policy_terms() -> str:
        """
        Get the general terms and conditions for refunds.
        This includes important information about:
        - How refund amounts are calculated
        - What fees are refundable/non-refundable
        - Duplicate refund prevention rules
        - Refund processing methods
        
        IMPORTANT: Review these terms before processing any refund to ensure compliance.
        """
        try:
            general_terms = policies.get_general_terms()
            
            response = "📋 **General Refund Policy Terms**\n\n"
            response += general_terms
            
            return response
        except Exception as e:
            return f"Error retrieving general terms: {str(e)}"
    
    return get_general_policy_terms


def create_get_order_facts_tool(user_id: int):
    """Tool to get factual order information for eligibility assessment"""
    
    @tool
    def get_order_facts(order_id: str | int, order_item_id: str | int) -> str:
        """
        Get factual information about an order and item for refund eligibility assessment.
        This includes: order status, dates, delivery status, and refund amount.
        
        Use this with the policy to determine if a refund is eligible.
        
        Args:
            order_id: The order ID
            order_item_id: The specific item ID within the order
        """
        try:
            # Convert to int if string
            order_id = int(order_id)
            order_item_id = int(order_item_id)
            
            facts = refunds.get_order_facts(order_id, order_item_id, user_id)
            
            if "error" in facts:
                return f"❌ {facts['message']}"
            
            response = "📊 **Order Facts**\n\n"
            response += f"**Order ID:** #{facts['order_id']}\n"
            response += f"**Item ID:** #{facts['order_item_id']}\n"
            response += f"**Order Status:** {facts['order_status']}\n"
            response += f"**Ordered:** {facts['created_at']} ({facts['days_since_order']} days ago)\n"
            
            if facts['is_delivered']:
                response += f"**Delivered:** {facts['delivered_at']} ({facts['days_since_delivery']} days ago)\n"
            else:
                response += f"**Delivered:** Not yet delivered\n"
            
            response += f"\n**Max Refund Amount:** ${facts['max_refund_amount']/100:.2f}\n"
            response += f"**Breakdown:** {facts['refund_breakdown']}\n"
            
            if facts['existing_refund_status']:
                response += f"\n⚠️ **Existing Refund:** {facts['existing_refund_status']}\n"
            
            return response
        except Exception as e:
            return f"Error getting order facts: {str(e)}"
    
    return get_order_facts


def create_calculate_refund_tool(user_id: int):
    """Tool to calculate refund amount for items"""
    
    @tool
    def calculate_refund(order_item_id: str | int, quantity: str | int | None = None) -> str:
        """
        Calculate the exact refund amount for an order item.
        Includes item price, tax, and deducts proportional discounts.
        
        Args:
            order_item_id: The item ID to calculate refund for
            quantity: Optional - specific quantity to refund (defaults to full quantity)
        """
        try:
            # Convert to int if string
            order_item_id = int(order_item_id)
            if quantity is not None:
                quantity = int(quantity)
            
            calc = refunds.calculate_refund_amount(order_item_id, quantity)
            
            response = f"💰 **Refund Calculation**\n\n"
            response += f"**Total Refund:** ${calc['total_refund']/100:.2f}\n\n"
            response += f"**Breakdown:**\n"
            response += f"• Item Price: ${calc['item_price']/100:.2f}\n"
            response += f"• Tax: ${calc['tax_amount']/100:.2f}\n"
            if calc['discount_amount'] > 0:
                response += f"• Discounts: -${calc['discount_amount']/100:.2f}\n"
            response += f"\n{calc['breakdown']}"
            
            return response
        except Exception as e:
            return f"Error calculating refund: {str(e)}"
    
    return calculate_refund


def create_process_refund_tool(user_id: int):
    """Tool to create and submit a refund request"""
    
    @tool
    def submit_refund_request(
        order_item_id: str | int,
        refund_type: str,
        reason: str,
        quantity: str | int | None = None,
        evidence: str | None = None
    ) -> str:
        """
        Submit a refund request for an order item. This creates the refund
        in the system and marks it as PENDING for review.
        
        Args:
            order_item_id: The item ID to refund
            refund_type: Type from taxonomy (e.g., DAMAGED_ITEM, MISSING_ITEM)
            reason: Detailed explanation for the refund
            quantity: Optional - specific quantity to refund
            evidence: Optional - description or reference to uploaded evidence
        """
        try:
            # Convert to int if string
            order_item_id = int(order_item_id)
            if quantity is not None:
                quantity = int(quantity)
            
            # Calculate refund amount
            calc = refunds.calculate_refund_amount(order_item_id, quantity)
            
            # Create refund record
            refund_id = refunds.create_refund(
                order_item_id=order_item_id,
                refund_type=refund_type,
                reason=reason,
                amount=calc["total_refund"],
                evidence=evidence,
                quantity=quantity
            )
            
            response = f"✅ **Refund Request Submitted!**\n\n"
            response += f"**Refund ID:** #{refund_id}\n"
            response += f"**Status:** PENDING REVIEW\n"
            response += f"**Amount:** ${calc['total_refund']/100:.2f}\n\n"
            response += f"Your refund request has been submitted and will be reviewed within 24-48 hours. "
            response += f"You'll receive a confirmation email once processed.\n\n"
            response += f"Is there anything else I can help you with?"
            
            return response
        except Exception as e:
            return f"Error submitting refund: {str(e)}"
    
    return submit_refund_request


def create_raise_ticket_tool(user_id: int):
    """Tool to raise a support ticket for manual review"""
    
    @tool
    def raise_support_ticket(
        order_id: str | int,
        title: str,
        description: str
    ) -> str:
        """
        Create a support ticket for cases requiring manual review or investigation.
        
        Use this when:
        - The refund request is complex and needs human review
        - There are suspicious or fraudulent activities suspected
        - Policy doesn't clearly cover the specific case
        - Evidence is inconclusive and requires expert assessment
        - High-value items require additional verification
        - Multiple failed refund attempts for the same issue
        
        Args:
            order_id: The order ID this ticket relates to
            title: Brief summary of the issue (e.g., "High-value damaged item requires verification")
            description: Detailed information about the issue, user's request, and why manual review is needed
        """
        try:
            # Convert to int if string
            order_id = int(order_id)
            
            # Verify the order belongs to the user
            order_check = db.execute(
                "SELECT id FROM orders WHERE id = %s AND user_id = %s;",
                (order_id, user_id)
            )
            
            if not order_check:
                return f"❌ Order #{order_id} not found or does not belong to you."
            
            # Create the ticket
            ticket_id = tickets.create_ticket(
                user_id=user_id,
                order_id=order_id,
                title=title,
                description=description
            )
            
            response = f"🎫 **Support Ticket Created**\n\n"
            response += f"**Ticket ID:** #{ticket_id}\n"
            response += f"**Order ID:** #{order_id}\n"
            response += f"**Title:** {title}\n\n"
            response += f"Your ticket has been escalated to our support team for manual review. "
            response += f"A specialist will contact you within 24-48 hours via email.\n\n"
            response += f"You can reference Ticket #{ticket_id} in any future communications about this issue."
            
            return response
        except Exception as e:
            return f"Error creating ticket: {str(e)}"
    
    return raise_support_ticket


def create_check_stock_tool(user_id: int):
    """Tool to check product stock availability for replacements"""
    
    @tool
    def check_product_stock(product_id: str | int, quantity: str | int = 1) -> str:
        """
        Check if a product is in stock for replacement.
        Use this when a user wants a replacement instead of a refund.
        
        Args:
            product_id: The product ID to check stock for
            quantity: The quantity needed (default: 1)
        """
        try:
            # Convert to int if string
            product_id = int(product_id)
            if quantity is not None:
                quantity = int(quantity)
            
            stock_info = products.check_stock_availability(product_id, quantity)
            
            response = f"📦 **Stock Availability Check**\n\n"
            response += f"**Product:** {stock_info.get('product_name', 'Unknown')}\n"
            response += f"**Status:** {stock_info['message']}\n"
            response += f"**Available Quantity:** {stock_info['stock_quantity']}\n"
            response += f"**Requested Quantity:** {quantity}\n\n"
            
            if stock_info['available']:
                response += "✅ This product is available for replacement!\n"
                response += "We can proceed with processing a replacement order for you."
            else:
                response += "❌ Unfortunately, this product is currently out of stock.\n"
                response += "We can offer you a full refund instead."
            
            return response
        except Exception as e:
            return f"Error checking stock: {str(e)}"
    
    return check_product_stock


# =============================================================================
# SYSTEM PROMPT
# =============================================================================


class _RefundClassification(BaseModel):
    refund_type: str
    reason: str


SYSTEM_PROMPT = """You are a refund agent that helps users with their orders and refunds.

IMPORTANT TOOL USAGE RULES:
1. When user mentions "orders", "my orders", "list orders", "show orders": 
   → Call get_user_orders to fetch all orders

2. When user asks about a SPECIFIC order by number like "order 1", "order #4", "products in order 2":
   → Call get_order_details with the order_id

3. When user provides order IDs for refund (single, multiple, or pasted list):
   → Call validate_order_ids to validate and deduplicate the IDs

4. To get the refund policy for a category:
   → Call get_refund_policy with the refund_type (e.g., DAMAGED_ITEM)

5. To get general policy terms (refund calculation, duplicate prevention, fees):
   → Call get_general_policy_terms (no parameters needed)
   → Review BEFORE processing any refund to understand what's refundable

6. To get factual order information for eligibility assessment:
   → Call get_order_facts with order_id and order_item_id
   → Then YOU must evaluate against the policy to determine eligibility

7. To calculate exact refund amount:
   → Call calculate_refund with order_item_id and optional quantity

8. To submit the refund:
   → Call submit_refund_request with all required details

9. To raise a support ticket for manual review:
   → Call raise_support_ticket with order_id, title, and description
   → Use when cases require human intervention (see MANUAL REVIEW section below)

10. To check if a product is in stock for replacement:
   → Call check_product_stock with product_id and quantity
   → Use when user wants a replacement instead of a refund

11. ALWAYS call the appropriate tool first. Do NOT make up order or product information.

CRITICAL POLICY RULES:
======================
Before processing ANY refund, you MUST:
1. Call get_general_policy_terms to understand refund calculation and restrictions
2. Check for duplicate refunds (order facts will show if refund already exists)
3. Remember: Shipping fees and platform fees are NON-REFUNDABLE
4. Only item price + taxes can be refunded (minus proportional discounts)

MANUAL REVIEW & TICKET ESCALATION:
===================================
You MUST raise a support ticket (using raise_support_ticket) in the following cases:

1. **Suspected Fraud or Abuse:**
   - Multiple refund requests from same user in short period
   - Suspicious patterns or inconsistencies in user's claims
   - Evidence appears manipulated or falsified

2. **High-Value Items:**
   - Items exceeding $500 (policy mentions high-value items may require return)
   - Premium or luxury products requiring additional verification

3. **Ambiguous or Uncovered Cases:**
   - Refund reason doesn't clearly fit into policy categories
   - Policy doesn't have specific guidelines for the situation
   - User's request requires interpretation beyond policy scope

4. **Inconclusive Evidence:**
   - Evidence provided is unclear or insufficient
   - Cannot determine eligibility based on available information
   - Requires expert assessment (e.g., technical damage evaluation)

5. **Complex Disputes:**
   - User disputes policy decision
   - Involves multiple orders or complicated order history
   - Legal or regulatory considerations

6. **Multiple Failed Attempts:**
   - Same user has had multiple failed refund attempts
   - Previous refunds were rejected for similar reasons

When creating a ticket:
- Include all relevant context: order details, refund request, evidence reviewed
- Explain clearly why manual review is needed
- Summarize the user's situation and their expectations
- Let the user know their case has been escalated to specialists

ELIGIBILITY ASSESSMENT:
=======================
YOU are responsible for determining eligibility by:
1. Getting the order facts (dates, status, delivery info)
2. Getting the relevant policy text for the refund type
3. Reading the policy carefully and applying the rules
4. Making a decision based on the policy requirements

Example: For DAMAGED_ITEM, the policy says "within 7 days of delivery"
- Get order facts: delivered 5 days ago → ELIGIBLE
- Get order facts: delivered 10 days ago → NOT ELIGIBLE

Do NOT hardcode time windows - read them from the policy each time.

REFUND WORKFLOW:
================

Step 1: ORDER IDENTIFICATION
- Accept order IDs in any format (single, comma-separated, pasted list)
- Validate and confirm which orders to process
- Show order details and let user select specific items

Step 2: ITEM SELECTION
- For multi-item orders, ask which specific items need refund
- Ask for quantity if partial refund needed
- Confirm the items before proceeding

Step 3: REFUND CLASSIFICATION
- Determine the refund type from the taxonomy
- Ask dynamic follow-up questions based on type:

For DAMAGED_ITEM:
- "How severe is the damage? (minor, major, completely unusable)"
- "Was the packaging damaged when delivered?"
- "Have you opened or used the product?"
- "Can you describe the damage?"
- Request photos if damage is not clear

For MISSING_ITEM:
- "Which specific item(s) are missing?"
- "Was the package opened/tampered with?"
- "Did you check all packaging materials?"

For LATE_DELIVERY:
- "When was the original delivery date?"
- "When did you actually receive it?"
- "Was this a time-sensitive order?"

For WRONG_ITEM:
- "What item did you receive instead?"
- "Is the item still unopened?"

For DUPLICATE_CHARGE:
- "How many times were you charged?"
- "Do you have multiple order confirmations?"

For CANCELLATION:
- "When did you request cancellation?"
- "Has the item been shipped yet?"

For RETURN_PICKUP_FAILED:
- "When was the pickup scheduled?"
- "Were you available at the scheduled time?"
- "Did you receive any notification from courier?"

For PAYMENT_DEBITED_BUT_FAILED:
- "When was the payment made?"
- "Did you receive an order confirmation?"

Step 4: EVIDENCE COLLECTION (when needed)
- For DAMAGED_ITEM: request clear photos showing damage
- For MISSING_ITEM: request package photos if available
- For WRONG_ITEM: request photos of received item
- Validate that evidence is relevant and clear

Step 4.5: REPLACEMENT OPTION (for eligible cases)
- For DAMAGED_ITEM or WRONG_ITEM, ask if user wants replacement or refund
- If user wants replacement:
  * Get the product_id from the order item
  * Call check_product_stock to verify availability
  * If in stock: Inform user replacement will be arranged
  * If out of stock: Offer refund instead
- Continue to refund process if user chooses refund

Step 5: ELIGIBILITY CHECK
- Get general policy terms using get_general_policy_terms tool FIRST
- Get order facts using get_order_facts tool
- Get relevant policy using get_refund_policy tool
- Check for existing refunds (in order facts) - REJECT if duplicate
- Read policy requirements carefully (time windows, conditions)
- Compare facts against policy to determine eligibility
- Verify no non-refundable fees are being claimed
- If not eligible, explain why based on policy
- If eligible, show max refund amount and proceed

Step 6: REFUND CALCULATION
- Calculate exact amount: item price + tax - discounts
- Show breakdown to user
- Confirm amount before proceeding

Step 7: SUBMISSION
- Create refund request in system
- Provide refund ID and expected timeline
- Offer to help with anything else

DYNAMIC QUESTIONING:
- Don't ask all questions at once
- Ask follow-ups based on user's answers
- If user provides evidence/details upfront, skip redundant questions
- Be conversational, not robotic

REFUND CATEGORIES:
"""

SYSTEM_PROMPT += "\n".join(
    [
        f"{refund['title']} - {refund['description']}"
        for refund in refunds.get_refund_taxonomy()
    ]
)

SYSTEM_PROMPT += "\nOther - Refund reason does not fit in any other category\n"


# =============================================================================
# GRAPH NODES
# =============================================================================
#
# A LangGraph graph has "nodes" (steps) and "edges" (connections).
#
# Our flow:
#   START → chat_node → (if tool call) → tools_node → chat_node
#                     → (if no tool call) → END
# =============================================================================


def chat_node(state: RefundAgentState) -> dict:
    """
    The main chat node. This:
    1. Gets the LLM's response to the conversation
    2. The LLM might respond with text OR request a tool call
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id")

    print(f"[DEBUG] chat_node called with user_id={user_id}")
    print(
        f"[DEBUG] Latest message: {messages[-1].content[:100] if messages else 'none'}"
    )

    # Create all tools with the user's ID
    get_orders_tool = create_get_orders_tool(user_id)
    get_order_details_tool = create_get_order_details_tool(user_id)
    validate_ids_tool = create_validate_order_ids_tool(user_id)
    get_policy_tool = create_get_policy_tool(user_id)
    get_general_terms_tool = create_get_general_terms_tool(user_id)
    get_order_facts_tool = create_get_order_facts_tool(user_id)
    calculate_refund_tool = create_calculate_refund_tool(user_id)
    process_refund_tool = create_process_refund_tool(user_id)
    raise_ticket_tool = create_raise_ticket_tool(user_id)
    check_stock_tool = create_check_stock_tool(user_id)
    
    tools = [
        get_orders_tool,
        get_order_details_tool,
        validate_ids_tool,
        get_policy_tool,
        get_general_terms_tool,
        get_order_facts_tool,
        calculate_refund_tool,
        process_refund_tool,
        raise_ticket_tool,
        check_stock_tool
    ]

    # Bind tools to the LLM with explicit tool configuration
    # tool_choice="auto" lets the LLM decide, but with clear instructions
    llm_with_tools = _llm.bind_tools(tools, tool_choice="auto")

    # Get response (might be text OR a tool call)
    response = llm_with_tools.invoke(messages)

    # Debug: Check if tool was called
    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"[DEBUG] Tool calls: {response.tool_calls}")
    else:
        print(f"[DEBUG] No tool calls, response: {str(response.content)[:100]}")

    # Check if conversation is complete (refund classified)
    refund = None
    is_complete = False
    try:
        refund = json.loads(str(response.content))
        _RefundClassification(**refund)
        is_complete = True
    except:
        pass

    return {
        "messages": [response],  # Add to message history
        "refund": refund,
        "is_complete": is_complete,
    }


def should_continue(state: RefundAgentState) -> Literal["tools", "__end__"]:
    """
    Decide what to do next:
    - If LLM requested a tool call → go to tools node
    - Otherwise → end (we're done)

    This is called a "conditional edge" in LangGraph.
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    # If the last message has tool_calls, we need to execute them
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "__end__"


def tools_node(state: RefundAgentState) -> dict:
    """
    Execute any tool calls the LLM requested.

    This node:
    1. Gets the last message (which contains tool calls)
    2. Executes each tool
    3. Returns the results as ToolMessages
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id")
    last_message = messages[-1]

    # Create the tools with user context
    get_orders_tool = create_get_orders_tool(user_id)
    get_order_details_tool = create_get_order_details_tool(user_id)
    validate_ids_tool = create_validate_order_ids_tool(user_id)
    get_policy_tool = create_get_policy_tool(user_id)
    get_general_terms_tool = create_get_general_terms_tool(user_id)
    get_order_facts_tool = create_get_order_facts_tool(user_id)
    calculate_refund_tool = create_calculate_refund_tool(user_id)
    process_refund_tool = create_process_refund_tool(user_id)
    raise_ticket_tool = create_raise_ticket_tool(user_id)
    check_stock_tool = create_check_stock_tool(user_id)
    
    tools_by_name = {
        "get_user_orders": get_orders_tool,
        "get_order_details": get_order_details_tool,
        "validate_order_ids": validate_ids_tool,
        "get_refund_policy": get_policy_tool,
        "get_general_policy_terms": get_general_terms_tool,
        "get_order_facts": get_order_facts_tool,
        "calculate_refund": calculate_refund_tool,
        "submit_refund_request": process_refund_tool,
        "raise_support_ticket": raise_ticket_tool,
        "check_product_stock": check_stock_tool,
    }

    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # Execute the tool
        if tool_name in tools_by_name:
            result = tools_by_name[tool_name].invoke(tool_args)
        else:
            result = f"Unknown tool: {tool_name}"

        # Create a ToolMessage with the result
        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_call["id"])
        )

    return {"messages": tool_messages}


# =============================================================================
# BUILD THE GRAPH
# =============================================================================

_builder = StateGraph(RefundAgentState)

# Add nodes
_builder.add_node("chat", chat_node)
_builder.add_node("tools", tools_node)

# Add edges
_builder.add_edge(START, "chat")  # Start → chat
_builder.add_conditional_edges(  # chat → (tools or end)
    "chat", should_continue, {"tools": "tools", "__end__": END}
)
_builder.add_edge("tools", "chat")  # tools → chat (loop back)

# Compile with checkpointer (for memory across messages)
graph = _builder.compile(checkpointer=db.checkpointer)


# =============================================================================
# PUBLIC API
# =============================================================================


def clear_thread(thread_id: str) -> bool:
    """
    Clear all state for a specific thread/conversation.
    
    Parameters:
    - thread_id: The thread ID to clear
    
    Returns:
    - True if successful
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        # LangGraph's checkpointer doesn't have a direct delete method,
        # but we can update the state to empty
        graph.update_state(config, {
            "messages": [],
            "user_id": 0,
            "refund": None,
            "is_complete": False,
            "selected_order_ids": None,
            "selected_items": None,
            "refund_details": None,
            "evidence_required": False,
            "eligibility_checked": False,
            "wants_replacement": False,
            "replacement_available": False,
        })
        return True
    except Exception as e:
        print(f"Error clearing thread {thread_id}: {e}")
        return False


def invoke_graph(
    thread_id: str,
    prompt: str,
    user_id: int,
    order_item_ids: list[str] | None = None,
):
    """
    Invoke the agent with a user message.

    Parameters:
    - thread_id: Unique ID for this conversation (for memory)
    - prompt: The user's message
    - user_id: The logged-in user's ID (for fetching their orders)
    """
    if not order_item_ids:
        order_item_ids = []

    config = {"configurable": {"thread_id": thread_id}}

    # Get existing messages from checkpoint
    try:
        state_snapshot = graph.get_state(config)
        existing_messages = (
            state_snapshot.values.get("messages", []) if state_snapshot.values else []
        )
    except:
        existing_messages = []

    # Add system message if new conversation
    if not existing_messages:
        existing_messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add the new user message
    existing_messages.append(HumanMessage(content=prompt))

    # Run the graph
    for chunk in graph.stream(
        {
            "messages": existing_messages,
            "user_id": user_id,
            "refund": None,
            "is_complete": False,
            "selected_order_ids": None,
            "selected_items": None,
            "refund_details": None,
            "evidence_required": False,
            "eligibility_checked": False,
            "wants_replacement": False,
            "replacement_available": False,
        },
        config=config,
        stream_mode="updates",
    ):
        json_chunk = json.dumps(
            chunk, default=lambda o: o.dict() if hasattr(o, "dict") else str(o)
        )
        yield json_chunk + "\n"
