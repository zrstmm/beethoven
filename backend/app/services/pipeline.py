import asyncio
import traceback
from app.database import supabase
from app.services.openrouter import transcribe_audio, analyze_transcription


async def process_recording(recording_id: str, employee_role: str):
    """Фоновый pipeline: транскрибация → анализ → сохранение."""
    try:
        # 1. Обновляем статус
        supabase.table("recordings").update(
            {"status": "transcribing"}
        ).eq("id", recording_id).execute()

        # 2. Скачиваем аудио из Supabase Storage
        rec = supabase.table("recordings").select("audio_path").eq(
            "id", recording_id
        ).single().execute()
        audio_path = rec.data["audio_path"]
        audio_bytes = supabase.storage.from_("audio").download(audio_path)

        # 3. Транскрибация
        transcription = await transcribe_audio(audio_bytes)

        supabase.table("recordings").update(
            {"transcription": transcription, "status": "analyzing"}
        ).eq("id", recording_id).execute()

        # 4. Получаем промпт из настроек
        prompt_key = "prompt_teacher" if employee_role == "teacher" else "prompt_sales"
        setting = supabase.table("settings").select("value").eq(
            "key", prompt_key
        ).single().execute()
        prompt = setting.data["value"]

        # 5. Анализ
        result = await analyze_transcription(transcription, prompt)

        supabase.table("recordings").update({
            "analysis": result["analysis"],
            "score": result["score"],
            "status": "done",
        }).eq("id", recording_id).execute()

    except Exception as e:
        traceback.print_exc()
        supabase.table("recordings").update(
            {"status": "error"}
        ).eq("id", recording_id).execute()


def run_pipeline_background(recording_id: str, employee_role: str):
    """Запускает pipeline в фоне."""
    asyncio.create_task(process_recording(recording_id, employee_role))
