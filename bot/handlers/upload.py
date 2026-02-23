import re
import logging
from datetime import datetime, timedelta
import httpx
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram import Client as PyrogramClient
from config import BACKEND_URL

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
    date_input = State()
    time_input = State()
    client_name = State()
    result = State()


def _build_date_keyboard():
    """Строим клавиатуру с быстрыми датами: Сегодня, Вчера, Завтра."""
    kb = InlineKeyboardBuilder()
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    for label, d in [
        (f"Сегодня ({d.strftime('%d.%m')})" if (d := today) else "", today),
        (f"Вчера ({d.strftime('%d.%m')})" if (d := yesterday) else "", yesterday),
        (f"Завтра ({d.strftime('%d.%m')})" if (d := tomorrow) else "", tomorrow),
    ]:
        kb.button(text=label, callback_data=f"qdate:{d.strftime('%d.%m.%Y')}")
    kb.adjust(3)
    return kb.as_markup()


def _build_time_keyboard():
    """Строим клавиатуру с сеткой времени."""
    kb = InlineKeyboardBuilder()
    for hour in range(9, 21):
        kb.button(text=f"{hour:02d}:00", callback_data=f"qtime:{hour:02d}:00")
    kb.adjust(4)
    return kb.as_markup()


# --- Вариант Б: аудио с подписью ---

@router.message(F.audio | F.voice | F.document)
async def handle_audio_message(message: Message, state: FSMContext, bot: Bot, pyrogram_client: PyrogramClient):
    # Проверяем регистрацию
    employee = await _get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы. Используйте /start")
        return

    caption = message.caption or ""

    # Пробуем распарсить подпись
    parsed = _parse_caption(caption, employee.get("role", "sales_manager"))
    if parsed:
        await _process_upload(message, bot, employee, parsed, pyrogram_client=pyrogram_client)
        return

    # Если подписи нет или не распознана — переключаемся на пошаговый флоу
    file_id = _get_file_id(message)
    await state.update_data(file_id=file_id, employee=employee)
    await state.set_state(UploadState.date_input)
    await message.answer(
        "Аудио получено! Выберите дату урока или введите вручную (ДД.ММ.ГГГГ):",
        reply_markup=_build_date_keyboard(),
    )


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
    await state.set_state(UploadState.date_input)
    await message.answer(
        "Выберите дату урока или введите вручную (ДД.ММ.ГГГГ):",
        reply_markup=_build_date_keyboard(),
    )


# --- Дата: callback от кнопок ---
@router.callback_query(UploadState.date_input, F.data.startswith("qdate:"))
async def process_date_callback(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":", 1)[1]
    await state.update_data(lesson_date=date_str)
    await callback.answer()
    await callback.message.edit_text(
        f"Дата: {date_str}\nВыберите время или введите вручную (ЧЧ:ММ):",
        reply_markup=_build_time_keyboard(),
    )
    await state.set_state(UploadState.time_input)


# --- Дата: текстовый ввод ---
@router.message(UploadState.date_input)
async def process_date_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r"\d{2}\.\d{2}\.\d{4}$", text):
        await message.answer(
            "Неверный формат. Используйте ДД.ММ.ГГГГ (например: 23.02.2026)\nИли выберите дату кнопкой:",
            reply_markup=_build_date_keyboard(),
        )
        return
    await state.update_data(lesson_date=text)
    await state.set_state(UploadState.time_input)
    await message.answer(
        f"Дата: {text}\nВыберите время или введите вручную (ЧЧ:ММ):",
        reply_markup=_build_time_keyboard(),
    )


