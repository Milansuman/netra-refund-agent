from fastapi import APIRouter, Response
from db.connections import db
import evaluate

simulation_router = APIRouter()

@simulation_router.post("/run-simulation/{dataset_id}")
def run_simulation(dataset_id: str, response: Response, failed: bool = False):
    try:
        db.return_real = not failed
        evaluate.run_simulation(dataset_id=dataset_id)
        return {
            "detail": "Simulation executed successfully"
        }
    except Exception as e:
        print(e)
        response.status_code = 400
        return {"detail": str(e)}