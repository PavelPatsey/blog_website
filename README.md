# Сайт блог

[![CI](https://github.com/PavelPatsey/blog_website/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/PavelPatsey/blog_website/actions/workflows/python-app.yml)

### Описание
Социальная сеть для публикации личных дневников. Можно создавать свою страницу, подписываться на других авторов и комментировать их записи.
### Технологии:
- Python 3.7
- Django 2.2.19
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
```
python3 -m venv venv
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Примените миграции:
```
python3 manage.py migrate
```
- Чтобы запустить работу сайта, в папке с файлом manage.py выполните команду:
```
python3 manage.py runserver
```
- Чтобы запустить тесты, в папке с файлом manage.py выполните команду:
```
python3 manage.py test
```
- Чтобы создать суперпользователя, в папке с файлом manage.py выполните команду:
```
python3 manage.py createsuperuser
```

### Авторы
Пацей Павел
