from pydantic import BaseModel

class SignupData(BaseModel):
    username: str
    email: str
    password: str

class LoginData(BaseModel):
    username_or_email: str
    password: str
