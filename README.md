____
# Yatube - социальная сеть для блогеров

* Читайте записи участников сообщества без регистрации
* Зарегистрируйтесь на сайте и создавайте посты с иллюстрациями, от своего имени и в тематических сообществах
* Оставляйте свои комментарии к записям 
* Подписывайтесь на авторов
* Доступен поиск по авторам и группам
____

## Технологии:
Python 3.7, Django 

## Как запустить проект:

1. Клонировать репозиторий, выполнив следующую команду в консоли:
```
git clone https://github.com/StrekozJulia/api_final_yatube.git
```
2. Перейти в него в командной строке
```
cd api_final_yatube
```
3. Cоздать виртуальное окружение
```
py -3.7 -m venv venv
```
4. Активировать виртуальное окружение
```
source venv/scripts/activate
```
5. Обновить пакетный установщик
```
py -3.7 -m pip install --upgrade pip
```
6. Установить зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
7. Выполнить миграции
```
python manage.py migrate
```
8. Запустить проект
```
python manage.py runserver
```
9. Перейти на локальный адрес сайта в браузере
```
http:/127.0.0.1:8000/
```
