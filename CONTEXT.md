# Beethoven — Контекст разработки

## Что это
Система автоматизации анализа пробных уроков и продаж для сети музыкальных студий Beethoven (Астана + Усть-Каменогорск). Три компонента: Telegram-бот, FastAPI backend, React админ-панель.

## Текущий статус: продукт готов, в тестировании

### Что работает
- **Backend** (FastAPI) — все эндпоинты, включая CRUD клиентов (GET/PUT/DELETE), расширенная аналитика
- **Telegram-бот** (aiogram 3 + Pyrogram) — регистрация, загрузка аудио с быстрыми кнопками дат/времени, разделение потоков (преподаватель vs МОП)
- **Frontend** (React + Vite) — Apple-style B&W дизайн, канбан-доска с edit/delete, 6 блоков аналитики, настройки
- **AI-пайплайн** — Gemini 2.5 Flash через OpenRouter (транскрибация + анализ)
- **Supabase** — PostgreSQL (таблицы, индексы), аудио НЕ хранится (только текст)
- **Pyrogram** — скачивание файлов до 2GB через MTProto

### Ключевые решения
- **Модель AI**: `google/gemini-2.5-flash` (и STT, и анализ) — ~$0.16 за часовую запись
- **Аудио не хранится на сервере** — скачивается, сжимается ffmpeg (mono 32kbps OGG), отправляется в OpenRouter и выбрасывается
- **Город сохраняется в localStorage** админки
- **Преподаватели не выбирают результат** (купил/не купил) — только МОПы
- **result опционален** на backend — можно создавать записи без него

### Стоимость обслуживания (~15,000-27,000 тг/мес)
| Статья | Стоимость |
|--------|-----------|
| VPS (1 vCPU, 1 GB RAM) | ~2,500-3,000 тг |
| OpenRouter (Gemini 2.5 Flash) | ~12,000-24,000 тг (зависит от кол-ва и длины записей) |
| Supabase (Free план, 500 MB) | 0 тг (хватит на ~2-3 года) |
| Telegram Bot API | 0 тг |

## Стек
- **Backend**: Python 3.12, FastAPI, Pydantic, supabase-py, PyJWT, httpx
- **Bot**: aiogram 3 (FSM), Pyrogram (MTProto файлы), httpx
- **Frontend**: React 18, Vite, Recharts, Lucide React (иконки), CSS
- **БД**: Supabase (PostgreSQL)
- **AI**: OpenRouter → Google Gemini 2.5 Flash (STT + анализ)

## Структура файлов
```
beethoven/
├── backend/
│   ├── app/
│   │   ├── main.py              — FastAPI приложение, CORS, startup
│   │   ├── config.py            — переменные окружения
│   │   ├── database.py          — Supabase клиент
│   │   ├── schemas.py           — Pydantic модели (Client, Recording, Analytics...)
│   │   ├── auth.py              — JWT авторизация
│   │   ├── routers/
│   │   │   ├── auth.py          — POST /api/auth/login
│   │   │   ├── employees.py     — CRUD сотрудников
│   │   │   ├── recordings.py    — POST /api/recordings (загрузка), GET status
│   │   │   ├── clients.py       — GET/PUT/DELETE /api/clients
│   │   │   ├── analytics.py     — GET /api/analytics (6 блоков)
│   │   │   └── settings.py      — GET/PUT /api/settings
│   │   └── services/
│   │       ├── pipeline.py      — фоновая обработка: ffmpeg → STT → анализ
│   │       └── openrouter.py    — Gemini 2.5 Flash API (STT + LLM)
│   ├── .env
│   ├── requirements.txt
│   └── venv/
├── bot/
│   ├── main.py                  — запуск бота (aiogram + Pyrogram)
│   ├── config.py                — переменные окружения
│   ├── handlers/
│   │   ├── register.py          — регистрация: имя → город → роль → направления
│   │   ├── upload.py            — загрузка аудио: кнопки дат/времени, role-aware flow
│   │   └── profile.py           — /profile, /status
│   ├── .env
│   ├── requirements.txt
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── main.jsx             — точка входа React
│   │   ├── App.jsx              — роутинг, город в localStorage
│   │   ├── api/client.js        — HTTP клиент (login, CRUD clients, analytics, settings)
│   │   ├── components/
│   │   │   ├── Layout.jsx       — header (blur), sidebar (Lucide иконки), city segmented
│   │   │   ├── ClientModal.jsx  — детальный просмотр клиента + записи
│   │   │   └── EditClientModal.jsx — редактирование клиента (имя, результат)
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx    — B&W логин
│   │   │   ├── AnalysesPage.jsx — канбан-доска (7 дней), edit/delete карточек
│   │   │   ├── AnalyticsPage.jsx — 6 секций: donut, тренд, рейтинг, направления, оценки, топ
│   │   │   └── SettingsPage.jsx — промпты + пароль
│   │   └── styles/global.css    — Apple-style B&W тема, анимации
│   ├── index.html               — Inter font (Google Fonts)
│   ├── package.json             — react, recharts, lucide-react
│   ├── vite.config.js           — proxy /api → localhost:8000
│   └── node_modules/
├── supabase_schema.sql          — DDL: employees, clients, recordings, settings
├── CONTEXT.md                   ← этот файл
├── start.md                     — инструкция запуска
└── plan.md
```

## API эндпоинты
| Метод | Путь | Описание |
|-------|------|----------|
| POST | /api/auth/login | Логин (пароль → JWT) |
| POST | /api/employees | Регистрация сотрудника |
| GET | /api/employees/{telegram_id} | Профиль сотрудника |
| PUT | /api/employees/{telegram_id} | Обновление профиля |
| POST | /api/recordings | Загрузка аудио + метаданные |
| GET | /api/recordings/{id}/status | Статус обработки |
| GET | /api/clients | Канбан (city + week_start) |
| GET | /api/clients/{id} | Детали клиента + записи |
| PUT | /api/clients/{id} | Редактирование клиента |
| DELETE | /api/clients/{id} | Удаление клиента (каскадно) |
| GET | /api/analytics | Аналитика (6 блоков) |
| GET | /api/settings | Все настройки |
| PUT | /api/settings/{key} | Обновление настройки |

## Бот: FSM-флоу загрузки аудио
```
Аудио с подписью → автопарсинг → upload (преподаватель: без result)
Аудио без подписи → date_input (кнопки: Сегодня/Вчера/Завтра)
                  → time_input (сетка 09:00-20:00)
                  → client_name
                  → result (только МОП: Купил/Не купил/Предоплата)
                  → upload
```

## Аналитика (6 блоков)
1. **Конверсия** — donut chart с % в центре
2. **Распределение оценок** — гистограмма 1-10
3. **Тренд конверсии по неделям** — area chart
4. **Рейтинг сотрудников** — таблица с bar
5. **По направлениям** — stacked bar chart
6. **Топ лучших/худших + частые ошибки**

## Что можно улучшить дальше
- Уведомления в Telegram когда анализ готов
- Экспорт аналитики в PDF/Excel
- Сравнение периодов (месяц к месяцу)
- Мобильная адаптация админки
- Автоочистка старых транскрипций (экономия места в Supabase)
- Дашборд для владельца с KPI
- Интеграция с CRM
