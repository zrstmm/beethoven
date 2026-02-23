# Beethoven — Инструкция по запуску

## Требования
- Python 3.12+
- Node.js 18+
- ffmpeg (должен быть в PATH)

## 1. Настройка окружения

### Backend (.env)
```bash
# backend/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENROUTER_API_KEY=your-openrouter-key
JWT_SECRET=your-jwt-secret
ADMIN_PASSWORD=your-admin-password
```

### Bot (.env)
```bash
# bot/.env
TELEGRAM_BOT_TOKEN=your-bot-token
BACKEND_URL=http://localhost:8000
TELEGRAM_API_ID=your-api-id
TELEGRAM_API_HASH=your-api-hash
```

> `TELEGRAM_API_ID` и `TELEGRAM_API_HASH` получить на https://my.telegram.org → "API development tools"

## 2. Установка зависимостей (один раз)

```bash
# Backend
cd backend
python -m venv venv
source venv/Scripts/activate    # Windows Git Bash
pip install -r requirements.txt

# Bot
cd ../bot
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## 3. Запуск (3 терминала)

### Терминал 1 — Backend (порт 8000)
```bash
cd backend
source venv/Scripts/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Терминал 2 — Telegram-бот
```bash
cd bot
source venv/Scripts/activate
python main.py
```

### Терминал 3 — Frontend (порт 5173)
```bash
cd frontend
npx vite --host 0.0.0.0 --port 5173
```

## 4. Проверка

| Компонент | URL / Проверка |
|-----------|---------------|
| Backend health | http://localhost:8000/api/health → `{"status":"ok"}` |
| Frontend | http://localhost:5173 → страница логина |
| Bot | отправить `/start` боту в Telegram |

## 5. Порядок запуска

**Важно:** Backend должен быть запущен первым — бот и фронтенд зависят от него.

```
1. Backend  →  2. Bot  →  3. Frontend
```

## 6. Для продакшена

На сервере (VPS) вместо ручного запуска использовать systemd-сервисы или docker-compose.

### Минимальный VPS
- 1 vCPU / 1 GB RAM
- Ubuntu 22.04+
- ffmpeg: `sudo apt install ffmpeg`

### Frontend build (статика)
```bash
cd frontend
npm run build
# Файлы в frontend/dist/ — раздавать через nginx
```

### Nginx (пример)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/beethoven/frontend/dist;
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
