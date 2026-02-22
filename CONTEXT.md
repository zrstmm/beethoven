# Beethoven — Контекст разработки

## Что это
Система автоматизации анализа продаж для музыкальной студии Beethoven (Астана + Усть-Каменогорск). Три компонента: Telegram-бот, FastAPI backend, React админ-панель.

## Текущий статус: MVP готов, тестируем

### Что сделано
- **Backend** (FastAPI + Pydantic + supabase-py) — все эндпоинты написаны, работает на порту 8000
- **Telegram-бот** (aiogram 3) — регистрация, отправка аудио (пошагово и одним сообщением), работает
- **Frontend** (React + Vite + CSS) — логин, канбан-доска, модалка анализа, аналитика, настройки
- **Supabase** — таблицы созданы, storage bucket `audio` создан
- **Зависимости** — всё установлено (venv в backend/ и bot/, node_modules в frontend/)
- **.env файлы** — заполнены (backend/.env и bot/.env)
- **Vite proxy** — исправлен (127.0.0.1 вместо localhost для IPv4/IPv6 совместимости)
- **Пароль админки** — синхронизируется из .env в БД при старте backend

### Где остановились
**Проблема: Telegram Bot API ограничивает скачивание файлов до 20MB**. Записи преподавателей ~60 мин, МОПов ~20-30 мин — файлы больше 20MB.

**Выбранное решение: Pyrogram** — использовать для скачивания файлов. Pyrogram работает через MTProto (лимит 2GB). aiogram остаётся для логики бота.

### Что нужно сделать дальше
1. **Пользователь должен:**
   - Зайти на https://my.telegram.org
   - Залогиниться → "API development tools" → создать приложение
   - Получить `api_id` и `api_hash`
   - Добавить их в `bot/.env`

2. **Разработка:**
   - Установить pyrogram + tgcrypto в bot/venv
   - Добавить `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` в bot/config.py
   - Создать pyrogram клиент в боте (инициализация с bot_token)
   - Заменить `bot.get_file()` + `bot.download_file()` на pyrogram download в handlers/upload.py
   - Добавить обработку ошибок в upload handler
   - Протестировать с большим аудиофайлом

3. **После решения проблемы с файлами:**
   - Протестировать полный pipeline: аудио → Supabase Storage → OpenRouter STT → OpenRouter анализ → оценка в БД
   - Проверить отображение на канбан-доске
   - Проверить модалку с анализом
   - Проверить раздел аналитики

## Как запустить
```bash
# Backend (порт 8000)
cd D:/repo/beethoven/backend
./venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Telegram бот
cd D:/repo/beethoven/bot
./venv/Scripts/python main.py

# Frontend (порт 5173, проксирует /api на backend)
cd D:/repo/beethoven/frontend
npx vite --port 5173
```

## Стек
- Backend: Python, FastAPI, Pydantic, supabase-py
- Bot: aiogram 3, httpx (+ будет pyrogram для скачивания файлов)
- Frontend: React, JavaScript, CSS, Vite, Recharts
- БД: Supabase (PostgreSQL + Storage)
- AI: OpenRouter (бесплатная модель для STT и анализа)

## Структура файлов
```
beethoven/
├── backend/
│   ├── app/
│   │   ├── main.py          — FastAPI приложение
│   │   ├── config.py         — переменные окружения
│   │   ├── database.py       — Supabase клиент
│   │   ├── schemas.py        — Pydantic модели
│   │   ├── auth.py           — JWT авторизация
│   │   ├── routers/          — API эндпоинты
│   │   └── services/         — OpenRouter STT + анализ, pipeline
│   ├── .env
│   └── requirements.txt
├── bot/
│   ├── main.py               — запуск бота
│   ├── config.py
│   ├── handlers/
│   │   ├── register.py       — регистрация сотрудников
│   │   ├── upload.py         — отправка аудиозаписей ← НУЖНО ОБНОВИТЬ (pyrogram)
│   │   └── profile.py        — профиль и статус
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js     — HTTP клиент
│   │   ├── components/       — Layout, ClientModal
│   │   ├── pages/            — Login, Analyses, Analytics, Settings
│   │   └── styles/
│   ├── package.json
│   └── vite.config.js
├── supabase_schema.sql
├── plan.md
└── CONTEXT.md                ← этот файл
```
