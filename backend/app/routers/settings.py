from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.schemas import SettingOut, SettingUpdate
from app.auth import verify_token

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=list[SettingOut])
async def get_settings(_: str = Depends(verify_token)):
    result = supabase.table("settings").select("*").execute()
    return result.data


@router.get("/{key}", response_model=SettingOut)
async def get_setting(key: str, _: str = Depends(verify_token)):
    result = supabase.table("settings").select("*").eq("key", key).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Setting not found")
    return result.data


@router.put("/{key}", response_model=SettingOut)
async def update_setting(key: str, data: SettingUpdate, _: str = Depends(verify_token)):
    result = supabase.table("settings").update(
        {"value": data.value}
    ).eq("key", key).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Setting not found")
    return result.data[0]
