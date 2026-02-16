from fastapi import APIRouter
from schemas.auth import LoginData, SignupData
from fastapi import Response, HTTPException, Cookie
from models import users
from typing import Annotated
from psycopg.errors import UniqueViolation

auth_router = APIRouter()

@auth_router.post("/login")
def login(data: LoginData, response: Response):
    try:
        session_id = users.login(data.username_or_email, data.password)
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return session_id
    except ValueError:
        response.status_code = 400
        return {"detail": "Invalid credentials"}
    
@auth_router.post("/logout")
def logout(response: Response, session_id: Annotated[str | None, Cookie()] = None):
    if not session_id:
        raise HTTPException(403)

    users.logout(session_id)
    response.delete_cookie("session_id")


@auth_router.post("/signup")
def signup(data: SignupData, response: Response):
    try:
        users.signup(data.username, data.email, data.password)
    except UniqueViolation:
        response.status_code = 400
        return {"detail": "User already exists"}
