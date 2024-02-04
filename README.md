### CI baige
![Foodgram workflow](https://github.com/karpovakatya/foodgram-project-react/actions/workflows/main.yml/badge.svg)

#  Описание проекта
Проект доступен по адресу: http://foodgram.servecounterstrike.com
[Проект Фудграм](http://foodgram.servecounterstrike.com)
Продуктовый помощник Фудграм - это приложение, в котором пользователи публикуют рецепты, могут подписываться на публикации других авторов и добавлять рецепты в избранное. Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

# Использованные технологии
Python 3.9, DRF, React, PostgreSQL, gunicorn, yaml

# Запуск проекта локально
### Клонировать репозиторий:
`git clone url.git`

### Cоздать и активировать виртуальное окружение, установить зависимости:
`python3 -m venv env`
`source env/bin/activate`
`python3 -m pip install --upgrade pip`
`pip install -r requirements.txt`

### Запустить проект локально:
`docker compose -f docker-compose.yml up --build -d`

### Выполнить миграции:
`docker compose -f docker-compose.yml exec backend python manage.py migrate`

### Собрать и скопировать статику
`docker compose -f docker-compose.yml exec backend python manage.py collectstatic`
`docker compose -f docker-compose.yml exec backend cp -r /app/static_backend/. /backend_static/static/`

### Настроить переменные окружения
Переименовать файл `.env.example` в `.env` и указать свои значения для переменных

# CI/CD workflow
Для запуска CI/CD в репозитории GitHub Actions Settings/Secrets/Actions прописать Secrets:
```
DOCKER_PASSWORD
DOCKER_USERNAME
HOST
POSTGRES_DB
POSTGRES_PASSWORD
POSTGRES_USER
SSH_KEY
SSH_PASSPHRASE
TELEGRAM_TO
TELEGRAM_TOKEN
USER
```

### Автор
Екатерина Карпова https://github.com/karpovakatya
