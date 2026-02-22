import httpx
import base64
from app.config import OPENROUTER_API_KEY

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Бесплатная мультимодальная модель (временное решение, можно менять)
STT_MODEL = "google/gemini-2.0-flash-exp:free"
ANALYSIS_MODEL = "google/gemini-2.0-flash-exp:free"


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Транскрибация аудио через мультимодальную модель на OpenRouter."""
    audio_b64 = base64.b64encode(audio_bytes).decode()

    payload = {
        "model": STT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Транскрибируй это аудио. Выведи только текст разговора, без комментариев. Если есть несколько говорящих, обозначь их как Говорящий 1, Говорящий 2 и т.д.",
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": mime_type.split("/")[-1],
                        },
                    },
                ],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            OPENROUTER_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def analyze_transcription(transcription: str, prompt: str) -> dict:
    """Анализ транскрипции через LLM. Возвращает {"analysis": str, "score": int}."""
    full_prompt = f"""{prompt}

Транскрипция:
{transcription}

ВАЖНО: В самом конце ответа на отдельной строке напиши только число — итоговую оценку от 1 до 10. Формат последней строки: SCORE:X (где X — число от 1 до 10)."""

    payload = {
        "model": ANALYSIS_MODEL,
        "messages": [
            {"role": "user", "content": full_prompt}
        ],
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            OPENROUTER_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    # Извлекаем оценку из последней строки
    score = 5  # дефолт
    lines = content.strip().split("\n")
    for line in reversed(lines):
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                score = int(line.replace("SCORE:", "").strip())
                score = max(1, min(10, score))
            except ValueError:
                pass
            break

    # Убираем строку SCORE из анализа
    analysis_text = "\n".join(
        l for l in lines if not l.strip().startswith("SCORE:")
    ).strip()

    return {"analysis": analysis_text, "score": score}
