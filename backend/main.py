from fastapi import FastAPI, Response, Request, Cookie, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg.errors import UniqueViolation
from typing import Annotated

from models import users, orders

app = FastAPI()

# Dependencies
def validate_session(response: Response, session_id: Annotated[str | None, Cookie()] = None):
    try:
        if not session_id:
            raise HTTPException(403)
        
        return users.get_session_user(session_id=session_id)
    except ValueError as e:
        raise HTTPException(403, e)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "all systems operational"
    }

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
        return {
            "detail": "User already exists"
        }

class LoginData(BaseModel):
    username_or_email: str
    password: str

@app.post("/login")
def login(data: LoginData, response: Response):
    try:
        session_id = users.login(data.username_or_email, data.password)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True
        )
        return session_id
    except ValueError:
        response.status_code = 400
        return {
            "detail": "Invalid credentials"
        }
    
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
def get_orders(response: Response, user: Annotated[users.User, Depends(validate_session)]):
    try:
        return {
            "orders": orders.get_user_orders(user_id=user["id"])
        }
    except ValueError as e:
        response.status_code = 400

        return {
            "detail": e
        }
    
@app.post("/chat")
def chat(response: Response, user: Annotated[users.User, Depends(validate_session)]):
    try:
        pass
    except ValueError as e:
        response.status_code = 400

        return {
            "detail": e
        }