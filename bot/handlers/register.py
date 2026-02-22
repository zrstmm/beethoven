import httpx
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BACKEND_URL

router = Router()

DIRECTIONS_BY_CITY = {
    "astana": [
        ("guitar", "Гитара"),
        ("piano", "Фортепиано"),
        ("vocal", "Вокал"),
        ("dombra", "Домбра"),
    ],
    "ust_kamenogorsk": [
        ("guitar", "Гитара"),
        ("piano", "Фортепиано"),
        ("vocal", "Вокал"),
    ],
}


class RegisterState(StatesGroup):
    name = State()
    city = State()
    role = State()
    directions = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Проверяем, зарегистрирован ли уже
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/employees/{message.from_user.id}")
        if resp.status_code == 200:
            emp = resp.json()
            await message.answer(
                f"Вы уже зарегистрированы как {emp['name']}.\n"
                f"Используйте /new для отправки записи.\n"
                f"Используйте /profile для просмотра профиля."
            )
            return

    await state.set_state(RegisterState.name)
    await message.answer("Добро пожаловать в Beethoven! Как вас зовут?")


@router.message(RegisterState.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    kb = InlineKeyboardBuilder()
    kb.button(text="Астана", callback_data="city:astana")
    kb.button(text="Усть-Каменогорск", callback_data="city:ust_kamenogorsk")
    kb.adjust(1)
    await state.set_state(RegisterState.city)
    await message.answer("Выберите город:", reply_markup=kb.as_markup())


@router.callback_query(RegisterState.city, F.data.startswith("city:"))
async def process_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(":")[1]
    await state.update_data(city=city)
    kb = InlineKeyboardBuilder()
    kb.button(text="Преподаватель", callback_data="role:teacher")
    kb.button(text="Менеджер отдела продаж", callback_data="role:sales_manager")
    kb.adjust(1)
    await state.set_state(RegisterState.role)
    await callback.message.edit_text("Ваша должность:", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(RegisterState.role, F.data.startswith("role:"))
async def process_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[1]
    await state.update_data(role=role, directions=[])

    if role == "teacher":
        data = await state.get_data()
        city = data["city"]
        await state.set_state(RegisterState.directions)
        await callback.message.edit_text(
            "Выберите направления (можно несколько, затем нажмите Готово):",
            reply_markup=_build_directions_kb(city, []),
        )
        await callback.answer()
    else:
        # МОП — сразу регистрируем
        await _finish_registration(callback.message, state, callback.from_user.id)
        await callback.answer()


@router.callback_query(RegisterState.directions, F.data.startswith("dir:"))
async def process_direction(callback: CallbackQuery, state: FSMContext):
    direction = callback.data.split(":")[1]
    data = await state.get_data()
    dirs = data.get("directions", [])

    if direction in dirs:
        dirs.remove(direction)
    else:
        dirs.append(direction)

    await state.update_data(directions=dirs)
    city = data["city"]
    await callback.message.edit_reply_markup(
        reply_markup=_build_directions_kb(city, dirs),
    )
    await callback.answer()


@router.callback_query(RegisterState.directions, F.data == "dirs_done")
async def process_directions_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("directions"):
        await callback.answer("Выберите хотя бы одно направление!")
        return
    await _finish_registration(callback.message, state, callback.from_user.id)
    await callback.answer()


def _build_directions_kb(city: str, selected: list[str]):
    kb = InlineKeyboardBuilder()
    for dir_id, dir_name in DIRECTIONS_BY_CITY.get(city, []):
        mark = " ✓" if dir_id in selected else ""
        kb.button(text=f"{dir_name}{mark}", callback_data=f"dir:{dir_id}")
    kb.button(text="Готово ✅", callback_data="dirs_done")
    kb.adjust(2)
    return kb.as_markup()


async def _finish_registration(message, state: FSMContext, telegram_id: int):
    data = await state.get_data()
    payload = {
        "telegram_id": telegram_id,
        "name": data["name"],
        "role": data["role"],
        "city": data["city"],
        "directions": data.get("directions", []),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}/api/employees", json=payload)

    if resp.status_code == 200:
        role_text = "Преподаватель" if data["role"] == "teacher" else "Менеджер отдела продаж"
        city_text = "Астана" if data["city"] == "astana" else "Усть-Каменогорск"
        text = f"Регистрация завершена!\n\n{data['name']}\n{role_text} — {city_text}"
        if data.get("directions"):
            dir_names = {
                "guitar": "Гитара", "piano": "Фортепиано",
                "vocal": "Вокал", "dombra": "Домбра",
            }
            dirs = ", ".join(dir_names.get(d, d) for d in data["directions"])
            text += f"\nНаправления: {dirs}"
        text += "\n\nИспользуйте /new для отправки записи."
        await message.edit_text(text)
    else:
        await message.edit_text(f"Ошибка регистрации: {resp.text}")

    await state.clear()
