import httpx
from aiogram import Router, F
from aiogram.types import Message
from config import BACKEND_URL

router = Router()

DIR_NAMES = {
    "guitar": "Гитара",
    "piano": "Фортепиано",
    "vocal": "Вокал",
    "dombra": "Домбра",
}

CITY_NAMES = {
    "astana": "Астана",
    "ust_kamenogorsk": "Усть-Каменогорск",
}


@router.message(F.text == "/profile")
async def cmd_profile(message: Message):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/employees/{message.from_user.id}")
    if resp.status_code != 200:
        await message.answer("Вы не зарегистрированы. Используйте /start")
        return

    emp = resp.json()
    role_text = "Преподаватель" if emp["role"] == "teacher" else "Менеджер отдела продаж"
    city_text = CITY_NAMES.get(emp["city"], emp["city"])
    text = f"Ваш профиль:\n\n{emp['name']}\n{role_text} — {city_text}"

    if emp.get("directions"):
        dirs = ", ".join(DIR_NAMES.get(d, d) for d in emp["directions"])
        text += f"\nНаправления: {dirs}"

    await message.answer(text)


@router.message(F.text == "/status")
async def cmd_status(message: Message):
    # Получаем последние записи через сотрудника
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/employees/{message.from_user.id}")
    if resp.status_code != 200:
        await message.answer("Вы не зарегистрированы. Используйте /start")
        return

    await message.answer(
        "Функция просмотра статуса будет доступна в ближайшем обновлении."
    )
