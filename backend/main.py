from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, Request, Cookie, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from psycopg.errors import UniqueViolation
from typing import Annotated
from datetime import datetime
import uuid
import json

from models import users, orders
from agent import invoke_graph, clear_thread
from db import db
import os
from netra import Netra, SpanWrapper
from netra.instrumentation.instruments import InstrumentSet
import evaluate

Netra.init(
    headers=f"x-api-key={os.getenv('NETRA_API_KEY')}",
    app_name="Refund agent",
    debug_mode=True,
    trace_content=True,
    block_instruments={InstrumentSet.LANGCHAIN, InstrumentSet.PSYCOPG}, #type: ignore
    enable_root_span=True
)

Netra.set_tenant_id("Velora")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Setup the database tables for the checkpointer
    try:
        db.setup_checkpointer()
        db.push()
        print("INFO: Database initialized (Checkpointer + Migrations)")
    except Exception as e:
        print(f"WARNING: Could not setup checkpointer: {e}")
    yield
    # Shutdown logic (if any) can go here
    db.close()


app = FastAPI(lifespan=lifespan)
# span: SpanWrapper | None = None

# Dependencies
def validate_session(
    response: Response, session_id: Annotated[str | None, Cookie()] = None
):
    try:
        # if not session_id:
        #     raise HTTPException(403)

        return users.get_session_user(session_id=session_id)
    except ValueError as e:
        raise HTTPException(403, e)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthcheck")
def healthcheck():
    return {"status": "all systems operational"}


class SignupData(BaseModel):
    username: str
    email: str
    password: str


@app.post("/signup")
def signup(data: SignupData, response: Response):
    try:
        users.signup(data.username, data.email, data.password)
    except UniqueViolation:
        response.status_code = 400
        return {"detail": "User already exists"}


class LoginData(BaseModel):
    username_or_email: str
    password: str


@app.post("/login")
def login(data: LoginData, response: Response):
    try:
        session_id = users.login(data.username_or_email, data.password)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return session_id
    except ValueError:
        response.status_code = 400
        return {"detail": "Invalid credentials"}


@app.post("/logout")
def logout(response: Response, session_id: Annotated[str | None, Cookie()] = None):
    if not session_id:
        raise HTTPException(403)

    users.logout(session_id)
    response.delete_cookie("session_id")


@app.get("/me")
def me(user: Annotated[users.User, Depends(validate_session)]):
    return user


@app.get("/orders")
def get_orders(
    response: Response, user: Annotated[users.User, Depends(validate_session)]
):
    try:
        return {"orders": orders.get_user_orders(user_id=user["id"])}
    except ValueError as e:
        response.status_code = 400

        return {"detail": e}


class ChatRequest(BaseModel):
    prompt: str
    thread_id: str | None = None

@app.post("/chat")
def chat(
    chat: ChatRequest,
    response: Response,
    user: Annotated[users.User, Depends(validate_session)],
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
        Netra.set_user_id(user["username"].capitalize())
        Netra.set_session_id(current_thread)

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


@app.delete("/chat/{thread_id}")
def clear_chat(
    thread_id: str,
    response: Response,
    user: Annotated[users.User, Depends(validate_session)],
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

@app.post("/run-simulation/{dataset_id}")
def run_simulation(dataset_id: str, response: Response, failed: bool = False):
    try:
        db.return_real = not failed
        evaluate.run_simulation(dataset_id=dataset_id)
        return {
            "detail": "Simulation executed successfully"
        }
    except Exception as e:
        print(e)
        response.status_code = 400
        return {"detail": str(e)}
