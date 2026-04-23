# Сервис опросов (Survey Service)

## 1. Название и назначение сервиса
Сервис опросов — микросервис, который отвечает за хранение и управление опросами,
категориями и вопросами, а также за прием и валидацию ответов пользователей.
Сервис хранит связь с user-service через `author_id` и `respondent_id`,
а для безопасной интеграции поддерживает идемпотентность при сохранении ответов.

Основные функции:
- создание, чтение, обновление и удаление опросов
- хранение категории и структуры вопросов внутри опроса
- сохранение ответов на опросы
- валидация ответов по типу вопроса
- поиск опросов по категории
- защита от дублей через идемпотентность и бизнес-ключи
- подсчет количества ответов по опросу

## 2. Архитектура и зависимости
Технологии и фреймворки:
- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic (миграции)
- SQLite (по умолчанию)
- Pytest (тесты)

Взаимодействие с другими микросервисами:
- сервис опросов предоставляет API, которым пользуются другие сервисы (например, аналитика, пользователи)
- исходящих запросов к другим сервисам у survey-service нет

Внешние сервисы:
- нет

## 3. Способы запуска сервиса

### Локальный запуск
```bash
cd services/survey-service
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8001
```

### Переменные окружения
- `DATABASE_URL` — строка подключения к БД (по умолчанию `sqlite:///./survey.db`).

### Миграции
Создание таблиц выполняется через Alembic:
```bash
cd services/survey-service
python -m alembic upgrade head
```

## 4. API документация
Swagger/OpenAPI:
- `http://localhost:8001/docs`
- `http://localhost:8001/openapi.json`

Основные эндпоинты:
- `POST /surveys` — создать опрос
- `GET /surveys` — список опросов или поиск по `category`
- `GET /surveys/{id}` — получить опрос по id
- `PUT /surveys/{id}` — обновить опрос
- `DELETE /surveys/{id}` — удалить опрос
- `POST /answers` — сохранить ответ
- `GET /surveys/{id}/answers/count` — количество ответов

## 5. Как тестировать
```bash
cd services/survey-service
pytest
```

Если `pytest` не найден:
```bash
python -m pytest
```

### Линтер и форматтер
```bash
cd services/survey-service
python -m ruff check .
python -m ruff format .
```

Пример тела запроса для `POST /answers`:
```json
{
  "survey_id": 1,
  "respondent_id": 42,
  "answers": [
    {"name": "experience", "value": "Отлично"},
    {"name": "language", "value": "python"},
    {"name": "topics", "value": ["api", "testing"]}
  ]
}
```

Пример тела запроса для `POST /surveys`:
```json
{
  "author_id": 7,
  "title": "Backend Survey",
  "description": "Сбор ответов от разработчиков",
  "category": "tech",
  "status": "active",
  "questions": [
    {"name": "experience", "text": "Какой был опыт?", "type": "text", "required": true},
    {
      "name": "language",
      "text": "Выбери основной язык",
      "type": "single_choice",
      "options": ["python", "go", "java"],
      "required": true
    },
    {
      "name": "topics",
      "text": "Выбери интересующие темы",
      "type": "multiple_choice",
      "options": ["api", "db", "testing"],
      "required": false
    }
  ]
}
```

Для `POST /answers` можно передавать заголовки:
- `Idempotency-Key` — повтор одного и того же запроса не создаст дубль
- `X-Source-Service` — имя сервиса-отправителя, например `users-service`

## 6. Контакты и поддержка
Авторы:
- Ивар Скалеух

Контакты:
- GitHub Issues: https://github.com/isco25/pius_project
- Telegram: @Truasu
