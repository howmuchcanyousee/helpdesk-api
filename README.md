# Helpdesk API

Backend-сервис для обработки заявок технической поддержки с авторизацией,
ролями пользователей, PostgreSQL, миграциями, тестами и запуском через Docker
Compose.

## Стек

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT
- Docker / Docker Compose
- pytest
- ruff
- GitHub Actions

## Возможности

- Регистрация и авторизация по email и паролю.
- Роли пользователей: `user`, `support`, `admin`.
- Создание и обработка заявок технической поддержки.
- Статусы и приоритеты заявок.
- Назначение исполнителя сотрудником поддержки.
- Комментарии к заявкам.
- Фильтрация списка заявок.
- Пагинация через `limit` и `offset`.
- Swagger / OpenAPI документация.
- Автоматические API-тесты.

## Быстрый запуск

Требуется установленный Docker Desktop с запущенным Docker Engine.

```bash
git clone https://github.com/howmuchcanyousee/helpdesk-api.git
cd helpdesk-api
cp .env.example .env
docker compose up --build
```

Для Windows PowerShell вместо `cp` используйте:

```powershell
Copy-Item .env.example .env
```

Перед первым запуском замените в `.env` placeholder пароля в
`POSTGRES_PASSWORD` и этот же пароль внутри `DATABASE_URL`, а также значение
`SECRET_KEY`. Случайный ключ можно создать командой
`python -c "import secrets; print(secrets.token_urlsafe(48))"`. Docker Compose
ожидает готовности PostgreSQL, затем API автоматически выполняет
`alembic upgrade head` и запускается по адресу `http://localhost:8000`.

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

Проверка работоспособности:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

## Переменные окружения

Основные настройки находятся в `.env.example`.

| Переменная | Описание |
| --- | --- |
| `APP_NAME` | Название приложения в документации FastAPI. |
| `APP_ENV` | Окружение запуска, например `development`. |
| `APP_DEBUG` | Режим отладки FastAPI: `true` или `false`. |
| `POSTGRES_DB` | Имя базы данных, создаваемой контейнером PostgreSQL. |
| `POSTGRES_USER` | Пользователь PostgreSQL. |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL для локального окружения. |
| `DATABASE_URL` | Строка подключения SQLAlchemy к PostgreSQL. В Docker hostname БД — `db`. |
| `SECRET_KEY` | Секрет для подписи JWT. Не должен попадать в Git. |
| `ALGORITHM` | Алгоритм JWT, по умолчанию `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access token в минутах. |

## Миграции

В Docker миграции применяются автоматически при запуске API. Для ручной работы
с Alembic используйте команды внутри контейнера, где hostname `db` доступен:

```bash
# Создать миграцию после изменения SQLAlchemy-моделей
docker compose exec api alembic revision --autogenerate -m "describe_change"

# Применить все миграции
docker compose exec api alembic upgrade head
```

## Демонстрационные данные

Команда seed создаёт пользователей, две заявки и комментарии только для
локальной разработки. Она не запускается при старте API и завершается с ошибкой,
если `APP_ENV` отличается от `development` или `test`.

В `.env.example` заданы исключительно локальные dev-пароли. Перед запуском при
необходимости замените `SEED_ADMIN_PASSWORD`, `SEED_SUPPORT_PASSWORD` и
`SEED_USER_PASSWORD` в своём `.env`, затем выполните:

```bash
docker compose exec api python -m app.scripts.seed
```

Повторный запуск не создаёт дубликаты и не перезаписывает существующие аккаунты.

| Пользователь | Роль | Пароль из `.env.example` |
| --- | --- | --- |
| `admin@example.com` | `admin` | `local-admin-password` |
| `support@example.com` | `support` | `local-support-password` |
| `user@example.com` | `user` | `local-user-password` |

## Тесты

Установите зависимости для разработки:

```bash
pip install -e ".[dev]"
```

Запуск тестов:

```bash
pytest
```

Тесты используют отдельную переменную `TEST_DATABASE_URL`. По умолчанию
используется изолированная SQLite БД в памяти. Для отдельной PostgreSQL БД:

```powershell
docker compose exec db createdb -U helpdesk helpdesk_test
$env:TEST_DATABASE_URL = "postgresql+psycopg://helpdesk:<password>@localhost:5432/helpdesk_test"
pytest
```

Защитная проверка не позволяет тестам очищать PostgreSQL-БД, имя которой не
заканчивается на `_test`.

Проверки стиля:

```bash
ruff check .
ruff format --check .
```

Установка Git hooks:

```bash
pre-commit install
pre-commit run --all-files
```

## CI

Workflow GitHub Actions запускается на каждый `push` и `pull_request`. Он
устанавливает зависимости для разработки и выполняет `ruff check .`,
`ruff format --check .` и `pytest` с изолированной SQLite БД.

## Примеры API-запросов

### Регистрация

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure-password","full_name":"Test User"}'
```

### Логин

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure-password"}'
```

Сохраните поле `access_token` из ответа и передавайте его как
`Authorization: Bearer <access_token>`.

### Создание заявки

```bash
curl -X POST http://localhost:8000/tickets \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Не работает вход","description":"После ввода пароля возникает ошибка.","priority":"high"}'
```

### Получение списка заявок

```bash
curl "http://localhost:8000/tickets?status=open&priority=high&limit=20&offset=0" \
  -H "Authorization: Bearer <access_token>"
```

### Добавление комментария

```bash
curl -X POST http://localhost:8000/tickets/1/comments \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"text":"Добавляю детали проблемы."}'
```

## Роли и права доступа

| Действие | `user` | `support` | `admin` |
| --- | --- | --- | --- |
| Просмотр заявок | Только своих | Всех | Всех |
| Создание заявки | Да | Да | Да |
| Изменение заявки | Свои `title`/`description`, кроме `closed` | `status` и `assigned_to_id` | Все поля |
| Удаление заявки | Нет | Нет | Да |
| Создание комментария | Только в своих заявках | В любой заявке | В любой заявке |
| Изменение комментария | Только своего | Только своего | Только своего |
| Удаление комментария | Нет | Да | Да |

## Что можно улучшить

- Добавить refresh token и механизм отзыва токенов.
- Реализовать email-уведомления о событиях по заявке.
- Добавить файловые вложения к заявкам и комментариям.
- Вынести фоновые задачи в Redis / Celery.
- Добавить frontend-клиент для работы с API.
