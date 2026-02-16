from fastapi import APIRouter, Depends
from schemas.users import User
from typing import Annotated
from dependencies import validate_session

user_router = APIRouter()

@user_router.get("/me")
def me(user: Annotated[User, Depends(validate_session)]):
    return user
