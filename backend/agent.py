from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langchain.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from typing import TypedDict, Literal
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

_llm = ChatGroq(
    api_key=GROQ_API_KEY, #type: ignore
    model="llama-3.3-70b-versatile"
)

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

REFUND CATEGORIES:\n
"""

SYSTEM_PROMPT += "\n".join([f"{refund["title"]} - {refund["description"]}" for refund in refunds.get_refund_taxonomy()])

SYSTEM_PROMPT += "\nOther - Refund reason does not fit in any other category\n"

# SYSTEM PROMPT


def collect_complaint_node(state: RefundAgentState) -> dict:
    messages = state["messages"]

    user_prompt = interrupt(messages[-1].content)
    messages.append(HumanMessage(
        content=user_prompt
    ))

    response = _llm.invoke(messages)
    messages.append(response)

    return {
        "messages": messages
    }

def should_continue_complaint_conversation(state: RefundAgentState) -> Command[Literal["collect_complaint_node", "output_messages"]]:
    messages = state["messages"]

    try:
        refund = json.loads(str(messages[-1].content))
        _RefundClassification(**refund)
        return Command(
            goto="output_messages",
            update={
                "refund": refund
            }
        )
    except:
        return Command(
            goto="collect_complaint_node"
        )
    
def output_messages_node(state: RefundAgentState) -> None:
    print(state["messages"])

_builder = StateGraph(RefundAgentState)
_builder.add_node("should_continue_complain_conversation", should_continue_complaint_conversation)
_builder.add_node("collect_complaint_node", collect_complaint_node)
_builder.add_node("output_messages", output_messages_node)

_builder.add_edge(START, "collect_complaint_node")
_builder.add_edge("collect_complaint_node", "should_continue_complain_conversation")
_builder.add_edge("output_messages", END)

graph = _builder.compile(checkpointer=db.checkpointer)

def invoke_graph(order_item_ids: list[str] | None, thread_id: str, prompt: str | None, new_chat: bool = False):
    if new_chat:
        if not order_item_ids:
            raise ValueError("Order item ids can't be None in a new chat")

        messages: list[AnyMessage] = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]
        for chunk in graph.stream({
            "order_item_ids": order_item_ids,
            "messages": messages,
            "refund": None
        }, config={
            "configurable": {
                "thread_id": thread_id
            }
        }, stream_mode=["messages"]):
            print(chunk)
            yield chunk
    else:
        for chunk in graph.stream(Command(resume=prompt), config={
            "configurable": {
                "thread_id": thread_id
            }
        }, stream_mode=["messages"]):
            yield chunk