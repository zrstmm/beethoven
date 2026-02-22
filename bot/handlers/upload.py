import re
import uuid
import logging
import httpx
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client as PyrogramClient
from config import BACKEND_URL, SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

router = Router()

RESULT_MAP = {"bought": "Купил", "not_bought": "Не купил", "prepayment": "Предоплата"}
RESULT_PARSE = {
    "купил": "bought",
    "не купил": "not_bought",
    "предоплата": "prepayment",
    "предоплату": "prepayment",
}


class UploadState(StatesGroup):
    audio = State()
    datetime_input = State()
    client_name = State()
    result = State()


# --- Вариант Б: аудио с подписью ---

@router.message(F.audio | F.voice | F.document)
async def handle_audio_message(message: Message, state: FSMContext, bot: Bot, pyrogram_client: PyrogramClient):
    # Проверяем регистрацию
    employee = await _get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы. Используйте /start")
        return

    caption = message.caption or ""

    # Пробуем распарсить подпись: "03.05.2025 15:00 Иванов Иван купил"
    parsed = _parse_caption(caption)
    if parsed:
        await _process_upload(message, bot, employee, parsed, pyrogram_client=pyrogram_client)
        return

    # Если подписи нет или не распознана — переключаемся на пошаговый флоу
    file_id = _get_file_id(message)
    await state.update_data(file_id=file_id, employee=employee)
    await state.set_state(UploadState.datetime_input)
    await message.answer("Аудио получено! Укажите дату и время урока (ДД.ММ.ГГГГ ЧЧ:ММ):")


# --- Вариант А: пошаговый ---

@router.message(F.text == "/new")
async def cmd_new(message: Message, state: FSMContext):
    employee = await _get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы. Используйте /start")
        return
    await state.update_data(employee=employee)
    await state.set_state(UploadState.audio)
    await message.answer("Отправьте аудиозапись:")


@router.message(UploadState.audio, F.audio | F.voice | F.document)
async def process_audio(message: Message, state: FSMContext):
    file_id = _get_file_id(message)
    await state.update_data(file_id=file_id)
    await state.set_state(UploadState.datetime_input)
    await message.answer("Укажите дату и время урока (ДД.ММ.ГГГГ ЧЧ:ММ):")


@router.message(UploadState.datetime_input)
async def process_datetime(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}", text):
        await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ ЧЧ:ММ (например: 03.05.2025 15:00)")
        return
    await state.update_data(lesson_datetime=text)
    await state.set_state(UploadState.client_name)
    await message.answer("Введите имя клиента:")


@router.message(UploadState.client_name)
async def process_client_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text.strip())
    kb = InlineKeyboardBuilder()
    kb.button(text="Купил", callback_data="result:bought")
    kb.button(text="Не купил", callback_data="result:not_bought")
    kb.button(text="Предоплата", callback_data="result:prepayment")
    kb.adjust(3)
    await state.set_state(UploadState.result)
    await message.answer("Результат:", reply_markup=kb.as_markup())


@router.callback_query(UploadState.result, F.data.startswith("result:"))
async def process_result(callback: CallbackQuery, state: FSMContext, bot: Bot, pyrogram_client: PyrogramClient):
    result = callback.data.split(":")[1]
    data = await state.get_data()
    parsed = {
        "lesson_datetime": data["lesson_datetime"],
        "client_name": data["client_name"],
        "result": result,
    }
    await callback.message.edit_text(f"Отправляю запись на обработку...")
    await _process_upload(callback.message, bot, data["employee"], parsed, data["file_id"], pyrogram_client=pyrogram_client)
    await state.clear()
    await callback.answer()


# --- Утилиты ---

def _get_file_id(message: Message) -> str:
    if message.audio:
        return message.audio.file_id
    elif message.voice:
        return message.voice.file_id
    elif message.document:
        return message.document.file_id
    return ""


def _parse_caption(caption: str) -> dict | None:
    """Парсит подпись вида '03.05.2025 15:00 Иванов Иван купил'."""
    if not caption:
        return None
    pattern = r"(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+(купил|не купил|предоплат[аy])\s*$"
    match = re.match(pattern, caption.strip(), re.IGNORECASE)
    if not match:
        return None
    return {
        "lesson_datetime": match.group(1),
        "client_name": match.group(2).strip(),
        "result": RESULT_PARSE.get(match.group(3).lower(), "not_bought"),
    }


async def _get_employee(telegram_id: int) -> dict | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/employees/{telegram_id}")
        if resp.status_code == 200:
            return resp.json()
    return None


async def _process_upload(
    message: Message,
    bot: Bot,
    employee: dict,
    parsed: dict,
    file_id: str | None = None,
    pyrogram_client: PyrogramClient = None,
):
    if not file_id:
        file_id = _get_file_id(message)
        if not file_id:
            await message.answer("Не удалось получить аудиофайл.")
            return

    # 1. Скачиваем файл через Pyrogram (MTProto, лимит 2GB)
    try:
        downloaded = await pyrogram_client.download_media(
            file_id,
            in_memory=True,
        )
        audio_data = downloaded.getvalue()
    except Exception as e:
        logger.error(f"Pyrogram download failed: {e}")
        await message.answer(f"Ошибка при скачивании файла: {e}")
        return

    logger.info(f"Downloaded {len(audio_data)} bytes from Telegram")

    # 2. Загружаем напрямую в Supabase Storage
    audio_filename = f"{uuid.uuid4()}.ogg"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=300.0)) as client:
            storage_resp = await client.post(
                f"{SUPABASE_URL}/storage/v1/object/audio/{audio_filename}",
                headers={
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "audio/ogg",
                },
                content=audio_data,
            )
        if storage_resp.status_code not in (200, 201):
            logger.error(f"Supabase Storage upload failed: {storage_resp.status_code} {storage_resp.text}")
            await message.answer(f"Ошибка загрузки аудио в хранилище: {storage_resp.text}")
            return
    except Exception as e:
        logger.error(f"Supabase Storage upload error: {e}")
        await message.answer(f"Ошибка загрузки аудио: {e}")
        return

    logger.info(f"Uploaded to Supabase Storage: {audio_filename}")

    # 3. Отправляем только метаданные на backend
    result_text = RESULT_MAP.get(parsed["result"], parsed["result"])
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/recordings",
            json={
                "employee_telegram_id": employee["telegram_id"],
                "client_name": parsed["client_name"],
                "lesson_datetime": parsed["lesson_datetime"],
                "result": parsed["result"],
                "city": employee["city"],
                "audio_path": audio_filename,
            },
        )

    if resp.status_code == 200:
        await message.answer(
            f"Запись принята!\n\n"
            f"Клиент: {parsed['client_name']}\n"
            f"Дата: {parsed['lesson_datetime']}\n"
            f"Результат: {result_text}\n\n"
            f"Обработка займёт несколько минут."
        )
    else:
        await message.answer(f"Ошибка при отправке: {resp.text}")
