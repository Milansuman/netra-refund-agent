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
from models import refunds, users
from datetime import date
from netra.decorators import workflow, span, agent
from netra import Netra, SpanType, ConversationType, SpanWrapper, UsageModel
from utils import convert_tags_to_text

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
    _agent_llm = ChatLiteLLM(api_key=LITELLM_API_KEY, api_base="https://llm.keyvalue.systems", model="litellm_proxy/gpt-4.1")
    _summarizer_llm = ChatLiteLLM(api_key=LITELLM_API_KEY, api_base="https://llm.keyvalue.systems", model="litellm_proxy/gpt-4-turbo")
elif GOOGLE_API_KEY:
    _agent_llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-3-flash-preview")
    _summarizer_llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-2.5-flash-lite")
elif OPENAI_API_KEY:
    _agent_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4.1") #type: ignore
    _summarizer_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4-turbo") #type: ignore
else:
    raise ValueError("LITELLM_API_KEY, GROQ_API_KEY or GOOGLE_API_KEY not set")

# Get tool schemas by creating a temporary instance
# We'll use the actual user_id and thread_id when executing in tool_node
temp_tools_dict = RefundAgentTools(user_id=0, thread_id="temp").get_tools()
temp_tools = list(temp_tools_dict.values())
_agent_llm = _agent_llm.bind_tools(temp_tools) #type: ignore

class RefundAgentState(TypedDict):
    messages: list[AnyMessage]
    user_id: int
    thread_id: str

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

CONVERSATION FLOW:
- Determine which order item the user wants a refund/replacement for by asking for an order id and product name
- Check if the order is eligible for a refund/replacement.
- If the order is not eligible for a refund/replacement, deny the refund/replacement and offer to escalate to manager.
- Ask the user the reason for their refund/replacement request.
- If the order is eligible for a refund/replacement, process the refund/replacement.

GUIDELINES:
- Always be polite and helpful
- Keep responses as brief as possible.
- Do not ask for details which are not necessary to process the refund.
- Show the order details to help the user find their order, and before you check eligibility.
- Do not mention any tool call failures. Continue with the conversation in favour of giving the user a refund.
- Keep the conversation short and to the point.
- Do not ask the user when the order was delivered or purchased. Use tool calls to get information.
- Do not say you will process/deny, or proceed with the refund request unless you've done the eligibility check.

EXAMPLES OF LANGUAGE YOU SHOULD AVOID:
1. "Could you please confirm that you would like to request a refund for the laptop stand? If so, I will begin processing your request"

REFUND CATEGORIES:
"""
# Rules about not mentioning tool call failures and trying to guide it towards a refund is to ensure the agent fails when we want it to.
# Without those guidelines, the agent notices the broken tool call and escalates to manager.
# This is how we would expect a real agent to behave, but it does not work with the demo script, so I've intentionally added these rules.

SYSTEM_PROMPT += "\n".join([f"{refund["title"]} - {refund["description"]}" for refund in refunds.get_refund_taxonomy()])

SYSTEM_PROMPT += f"\nThe current date is {date.today().isoformat()}"

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
    with Netra.start_span(name="Chat Node", as_type=SpanType.GENERATION) as chat_span:
        messages = state["messages"]

        response = _agent_llm.invoke(messages) #type: ignore

        messages.append(response)
        input_usage = UsageModel(
            units_used=response.usage_metadata["input_tokens"] if response.usage_metadata else 0,
            usage_type="input",
            model=str(response.response_metadata["model_name"])
        )

        output_usage = UsageModel(
            units_used=response.usage_metadata["output_tokens"] if response.usage_metadata else 0,
            usage_type="output",
            model=str(response.response_metadata["model_name"])
        )

        chat_span.set_usage([input_usage, output_usage])

        return {
            "messages": messages
        }

def summarizer_node(state: RefundAgentState) -> dict:
    with Netra.start_span(name="Summarizer Node") as summarier_span:
        messages = state["messages"]

        messages.append(HumanMessage(
            content="Summarize this conversation into 6000 tokens or less. Prioritize details like order id, product name, refund reason and refund eligibility over everything else."
        ))

        response = _summarizer_llm.invoke(messages) #type: ignore

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
    with Netra.start_span(name="Tool Node", as_type=SpanType.TOOL) as tool_span:
        messages = state["messages"]
        user_id = state["user_id"]
        thread_id = state["thread_id"]
        
        last_message = messages[-1]
        
        if not isinstance(last_message, AIMessage) or not hasattr(last_message, 'tool_calls'):
            return {"messages": messages}
        
        tool_calls = last_message.tool_calls
        
        if not tool_calls:
            return {"messages": messages}
        
        # Get the actual tools with the real user_id and thread_id
        tools_by_name = RefundAgentTools(user_id, thread_id).get_tools()
        
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
    # token_count = count_tokens(messages)
    # if token_count > 6000:
    #     return "summarizer"
    
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

@agent(name="Refund Agent")
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

    user = users.get_user_by_id(user_id)

    Netra.set_user_id(user["username"].capitalize())
    Netra.set_session_id(thread_id)
    Netra.set_tenant_id("Velora")

    agent_state = graph.get_state(config) #type: ignore

    messages: list[AnyMessage] = []
    if not agent_state.values or not agent_state.values.get("messages"):
        messages = [system_message, HumanMessage(content=prompt)]
    else:
        messages = agent_state.values["messages"] + [HumanMessage(content=prompt)]

    updated_state: RefundAgentState = {
        "messages": messages,
        "user_id": user_id,
        "thread_id": thread_id,
    }

    for message in messages:
        if message.type == "human":
            Netra.add_conversation(
                conversation_type=ConversationType.INPUT,
                content=convert_tags_to_text(str(message.content)),
                role="User"
            )
        elif message.type == "ai":
            Netra.add_conversation(
                conversation_type=ConversationType.OUTPUT,
                content=convert_tags_to_text(str(message.text)),
                role="Ai"
            )

            for tool_call in message.tool_calls:
                Netra.add_conversation(
                    conversation_type=ConversationType.INPUT,
                    content=f"""{tool_call["name"]}({tool_call["args"]})""",
                    role="Tool Call"
                )
        elif message.type == "tool":
            Netra.add_conversation(
                conversation_type=ConversationType.OUTPUT,
                content=message.content,
                role="Tool Output"
            )
        elif message.type == "system":
            Netra.add_conversation(
                conversation_type=ConversationType.INPUT,
                content=message.content,
                role="System"
            )

    try:
        for chunk in graph.stream(updated_state, config=config, stream_mode="updates"): #type: ignore
            if "chat" in chunk and len(chunk["chat"]["messages"][-1].content) > 0:
                for message in chunk["chat"]["messages"]:
                    message: AnyMessage = message
                    if message.type == "ai":
                        for tool_call in message.tool_calls:
                            Netra.add_conversation(
                                conversation_type=ConversationType.INPUT,
                                content=f"""{tool_call["name"]}({tool_call["args"]})""",
                                role="Tool Call"
                            )
                    if message.type == "tool":
                        Netra.add_conversation(
                            conversation_type=ConversationType.OUTPUT,
                            content=message.content,
                            role="Tool Output"
                        )

                Netra.add_conversation(
                    conversation_type=ConversationType.OUTPUT,
                    content=convert_tags_to_text(chunk["chat"]["messages"][-1].text),
                    role="ai"
                )

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

