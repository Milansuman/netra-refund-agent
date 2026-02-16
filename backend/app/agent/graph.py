from typing import TypedDict
from langchain.messages import AnyMessage, ToolMessage, AIMessage, HumanMessage
from netra import Netra, SpanType, UsageModel, ConversationType
from utils import convert_tags_to_text
from netra.decorators import agent
from agent.tools import create_refund_agent_tools
import json
from langgraph.graph import StateGraph, START, END
from db.connections import db
from langchain_core.runnables import RunnableConfig
from models import users
from agent.prompts import system_message
from agent.llm import agent_llm

class RefundAgentState(TypedDict):
    messages: list[AnyMessage]
    user_id: int
    thread_id: str

def chat_node(state: RefundAgentState) -> dict:
    with Netra.start_span(name="Chat Node", as_type=SpanType.GENERATION) as chat_span:
        messages = state["messages"]

        response = agent_llm.invoke(messages) #type: ignore

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
        tools_by_name = create_refund_agent_tools(user_id, thread_id)
        
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
    
    return "end"

graph_builder = StateGraph(RefundAgentState)

# Add nodes
graph_builder.add_node("chat", chat_node)
graph_builder.add_node("tools", tool_node)

# Add edges
graph_builder.add_edge(START, "chat")
graph_builder.add_conditional_edges(
    "chat",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
graph_builder.add_edge("tools", "chat")

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