from fastapi import Response, Cookie, HTTPException
from typing import Annotated
from models import users

def validate_session(session_id: Annotated[str | None, Cookie()] = None):
    try:
        # if not session_id:
        #     raise HTTPException(403)

        return users.get_session_user(session_id=session_id)
    except ValueError as e:
        raise HTTPException(403, e)