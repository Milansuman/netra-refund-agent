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
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
import operator
import os
from models import refunds, orders
import json
from pydantic import BaseModel
from db import db

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")


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


# =============================================================================
# LLM SETUP
# =============================================================================

_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")


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
    def get_order_details(order_id: int) -> str:
        """
        Get detailed information about a specific order including all products.
        Use this when the user asks about a specific order by ID, like
        "show me order #1" or "what's in order 2".

        Args:
            order_id: The order ID to look up (e.g., 1, 2, 3)
        """
        try:
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
                    elif discount.get("amount"):
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

3. ALWAYS call the appropriate tool first. Do NOT make up order or product information.
4. The tools will return real data that you should present to the user.

For refund requests, categorize complaints into types. Ask questions until you're sure, then respond with ONLY this JSON:

{
    "refund_type": string,
    "reason": string
}

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

    # Create tools with the user's ID
    get_orders_tool = create_get_orders_tool(user_id)
    get_order_details_tool = create_get_order_details_tool(user_id)
    tools = [get_orders_tool, get_order_details_tool]

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
    tools_by_name = {
        "get_user_orders": get_orders_tool,
        "get_order_details": get_order_details_tool,
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
        },
        config=config,
        stream_mode="updates",
    ):
        json_chunk = json.dumps(
            chunk, default=lambda o: o.dict() if hasattr(o, "dict") else str(o)
        )
        yield json_chunk + "\n"
