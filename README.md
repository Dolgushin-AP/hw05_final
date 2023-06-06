## Yatube

Социальная сеть блогеров. Позволяет писать посты и публиковать их в отдельных группах, делать подписки на посты и любимых блогеров, добавлять, удалять записи и комментировать их.

### Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

```
https://github.com/Dolgushin-AP/hw05_final.git
```

```
cd hw05_final
```

Установите и активируйте виртуальное окружение (Windows):

```
python -m venv venv
```
```
source venv/Scripts/activate
```

Установить зависимости:

```
pip install -r requirements.txt
```

Применить миграции:

```
python manage.py makemigrations
```
```
python manage.py migrate
```

Создание суперпользователя:

```
python manage.py createsuperuser
```

Запуск приложения:

```
python manage.py runserver
```

### Технологии:
- Python 3
- Django 2
- Django Unittest
- SQLite
- Git
