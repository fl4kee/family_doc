==================
Тестовое задание
==================
| Для работы приложения необходимо вставить api ключ в переменную API_KEY файл .env Ключ можно получить здесь https://api.openweathermap.org 
|
| Данные передаются по московскому времени. Изменить часовой пояс можно в файле .env переменная TIME_ZONE
|
| Для запуска используется docker-compose version 1.29.2
|
| 1 Скопировать репозиторий $ git clone https://github.com/fl4kee/family_doc && cd family_doc
|
| 2 Вставить полученный ключ в переменную API_KEY в .env файле
|
| 3 Запустить build $ docker-compose build
|
| 4 Произвести миграции $ docker-compose run app python3.9 manage.py migrate
|  
| 5 Запустить контейнеры $ docker-compose up
|
| Приложение работает на http://127.0.0.1:8000/
| 
| Пример ендпойнта /weather?country_code=RU&city=Moscow&date=08.02.2022T12:00 
| country_code - код страны (найти можно здесь https://ru.wikipedia.org/wiki/ISO_3166-1)
| city - наименование города
| data - дата и время в формате {day}.{month}.{year}T{hour}:{seconds}

