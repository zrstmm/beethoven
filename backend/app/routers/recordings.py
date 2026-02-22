import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase
from app.schemas import RecordingOut, RecordingStatusOut, ClientResult, City
from app.services.pipeline import run_pipeline_background

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


class CreateRecordingRequest(BaseModel):
    employee_telegram_id: int
    client_name: str
    lesson_datetime: str  # "DD.MM.YYYY HH:MM"
    result: ClientResult
    city: City
    audio_path: str  # filename in Supabase Storage (uploaded by bot)


@router.post("", response_model=RecordingOut)
async def create_recording(body: CreateRecordingRequest):
    logger.info(f"Recording: employee={body.employee_telegram_id}, client={body.client_name}, dt={body.lesson_datetime}, result={body.result}, city={body.city}, audio={body.audio_path}")

    # 1. Находим сотрудника
    emp = supabase.table("employees").select("*").eq(
        "telegram_id", body.employee_telegram_id
    ).execute()
    if not emp.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee = emp.data[0]

    # 2. Парсим дату
    try:
        parsed_dt = datetime.strptime(body.lesson_datetime, "%d.%m.%Y %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use DD.MM.YYYY HH:MM")

    dt_iso = parsed_dt.isoformat()

    # 3. Находим или создаём клиента
    existing_client = supabase.table("clients").select("*").eq(
        "name", body.client_name
    ).eq("city", body.city.value).eq("lesson_datetime", dt_iso).execute()

    if existing_client.data:
        client = existing_client.data[0]
        if not client.get("result"):
            supabase.table("clients").update(
                {"result": body.result.value}
            ).eq("id", client["id"]).execute()
    else:
        client_res = supabase.table("clients").insert({
            "name": body.client_name,
            "city": body.city.value,
            "lesson_datetime": dt_iso,
            "result": body.result.value,
        }).execute()
        client = client_res.data[0]

    # 4. Создаём запись (аудио уже загружено ботом в Supabase Storage)
    rec = supabase.table("recordings").insert({
        "client_id": client["id"],
        "employee_id": employee["id"],
        "audio_path": body.audio_path,
        "status": "pending",
    }).execute()
    recording = rec.data[0]

    # 5. Запускаем pipeline в фоне
    run_pipeline_background(recording["id"], employee["role"])

    return recording


@router.get("/{recording_id}/status", response_model=RecordingStatusOut)
async def get_recording_status(recording_id: str):
    result = supabase.table("recordings").select("id, status").eq(
        "id", recording_id
    ).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Recording not found")
    return result.data[0]
