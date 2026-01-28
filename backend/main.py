from fastapi import FastAPI, Response, Request
from db import Database
from pydantic import BaseModel
from psycopg.errors import UniqueViolation

from models import users

app = FastAPI()
db = Database()

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
        users.signup(db, data.username, data.email, data.password)
    except UniqueViolation:
        response.status_code = 400
        return {
            "error": "User already exists"
        }

class LoginData(BaseModel):
    username_or_email: str
    password: str

@app.post("/login")
def login(data: LoginData, response: Response):
    try:
        session_id = users.login(db, data.username_or_email, data.password)
        response.set_cookie(
            key="SESSION",
            value=session_id,
            httponly=True
        )
        return session_id
    except ValueError:
        return {
            "error": "Invalid credentials"
        }