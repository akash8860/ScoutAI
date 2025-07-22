import json, os
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()
HISTORY_FILE = "history.json"

def save_history(user, url, city, mode, file_path):
    log = {
        "user": user,
        "url": url,
        "city": city,
        "mode": mode,
        "file": file_path,
        "timestamp": datetime.now().isoformat()
    }
    data = []
    if os.path.exists(HISTORY_FILE):
        data = json.load(open(HISTORY_FILE))
    data.append(log)
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/history")
def get_history():
    if not os.path.exists(HISTORY_FILE): return []
    return json.load(open(HISTORY_FILE))
