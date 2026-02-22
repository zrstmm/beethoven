from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import LoginRequest, TokenOut
from app.auth import create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(data: LoginRequest):
    # Получаем пароль из настроек
    result = supabase.table("settings").select("value").eq(
        "key", "admin_password"
    ).single().execute()

    if not result.data or data.password != result.data["value"]:
        raise HTTPException(status_code=401, detail="Wrong password")

    token = create_token()
    return TokenOut(token=token)
