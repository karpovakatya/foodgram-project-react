### CI baige
![Foodgram workflow](https://github.com/karpovakatya/foodgram-project-react/actions/workflows/main.yml/badge.svg)

#  Описание проекта Фудграм
Проект доступен по адресу: http://foodgram.servecounterstrike.com

Продуктовый помощник Фудграм - это приложение, в котором пользователи публикуют рецепты, могут подписываться на публикации других авторов и добавлять рецепты в избранное. Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

# Стек технологий
Python 3.9, DRF, React, PostgreSQL, gunicorn, yaml

# Запуск проекта локально
### Клонировать репозиторий:
`git clone url.git`

### Настроить переменные окружения
Переименовать файл `.env.example` в `.env` и указать свои значения для переменных

### Запустить проект локально
Перейти в /foodgram-project-react/ и запустить сборку:
`docker compose up --build -d`

### Выполнить миграции:
`docker compose exec backend python manage.py migrate`

### Собрать и скопировать статику
`docker compose exec backend python manage.py collectstatic`
`docker compose exec backend cp -r /app/static/. /backend_static/static/`

### Создать суперюзера
`docker compose exec backend python manage.py createsuperuser`

# Открыть проект
http://localhost:7000 - приложение
http://127.0.0.1:7000/admin/ - админка

# API документация
После сборки проекта документация будет доступна по адресу: 
http://localhost:7000/api/docs/

### Примеры запросов
**Получить токен**
```python
POST /api/auth/token/login/
{
  "password": "string",
  "email": "string"
}

201
{
  "auth_token": "string"
}
```
**Список рецептов**
```python
GET /api/recipes/

200
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "color": "#E26C2D",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Пупкин",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

# CI/CD workflow
Для запуска CI/CD в репозитории GitHub Actions Settings/Secrets/Actions прописать Secrets:
```
- DOCKER_PASSWORD
- DOCKER_USERNAME
- HOST
- POSTGRES_DB
- POSTGRES_PASSWORD
- POSTGRES_USER
- SSH_KEY
- SSH_PASSPHRASE
- TELEGRAM_TO
- TELEGRAM_TOKEN
- USER
```
Для запуска автодеплоя нужно сделать пуш в репозиторий.

### Автор
Екатерина Карпова https://github.com/karpovakatya
