from netra import Netra
from netra.simulation import BaseTask, TaskResult
from dotenv import load_dotenv
import os
from typing import Optional
from uuid import uuid4
from agent import invoke_graph
import json

load_dotenv()

NETRA_API_KEY = os.getenv("NETRA_API_KEY")
if not NETRA_API_KEY:
    raise ValueError("NETRA_API_KEY not set")

class RefundAgentTask(BaseTask):
    
    def run(self, message: str, session_id: Optional[str] = None) -> TaskResult:
        # Generate thread_id similar to chat endpoint in main.py
        thread_id = uuid4().hex if not session_id else session_id
        user_id = 1  # Using test user for simulation
        order_item_ids = None

        # Invoke the agent graph and collect the response (similar to chat endpoint)
        final_message = ""
        for chunk in invoke_graph(thread_id, message, user_id, order_item_ids):
            try:
                # Parse the JSON chunk from the stream
                chunk_data = json.loads(chunk.strip())
                
                # Check if this chunk contains a chat node update with AI messages
                if "chat" in chunk_data:
                    messages = chunk_data["chat"].get("messages", [])
                    if messages:
                        # Extract the AI's response from the last message
                        last_msg = messages[-1]
                        if isinstance(last_msg, dict) and last_msg.get("type") == "ai":
                            final_message = last_msg.get("content", "")
                        elif isinstance(last_msg, str):
                            final_message = last_msg
                        elif hasattr(last_msg, "content"):
                            final_message = last_msg.content #type: ignore
            except (json.JSONDecodeError, KeyError, AttributeError):
                # Skip malformed or incomplete chunks
                continue

        return TaskResult(
            message=final_message,
            session_id=thread_id
        )


def main():
    Netra.init(
        headers=f"x-api-key={os.getenv('NETRA_API_KEY')}",
        app_name="Refund agent simulation",
        debug_mode=True,
        trace_content=True
    )

    Netra.simulation.run_simulation( #type: ignore
        name="Refund Agent Simulation",
        dataset_id="8692d768-29f9-45d7-8845-bbafd5b2b2ff",
        task=RefundAgentTask()
    )

if  __name__ == "__main__":
    main()