from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import EmployeeCreate, EmployeeOut

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.post("", response_model=EmployeeOut)
async def create_employee(data: EmployeeCreate):
    # Проверяем, не зарегистрирован ли уже
    existing = supabase.table("employees").select("*").eq(
        "telegram_id", data.telegram_id
    ).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Employee already registered")

    row = {
        "telegram_id": data.telegram_id,
        "name": data.name,
        "role": data.role.value,
        "city": data.city.value,
        "directions": [d.value for d in data.directions],
    }
    result = supabase.table("employees").insert(row).execute()
    return result.data[0]


@router.get("/{telegram_id}", response_model=EmployeeOut)
async def get_employee(telegram_id: int):
    result = supabase.table("employees").select("*").eq(
        "telegram_id", telegram_id
    ).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result.data[0]


@router.put("/{telegram_id}", response_model=EmployeeOut)
async def update_employee(telegram_id: int, data: EmployeeCreate):
    result = supabase.table("employees").update({
        "name": data.name,
        "role": data.role.value,
        "city": data.city.value,
        "directions": [d.value for d in data.directions],
    }).eq("telegram_id", telegram_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    return result.data[0]
