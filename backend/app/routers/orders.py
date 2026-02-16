from fastapi import APIRouter, Depends, Response
from schemas.users import User
from typing import Annotated
from dependencies import validate_session

from models import orders

order_router = APIRouter()

@order_router.get("/orders")
def get_orders(
    response: Response, user: Annotated[User, Depends(validate_session)]
):
    try:
        return {"orders": orders.get_user_orders(user_id=user["id"])}
    except ValueError as e:
        response.status_code = 400

        return {"detail": e}
