from netra import Netra
from netra.simulation import BaseTask, TaskResult
from dotenv import load_dotenv
import os
from typing import Optional
from uuid import uuid4
from agent import invoke_graph
import json
from utils import convert_tags_to_text, format_order_to_text

load_dotenv()

NETRA_API_KEY = os.getenv("NETRA_API_KEY")
if not NETRA_API_KEY:
    raise ValueError("NETRA_API_KEY not set")


class RefundAgentTask(BaseTask):
    
    def run(self, message: str, session_id: Optional[str] = None) -> TaskResult:
        # Generate thread_id similar to chat endpoint in main.py
        thread_id = uuid4().hex if not session_id else session_id
        user_id = 1  # Using test user for simulation

        # Invoke the agent graph and collect the response (similar to chat endpoint)
        final_message = ""
        for chunk in invoke_graph(thread_id, message, user_id):
            try:
                # Parse the JSON chunk from the stream
                chunk_data = json.loads(chunk.strip())
                
                # Check for new streaming format: {"type": "message", "content": "..."}
                if chunk_data.get("type") == "message" and chunk_data.get("content"):
                    final_message = chunk_data["content"]
                elif chunk_data.get("type") == "error":
                    # Handle error responses
                    final_message = f"Error: {chunk_data.get('content', 'Unknown error')}"
            except (json.JSONDecodeError, KeyError, AttributeError):
                # Skip malformed or incomplete chunks
                continue

        # Convert structured tags to human-friendly text
        final_message = convert_tags_to_text(final_message)

        return TaskResult(
            message=final_message,
            session_id=thread_id
        )
    
def run_simulation(dataset_id: str) -> None:
    Netra.simulation.run_simulation( #type: ignore
        name="Refund Agent Simulation",
        dataset_id=dataset_id,
        task=RefundAgentTask()
    )


def main():
    Netra.init(
        headers=f"x-api-key={os.getenv('NETRA_API_KEY')}",
        app_name="Refund agent simulation",
        debug_mode=True,
        trace_content=True
    )

    run_simulation("b7e09b66-2ccc-4610-8fa5-591c50d61ad6")

    
if  __name__ == "__main__":
    main()