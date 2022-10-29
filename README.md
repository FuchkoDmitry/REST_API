# «API Сервис заказа товаров для розничных сетей».

---

## Описание.

---

Приложение предназначено для автоматизации закупок в розничной сети. Пользователи сервиса — покупатель (менеджер торговой сети, который закупает товары для продажи в магазине) и поставщик товаров.

### Клиент (покупатель):

* Менеджер закупок через API делает ежедневные закупки по каталогу, в котором представлены товары от нескольких поставщиков.
* В одном заказе можно указать товары от разных поставщиков.
* Пользователь может авторизироваться, регистрироваться и восстанавливать пароль через API.

### Поставщик:

* Через API информирует сервис об обновлении прайса. (Пример yaml файла ./data/shop1.yaml)
* Может включать и отключать прием заказов.
* Может получать список оформленных заказов (с товарами из его прайса).

### Технологии: 
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) 
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white) 
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
* Celery, 
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

### ***Инструкция:***
* Запустить в Docker:
    + в корне проекта(на одном уровне с docker-compose.yaml ) `docker-compose up`
* Документация по адресу <http://127.0.0.1:8000/swagger/> 
* Примеры запросов в Postman [![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/5ebc7d23f80fb0a15f2c?action=collection%2Fimport)