# Сервис аналитики (Analytics Service)

## 1. Название и назначение сервиса
Сервис аналитики — микросервис, который отвечает за сбор и предоставление статистической информации об опросах. Реализует базовую аналитику по опросам и агрегированную статистику по пользователям.

Основные функции:
- получение базовой статистики по опросу (количество ответов)
- получение статистики по всем опросам пользователя
- проверка работоспособности сервиса

## 2. Архитектура и зависимости
Технологии и фреймворки:
- Python 3.11+
- FastAPI
- HTTPX (HTTP-клиент)
- Pydantic v2
- Pytest (тесты)
- Ruff (линтер)

Взаимодействие с другими микросервисами:
- сервис аналитики отправляет HTTP-запросы к сервису опросов для получения данных:
  - `GET /surveys/{id}/answers/count` — количество ответов по опросу
  - `GET /users/{user_id}/surveys` — список опросов пользователя

Внешние сервисы:
- нет

## 3. Способы запуска сервиса

### Локальный запуск

```bash
cd services/analytics-service
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8003
```

Для запуска с явным указанием URL сервиса опросов:

```bash
python -m uvicorn app.main:app --reload --port 8003
```

## 4. API документация
Swagger/OpenAPI:
- `http://localhost:8003/docs`
- `http://localhost:8003/openapi.json`

Основные эндпоинты:
- `GET /health` — проверка работоспособности сервиса
- `GET /analytics/surveys/{id}/basic` — базовая статистика по опросу
- `GET /analytics/users/{id}/statistics` — статистика по всем опросам пользователя

## 5. Как тестировать

```bash
cd services/analytics-service
pip install -r requirements-dev.txt
pytest
```

Если `pytest` не найден:

```bash
python -m pytest
```

Проверка качества кода:

```bash
ruff check .
ruff format .
```

## 6. Контакты и поддержка
Авторы:
- Бозванов Иван

Контакты:
- GitHub Issues: https://github.com/isco25/pius_project
- Telegram: @Bozvanchik
```
