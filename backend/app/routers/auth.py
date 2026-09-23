"""Login route. Same behavior as the Express auth router."""
import secrets

from fastapi import APIRouter, Body

from ..config import settings
from ..errors import AppError

router = APIRouter()


@router.post("/login")
def login(payload: dict | None = Body(default=None)):
    data = payload or {}
    username = str(data.get("username") if data.get("username") is not None else "").strip()
    password = str(data.get("password") if data.get("password") is not None else "")
    if username == settings.admin_user and password == settings.admin_password:
        return {"token": secrets.token_urlsafe(24), "username": username}
    raise AppError(401, "Invalid username or password.")