# --- Время: callback от кнопок ---
@router.callback_query(UploadState.time_input, F.data.startswith("qtime:"))
async def process_time_callback(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.split(":", 1)[1]
    data = await state.get_data()
    lesson_datetime = f"{data['lesson_date']} {time_str}"
    await state.update_data(lesson_datetime=lesson_datetime)
    await callback.answer()
    await callback.message.edit_text(f"Дата и время: {lesson_datetime}\nВведите имя клиента:")
    await state.set_state(UploadState.client_name)


# --- Время: текстовый ввод ---
@router.message(UploadState.time_input)
async def process_time_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not re.match(r"\d{2}:\d{2}$", text):
        await message.answer(
            "Неверный формат. Используйте ЧЧ:ММ (например: 15:00)\nИли выберите время кнопкой:",
            reply_markup=_build_time_keyboard(),
        )
        return
    data = await state.get_data()
    lesson_datetime = f"{data['lesson_date']} {text}"
    await state.update_data(lesson_datetime=lesson_datetime)
    await state.set_state(UploadState.client_name)
    await message.answer(f"Дата и время: {lesson_datetime}\nВведите имя клиента:")


@router.message(UploadState.client_name)
async def process_client_name(message: Message, state: FSMContext, bot: Bot, pyrogram_client: PyrogramClient):
    await state.update_data(client_name=message.text.strip())
    data = await state.get_data()
    employee = data["employee"]

    # Если преподаватель — пропускаем выбор результата
    if employee.get("role") == "teacher":
        parsed = {
            "lesson_datetime": data["lesson_datetime"],
            "client_name": data["client_name"],
            "result": None,
        }
        await message.answer("Отправляю запись на обработку...")
        await _process_upload(message, bot, employee, parsed, data.get("file_id"), pyrogram_client=pyrogram_client)
        await state.clear()
        return

    # МОП — показываем кнопки результата
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
    await callback.answer()
    await callback.message.edit_text("Отправляю запись на обработку...")
    await _process_upload(callback.message, bot, data["employee"], parsed, data.get("file_id"), pyrogram_client=pyrogram_client)
    await state.clear()


# --- Утилиты ---

def _get_file_id(message: Message) -> str:
    if message.audio:
        return message.audio.file_id
    elif message.voice:
        return message.voice.file_id
    elif message.document:
        return message.document.file_id
    return ""


def _parse_caption(caption: str, role: str = "sales_manager") -> dict | None:
    """Парсит подпись вида '03.05.2025 15:00 Иванов Иван купил' (МОП)
    или '03.05.2025 15:00 Иванов Иван' (преподаватель)."""
    if not caption:
        return None

    # Пробуем полный формат (с результатом)
    pattern_full = r"(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})\s+(.+?)\s+(купил|не купил|предоплат[аy])\s*$"
    match = re.match(pattern_full, caption.strip(), re.IGNORECASE)
    if match:
        return {
            "lesson_datetime": match.group(1),
            "client_name": match.group(2).strip(),
            "result": RESULT_PARSE.get(match.group(3).lower(), "not_bought"),
        }

    # Для преподавателей — формат без результата
    if role == "teacher":
        pattern_short = r"(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})\s+(.+?)\s*$"
        match = re.match(pattern_short, caption.strip(), re.IGNORECASE)
        if match:
            return {
                "lesson_datetime": match.group(1),
                "client_name": match.group(2).strip(),
                "result": None,
            }

    return None


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

    # 2. Отправляем аудио + метаданные на backend
    form_data = {
        "employee_telegram_id": str(employee["telegram_id"]),
        "client_name": parsed["client_name"],
        "lesson_datetime": parsed["lesson_datetime"],
        "city": employee["city"],
    }
    if parsed.get("result"):
        form_data["result"] = parsed["result"]

    result_text = RESULT_MAP.get(parsed.get("result", ""), "—")

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/recordings",
            data=form_data,
            files={"audio": ("recording.ogg", audio_data, "audio/ogg")},
        )

    if resp.status_code == 200:
        result_line = f"Результат: {result_text}\n" if parsed.get("result") else ""
        await message.answer(
            f"Запись принята!\n\n"
            f"Клиент: {parsed['client_name']}\n"
            f"Дата: {parsed['lesson_datetime']}\n"
            f"{result_line}\n"
            f"Обработка займёт несколько минут."
        )
    else:
        await message.answer(f"Ошибка при отправке: {resp.text}")
