from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class RefundAgentState(TypedDict):
    order_ids: list[int]
    user_id: int
    