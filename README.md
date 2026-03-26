```markdown
# Survey Platform API — Сервис пользователей

Сервис пользователей для платформы опросов. Реализует регистрацию, аутентификацию с JWT и получение данных пользователя.

---

## 🚀 Функциональность

| Метод | Эндпоинт | Описание | Аутентификация |
|-------|----------|----------|----------------|
| POST | `/register` | Регистрация нового пользователя | ❌ нет |
| POST | `/login` | Вход в систему, получение JWT-токена | ❌ нет |
| GET | `/users/{id}` | Получение данных пользователя по ID | ✅ требуется JWT |

---

## 🛠 Технологии

- **Python 3.11+**
- **FastAPI** — веб-фреймворк
- **Uvicorn** — ASGI-сервер
- **SQLite** — база данных
- **JWT (HS256)** — аутентификация
- **PBKDF2-SHA256** — хеширование паролей
- **Pydantic** — валидация данных
- **unittest** — тестирование

---

## 📁 Структура проекта

```
src/app/
├── main.py                    # Точка входа
├── application.py             # Фабрика приложения
├── config.py                  # Настройки
├── database.py                # Работа с SQLite
├── security.py                # Хеширование паролей + JWT
└── users/                     # Модуль пользователей
    ├── models.py              # Модель User
    ├── schemas.py             # Pydantic-схемы
    ├── repository.py          # Доступ к БД
    ├── service.py             # Бизнес-логика
    └── router.py              # Эндпоинты API

tests/
└── test_users.py              # Интеграционные тесты
```

---

## ⚙️ Установка и запуск

```bash
# Клонирование
git clone https://github.com/isco25/pius_project.git
cd pius_project

# Виртуальное окружение
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate            # Windows

# Установка зависимостей
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Запуск сервера
uvicorn app.main:app --app-dir src --reload
```

Сервер доступен: http://127.0.0.1:8000  
Документация: http://127.0.0.1:8000/docs

---

## 🔐 Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `APP_NAME` | `Survey Platform API` | Название приложения |
| `DATABASE_URL` | `data/survey_platform.db` | Путь к SQLite |
| `JWT_SECRET` | `change-me-in-production` | Секрет JWT |
| `JWT_EXPIRATION_MINUTES` | `60` | Время жизни токена |

---

## 📡 Примеры запросов

### Регистрация
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "StrongPass123"}'
```

### Вход
```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "StrongPass123"}'
```

### Получение пользователя
```bash
curl -X GET http://127.0.0.1:8000/users/1 \
  -H "Authorization: Bearer <token>"
```

---

## 🧪 Тестирование

```bash
python -m unittest discover -s tests -v
```

---

## 🧹 Линтинг и форматирование

```bash
ruff check .
ruff format .
```

---

## 👤 Разработчик

Андреев — сервис пользователей  
Лабораторная работа №2
```
