# Book Library App (MTS SHAD)

Учебное FastAPI-приложение, доработанное под платформу объявлений о продаже книг.

## Что реализовано

### Модели и связи

- Добавлена модель `Seller` с полями:
  - `id`
  - `first_name`
  - `last_name`
  - `e_mail`
  - `password`
- В модель `Book` добавлено поле `seller_id`.
- Связь `Seller (1) -> (N) Book`.
- При удалении продавца удаляются все его книги (cascade delete).

### Эндпоинты Seller

- `POST /api/v1/seller` — регистрация продавца.
- `GET /api/v1/seller` — список всех продавцов (без `password` в ответе).
- `GET /api/v1/seller/{seller_id}` — продавец + его книги (без `password`).
- `PUT /api/v1/seller/{seller_id}` — обновление данных продавца (без обновления пароля и книг).
- `DELETE /api/v1/seller/{seller_id}` — удаление продавца и его книг.

### JWT авторизация (дополнительное задание)

- `POST /api/v1/token` — получение токена по `email + password`.
- Формат заголовка: `Authorization: Bearer <token>`.
- Защищены эндпоинты:
  - `GET /api/v1/seller/{seller_id}`
  - `POST /api/v1/books/`
  - `PUT /api/v1/books/{book_id}`

## Локальный запуск

### 1) Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2) Настройка переменных окружения

Создайте `.env` по примеру `.env_example` и укажите подключение к PostgreSQL.

Минимально нужны:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USERNAME`
- `DB_PASSWORD`

Для тестов используйте отдельную БД:
- `DB_TEST_NAME=fastapi_project_test_db`

### 3) Запуск приложения

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8010 --reload
```

Swagger UI:
- `http://127.0.0.1:8010/docs`

## Тесты

Запуск:

```bash
python -m pytest src
```

Текущее состояние: `23 passed`.

## Ручная проверка в Swagger/Postman

1. Создать продавца через `POST /api/v1/seller`.
2. Получить токен через `POST /api/v1/token`.
3. Нажать `Authorize` в Swagger и вставить токен в формате `Bearer <token>`.
4. Проверить защищенные ручки:
   - `POST /api/v1/books/`
   - `PUT /api/v1/books/{book_id}`
   - `GET /api/v1/seller/{seller_id}`
