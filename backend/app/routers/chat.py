from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from schemas.chat import ChatRequest
from schemas.users import User
from dependencies import validate_session
from typing import Annotated
import uuid
import json
from agent.graph import invoke_graph

from models.threads import clear_thread

chat_router = APIRouter()


@chat_router.post("/chat")
def chat(
    chat: ChatRequest,
    response: Response,
    user: Annotated[User, Depends(validate_session)],
):
    """
    Chat endpoint that connects the frontend to the refund agent.

    The 'user' parameter comes from validate_session which:
    1. Reads the session_id cookie
    2. Looks up the user in the database
    3. Returns the user dict with 'id', 'username', 'email'

    We pass user['id'] to the agent so tools can fetch user-specific data.
    """
    try:
        # Generate new thread_id if not provided
        current_thread = ""
        if chat.thread_id == None:
            current_thread = str(uuid.uuid4())
        else:
            current_thread = chat.thread_id

        # Get the user's ID from the session
        user_id = user["id"]

        def generate():
            # First, yield the thread_id so frontend can track it
            yield json.dumps({"thread_id": current_thread}) + "\n"
            # Then yield the agent response chunks
            # Note: We pass user_id so the agent can fetch their orders
            for chunk in invoke_graph(
                current_thread, chat.prompt, user_id
            ):
                yield chunk

        return StreamingResponse(generate(), media_type="application/x-ndjson")
    except ValueError as e:
        print(e)
        response.status_code = 400
        return {"detail": str(e)}


@chat_router.delete("/chat/{thread_id}")
def clear_chat(
    thread_id: str,
    response: Response
):
    """
    Clear/delete a conversation thread.
    This removes all state associated with the thread_id.
    """
    try:
        success = clear_thread(thread_id)
        if success:
            return {"message": "Thread cleared successfully"}
        else:
            response.status_code = 500
            return {"detail": "Failed to clear thread"}
    except Exception as e:
        print(e)
        response.status_code = 400
        return {"detail": str(e)}