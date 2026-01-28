from db import Database
from hashlib import sha256

def signup(db: Database, username: str, email: str, password: str):
    db.execute("insert into users(email, password, username) values (%s,%s,%s);", (email, sha256(password.encode()).hexdigest(), username))

def login(db: Database, username_or_email: str, password: str) -> str:
    users = db.execute("select id from users where (email = %s or username = %s) and password = %s;", (username_or_email, username_or_email, sha256(password.encode()).hexdigest()))

    if len(users) > 0:
        user_id: int = users[0][0]
        session_id, = db.execute("insert into sessions(id, user_id) values (%s, %s) on conflict (id) do update set user_id = %s returning id;", (sha256(str(user_id).encode()).hexdigest(), user_id, user_id))[0]
        return session_id
    else:
        raise ValueError("Invalid credentials")
