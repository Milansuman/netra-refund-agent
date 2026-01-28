from fastapi import FastAPI
from db import Database

app = FastAPI()
db = Database()

@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "all systems operational"
    }