from typing import TypedDict

class User(TypedDict):
    id: int
    email: str
    username: str
    session_id: str | None