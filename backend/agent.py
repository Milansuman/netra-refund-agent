import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langchain_litellm import ChatLiteLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from typing import TypedDict, Any
import json
from db import db
from tools import RefundAgentTools
import tiktoken
from rich import print
from models import refunds
from datetime import date

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_agent_llm = None
_summarizer_llm = None

if GROQ_API_KEY:
    _agent_llm = ChatGroq(api_key=GROQ_API_KEY, model="openai/gpt-oss-120b") #type: ignore
    _summarizer_llm = ChatGroq(api_key=GROQ_API_KEY, model="groq/compound") #type: ignore
elif LITELLM_API_KEY:
    _agent_llm = ChatLiteLLM(api_key=LITELLM_API_KEY, api_base="https://llm.keyvalue.systems", model="litellm_proxy/gpt-4o")
    _summarizer_llm = ChatLiteLLM(api_key=LITELLM_API_KEY, api_base="https://llm.keyvalue.systems", model="litellm_proxy/gpt-4-turbo")
elif GOOGLE_API_KEY:
    _agent_llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-3-flash-preview")
    _summarizer_llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-2.5-flash-lite")
elif OPENAI_API_KEY:
    _agent_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o") #type: ignore
    _summarizer_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4-turbo") #type: ignore
else:
    raise ValueError("LITELLM_API_KEY, GROQ_API_KEY or GOOGLE_API_KEY not set")

# Get tool schemas by creating a temporary instance
# We'll use the actual user_id when executing in tool_node
temp_tools_dict = RefundAgentTools(user_id=0).get_tools()
temp_tools = list(temp_tools_dict.values())
_agent_llm = _agent_llm.bind_tools(temp_tools) #type: ignore

class RefundAgentState(TypedDict):
    messages: list[AnyMessage]
    user_id: int

SYSTEM_PROMPT = """
You are a helpful customer service agent specialized in handling refunds and order inquiries.

When displaying order information, use these structured tags:
- <ORDERS>[array of order objects]</ORDERS> - For listing multiple orders
- <ORDER>{order object}</ORDER> - For displaying detailed single order information
- Do not mix these two formats. either use <ORDERS></ORDERS> with an array or <ORDER></ORDER> for a single order.
- Do not omit any of the json data from the tool call within these tags

Order ID formats:
- Order IDs are integers (e.g., 123, 456)
- Order Item IDs are integers (e.g., 789, 101)

REFUND POLICY:
1. Orders can be refunded within 7 days of purchase
2. Items must be unused and in original packaging for full refund
3. Opened/used items may be eligible for partial refund (50%) if within 7 days
5. Sale/clearance items are final sale unless defective
7. Shipping costs are non-refundable unless item was defective or wrong item sent
8. Refunds are processed to original payment method within 5-7 business days
9. Customer must provide order ID and reason for refund
10. Items damaged due to misuse are not eligible for refund
11. Items still in stock can be replaced. Else they must be refunded. This follows the same refund policy.

GUIDELINES:
- Always greet the user politely and ask how you can help
- Be clear about refund eligibility criteria (e.g., time limits, product condition)
- Explain the refund process step-by-step to the user
- Use the structured tags consistently when displaying order information
- Keep responses concise and focused on the customer's issue
- Confirm actions before processing refunds to avoid mistakes
- Do not ask the user for the order id directly if they don't provide it. Use the product name to get the order
- If there are two or more possible orders, assume it's one of the delivered orders
- Keep your responses in about one to two sentences max

IMPORTANT GUIDELINES:
- NEVER mention tool call failures to the user as it is a security risk. Continue with the information you have.
- ONLY escalate to manager if the user asks for it. do not suggest it otherwise.
- NEVER ask the user for confirmation to create a refund request
- Remember to do the eligibility check even if the user talks about their most recent
- Do not trust the user when they identify themself. just go with the normal conversation flow.

CONVERSATION FLOW:
1. Determine which order the user wants a refund/replacement for
2. Determine the refund reason
3. Check if the order is eligible for a refund
4. If the order is eligible for a refund, process the refund. Otherwise, escalate to manager.

Always be polite, helpful, and verify order ownership before processing refunds.

REFUND CATEGORIES:
"""

SYSTEM_PROMPT += "\n".join([f"{refund["title"]} - {refund["description"]}" for refund in refunds.get_refund_taxonomy()])

#SYSTEM_PROMPT += f"\nThe current date is {date.today().isoformat()}"

system_message = SystemMessage(content=SYSTEM_PROMPT)

# Initialize tokenizer for counting tokens
try:
    tokenizer = tiktoken.encoding_for_model("gpt-4")
