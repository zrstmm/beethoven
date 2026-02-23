import asyncio
import logging
import traceback
from app.database import supabase
from app.services.openrouter import transcribe_audio, analyze_transcription

logger = logging.getLogger(__name__)


async def compress_audio(audio_bytes: bytes) -> bytes:
    """Сжимает аудио в mono 32kbps OGG через ffmpeg для экономии токенов API."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", "pipe:0",
        "-ac", "1",           # mono
        "-b:a", "32k",        # 32 kbps
        "-map", "0:a",        # только аудио
        "-f", "ogg",          # формат
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=audio_bytes)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {stderr.decode()}")
    return stdout


async def process_recording(recording_id: str, employee_role: str, audio_bytes: bytes):
    """Фоновый pipeline: сжатие → транскрибация → анализ → сохранение."""
    try:
        # 1. Обновляем статус
        supabase.table("recordings").update(
            {"status": "transcribing"}
        ).eq("id", recording_id).execute()

        # 2. Сжимаем аудио перед отправкой в API
        original_size = len(audio_bytes)
        audio_bytes = await compress_audio(audio_bytes)
        logger.info(f"Recording {recording_id}: compressed {original_size} -> {len(audio_bytes)} bytes")

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


def run_pipeline_background(recording_id: str, employee_role: str, audio_bytes: bytes):
    """Запускает pipeline в фоне."""
    asyncio.create_task(process_recording(recording_id, employee_role, audio_bytes))
