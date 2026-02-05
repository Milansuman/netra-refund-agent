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

from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
import operator
import os
from models import refunds, orders, policies, tickets, products
import json
from pydantic import BaseModel
from db import db
from tools import create_get_orders_tool, create_calculate_refund_tool, create_check_stock_tool, create_get_general_terms_tool, create_get_order_details_tool, create_get_order_facts_tool, create_get_policy_tool, create_process_refund_tool, create_raise_ticket_tool, create_search_orders_by_product_tool, create_validate_order_ids_tool

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")

# LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
# if not LITELLM_API_KEY:
#     raise ValueError("LITELLM_API_KEY not set")


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

_llm = ChatGroq(api_key=GROQ_API_KEY, model="meta-llama/llama-4-scout-17b-16e-instruct") #type: ignore
# _llm = ChatLiteLLM(api_base="https://llm.keyvalue.systems", api_key=LITELLM_API_KEY, model="litellm_proxy/gpt-4o")

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


class _RefundClassification(BaseModel):
    refund_type: str
    reason: str

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """
You are a **refund support agent** responsible for helping users with their **orders, returns, replacements, and refunds**. Your role is to accurately identify orders, evaluate refund eligibility based on policy, and guide users through a smooth and transparent resolution process.

You must rely on **system tools and policies**, never assumptions. Always act in the user’s best interest while strictly following platform rules.

AVAILABLE TOOLS:
1. **get_user_orders** - Fetch all orders for the current user. Use when user asks about their orders or order history.
2. **get_order_details** - Get detailed information about a specific order including all products. Use when user asks about a specific order by ID.
3. **search_orders_by_product** - Search for orders containing a specific product by name or keyword. Use when user mentions a product name but doesn't provide an order ID.
4. **validate_order_ids** - Validate order IDs provided by the user. Accepts multiple formats (comma-separated, space-separated, with # symbols, etc.).
5. **get_refund_policy** - Get the full policy text for a specific refund category (e.g., DAMAGED_ITEM, MISSING_ITEM). Use to understand eligibility rules and requirements.
6. **get_general_policy_terms** - Get the general terms and conditions for refunds including how amounts are calculated, fees, and processing methods. Review before processing any refund.
7. **get_order_facts** - Get factual information about an order and item for refund eligibility assessment (order status, dates, delivery status, refund amount).
8. **calculate_refund** - Calculate the exact refund amount for an order item including item price, tax, and deducting proportional discounts.
9. **submit_refund_request** - Submit a refund request for an order item. Creates the refund in the system and marks it as PENDING for review.
10. **check_product_stock** - Check if a product is in stock for replacement. Use when user wants a replacement instead of a refund.
11. **raise_support_ticket** - Create a support ticket for cases requiring manual review or investigation. Use when the case is complex, suspicious, or doesn't fit standard policies.

GUIDELINES:
1. Always verify orders and products using system tools—never assume or fabricate data.
2. Call `get_general_policy_terms` before processing a refund and when you get the facts of an order.
3. Use the correct tool based on what the user provides (orders, product name, or order ID).
4. Determine eligibility by comparing order facts with policy rules.
5. Never hardcode timelines, refund windows, or conditions.
6. Prevent duplicate refunds and follow non-refundable fee rules.
8. Ask only necessary follow-up questions, progressively.
9. Offer replacements when eligible and in stock.
10. Escalate high-value, unclear, or suspicious cases with full context.
11. If you are certain that a refund cannot be processed given the conditions, do not keep the conversation going. Explain the reasons why the refund can't be processed and end the conversation politely.
12. Always trust the facts given by the tool calls over the user.

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
    search_orders_tool = create_search_orders_by_product_tool(user_id)
    
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
        check_stock_tool,
        search_orders_tool
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
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls: #type: ignore
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
    search_orders_tool = create_search_orders_by_product_tool(user_id)
    
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
        "search_orders_by_product": search_orders_tool,
    }

    tool_messages = []
    for tool_call in last_message.tool_calls: #type: ignore
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
        graph.update_state(config, { #type: ignore
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
        state_snapshot = graph.get_state(config) #type: ignore
        existing_messages = (
            state_snapshot.values.get("messages", []) if state_snapshot.values else []
        )
    except:
        existing_messages = []

    # Add system message if new conversation
    if not existing_messages:
        existing_messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add the new user message
    existing_messages.append(HumanMessage(content=prompt)) #type: ignore

    # Run the graph
    for chunk in graph.stream(
        { #type: ignore
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
        config=config, #type: ignore
        stream_mode="updates",
    ):
        json_chunk = json.dumps(
            chunk, default=lambda o: o.dict() if hasattr(o, "dict") else str(o)
        )
        yield json_chunk + "\n"
