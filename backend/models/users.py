from db import db
from hashlib import sha256
from typing import TypedDict

class User(TypedDict):
    id: int
    email: str
    username: str
    session_id: str | None

def signup(username: str, email: str, password: str):
    db.execute("insert into users(email, password, username) values (%s,%s,%s);", (email, sha256(password.encode()).hexdigest(), username))

def login(username_or_email: str, password: str) -> str:
    users = db.execute("select id from users where (email = %s or username = %s) and password = %s;", (username_or_email, username_or_email, sha256(password.encode()).hexdigest()))

    if len(users) > 0:
        user_id: int = users[0][0]
        session_id, = db.execute("insert into sessions(id, user_id) values (%s, %s) on conflict (id) do update set user_id = %s returning id;", (sha256(str(user_id).encode()).hexdigest(), user_id, user_id))[0]
        return session_id
    else:
        raise ValueError("Invalid credentials")
    
def logout(session_id: str) -> None:
    db.execute("delete from sessions where id = %s;", (session_id,))

def get_session_user(session_id: str | None) -> User:
    # If no session_id provided, return the first user
    if session_id is None:
        first_users = db.execute("select id, username, email from users order by id limit 1;")
        if len(first_users) > 0:
            (user_id, username, email) = first_users[0]
            return {
                "id": user_id,
                "email": email,
                "username": username,
                "session_id": session_id
            }
        else:
            raise ValueError("No users exist in the database")
    
    users = db.execute("select users.id, users.username, users.email from users inner join sessions on sessions.user_id = users.id where sessions.id = %s;", (session_id,))

    if len(users) > 0:
        (user_id, username, email) = users[0]
        return {
            "id": user_id,
            "email": email,
            "username": username,
            "session_id": session_id
        }
    else:
        # If no session exists, return the first user in the table
        first_users = db.execute("select id, username, email from users order by id limit 1;")
        if len(first_users) > 0:
            (user_id, username, email) = first_users[0]
            return {
                "id": user_id,
                "email": email,
                "username": username,
                "session_id": session_id
            }
        else:
            raise ValueError("No users exist in the database")