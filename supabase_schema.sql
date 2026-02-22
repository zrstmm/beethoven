-- Beethoven: схема базы данных для Supabase

-- Перечисления
CREATE TYPE employee_role AS ENUM ('teacher', 'sales_manager');
CREATE TYPE city_enum AS ENUM ('astana', 'ust_kamenogorsk');
CREATE TYPE direction_enum AS ENUM ('guitar', 'piano', 'vocal', 'dombra');
CREATE TYPE client_result AS ENUM ('bought', 'not_bought', 'prepayment');
CREATE TYPE recording_status AS ENUM ('pending', 'transcribing', 'analyzing', 'done', 'error');

-- Сотрудники
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role employee_role NOT NULL,
    city city_enum NOT NULL,
    directions direction_enum[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Клиенты (один пробный урок = одна запись)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    city city_enum NOT NULL,
    lesson_datetime TIMESTAMPTZ NOT NULL,
    result client_result,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (name, city, lesson_datetime)
);

-- Записи (аудио + транскрипция + анализ)
CREATE TABLE recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    audio_path TEXT NOT NULL,
    transcription TEXT,
    analysis TEXT,
    score SMALLINT CHECK (score >= 1 AND score <= 10),
    status recording_status DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Настройки (промпты, пароль админки)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Начальные настройки
INSERT INTO settings (key, value) VALUES
('admin_password', 'changeme'),
('prompt_teacher', 'Ты — эксперт по анализу пробных уроков в музыкальной студии. Проанализируй транскрипцию пробного урока преподавателя по следующим критериям:

1. **Прогрев клиента** — насколько преподаватель расположил к себе клиента, создал дружескую атмосферу
2. **Создание вау-эффекта** — удалось ли показать клиенту быстрый результат, впечатлить его
3. **Подготовка к продаже** — насколько преподаватель подвёл клиента к желанию продолжить обучение
4. **Вовлечение клиента** — был ли клиент активным участником, а не пассивным слушателем
5. **Общее впечатление** — общая оценка урока

По каждому критерию дай оценку от 1 до 10 и краткий комментарий.
В конце дай итоговую оценку от 1 до 10 и общий вывод.

Формат ответа:
**1. Прогрев клиента: X/10**
Комментарий...

**2. Создание вау-эффекта: X/10**
Комментарий...

**3. Подготовка к продаже: X/10**
Комментарий...

**4. Вовлечение клиента: X/10**
Комментарий...

**5. Общее впечатление: X/10**
Комментарий...

**Итоговая оценка: X/10**
Общий вывод...'),
('prompt_sales', 'Ты — эксперт по анализу продаж в музыкальной студии. Проанализируй транскрипцию разговора менеджера отдела продаж с клиентом после пробного урока по следующим критериям:

1. **Выявление потребностей** — задавал ли менеджер вопросы, выяснял мотивацию клиента
2. **Работа с возражениями** — как менеджер обрабатывал сомнения и возражения клиента
3. **Презентация продукта** — насколько убедительно менеджер представил программу обучения и условия
4. **Закрытие сделки** — предложил ли конкретный план действий, довёл ли до покупки
5. **Общее качество продажи** — профессионализм, уверенность, эмпатия

По каждому критерию дай оценку от 1 до 10 и краткий комментарий.
В конце дай итоговую оценку от 1 до 10 и общий вывод.

Формат ответа:
**1. Выявление потребностей: X/10**
Комментарий...

**2. Работа с возражениями: X/10**
Комментарий...

**3. Презентация продукта: X/10**
Комментарий...

**4. Закрытие сделки: X/10**
Комментарий...

**5. Общее качество продажи: X/10**
Комментарий...

**Итоговая оценка: X/10**
Общий вывод...');

-- Индексы
CREATE INDEX idx_clients_city_datetime ON clients(city, lesson_datetime);
CREATE INDEX idx_recordings_client_id ON recordings(client_id);
CREATE INDEX idx_recordings_status ON recordings(status);
CREATE INDEX idx_employees_telegram_id ON employees(telegram_id);

-- Storage bucket (выполнить через Supabase Dashboard или API):
-- Создать bucket "audio" с public access = false
