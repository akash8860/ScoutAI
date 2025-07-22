import hashlib, json, os
from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse

router = APIRouter()
USER_FILE = "users.json"

def read_users():
    if not os.path.exists(USER_FILE): return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def write_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    users = read_users()
    if username in users:
        return {"error": "Username exists"}
    users[username] = hashlib.sha256(password.encode()).hexdigest()
    write_users(users)
    return {"msg": "Registered"}

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = read_users()
    if username not in users:
        return {"error": "Invalid user"}
    if users[username] != hashlib.sha256(password.encode()).hexdigest():
        return {"error": "Wrong password"}
    request.session["user"] = username
    return {"msg": "Logged in"}

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"msg": "Logged out"}
