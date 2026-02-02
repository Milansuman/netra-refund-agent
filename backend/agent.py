from langgraph.graph import StateGraph, START, END
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from typing import TypedDict
from dotenv import load_dotenv
import os
from models import refunds
import json
from pydantic import BaseModel
from db import db

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")


class RefundAgentState(TypedDict):
    order_item_ids: list[str]
    messages: list[AnyMessage]
    refund: dict | None
    is_complete: bool


_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")  # type: ignore


class _RefundClassification(BaseModel):
    refund_type: str
    reason: str


# SYSTEM PROMPT
SYSTEM_PROMPT = """You are a refund agent that listens to the users complaints and categorizes it into one of the given refund categories. Ask questions to the user until you're sure of which refund type to classify the complaint as. Respond normally to the user until you've figured out the refund type, at which point respond with the following schema:

{
    refund_type: string,
    reason: string // Summary of complaint
}

Only use refund_type other if you're absolutely sure that the complaint doesn't fit into any of the other categories.

GUIDELINES:
- Ask questions and converse with the user until you're sure of the refund type
- Return JSON of the given schema when you figure out the refund type
- Do not add text before or after the JSON when you find the refund type

REFUND CATEGORIES:
"""

SYSTEM_PROMPT += "\n".join(
    [
        f"{refund['title']} - {refund['description']}"
        for refund in refunds.get_refund_taxonomy()
    ]
)

SYSTEM_PROMPT += "\nOther - Refund reason does not fit in any other category\n"


def chat_node(state: RefundAgentState) -> dict:
    """Process the conversation and generate a response."""
    messages = state.get("messages", [])

    # Ensure system message is first
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

    # Get LLM response
    response = _llm.invoke(messages)
    messages.append(response)

    # Check if this is a refund classification (JSON response)
    refund = None
    is_complete = False
    try:
        refund = json.loads(str(response.content))
        _RefundClassification(**refund)
        is_complete = True
    except:
        pass

    return {"messages": messages, "refund": refund, "is_complete": is_complete}


# Build the graph - simple single-node design
_builder = StateGraph(RefundAgentState)
_builder.add_node("chat", chat_node)
_builder.add_edge(START, "chat")
_builder.add_edge("chat", END)

graph = _builder.compile(checkpointer=db.checkpointer)


def invoke_graph(
    thread_id: str,
    prompt: str,
    order_item_ids: list[str] | None = None,
):
    """
    Invoke the refund agent with a user message.

    This is a simpler design that:
    1. Loads the existing conversation from the checkpoint
    2. Adds the new user message
    3. Generates a response
    4. Saves the updated state to the checkpoint
    """
    if not order_item_ids:
        order_item_ids = []

    # Get existing state from checkpoint (if any)
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_snapshot = graph.get_state(config)
        existing_messages = (
            state_snapshot.values.get("messages", []) if state_snapshot.values else []
        )
    except:
        existing_messages = []

    # Add system message if it's a new conversation
    if not existing_messages:
        existing_messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Add the new user message
    existing_messages.append(HumanMessage(content=prompt))

    # Run the graph
    for chunk in graph.stream(
        {
            "order_item_ids": order_item_ids,
            "messages": existing_messages,
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
