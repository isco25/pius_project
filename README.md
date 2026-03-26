# Survey Platform API

Минимальный backend-каркас для лабораторной работы №2 "Базовая инфраструктура и ядро системы".

Сейчас в проекте реализована часть разработчика A:

- сервис пользователей;
- регистрация `POST /register`;
- авторизация с JWT `POST /login`;
- получение пользователя `GET /users/{id}`;
- unit/integration tests для пользовательского модуля;
- базовая инфраструктура проекта, линтер и форматтер.

## Стек

- Python 3.11+
- FastAPI
- SQLite (`sqlite3` из стандартной библиотеки)
- JWT на HMAC SHA-256
- Ruff для lint/format
- unittest + FastAPI TestClient

## Структура проекта

```text
src/
  app/
    config.py
    database.py
    main.py
    security.py
    users/
tests/
```

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --app-dir src --reload
```

По умолчанию база создается в `data/survey_platform.db`.

## Переменные окружения

- `APP_NAME` - имя приложения, по умолчанию `Survey Platform API`
- `DATABASE_URL` - путь к SQLite-файлу, по умолчанию `data/survey_platform.db`
- `JWT_SECRET` - секрет для подписи JWT, по умолчанию `change-me-in-production`
- `JWT_EXPIRATION_MINUTES` - срок жизни токена, по умолчанию `60`

## Эндпоинты

### `POST /register`

Создает нового пользователя.

Пример тела запроса:

```json
{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

### `POST /login`

Возвращает JWT-токен.

Пример ответа:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### `GET /users/{id}`

Возвращает пользователя по `id`.

Требует заголовок:

```text
Authorization: Bearer <jwt>
```

## Проверки

Запуск тестов:

```bash
python -m unittest discover -s tests -v
```

Запуск линтера:

```bash
python -m ruff check .
```

Форматирование:

```bash
python -m ruff format .
```

## Дальнейшее расширение

Каркас приложения уже готов к добавлению сервисов аналитики, опросов и ответов в отдельных модулях с подключением роутеров в `src/app/main.py`.
