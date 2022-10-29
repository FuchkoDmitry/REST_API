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
---

### Технологии: 
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) 
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white) 
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
<img src="https://img.shields.io/badge/celery-%2337814A.svg?&style=for-the-badge&logo=celery&logoColor=white" />
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)

---
### ***Инструкция по запусу проекта в `docker`:***

* Создать файл `.env` в корне проекта
* Внести в созданный файл следующие переменные:
   + POSTGRES_USER=username
   + POSTGRES_PASSWORD=1234
   + POSTGRES_DB=db_name
   + POSTGRES_PORT=5432
   + POSTGRES_HOST=db
   + POSTGRES_ENGINE=django.db.backends.postgresql
   + EMAIL=your_email@mail.ru
   + EMAIL_HOST=smtp.mail.ru(в зависимости от использованной почты, указан для mail почты)
   + EMAIL_PORT=465(в зависимости от использованной почты, указан для mail почты)
   + EMAIL_PASSWORD=passwordforexternalapps([инструкция](https://help.mail.ru/mail/security/protection/external))
   + SECRET_KEY=yoursecretkey
   + DEBUG=False
   + DJANGO_SUPERUSER_PASSWORD=passwordforsuperuser(создается при запуске приложения в докере)
   + DJANGO_SUPERUSER_EMAIL=yoursuperuseremail@mail.ru
   + DJANGO_SUPERUSER_USERNAME=superusername
   + CELERY_BROKER=redis://redis:6379/0
   + CELERY_BACKEND=redis://redis:6379/1
* в корне проекта(на одном уровне с docker-compose.yaml ) `docker-compose up --build`
---
### ***Документация*** <http://localhost/swagger/>

---
### ***Примеры запросов в Postman***
[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/5ebc7d23f80fb0a15f2c?action=collection%2Fimport)

---

### ***Фунциональность:***

* #### ***Регистрация.***

Пользователь может зарегистрироваться, после этого ему приходит письмо на указанный адрес для подтверждения почты. 
* #### ***Вход/Выход***
После подтверждения почты необходимо выполнить вход на сайт по логину и пароля. При успешном входе пользователю отправляется токен для совершения дальнейшних запросов.
После выхода с сайта(logout) токен удаляется и для дальнейших запросов необходимо выполнить повторный вход.
* #### ***Сброс/Смена пароля***
Есть возможность сменить/сбросить пароль. На почту придет токен, его необходимо будет передать в следующем запросе вместе с новым паролем.
* #### ***Личный кабинет***
Есть личный кабинет, где можно посмотреть и изменить пероснальные данные, а также посмотреть, указанные адреса доставок.
Можно изменить, удалить и добавить  новый адрес доставки.
* #### ***Для клиента***
  * Магазины. Посмотреть все магазины представленные на сайте и посмотреть все товары представленные в конкретном магазине.
  * Категории. Посмотреть все категории продуктов представленных на сайте и все продукты в отдельно святой категории.
  * Продукты. Посмотреть список всех продуктов, с информацией о наличии в магазинах(есть фильтрация по id продукта, id магазина и категории, а таже поиск по имени) и подробную информацию о продукте.
  * Корзина. Добавить товары в корзину, обновить, заменить состав корзины и удалить корзину.
  * Оформить заказ. Подтвердить заказ передачей id необходимого адреса доставки или все необходимые данные доставки(Отправляется письмо о создании нового заказа(также администратору сайта)).
  * Истроия заказов. Посмотреть историю заказов и детали определенного заказа.
* #### ***Для поставщика***
  * Импорт товаров. Выслать `yaml` файл со списком доступных товаров(Пример yaml файла ./data/shop1.yaml)
  * Прием заказов. Открыть/закрыть прием заказов. 
  * Данные магазина. Изменить название и адрес сайта(при необходимости)
  * Получить список заказовс товарами из своего прайс-листа
* #### ***Изменение статуса заказа***
  * Осуществляется администратором сайта через admin панель. При изменении статуса заказа высылается письмо клиенту оформившему заказ и администратору.
При изменении статуса заказа на "Подтвержден" происходит проверка в прайс листах магазинов. Если необходимое количество товаров есть в наличии заказ подтверждается и количество товара в магазинах уменьшается на количество указанное в заказе. 