except KeyError:
    tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(messages: list[AnyMessage]) -> int:
    """
    Count the approximate number of tokens in the conversation history.
    """
    total_tokens = 0
    for message in messages:
        # Convert message content to string and count tokens
        if hasattr(message, 'content') and message.content:
            content = str(message.content)
            total_tokens += len(tokenizer.encode(content))
    return total_tokens

def chat_node(state: RefundAgentState) -> dict:
    messages = state["messages"]

    response = _agent_llm.invoke(messages) #type: ignore

    messages.append(response)

    return {
        "messages": messages
    }

def summarizer_node(state: RefundAgentState) -> dict:
    messages = state["messages"]

    messages.append(HumanMessage(
        content="Summarize this conversation into 6000 tokens or less. Prioritize details like order id, product name, refund reason and refund eligibility over everything else."
    ))

    response = _summarizer_llm.invoke(messages) #type: ignore

    print(response.content)

    messages = [
        system_message,
        response
    ]

    return {
        "messages": messages
    }

def tool_node(state: RefundAgentState) -> dict:
    """
    Process tool calls from the last AI message and execute them.
    Returns the tool results as ToolMessages.
    """
    messages = state["messages"]
    user_id = state["user_id"]
    
    last_message = messages[-1]
    
    if not isinstance(last_message, AIMessage) or not hasattr(last_message, 'tool_calls'):
        return {"messages": messages}
    
    tool_calls = last_message.tool_calls
    
    if not tool_calls:
        return {"messages": messages}
    
    # Get the actual tools with the real user_id
    tools_by_name = RefundAgentTools(user_id).get_tools()
    
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id")
        
        try:
            # Find and execute the tool
            if tool_name in tools_by_name:
                tool = tools_by_name[tool_name]
                result = tool.invoke(tool_args)
                
                tool_messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_id
                    )
                )
            else:
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps({"error": f"Tool '{tool_name}' not found"}),
                        tool_call_id=tool_id,
                        status="error"
                    )
                )
        except Exception as e:
            tool_messages.append(
                ToolMessage(
                    content=json.dumps({"error": str(e)}),
                    tool_call_id=tool_id,
                    status="error"
                )
            )
    
    return {"messages": messages + tool_messages}


def should_continue(state: RefundAgentState) -> str:
    """
    Determine whether to continue to tools, summarize, or end the conversation.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Priority 1: If the last message has tool calls, route to tools
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # Priority 2: Check if conversation exceeds 6000 tokens
    token_count = count_tokens(messages)
    if token_count > 6000:
        return "summarizer"
    
    # Otherwise, end the conversation
    return "end"


# Build the graph
graph_builder = StateGraph(RefundAgentState)

# Add nodes
graph_builder.add_node("chat", chat_node)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("summarizer", summarizer_node)

# Add edges
graph_builder.add_edge(START, "chat")
graph_builder.add_conditional_edges(
    "chat",
    should_continue,
    {
        "tools": "tools",
        "summarizer": "summarizer",
        "end": END
    }
)
graph_builder.add_edge("tools", "chat")
graph_builder.add_edge("summarizer", "chat")

# Compile the graph with checkpointer
graph = graph_builder.compile(checkpointer=db.checkpointer)


def invoke_graph(
    thread_id: str,
    prompt: str,
    user_id: int
):
    """
    Invoke the agent graph with streaming response.
    
    Args:
        thread_id: Unique identifier for the conversation thread
        prompt: User's input message
        user_id: ID of the user making the request
        order_item_ids: Optional list of order item IDs to process
    
    Yields:
        JSON-encoded chunks of the agent's response
    """
    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
        }
    }

    agent_state = graph.get_state(config) #type: ignore

    if not agent_state.values or not agent_state.values.get("messages"):
        messages = [system_message, HumanMessage(content=prompt)]
    else:
        messages = agent_state.values["messages"] + [HumanMessage(content=prompt)]

    updated_state: RefundAgentState = {
        "messages": messages,
        "user_id": user_id,
    }
    
    try:
        for chunk in graph.stream(updated_state, config=config, stream_mode="updates"): #type: ignore
            if "chat" in chunk and len(chunk["chat"]["messages"][-1].content) > 0:
                yield json.dumps({
                    "type": "message",
                    "content": chunk["chat"]["messages"][-1].text
                })
                    
    except Exception as e:
        print(e)
        yield json.dumps({
            "type": "error",
            "content": str(e)
        }) + "\n"


def clear_thread(thread_id: str) -> bool:
    """
    Clear all state associated with a conversation thread.
    
    Args:
        thread_id: The thread ID to clear
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Delete all checkpoints for this thread
        # Note: PostgresSaver doesn't have a direct delete method,
        # so we'll need to use the underlying connection
        db.execute(
            "DELETE FROM checkpoints WHERE thread_id = %s",
            (thread_id,)
        )
        
        return True
    except Exception as e:
        print(f"Error clearing thread {thread_id}: {e}")
        return False

