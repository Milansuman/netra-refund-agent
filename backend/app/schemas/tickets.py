from typing import TypedDict

class Ticket(TypedDict):
    id: int
    order_id: int
    user_id: int
    title: str
    description: str | None