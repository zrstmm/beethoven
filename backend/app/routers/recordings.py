import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.database import supabase
from app.schemas import RecordingOut, RecordingStatusOut, ClientResult, City
from app.services.pipeline import run_pipeline_background

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


@router.post("", response_model=RecordingOut)
async def create_recording(
    audio: UploadFile = File(...),
    employee_telegram_id: int = Form(...),
    client_name: str = Form(...),
    lesson_datetime: str = Form(...),
    result: Optional[ClientResult] = Form(None),
    city: City = Form(...),
):
    audio_bytes = await audio.read()
    logger.info(f"Recording: employee={employee_telegram_id}, client={client_name}, dt={lesson_datetime}, result={result}, city={city}, audio={len(audio_bytes)} bytes")

    # 1. Находим сотрудника
    emp = supabase.table("employees").select("*").eq(
        "telegram_id", employee_telegram_id
    ).execute()
    if not emp.data:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee = emp.data[0]

    # 2. Парсим дату (все пользователи в Казахстане, UTC+5)
    KZ_TZ = timezone(timedelta(hours=5))
    try:
        parsed_dt = datetime.strptime(lesson_datetime, "%d.%m.%Y %H:%M")
        parsed_dt = parsed_dt.replace(tzinfo=KZ_TZ)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Use DD.MM.YYYY HH:MM")

    dt_iso = parsed_dt.isoformat()

    # 3. Находим или создаём клиента
    existing_client = supabase.table("clients").select("*").eq(
        "name", client_name
    ).eq("city", city.value).eq("lesson_datetime", dt_iso).execute()

    if existing_client.data:
        client = existing_client.data[0]
        if result and not client.get("result"):
            supabase.table("clients").update(
                {"result": result.value}
            ).eq("id", client["id"]).execute()
    else:
        client_data = {
            "name": client_name,
            "city": city.value,
            "lesson_datetime": dt_iso,
        }
        if result:
            client_data["result"] = result.value
        client_res = supabase.table("clients").insert(client_data).execute()
        client = client_res.data[0]

    # 4. Создаём запись
    rec = supabase.table("recordings").insert({
        "client_id": client["id"],
        "employee_id": employee["id"],
        "audio_path": "",
        "status": "pending",
    }).execute()
    recording = rec.data[0]

    # 5. Запускаем pipeline в фоне с аудио байтами (без хранения файла)
    run_pipeline_background(recording["id"], employee["role"], audio_bytes)

    return recording


@router.get("/{recording_id}/status", response_model=RecordingStatusOut)
async def get_recording_status(recording_id: str):
    result = supabase.table("recordings").select("id, status").eq(
        "id", recording_id
    ).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Recording not found")
    return result.data[0]
