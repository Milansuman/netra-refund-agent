from netra import Netra
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.connections import db
from netra.instrumentation.instruments import InstrumentSet
from routers import (
    chat,
    auth,
    orders,
    simulations,
    users
)
from config import config

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        db.setup_checkpointer()
        db.push()
        print("INFO: Database initialized (Checkpointer + Migrations)")
    except Exception as e:
        print(f"WARNING: Could not setup checkpointer: {e}")
    yield
    db.close()

Netra.init(
    headers=f"x-api-key={config.NETRA_API_KEY}",
    app_name="Refund agent",
    environment="development",
    debug_mode=True,
    trace_content=True,
    # instruments={InstrumentSet.FASTAPI},
    block_instruments={InstrumentSet.LANGCHAIN, InstrumentSet.PSYCOPG, InstrumentSet.OPENAI, InstrumentSet.LITELLM, InstrumentSet.REQUESTS, InstrumentSet.HTTPX}, #type: ignore
)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.auth_router)
app.include_router(users.user_router)
app.include_router(chat.chat_router)
app.include_router(orders.order_router)
app.include_router(simulations.simulation_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

