from fastapi import APIRouter
import json, os

router = APIRouter()
STATUS_FILE = "status.json"

@router.get("/status")
def get_status():
    if not os.path.exists(STATUS_FILE):
        return {"status": "Idle"}
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

def update_status(message: str):
    with open(STATUS_FILE, "w") as f:
        json.dump({"status": message}, f)
