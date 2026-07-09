# Helpdesk API

Портфолио-проект backend-сервиса для технической поддержки. API позволяет
регистрировать пользователей, получать JWT-токены и управлять заявками с
разграничением прав для клиентов, сотрудников поддержки и администраторов.

## Стек

- Python 3.12, FastAPI и Pydantic v2
- PostgreSQL, SQLAlchemy 2.0 и Alembic
- JWT, PyJWT и passlib[bcrypt]
- Docker и Docker Compose
- pytest, httpx, ruff и pre-commit

## Возможности

- Регистрация и вход по email и паролю.
- JWT access token без refresh token.
- Роли: `user`, `support`, `admin`.
- Создание, просмотр, частичное изменение и удаление заявок.
- Фильтрация и пагинация списка заявок.
- Контроль доступа в зависимости от роли пользователя.

## Быстрый запуск через Docker

1. Скопируйте файл настроек:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Укажите в `.env` длинное случайное значение `SECRET_KEY`.

3. Дважды кликните по `start.bat`.

Скрипт соберёт контейнеры, запустит PostgreSQL, применит миграции Alembic и
поднимет API по адресу `http://localhost:8000`.

Альтернативно можно выполнить:

```bash
docker compose up --build
```

## Документация и проверка сервиса

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

```json
{"status":"ok"}
```

## Основные endpoints

| Метод | Endpoint | Описание |
| --- | --- | --- |
| POST | `/auth/register` | Регистрация пользователя |
| POST | `/auth/login` | Получение JWT access token |
| GET | `/users/me` | Профиль текущего пользователя |
| POST | `/tickets` | Создание заявки |
| GET | `/tickets` | Список доступных заявок |
| GET | `/tickets/{ticket_id}` | Одна заявка |
| PATCH | `/tickets/{ticket_id}` | Частичное изменение заявки |
| DELETE | `/tickets/{ticket_id}` | Удаление заявки администратором |

Для защищённых endpoints передайте заголовок:

```text
Authorization: Bearer <access_token>
```

## Локальная разработка

Создайте окружение Python 3.12 и установите зависимости:

```bash
pip install -e ".[dev]"
```

Запуск проверок:

```bash
ruff check .
ruff format --check .
pytest
```

Установка Git hooks:

```bash
pre-commit install
```
