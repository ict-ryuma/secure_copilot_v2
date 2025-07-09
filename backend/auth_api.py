from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.auth import login_user

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    team_name: str
    is_admin: bool

@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    print("🔥 /login HIT:", repr(req.username), repr(req.password))
    success, team_name, is_admin = login_user(req.username, req.password)
    print("🧠 login_user returned:", success, team_name, is_admin)
    if success:
        return {
            "team_name": team_name,
            "is_admin": is_admin
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")