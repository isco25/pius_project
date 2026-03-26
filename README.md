# Survey Analytics Platform

## 1. Название и назначение проекта

**Survey Analytics Platform** — это платформа для создания опросов, сбора ответов и анализа данных. 

### Состав платформы

| Сервис | Роль | Основные функции |
|--------|------|------------------|
| **User Service** | Управление пользователями | Регистрация, авторизация, профили пользователей |
| **Survey Service** | Управление опросами и ответами | CRUD опросов, сохранение ответов, валидация |
| **Analytics Service** | Аналитика и статистика | Базовая статистика по опросам |

---

## 2. Архитектура проекта

### Технологический стек

| Технология | Назначение |
|------------|------------|
| **Python 3.11+** | Язык программирования для всех сервисов |
| **FastAPI** | Веб-фреймворк для создания REST API |
| **Uvicorn** | ASGI-сервер для запуска приложений |
| **Pydantic** | Валидация данных и сериализация |
| **HTTPX** | Асинхронный HTTP-клиент для взаимодействия между сервисами |
| **Pytest** | Фреймворк для тестирования |
| **Ruff** | Линтер и форматтер кода |

**Связи между сервисами на текущем этапе:**
- **Analytics Service** → **Survey Service**: получение данных об опросах и количества ответов
- **Survey Service** → **User Service**: проверка авторизации пользователей (при создании опросов и ответов)

---

## 3. Запуск проекта

### Требования
- Python 3.11 или выше
- Git

### Способ 1: Локальный запуск всех сервисов

#### Шаг 1: Клонирование репозитория
```bash
git clone <repository-url>
cd survey-analytics-platform
```


#### Шаг 2: Запуск User Service (порт 8001)
```bash
cd user-service
python -m venv .venv
source .venv/Scripts/activate
/.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt (если нужны тесты/ruff)
./.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir src --reload
```

#### Шаг 3: Запуск Survey Service (порт 8002)
```bash
cd survey-service
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

#### Шаг 4: Запуск Analytics Service (порт 8003)
```bash
cd analytics-service
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

### Переменные окружения

Для каждого сервиса можно настроить переменные окружения:

**Analytics Service:**
```env
SURVEY_SERVICE_URL=http://localhost:8002
HOST=0.0.0.0
PORT=8003
```

**Survey Service:**
```env
USER_SERVICE_URL=http://localhost:8001
HOST=0.0.0.0
PORT=8002
```

**User Service:**
```env
SECRET_KEY=your-secret-key-here
HOST=0.0.0.0
PORT=8001
```

---

## 4. API документация

После запуска каждого сервиса документация доступна по адресу `/docs`:

| Сервис | Swagger UI |
|--------|------------|
| User Service | http://localhost:8001/docs | 
| Survey Service | http://localhost:8002/docs | 
| Analytics Service | http://localhost:8003/docs | 

### Эндпоинты по сервисам

#### User Service (порт 8001)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/register` | Регистрация нового пользователя |
| `POST` | `/login` | Авторизация, получение JWT токена |
| `GET` | `/users/{id}` | Получение информации о пользователе |

#### Survey Service (порт 8002)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/surveys` | Создание нового опроса |
| `GET` | `/surveys/{id}` | Получение опроса по ID |
| `PUT` | `/surveys/{id}` | Обновление опроса |
| `DELETE` | `/surveys/{id}` | Удаление опроса |
| `POST` | `/answers` | Сохранение ответа на опрос |

#### Analytics Service (порт 8003)

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/health` | Проверка работоспособности сервиса |
| `GET` | `/analytics/surveys/{id}/basic` | Получение базовой статистики по опросу |
| `GET` | `/analytics/users/{id}/statistics` | Получение статистики по всем опросам пользователя |


## 5. Тестирование

### Запуск тестов для конкретного сервиса

```bash
# User Service
cd user-service
pip install -r requirements-dev.txt
pytest

# Survey Service
cd survey-service
pip install -r requirements-dev.txt
pytest

# Analytics Service
cd analytics-service
pip install -r requirements-dev.txt
pytest
```

### Линтинг и форматирование кода

Все сервисы используют Ruff для проверки стиля кода:

```bash
# В каждом сервисе
ruff check .              # Проверка кода
ruff check --fix .        # Автоисправление проблем
ruff format .             # Форматирование кода
```

---


## 6. Контакты и поддержка

### Авторы

| Разработчик | Роль | GitHub |
|-------------|------|--------|
| Андреев И. | Разработчик A (User Service) | [@Iv05An](https://github.com/Iv05An) |
| Бозванов И. | Разработчик B (Analytics Service) | [@bozvan](https://github.com/bozvan) |
| Скалеух И. | Разработчик C (Survey Service) | [@isco25](https://github.com/isco25) |

### Обратная связь

По всем вопросам и предложениям обращайтесь через:
- **GitHub Issues**: [ссылка на репозиторий](https://github.com/isco25/pius_project)
